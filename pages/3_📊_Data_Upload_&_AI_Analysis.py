import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
import os
import numpy as np
import io

# Add parent directory to import path for direct running
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the AI assistant module
from ai_assistant import generate_ai_insight_from_data
from utils.custom_data_processor import process_custom_data

# Page config
st.set_page_config(
    page_title="San Jose Safe Commute | Data Upload & AI Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom sidebar with navigation
with st.sidebar:
    st.title("San Jose Safe Commute")
    st.markdown("---")
    
    # Navigation links section
    st.page_link("1_🏠_Home.py", label="Home", icon="🏠")
    st.page_link("pages/2_📊_Analytics_Dashboard.py", label="Analytics Dashboard", icon="📊")
    st.page_link("pages/3_🔍_Crash_Data_Analysis.py", label="Crash Data Analysis", icon="🔍")
    st.page_link("pages/3_📊_Data_Upload_&_AI_Analysis.py", label="Upload & AI Analysis", icon="📊")

# Custom CSS
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .insight-box {
        background-color: #f0f7ff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 5px solid #0068c9;
    }
    .ai-badge {
        background-color: #8e44ad;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-left: 0.5rem;
    }
    .upload-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px dashed #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for uploaded data
if 'uploaded_data' not in st.session_state:
    st.session_state['uploaded_data'] = None
    
if 'processed_data' not in st.session_state:
    st.session_state['processed_data'] = None
    
if 'data_stats' not in st.session_state:
    st.session_state['data_stats'] = None
    
if 'data_insights' not in st.session_state:
    st.session_state['data_insights'] = None

# Title and explanation
st.title("📊 Data Upload & AI Analysis")
st.markdown("""
<div style="display: flex; align-items: center;">
    <h3>Upload Your Own Data for AI-Powered Safety Analysis</h3>
    <span class="ai-badge">AI Enhanced</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
This tool allows you to upload your own traffic or safety-related dataset and get AI-powered insights.
Our system will analyze your data to identify patterns, risk factors, and safety recommendations.

**Supported file formats:** CSV, Excel (.xlsx)

**Recommended data fields:** 
- Incident date/time
- Location information (address, latitude/longitude)
- Severity or impact metrics
- Weather or environmental conditions
- Traffic conditions or factors
""")

# File upload section
st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
st.subheader("📤 Upload Your Data")

uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Read the file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # Display raw data preview
        st.subheader("📋 Raw Data Preview")
        st.dataframe(df.head(5), use_container_width=True)
        
        # Allow column mapping
        st.subheader("🔄 Map Your Data Fields")
        st.markdown("To get the best analysis, map your data columns to our standard fields:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            date_col = st.selectbox("Date/Time Column", options=[None] + list(df.columns), 
                                  help="Column containing the date or time of incidents")
            
            location_col = st.selectbox("Location Column", options=[None] + list(df.columns),
                                      help="Column containing location information")
            
            severity_col = st.selectbox("Severity Column", options=[None] + list(df.columns),
                                      help="Column indicating incident severity or impact")
        
        with col2:
            weather_col = st.selectbox("Weather Column (optional)", options=[None] + list(df.columns),
                                     help="Column with weather or environmental information")
            
            factor_col = st.selectbox("Contributing Factor Column (optional)", options=[None] + list(df.columns),
                                    help="Column with information about contributing factors")
            
            time_col = st.selectbox("Time Column (if separate from date)", options=[None] + list(df.columns),
                                  help="Column containing just the time if it's separate from the date")
            
        # Process button
        if st.button("Process Data for Analysis", type="primary"):
            if date_col is None and location_col is None:
                st.error("Please select at least a Date or Location column to continue.")
            else:
                # Create column mapping
                column_mapping = {
                    "date": date_col,
                    "location": location_col,
                    "severity": severity_col,
                    "weather": weather_col,
                    "factor": factor_col,
                    "time": time_col
                }
                
                # Process with custom data processor
                with st.spinner("Processing your data with AI analysis..."):
                    try:
                        processed_df, stats = process_custom_data(df, column_mapping)
                        
                        # Store in session state
                        st.session_state['uploaded_data'] = df
                        st.session_state['processed_data'] = processed_df
                        st.session_state['data_stats'] = stats
                        
                        # Generate AI insights
                        st.session_state['data_insights'] = generate_ai_insight_from_data(processed_df, stats, custom_data=True)
                        
                        st.success("✅ Data processed successfully! Scroll down to see the analysis.")
                    except Exception as e:
                        st.error(f"Error processing data: {str(e)}")
        
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# Display analysis if data is processed
if st.session_state['processed_data'] is not None:
    df = st.session_state['processed_data']
    original_df = st.session_state['uploaded_data']
    stats = st.session_state['data_stats']
    
    # Display data summary
    st.markdown("---")
    st.subheader("📈 Data Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", f"{stats.get('total_incidents', 0):,}")
    with col2:
        date_range = stats.get('date_range', "Not available")
        st.metric("Date Range", date_range)
    with col3:
        avg_per_month = stats.get('avg_monthly', 0)
        st.metric("Avg. Monthly", f"{avg_per_month:,.1f}")
    
    # Display AI insights
    if st.session_state['data_insights']:
        st.markdown("### 🧠 AI-Generated Insights")
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        
        for insight in st.session_state['data_insights']:
            st.markdown(f"✨ {insight}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["📊 Data Overview", "📈 Trend Analysis", "🔍 Detailed Breakdown"])
    
    with tab1:
        st.subheader("Data Overview")
        
        # Distribution plots based on available data
        if 'severity' in df.columns and not df['severity'].isna().all():
            st.markdown("### Severity Distribution")
            severity_counts = df['severity'].value_counts().reset_index()
            severity_counts.columns = ['Severity', 'Count']
            
            fig = px.pie(severity_counts, names='Severity', values='Count',
                        title='Distribution by Severity Level')
            st.plotly_chart(fig, use_container_width=True)
        
        # Time of day distribution if available
        if 'hour' in df.columns and not df['hour'].isna().all():
            st.markdown("### Time of Day Distribution")
            hour_counts = df['hour'].value_counts().sort_index().reset_index()
            hour_counts.columns = ['Hour', 'Count']
            
            fig = px.bar(hour_counts, x='Hour', y='Count',
                       title='Incidents by Hour of Day')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Trend Analysis")
        
        # Time trend if date available
        if 'date' in df.columns and not df['date'].isna().all():
            try:
                st.markdown("### Incident Trends Over Time")
                df_trend = df.copy()
                df_trend['month_year'] = pd.to_datetime(df_trend['date']).dt.to_period('M')
                monthly_counts = df_trend.groupby('month_year').size().reset_index(name='count')
                monthly_counts['month_year'] = monthly_counts['month_year'].astype(str)
                
                fig = px.line(monthly_counts, x='month_year', y='count', 
                           title='Monthly Incident Counts', markers=True)
                fig.update_xaxes(title="Month")
                fig.update_yaxes(title="Number of Incidents")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Could not create time trend: {str(e)}")
        
        # Factors breakdown if available
        if 'factor' in df.columns and not df['factor'].isna().all():
            st.markdown("### Contributing Factors")
            factor_counts = df['factor'].value_counts().head(10).reset_index()
            factor_counts.columns = ['Factor', 'Count']
            
            fig = px.bar(factor_counts, x='Count', y='Factor',
                       title='Top 10 Contributing Factors', orientation='h')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Detailed Breakdown")
        
        # Allow interactive filtering
        st.markdown("### Interactive Data Explorer")
        st.markdown("Use the filters below to explore specific subsets of your data:")
        
        col1, col2 = st.columns(2)
        filters = {}
        
        # Dynamically add filters based on available columns
        with col1:
            if 'severity' in df.columns and len(df['severity'].dropna().unique()) < 10:
                severity_options = ['All'] + sorted(df['severity'].dropna().unique().tolist())
                selected_severity = st.selectbox("Severity Level", options=severity_options)
                if selected_severity != 'All':
                    filters['severity'] = selected_severity
            
            if 'weather' in df.columns and len(df['weather'].dropna().unique()) < 15:
                weather_options = ['All'] + sorted(df['weather'].dropna().unique().tolist())
                selected_weather = st.selectbox("Weather Condition", options=weather_options)
                if selected_weather != 'All':
                    filters['weather'] = selected_weather
        
        with col2:
            if 'hour' in df.columns:
                hour_range = st.slider("Hour of Day", 0, 23, (0, 23))
                if hour_range != (0, 23):
                    filters['hour_min'] = hour_range[0]
                    filters['hour_max'] = hour_range[1]
            
            if 'day_of_week' in df.columns:
                dow_options = ['All', 'Weekday', 'Weekend']
                selected_dow = st.selectbox("Day Type", options=dow_options)
                if selected_dow == 'Weekday':
                    filters['weekday'] = True
                elif selected_dow == 'Weekend':
                    filters['weekday'] = False
        
        # Apply filters
        filtered_df = df.copy()
        for key, value in filters.items():
            if key == 'hour_min':
                filtered_df = filtered_df[filtered_df['hour'] >= value]
            elif key == 'hour_max':
                filtered_df = filtered_df[filtered_df['hour'] <= value]
            elif key == 'weekday':
                if value:  # Weekdays (0=Monday, 4=Friday)
                    filtered_df = filtered_df[filtered_df['day_of_week'].isin([0, 1, 2, 3, 4])] 
                else:  # Weekends (5=Saturday, 6=Sunday)
                    filtered_df = filtered_df[filtered_df['day_of_week'].isin([5, 6])]
            else:
                filtered_df = filtered_df[filtered_df[key] == value]
        
        # Show filtered data count
        st.metric("Filtered Records", len(filtered_df))
        
        # Display the filtered data
        st.dataframe(filtered_df, use_container_width=True)
        
        # Export option
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download Filtered Data",
                data=csv,
                file_name="filtered_data.csv",
                mime="text/csv",
            )

# Methodology explanation
st.markdown("---")
st.subheader("🔍 About Our Data Analysis Methodology")
st.markdown("""
Our AI-powered data analysis system processes your uploaded data through several steps:

1. **Data Cleaning & Normalization**: We standardize your data format, handle missing values, and align it with our analysis framework.

2. **Temporal Pattern Recognition**: We identify time-based patterns including time-of-day, day-of-week, and seasonal trends.

3. **Statistical Analysis**: We calculate key statistics and metrics to identify significant patterns and outliers in your data.

4. **Machine Learning Pattern Detection**: For larger datasets, we use cluster analysis and anomaly detection to identify non-obvious patterns.

5. **Natural Language Processing**: Our AI assistant interprets the statistical findings and translates them into plain English insights and recommendations.

This process gives you actionable intelligence from your safety data that would typically require a team of data scientists to produce.
""")

# Footer with attribution
st.markdown("---")
st.markdown("""
<div style="display: flex; justify-content: space-between; font-size: 0.8em;">
    <span>© 2025 San Jose Safe Commute</span>
    <span>Version 2.2.0</span>
</div>
""", unsafe_allow_html=True)