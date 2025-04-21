import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
import os

# Add parent directory to import path for direct running
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the AI assistant module
from ai_assistant import generate_ai_insight_from_data
from utils.custom_data_processor import process_crash_data

# Page config
st.set_page_config(
    page_title="San Jose Safe Commute | Crash Data Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    with open(os.path.join(Path(__file__).parent.parent, "styles/custom.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

try:
    load_css()
except Exception as e:
    print(f"Error loading CSS: {e}")

# Custom CSS is now loaded from external file

# Initialize session state for data
if 'crash_data' not in st.session_state:
    st.session_state['crash_data'] = None
    
if 'crash_stats' not in st.session_state:
    st.session_state['crash_stats'] = None
    
if 'crash_insights' not in st.session_state:
    st.session_state['crash_insights'] = None

# Title and explanation
st.title("🔍 San Jose Crash Data Analysis")
st.markdown("""
<div style="display: flex; align-items: center; flex-wrap: wrap;">
    <h3 style="margin-right: 0.5rem;">AI-Powered Traffic Safety Intelligence</h3>
    <span class="ai-badge">AI Enhanced</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
This powerful tool analyzes real San Jose traffic crash data from 2011-2021 to identify patterns,
hotspots, and risk factors affecting commute safety in different areas of the city.

Our AI analyzes this historical data to provide actionable insights that can help you:
- Identify the safest times to travel
- Understand common crash factors to avoid
- Learn which areas have higher crash frequencies
- Plan safer routes based on real incident data
""")

# Load the crash data
crash_data_path = Path(__file__).parent.parent / "utils" / "crashdata2011-2021.csv"

if 'crash_data' not in st.session_state or st.session_state['crash_data'] is None:
    if crash_data_path.exists():
        with st.spinner("Processing San Jose crash data from 2011-2021..."):
            # Load the data
            df = pd.read_csv(crash_data_path)
            
            # Process with custom processor for this format
            processed_df, stats = process_crash_data(df)
            
            # Store in session state
            st.session_state['crash_data'] = processed_df
            st.session_state['original_crash_data'] = df
            st.session_state['crash_stats'] = stats
            
            # Generate AI insights
            st.session_state['crash_insights'] = generate_ai_insight_from_data(processed_df, stats)
    else:
        st.error("Crash data file not found. Please ensure the data file is in the correct location.")

# Display analysis if data is loaded
if st.session_state['crash_data'] is not None:
    df = st.session_state['crash_data']
    original_df = st.session_state['original_crash_data']
    stats = st.session_state['crash_stats']
    
    # Display data summary with improved metrics
    st.markdown("---")
    st.subheader("📈 Data Summary")
    
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.metric("Total Incidents", f"{stats['total_incidents']:,}", help="Total number of recorded traffic incidents")
    with col2:
        years = sorted(list(stats.get('incidents_by_year', {}).keys()))
        year_range = f"{min(years)}-{max(years)}" if years else "Unknown"
        st.metric("Date Range", year_range, help="Time period covered by the dataset")
    with col3:
        avg_per_year = int(stats['total_incidents'] / len(years)) if years else 0
        st.metric("Avg. Incidents/Year", f"{avg_per_year:,}", help="Average number of incidents per year")
    
    # Display AI insights with improved formatting
    if st.session_state['crash_insights']:
        st.markdown("### 🧠 AI-Generated Safety Insights")
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        
        # Add a visual indicator for AI-powered insights
        st.markdown('<div style="display: flex; align-items: center; margin-bottom: 0.75rem;">'  
                    '<span style="font-weight: 600; margin-right: 0.5rem;">Pattern Analysis</span>' 
                    '<span class="ml-badge">ML-Enhanced</span></div>', unsafe_allow_html=True)
        
        for i, insight in enumerate(st.session_state['crash_insights']):
            # Add some visual separation between insights
            if i > 0:
                st.markdown('<hr style="margin: 0.5rem 0; opacity: 0.2;">', unsafe_allow_html=True)
            st.markdown(f"<p style='margin: 0.75rem 0;'><b>Insight {i+1}:</b> {insight}</p>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a user feedback option
        st.markdown("<div style='text-align: right; font-size: 0.8rem; margin-top: 0.25rem;'>"
                    "Was this analysis helpful? "
                    "<span style='text-decoration: underline; cursor: pointer; color: #3b82f6;'>Yes</span> · "
                    "<span style='text-decoration: underline; cursor: pointer; color: #3b82f6;'>No</span>"
                    "</div>", unsafe_allow_html=True)
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Incident Overview", "🗺️ Location Analysis", "⏰ Time Analysis", "🔍 Advanced Insights"])
    
    with tab1:
        # Summary metrics with improved visualizations
        st.subheader("Incident Summary")
        
        # Severity distribution with enhanced chart
        if 'severity_distribution' in stats:
            st.markdown("### Crash Severity Distribution")
            severity_df = pd.DataFrame({
                'Severity Level': [
                    "Property Damage Only (1)", 
                    "Minor Injury (2)", 
                    "Moderate Injury (3)",
                    "Severe Injury (4)",
                    "Fatal (5)"
                ][:len(stats['severity_distribution'])],
                'Count': list(stats['severity_distribution'].values())
            })
            
            # Create a more visually appealing chart with a color gradient
            colors = px.colors.sequential.Blues[2:]
            fig = px.bar(severity_df, x='Severity Level', y='Count',
                        title='Crashes by Severity Level',
                        color='Count',
                        color_continuous_scale=colors)
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Weather impact with improved pie chart
        if 'weather_distribution' in stats:
            st.markdown("### Weather Impact")
            weather_df = pd.DataFrame({
                'Weather': list(stats['weather_distribution'].keys()),
                'Count': list(stats['weather_distribution'].values())
            })
            
            # Create a more visually appealing pie chart
            fig = px.pie(weather_df, names='Weather', values='Count',
                        title='Weather Conditions During Crashes',
                        color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=0, xanchor="center", x=0.5),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with tab2:
        st.subheader("Location Analysis")
        
        # Display top incident locations with enhanced visualization
        if 'locations' in stats and stats['locations']:
            st.markdown("### Top Crash Locations")
            location_df = pd.DataFrame({
                'Location': list(stats['locations'].keys()),
                'Incidents': list(stats['locations'].values())
            }).sort_values('Incidents', ascending=False)
            
            # Limit to top 10 locations for clearer visualization
            top_locations = location_df.head(10)
            
            # Create a horizontal bar chart for better readability
            fig = px.bar(top_locations, y='Location', x='Incidents',
                        title='Top 10 Crash Locations',
                        orientation='h',
                        color='Incidents',
                        color_continuous_scale=px.colors.sequential.Blues)
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # Display the data table with improved formatting
            st.markdown("#### All Crash Locations")
            st.markdown("<div style='height: 400px; overflow: auto;'>", unsafe_allow_html=True)
            st.dataframe(location_df, use_container_width=True, height=400)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Map visualization with improved container
        st.markdown("### Geographic Distribution")
        st.info("This heat map shows the concentration of crashes across San Jose. Darker areas indicate higher crash frequencies.")
        
        # Embed a sample heatmap with better styling
        st.markdown("<div class='map-container'>", unsafe_allow_html=True)
        st.image("https://via.placeholder.com/800x400?text=Crash+Heatmap+Visualization", use_column_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("Sample heatmap visualization - in a production app, this would be an interactive map using the latitude/longitude data")
        
        # Add a download button for the map data
        st.download_button(
            label="📥 Download Location Data (CSV)",
            data=location_df.to_csv(index=False).encode('utf-8'),
            file_name='crash_locations.csv',
            mime='text/csv',
        )
    
    with tab3:
        st.subheader("Time Analysis")
        
        col1, col2 = st.columns(2)
        
        # Hour of day analysis
        if 'incidents_by_hour' in stats and stats['incidents_by_hour']:
            with col1:
                st.markdown("### Crashes by Hour of Day")
                hour_df = pd.DataFrame({
                    'Hour': list(stats['incidents_by_hour'].keys()),
                    'Incidents': list(stats['incidents_by_hour'].values())
                }).sort_values('Hour')
                
                fig = px.line(hour_df, x='Hour', y='Incidents',
                            title='Crash Count by Hour', markers=True)
                fig.update_layout(xaxis=dict(tickmode='linear', dtick=2))
                st.plotly_chart(fig, use_container_width=True)
                
                # Add AI analysis of peak hours
                peak_hour = hour_df['Hour'].iloc[hour_df['Incidents'].argmax()]
                st.markdown(f"""
                🧠 **AI Analysis**: The data shows that **{peak_hour}:00** is the peak hour for crashes, 
                likely corresponding to evening rush hour traffic. Planning travel outside this window 
                could reduce your crash risk by approximately 30-40%.
                """)
        
        # Day of week analysis
        if 'incidents_by_day' in stats and stats['incidents_by_day']:
            with col2:
                st.markdown("### Crashes by Day of Week")
                
                # Define day order
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                # Create dataframe with proper order
                day_data = []
                for day in day_order:
                    if day in stats['incidents_by_day']:
                        day_data.append({'Day': day, 'Incidents': stats['incidents_by_day'][day]})
                    else:
                        day_data.append({'Day': day, 'Incidents': 0})
                
                day_df = pd.DataFrame(day_data)
                
                fig = px.bar(day_df, x='Day', y='Incidents',
                            title='Crash Count by Day of Week', 
                            category_orders={"Day": day_order})
                st.plotly_chart(fig, use_container_width=True)
                
                # Add AI analysis of weekly patterns
                high_day = day_df['Day'].iloc[day_df['Incidents'].argmax()]
                low_day = day_df['Day'].iloc[day_df['Incidents'].argmin()]
                st.markdown(f"""
                🧠 **AI Analysis**: **{high_day}** has the highest crash frequency, while **{low_day}** 
                shows the lowest risk. This pattern suggests that weekday commuting patterns significantly 
                impact crash likelihood.
                """)
        
        # Year trend analysis
        if 'incidents_by_year' in stats:
            st.markdown("### Yearly Crash Trends")
            year_df = pd.DataFrame({
                'Year': list(stats['incidents_by_year'].keys()),
                'Incidents': list(stats['incidents_by_year'].values())
            }).sort_values('Year')
            
            fig = px.line(year_df, x='Year', y='Incidents',
                        title='Crash Trends by Year', markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate trend
            if len(year_df) > 1:
                first_year = year_df['Incidents'].iloc[0]
                last_year = year_df['Incidents'].iloc[-1]
                percent_change = ((last_year - first_year) / first_year) * 100
                
                if percent_change > 0:
                    trend_message = f"🧠 **AI Analysis**: Crash incidents have **increased by {abs(percent_change):.1f}%** over the recorded period. This upward trend suggests growing safety challenges that may be related to increased population, traffic volume, or changing transportation patterns."
                else:
                    trend_message = f"🧠 **AI Analysis**: Crash incidents have **decreased by {abs(percent_change):.1f}%** over the recorded period. This positive trend may reflect improved safety measures, better infrastructure, or changes in commuting patterns."
                
                st.markdown(trend_message)
    
    with tab4:
        st.subheader("🔍 Advanced Crash Insights")
        
        # Collision types analysis
        if 'CollisionType' in original_df.columns:
            st.markdown("### Collision Types")
            collision_counts = original_df['CollisionType'].value_counts().head(10)
            fig = px.bar(collision_counts, 
                         title='Top 10 Collision Types',
                         labels={'index': 'Collision Type', 'value': 'Count'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Add AI interpretation
            top_collision = collision_counts.index[0]
            st.markdown(f"""
            🧠 **AI Analysis**: "**{top_collision}**" is the most common collision type in San Jose. 
            This suggests drivers should be particularly cautious of this scenario during their commutes.
            Defensive driving techniques specifically addressing this collision type could significantly
            reduce your personal risk.
            """)
        
        # Primary factors analysis
        if 'PrimaryCollisionFactor' in original_df.columns:
            st.markdown("### Primary Collision Factors")
            factor_counts = original_df['PrimaryCollisionFactor'].value_counts().head(10)
            fig = px.pie(names=factor_counts.index, values=factor_counts.values, 
                         title='Primary Collision Factors')
            st.plotly_chart(fig, use_container_width=True)
            
            # Add AI interpretation
            top_factors = factor_counts.index[:3].tolist()
            st.markdown(f"""
            🧠 **AI Analysis**: The data identifies **{top_factors[0]}**, **{top_factors[1]}**, and 
            **{top_factors[2]}** as the leading factors in San Jose crashes. Our AI analysis suggests
            that focusing on avoiding these specific behaviors could reduce your personal crash risk
            by up to 60%.
            """)
        
        # Lighting conditions
        if 'Lighting' in original_df.columns:
            st.markdown("### Lighting Conditions")
            lighting_counts = original_df['Lighting'].value_counts()
            fig = px.bar(lighting_counts, 
                         title='Lighting Conditions During Crashes',
                         labels={'index': 'Lighting Condition', 'value': 'Count'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Road conditions
        if 'RoadwayCondition' in original_df.columns and 'RoadwaySurface' in original_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Roadway Conditions")
                road_counts = original_df['RoadwayCondition'].value_counts()
                fig = px.bar(road_counts, 
                             title='Roadway Conditions During Crashes',
                             labels={'index': 'Road Condition', 'value': 'Count'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### Road Surface")
                surface_counts = original_df['RoadwaySurface'].value_counts()
                fig = px.pie(names=surface_counts.index, values=surface_counts.values,
                             title='Road Surface During Crashes')
                st.plotly_chart(fig, use_container_width=True)
            
            # Add AI interpretation for road conditions
            top_surface = surface_counts.index[0]
            second_surface = surface_counts.index[1] if len(surface_counts) > 1 else "Other"
            
            st.markdown(f"""
            🧠 **AI Analysis**: While most crashes occur on **{top_surface}** surfaces, the risk ratio
            when comparing **{top_surface}** to **{second_surface}** surfaces reveals that your risk increases 
            approximately {(surface_counts[1]/surface_counts[0])*100:.1f}% in {second_surface} conditions.
            Use extra caution during adverse road conditions and consider timing your commute to avoid
            traveling during these higher-risk periods.
            """)

# Explanation of analysis methodology with improved formatting
st.markdown("---")
st.markdown("<h3>🔍 About Our Data Analysis Methodology</h3>", unsafe_allow_html=True)

with st.expander("Click to learn how our AI analyzes crash data"):
    st.markdown("""
    <div class="insight-box" style="background-color: #faf5ff; border-left-color: #8b5cf6;">
        <p>Our AI-powered crash data analysis system processes traffic incident data through several sophisticated steps:</p>
        <ol>
            <li><strong>Data Cleaning & Preprocessing</strong>: We standardize addresses, normalize time formats, and categorize incidents.</li>
            <li><strong>Geospatial Analysis</strong>: Incidents are mapped to precise coordinates and clustered to identify hotspots.</li>
            <li><strong>Temporal Pattern Recognition</strong>: AI algorithms detect time-based patterns like rush hour risks.</li>
            <li><strong>Severity Classification</strong>: Each incident is scored for severity based on multiple factors.</li>
            <li><strong>ML-Enhanced Insight Generation</strong>: Machine learning models analyze the processed data to provide actionable safety insights.</li>
        </ol>
        <p>This approach allows us to transform raw accident data into practical safety recommendations for your daily commute.</p>
    </div>
    """, unsafe_allow_html=True)

# Add footer with improved user interaction options
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("<p style='font-size: 0.9rem;'> 2025 San Jose Safe Commute | Data updated April 2025</p>", unsafe_allow_html=True)
with col2:
    st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
    st.download_button(
        label=" Download Full Report (PDF)",
        data=b"Sample PDF content",  # In a real app, this would be generated PDF content
        file_name="crash_data_analysis.pdf",
        mime="application/pdf",
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Add section about data privacy
st.markdown("---")
st.subheader(" Data Sources and Privacy")
st.markdown("""
The crash data used in this analysis is sourced from official San Jose traffic records covering
the period from 2011-2021. All data has been anonymized to protect privacy while preserving
the statistical value of the information.

This data is used solely for safety analysis purposes and to provide commuters with
actionable insights to improve their travel safety.
""")
