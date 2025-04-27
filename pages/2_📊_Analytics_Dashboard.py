import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="San Jose Safe Commute | Analytics",
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

# Custom CSS for better spacing and readability
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Generate sample data (we'll replace this with real data later)
def generate_sample_data():
    np.random.seed(42)
    
    # Generate hourly data for the last 30 days
    dates = pd.date_range(
        end=datetime.now(),
        periods=30*24,  # 30 days * 24 hours
        freq='H'
    )
    
    # Define San Jose neighborhoods with their characteristics
    neighborhoods = {
        'Downtown': {'base_risk': 6.0, 'traffic_mult': 1.4},
        'North San Jose': {'base_risk': 7.5, 'traffic_mult': 1.2},
        'West San Jose': {'base_risk': 8.0, 'traffic_mult': 0.9},
        'East San Jose': {'base_risk': 6.5, 'traffic_mult': 1.1},
        'South San Jose': {'base_risk': 7.0, 'traffic_mult': 1.0},
        'Willow Glen': {'base_risk': 8.5, 'traffic_mult': 0.8},
        'Japantown': {'base_risk': 8.0, 'traffic_mult': 0.9},
        'Rose Garden': {'base_risk': 8.5, 'traffic_mult': 0.7}
    }
    
    # Initialize data dictionary
    data = {
        'datetime': dates,
        'incidents': [],
        'risk_score': [],
        'traffic_density': [],
        'weather': np.random.choice(['Clear', 'Cloudy', 'Rain'], size=len(dates), p=[0.6, 0.3, 0.1]),
        'neighborhood': np.random.choice(list(neighborhoods.keys()), size=len(dates))
    }
    
    # Generate time-based patterns
    for dt in dates:
        hour = dt.hour
        
        # Base incident rate
        base_incidents = 3
        
        # Time-based incident adjustments
        if 22 <= hour or hour < 4:  # Late night
            incident_factor = 2.0
            risk_base = 4.0
            traffic_base = 0.2
        elif (7 <= hour < 9) or (16 <= hour < 19):  # Rush hours
            incident_factor = 1.5
            risk_base = 5.0
            traffic_base = 0.8
        elif 9 <= hour < 16:  # Mid-day
            incident_factor = 1.0
            risk_base = 7.0
            traffic_base = 0.5
        else:  # Early morning/evening
            incident_factor = 1.2
            risk_base = 6.0
            traffic_base = 0.4
        
        # Add random variation
        incidents = int(np.random.poisson(base_incidents * incident_factor))
        risk_score = min(10, max(1, risk_base + np.random.normal(0, 0.5)))
        traffic_density = min(1, max(0, traffic_base + np.random.normal(0, 0.1)))
        
        data['incidents'].append(incidents)
        data['risk_score'].append(risk_score)
        data['traffic_density'].append(traffic_density)
    
    df = pd.DataFrame(data)
    
    # Add day of week and hour columns
    df['day_of_week'] = df['datetime'].dt.day_name()
    df['hour'] = df['datetime'].dt.hour
    df['hour_12'] = df['datetime'].dt.strftime('%I %p')
    
    return df

# Load or generate data
df = generate_sample_data()

# Title and Description
st.title("📊 San Jose Traffic Safety Analytics")
st.markdown("""
### Comprehensive Safety Intelligence Dashboard

Welcome to the analytics hub of San Jose Safe Commute. This dashboard leverages historical data 
and real-time information to provide actionable insights about traffic safety in San Jose.

#### Dashboard Features:
- 📈 **Real-time Metrics**: Monitor current safety levels and incident rates
- 🗺️ **Geographic Analysis**: Identify safety patterns across different neighborhoods
- 📉 **Trend Analysis**: Track safety improvements and areas needing attention
- 🌦️ **Environmental Impact**: Understand how weather and time affect safety

*The insights provided here are based on historical data analysis and predictive modeling.*
""")

# Top-level metrics with explanations
st.subheader("📊 Key Safety Metrics")
st.markdown("Real-time overview of critical safety indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container():
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            "Average Daily Incidents", 
            f"{df['incidents'].mean():.1f}",
            f"{df['incidents'].mean() - df['incidents'].iloc[-7*24:].mean():.1f}",
            help="Average number of traffic incidents per day, with week-over-week change"
        )
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            "Current Risk Score", 
            f"{df['risk_score'].iloc[-1]:.1f}/10",
            f"{df['risk_score'].iloc[-1] - df['risk_score'].iloc[-2]:.1f}",
            help="Overall safety score (0-10) based on current conditions"
        )
        st.markdown('</div>', unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            "Traffic Density", 
            f"{df['traffic_density'].iloc[-1]:.1%}",
            f"{(df['traffic_density'].iloc[-1] - df['traffic_density'].iloc[-2])*100:.1f}%",
            help="Current traffic density as a percentage of maximum capacity"
        )
        st.markdown('</div>', unsafe_allow_html=True)

with col4:
    with st.container():
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        most_common_weather = df['weather'].mode()[0]
        st.metric(
            "Current Weather", 
            most_common_weather, 
            "",
            help="Current weather conditions affecting traffic safety"
        )
        st.markdown('</div>', unsafe_allow_html=True)

# Analysis Sections
st.markdown("---")
st.subheader("🔎 Detailed Analysis Sections")
st.markdown("Explore different aspects of traffic safety through interactive visualizations")

tab1, tab2, tab3 = st.tabs(["📈 Time-Based Safety Analysis", "🗺️ Neighborhood Analysis", "🎯 Risk Assessment"])

with tab1:
    st.subheader("📈 Time-Based Safety Analysis")
    
    # Hourly patterns
    st.markdown("### ⏰ Hourly Safety Patterns")
    hourly_avg = df.groupby('hour_12').agg({
        'incidents': 'mean',
        'risk_score': 'mean',
        'traffic_density': 'mean'
    }).reset_index()
    
    # Incidents by hour
    fig = px.bar(hourly_avg, x='hour_12', y='incidents',
                 title='Average Incidents by Hour',
                 labels={'hour_12': 'Hour', 'incidents': 'Average Incidents'})
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk score by hour
    fig = px.line(hourly_avg, x='hour_12', y='risk_score',
                  title='Safety Score by Hour',
                  labels={'hour_12': 'Hour', 'risk_score': 'Safety Score'},
                  markers=True)
    fig.update_layout(showlegend=False)
    fig.add_hline(y=7, line_dash="dash", line_color="green", annotation_text="Safe")
    fig.add_hline(y=4, line_dash="dash", line_color="red", annotation_text="High Risk")
    st.plotly_chart(fig, use_container_width=True)
    
    # Traffic density heatmap
    st.markdown("### 📆 Weekly Traffic Patterns")
    weekly_data = df.pivot_table(
        index='day_of_week',
        columns='hour_12',
        values='traffic_density',
        aggfunc='mean'
    )
    
    # Reorder days of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_data = weekly_data.reindex(day_order)
    
    fig = px.imshow(weekly_data,
                    title='Traffic Density Heatmap',
                    labels=dict(x='Hour', y='Day of Week', color='Traffic Density'),
                    color_continuous_scale='RdYlGn_r')
    st.plotly_chart(fig, use_container_width=True)
    
    # Key findings
    st.markdown("### 🔍 Key Findings")
    st.markdown("""
    - 🌙 **Late Night (10 PM - 4 AM)**: Highest risk period with fewer but more severe incidents
    - 🚶 **Rush Hours (7-9 AM, 4-7 PM)**: Moderate risk due to high traffic density
    """)

with tab2:
    st.subheader(" Neighborhood Safety Analysis")
    st.markdown("Explore safety patterns across different San Jose neighborhoods")
    
    # Calculate neighborhood statistics
    neighborhood_stats = df.groupby('neighborhood').agg({
        'incidents': 'mean',
        'risk_score': 'mean',
        'traffic_density': 'mean'
    }).round(2)
    
    # Add overall safety score
    neighborhood_stats['safety_score'] = (
        (10 - neighborhood_stats['incidents']/neighborhood_stats['incidents'].max() * 5) * 0.4 +
        (neighborhood_stats['risk_score']) * 0.4 +
        (10 - neighborhood_stats['traffic_density'] * 10) * 0.2
    ).round(1)

    # Display neighborhood metrics
    st.markdown("### Neighborhood Safety Metrics")
    cols = st.columns(4)
    
    # Find safest and most concerning neighborhoods
    safest = neighborhood_stats.safety_score.idxmax()
    concerning = neighborhood_stats.safety_score.idxmin()
    
    with cols[0]:
        st.metric(
            "Safest Neighborhood",
            safest,
            f"{neighborhood_stats.loc[safest, 'safety_score']:.1f}/10",
            help="Based on combined safety metrics"
        )
    with cols[1]:
        st.metric(
            "Most Incidents",
            neighborhood_stats['incidents'].idxmax(),
            f"{neighborhood_stats['incidents'].max():.1f} avg/day"
        )
    with cols[2]:
        st.metric(
            "Highest Traffic",
            neighborhood_stats['traffic_density'].idxmax(),
            f"{neighborhood_stats['traffic_density'].max():.1%}"
        )
    with cols[3]:
        st.metric(
            "Needs Attention",
            concerning,
            f"{neighborhood_stats.loc[concerning, 'safety_score']:.1f}/10"
        )

    # Create bar chart for safety scores by neighborhood
    st.markdown("### Overall Safety Scores")
    fig = px.bar(
        neighborhood_stats.reset_index(),
        x='neighborhood',
        y='safety_score',
        title='Neighborhood Safety Scores (out of 10)',
        color='safety_score',
        color_continuous_scale='RdYlGn',
        labels={'safety_score': 'Safety Score', 'neighborhood': 'Neighborhood'}
    )
    fig.add_hline(y=7.5, line_dash="dash", line_color="green", annotation_text="Very Safe")
    fig.add_hline(y=5.0, line_dash="dash", line_color="red", annotation_text="Needs Improvement")
    st.plotly_chart(fig, use_container_width=True)

    # Create scatter plot for risk factors
    st.markdown("### Risk Factor Analysis")
    fig = px.scatter(
        neighborhood_stats.reset_index(),
        x='traffic_density',
        y='incidents',
        size='risk_score',
        color='safety_score',
        title='Neighborhood Risk Factors Comparison',
        labels={
            'traffic_density': 'Traffic Density',
            'incidents': 'Average Daily Incidents',
            'risk_score': 'Risk Score',
            'safety_score': 'Safety Score'
        },
        text='neighborhood',
        color_continuous_scale='RdYlGn'
    )
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig, use_container_width=True)
    
    # Key insights
    st.markdown("### Key Neighborhood Insights")
    st.markdown(f"""
    - **Safest Area**: {safest} leads with a safety score of {neighborhood_stats.loc[safest, 'safety_score']:.1f}/10
    - **Areas for Improvement**: {concerning} shows opportunities for safety enhancements
    - **Traffic Patterns**: {neighborhood_stats['traffic_density'].idxmax()} experiences the highest traffic density
    - **Incident Rates**: {neighborhood_stats['incidents'].idxmax()} reports the most incidents on average
    """)

with tab3:
    st.subheader("🎯 Risk Factor Analysis")
    st.markdown("Analyze how different factors affect safety metrics")

    # Time period categories
    def categorize_time_period(hour):
        if 22 <= hour or hour < 4:
            return 'Late Night (10 PM - 4 AM)'
        elif (7 <= hour < 9) or (16 <= hour < 19):
            return 'Rush Hours'
        elif 9 <= hour < 16:
            return 'Mid-Day'
        else:
            return 'Other Hours'

    # Add time period category
    df['time_period'] = df['hour'].apply(categorize_time_period)

    # Analyze time periods
    time_analysis = df.groupby('time_period').agg({
        'incidents': 'mean',
        'risk_score': 'mean',
        'traffic_density': 'mean'
    }).round(2)

    # Display time period metrics
    st.markdown("### ⏰ Time Period Analysis")
    cols = st.columns(len(time_analysis))
    
    for i, (period, data) in enumerate(time_analysis.iterrows()):
        with cols[i]:
            st.metric(
                period,
                f"Risk: {data['risk_score']:.1f}/10",
                f"Incidents: {data['incidents']:.1f}",
                help=f"Traffic: {data['traffic_density']:.1%}"
            )

    # Create comprehensive time period analysis
    fig = go.Figure()
    
    # Add bars for incidents
    fig.add_trace(go.Bar(
        name='Incidents',
        x=time_analysis.index,
        y=time_analysis['incidents'],
        yaxis='y',
        offsetgroup=1
    ))
    
    # Add lines for risk score
    fig.add_trace(go.Scatter(
        name='Risk Score',
        x=time_analysis.index,
        y=time_analysis['risk_score'],
        yaxis='y2',
        line=dict(color='red')
    ))
    
    # Add bars for traffic density
    fig.add_trace(go.Bar(
        name='Traffic Density',
        x=time_analysis.index,
        y=time_analysis['traffic_density'],
        yaxis='y3',
        offsetgroup=2
    ))
    
    # Update layout
    fig.update_layout(
        title='Safety Metrics by Time Period',
        yaxis=dict(
            title='Average Incidents',
            side='left'
        ),
        yaxis2=dict(
            title='Risk Score',
            overlaying='y',
            side='right'
        ),
        yaxis3=dict(
            title='Traffic Density',
            overlaying='y',
            side='right',
            position=0.85
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # Weather impact analysis
    st.markdown("### 🌦️ Weather Impact Analysis")
    weather_analysis = df.groupby('weather').agg({
        'incidents': 'mean',
        'risk_score': 'mean',
        'traffic_density': 'mean'
    }).round(2)

    # Display weather metrics
    cols = st.columns(len(weather_analysis))
    for i, (weather, data) in enumerate(weather_analysis.iterrows()):
        with cols[i]:
            st.metric(
                weather,
                f"Risk: {data['risk_score']:.1f}/10",
                f"Incidents: {data['incidents']:.1f}",
                help=f"Traffic: {data['traffic_density']:.1%}"
            )

    # Create weather analysis visualization
    fig = px.scatter(
        weather_analysis.reset_index(),
        x='traffic_density',
        y='incidents',
        size='risk_score',
        color='weather',
        title='Weather Impact on Safety Metrics',
        labels={
            'traffic_density': 'Traffic Density',
            'incidents': 'Average Incidents',
            'risk_score': 'Risk Score',
            'weather': 'Weather Condition'
        },
        text='weather'
    )
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig, use_container_width=True)

    # Key findings
    st.markdown("### 🔍 Key Risk Findings")
    st.markdown(f"""
    **Time-Based Patterns:**
    - 🌙 **Late Night**: Higher risk ({time_analysis.loc['Late Night (10 PM - 4 AM)', 'risk_score']:.1f}/10) with {time_analysis.loc['Late Night (10 PM - 4 AM)', 'incidents']:.1f} avg incidents
    - 🚗 **Rush Hours**: Moderate risk ({time_analysis.loc['Rush Hours', 'risk_score']:.1f}/10) with high traffic ({time_analysis.loc['Rush Hours', 'traffic_density']:.1%})
    - ☀️ **Mid-Day**: Lower risk ({time_analysis.loc['Mid-Day', 'risk_score']:.1f}/10) with better visibility

    **Weather Impact:**
    - ☔️ **Rain**: {weather_analysis.loc['Rain', 'risk_score']:.1f}/10 risk score, {weather_analysis.loc['Rain', 'incidents']:.1f} avg incidents
    - ☁️ **Cloudy**: {weather_analysis.loc['Cloudy', 'risk_score']:.1f}/10 risk score
    - ☀️ **Clear**: {weather_analysis.loc['Clear', 'risk_score']:.1f}/10 risk score (baseline)
    """)

# Additional insights
st.subheader("📋 Key Insights")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### Safety Patterns
    - Most incidents occur during peak hours
    - Weather significantly impacts risk scores
    - Certain neighborhoods show consistently higher risk
    """)

with col2:
    st.markdown("""
    #### Recommendations
    - Plan trips outside peak hours when possible
    - Take extra precautions during adverse weather
    - Consider alternate routes through safer neighborhoods
    """)
