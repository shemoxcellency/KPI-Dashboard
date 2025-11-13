"""
Employee KPI Management System
A comprehensive Streamlit application for KPI tracking, scoring, and visualization
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime, date
import io
import base64
from pathlib import Path
import sqlite3
import hashlib

# Page configuration
st.set_page_config(
    page_title="KPI Management System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3a8a;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #e0f2fe 0%, #f0f9ff 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: green;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-met { color: #10b981; font-weight: bold; }
    .status-partial { color: #f59e0b; font-weight: bold; }
    .status-not-met { color: #ef4444; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'employees_data' not in st.session_state:
    st.session_state.employees_data = {}
if 'current_assessment' not in st.session_state:
    st.session_state.current_assessment = {}
if 'assessment_date' not in st.session_state:
    st.session_state.assessment_date = date.today()

# KPI Structure Definition
KPI_STRUCTURE = {
    "Performance & Delivery": {
        "weight": 35,
        "kpis": [
            {
                "name": "Task Completion Rate",
                "description": "Percentage of assigned tasks completed within agreed timelines",
                "measurement": "(# completed on time ÷ total assigned) × 100",
                "target": "≥ 90%",
                "target_value": 90,
                "weight": 8.75
            },
            {
                "name": "Quality of Output",
                "description": "Accuracy, attention to detail, and adherence to standards",
                "measurement": "% of work approved without revisions",
                "target": "≥ 95%",
                "target_value": 95,
                "weight": 8.75
            },
            {
                "name": "Process Efficiency",
                "description": "Ability to complete tasks with minimal rework",
                "measurement": "# of reworks per project or task",
                "target": "≤ 10%",
                "target_value": 90,  # Inverse metric
                "weight": 8.75
            },
            {
                "name": "Documentation & Compliance",
                "description": "Following team processes, SOPs, and file protocols",
                "measurement": "Audit or lead review",
                "target": "Full compliance",
                "target_value": 100,
                "weight": 8.75
            }
        ]
    },
    "Collaboration & Team Engagement": {
        "weight": 20,
        "kpis": [
            {
                "name": "Cross-Team Communication",
                "description": "Timely, professional interaction with colleagues and other teams",
                "measurement": "Peer feedback survey",
                "target": "≥ 4/5",
                "target_value": 80,
                "weight": 5
            },
            {
                "name": "Meeting Participation",
                "description": "Attendance and constructive contribution in meetings",
                "measurement": "Attendance record + feedback",
                "target": "≥ 90% participation",
                "target_value": 90,
                "weight": 5
            },
            {
                "name": "Collaboration Quality",
                "description": "How effectively the member works with others to achieve shared goals",
                "measurement": "360° feedback",
                "target": "Positive trend",
                "target_value": 80,
                "weight": 5
            },
            {
                "name": "Team Morale Contribution",
                "description": "Proactive positivity, mentorship, or support of peers",
                "measurement": "Peer/lead feedback",
                "target": "Demonstrated contribution",
                "target_value": 80,
                "weight": 5
            }
        ]
    },
    "Ownership & Initiative": {
        "weight": 20,
        "kpis": [
            {
                "name": "Accountability",
                "description": "Consistency in following through on commitments",
                "measurement": "Manager review + peer inputs",
                "target": "Consistent accountability",
                "target_value": 85,
                "weight": 5
            },
            {
                "name": "Problem Solving",
                "description": "Identifies and resolves issues proactively",
                "measurement": "# of issues resolved without escalation",
                "target": "≥ 80%",
                "target_value": 80,
                "weight": 5
            },
            {
                "name": "Innovation & Continuous Improvement",
                "description": "Suggestions, ideas, or efficiencies introduced",
                "measurement": "# of improvements suggested or implemented",
                "target": "≥ 1 per quarter",
                "target_value": 75,
                "weight": 5
            },
            {
                "name": "Dependability Index",
                "description": "Reliability under deadlines or pressure",
                "measurement": "Lead assessment",
                "target": "Above Average",
                "target_value": 85,
                "weight": 5
            }
        ]
    },
    "Learning & Growth": {
        "weight": 15,
        "kpis": [
            {
                "name": "Skill Advancement",
                "description": "Participation in internal/external learning activities",
                "measurement": "# of trainings, courses, or certifications completed",
                "target": "≥ 1 per quarter",
                "target_value": 100,
                "weight": 3.75
            },
            {
                "name": "Application of Learning",
                "description": "Using new skills in actual work scenarios",
                "measurement": "Evidence of application in deliverables",
                "target": "Demonstrated improvement",
                "target_value": 80,
                "weight": 3.75
            },
            {
                "name": "Growth Goal Achievement",
                "description": "Progress toward individual development plans",
                "measurement": "% of personal goals met",
                "target": "≥ 80%",
                "target_value": 80,
                "weight": 3.75
            },
            {
                "name": "Knowledge Sharing",
                "description": "Teaching or mentoring others on new skills",
                "measurement": "# of sessions, guides, or shared learnings",
                "target": "≥ 1 per quarter",
                "target_value": 100,
                "weight": 3.75
            }
        ]
    },
    "Business & Impact Alignment": {
        "weight": 10,
        "kpis": [
            {
                "name": "Impact on KPIs",
                "description": "Contribution to key company/team metrics",
                "measurement": "Direct link to department KPIs",
                "target": "Documented alignment",
                "target_value": 85,
                "weight": 2.5
            },
            {
                "name": "Customer or Stakeholder Feedback",
                "description": "External feedback on professionalism, quality, or communication",
                "measurement": "Client or stakeholder rating",
                "target": "≥ 4/5",
                "target_value": 80,
                "weight": 2.5
            },
            {
                "name": "Efficiency Contribution",
                "description": "Ideas or efforts that saved time, cost, or resources",
                "measurement": "Quantified impact or manager validation",
                "target": "≥ 1 measurable improvement/quarter",
                "target_value": 75,
                "weight": 2.5
            },
            {
                "name": "Strategic Alignment",
                "description": "Understanding and acting in line with company goals",
                "measurement": "Leadership evaluation",
                "target": "Strong alignment",
                "target_value": 85,
                "weight": 2.5
            }
        ]
    }
}

class KPIDatabase:
    """Database handler for KPI data persistence"""
    
    def __init__(self):
        self.conn = sqlite3.connect('kpi_database.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create necessary database tables"""
        cursor = self.conn.cursor()
        
        # Employees table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT,
                position TEXT,
                manager TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # KPI Assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                assessment_date DATE NOT NULL,
                quarter TEXT,
                year INTEGER,
                category TEXT NOT NULL,
                kpi_name TEXT NOT NULL,
                actual_value REAL,
                status TEXT,
                points_earned REAL,
                points_possible REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
        ''')
        
        self.conn.commit()
    
    def save_employee(self, employee_data):
        """Save or update employee information"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO employees (employee_id, name, department, position, manager)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            employee_data['employee_id'],
            employee_data['name'],
            employee_data.get('department', ''),
            employee_data.get('position', ''),
            employee_data.get('manager', '')
        ))
        self.conn.commit()
    
    def save_assessment(self, assessment_data):
        """Save KPI assessment data"""
        cursor = self.conn.cursor()
        for record in assessment_data:
            cursor.execute('''
                INSERT INTO assessments 
                (employee_id, assessment_date, quarter, year, category, kpi_name, 
                 actual_value, status, points_earned, points_possible, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', record)
        self.conn.commit()
    
    def get_employee_data(self, employee_id):
        """Retrieve employee assessment data"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM assessments 
            WHERE employee_id = ? 
            ORDER BY assessment_date DESC
        ''', (employee_id,))
        return cursor.fetchall()
    
    def get_all_employees(self):
        """Get list of all employees"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM employees ORDER BY name')
        return cursor.fetchall()

# Initialize database
db = KPIDatabase()

def calculate_status_and_points(actual_value, target_value, kpi_weight):
    """Calculate status and points earned based on actual vs target"""
    if actual_value >= target_value:
        status = "Met"
        points = kpi_weight
    elif actual_value >= target_value * 0.5:
        status = "Partial"
        points = kpi_weight * 0.5
    else:
        status = "Not Met"
        points = 0
    return status, points

def get_category_status(earned, possible):
    """Determine category status based on points earned"""
    percentage = (earned / possible) * 100
    if percentage >= 85:
        return "On Track", "🟢"
    elif percentage >= 70:
        return "Improve", "🟡"
    else:
        return "Needs Attention", "🔴"

def get_overall_rating(score):
    """Determine overall performance rating"""
    if score >= 90:
        return "Exceeds Expectations", "🌟"
    elif score >= 80:
        return "Meets Expectations", "✅"
    elif score >= 70:
        return "Partially Meets", "⚠️"
    else:
        return "Needs Improvement", "⚡"

def create_radar_chart(data):
    """Create a radar chart for category scores"""
    categories = list(data.keys())
    scores = [data[cat]['percentage'] for cat in categories]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Performance',
        line_color='rgba(59, 130, 246, 0.8)',
        fillcolor='rgba(59, 130, 246, 0.3)'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[85] * len(categories),  # Target line at 85%
        theta=categories,
        name='Target',
        line_color='rgba(239, 68, 68, 0.5)',
        line_dash='dash'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix='%'
            )
        ),
        showlegend=True,
        title="Category Performance Overview",
        height=500
    )
    
    return fig

def create_kpi_breakdown_chart(assessment_data):
    """Create a detailed KPI breakdown chart"""
    kpi_names = []
    actual_values = []
    target_values = []
    colors = []
    
    for category, cat_data in assessment_data.items():
        for kpi in cat_data['kpis']:
            kpi_names.append(f"{kpi['name'][:30]}...")
            actual_values.append(kpi['actual_value'])
            target_values.append(kpi['target_value'])
            
            if kpi['status'] == 'Met':
                colors.append('green')
            elif kpi['status'] == 'Partial':
                colors.append('orange')
            else:
                colors.append('red')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Actual',
        x=kpi_names,
        y=actual_values,
        marker_color=colors,
        text=[f"{v:.1f}%" for v in actual_values],
        textposition='outside'
    ))
    
    fig.add_trace(go.Scatter(
        name='Target',
        x=kpi_names,
        y=target_values,
        mode='markers',
        marker=dict(size=10, symbol='line-ew', color='red', line=dict(width=3))
    ))
    
    fig.update_layout(
        title="Individual KPI Performance",
        xaxis_title="KPIs",
        yaxis_title="Score (%)",
        xaxis_tickangle=-45,
        height=600,
        showlegend=True,
        yaxis=dict(range=[0, 110])
    )
    
    return fig

def create_heatmap(assessment_data):
    """Create a heatmap showing status across all KPIs"""
    categories = []
    kpis = []
    statuses = []
    
    status_map = {'Met': 2, 'Partial': 1, 'Not Met': 0}
    
    for category, cat_data in assessment_data.items():
        for kpi in cat_data['kpis']:
            categories.append(category[:20])
            kpis.append(kpi['name'][:25])
            statuses.append(status_map[kpi['status']])
    
    # Reshape data for heatmap
    unique_cats = list(dict.fromkeys(categories))
    unique_kpis = list(dict.fromkeys(kpis))
    
    matrix = []
    for kpi in unique_kpis:
        row = []
        for cat in unique_cats:
            try:
                idx = [i for i, (c, k) in enumerate(zip(categories, kpis)) if c == cat and k == kpi][0]
                row.append(statuses[idx])
            except:
                row.append(-1)
        matrix.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=unique_cats,
        y=unique_kpis,
        colorscale=[[0, 'red'], [0.5, 'orange'], [1, 'green']],
        showscale=False,
        text=[['Not Met', 'Partial', 'Met'][int(val)] if val >= 0 else '' for row in matrix for val in row],
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title="KPI Status Heatmap",
        xaxis_title="Categories",
        yaxis_title="KPIs",
        height=800
    )
    
    return fig

def generate_pdf_report(employee_data, assessment_data):
    """Generate a comprehensive PDF report"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=30
    )
    
    elements.append(Paragraph("KPI Performance Report", title_style))
    elements.append(Spacer(1, 20))
    
    # Employee Information
    emp_info = [
        ['Employee Information', ''],
        ['Name:', employee_data['name']],
        ['Employee ID:', employee_data['employee_id']],
        ['Department:', employee_data.get('department', 'N/A')],
        ['Assessment Date:', str(employee_data.get('assessment_date', date.today()))]
    ]
    
    emp_table = Table(emp_info, colWidths=[2*inch, 4*inch])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#e0f2fe')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    
    elements.append(emp_table)
    elements.append(Spacer(1, 30))
    
    # Summary Scores
    summary_data = [['Category', 'Weight', 'Points Earned', 'Max Points', 'Percentage', 'Status']]
    
    total_earned = 0
    total_possible = 100
    
    for category, cat_data in assessment_data.items():
        earned = cat_data['points_earned']
        possible = cat_data['points_possible']
        percentage = cat_data['percentage']
        status = cat_data['status']
        
        total_earned += earned
        
        summary_data.append([
            category,
            f"{possible}%",
            f"{earned:.2f}",
            f"{possible}",
            f"{percentage:.1f}%",
            status
        ])
    
    summary_data.append([
        'TOTAL',
        '100%',
        f"{total_earned:.2f}",
        '100',
        f"{total_earned:.1f}%",
        get_overall_rating(total_earned)[0]
    ])
    
    summary_table = Table(summary_data, colWidths=[2*inch, 0.8*inch, 1*inch, 0.9*inch, 1*inch, 1.3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fef3c7')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    
    elements.append(Paragraph("Performance Summary", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(summary_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def main():
    st.markdown("<h1 class='main-header'>🎯 KPI Management System</h1>", unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["📝 Data Entry", "📊 Dashboard", "👥 Employee Management", "📈 Analytics", "⚙️ Settings"]
    )
    
    if page == "📝 Data Entry":
        st.header("KPI Assessment Data Entry")
        
        # Employee Information Section
        col1, col2, col3 = st.columns(3)
        
        with col1:
            employee_id = st.text_input("Employee ID*", key="emp_id")
            department = st.selectbox(
                "Department",
                ["Data Manager", "Programming"]
            )
        
        with col2:
            employee_name = st.text_input("Employee Name*", key="emp_name")
            position = st.text_input("Position")
        
        with col3:
            assessment_date = st.date_input("Assessment Date", value=date.today())
            manager = st.text_input("Manager")
        
        st.markdown("---")
        
        if employee_id and employee_name:
            # Initialize assessment data
            assessment_data = {}
            
            # Create tabs for each category
            category_tabs = st.tabs(list(KPI_STRUCTURE.keys()))
            
            for idx, (category, cat_data) in enumerate(KPI_STRUCTURE.items()):
                with category_tabs[idx]:
                    st.subheader(f"{category} (Weight: {cat_data['weight']}%)")
                    
                    category_assessment = {
                        'weight': cat_data['weight'],
                        'kpis': [],
                        'points_earned': 0,
                        'points_possible': cat_data['weight']
                    }
                    
                    # Display KPIs in this category
                    for kpi_idx, kpi in enumerate(cat_data['kpis']):
                        st.markdown(f"### {kpi['name']}")
                        
                        col1, col2, col3 = st.columns([2, 1, 2])
                        
                        with col1:
                            st.caption(f"📋 {kpi['description']}")
                            st.caption(f"📏 Measurement: {kpi['measurement']}")
                            st.caption(f"🎯 Target: {kpi['target']}")
                        
                        with col2:
                            actual_value = st.number_input(
                                "Actual Value (%)",
                                min_value=0.0,
                                max_value=100.0,
                                value=50.0,
                                step=5.0,
                                key=f"{category}_{kpi_idx}_actual"
                            )
                        
                        with col3:
                            # Calculate status and points
                            status, points = calculate_status_and_points(
                                actual_value, 
                                kpi['target_value'], 
                                kpi['weight']
                            )
                            
                            if status == "Met":
                                st.success(f"✅ Status: {status}")
                            elif status == "Partial":
                                st.warning(f"⚠️ Status: {status}")
                            else:
                                st.error(f"❌ Status: {status}")
                            
                            st.info(f"Points: {points:.2f} / {kpi['weight']}")
                        
                        # Notes field
                        notes = st.text_area(
                            "Notes (optional)",
                            key=f"{category}_{kpi_idx}_notes",
                            height=70
                        )
                        
                        # Store KPI assessment
                        category_assessment['kpis'].append({
                            'name': kpi['name'],
                            'actual_value': actual_value,
                            'target_value': kpi['target_value'],
                            'status': status,
                            'points_earned': points,
                            'points_possible': kpi['weight'],
                            'notes': notes
                        })
                        
                        category_assessment['points_earned'] += points
                        
                        st.markdown("---")
                    
                    # Category Summary
                    category_assessment['percentage'] = (
                        category_assessment['points_earned'] / 
                        category_assessment['points_possible']
                    ) * 100
                    
                    status_text, icon = get_category_status(
                        category_assessment['points_earned'],
                        category_assessment['points_possible']
                    )
                    category_assessment['status'] = status_text
                    
                    st.markdown(f"### Category Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Points Earned",
                            f"{category_assessment['points_earned']:.2f}",
                            f"/ {category_assessment['points_possible']}"
                        )
                    with col2:
                        st.metric(
                            "Percentage",
                            f"{category_assessment['percentage']:.1f}%"
                        )
                    with col3:
                        st.markdown(f"### {icon} {status_text}")
                    
                    assessment_data[category] = category_assessment
            
            # Overall Summary Section
            st.markdown("---")
            st.header("📊 Overall Assessment Summary")
            
            # Calculate totals
            total_earned = sum(cat['points_earned'] for cat in assessment_data.values())
            total_possible = 100
            overall_percentage = total_earned
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Score", f"{total_earned:.2f}", f"/ {total_possible}")
            
            with col2:
                st.metric("Percentage", f"{overall_percentage:.1f}%")
            
            with col3:
                rating, icon = get_overall_rating(overall_percentage)
                st.markdown(f"### {icon}")
                st.markdown(f"**{rating}**")
            
            with col4:
                if st.button("💾 Save Assessment", type="primary", use_container_width=True):
                    # Prepare data for database
                    employee_data = {
                        'employee_id': employee_id,
                        'name': employee_name,
                        'department': department,
                        'position': position,
                        'manager': manager,
                        'assessment_date': assessment_date
                    }
                    
                    # Save to database
                    db.save_employee(employee_data)
                    
                    # Prepare assessment records
                    assessment_records = []
                    quarter = f"Q{(assessment_date.month - 1) // 3 + 1}"
                    year = assessment_date.year
                    
                    for category, cat_data in assessment_data.items():
                        for kpi in cat_data['kpis']:
                            assessment_records.append((
                                employee_id,
                                assessment_date,
                                quarter,
                                year,
                                category,
                                kpi['name'],
                                kpi['actual_value'],
                                kpi['status'],
                                kpi['points_earned'],
                                kpi['points_possible'],
                                kpi['notes']
                            ))
                    
                    db.save_assessment(assessment_records)
                    
                    # Store in session state
                    st.session_state.employees_data[employee_id] = {
                        'info': employee_data,
                        'assessment': assessment_data,
                        'total_score': total_earned,
                        'rating': rating
                    }
                    
                    st.success("✅ Assessment saved successfully!")
                    
                    # Generate PDF option
                    pdf_buffer = generate_pdf_report(employee_data, assessment_data)
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name=f"KPI_Report_{employee_id}_{assessment_date}.pdf",
                        mime="application/pdf"
                    )
    
    elif page == "📊 Dashboard":
        st.header("KPI Dashboard")
        
        if st.session_state.employees_data:
            # Employee selector
            employee_ids = list(st.session_state.employees_data.keys())
            selected_emp = st.selectbox("Select Employee", employee_ids)
            
            if selected_emp:
                emp_data = st.session_state.employees_data[selected_emp]
                emp_info = emp_data['info']
                assessment = emp_data['assessment']
                
                # Display employee info
                st.subheader(f"Dashboard for {emp_info['name']}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Employee ID", emp_info['employee_id'])
                with col2:
                    st.metric("Department", emp_info['department'])
                with col3:
                    st.metric("Total Score", f"{emp_data['total_score']:.1f}%")
                with col4:
                    st.metric("Rating", emp_data['rating'])
                
                # Visualizations
                tab1, tab2, tab3, tab4 = st.tabs(["Radar Chart", "KPI Breakdown", "Status Heatmap", "Data Table"])
                
                with tab1:
                    fig_radar = create_radar_chart(assessment)
                    st.plotly_chart(fig_radar, use_container_width=True)
                
                with tab2:
                    fig_breakdown = create_kpi_breakdown_chart(assessment)
                    st.plotly_chart(fig_breakdown, use_container_width=True)
                
                with tab3:
                    fig_heatmap = create_heatmap(assessment)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                
                with tab4:
                    # Create detailed data table
                    table_data = []
                    for category, cat_data in assessment.items():
                        for kpi in cat_data['kpis']:
                            table_data.append({
                                'Category': category,
                                'KPI': kpi['name'],
                                'Target': kpi['target_value'],
                                'Actual': kpi['actual_value'],
                                'Status': kpi['status'],
                                'Points Earned': kpi['points_earned'],
                                'Max Points': kpi['points_possible']
                            })
                    
                    df = pd.DataFrame(table_data)
                    
                    # Apply styling
                    def color_status(val):
                        if val == 'Met':
                            return 'background-color: #d4edda'
                        elif val == 'Partial':
                            return 'background-color: #fff3cd'
                        else:
                            return 'background-color: #f8d7da'
                    
                    styled_df = df.style.applymap(color_status, subset=['Status'])
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Export options
                    st.markdown("### Export Options")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"kpi_data_{selected_emp}_{date.today()}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        json_data = json.dumps(assessment, indent=2)
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_data,
                            file_name=f"kpi_data_{selected_emp}_{date.today()}.json",
                            mime="application/json"
                        )
                    
                    with col3:
                        # Excel export
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, sheet_name='KPI Data', index=False)
                            
                            # Add summary sheet
                            summary_df = pd.DataFrame([{
                                'Employee': emp_info['name'],
                                'ID': emp_info['employee_id'],
                                'Department': emp_info['department'],
                                'Total Score': emp_data['total_score'],
                                'Rating': emp_data['rating']
                            }])
                            summary_df.to_excel(writer, sheet_name='Summary', index=False)
                        
                        output.seek(0)
                        st.download_button(
                            label="📥 Download Excel",
                            data=output.getvalue(),
                            file_name=f"kpi_report_{selected_emp}_{date.today()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        else:
            st.info("No assessment data available. Please enter data in the Data Entry page first.")
    
    elif page == "👥 Employee Management":
        st.header("Employee Management")
        
        # Get all employees from database
        employees = db.get_all_employees()
        
        if employees:
            st.subheader("Employee List")
            
            # Convert to DataFrame for display
            emp_df = pd.DataFrame(
                employees,
                columns=['ID', 'Employee ID', 'Name', 'Department', 'Position', 'Manager', 'Created At']
            )
            emp_df = emp_df.drop('ID', axis=1)
            
            st.dataframe(emp_df, use_container_width=True)
            
            # Bulk comparison
            st.subheader("Employee Comparison")
            
            if st.session_state.employees_data:
                comparison_data = []
                for emp_id, emp_data in st.session_state.employees_data.items():
                    comparison_data.append({
                        'Employee': emp_data['info']['name'],
                        'Department': emp_data['info']['department'],
                        'Total Score': emp_data['total_score'],
                        'Rating': emp_data['rating']
                    })
                
                comp_df = pd.DataFrame(comparison_data)
                
                # Bar chart comparison
                fig = px.bar(
                    comp_df, 
                    x='Employee', 
                    y='Total Score',
                    color='Rating',
                    title='Employee Performance Comparison',
                    color_discrete_map={
                        'Exceeds Expectations': '#10b981',
                        'Meets Expectations': '#3b82f6',
                        'Partially Meets': '#f59e0b',
                        'Needs Improvement': '#ef4444'
                    }
                )
                fig.add_hline(y=85, line_dash="dash", line_color="red", 
                            annotation_text="Target (85%)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Department analysis
                if len(comp_df) > 0:
                    dept_avg = comp_df.groupby('Department')['Total Score'].mean().reset_index()
                    
                    fig_dept = px.pie(
                        dept_avg,
                        values='Total Score',
                        names='Department',
                        title='Department Average Performance'
                    )
                    st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("No employees in the database yet.")
    
    elif page == "📈 Analytics":
        st.header("Advanced Analytics")
        
        if st.session_state.employees_data:
            # Aggregate analytics
            all_scores = [emp['total_score'] for emp in st.session_state.employees_data.values()]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Average Score", f"{np.mean(all_scores):.1f}%")
            
            with col2:
                st.metric("Highest Score", f"{np.max(all_scores):.1f}%")
            
            with col3:
                st.metric("Lowest Score", f"{np.min(all_scores):.1f}%")
            
            with col4:
                above_target = sum(1 for s in all_scores if s >= 85)
                st.metric("Above Target", f"{above_target}/{len(all_scores)}")
            
            # Distribution plot
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=all_scores,
                nbinsx=20,
                name='Score Distribution',
                marker_color='rgba(59, 130, 246, 0.7)'
            ))
            fig_dist.add_vline(x=85, line_dash="dash", line_color="red",
                             annotation_text="Target")
            fig_dist.update_layout(
                title='Score Distribution',
                xaxis_title='Score (%)',
                yaxis_title='Number of Employees',
                height=400
            )
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Category-wise analysis
            st.subheader("Category Analysis Across All Employees")
            
            category_scores = {cat: [] for cat in KPI_STRUCTURE.keys()}
            
            for emp_data in st.session_state.employees_data.values():
                for category, cat_data in emp_data['assessment'].items():
                    category_scores[category].append(cat_data['percentage'])
            
            # Box plot for category performance
            box_data = []
            for category, scores in category_scores.items():
                for score in scores:
                    box_data.append({'Category': category, 'Score': score})
            
            box_df = pd.DataFrame(box_data)
            
            fig_box = px.box(
                box_df,
                x='Category',
                y='Score',
                title='Category Performance Distribution',
                color='Category'
            )
            fig_box.add_hline(y=85, line_dash="dash", line_color="red")
            st.plotly_chart(fig_box, use_container_width=True)
            
            # Correlation matrix
            st.subheader("Category Correlation Matrix")
            
            if len(st.session_state.employees_data) > 2:
                corr_data = []
                for emp_data in st.session_state.employees_data.values():
                    emp_scores = {}
                    for category, cat_data in emp_data['assessment'].items():
                        emp_scores[category[:15]] = cat_data['percentage']
                    corr_data.append(emp_scores)
                
                corr_df = pd.DataFrame(corr_data)
                correlation = corr_df.corr()
                
                fig_corr = go.Figure(data=go.Heatmap(
                    z=correlation.values,
                    x=correlation.columns,
                    y=correlation.columns,
                    colorscale='RdBu',
                    zmid=0,
                    text=np.round(correlation.values, 2),
                    texttemplate='%{text}',
                    textfont={"size": 10}
                ))
                fig_corr.update_layout(
                    title='Category Performance Correlation',
                    height=500
                )
                st.plotly_chart(fig_corr, use_container_width=True)
            
            # Recommendations engine
            st.subheader("🎯 Improvement Recommendations")
            
            for emp_id, emp_data in st.session_state.employees_data.items():
                with st.expander(f"Recommendations for {emp_data['info']['name']}"):
                    weak_areas = []
                    for category, cat_data in emp_data['assessment'].items():
                        if cat_data['percentage'] < 70:
                            weak_kpis = [
                                kpi['name'] for kpi in cat_data['kpis'] 
                                if kpi['status'] in ['Partial', 'Not Met']
                            ]
                            weak_areas.append({
                                'Category': category,
                                'Score': cat_data['percentage'],
                                'Weak KPIs': weak_kpis
                            })
                    
                    if weak_areas:
                        for area in weak_areas:
                            st.warning(f"**{area['Category']}** (Score: {area['Score']:.1f}%)")
                            st.write("Focus areas:")
                            for kpi in area['Weak KPIs']:
                                st.write(f"  • {kpi}")
                    else:
                        st.success("Great performance! Continue maintaining high standards.")
        else:
            st.info("No data available for analytics. Please add employee assessments first.")
    
    elif page == "⚙️ Settings":
        st.header("Settings & Configuration")
        
        st.subheader("Export/Import Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Export All Data")
            if st.button("Export to JSON"):
                all_data = {
                    'employees': st.session_state.employees_data,
                    'export_date': str(datetime.now()),
                    'version': '1.0'
                }
                json_str = json.dumps(all_data, indent=2, default=str)
                st.download_button(
                    label="📥 Download Complete Dataset",
                    data=json_str,
                    file_name=f"kpi_complete_data_{date.today()}.json",
                    mime="application/json"
                )
        
        with col2:
            st.markdown("### Import Data")
            uploaded_file = st.file_uploader("Choose a JSON file", type="json")
            if uploaded_file is not None:
                data = json.loads(uploaded_file.read())
                st.session_state.employees_data = data.get('employees', {})
                st.success("Data imported successfully!")
                st.rerun()
        
        st.subheader("Clear Data")
        st.warning("⚠️ This action cannot be undone!")
        if st.button("Clear All Data", type="secondary"):
            st.session_state.employees_data = {}
            st.success("All data cleared!")
            st.rerun()
        
        st.subheader("About")
        st.info("""
        **KPI Management System v1.0**
        
        A comprehensive tool for managing and tracking employee KPIs with:
        - Automated scoring and status calculation
        - Visual dashboards and analytics
        - PDF report generation
        - Data export in multiple formats
        - Historical tracking and comparison
        
        © 2024 - Built with Streamlit
        """)

if __name__ == "__main__":
    main()