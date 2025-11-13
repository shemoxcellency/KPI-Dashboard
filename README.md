# KPI Management System

A comprehensive Streamlit-based application for managing, tracking, and analyzing employee KPI performance with automated scoring, visual dashboards, and detailed reporting capabilities.

## Features

### 📝 Data Entry
- **Employee Information Management**: Track employee ID, name, department, position, manager
- **KPI Assessment Input**: Easy-to-use interface for entering actual performance values
- **Automated Scoring**: Automatic calculation of status (Met/Partial/Not Met) and points earned
- **Real-time Feedback**: Instant visual feedback on performance status
- **Notes & Comments**: Add contextual notes for each KPI

### 📊 Automated Calculations
- **Status Determination**:
  - **Met**: ≥ Target value → 100% of KPI weight points
  - **Partial**: ≥ 50% of target → 50% of KPI weight points
  - **Not Met**: < 50% of target → 0 points
- **Category Scoring**: Automatic aggregation of KPI scores by category
- **Overall Performance Rating**: Comprehensive performance classification

### 📈 Visualizations
- **Radar Chart**: Category performance overview
- **KPI Breakdown Chart**: Individual KPI performance vs targets
- **Status Heatmap**: Visual representation of all KPI statuses
- **Distribution Analysis**: Score distribution across employees
- **Comparison Charts**: Team and department comparisons
- **Correlation Matrix**: Category performance correlations

### 💾 Data Management
- **SQLite Database**: Persistent storage of all assessments
- **Multiple Export Formats**:
  - CSV for data analysis
  - Excel with multiple sheets
  - JSON for data interchange
  - PDF reports for documentation
- **Import/Export**: Backup and restore functionality
- **Historical Tracking**: Maintain assessment history

### 📄 Reporting
- **Individual Reports**: Comprehensive PDF reports per employee
- **Team Analytics**: Department and team-level analysis
- **Recommendations Engine**: Automated improvement suggestions
- **Downloadable Reports**: All reports available for download

## Installation

1. **Clone or download the files**:
   ```bash
   # Create a new directory
   mkdir kpi-system
   cd kpi-system
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run kpi_management_system.py
   ```

4. **Access the application**:
   - The app will automatically open in your browser
   - Default URL: `http://localhost:8501`

## Usage Guide

### Step 1: Data Entry
1. Navigate to **📝 Data Entry** page
2. Enter employee information:
   - Employee ID (required)
   - Employee Name (required)
   - Department, Position, Manager (optional)
3. For each KPI category tab:
   - Enter actual performance values (0-100%)
   - System automatically calculates status and points
   - Add notes if needed
4. Review the overall summary
5. Click **💾 Save Assessment** to store the data
6. Download PDF report if needed

### Step 2: View Dashboard
1. Go to **📊 Dashboard** page
2. Select an employee from the dropdown
3. View performance visualizations:
   - Radar chart for category overview
   - Bar chart for KPI breakdown
   - Heatmap for status overview
   - Detailed data table
4. Export data in your preferred format

### Step 3: Team Analytics
1. Navigate to **👥 Employee Management**
2. View all employees in the system
3. Compare performance across team members
4. Analyze department-wise performance

### Step 4: Advanced Analytics
1. Go to **📈 Analytics** page
2. View aggregate statistics
3. Analyze score distributions
4. Review category correlations
5. Get automated recommendations

## KPI Categories & Weights

### Performance & Delivery (35%)
- Task Completion Rate (8.75 points)
- Quality of Output (8.75 points)
- Process Efficiency (8.75 points)
- Documentation & Compliance (8.75 points)

### Collaboration & Team Engagement (20%)
- Cross-Team Communication (5 points)
- Meeting Participation (5 points)
- Collaboration Quality (5 points)
- Team Morale Contribution (5 points)

### Ownership & Initiative (20%)
- Accountability (5 points)
- Problem Solving (5 points)
- Innovation & Continuous Improvement (5 points)
- Dependability Index (5 points)

### Learning & Growth (15%)
- Skill Advancement (3.75 points)
- Application of Learning (3.75 points)
- Growth Goal Achievement (3.75 points)
- Knowledge Sharing (3.75 points)

### Business & Impact Alignment (10%)
- Impact on KPIs (2.5 points)
- Customer/Stakeholder Feedback (2.5 points)
- Efficiency Contribution (2.5 points)
- Strategic Alignment (2.5 points)

## Performance Ratings

- **90-100%**: 🌟 Exceeds Expectations
- **80-89%**: ✅ Meets Expectations
- **70-79%**: ⚠️ Partially Meets
- **Below 70%**: ⚡ Needs Improvement

## Category Status

- **85%+**: 🟢 On Track
- **70-84%**: 🟡 Improve
- **Below 70%**: 🔴 Needs Attention

## Database Schema

The system uses SQLite with two main tables:

### Employees Table
- `employee_id` (Primary Key)
- `name`
- `department`
- `position`
- `manager`
- `created_at`

### Assessments Table
- `id` (Primary Key)
- `employee_id` (Foreign Key)
- `assessment_date`
- `quarter`
- `year`
- `category`
- `kpi_name`
- `actual_value`
- `status`
- `points_earned`
- `points_possible`
- `notes`
- `created_at`

## Tips for Best Results

1. **Regular Updates**: Enter KPI data monthly or quarterly for trend analysis
2. **Consistent Scoring**: Use the same evaluation criteria across all employees
3. **Add Context**: Use the notes field to provide context for scores
4. **Export Regularly**: Backup your data regularly using the export function
5. **Review Analytics**: Use the analytics page to identify patterns and improvement areas

## Troubleshooting

### Common Issues

1. **Application won't start**:
   - Ensure all packages are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ recommended)

2. **Charts not displaying**:
   - Refresh the browser page
   - Clear browser cache
   - Check if data is properly saved

3. **Export not working**:
   - Ensure you have write permissions in the directory
   - Check available disk space

4. **Database errors**:
   - The system creates `kpi_database.db` automatically
   - If corrupted, delete the file to start fresh

## Future Enhancements

Potential improvements for future versions:
- Email notifications for assessments
- Role-based access control
- API integration for automated data import
- Predictive analytics for performance trends
- Mobile-responsive design
- Multi-language support
- Custom KPI templates
- Automated report scheduling

## Support

For issues or questions, please ensure you have:
1. Latest version of Streamlit
2. All required packages installed
3. Sufficient permissions for file operations
4. Modern web browser (Chrome, Firefox, Safari, Edge)

## License

This KPI Management System is provided as-is for organizational use.

---

**Version**: 1.0
**Last Updated**: November 2024