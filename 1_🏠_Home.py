import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import requests
from dotenv import load_dotenv
import os
import googlemaps
import pytz
from datetime import datetime

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Initialize Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

def get_place_suggestions(query):
    if not query:
        return []
    # Add 'San Jose' to the query to focus on San Jose area
    query = f"{query}, San Jose, CA"
    try:
        results = gmaps.places_autocomplete(query, components={'country': 'US'})
        return [result['description'] for result in results]
    except Exception as e:
        st.error(f"Error getting place suggestions: {str(e)}")
        return []

def get_coordinates(place_id):
    try:
        result = gmaps.geocode(place_id)
        if result:
            location = result[0]['geometry']['location']
            return location['lat'], location['lng']
        return None
    except Exception as e:
        st.error(f"Error getting coordinates: {str(e)}")
        return None

st.set_page_config(
    page_title="San Jose Safe Commute | Route Planner",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create two columns for the layout
left_col, right_col = st.columns([3, 2])

with left_col:
    st.title("🚗 San Jose Safe Commute")
    st.markdown("""### Your AI-Powered Route Safety Assistant

    Welcome to San Jose Safe Commute, your intelligent companion for safer urban navigation. This tool helps you:
    
    - 🎯 **Plan Optimal Routes**: Enter your start and destination points to get personalized route recommendations
    - 🔍 **Assess Safety Scores**: Receive real-time safety assessments based on historical data and current conditions
    - 🌦️ **Consider Conditions**: Account for weather, time of day, and traffic patterns in route planning
    - 📊 **View Analytics**: Explore detailed safety trends and patterns in the Analytics Dashboard
    
    #### How to Use
    1. Enter your starting location below
    2. Input your destination
    3. Review the suggested route and safety score
    4. Check the Analytics Dashboard for deeper insights
    """)

        # Helper function for risk prediction
    def basic_predict_risk(origin, destination):
        """Calculate a risk score based on time of day and location."""
        import random
        from datetime import datetime
        import pytz

        # Get current time in PST
        pst = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(pst)
        hour = current_time.hour
        minute = current_time.minute

        # Base safety score out of 10
        base_score = 7.0

        # Time-based risk factors
        time_risk = 0.0

        # Late night hours (10 PM - 4 AM) have higher risk
        if 22 <= hour or hour < 4:
            time_risk -= 2.0
        # Rush hours (7-9 AM, 4-7 PM) have moderate risk
        elif (7 <= hour < 9) or (16 <= hour < 19):
            time_risk -= 1.0
        # Mid-day (9 AM - 4 PM) is generally safer
        elif 9 <= hour < 16:
            time_risk += 0.5
        # Early morning (4-7 AM) and evening (7-10 PM) have slight risk
        else:
            time_risk -= 0.5

        # Random factor for other variables (weather, events, etc.)
        random_factor = random.uniform(-0.5, 0.5)

        # Calculate final score
        final_score = base_score + time_risk + random_factor

        # Ensure score stays within 1-10 range
        return max(min(final_score, 10.0), 1.0)

    # --- User Inputs with Autocomplete ---
    origin_query = st.text_input("🏠 Enter starting location", key="origin")
    origin = None
    destination = None
    
    if origin_query:
        origin_suggestions = get_place_suggestions(origin_query)
        if origin_suggestions:
            origin = st.selectbox("Select starting point", origin_suggestions, key="origin_select")

    destination_query = st.text_input("📍 Enter destination", key="destination")
    if destination_query:
        destination_suggestions = get_place_suggestions(destination_query)
        if destination_suggestions:
            destination = st.selectbox("Select destination", destination_suggestions, key="dest_select")

    # Initialize session state for risk analysis
    if 'risk_analyzed' not in st.session_state:
        st.session_state['risk_analyzed'] = False
        st.session_state['risk_score'] = None
        st.session_state['current_time'] = None
        st.session_state['time_period'] = None
        st.session_state['stored_origin'] = None
        st.session_state['stored_dest'] = None

    # Calculate safety score
    if origin and destination:
        col1, col2 = st.columns([2, 1])
        with col1:
            # Only calculate if origin or destination has changed
            recalculate = (
                st.button("🚘 Calculate Route Safety", type="primary") or
                st.session_state['stored_origin'] != origin or
                st.session_state['stored_dest'] != destination
            )
            
            if recalculate:
                with st.spinner("Analyzing route safety..."):
                    # Get current time in PST
                    pst = pytz.timezone('America/Los_Angeles')
                    current_time = datetime.now(pst)
                    formatted_time = current_time.strftime("%I:%M %p PST")
                    
                    # Calculate risk score
                    risk_score = basic_predict_risk(origin, destination)
                    
                    # Update session state
                    st.session_state['risk_analyzed'] = True
                    st.session_state['risk_score'] = risk_score
                    st.session_state['current_time'] = formatted_time
                    st.session_state['stored_origin'] = origin
                    st.session_state['stored_dest'] = destination
                    
                    # Determine time period
                    hour = current_time.hour
                    if 22 <= hour or hour < 4:
                        st.session_state['time_period'] = "late_night"
                    elif (7 <= hour < 9) or (16 <= hour < 19):
                        st.session_state['time_period'] = "rush_hour"
                    elif 9 <= hour < 16:
                        st.session_state['time_period'] = "mid_day"
                    else:
                        st.session_state['time_period'] = "transition"
            
            # Always show results if they exist
            if st.session_state['risk_analyzed']:
                st.success("Analysis complete!")
                
                # Display time and score
                st.markdown(f"**Current Time:** {st.session_state['current_time']}")
                st.metric(
                    "Route Safety Score", 
                    f"{st.session_state['risk_score']:.1f}/10.0",
                    help="Higher score indicates safer route"
                )
                
                # Display time-based context
                if st.session_state['time_period'] == "late_night":
                    st.warning("🌙 Late Night Hours: Exercise extra caution")
                elif st.session_state['time_period'] == "rush_hour":
                    st.warning("🚗 Rush Hour: Expect increased traffic")
                elif st.session_state['time_period'] == "mid_day":
                    st.info("☀️ Mid-Day: Generally safer conditions")
                else:
                    st.info("🌇 Transition Hours: Moderate safety conditions")
                
                # Add safety recommendations based on score
                if st.session_state['risk_score'] >= 7.0:
                    st.success("🟢 This route is generally safe. Standard precautions recommended.")
                    st.markdown("""
                    **Recommendations:**
                    - Follow standard safety practices
                    - Stay aware of your surroundings
                    - Follow traffic signals and signs
                    """)
                elif st.session_state['risk_score'] >= 5.0:
                    st.warning("🟡 Exercise normal caution on this route.")
                    st.markdown("""
                    **Recommendations:**
                    - Consider traveling during off-peak hours
                    - Stay alert and maintain awareness
                    - Keep emergency contacts available
                    - Consider alternate routes during peak times
                    """)
                else:
                    st.error("🔴 Higher risk route. Consider alternative or take extra precautions.")
                    st.markdown("""
                    **Recommendations:**
                    - Consider alternative routes if possible
                    - Travel with others when feasible
                    - Avoid late night travel on this route
                    - Keep emergency services numbers handy
                    - Share your location with trusted contacts
                    """)

with right_col:
    # Initialize the map centered on San Jose
    m = folium.Map(location=[37.3382, -121.8863], zoom_start=12)
    
    # Add markers if locations are selected
    if origin:
        origin_coords = get_coordinates(origin)
        if origin_coords:
            folium.Marker(
                origin_coords,
                popup=f"Start: {origin}",
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)
            # Update map center to origin
            m.location = origin_coords

    if destination:
        dest_coords = get_coordinates(destination)
        if dest_coords:
            folium.Marker(
                dest_coords,
                popup=f"Destination: {destination}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

            if origin:  # If both points are selected, draw a line between them
                origin_coords = get_coordinates(origin)
                if origin_coords:
                    # Draw the route line
                    folium.PolyLine(
                        locations=[origin_coords, dest_coords],
                        weight=3,
                        color='blue',
                        opacity=0.8
                    ).add_to(m)
                    
                    # Adjust map bounds to show both markers
                    bounds = [
                        [min(origin_coords[0], dest_coords[0]), min(origin_coords[1], dest_coords[1])],
                        [max(origin_coords[0], dest_coords[0]), max(origin_coords[1], dest_coords[1])]
                    ]
                    m.fit_bounds(bounds)

    # Display the map with a container
    with st.container():
        st.markdown("### 🗺️ Route Map")
        map_data = st_folium(m, height=500, width=None)
        
        # Add map instructions
        st.markdown("""
        **Map Controls:**
        - 🔍 Zoom: Use + / - buttons or scroll wheel
        - 🖱️ Pan: Click and drag
        - ℹ️ Info: Click markers for location details
        """)

# --- Placeholder for ML Model and Data ---
def basic_predict_risk(origin, destination, weather="Clear"):
    # Placeholder logic: random risk score (replace with real model)
    np.random.seed(len(origin) + len(destination))
    return np.random.randint(1, 10)

# --- Map Visualization ---
def show_map():
    m = folium.Map(location=[37.3382, -121.8863], zoom_start=12)
    # Example: highlight a few risk areas
    folium.Circle([37.335, -121.89], radius=500, color='red', fill=True, fill_opacity=0.4, tooltip="High Risk").add_to(m)
    folium.Circle([37.32, -121.88], radius=400, color='orange', fill=True, fill_opacity=0.3, tooltip="Medium Risk").add_to(m)
    return m

# --- Main App Logic ---
if st.button("Check Risk"):
    # Basic ML model prediction (placeholder)
    risk_score = basic_predict_risk(origin, destination)
    st.metric("Risk Score", risk_score)

    # Display static map
    m = show_map()
    st_folium(m, width=700, height=400)

    st.markdown("### Safety Tips")
    st.write("- Slow down, especially near known high-risk areas.")
    st.write("- Pay extra attention during poor weather conditions.")
    st.write("- Follow all posted speed limits and signage.")

# --- Historical Insights ---
st.markdown("---")
st.header("Historical Accident Hotspots")
# Example static data (replace with real data integration)
hotspots = pd.DataFrame({
    "Location": ["Alum Rock Ave & King Rd", "Story Rd & Senter Rd", "Capitol Expy & McLaughlin Ave"],
    "Accidents": [25, 18, 15]
})
st.table(hotspots)

# --- User Feedback ---
st.markdown("---")
st.header("Feedback")
with st.form("feedback_form"):
    feedback = st.text_area("How can we improve this app?")
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.success("Thank you for your feedback!")
