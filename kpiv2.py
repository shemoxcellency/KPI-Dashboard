"""
ClinFocus KPI Management Dashboard
Streamlit application for collecting KPI status and visualizing performance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import date
import plotly.express as px
import plotly.graph_objects as go
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="KPI Management System",
    page_icon="🎯",
    layout="wide",
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        color: white;
        text-align: center;
        padding: 1rem;
        background: #1e3a8a;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# KPI STRUCTURE
# ------------------------------------------------------------
KPI_DATA = [
    # Category, KPI, Weight
    ("Performance & Delivery", "Task Completion Rate", 8.75),
    ("Performance & Delivery", "Quality of Output", 8.75),
    ("Performance & Delivery", "Process Efficiency", 8.75),
    ("Performance & Delivery", "Documentation & Compliance", 8.75),

    ("Collaboration & Team Engagement", "Cross-Team Communication", 5),
    ("Collaboration & Team Engagement", "Meeting Participation", 5),
    ("Collaboration & Team Engagement", "Collaboration Quality", 5),
    ("Collaboration & Team Engagement", "Team Morale Contribution", 5),

    ("Ownership & Initiative", "Accountability", 5),
    ("Ownership & Initiative", "Problem Solving", 5),
    ("Ownership & Initiative", "Innovation & Continuous Improvement", 5),
    ("Ownership & Initiative", "Dependability Index", 5),

    ("Learning & Growth", "Skill Advancement", 3.75),
    ("Learning & Growth", "Application of Learning", 3.75),
    ("Learning & Growth", "Growth Goal Achievement", 3.75),
    ("Learning & Growth", "Knowledge Sharing", 3.75),

    ("Business & Impact Alignment", "Impact on KPIs", 2.5),
    ("Business & Impact Alignment", "Customer or Stakeholder Feedback", 2.5),
    ("Business & Impact Alignment", "Efficiency Contribution", 2.5),
    ("Business & Impact Alignment", "Strategic Alignment", 2.5),
]

CATEGORY_WEIGHTS = {
    "Performance & Delivery": 35,
    "Collaboration & Team Engagement": 20,
    "Ownership & Initiative": 20,
    "Learning & Growth": 15,
    "Business & Impact Alignment": 10,
}


# ------------------------------------------------------------
# DATABASE HANDLER
# ------------------------------------------------------------
class KPIDatabase:
    def __init__(self):
        self.conn = sqlite3.connect("kpi_database.db", check_same_thread=False)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                name TEXT,
                department TEXT,
                assessment_date TEXT,
                category TEXT,
                kpi TEXT,
                status TEXT,
                points REAL,
                weight REAL,
                category_weight REAL,
                total_score REAL
            )
        """)
        self.conn.commit()

    def save(self, records):
        self.conn.executemany("""
            INSERT INTO assessments
            (employee_id, name, department, assessment_date, category, kpi, status, points, weight, category_weight, total_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)
        self.conn.commit()

    def fetch(self):
        return pd.read_sql_query("SELECT * FROM assessments", self.conn)


db = KPIDatabase()


# ------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------
def calculate_points(status, weight):
    if status == "Met":
        return weight
    elif status == "Partial":
        return weight * 0.5
    return 0


def category_status(earned, max_weight):
    pct = (earned / max_weight) * 100 if max_weight else 0
    if pct >= 85:
        return "On Track"
    elif pct >= 70:
        return "Improve"
    return "Needs Attention"


def export_pdf(employee, df_summary):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("KPI Summary Report", styles['Heading1']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Employee: {employee['name']}", styles['Normal']))
    elements.append(Paragraph(f"Employee ID: {employee['employee_id']}", styles['Normal']))
    elements.append(Paragraph(f"Department: {employee['department']}", styles['Normal']))
    elements.append(Paragraph(f"Date: {employee['assessment_date']}", styles['Normal']))
    elements.append(Spacer(1, 20))

    data = [["Category", "Earned", "Max", "Status"]]
    for _, row in df_summary.iterrows():
        data.append([row["Category"], f"{row['Earned']:.2f}", f"{row['Max']}", row["Status"]])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎯 ClinFocus KPI Dashboard</h1>", unsafe_allow_html=True)

page = st.sidebar.radio("Navigation", ["📝 Data Entry", "📊 Dashboard"])

# ------------------------------------------------------------
# DATA ENTRY PAGE
# ------------------------------------------------------------
if page == "📝 Data Entry":
    st.header("Employee KPI Entry")

    col1, col2, col3 = st.columns(3)
    with col1:
        employee_id = st.text_input("Employee ID")
    with col2:
        employee_name = st.text_input("Employee Name")
    with col3:
        department = st.selectbox("Department", ["Data Management", "Programming"])

    assessment_date = st.date_input("Assessment Date", value=date.today())
    st.markdown("---")

    if employee_id and employee_name:
        records = []
        total_score = 0

        for category, kpi, weight in KPI_DATA:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{category}** — {kpi}")
            with col2:
                status = st.selectbox(
                    "Status",
                    ["Met", "Partial", "Not Met"],
                    key=f"{category}_{kpi}"
                )
            with col3:
                points = calculate_points(status, weight)
                st.metric("Points", f"{points:.2f}")
            total_score += points
            records.append((employee_id, employee_name, department, str(assessment_date),
                            category, kpi, status, points, weight, CATEGORY_WEIGHTS[category], 0))

        if st.button("💾 Save Assessment", type="primary"):
            for i in range(len(records)):
                r = list(records[i])
                r[-1] = total_score
                records[i] = tuple(r)
            db.save(records)
            st.success(f"Assessment saved successfully! Total Score: {total_score:.2f}")

# ------------------------------------------------------------
# DASHBOARD PAGE
# ------------------------------------------------------------
else:
    data = db.fetch()

    if data.empty:
        st.info("No data recorded yet. Add KPI assessments first.")
    else:
        st.header("KPI Dashboard")

        employee_list = data["name"].unique()
        selected_emp = st.selectbox("Select Employee", employee_list)
        emp_data = data[data["name"] == selected_emp]

        st.subheader(f"Overview for {selected_emp}")
        total_score = emp_data["points"].sum()
        st.metric("Total Score", f"{total_score:.2f} / 100")

        # Category summary
        summary = emp_data.groupby("category").agg({"points": "sum", "category_weight": "max"}).reset_index()
        summary.rename(columns={"category": "Category", "points": "Earned", "category_weight": "Max"}, inplace=True)
        summary["Status"] = summary.apply(lambda r: category_status(r["Earned"], r["Max"]), axis=1)

        st.dataframe(summary, use_container_width=True)

        # Bar chart
        fig = px.bar(summary, x="Category", y="Earned", color="Status",
                     color_discrete_map={
                         "On Track": "#10b981",
                         "Improve": "#f59e0b",
                         "Needs Attention": "#ef4444"
                     },
                     title="Category Performance")
        st.plotly_chart(fig, use_container_width=True)

        # Overall performance
        overall_status = category_status(total_score, 100)
        st.subheader(f"Overall Status: {overall_status}")

        # Export section
        col1, col2, col3 = st.columns(3)
        with col1:
            csv = emp_data.to_csv(index=False)
            st.download_button("📥 Download CSV", data=csv, file_name=f"{selected_emp}_KPI.csv")
        with col2:
            excel = io.BytesIO()
            with pd.ExcelWriter(excel, engine='xlsxwriter') as writer:
                emp_data.to_excel(writer, index=False, sheet_name="KPI Data")
                summary.to_excel(writer, index=False, sheet_name="Summary")
            st.download_button("📊 Download Excel", data=excel.getvalue(),
                               file_name=f"{selected_emp}_KPI.xlsx")
        with col3:
            pdf = export_pdf({
                "employee_id": emp_data["employee_id"].iloc[0],
                "name": selected_emp,
                "department": emp_data["department"].iloc[0],
                "assessment_date": emp_data["assessment_date"].iloc[0]
            }, summary)
            st.download_button("📄 Download PDF", data=pdf, file_name=f"{selected_emp}_KPI.pdf", mime="application/pdf")

        # Organization-wide view
        st.markdown("---")
        st.subheader("📈 Organization Overview")
        org_summary = data.groupby(["name"]).agg({"points": "sum"}).reset_index()
        org_summary["Status"] = org_summary["points"].apply(lambda p: category_status(p, 100))

        fig_org = px.bar(org_summary, x="name", y="points", color="Status",
                         color_discrete_map={
                             "On Track": "#10b981",
                             "Improve": "#f59e0b",
                             "Needs Attention": "#ef4444"
                         },
                         title="Overall Employee Performance")
        st.plotly_chart(fig_org, use_container_width=True)
