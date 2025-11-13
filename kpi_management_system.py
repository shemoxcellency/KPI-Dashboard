"""
Zilla CLinicals KPI Management and Analytics Dashboard (Stable Edition)
Includes safe database handling, retry logic, and full analytics suite.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3, time, io
from datetime import date
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="ZILLA CLINICAL KPI Dashboard",
    page_icon="🎯",
    layout="wide",
)
st.markdown("""
    <style>
    .main-header {
        font-size: 2.4rem;
        color: white;
        text-align: center;
        padding: 1rem;
        background: #1e3a8a;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .section-title {
        font-size: 1.4rem;
        color: #1e3a8a;
        font-weight: 600;
        margin-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# KPI STRUCTURE
# ------------------------------------------------------------
KPI_DATA = [
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
# STABLE DATABASE HANDLER
# ------------------------------------------------------------
class KPIDatabase:
    def __init__(self, db_path="kpi_full.db", retries=3):
        self.db_path = db_path
        self.retries = retries
        self.connect()
        self.create_tables()

    def connect(self):
        """Retry connection if locked."""
        for attempt in range(self.retries):
            try:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10)
                self.conn.execute("PRAGMA journal_mode=WAL;")
                return
            except sqlite3.OperationalError:
                time.sleep(2)
        raise sqlite3.OperationalError("Failed to connect to database after retries.")

    def create_tables(self):
        """Ensure required tables exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    department TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    def safe_execute(self, query, params=()):
        """Execute safely with retry logic for locked DB."""
        for attempt in range(self.retries):
            try:
                with self.conn:
                    self.conn.execute(query, params)
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    time.sleep(2)
                else:
                    raise
        raise sqlite3.OperationalError("Database remained locked after retries.")

    def safe_executemany(self, query, params_list):
        for attempt in range(self.retries):
            try:
                with self.conn:
                    self.conn.executemany(query, params_list)
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    time.sleep(2)
                else:
                    raise
        raise sqlite3.OperationalError("Database remained locked after retries.")

    def add_employee(self, name, department):
        self.safe_execute(
            "INSERT OR IGNORE INTO employees (name, department) VALUES (?, ?)",
            (name, department)
        )

    def delete_employee(self, name):
        with self.conn:
            self.conn.execute("DELETE FROM employees WHERE name=?", (name,))
            self.conn.execute("DELETE FROM assessments WHERE name=?", (name,))

    def get_employees(self):
        return pd.read_sql_query("SELECT * FROM employees", self.conn)

    def save_assessments(self, records):
        self.safe_executemany("""
            INSERT INTO assessments
            (name, department, assessment_date, category, kpi, status, points, weight, category_weight, total_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

    def fetch_assessments(self):
        return pd.read_sql_query("SELECT * FROM assessments", self.conn)


# Initialize DB
db = KPIDatabase()


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def calculate_points(status, weight):
    return weight if status == "Met" else (weight * 0.5 if status == "Partial" else 0)


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
    elements.append(Paragraph("KPI Summary Report", styles["Heading1"]))
    elements.append(Paragraph(f"Employee: {employee['name']}", styles["Normal"]))
    elements.append(Paragraph(f"Department: {employee['department']}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {employee['assessment_date']}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    data = [["Category", "Earned", "Max", "Status"]] + \
           [[r["Category"], f"{r['Earned']:.2f}", f"{r['Max']}", r["Status"]] for _, r in df_summary.iterrows()]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ------------------------------------------------------------
# APP UI
# ------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎯 ZILLA CLINICALS KPI Dashboard</h1>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", ["📝 Data Entry", "📊 Dashboard", "👥 Employee Management", "📈 Analytics"])

# ------------------------------------------------------------
# DATA ENTRY
# ------------------------------------------------------------
if page == "📝 Data Entry":
    st.header("Step 1: Data Entry")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Employee Name")
    with col2:
        department = st.selectbox("Department", ["Data Management", "Programming"])
    assessment_date = st.date_input("Assessment Date", value=date.today())

    if name:
        db.add_employee(name, department)
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
                    key=f"{category}_{kpi}_{name}"
                )
            with col3:
                points = calculate_points(status, weight)
                st.metric("Points", f"{points:.2f}")
            total_score += points
            records.append((name, department, str(assessment_date),
                            category, kpi, status, points, weight, CATEGORY_WEIGHTS[category], 0))

        if st.button("💾 Save Assessment", type="primary"):
            for i in range(len(records)):
                r = list(records[i])
                r[-1] = total_score
                records[i] = tuple(r)
            db.save_assessments(records)
            st.success(f"Assessment saved successfully! Total Score: {total_score:.2f}")


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
elif page == "📊 Dashboard":
    st.header("Step 2: Dashboard View")
    data = db.fetch_assessments()
    if data.empty:
        st.info("No data yet.")
    else:
        name = st.selectbox("Select Employee", data["name"].unique())
        emp_data = data[data["name"] == name]
        total_score = emp_data["points"].sum()
        st.metric("Total Score", f"{total_score:.2f} / 100")

        summary = emp_data.groupby("category").agg({"points": "sum", "category_weight": "max"}).reset_index()
        summary.rename(columns={"category": "Category", "points": "Earned", "category_weight": "Max"}, inplace=True)
        summary["Status"] = summary.apply(lambda r: category_status(r["Earned"], r["Max"]), axis=1)
        st.dataframe(summary, use_container_width=True)

        # Visualizations
        tab1, tab2, tab3 = st.tabs(["Radar", "Bar", "Heatmap"])
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=(summary["Earned"] / summary["Max"]) * 100,
                theta=summary["Category"],
                fill='toself'
            ))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            fig2 = px.bar(summary, x="Category", y="Earned", color="Status",
                          color_discrete_map={"On Track": "#10b981", "Improve": "#f59e0b", "Needs Attention": "#ef4444"})
            st.plotly_chart(fig2, use_container_width=True)
        with tab3:
            pivot = emp_data.pivot_table(index="category", columns="kpi", values="points", fill_value=0)
            st.dataframe(pivot.style.background_gradient(cmap="Blues"), use_container_width=True)

        st.subheader("Export")
        c1, c2, c3 = st.columns(3)
        csv = emp_data.to_csv(index=False)
        c1.download_button("📥 CSV", csv, f"{name}_kpi.csv")
        excel = io.BytesIO()
        with pd.ExcelWriter(excel, engine='xlsxwriter') as writer:
            emp_data.to_excel(writer, index=False)
            summary.to_excel(writer, index=False, sheet_name="Summary")
        c2.download_button("📊 Excel", excel.getvalue(), f"{name}_kpi.xlsx")
        pdf = export_pdf({"name": name, "department": emp_data['department'].iloc[0], "assessment_date": emp_data['assessment_date'].iloc[0]}, summary)
        c3.download_button("📄 PDF", pdf, f"{name}_kpi.pdf", mime="application/pdf")


# ------------------------------------------------------------
# EMPLOYEE MANAGEMENT
# ------------------------------------------------------------
elif page == "👥 Employee Management":
    st.header("Step 3: Employee Management")
    employees = db.get_employees()
    if employees.empty:
        st.info("No employees added yet.")
    else:
        st.dataframe(employees[['name', 'department', 'created_at']], use_container_width=True)
        name_to_delete = st.selectbox("Select Employee to Delete", employees["name"].unique())
        if st.button("🗑️ Delete Employee", type="secondary"):
            db.delete_employee(name_to_delete)
            st.success(f"Deleted {name_to_delete} and all KPI data.")
            st.rerun()

    data = db.fetch_assessments()
    if not data.empty:
        team_summary = data.groupby(["name", "department"])["points"].sum().reset_index()
        team_summary["Status"] = team_summary["points"].apply(lambda x: category_status(x, 100))
        fig_team = px.bar(team_summary, x="name", y="points", color="Status",
                          color_discrete_map={"On Track": "#10b981", "Improve": "#f59e0b", "Needs Attention": "#ef4444"})
        st.plotly_chart(fig_team, use_container_width=True)


# ------------------------------------------------------------
# ANALYTICS
# ------------------------------------------------------------
elif page == "📈 Analytics":
    st.header("Step 4: Advanced Analytics")
    data = db.fetch_assessments()
    if data.empty:
        st.info("No data available.")
    else:
        all_scores = data.groupby("name")["points"].sum().reset_index()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Average", f"{all_scores['points'].mean():.1f}")
        c2.metric("Highest", f"{all_scores['points'].max():.1f}")
        c3.metric("Lowest", f"{all_scores['points'].min():.1f}")
        c4.metric("Total Employees", f"{len(all_scores)}")

        fig_hist = px.histogram(all_scores, x="points", nbins=15, title="Score Distribution", color_discrete_sequence=["#1e3a8a"])
        st.plotly_chart(fig_hist, use_container_width=True)

        category_scores = data.groupby("category")["points"].mean().reset_index()
        fig_cat = px.bar(category_scores, x="category", y="points", title="Average Category Performance", color="points", color_continuous_scale="Blues")
        st.plotly_chart(fig_cat, use_container_width=True)

        st.subheader("🎯 Recommendations")
        for _, r in all_scores.iterrows():
            if r["points"] < 70:
                st.warning(f"{r['name']}: Needs improvement — focus on process efficiency and documentation.")
            elif 70 <= r["points"] < 85:
                st.info(f"{r['name']}: Improving steadily — maintain consistency.")
            else:
                st.success(f"{r['name']}: Excellent — keep performance at this level.")
