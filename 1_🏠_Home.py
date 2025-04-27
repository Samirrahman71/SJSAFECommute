"""
San Jose Safe Commute - Enhanced Safety Analysis
An interactive tool to analyze route safety with AI assistance.
"""

import streamlit as st
import folium
import pandas as pd
import numpy as np
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
# Add parent directory to import path for direct running
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import app components
from enhanced_safety import get_enhanced_safety_analysis, display_enhanced_safety_timeline, enhance_safety_map, display_safety_recommendations
import utils  # Import utils for access to the original safety functions
from utils.departure_advisor import get_departure_recommendation, update_user_preferences

# Initialize session state if it doesn't exist
if 'last_analysis' not in st.session_state:
    # Initialize with default empty dictionary, not None
    st.session_state['last_analysis'] = {}

if 'last_origin' not in st.session_state:
    st.session_state['last_origin'] = "Downtown San Jose"
    
if 'last_destination' not in st.session_state:
    st.session_state['last_destination'] = "Santana Row, San Jose"
    
# Initialize departure advisor preferences in session state
if 'schedule_type' not in st.session_state:
    st.session_state['schedule_type'] = "moderate"
    
if 'arrival_time' not in st.session_state:
    # Default arrival time 30 minutes from now, rounded to nearest 5 minutes
    now = datetime.now() + timedelta(minutes=30)
    rounded_minutes = 5 * round(now.minute / 5)
    now = now.replace(minute=rounded_minutes % 60)
    if rounded_minutes >= 60:
        now = now.replace(hour=(now.hour + 1) % 24)
    st.session_state['arrival_time'] = now.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")

def main():
    """
    Enhanced safety analysis for San Jose Safe Commute.
    Run with: streamlit run test_safety.py
    """
    # Set page config for a cleaner look
    st.set_page_config(
        page_title="San Jose Safe Commute",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom responsive CSS for better UI on mobile and desktop
    with open('styles/responsive.css', 'r') as f:
        custom_css = f.read()
    
    st.markdown(f"""
    <style>
    {custom_css}
    </style>
    """, unsafe_allow_html=True)
    
    # App header with AI emphasis - using custom classes for responsive design
    st.markdown("""
    <div class="app-header animate-fadeIn">
        <h1 class="app-title">San Jose Safe Commute</h1>
        <p class="app-subtitle">Route Safety Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add preference learning section using custom classes
    st.markdown("---")
    st.markdown("""
    <div class="feature-section animate-fadeIn">
        <h2>Your Travel Preferences</h2>
        <p>Adjust these sliders to set your personal travel priorities. These will help us
        provide better recommendations for your commute:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # This text is now included in the HTML above
    pass
    
    # Create columns for preference sliders - wrapped in a card for better visual appearance
    st.markdown('<div class="card">', unsafe_allow_html=True)
    pref_col1, pref_col2 = st.columns(2)
    
    with pref_col1:
        time_weight = st.slider("Time Efficiency", 0, 100, 50, 5, 
                             format="%d%%", help="Prioritize fastest routes")
        safety_weight = st.slider("Safety", 0, 100, 30, 5, 
                               format="%d%%", help="Prioritize safer routes")
    
    with pref_col2:
        comfort_weight = st.slider("Comfort", 0, 100, 20, 5, 
                                format="%d%%", help="Prioritize routes with fewer transfers/stops")
        scenic_weight = st.slider("Scenic Routes", 0, 100, 10, 5, 
                               format="%d%%", help="Prioritize more scenic routes")
    
    # Only update preferences if total is reasonable (80%-120% range)
    total = time_weight + safety_weight + comfort_weight + scenic_weight
    if 80 <= total <= 120:
        # Normalize and update preferences
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
        st.warning(f"Total preference weight ({total}%) is outside the acceptable range (80-120%). Adjustments not saved.")
        
    # Close the card div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add footer with version and attribution
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; justify-content: space-between; font-size: 0.8em;">
        <span> 2025 San Jose Safe Commute</span>
        <span>Version 2.2.0</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced app description with AI capabilities - in a feature section
    st.markdown("""
    <div class="feature-section animate-fadeIn">
        <h2>Route Safety Analysis</h2>
        <p>This tool helps you stay safe while traveling in San Jose by providing:</p>
        <ul style="padding-left: 1.5rem;">
            <li><strong>Safety Insights</strong>: Based on your specific route</li>
            <li><strong>Time-of-Day Analysis</strong>: See when it's safest to travel</li>
            <li><strong>Weather & Traffic</strong>: How conditions affect your commute</li>
            <li><strong>Practical Tips</strong>: Simple ways to improve your safety</li>
        </ul>
        <p>Enter your starting point and destination below to get started:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a spacer for better layout
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create a card wrapper for the input section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Create a two-column layout for inputs
    col_input1, col_input2 = st.columns([1, 1])
    
    with col_input1:
        st.markdown('<h3 class="card-header">📍 Route Information</h3>', unsafe_allow_html=True)
        
        # Create a comprehensive list of San Jose addresses for autofill
        san_jose_addresses = [
            "San Jose State University, 1 Washington Square, San Jose, CA 95192",
            "Nutanix, 1740 Technology Dr, San Jose, CA 95110",
            "SAP Center, 525 W Santa Clara St, San Jose, CA 95113",
            "Santana Row, 377 Santana Row, San Jose, CA 95128",
            "Downtown San Jose, San Jose, CA 95113",
            "San Jose City Hall, 200 E Santa Clara St, San Jose, CA 95113",
            "San Jose International Airport, 1701 Airport Blvd, San Jose, CA 95110",
            "Winchester Mystery House, 525 S Winchester Blvd, San Jose, CA 95128",
            "The Tech Interactive, 201 S Market St, San Jose, CA 95113",
            "Japanese Friendship Garden, 1300 Senter Rd, San Jose, CA 95112",
            "Happy Hollow Park & Zoo, 1300 Senter Rd, San Jose, CA 95112",
            "Children's Discovery Museum, 180 Woz Way, San Jose, CA 95110",
            "Alum Rock Park, 15350 Penitencia Creek Rd, San Jose, CA 95127",
            "Municipal Rose Garden, 1649 Naglee Ave, San Jose, CA 95126",
            "Willow Glen, Lincoln Avenue, San Jose, CA 95125",
            "Westfield Valley Fair, 2855 Stevens Creek Blvd, Santa Clara, CA 95050",
            "Japantown, San Jose, CA 95112",
            "San Pedro Square Market, 87 N San Pedro St, San Jose, CA 95110",
            "Communication Hill, San Jose, CA 95136",
            "Kelley Park, 1300 Senter Rd, San Jose, CA 95112",
            "Guadalupe River Park, 438 Coleman Ave, San Jose, CA 95110",
            "Adobe Headquarters, 345 Park Ave, San Jose, CA 95110",
            "eBay Campus, 2025 Hamilton Ave, San Jose, CA 95125",
            "PayPal Campus, 2211 N 1st St, San Jose, CA 95131",
            "Cisco Systems, 170 W Tasman Dr, San Jose, CA 95134",
            "10th & William, San Jose, CA 95112",
            "1st & Santa Clara, San Jose, CA 95113",
            "Capitol Expressway & Tully Rd, San Jose, CA 95121",
            "Westgate Shopping Center, 1600 Saratoga Ave, San Jose, CA 95129",
            "Eastridge Mall, 2200 Eastridge Loop, San Jose, CA 95122"
        ]
        
        # For autofill origin - allow user to type and show matches
        # Use last origin or default
        default_origin = st.session_state.get('last_origin', "San Jose State University")
        
        origin_input = st.text_input(
            "Starting Address", 
            value=default_origin,
            placeholder="Start typing any address in San Jose", 
            key="origin_input"
        )
        
        # Filter addresses that match what user typed for origin
        origin_matches = [addr for addr in san_jose_addresses if origin_input.lower() in addr.lower()]
        
        # Show dropdown of matched addresses for origin
        if origin_matches:
            origin = st.selectbox(
                "Select from matching addresses", 
                options=origin_matches,
                index=0,
                key="origin_select"
            )
        else:
            # If no matches, use what the user typed
            origin = origin_input
        
        # Store the selected origin
        st.session_state['last_origin'] = origin
        
        # For autofill destination - similar approach
        # Use last destination or default
        default_destination = st.session_state.get('last_destination', "Santana Row, San Jose")
        
        destination_input = st.text_input(
            "Destination Address", 
            value=default_destination,
            placeholder="Start typing any address in San Jose", 
            key="destination_input"
        )
        
        # Filter addresses that match what user typed for destination
        destination_matches = [addr for addr in san_jose_addresses if destination_input.lower() in addr.lower() 
                              and addr != origin]  # Exclude the origin address
        
        # Show dropdown of matched addresses for destination
        if destination_matches:
            destination = st.selectbox(
                "Select from matching addresses", 
                options=destination_matches,
                index=0,
                key="destination_select"
            )
        else:
            # If no matches, use what the user typed
            destination = destination_input
            
        # Store the selected destination
        st.session_state['last_destination'] = destination
        
        # Add a note about address entry
        st.caption("📍 Type any address, place, or intersection in San Jose for Google Maps-like suggestions")
        
        # Improve the geocoding simulation
        def simulate_geocoding(location):
            """Simulate geocoding for demonstration purposes"""
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
    
    with col_input2:
        st.markdown('<h3 class="card-header">📅 Travel Conditions</h3>', unsafe_allow_html=True)
        
        # Adding time of day options with descriptive labels
        time_labels = {
            "early_morning": "Early Morning (5-7 AM)",
            "morning_rush": "Morning Rush Hour (7-9 AM)",
            "mid_day": "Mid-Day (9 AM-4 PM)",
            "evening_rush": "Evening Rush Hour (4-7 PM)",
            "evening": "Evening (7-10 PM)",
            "late_night": "Late Night (10 PM-5 AM)"
        }
        
        # Get current hour to suggest appropriate time of day
        current_hour = datetime.now().hour
        default_time = "mid_day"
        if 5 <= current_hour < 7:
            default_time = "early_morning"
        elif 7 <= current_hour < 9:
            default_time = "morning_rush"
        elif 9 <= current_hour < 16:
            default_time = "mid_day"
        elif 16 <= current_hour < 19:
            default_time = "evening_rush"
        elif 19 <= current_hour < 22:
            default_time = "evening"
        else:
            default_time = "late_night"
        
        # Transportation mode with icons
        mode = st.selectbox(
            "🚗 Transportation Mode", 
            ["driving", "walking", "bicycling", "transit"],
            format_func=lambda x: {
                "driving": "🚗 Driving",
                "walking": "🚶 Walking",
                "bicycling": "🚴 Bicycling",
                "transit": "🚌 Transit"
            }.get(x, x),
            index=0
        )
        
        # Time of day selector with proper labels
        time_index = list(time_labels.keys()).index(default_time)
        
        time_of_day = st.selectbox(
            "🕰 Time of Day",
            list(time_labels.keys()),
            format_func=lambda x: time_labels.get(x, x),
            index=time_index
        )
        
        # Weather condition with icons
        default_weather = 'clear'
        weather_options = ["clear", "rain", "fog", "snow", "storm"]
        weather_index = weather_options.index(default_weather)
        
        weather = st.selectbox(
            "🌤️ Weather Condition",
            weather_options,
            format_func=lambda x: {
                "clear": "☀️ Clear",
                "rain": "🌧️ Rain",
                "fog": "🌫️ Fog",
                "snow": "❄️ Snow",
                "storm": "⚡ Storm"
            }.get(x, x),
            index=weather_index
        )
        
        # Traffic density with visual cues
        default_traffic = 'medium'
        traffic_options = ["low", "medium", "high"]
        traffic_index = traffic_options.index(default_traffic)
        
        traffic_density = st.selectbox(
            "🚘 Traffic Density",
            traffic_options,
            format_func=lambda x: {
                "low": "🟢 Low Traffic",
                "medium": "🟡 Medium Traffic",
                "high": "🔴 Heavy Traffic"
            }.get(x, x),
            index=traffic_index
        )
    
    # Load environment variables
    load_dotenv()

    # Try to get API keys from Streamlit secrets first, then fall back to environment variables
    try:
        GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    except:
        GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
        
    try:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    except:
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # This is just a placeholder - the actual button is below
    
    # Convert locations to coordinates using our simulation function
    origin_coords = simulate_geocoding(origin)
    dest_coords = simulate_geocoding(destination)
    
    # Create a simple route by connecting origin and destination with intermediate points
    def create_simulated_route(origin, destination):
        """Create a simulated route between two points with a slight curve"""
        # Extract coordinates
        start_lat, start_lng = origin
        end_lat, end_lng = destination
        
        # Create a list to hold route points
        route = []
        
        # Add starting point
        route.append([start_lat, start_lng])
        
        # Create intermediate points for a more realistic route
        steps = 6  # Number of intermediate points
        for i in range(1, steps):
            # Linear interpolation with a slight randomization for curve
            progress = i / steps
            lat = start_lat + (end_lat - start_lat) * progress
            lng = start_lng + (end_lng - start_lng) * progress
            
            # Add a slight curve - higher in the middle, less at ends
            curve_factor = progress * (1 - progress) * 0.01  # Controls curve magnitude
            perpendicular_offset = curve_factor * 4 * (np.random.random() - 0.5)
            
            # Apply perpendicular offset
            # Simplified - assuming small distances where Earth's curvature doesn't matter much
            lat += perpendicular_offset
            lng += perpendicular_offset
            
            route.append([lat, lng])
        
        # Add ending point
        route.append([end_lat, end_lng])
        
        return route
    
    # Create route coordinates
    route_coords = create_simulated_route(origin_coords, dest_coords)
    
    # Create simulated incidents (safety hotspots) along and near route
    def create_simulated_incidents(route, count=5):
        """Create simulated safety incidents near the route"""
        incidents = []
        
        # Add incidents along the route
        for _ in range(count):
            # Pick a random segment of the route
            segment_idx = np.random.randint(0, len(route) - 1)
            point1 = route[segment_idx]
            point2 = route[segment_idx + 1]
            
            # Interpolate a random point along this segment
            t = np.random.random()  # Value between 0 and 1
            lat = point1[0] + (point2[0] - point1[0]) * t
            lng = point1[1] + (point2[1] - point1[1]) * t
            
            # Add some random offset to make it near but not exactly on the route
            offset = 0.005 * (np.random.random() - 0.5)  # About 500m max
            lat += offset
            lng += offset
            
            incidents.append([lat, lng])
        
        return incidents
    
    # Simulate incidents
    incident_coords = create_simulated_incidents(route_coords, count=7)
    
    # Analysis button - make it more prominent
    analyze_button = st.button("Analyze Route Safety", type="primary", use_container_width=True)
    
    # Close the card div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Only perform analysis when the button is clicked or inputs change
    if analyze_button or 'last_analysis' not in st.session_state or not st.session_state['last_analysis']:
        with st.spinner("Analyzing route safety..."):
            try:
                # Get enhanced analysis using our safety API
                safety_data = get_enhanced_safety_analysis(
                    origin=origin,
                    destination=destination,
                    time_of_day=time_of_day,
                    weather=weather,
                    mode=mode,
                    traffic_density=traffic_density
                )
                
                # Ensure we got a dictionary back
                if safety_data is None:
                    safety_data = {}
                    st.warning("Could not retrieve AI safety analysis. Using local model.")
                    
                    # Fallback to original safety prediction function from utils
                    # Calculate risk score based on input parameters
                    risk_score = 5.0  # Base score
                    
                    # Adjust based on time of day
                    time_risk_map = {
                        "early_morning": -1.5,  # Safer
                        "morning_rush": 1.5,   # Riskier
                        "mid_day": 0,         # Neutral
                        "evening_rush": 2.0,   # Riskier
                        "evening": 0.5,        # Slightly riskier
                        "late_night": -1.0     # Safer
                    }
                    risk_score += time_risk_map.get(time_of_day, 0)
                    
                    # Adjust based on weather
                    weather_risk_map = {
                        "clear": 0,      # Neutral
                        "rain": 1.5,     # Riskier
                        "fog": 2.0,      # Riskier
                        "snow": 2.5,     # Much riskier
                        "storm": 3.0     # Most risky
                    }
                    risk_score += weather_risk_map.get(weather, 0)
                    
                    # Adjust based on traffic density
                    traffic_risk_map = {
                        "low": -1.0,     # Safer
                        "medium": 0.5,   # Slightly riskier
                        "high": 2.0      # Much riskier
                    }
                    risk_score += traffic_risk_map.get(traffic_density, 0)
                    
                    # Normalize to 0-10 scale
                    risk_score = max(0, min(10, risk_score))
                    safety_score = 10 - risk_score  # Invert for safety score
                    
                    # Generate safety predictions using the original function
                    risk_factors = {
                        "time_of_day": time_of_day,
                        "weather": weather,
                        "traffic_density": traffic_density,
                        "day_of_week": datetime.now().strftime("%A").lower()
                    }
                    
                    try:
                        time_predictions = utils.get_safety_time_predictions(origin, destination, safety_score, risk_factors)
                        
                        # Format the time predictions for display
                        formatted_predictions = {}
                        for time_label, score in time_predictions.items():
                            # Convert the time labels to the format used in our UI
                            formatted_predictions[time_label] = float(score)
                        
                        # Build a safety data object compatible with our display functions
                        safety_data = {
                            "safety_score": round(safety_score, 1),
                            "color": "green" if safety_score >= 8 else "yellow" if safety_score >= 6 else "red",
                            "time_predictions": formatted_predictions,
                            "alerts": [
                                {"coords": incident, "text": utils.get_hotspot_tip("high" if i % 3 == 0 else "medium", "evening"), "severity": "high" if i % 3 == 0 else "med"}
                                for i, incident in enumerate(incident_coords)
                            ],
                            "top_reasons": [
                                f"Traffic density is {traffic_density}",
                                f"Weather conditions: {weather}",
                                f"Time of day: {time_labels.get(time_of_day, time_of_day)}"
                            ],
                            "tip": {
                                "badge": "car" if mode == "driving" else "umbrella" if weather in ["rain", "storm"] else "bicycle" if mode == "bicycling" else "car",
                                "text": utils.get_hotspot_tip("medium", time_of_day)
                            }
                        }
                    except Exception as e:
                        st.error(f"Error using fallback safety prediction: {str(e)}")
                
                # Store in session state
                st.session_state['last_analysis'] = safety_data
                st.session_state['last_origin'] = origin
                st.session_state['last_destination'] = destination
                st.session_state['route_coords'] = route_coords
                st.session_state['incident_coords'] = incident_coords
                st.session_state['origin_coords'] = origin_coords
                st.session_state['dest_coords'] = dest_coords
                
            except Exception as e:
                st.error(f"Error analyzing route: {str(e)}")
                safety_data = {}
    else:
        # Use cached data
        safety_data = st.session_state.get('last_analysis', {})
        origin = st.session_state.get('last_origin', origin)
        destination = st.session_state.get('last_destination', destination)
        route_coords = st.session_state.get('route_coords', route_coords)
        incident_coords = st.session_state.get('incident_coords', incident_coords)
        origin_coords = st.session_state.get('origin_coords', origin_coords)
        dest_coords = st.session_state.get('dest_coords', dest_coords)
        
    # Ensure safety_data is always a dictionary
    if not isinstance(safety_data, dict):
        st.warning("Safety data format is incorrect. Using default values.")
        safety_data = {}
    
    # Display basic information
    st.header(f"Route: {origin} to {destination}")
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display safety score with AI badge
        score = safety_data.get("safety_score", 7.5)  # Default to moderate score if not available
        color = safety_data.get("color", "yellow")
        
        # Map color to hex
        color_map = {
            "green": "#28a745",
            "yellow": "#ffc107", 
            "red": "#dc3545"
        }
        hex_color = color_map.get(color, "#ffc107")
        
        # Display score with AI label using custom classes
        st.markdown(f"""
        <div class="safety-score animate-fadeIn" style="background-color: {hex_color};">
            <div class="ai-badge">
                <span style="font-family: monospace;">AI-Generated</span>
            </div>
            <h2>Safety Score: {score}/10</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Display safety timeline with error handling and AI badge - using custom classes
        st.markdown("""
        <div class="feature-section animate-fadeIn">
            <h2>Safety Throughout the Day</h2>
        """, unsafe_allow_html=True)
        
        try:
            # Check if time predictions exist
            if "time_predictions" in safety_data and safety_data["time_predictions"]:
                display_enhanced_safety_timeline(safety_data)
            else:
                st.info("Time-based safety predictions are not available for this route.")
                # Show a placeholder timeline with default values
                default_times = {
                    "time_predictions": {
                        "5:00-7:00 AM": 8.5,
                        "7:00-9:00 AM": 6.2,
                        "9:00 AM-4:00 PM": 7.8,
                        "4:00-7:00 PM": 5.5,
                        "7:00-10:00 PM": 6.8, 
                        "10:00 PM-5:00 AM": 5.0
                    }
                }
                display_enhanced_safety_timeline(default_times)
        except Exception as e:
            st.error(f"Could not display safety timeline: {str(e)}")
    
    with col2:
        # Get safety score for determining route color
        safety_score = safety_data.get("safety_score", 7.5)
        route_color = "#28a745" if safety_score >= 8 else "#ffc107" if safety_score >= 6 else "#dc3545"
        
        # Convert color hex to named colors for folium
        color_map = {
            "#28a745": "green",  # Safe
            "#ffc107": "orange", # Moderate risk
            "#dc3545": "red"     # High risk
        }
        folium_color = color_map.get(route_color, "blue")
        
        # Calculate safety color for visual elements
        route_card_color = "#28a745" if safety_score >= 8 else "#ffc107" if safety_score >= 6 else "#dc3545"
        
        # Safety alerts based on the route and conditions
        # More realistic alert count based on conditions and time of day
        base_alert_count = 2  # minimum number of alerts
        
        # More alerts during risky conditions
        if time_of_day in ["morning_rush", "evening_rush"]:
            base_alert_count += 2
        if weather in ["rain", "fog", "storm"]:
            base_alert_count += 2
        if traffic_density == "high":
            base_alert_count += 1
        
        st.markdown(f"""
        <div style="margin-bottom: 15px; display: flex; align-items: center;">
            <span style="background-color: #dc3545; color: white; font-weight: bold; padding: 2px 8px; 
                      border-radius: 10px; margin-right: 10px;">{base_alert_count}</span>
            <span><b>Safety Alerts</b> potential hazards identified on this route</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Create realistic time-based safety predictions
        # These follow the pattern we've established where early morning and late night are safer than rush hours
        st.markdown("<b>Recommended Travel Times:</b>", unsafe_allow_html=True)
        
        # Define realistic safety scores for each time period
        # This reflects your requirement that early morning and late night are safer (less traffic)
        realistic_time_predictions = {
            "Early Morning (5-7 AM)": 8.5,  # Very safe - light traffic
            "Morning Rush (7-9 AM)": 5.8,  # Risky - heavy commute traffic
            "Mid-Day (9 AM-4 PM)": 7.2,  # Moderately safe - steady but manageable traffic
            "Evening Rush (4-7 PM)": 5.5,  # Most risky - heaviest traffic and fatigue
            "Evening (7-10 PM)": 7.0,    # Moderately safe - decreasing traffic
            "Late Night (10 PM-5 AM)": 8.7  # Safest - minimal traffic (though dark)
        }
        
        # Show time predictions from data, or use our realistic fallback
        time_predictions = safety_data.get("time_predictions", realistic_time_predictions)
        
        # Ensure the patterns are correct (early morning and late night MUST be safer)
        if not isinstance(time_predictions, dict) or len(time_predictions) < 6:
            time_predictions = realistic_time_predictions
        
        # Sort by safety score in descending order to show safest times first
        sorted_times = sorted(time_predictions.items(), key=lambda x: float(x[1]) if isinstance(x[1], (int, float, str)) else 0, reverse=True)
        
        # Display the safest times with color-coding
        for i, (period, score) in enumerate(sorted_times[:3]):
            try:
                score_float = float(score)
                color = "#28a745" if score_float >= 8 else "#ffc107" if score_float >= 6 else "#dc3545"
                emojis = {
                    "Early Morning": "🌅",
                    "Morning Rush": "🚶‍♂️",
                    "Mid-Day": "☀️",
                    "Evening Rush": "🚘",
                    "Evening": "🌆",
                    "Late Night": "🌙"
                }
                
                # Find matching emoji
                emoji = "⏰"
                for key, value in emojis.items():
                    if key in period:
                        emoji = value
                        break
                        
                st.markdown(f"""
                <div style="background-color: {color}; color: white; border-radius: 5px; padding: 8px; margin-bottom: 8px;">
                    {emoji} <b>{period}</b> - Safety Score: {score_float}/10
                </div>
                """, unsafe_allow_html=True)
            except (ValueError, TypeError):
                pass
                
        # Safety tip
        tip = ""
        if isinstance(safety_data.get("tip"), dict) and "text" in safety_data["tip"]:
            tip = safety_data["tip"]["text"]
        else:
            # Fallback safety tip
            tips = [
                "Maintain safe following distance in all weather conditions.",
                "Be extra cautious at intersections - most accidents happen there.",
                "Use turn signals early to communicate your intentions to other drivers.",
                "Avoid distracted driving, especially in high traffic areas.",
                "Check traffic reports before departing for your journey."
            ]
            import random
            tip = random.choice(tips)
            
        st.info(f"💡 **Safety Tip:** {tip}")
    
    # Add Personalized Departure Advisor section - using custom classes with complete HTML structure
    st.markdown("---")
    st.markdown("""
    <div class="feature-section animate-fadeIn">
        <h2>Departure Time Recommendations</h2>
        <p>Get a personalized recommendation for when to leave based on your schedule and priorities. 
        This helps you balance arriving on time with staying safe.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add explanation of the feature directly in the HTML
    # The previous div is already closed in the HTML
    
    # Create a card for departure advisor inputs
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("When do you need to arrive at your destination?")
    advisor_col1, advisor_col2, advisor_col3 = st.columns([1.5, 1, 1])
    
    with advisor_col1:
        # Schedule type with descriptions
        schedule_type = st.radio(
            "Schedule Flexibility",
            options=["strict", "moderate", "flexible"],
            format_func=lambda x: {
                "strict": "Must be exactly on time",
                "moderate": "Can be a few minutes late",
                "flexible": "Arrival time is flexible"
            }.get(x, x),
            index=["strict", "moderate", "flexible"].index(st.session_state.get('schedule_type', "moderate")),
            horizontal=True
        )
        st.session_state['schedule_type'] = schedule_type
    
    with advisor_col2:
        # Arrival time input
        arrival_time = st.text_input(
            "Desired Arrival Time",
            value=st.session_state.get('arrival_time', "9:00 AM"),
            help="Enter time in format: 9:00 AM or 17:30"
        )
        st.session_state['arrival_time'] = arrival_time
    
    with advisor_col3:
        # Generate recommendation button
        recommend_clicked = st.button("Find Best Departure Time", type="primary")
        
    # Close the card div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get and display recommendation when the button is clicked
    if recommend_clicked or ('show_recommendation' in st.session_state and st.session_state['show_recommendation']):
        st.session_state['show_recommendation'] = True
        
        with st.spinner("Generating AI departure recommendation..."):
            # Get recommendation using the Departure Advisor
            recommendation = get_departure_recommendation(
                origin=origin,
                destination=destination,
                arrival_time=arrival_time,
                schedule_type=schedule_type,
                time_of_day=time_of_day,
                mode=mode,
                weather=weather,
                traffic=traffic_density
            )
        
        # Display the recommendation
        rec_col1, rec_col2 = st.columns([2, 1])
        
        with rec_col1:
            # Display explanation using custom classes
            st.markdown(f"""<div class="explanation-card animate-fadeIn">
                <p>{recommendation['explanation']}</p>
            </div>""", unsafe_allow_html=True)
        
        with rec_col2:
            # Display the departure times using custom classes for better mobile/desktop experience
            st.markdown(f"""
            <div class="departure-optimal animate-fadeIn">
                <h3>Optimal Departure</h3>
                <h2>{recommendation['optimal_departure_time']}</h2>
            </div>
            
            <div class="departure-range animate-fadeIn">
                <div class="departure-time">
                    <p>Earliest</p>
                    <p>{recommendation['earliest_departure']}</p>
                </div>
                <div class="departure-time">
                    <p>Latest</p>
                    <p>{recommendation['latest_departure']}</p>
                </div>
            </div>
            
            <div class="departure-duration animate-fadeIn">
                <p>Estimated Trip Duration</p>
                <p>{recommendation['estimated_duration']} minutes</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Display recommendations with error handling
    try:
        if safety_data.get("top_reasons") or safety_data.get("alternatives") or safety_data.get("tip"):
            display_safety_recommendations(safety_data)
        else:
            st.subheader("🛡️ Safety Recommendations")
            st.info("Stay alert and follow normal traffic rules when traveling on this route.")
    except Exception as e:
        st.error(f"Could not display recommendations: {str(e)}")
    
    # Display raw data for debugging
    with st.expander("Raw Safety Data"):
        st.json(safety_data)

if __name__ == "__main__":
    main()
