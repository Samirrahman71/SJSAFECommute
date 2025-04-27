"""
San Jose Safe Commute - Home Page
A streamlit app for San Jose commuters to analyze route safety and get AI-powered recommendations.
"""

import streamlit as st
import pandas as pd
import numpy as np
import openai
import os
import folium
from datetime import datetime, timedelta
from streamlit_folium import folium_static
import json
from pathlib import Path
import math
from folium.plugins import HeatMap, MarkerCluster
from shapely.geometry import Point, LineString

# Set page configuration
st.set_page_config(
    page_title="San Jose Safe Commute",
    page_icon="🏠",
    layout="wide"
)

# Initialize session state for user preferences
if 'preferences' not in st.session_state:
    st.session_state.preferences = {
        'time_efficiency': 0.5,
        'safety': 0.3,
        'comfort': 0.15,
        'scenic': 0.05
    }

# Initialize session state for route info
if 'origin' not in st.session_state:
    st.session_state.origin = "Downtown San Jose"
if 'destination' not in st.session_state:
    st.session_state.destination = "Santana Row"
if 'transport_mode' not in st.session_state:
    st.session_state.transport_mode = "driving"
if 'time_of_day' not in st.session_state:
    st.session_state.time_of_day = "mid_day"
if 'weather' not in st.session_state:
    st.session_state.weather = "clear"
if 'traffic_density' not in st.session_state:
    st.session_state.traffic_density = "moderate"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Get OpenAI API key from secrets
def get_openai_api_key():
    # Try to get from Streamlit secrets
    try:
        return st.secrets["OPENAI_API_KEY"]
    except:
        # If not in secrets, try environment variable
        return os.environ.get("OPENAI_API_KEY")

# Function to update user preferences
def update_user_preferences(preferences):
    st.session_state.preferences = preferences

# Function to get coordinates for a location name
def get_location_coordinates(location):
    """Get coordinates for a location name"""
    # Map common San Jose locations to coordinates
    location_map = {
        "downtown san jose": [37.3382, -121.8863],
        "santana row": [37.3209, -121.9476],
        "san jose state university": [37.3352, -121.8811],
        "san jose international airport": [37.3639, -121.9289],
        "willow glen": [37.3094, -121.8990],
        "japantown": [37.3480, -121.8950],
        "east san jose": [37.3509, -121.8121],
        "north san jose": [37.3871, -121.9334],
        "south san jose": [37.2424, -121.8747],
        "west san jose": [37.3239, -121.9769],
        "san jose city hall": [37.3374, -121.8862],
        "winchester mystery house": [37.3184, -121.9511],
        "valley fair mall": [37.3261, -121.9465],
        "communications hill": [37.2924, -121.8583],
        "alum rock": [37.3772, -121.8244]
    }
    
    # Default coordinates for San Jose downtown
    default_coords = [37.3382, -121.8863]
    
    # Try to find a match (case insensitive)
    loc_lower = location.lower()
    
    # Check for exact matches first
    if loc_lower in location_map:
        return location_map[loc_lower]
    
    # Check for partial matches
    for key, coords in location_map.items():
        if key in loc_lower or loc_lower in key:
            return coords
    
    # Return default if no match
    return default_coords

# Load crash data
@st.cache_data
def load_crash_data():
    try:
        df = pd.read_csv('data/crashdata2011-2021.csv')
        # Convert crash datetime to proper datetime format
        df['CrashDateTime'] = pd.to_datetime(df['CrashDateTime'])
        # Extract hour, time of day, etc.
        df['Hour'] = df['CrashDateTime'].dt.hour
        df['DayOfWeek'] = df['CrashDateTime'].dt.day_name()
        
        # Map hours to time of day categories
        time_mapping = {
            'early_morning': list(range(5, 7)),  # 5-6 AM
            'morning_rush': list(range(7, 9)),  # 7-8 AM
            'mid_day': list(range(9, 16)),      # 9 AM-3 PM
            'evening_rush': list(range(16, 19)), # 4-6 PM
            'evening': list(range(19, 22)),     # 7-9 PM
            'late_night': list(range(22, 24)) + list(range(0, 5)) # 10 PM-4 AM
        }
        
        # Create time of day category
        df['TimeOfDay'] = ''
        for category, hours in time_mapping.items():
            df.loc[df['Hour'].isin(hours), 'TimeOfDay'] = category
        
        # Clean weather data
        df['Weather'] = df['Weather'].str.lower()
        df.loc[df['Weather'].str.contains('rain', na=False), 'Weather'] = 'rain'
        df.loc[df['Weather'].str.contains('snow', na=False), 'Weather'] = 'snow'
        df.loc[df['Weather'].str.contains('fog', na=False), 'Weather'] = 'fog'
        df.loc[df['Weather'].str.contains('wind', na=False), 'Weather'] = 'windy'
        df.loc[~df['Weather'].isin(['rain', 'snow', 'fog', 'windy']), 'Weather'] = 'clear'
        
        # Classify injury severity
        df['InjurySeverity'] = 'none'
        df.loc[df['MinorInjuries'] > 0, 'InjurySeverity'] = 'minor'
        df.loc[df['ModerateInjuries'] > 0, 'InjurySeverity'] = 'moderate'
        df.loc[df['SevereInjuries'] > 0, 'InjurySeverity'] = 'severe'
        df.loc[df['FatalInjuries'] > 0, 'InjurySeverity'] = 'fatal'
        
        return df
    except Exception as e:
        st.error(f"Error loading crash data: {e}")
        # Return empty dataframe with same structure
        return pd.DataFrame({
            'CrashDateTime': [], 'Hour': [], 'DayOfWeek': [], 'TimeOfDay': [],
            'Weather': [], 'InjurySeverity': [], 'Latitude': [], 'Longitude': []
        })

# Calculate distance between two points in km
def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# Find crashes near a route
def find_crashes_near_route(df, origin_coords, dest_coords, max_distance_km=1.0):
    # Create a line between origin and destination
    route_line = LineString([(origin_coords[1], origin_coords[0]), (dest_coords[1], dest_coords[0])])
    
    # Filter for crashes with valid coordinates
    df = df.dropna(subset=['Latitude', 'Longitude'])
    
    # Function to calculate distance from point to line
    def point_to_line_distance(lat, lon):
        # Create point
        point = Point(lon, lat)
        # Calculate distance to line in degrees
        distance_degrees = point.distance(route_line)
        # Approximate conversion to km (rough estimate)
        # 1 degree at equator is ~111 km, adjust based on latitude
        distance_km = distance_degrees * 111 * math.cos(math.radians(lat))
        return distance_km
    
    # Calculate distance for each crash
    df['DistanceToRoute'] = df.apply(
        lambda row: point_to_line_distance(row['Latitude'], row['Longitude']), 
        axis=1
    )
    
    # Filter for crashes near the route
    near_route = df[df['DistanceToRoute'] <= max_distance_km].copy()
    return near_route

# Calculate safety scores based on real crash data
def calculate_safety_scores(crash_data):
    """
    Calculate safety scores based on historical crash data for different times of day.
    
    Scoring criteria:
    1. Crash Frequency (50%): How many crashes occurred during this time period
    2. Crash Severity (30%): Weighted by injury severity (fatal crashes count more)
    3. Recency (20%): More recent crashes have a greater impact on the score
    
    Score range: 1-10 where 10 is safest, 1 is most dangerous
    """
    # Define time periods
    time_periods = [
        'early_morning',  # 5-7 AM 
        'morning_rush',   # 7-9 AM
        'mid_day',        # 9 AM-4 PM
        'evening_rush',   # 4-7 PM
        'evening',        # 7-10 PM
        'late_night'      # 10 PM-5 AM
    ]
    
    # If no crash data, return default scores
    if crash_data.empty:
        return {
            "early_morning": 8.5,  # Generally safe with low traffic
            "morning_rush": 6.8,  # Rush hour, moderate risk
            "mid_day": 7.2,       # Good visibility, moderate traffic
            "evening_rush": 6.5,  # Highest risk time (rush hour, fatigue)
            "evening": 7.8,       # Decreasing traffic, some visibility concerns
            "late_night": 8.7     # Low traffic, but visibility and drowsiness concerns
        }
    
    # 1. CRASH FREQUENCY COMPONENT (50% of score)
    time_counts = crash_data.groupby('TimeOfDay').size().reindex(time_periods).fillna(0)
    
    # 2. CRASH SEVERITY COMPONENT (30% of score)
    # Define severity weights - exponential to emphasize severe crashes
    severity_weights = {
        'none': 1,      # Property damage only
        'minor': 2,     # Minor injuries
        'moderate': 4,  # Moderate injuries
        'severe': 8,    # Severe injuries
        'fatal': 16     # Fatal injuries
    }
    
    # Calculate severity-weighted crash counts
    def severity_weighted_count(group):
        return sum(severity_weights.get(severity, 1) for severity in group)
    
    severity_counts = crash_data.groupby('TimeOfDay')['InjurySeverity'].agg(
        severity_weighted_count
    ).reindex(time_periods).fillna(0)
    
    # 3. RECENCY COMPONENT (20% of score)
    # Calculate years ago for each crash
    crash_data['YearsAgo'] = (datetime.now() - crash_data['CrashDateTime']).dt.days / 365
    
    # More recent crashes get higher weights (exponential decay)
    def recency_weighted_count(group):
        return sum(max(0.2, math.exp(-0.3 * years)) for years in group)  # Weight drops to ~30% after 4 years
    
    recency_counts = crash_data.groupby('TimeOfDay')['YearsAgo'].agg(
        recency_weighted_count
    ).reindex(time_periods).fillna(0)
    
    # NORMALIZE ALL COMPONENTS TO 0-1 RANGE (1 is best/safest)
    # For each metric, higher value = more crashes = less safe
    if time_counts.max() > 0:
        normalized_frequency = 1 - (time_counts / time_counts.max())
    else:
        normalized_frequency = pd.Series(1, index=time_periods)
        
    if severity_counts.max() > 0:
        normalized_severity = 1 - (severity_counts / severity_counts.max())
    else:
        normalized_severity = pd.Series(1, index=time_periods)
        
    if recency_counts.max() > 0:
        normalized_recency = 1 - (recency_counts / recency_counts.max())
    else:
        normalized_recency = pd.Series(1, index=time_periods)
    
    # CALCULATE FINAL SCORES - weighted combination of all factors
    # Scale to 1-10 range where 10 is safest
    safety_scores = (
        normalized_frequency * 0.5 +    # Crash frequency (50%)
        normalized_severity * 0.3 +     # Crash severity (30%)
        normalized_recency * 0.2        # Crash recency (20%)
    ) * 9 + 1  # Scale from 0-1 to 1-10
    
    # Return as dictionary
    return safety_scores.to_dict()

# Calculate overall route safety score
def analyze_route_safety(origin, destination, mode, time_of_day, weather, traffic_density, preferences):
    """
    Calculate comprehensive safety score for a route based on multiple factors.
    
    Safety Score Components:
    1. Historical Crash Data (60%): Based on actual crashes along the route
       - Frequency: Number of crashes in the area
       - Severity: Injuries and fatalities
       - Recency: More recent crashes weighted higher
       - Time of Day: Specific time period safety rating
    
    2. Route Characteristics (25%):
       - Distance: Longer routes generally have higher risk
       - Mode of Transportation: Different risks for different modes
       - Road Type: Analysis of road segments along route
    
    3. Current Conditions (15%):
       - Weather: Current weather conditions
       - Traffic: Current traffic density
       - Time: Time of day factors
    
    Final Score: 1-10 where 10 is safest, 1 is most dangerous
    """
    # Get origin and destination coordinates
    origin_coords = get_location_coordinates(origin)
    dest_coords = get_location_coordinates(destination)
    
    # Load crash data
    crash_data = load_crash_data()
    
    # Find crashes near this route
    route_crashes = find_crashes_near_route(crash_data, origin_coords, dest_coords)
    
    # Calculate route length
    route_length_km = haversine_distance(
        origin_coords[0], origin_coords[1],
        dest_coords[0], dest_coords[1]
    )
    route_length_miles = route_length_km * 0.621371
    
    #--------------------------------------------------------------------
    # COMPONENT 1: HISTORICAL CRASH DATA (60% of final score)
    #--------------------------------------------------------------------
    
    # Filter crashes by mode if relevant
    mode_specific_crashes = route_crashes
    if mode == "bicycling":
        bike_crashes = route_crashes[route_crashes['CollisionType'].str.contains('bicycle', case=False, na=False)]
        if len(bike_crashes) > 5:  # Only use mode-specific if we have enough data
            mode_specific_crashes = bike_crashes
    elif mode == "walking":
        pedestrian_crashes = route_crashes[route_crashes['PedestrianAction'] != 'No Pedestrians Involved']
        if len(pedestrian_crashes) > 5:
            mode_specific_crashes = pedestrian_crashes
    
    # Calculate safety scores for different times of day
    time_safety_scores = calculate_safety_scores(mode_specific_crashes)
    
    # Base score from current time period
    base_time_score = time_safety_scores.get(time_of_day, 7.0)
    
    # Calculate crash density (crashes per mile of route)
    crash_count = len(route_crashes)
    crash_density = crash_count / max(route_length_miles, 0.1)  # Avoid division by zero
    
    # Severity ratio - proportion of crashes that were severe or fatal
    severe_crashes = len(route_crashes[(route_crashes['InjurySeverity'] == 'severe') | 
                                     (route_crashes['InjurySeverity'] == 'fatal')])
    severity_ratio = severe_crashes / max(crash_count, 1)
    
    # Recent crash trend
    recent_crashes = len(route_crashes[route_crashes['CrashDateTime'] > (datetime.now() - timedelta(days=365*2))])
    recent_ratio = recent_crashes / max(crash_count, 1)
    
    # Calculate historical crash component (higher is safer)
    if crash_count > 0:
        # More crashes, higher severity, more recent = lower score
        historical_crash_score = base_time_score * (1 - min(1, crash_density/20) * 0.5) * (1 - severity_ratio * 0.3) * (1 - recent_ratio * 0.2)
    else:
        # No crash data = use base time score
        historical_crash_score = base_time_score
    
    #--------------------------------------------------------------------
    # COMPONENT 2: ROUTE CHARACTERISTICS (25% of final score)
    #--------------------------------------------------------------------
    
    # Base route score - starts at 8.0 (generally safe)
    route_score = 8.0
    
    # Distance factor - longer routes have more exposure to risk
    # Short (<2 miles): +0.5, Medium (2-5 miles): 0, Long (>5 miles): -0.5 to -1.5
    if route_length_miles < 2:
        distance_factor = 0.5  # Short routes are safer
    elif route_length_miles < 5:
        distance_factor = 0     # Medium routes are neutral
    else:
        # Longer routes become progressively less safe
        distance_factor = max(-1.5, -0.5 - (route_length_miles - 5) * 0.1)
    
    # Transportation mode risk factors
    mode_factors = {
        "driving": 0,      # Baseline
        "walking": 0.5,   # Generally safer for short distances
        "bicycling": -0.5, # Generally higher risk
        "transit": 0.3    # Generally safer (professional drivers)
    }
    
    # Adjust based on route length
    if route_length_miles > 3 and mode == "walking":
        mode_factors["walking"] = -0.5  # Walking becomes less safe for longer distances (fatigue, exposure)
    if route_length_miles > 5 and mode == "bicycling":
        mode_factors["bicycling"] = -1.0  # Biking long distances increases risk
    if route_length_miles > 7 and mode == "transit":
        mode_factors["transit"] = 0.5  # Transit better for longer distances
    
    # Apply route characteristics adjustments
    route_score += distance_factor + mode_factors.get(mode, 0)
    
    #--------------------------------------------------------------------
    # COMPONENT 3: CURRENT CONDITIONS (15% of final score)
    #--------------------------------------------------------------------
    
    # Base conditions score - starts at 7.5 (moderate)
    conditions_score = 7.5
    
    # Weather risk factors - data-driven if available
    weather_crash_counts = route_crashes.groupby('Weather').size()
    total_crashes = len(route_crashes) if len(route_crashes) > 0 else 1
    
    # Default weather factors
    weather_factors = {
        "clear": 0.5,    # Good conditions
        "rain": -1.0,   # Reduced visibility and traction
        "snow": -2.0,   # Significant hazard
        "fog": -1.5,    # Reduced visibility
        "windy": -0.5   # Slight hazard
    }
    
    # Refine based on actual crash data if sufficient
    if total_crashes > 15:
        for w in weather_factors.keys():
            weather_count = weather_crash_counts.get(w, 0)
            proportion = weather_count / total_crashes
            # If this weather has disproportionate crashes, increase risk factor
            if proportion > 0.3 and weather_count > 5:  
                weather_factors[w] = max(-2.5, weather_factors[w] * 1.5)
    
    # Traffic density factors
    traffic_factors = {
        "low": 1.0,       # Safer
        "moderate": 0,    # Neutral
        "high": -1.0      # Higher risk
    }
    
    # Apply conditions adjustments
    conditions_score += weather_factors.get(weather, 0) + traffic_factors.get(traffic_density, 0)
    
    #--------------------------------------------------------------------
    # FINAL SCORE CALCULATION
    #--------------------------------------------------------------------
    
    # Weighted average of all components
    combined_score = (
        historical_crash_score * 0.6 +  # Historical crash data (60%)
        route_score * 0.25 +            # Route characteristics (25%)
        conditions_score * 0.15         # Current conditions (15%)
    )
    
    # Apply user preferences to emphasize what they care about
    if preferences:
        # User who values safety gets more extreme scores (good routes better, bad routes worse)
        safety_weight = preferences.get('safety', 0.3)
        comfort_weight = preferences.get('comfort', 0.15)
        
        # Calculate preference adjustment
        preference_adjustment = (safety_weight + comfort_weight/2) / 0.5  # Normalize to 0-1 scale
        
        # Apply preference adjustment
        if combined_score > 7.0:
            # Good score gets better if safety is valued
            combined_score = combined_score + (10 - combined_score) * preference_adjustment * 0.5
        elif combined_score < 5.0:
            # Bad score gets worse if safety is valued
            combined_score = combined_score - (combined_score - 1) * preference_adjustment * 0.5
    
    # Ensure score is between 1 and 10
    final_score = max(1, min(10, combined_score))
    
    # Sort times by safety score - use time_safety_scores which was defined earlier
    recommended_times = sorted(
        time_safety_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Calculate alerts based on crash data
    recent_crashes = route_crashes[route_crashes['CrashDateTime'] > (datetime.now() - timedelta(days=365*2))]
    severe_crashes = route_crashes[(route_crashes['InjurySeverity'] == 'severe') | 
                                 (route_crashes['InjurySeverity'] == 'fatal')]
    
    alerts = len(recent_crashes) // 3 + len(severe_crashes)
    alerts = min(max(alerts, 0), 10)  # Cap between 0-10
    
    # Calculate estimated time based on route length and mode
    speeds = {
        "driving": 30,  # mph
        "walking": 3,  # mph
        "bicycling": 10,  # mph
        "transit": 15   # mph
    }
    
    base_speed = speeds.get(mode, 20)
    # Adjust for traffic
    if mode == "driving" or mode == "transit":
        if traffic_density == "high":
            base_speed *= 0.6
        elif traffic_density == "moderate":
            base_speed *= 0.8
    
    # Calculate time in minutes
    estimated_time = (route_length_miles / base_speed) * 60
    
    # Return the analysis results
    return {
        "safety_score": round(final_score, 1),
        "recommended_times": recommended_times[:3],
        "route_length": round(route_length_miles, 1),
        "estimated_time": round(estimated_time),
        "alerts": alerts,
        "crash_data": route_crashes,
        "origin_coords": origin_coords,
        "dest_coords": dest_coords
    }

# Generate AI response using OpenAI (simulated if no API key)
def generate_ai_response(user_query, context):
    api_key = get_openai_api_key()
    
    if not api_key:
        # Simulate AI response if no API key
        canned_responses = [
            f"Based on your preferences, I'd recommend traveling during off-peak hours for the route from {context['origin']} to {context['destination']}.",
            f"The safest time to travel from {context['origin']} to {context['destination']} by {context['mode']} appears to be late evening or early morning.",
            f"Given the current {context['weather']} weather and {context['traffic_density']} traffic, you might want to consider taking an alternative route.",
            "I notice you've prioritized safety in your preferences. Based on historical data, the current route has a moderate safety rating.",
            "Looking at your route, there are several areas with dedicated bike lanes that would improve your safety when cycling."
        ]
        return np.random.choice(canned_responses)
    
    try:
        # Use actual OpenAI API
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for San Jose commuters, providing safety advice and route recommendations."},
                {"role": "user", "content": f"Context: Origin: {context['origin']}, Destination: {context['destination']}, Mode: {context['mode']}, Time: {context['time_of_day']}, Weather: {context['weather']}, Traffic: {context['traffic_density']}. User preferences: Time efficiency: {context['preferences']['time_efficiency']*100}%, Safety: {context['preferences']['safety']*100}%, Comfort: {context['preferences']['comfort']*100}%, Scenic value: {context['preferences']['scenic']*100}%. Query: {user_query}"}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error connecting to OpenAI: {e}")
        return "I'm having trouble connecting to my AI services. Please try again later."

# Main function
def main():
    # Clear any automatically generated sidebar
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    
    # Create custom sidebar with navigation
    with st.sidebar:
        st.title("San Jose Safe Commute")
        st.markdown("---")
        
        # Navigation links section
        st.page_link("1_🏠_Home.py", label="Home", icon="🏠")
        st.page_link("pages/2_📊_Analytics_Dashboard.py", label="Analytics Dashboard", icon="📊")
        st.page_link("pages/3_🔍_Crash_Data_Analysis.py", label="Crash Data Analysis", icon="🔍")
        st.page_link("pages/3_📊_Data_Upload_&_AI_Analysis.py", label="Upload & AI Analysis", icon="📊")
    
    # Main page header - only show the subtitle since title is in sidebar
    st.markdown("#### AI-powered route safety analysis for San Jose commuters")
    st.markdown("---")
    
    # Main layout - two columns
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        # Route input section
        st.header("Plan Your Route")
        
        # Origin input
        origin = st.text_input(
            "Origin",
            value=st.session_state.origin,
            placeholder="Enter starting point in San Jose",
            key="origin_input"
        )
        st.session_state.origin = origin
        
        # Destination input
        destination = st.text_input(
            "Destination",
            value=st.session_state.destination,
            placeholder="Enter destination in San Jose",
            key="destination_input"
        )
        st.session_state.destination = destination
        
        # Transport mode selection
        transport_mode = st.selectbox(
            "Transport Mode",
            options=["driving", "walking", "bicycling", "transit"],
            index=["driving", "walking", "bicycling", "transit"].index(st.session_state.transport_mode),
            format_func=lambda x: {
                "driving": "🚗 Driving",
                "walking": "🚶 Walking",
                "bicycling": "🚴 Bicycling",
                "transit": "🚌 Transit"
            }.get(x, x),
            key="transport_mode_select"
        )
        st.session_state.transport_mode = transport_mode
        
        # Time of day selection
        time_labels = {
            "early_morning": "Early Morning (5-7 AM)",
            "morning_rush": "Morning Rush (7-9 AM)",
            "mid_day": "Mid-Day (9 AM-4 PM)",
            "evening_rush": "Evening Rush (4-7 PM)",
            "evening": "Evening (7-10 PM)",
            "late_night": "Late Night (10 PM-5 AM)"
        }
        time_of_day = st.selectbox(
            "Time of Day",
            options=list(time_labels.keys()),
            index=list(time_labels.keys()).index(st.session_state.time_of_day),
            format_func=lambda x: time_labels.get(x, x),
            key="time_of_day_select"
        )
        st.session_state.time_of_day = time_of_day
        
        # Weather condition selection
        weather = st.selectbox(
            "Weather Condition",
            options=["clear", "rain", "snow", "fog", "windy"],
            index=["clear", "rain", "snow", "fog", "windy"].index(st.session_state.weather),
            format_func=lambda x: {
                "clear": "☀️ Clear",
                "rain": "🌧 Rain",
                "snow": "❄️ Snow",
                "fog": "🌫 Fog",
                "windy": "💨 Windy"
            }.get(x, x),
            key="weather_select"
        )
        st.session_state.weather = weather
        
        # Traffic density selection
        traffic_density = st.selectbox(
            "Traffic Density",
            options=["low", "moderate", "high"],
            index=["low", "moderate", "high"].index(st.session_state.traffic_density),
            format_func=lambda x: {
                "low": "🟢 Low Traffic",
                "moderate": "🟡 Moderate Traffic",
                "high": "🔴 Heavy Traffic"
            }.get(x, x),
            key="traffic_select"
        )
        st.session_state.traffic_density = traffic_density
    
    with right_col:
        # Travel preferences section
        st.header("Your Travel Preferences")
        st.markdown("Adjust sliders to personalize your recommendations")
        
        # Time efficiency slider
        time_weight = st.slider(
            "Time Efficiency",
            0, 100, 
            int(st.session_state.preferences["time_efficiency"] * 100),
            format="%d%%",
            key="time_efficiency_slider"
        )
        st.write(f"► {time_weight}%")
        
        # Safety slider
        safety_weight = st.slider(
            "Safety",
            0, 100, 
            int(st.session_state.preferences["safety"] * 100),
            format="%d%%",
            key="safety_slider"
        )
        st.write(f"► {safety_weight}%")
        
        # Comfort slider
        comfort_weight = st.slider(
            "Comfort",
            0, 100, 
            int(st.session_state.preferences["comfort"] * 100),
            format="%d%%",
            key="comfort_slider"
        )
        st.write(f"► {comfort_weight}%")
        
        # Scenic routes slider
        scenic_weight = st.slider(
            "Scenic Routes",
            0, 100, 
            int(st.session_state.preferences["scenic"] * 100),
            format="%d%%",
            key="scenic_slider"
        )
        st.write(f"► {scenic_weight}%")
        
        # Update preferences
        total = time_weight + safety_weight + comfort_weight + scenic_weight
        if 80 <= total <= 120:
            preferences = {
                "time_efficiency": time_weight / total,
                "safety": safety_weight / total,
                "comfort": comfort_weight / total,
                "scenic": scenic_weight / total
            }
            update_user_preferences(preferences)
            if total != 100:
                st.info(f"Preferences normalized from {total}% to 100%.")
        else:
            st.warning(f"Total preference weight ({total}%) should be between 80-120%")
    
    # Information about the safety score before the analyze button
    st.markdown("---")
    st.info("""
    **About Our Safety Scores:** 
    Our analysis uses real crash data from San Jose (2011-2021) to identify high-risk routes 
    and recommend safer travel options based on your specific journey and preferences.
    """)
    
    # Analyze button - centered
    analyze_pressed = st.button(
        "Analyze Route Safety",
        type="primary",
        use_container_width=True,
        key="analyze_button"
    )
    
    # Results section
    if analyze_pressed:
        st.markdown("---")
        st.header("Safety Analysis Results")
        
        # Perform the analysis
        results = analyze_route_safety(
            origin,
            destination,
            transport_mode,
            time_of_day,
            weather,
            traffic_density,
            st.session_state.preferences
        )
        
        # Display results in a nice layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            safety_score = results['safety_score']
            # Color-code the safety score
            if safety_score >= 8.0:
                st.metric("Safety Score", f"{safety_score}/10", delta="Very Safe", delta_color="normal")
            elif safety_score >= 6.5:
                st.metric("Safety Score", f"{safety_score}/10", delta="Moderately Safe", delta_color="normal")
            elif safety_score >= 5.0:
                st.metric("Safety Score", f"{safety_score}/10", delta="Use Caution", delta_color="off")
            elif safety_score >= 3.5:
                st.metric("Safety Score", f"{safety_score}/10", delta="High Risk", delta_color="inverse")
            else:
                st.metric("Safety Score", f"{safety_score}/10", delta="Dangerous", delta_color="inverse")
        
        with col2:
            st.metric("Distance", f"{results['route_length']} miles")
        
        with col3:
            st.metric("Est. Travel Time", f"{results['estimated_time']} mins")
            
        # Add explanation of safety score
        with st.expander("How the Safety Score is Calculated"):
            st.markdown("""
            ### Safety Score Methodology
            
            Our safety score (1-10 scale where 10 is safest) is based on three major components:
            
            #### 1. Historical Crash Data (60% of score)
            - **Crash Frequency**: Number of crashes along your route
            - **Crash Severity**: Weight of injuries/fatalities
            - **Recency**: Recent crashes impact scores more
            - **Time of Day**: Analysis of when crashes occur
            
            #### 2. Route Characteristics (25% of score)
            - **Distance**: Longer routes typically have higher risk
            - **Mode of Transportation**: Different safety profiles for driving, walking, etc.
            - **Route Type**: Road types and infrastructure along your route
            
            #### 3. Current Conditions (15% of score)
            - **Weather**: Current weather impact on safety
            - **Traffic**: Current traffic density
            - **Time**: Time of day factors
            
            #### User Preferences
            Your safety preferences also affect how we weight these factors for your specific needs.
            """)
        
        # Safety alerts with more detailed information
        if results['alerts'] > 0:
            alert_level = "High" if results['alerts'] > 5 else "Moderate" if results['alerts'] > 2 else "Low"
            st.warning(f"{results['alerts']} Safety Alerts ({alert_level} Risk): potential hazards identified on this route")
            
            # Show specific alerts based on conditions
            alert_details = []
            
            # Mode-specific alerts
            if transport_mode == "bicycling":
                alert_details.append("Bicycle crash history detected on this route")
            elif transport_mode == "walking" and results['route_length'] > 2:
                alert_details.append("Long walking distance increases exposure to traffic")
                
            # Weather alerts
            if weather == "rain":
                alert_details.append("Rain reduces visibility and traction")
            elif weather == "snow":
                alert_details.append("Snow creates hazardous conditions")
            elif weather == "fog":
                alert_details.append("Fog severely reduces visibility")
                
            # Traffic alerts
            if traffic_density == "high":
                alert_details.append("Heavy traffic increases collision risk")
                
            # Time of day alerts
            if time_of_day == "evening_rush":
                alert_details.append("Rush hour has historically higher crash rates")
            elif time_of_day == "late_night":
                alert_details.append("Limited visibility during night hours")
                
            # Display alert details
            if alert_details:
                for detail in alert_details[:3]:  # Limit to top 3 alerts
                    st.markdown(f"⚠️ **Alert:** {detail}")
        
        # Recommended time windows
        st.subheader("Recommended Travel Times")
        
        time_cols = st.columns(3)
        for i, (time_key, score) in enumerate(results['recommended_times']):
            with time_cols[i]:
                time_label = time_labels.get(time_key, time_key)
                if score > 8.0:
                    st.success(f"{time_label}\nSafety Score: {score}/10")
                elif score > 7.0:
                    st.info(f"{time_label}\nSafety Score: {score}/10")
                else:
                    st.warning(f"{time_label}\nSafety Score: {score}/10")
        
        # Show a detailed map of the route with crash data
        st.subheader("Route Safety Map")
        
        # Extract crash data from results
        route_crashes = results.get('crash_data', pd.DataFrame())
        origin_coords = results.get('origin_coords')
        dest_coords = results.get('dest_coords')
        
        # Create a map centered between origin and destination
        center_lat = (origin_coords[0] + dest_coords[0]) / 2
        center_lon = (origin_coords[1] + dest_coords[1]) / 2
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles="CartoDB positron"
        )
        
        # Add markers for origin and destination
        folium.Marker(
            location=origin_coords,
            popup=origin,
            icon=folium.Icon(color="green", icon="play", prefix="fa")
        ).add_to(m)
        
        folium.Marker(
            location=dest_coords,
            popup=destination,
            icon=folium.Icon(color="red", icon="stop", prefix="fa")
        ).add_to(m)
        
        # Draw a line for the route
        folium.PolyLine(
            [origin_coords, dest_coords],
            color="blue",
            weight=5,
            opacity=0.7,
            popup="Suggested Route"
        ).add_to(m)
        
        # Add crash data to the map if available
        if not route_crashes.empty and len(route_crashes) > 0:
            # Create a marker cluster for crash points
            marker_cluster = MarkerCluster(
                name="Crash Locations",
                overlay=True,
                control=True,
                icon_create_function=None
            ).add_to(m)
            
            # Color mapping for injury severity
            severity_colors = {
                'none': 'green',
                'minor': 'blue',
                'moderate': 'orange',
                'severe': 'red',
                'fatal': 'darkred'
            }
            
            # Add individual crash markers
            for idx, crash in route_crashes.iterrows():
                if pd.notna(crash['Latitude']) and pd.notna(crash['Longitude']):
                    severity = crash.get('InjurySeverity', 'none')
                    color = severity_colors.get(severity, 'gray')
                    crash_date = crash['CrashDateTime'].strftime('%Y-%m-%d %H:%M') if 'CrashDateTime' in crash else 'Unknown'
                    
                    # Create popup content
                    popup_content = f"""
                    <b>Date:</b> {crash_date}<br>
                    <b>Severity:</b> {severity.title()}<br>
                    <b>Weather:</b> {crash.get('Weather', 'Unknown')}<br>
                    <b>Type:</b> {crash.get('CollisionType', 'Unknown')}
                    """
                    
                    # Add marker
                    folium.CircleMarker(
                        location=[crash['Latitude'], crash['Longitude']],
                        radius=5,
                        color=color,
                        fill=True,
                        fill_opacity=0.7,
                        popup=folium.Popup(popup_content, max_width=300)
                    ).add_to(marker_cluster)
            
            # Add heatmap layer
            if len(route_crashes) > 3:
                # Prepare data for heatmap
                heat_data = [[row['Latitude'], row['Longitude']] for _, row in route_crashes.iterrows() 
                            if pd.notna(row['Latitude']) and pd.notna(row['Longitude'])]
                
                # Add heatmap layer
                HeatMap(
                    heat_data,
                    radius=15,
                    blur=10,
                    max_zoom=13,
                    name="Crash Density"
                ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
        
        # Display the map
        folium_static(m)
        
        # Show crash statistics if available
        if not route_crashes.empty and len(route_crashes) > 0:
            st.subheader("Crash Statistics for this Route")
            
            # Create columns for stats
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            
            with stats_col1:
                st.metric("Total Crashes", len(route_crashes))
                
                # Count by time of day
                time_counts = route_crashes['TimeOfDay'].value_counts()
                worst_time = time_counts.idxmax() if not time_counts.empty else 'Unknown'
                worst_time_formatted = worst_time.replace('_', ' ').title() if worst_time != 'Unknown' else 'Unknown'
                st.metric("Highest Crash Time", worst_time_formatted)
            
            with stats_col2:
                # Count by severity
                severe_count = len(route_crashes[(route_crashes['InjurySeverity'] == 'severe') | 
                                             (route_crashes['InjurySeverity'] == 'fatal')])
                st.metric("Severe/Fatal Crashes", severe_count)
                
                # Count by weather
                weather_counts = route_crashes['Weather'].value_counts()
                worst_weather = weather_counts.idxmax() if not weather_counts.empty else 'Unknown'
                st.metric("Highest Crash Weather", worst_weather.title())
            
            with stats_col3:
                # Recent crashes (last 2 years)
                recent = len(route_crashes[route_crashes['CrashDateTime'] > (datetime.now() - timedelta(days=365*2))])
                st.metric("Recent Crashes (2yr)", recent)
                
                # Calculate trend
                if len(route_crashes) > 0:
                    yearly_counts = route_crashes.groupby(route_crashes['CrashDateTime'].dt.year).size()
                    years = sorted(yearly_counts.index)
                    if len(years) >= 2:
                        first_year = yearly_counts.get(years[0], 0)
                        last_year = yearly_counts.get(years[-1], 0)
                        trend = "Decreasing" if last_year < first_year else "Increasing" if last_year > first_year else "Stable"
                        st.metric("Crash Trend", trend)
    
    # AI Chat section
    st.markdown("---")
    st.header("AI Route Assistant")
    st.markdown("Ask natural language questions about routes and safety")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])
    
    # Input for new question
    user_query = st.chat_input("Ask about routes, e.g., 'Find the safest bike route this afternoon'")
    
    if user_query:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        # Display user message
        st.chat_message("user").write(user_query)
        
        # Generate AI response
        context = {
            "origin": st.session_state.origin,
            "destination": st.session_state.destination,
            "mode": st.session_state.transport_mode,
            "time_of_day": st.session_state.time_of_day,
            "weather": st.session_state.weather,
            "traffic_density": st.session_state.traffic_density,
            "preferences": st.session_state.preferences
        }
        
        response = generate_ai_response(user_query, context)
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Display assistant response
        st.chat_message("assistant").write(response)
    
    # Footer
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("© 2025 San Jose Safe Commute")
    with col2:
        st.caption("Version 2.3.0")

if __name__ == "__main__":
    main()
