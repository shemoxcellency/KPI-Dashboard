"""
Zilla Clinicals KPI Management and Analytics Dashboard (Enhanced Edition)
With Team Analytics, Company Performance, and Quarterly/Yearly Tracking
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import time
import io
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import calendar

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
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .section-title {
        font-size: 1.4rem;
        color: #1e3a8a;
        font-weight: 600;
        margin-top: 2rem;
        border-left: 4px solid #3b82f6;
        padding-left: 10px;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .team-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
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

TEAMS = ["CDM Team 1", "CDM Team 2", "Administrative Team", "Programming Team"]

# ------------------------------------------------------------
# ENHANCED DATABASE HANDLER
# ------------------------------------------------------------
class EnhancedKPIDatabase:
    def __init__(self, db_path="kpi_enhanced.db", retries=3):
        self.db_path = db_path
        self.retries = retries
        self.connect()
        self.create_tables()
        self.migrate_database()

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
        """Ensure required tables exist with enhanced structure."""
        with self.conn:
            # Employees table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    department TEXT,
                    position TEXT,
                    hire_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Enhanced assessments table with period tracking
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    department TEXT,
                    assessment_date TEXT,
                    assessment_year INTEGER,
                    assessment_quarter TEXT,
                    assessment_period TEXT,
                    category TEXT,
                    kpi TEXT,
                    status TEXT,
                    points REAL,
                    weight REAL,
                    category_weight REAL,
                    total_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Team performance tracking
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS team_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    department TEXT,
                    assessment_period TEXT,
                    assessment_year INTEGER,
                    assessment_quarter TEXT,
                    avg_score REAL,
                    min_score REAL,
                    max_score REAL,
                    total_employees INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Company performance tracking
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS company_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assessment_period TEXT,
                    assessment_year INTEGER,
                    assessment_quarter TEXT,
                    avg_score REAL,
                    min_score REAL,
                    max_score REAL,
                    total_employees INTEGER,
                    total_teams INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def migrate_database(self):
        """Add new columns if they don't exist in existing database."""
        try:
            # Check if new columns exist
            cursor = self.conn.execute("PRAGMA table_info(assessments)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'assessment_year' not in columns:
                self.conn.execute("ALTER TABLE assessments ADD COLUMN assessment_year INTEGER")
            if 'assessment_quarter' not in columns:
                self.conn.execute("ALTER TABLE assessments ADD COLUMN assessment_quarter TEXT")
            if 'assessment_period' not in columns:
                self.conn.execute("ALTER TABLE assessments ADD COLUMN assessment_period TEXT")
        except:
            pass

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

    def add_employee(self, name, department, position=None, hire_date=None):
        self.safe_execute(
            """INSERT OR IGNORE INTO employees (name, department, position, hire_date) 
               VALUES (?, ?, ?, ?)""",
            (name, department, position, hire_date)
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
            (name, department, assessment_date, assessment_year, assessment_quarter, 
             assessment_period, category, kpi, status, points, weight, category_weight, total_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

    def fetch_assessments(self, filters=None):
        query = "SELECT * FROM assessments"
        if filters:
            conditions = []
            params = []
            if 'year' in filters:
                conditions.append("assessment_year = ?")
                params.append(filters['year'])
            if 'quarter' in filters:
                conditions.append("assessment_quarter = ?")
                params.append(filters['quarter'])
            if 'department' in filters:
                conditions.append("department = ?")
                params.append(filters['department'])
            if 'name' in filters:
                conditions.append("name = ?")
                params.append(filters['name'])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            return pd.read_sql_query(query, self.conn, params=params)
        return pd.read_sql_query(query, self.conn)

    def save_team_performance(self, department, period, year, quarter, metrics):
        self.safe_execute("""
            INSERT OR REPLACE INTO team_performance
            (department, assessment_period, assessment_year, assessment_quarter, 
             avg_score, min_score, max_score, total_employees)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (department, period, year, quarter, 
              metrics['avg'], metrics['min'], metrics['max'], metrics['count']))

    def save_company_performance(self, period, year, quarter, metrics):
        self.safe_execute("""
            INSERT OR REPLACE INTO company_performance
            (assessment_period, assessment_year, assessment_quarter, 
             avg_score, min_score, max_score, total_employees, total_teams)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (period, year, quarter, 
              metrics['avg'], metrics['min'], metrics['max'], 
              metrics['total_employees'], metrics['total_teams']))

    def get_historical_data(self, entity_type='employee', entity_name=None, periods=4):
        """Fetch historical data for comparison."""
        if entity_type == 'employee':
            query = """
                SELECT DISTINCT assessment_period, assessment_year, assessment_quarter, 
                       SUM(points) as total_score
                FROM assessments
                WHERE name = ?
                GROUP BY assessment_period
                ORDER BY assessment_year DESC, assessment_quarter DESC
                LIMIT ?
            """
            return pd.read_sql_query(query, self.conn, params=(entity_name, periods))
        
        elif entity_type == 'team':
            query = """
                SELECT * FROM team_performance
                WHERE department = ?
                ORDER BY assessment_year DESC, assessment_quarter DESC
                LIMIT ?
            """
            return pd.read_sql_query(query, self.conn, params=(entity_name, periods))
        
        elif entity_type == 'company':
            query = """
                SELECT * FROM company_performance
                ORDER BY assessment_year DESC, assessment_quarter DESC
                LIMIT ?
            """
            return pd.read_sql_query(query, self.conn, params=(periods,))

# Initialize Enhanced DB
db = EnhancedKPIDatabase()

# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------
def get_quarter_from_date(date_obj):
    """Get quarter from date."""
    month = date_obj.month
    quarter = (month - 1) // 3 + 1
    return f"Q{quarter}"

def get_assessment_period(date_obj):
    """Get assessment period string."""
    quarter = get_quarter_from_date(date_obj)
    year = date_obj.year
    return f"{year}-{quarter}"

def calculate_points(status, weight):
    """Calculate points based on status and weight."""
    return weight if status == "Met" else (weight * 0.5 if status == "Partial" else 0)

def get_performance_grade(score):
    """Get performance grade based on score."""
    if score >= 90:
        return "Outstanding", "#10b981"
    elif score >= 80:
        return "Exceeds Expectations", "#34d399"
    elif score >= 70:
        return "Meets Expectations", "#fbbf24"
    elif score >= 60:
        return "Needs Improvement", "#fb923c"
    else:
        return "Unsatisfactory", "#ef4444"

def calculate_trend(current, previous):
    """Calculate trend percentage."""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def export_comprehensive_report(data, report_type='individual', entity_name=None):
    """Generate comprehensive PDF report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = f"KPI {report_type.title()} Report"
    elements.append(Paragraph(title, styles["Title"]))
    
    if entity_name:
        elements.append(Paragraph(f"Entity: {entity_name}", styles["Heading2"]))
    
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    # Add data tables and charts based on report type
    if isinstance(data, pd.DataFrame) and not data.empty:
        # Convert DataFrame to table
        table_data = [data.columns.tolist()] + data.values.tolist()
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
st.markdown("<h1 class='main-header'>🎯 ZILLA CLINICALS KPI Dashboard</h1>", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["📝 Data Entry", "👤 Individual Performance", "👥 Team Analytics", 
     "🏢 Company Overview", "📊 Comparative Analysis", "⚙️ Management"]
)

# ------------------------------------------------------------
# DATA ENTRY PAGE
# ------------------------------------------------------------
if page == "📝 Data Entry":
    st.header("📝 KPI Assessment Data Entry")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        name = st.text_input("Employee Name")
    with col2:
        department = st.selectbox("Department", TEAMS)
    with col3:
        position = st.text_input("Position (Optional)")
    with col4:
        assessment_date = st.date_input("Assessment Date", value=date.today())
    
    # Calculate period information
    year = assessment_date.year
    quarter = get_quarter_from_date(assessment_date)
    period = get_assessment_period(assessment_date)
    
    st.info(f"📅 Assessment Period: **{period}** (Year: {year}, Quarter: {quarter})")
    
    if name:
        db.add_employee(name, department, position)
        
        st.subheader("KPI Assessment")
        
        # Create assessment form
        records = []
        total_score = 0
        
        # Group KPIs by category for better organization
        categories_data = {}
        for category, kpi, weight in KPI_DATA:
            if category not in categories_data:
                categories_data[category] = []
            categories_data[category].append((kpi, weight))
        
        # Display KPIs by category
        for category, kpis in categories_data.items():
            st.markdown(f"### {category} (Weight: {CATEGORY_WEIGHTS[category]}%)")
            
            cols = st.columns(len(kpis))
            for idx, (kpi, weight) in enumerate(kpis):
                with cols[idx]:
                    st.markdown(f"**{kpi}**")
                    st.caption(f"Max Points: {weight}")
                    status = st.selectbox(
                        "Status",
                        ["Met", "Partial", "Not Met"],
                        key=f"{category}_{kpi}_{name}_{assessment_date}"
                    )
                    points = calculate_points(status, weight)
                    st.metric("Points", f"{points:.2f}")
                    
                    total_score += points
                    records.append((
                        name, department, str(assessment_date), year, quarter, period,
                        category, kpi, status, points, weight, 
                        CATEGORY_WEIGHTS[category], 0
                    ))
        
        # Display total score
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col2:
            grade, color = get_performance_grade(total_score)
            st.markdown(f"<h2 style='text-align: center; color: {color};'>Total Score: {total_score:.2f}/100</h2>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: {color};'>Grade: {grade}</h3>", unsafe_allow_html=True)
        
        # Save button
        if st.button("💾 Save Assessment", type="primary", use_container_width=True):
            # Update total score in records
            for i in range(len(records)):
                r = list(records[i])
                r[-1] = total_score
                records[i] = tuple(r)
            
            db.save_assessments(records)
            
            # Calculate and save team performance
            team_data = db.fetch_assessments({'department': department, 'period': period})
            if not team_data.empty:
                team_scores = team_data.groupby('name')['points'].sum().reset_index()
                metrics = {
                    'avg': team_scores['points'].mean(),
                    'min': team_scores['points'].min(),
                    'max': team_scores['points'].max(),
                    'count': len(team_scores)
                }
                db.save_team_performance(department, period, year, quarter, metrics)
            
            # Calculate and save company performance
            company_data = db.fetch_assessments({'period': period})
            if not company_data.empty:
                company_scores = company_data.groupby('name')['points'].sum().reset_index()
                team_count = company_data['department'].nunique()
                metrics = {
                    'avg': company_scores['points'].mean(),
                    'min': company_scores['points'].min(),
                    'max': company_scores['points'].max(),
                    'total_employees': len(company_scores),
                    'total_teams': team_count
                }
                db.save_company_performance(period, year, quarter, metrics)
            
            st.success(f"✅ Assessment saved successfully! Total Score: {total_score:.2f}")
            st.balloons()

# ------------------------------------------------------------
# INDIVIDUAL PERFORMANCE PAGE
# ------------------------------------------------------------
elif page == "👤 Individual Performance":
    st.header("👤 Individual Employee Performance")
    
    data = db.fetch_assessments()
    if data.empty:
        st.info("No assessment data available yet.")
    else:
        # Employee selection
        col1, col2 = st.columns([2, 1])
        with col1:
            employees = data['name'].unique()
            selected_employee = st.selectbox("Select Employee", employees)
        with col2:
            periods = data['assessment_period'].unique()
            selected_period = st.selectbox("Select Period", sorted(periods, reverse=True))
        
        # Filter data
        emp_data = data[(data['name'] == selected_employee) & 
                       (data['assessment_period'] == selected_period)]
        
        if not emp_data.empty:
            # Employee info
            st.markdown(f"### {selected_employee}")
            st.markdown(f"**Department:** {emp_data['department'].iloc[0]} | **Period:** {selected_period}")
            
            # Score metrics
            total_score = emp_data['points'].sum()
            grade, color = get_performance_grade(total_score)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Score", f"{total_score:.2f}/100")
            with col2:
                st.metric("Grade", grade)
            with col3:
                # Get previous period score for comparison
                historical = db.get_historical_data('employee', selected_employee, 2)
                if len(historical) > 1:
                    prev_score = historical.iloc[1]['total_score']
                    delta = total_score - prev_score
                    st.metric("vs Previous", f"{delta:+.2f}", delta=f"{delta:+.2f}")
                else:
                    st.metric("vs Previous", "N/A")
            with col4:
                st.metric("Completion", "100%", delta="All KPIs assessed")
            
            # Category breakdown
            st.markdown("### Category Performance")
            category_summary = emp_data.groupby('category').agg({
                'points': 'sum',
                'category_weight': 'max'
            }).reset_index()
            category_summary['percentage'] = (category_summary['points'] / category_summary['category_weight']) * 100
            category_summary['status'] = category_summary['percentage'].apply(
                lambda x: "🟢 Excellent" if x >= 85 else ("🟡 Good" if x >= 70 else "🔴 Needs Improvement")
            )
            
            # Visualizations
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Radar Chart", "📈 Trends", "📋 Details"])
            
            with tab1:
                # Category performance bar chart
                fig = px.bar(
                    category_summary,
                    x='category',
                    y='percentage',
                    color='percentage',
                    color_continuous_scale='RdYlGn',
                    range_color=[0, 100],
                    title="Category Performance (%)"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Category table
                st.dataframe(
                    category_summary[['category', 'points', 'category_weight', 'percentage', 'status']],
                    hide_index=True,
                    use_container_width=True
                )
            
            with tab2:
                # Radar chart
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=category_summary['percentage'],
                    theta=category_summary['category'],
                    fill='toself',
                    name='Performance'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )
                    ),
                    title="Performance Radar",
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                # Historical trend
                historical = db.get_historical_data('employee', selected_employee, 8)
                if not historical.empty:
                    fig = px.line(
                        historical,
                        x='assessment_period',
                        y='total_score',
                        markers=True,
                        title=f"Performance Trend - {selected_employee}"
                    )
                    fig.update_layout(
                        yaxis_range=[0, 100],
                        xaxis_title="Period",
                        yaxis_title="Score"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No historical data available for trend analysis.")
            
            with tab4:
                # Detailed KPI breakdown
                kpi_details = emp_data[['category', 'kpi', 'status', 'points', 'weight']]
                st.dataframe(kpi_details, hide_index=True, use_container_width=True)
            
            # Export options
            st.markdown("### Export Options")
            col1, col2, col3 = st.columns(3)
            with col1:
                csv = emp_data.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"{selected_employee}_{selected_period}_kpi.csv",
                    mime="text/csv"
                )
            with col2:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    emp_data.to_excel(writer, sheet_name='KPI Data', index=False)
                    category_summary.to_excel(writer, sheet_name='Category Summary', index=False)
                st.download_button(
                    "📊 Download Excel",
                    excel_buffer.getvalue(),
                    f"{selected_employee}_{selected_period}_kpi.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with col3:
                pdf = export_comprehensive_report(
                    category_summary,
                    'individual',
                    selected_employee
                )
                st.download_button(
                    "📄 Download PDF Report",
                    pdf,
                    f"{selected_employee}_{selected_period}_report.pdf",
                    mime="application/pdf"
                )

# ------------------------------------------------------------
# TEAM ANALYTICS PAGE
# ------------------------------------------------------------
elif page == "👥 Team Analytics":
    st.header("👥 Team Performance Analytics")
    
    data = db.fetch_assessments()
    if data.empty:
        st.info("No assessment data available yet.")
    else:
        # Team selection
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_team = st.selectbox("Select Team", TEAMS)
        with col2:
            periods = data['assessment_period'].unique()
            selected_period = st.selectbox("Select Period", sorted(periods, reverse=True))
        
        # Filter team data
        team_data = data[(data['department'] == selected_team) & 
                        (data['assessment_period'] == selected_period)]
        
        if not team_data.empty:
            # Team metrics
            team_employees = team_data['name'].nunique()
            employee_scores = team_data.groupby('name')['points'].sum().reset_index()
            
            avg_score = employee_scores['points'].mean()
            min_score = employee_scores['points'].min()
            max_score = employee_scores['points'].max()
            
            # Display metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Team Size", team_employees)
            with col2:
                st.metric("Average Score", f"{avg_score:.2f}")
            with col3:
                st.metric("Highest Score", f"{max_score:.2f}")
            with col4:
                st.metric("Lowest Score", f"{min_score:.2f}")
            with col5:
                grade, _ = get_performance_grade(avg_score)
                st.metric("Team Grade", grade)
            
            # Team performance distribution
            st.markdown("### Team Performance Distribution")
            
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Distribution", "👥 Individual Scores", "📈 Trends", "🎯 Category Analysis"])
            
            with tab1:
                # Score distribution
                fig = px.histogram(
                    employee_scores,
                    x='points',
                    nbins=20,
                    title=f"{selected_team} Score Distribution",
                    labels={'points': 'Score', 'count': 'Number of Employees'}
                )
                fig.add_vline(x=avg_score, line_dash="dash", line_color="red",
                            annotation_text=f"Team Average: {avg_score:.1f}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Box plot
                fig2 = px.box(
                    employee_scores,
                    y='points',
                    title="Score Distribution Box Plot",
                    points="all"
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            with tab2:
                # Individual employee scores
                employee_scores['grade'] = employee_scores['points'].apply(
                    lambda x: get_performance_grade(x)[0]
                )
                employee_scores = employee_scores.sort_values('points', ascending=False)
                
                # Bar chart of individual scores
                fig = px.bar(
                    employee_scores,
                    x='name',
                    y='points',
                    color='grade',
                    title="Individual Employee Scores",
                    color_discrete_map={
                        "Outstanding": "#10b981",
                        "Exceeds Expectations": "#34d399",
                        "Meets Expectations": "#fbbf24",
                        "Needs Improvement": "#fb923c",
                        "Unsatisfactory": "#ef4444"
                    }
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(employee_scores, hide_index=True, use_container_width=True)
            
            with tab3:
                # Historical team performance
                historical_team = db.get_historical_data('team', selected_team, 8)
                if not historical_team.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=historical_team['assessment_period'],
                        y=historical_team['avg_score'],
                        mode='lines+markers',
                        name='Average Score',
                        line=dict(width=3)
                    ))
                    fig.add_trace(go.Scatter(
                        x=historical_team['assessment_period'],
                        y=historical_team['max_score'],
                        mode='lines',
                        name='Max Score',
                        line=dict(dash='dash')
                    ))
                    fig.add_trace(go.Scatter(
                        x=historical_team['assessment_period'],
                        y=historical_team['min_score'],
                        mode='lines',
                        name='Min Score',
                        line=dict(dash='dash')
                    ))
                    fig.update_layout(
                        title=f"{selected_team} Performance Trend",
                        xaxis_title="Period",
                        yaxis_title="Score",
                        yaxis_range=[0, 100]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No historical data available for trend analysis.")
            
            with tab4:
                # Category performance by team
                team_category = team_data.groupby('category').agg({
                    'points': 'mean',
                    'category_weight': 'max'
                }).reset_index()
                team_category['percentage'] = (team_category['points'] / team_category['category_weight']) * 100
                
                fig = px.bar(
                    team_category,
                    x='category',
                    y='percentage',
                    title="Average Category Performance",
                    color='percentage',
                    color_continuous_scale='RdYlGn',
                    range_color=[0, 100]
                )
                st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# COMPANY OVERVIEW PAGE
# ------------------------------------------------------------
elif page == "🏢 Company Overview":
    st.header("🏢 Company-Wide Performance Overview")
    
    data = db.fetch_assessments()
    if data.empty:
        st.info("No assessment data available yet.")
    else:
        # Period selection
        periods = data['assessment_period'].unique()
        selected_period = st.selectbox("Select Period", sorted(periods, reverse=True))
        
        # Filter data
        period_data = data[data['assessment_period'] == selected_period]
        
        if not period_data.empty:
            # Company metrics
            total_employees = period_data['name'].nunique()
            total_teams = period_data['department'].nunique()
            
            employee_scores = period_data.groupby('name')['points'].sum().reset_index()
            company_avg = employee_scores['points'].mean()
            
            # Team averages
            team_scores = period_data.groupby(['department', 'name'])['points'].sum().reset_index()
            team_averages = team_scores.groupby('department')['points'].mean().reset_index()
            
            # Display company metrics
            st.markdown("### 📊 Company Metrics")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Employees", total_employees)
            with col2:
                st.metric("Active Teams", total_teams)
            with col3:
                st.metric("Company Average", f"{company_avg:.2f}")
            with col4:
                grade, _ = get_performance_grade(company_avg)
                st.metric("Company Grade", grade)
            with col5:
                # Get trend
                historical_company = db.get_historical_data('company', periods=2)
                if len(historical_company) > 1:
                    prev_avg = historical_company.iloc[1]['avg_score']
                    trend = calculate_trend(company_avg, prev_avg)
                    st.metric("Trend", f"{trend:+.1f}%", delta=f"{trend:+.1f}%")
                else:
                    st.metric("Trend", "N/A")
            
            # Visualization tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["📊 Overview", "👥 Team Comparison", "🏆 Rankings", "📈 Trends", "📋 Reports"]
            )
            
            with tab1:
                # Company overview dashboard
                col1, col2 = st.columns(2)
                
                with col1:
                    # Team performance comparison
                    fig = px.bar(
                        team_averages,
                        x='department',
                        y='points',
                        title="Team Average Scores",
                        color='points',
                        color_continuous_scale='RdYlGn',
                        range_color=[0, 100]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Performance distribution pie chart
                    grade_dist = employee_scores['points'].apply(
                        lambda x: get_performance_grade(x)[0]
                    ).value_counts().reset_index()
                    grade_dist.columns = ['Grade', 'Count']
                    
                    fig = px.pie(
                        grade_dist,
                        values='Count',
                        names='Grade',
                        title="Employee Performance Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Category performance across company
                st.markdown("### Category Performance Across Company")
                company_category = period_data.groupby('category').agg({
                    'points': 'mean',
                    'category_weight': 'max'
                }).reset_index()
                company_category['percentage'] = (company_category['points'] / company_category['category_weight']) * 100
                
                fig = px.bar(
                    company_category,
                    x='category',
                    y='percentage',
                    title="Company-Wide Category Performance",
                    color='percentage',
                    color_continuous_scale='RdYlGn',
                    range_color=[0, 100]
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                # Detailed team comparison
                st.markdown("### Detailed Team Comparison")
                
                # Create comparison matrix
                team_metrics = []
                for team in TEAMS:
                    team_data_filtered = period_data[period_data['department'] == team]
                    if not team_data_filtered.empty:
                        scores = team_data_filtered.groupby('name')['points'].sum()
                        team_metrics.append({
                            'Team': team,
                            'Employees': len(scores),
                            'Average': scores.mean(),
                            'Min': scores.min(),
                            'Max': scores.max(),
                            'Std Dev': scores.std()
                        })
                
                if team_metrics:
                    comparison_df = pd.DataFrame(team_metrics)
                    
                    # Heatmap
                    fig = go.Figure(data=go.Heatmap(
                        z=comparison_df[['Average', 'Min', 'Max']].values.T,
                        x=comparison_df['Team'],
                        y=['Average', 'Min', 'Max'],
                        colorscale='RdYlGn',
                        text=comparison_df[['Average', 'Min', 'Max']].values.T.round(2),
                        texttemplate='%{text}',
                        textfont={"size": 12},
                    ))
                    fig.update_layout(title="Team Performance Heatmap")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Comparison table
                    st.dataframe(comparison_df, hide_index=True, use_container_width=True)
            
            with tab3:
                # Rankings
                st.markdown("### 🏆 Performance Rankings")
                
                # Top performers
                top_performers = employee_scores.nlargest(10, 'points')
                bottom_performers = employee_scores.nsmallest(10, 'points')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 🌟 Top 10 Performers")
                    top_performers['rank'] = range(1, len(top_performers) + 1)
                    st.dataframe(
                        top_performers[['rank', 'name', 'points']],
                        hide_index=True,
                        use_container_width=True
                    )
                
                with col2:
                    st.markdown("#### 📈 Employees Needing Support")
                    bottom_performers['improvement_needed'] = 70 - bottom_performers['points']
                    st.dataframe(
                        bottom_performers[['name', 'points', 'improvement_needed']],
                        hide_index=True,
                        use_container_width=True
                    )
            
            with tab4:
                # Historical trends
                st.markdown("### 📈 Historical Company Performance")
                
                historical = db.get_historical_data('company', periods=12)
                if not historical.empty:
                    fig = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=("Average Score Trend", "Employee Count Trend")
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=historical['assessment_period'],
                            y=historical['avg_score'],
                            mode='lines+markers',
                            name='Avg Score'
                        ),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Bar(
                            x=historical['assessment_period'],
                            y=historical['total_employees'],
                            name='Employees'
                        ),
                        row=2, col=1
                    )
                    
                    fig.update_layout(height=600, showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Not enough historical data for trend analysis.")
            
            with tab5:
                # Export reports
                st.markdown("### 📋 Generate Reports")
                
                report_type = st.selectbox(
                    "Select Report Type",
                    ["Company Summary", "Team Breakdown", "Full Analytics"]
                )
                
                if st.button("Generate Report"):
                    if report_type == "Company Summary":
                        report_data = pd.DataFrame({
                            'Metric': ['Total Employees', 'Active Teams', 'Average Score', 'Company Grade'],
                            'Value': [total_employees, total_teams, f"{company_avg:.2f}", grade]
                        })
                    elif report_type == "Team Breakdown":
                        report_data = team_averages
                    else:
                        report_data = employee_scores
                    
                    # Export options
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = report_data.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            f"company_report_{selected_period}.csv",
                            mime="text/csv"
                        )
                    with col2:
                        pdf = export_comprehensive_report(
                            report_data,
                            'company',
                            f"Period: {selected_period}"
                        )
                        st.download_button(
                            "📄 Download PDF",
                            pdf,
                            f"company_report_{selected_period}.pdf",
                            mime="application/pdf"
                        )

# ------------------------------------------------------------
# COMPARATIVE ANALYSIS PAGE
# ------------------------------------------------------------
elif page == "📊 Comparative Analysis":
    st.header("📊 Comparative Analysis")
    
    data = db.fetch_assessments()
    if data.empty:
        st.info("No assessment data available yet.")
    else:
        st.markdown("### Select Comparison Type")
        
        comparison_type = st.selectbox(
            "Comparison Type",
            ["Quarter-over-Quarter", "Year-over-Year", "Team vs Team", "Employee vs Team Average"]
        )
        
        if comparison_type == "Quarter-over-Quarter":
            # Quarter comparison
            quarters = data['assessment_quarter'].unique()
            if len(quarters) >= 2:
                col1, col2 = st.columns(2)
                with col1:
                    q1 = st.selectbox("Select First Quarter", sorted(quarters, reverse=True))
                with col2:
                    q2 = st.selectbox("Select Second Quarter", sorted(quarters, reverse=True))
                
                if q1 != q2:
                    q1_data = data[data['assessment_quarter'] == q1]
                    q2_data = data[data['assessment_quarter'] == q2]
                    
                    q1_scores = q1_data.groupby('name')['points'].sum().reset_index()
                    q2_scores = q2_data.groupby('name')['points'].sum().reset_index()
                    
                    comparison = pd.merge(
                        q1_scores,
                        q2_scores,
                        on='name',
                        suffixes=(f'_{q1}', f'_{q2}')
                    )
                    comparison['change'] = comparison[f'points_{q2}'] - comparison[f'points_{q1}']
                    comparison['change_pct'] = (comparison['change'] / comparison[f'points_{q1}']) * 100
                    
                    # Visualization
                    fig = px.scatter(
                        comparison,
                        x=f'points_{q1}',
                        y=f'points_{q2}',
                        hover_data=['name', 'change', 'change_pct'],
                        title=f"Quarter Comparison: {q1} vs {q2}",
                        labels={f'points_{q1}': f'{q1} Score', f'points_{q2}': f'{q2} Score'}
                    )
                    fig.add_line(x=[0, 100], y=[0, 100], line_dash="dash", line_color="gray")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show top improvers and decliners
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### 📈 Top Improvers")
                        top_improvers = comparison.nlargest(5, 'change_pct')[['name', 'change_pct']]
                        st.dataframe(top_improvers, hide_index=True)
                    with col2:
                        st.markdown("#### 📉 Needs Attention")
                        bottom = comparison.nsmallest(5, 'change_pct')[['name', 'change_pct']]
                        st.dataframe(bottom, hide_index=True)
            else:
                st.warning("Not enough quarters for comparison.")
        
        elif comparison_type == "Year-over-Year":
            # Year comparison
            years = data['assessment_year'].unique()
            if len(years) >= 2:
                col1, col2 = st.columns(2)
                with col1:
                    y1 = st.selectbox("Select First Year", sorted(years, reverse=True))
                with col2:
                    y2 = st.selectbox("Select Second Year", sorted(years, reverse=True))
                
                if y1 != y2:
                    y1_data = data[data['assessment_year'] == y1]
                    y2_data = data[data['assessment_year'] == y2]
                    
                    # Calculate yearly averages
                    y1_avg = y1_data.groupby('name')['points'].mean().mean()
                    y2_avg = y2_data.groupby('name')['points'].mean().mean()
                    
                    change = y2_avg - y1_avg
                    change_pct = (change / y1_avg) * 100
                    
                    # Display comparison
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"{y1} Average", f"{y1_avg:.2f}")
                    with col2:
                        st.metric(f"{y2} Average", f"{y2_avg:.2f}")
                    with col3:
                        st.metric("Change", f"{change:+.2f}", delta=f"{change_pct:+.1f}%")
            else:
                st.warning("Not enough years for comparison.")
        
        elif comparison_type == "Team vs Team":
            # Team comparison
            col1, col2 = st.columns(2)
            with col1:
                team1 = st.selectbox("Select First Team", TEAMS)
            with col2:
                team2 = st.selectbox("Select Second Team", TEAMS, index=1)
            
            if team1 != team2:
                period = st.selectbox("Select Period", sorted(data['assessment_period'].unique(), reverse=True))
                
                team1_data = data[(data['department'] == team1) & (data['assessment_period'] == period)]
                team2_data = data[(data['department'] == team2) & (data['assessment_period'] == period)]
                
                if not team1_data.empty and not team2_data.empty:
                    # Category comparison
                    team1_cat = team1_data.groupby('category')['points'].mean().reset_index()
                    team2_cat = team2_data.groupby('category')['points'].mean().reset_index()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(name=team1, x=team1_cat['category'], y=team1_cat['points']))
                    fig.add_trace(go.Bar(name=team2, x=team2_cat['category'], y=team2_cat['points']))
                    fig.update_layout(barmode='group', title=f"Team Comparison: {team1} vs {team2}")
                    st.plotly_chart(fig, use_container_width=True)
        
        elif comparison_type == "Employee vs Team Average":
            # Employee vs team comparison
            employee = st.selectbox("Select Employee", data['name'].unique())
            period = st.selectbox("Select Period", sorted(data['assessment_period'].unique(), reverse=True))
            
            emp_data = data[(data['name'] == employee) & (data['assessment_period'] == period)]
            if not emp_data.empty:
                emp_dept = emp_data['department'].iloc[0]
                team_data = data[(data['department'] == emp_dept) & 
                                (data['assessment_period'] == period)]
                
                # Calculate comparisons
                emp_score = emp_data['points'].sum()
                team_avg = team_data.groupby('name')['points'].sum().mean()
                
                # Display comparison
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Employee Score", f"{emp_score:.2f}")
                with col2:
                    st.metric("Team Average", f"{team_avg:.2f}")
                with col3:
                    diff = emp_score - team_avg
                    st.metric("Difference", f"{diff:+.2f}", 
                            delta="Above Average" if diff > 0 else "Below Average")

# ------------------------------------------------------------
# MANAGEMENT PAGE
# ------------------------------------------------------------
elif page == "⚙️ Management":
    st.header("⚙️ System Management")
    
    tab1, tab2, tab3 = st.tabs(["👥 Employee Management", "📊 Data Management", "⚙️ Settings"])
    
    with tab1:
        st.markdown("### Employee Management")
        
        employees = db.get_employees()
        if not employees.empty:
            st.dataframe(employees[['name', 'department', 'position']], use_container_width=True)
            
            # Delete employee
            st.markdown("#### Remove Employee")
            emp_to_delete = st.selectbox("Select Employee to Remove", employees['name'])
            if st.button("🗑️ Remove Employee", type="secondary"):
                if st.checkbox("I confirm I want to delete this employee and all their data"):
                    db.delete_employee(emp_to_delete)
                    st.success(f"Removed {emp_to_delete} from the system")
                    st.rerun()
        else:
            st.info("No employees in the system yet.")
    
    with tab2:
        st.markdown("### Data Management")
        
        # Export all data
        if st.button("📥 Export All Data"):
            all_data = db.fetch_assessments()
            if not all_data.empty:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    all_data.to_excel(writer, sheet_name='All Assessments', index=False)
                    employees = db.get_employees()
                    employees.to_excel(writer, sheet_name='Employees', index=False)
                
                st.download_button(
                    "Download Complete Database Export",
                    excel_buffer.getvalue(),
                    f"kpi_database_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Data statistics
        st.markdown("#### Database Statistics")
        data = db.fetch_assessments()
        if not data.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(data))
            with col2:
                st.metric("Unique Employees", data['name'].nunique())
            with col3:
                st.metric("Assessment Periods", data['assessment_period'].nunique())
            with col4:
                st.metric("Teams", data['department'].nunique())
    
    with tab3:
        st.markdown("### System Settings")
        st.info("System configuration options would go here in production version.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Zilla Clinicals KPI Management System v2.0 | Enhanced with Team & Company Analytics"
    "</div>",
    unsafe_allow_html=True
)