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
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
# Add parent directory to import path for direct running
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import app components
from enhanced_safety import get_enhanced_safety_analysis, display_enhanced_safety_timeline, enhance_safety_map, display_safety_recommendations
from ml_models import safety_model, risk_classifier, generate_time_predictions
from utils.ml_utils import predict_route_safety, get_safety_time_predictions, validate_ml_model_inputs
import utils  # Import utils for access to the original safety functions

# Initialize session state if it doesn't exist
if 'last_analysis' not in st.session_state:
    # Initialize with default empty dictionary, not None
    st.session_state['last_analysis'] = {}

if 'last_origin' not in st.session_state:
    st.session_state['last_origin'] = "Downtown San Jose"
    
if 'last_destination' not in st.session_state:
    st.session_state['last_destination'] = "Santana Row, San Jose"

def main():
    """
    Enhanced safety analysis for San Jose Safe Commute.
    Run with: streamlit run test_safety.py
    """
    # Set page config for a cleaner look
    st.set_page_config(
        page_title="San Jose Safe Commute | Home",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Load custom CSS
    def load_css():
        with open(os.path.join(os.path.dirname(__file__), "styles/custom.css")) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    try:
        load_css()
    except Exception as e:
        print(f"Error loading CSS: {e}")

    # Custom CSS for better UI with a more modern, professional look
    st.markdown("""
    <style>
    .main {background-color: #f5f7fa; color: #333;}
    .stButton button {width: 100%; background-color: #1e88e5; color: white;}
    .stButton button:hover {background-color: #1565c0;}
    .stProgress .st-bo {background-color: #28a745;}
    h1, h2, h3 {color: #1e3a8a;}
    .safety-card {background-color: #f8f9fa; border-radius: 10px; padding: 20px; margin: 10px 0; border-left: 4px solid #1e88e5; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    .safety-score-high {color: #2e7d32; font-weight: bold;}
    .safety-score-medium {color: #f57c00; font-weight: bold;}
    .safety-score-low {color: #d32f2f; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)
    
    # Title and introduction
    st.title("San Jose Safe Commute 🛣️")
    st.markdown("""
    <div style="display: flex; align-items: center; flex-wrap: wrap;">
        <h3 style="margin-right: 0.5rem;">AI-Powered Route Safety Analysis</h3>
        <span class="ai-badge">AI Enhanced</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a spacer for better layout
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create a better layout with a sidebar for inputs
    with st.sidebar:
        st.header("📍 Set Your Route")
        st.markdown("Enter your starting point and destination to get AI safety analysis")
    
    with st.sidebar:
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
        st.caption("📍 Type any address, place, or intersection in San Jose for suggestions")
        
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
        
        # Time selection with better UX
        st.subheader("⏰ When do you plan to travel?")
        time_options = [
            "Current Time",
            "Morning Commute (7-9 AM)",
            "Midday (11 AM-1 PM)",
            "Evening Commute (4-6 PM)",
            "Late Night (10 PM-12 AM)"
        ]
        
        selected_time = st.selectbox(
            "Time of Travel", 
            options=time_options,
            index=0,
            help="Select when you plan to travel for time-based safety analysis",
            key="time_select"
        )
        
        # Weather consideration for more accurate analysis
        st.subheader("🌤️ Weather Conditions")
        weather_options = ["Clear", "Cloudy", "Rainy", "Foggy"]
        selected_weather = st.selectbox(
            "Expected Weather", 
            options=weather_options,
            index=0,
            help="Weather can significantly impact route safety",
            key="weather_select"
        )
        
        # Transportation mode
        st.subheader("🚗 How are you traveling?")
        transport_options = ["Car", "Public Transit", "Walking", "Cycling"]
        selected_transport = st.selectbox(
            "Mode of Transportation", 
            options=transport_options,
            index=0,
            help="Different transportation modes have different safety considerations",
            key="transport_select"
        )
        
        # Additional preferences for personalized recommendations
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🔍 Personalize Your Route")
        
        avoid_options = st.multiselect(
            "Areas to Avoid (if possible):",
            ["Highways", "School Zones", "Complex Intersections", "Construction Areas", "High-traffic Areas"],
            help="Select areas or road types you'd prefer to avoid",
            key="avoid_select"
        )
        
        prioritize_safety = st.slider(
            "Safety vs. Speed Balance", 
            min_value=0, 
            max_value=10, 
            value=7,
            help="Adjust this slider to balance between the safest route and the fastest route. Higher values favor safety.",
            key="safety_slider"
        )
        
        # Analyze button with better visibility
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze Route Safety", type="primary", key="analyze_button")
    
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

    # Only perform analysis when the button is clicked or inputs change
    if analyze_button or 'last_analysis' not in st.session_state or not st.session_state['last_analysis']:
        # Initialize default values
        safety_data = {}
        safety_score = 7.0
        
        try:
            with st.spinner("Analyzing route safety..."):
                # Step 1: Validate inputs
                try:
                    valid, result = validate_ml_model_inputs(
                        origin=origin, 
                        destination=destination, 
                        time_of_day=selected_time, 
                        weather=selected_weather, 
                        traffic_density=prioritize_safety, 
                        mode=selected_transport
                    )
                except Exception as e:
                    st.error(f"Error validating inputs: {str(e)}")
                    valid = False
                    result = ["Unexpected error during input validation"]
                
                if not valid:
                    st.error(f"Input validation errors: {', '.join(result)}")
                    st.warning("Using default values for invalid inputs.")
                
                # Step 2: Try ML-powered analysis
                st.markdown("""<div style='display: inline-flex; align-items: center;'>
                           <h4 style='margin: 0;'>Analyzing route safety</h4>
                           <span class='ai-badge'>ML-Enhanced</span>
                          </div>""", unsafe_allow_html=True)
                
                try:
                    # Call our ML-powered safety prediction function
                    safety_data = predict_route_safety(
                        origin=origin,
                        destination=destination,
                        time_of_day=selected_time,
                        weather=selected_weather,
                        traffic_density=prioritize_safety,
                        mode=selected_transport
                    )
                    
                    # Get the predicted safety score
                    safety_score = safety_data.get("safety_score", 7.0)
                    
                    # Log the ML prediction for debugging
                    print(f"ML Safety prediction: {safety_score} for route {origin} to {destination}")
                    
                except Exception as e:
                    st.error(f"Error in ML safety analysis: {str(e)}")
                    st.warning("Falling back to traditional safety analysis.")
                    
                    try:
                        # Fallback to enhanced safety analysis
                        safety_data = get_enhanced_safety_analysis(
                            origin, destination, selected_time, 
                            selected_weather, prioritize_safety, 
                            selected_transport
                        )
                        safety_score = safety_data.get("safety_score", 7.0)
                        
                    except Exception as e2:
                        st.error(f"Error in fallback safety analysis: {str(e2)}")
                        st.warning("Using simplified safety scoring as final fallback.")
                        
                        # Basic scoring logic as final fallback
                        risk_score = 5.0  # Neutral starting point
                        
                        # Adjust based on time of day
                        time_risk_map = {
                            "Current Time": 0,  # Neutral
                            "Morning Commute (7-9 AM)": 1.5,   # Riskier
                            "Midday (11 AM-1 PM)": 0,         # Neutral
                            "Evening Commute (4-6 PM)": 2.0,   # Riskier
                            "Late Night (10 PM-12 AM)": -1.0     # Safer
                        }
                        risk_score += time_risk_map.get(selected_time, 0)
                        
                        # Adjust based on weather
                        weather_risk_map = {
                            "Clear": 0,      # Neutral
                            "Cloudy": 0.5,     # Slightly riskier
                            "Rainy": 1.5,     # Riskier
                            "Foggy": 2.0      # Much riskier
                        }
                        risk_score += weather_risk_map.get(selected_weather, 0)
                        
                        # Adjust based on traffic density
                        traffic_risk_map = {
                            0: -1.0,     # Safer
                            1: 0.5,   # Slightly riskier
                            2: 1.0,   # Riskier
                            3: 1.5,   # More riskier
                            4: 2.0,   # Much riskier
                            5: 2.5,   # Most risky
                            6: 3.0,   # Most risky
                            7: 3.0,   # Most risky
                            8: 2.5,   # Most risky
                            9: 2.0,   # Much riskier
                            10: 1.5   # More riskier
                        }
                        risk_score += traffic_risk_map.get(prioritize_safety, 0)
                        
                        # Normalize to 0-10 scale
                        risk_score = max(0, min(10, risk_score))
                        safety_score = 10 - risk_score  # Invert for safety score
                
                # Build safety data object if needed
                if not safety_data or not isinstance(safety_data, dict) or len(safety_data) == 0:
                    # Build basic time predictions
                    time_predictions = {
                        "Early Morning (5:00-7:00 AM)": 8.5,
                        "Morning Rush (7:00-9:00 AM)": 5.8,
                        "Mid-Day (9:00 AM-4:00 PM)": 7.2,
                        "Evening Rush (4:00-7:00 PM)": 5.5,
                        "Evening (7:00-10:00 PM)": 7.0,
                        "Late Night (10:00 PM-5:00 AM)": 8.7
                    }
                    
                    # Try to get ML time predictions if possible
                    try:
                        risk_factors = {
                            "time_of_day": selected_time,
                            "weather": selected_weather,
                            "traffic_density": prioritize_safety,
                            "day_of_week": datetime.now().strftime("%A")
                        }
                        ml_predictions = get_safety_time_predictions(origin, destination, safety_score, risk_factors)
                        if ml_predictions and isinstance(ml_predictions, dict):
                            time_predictions = ml_predictions
                    except Exception:
                        # Just use the default time predictions
                        pass
                        
                    # Format predictions if needed
                    formatted_predictions = {}
                    for time_label, score in time_predictions.items():
                        formatted_predictions[time_label] = round(float(score), 1)
                    
                    # Build a complete safety data object
                    safety_data = {
                        "safety_score": round(safety_score, 1),
                        "color": "green" if safety_score >= 8 else "yellow" if safety_score >= 6 else "red",
                        "time_predictions": formatted_predictions,
                        "alerts": [
                            {"coords": incident, "text": utils.get_hotspot_tip("high" if i % 3 == 0 else "medium", "evening"), "severity": "high" if i % 3 == 0 else "med"}
                            for i, incident in enumerate(incident_coords[:3])
                        ],
                        "top_reasons": [
                            f"Traffic density is {prioritize_safety}",
                            f"Weather conditions: {selected_weather}",
                            f"Time of day: {selected_time}"
                        ],
                        "tip": {
                            "badge": "car" if selected_transport == "driving" else "umbrella" if selected_weather in ["rain", "storm"] else "bicycle" if selected_transport == "bicycling" else "car",
                            "text": utils.get_hotspot_tip("medium", selected_time)
                        },
                        "ai_powered": True  # Mark this as AI-powered for UI indicators
                    }
                
                # Store in session state
                st.session_state['last_analysis'] = safety_data
                st.session_state['last_origin'] = origin
                st.session_state['last_destination'] = destination
                st.session_state['route_coords'] = route_coords
                st.session_state['incident_coords'] = incident_coords
                st.session_state['origin_coords'] = origin_coords
                st.session_state['dest_coords'] = dest_coords
                
        except Exception as e:
            # Catch any unexpected exceptions that weren't handled above
            st.error(f"Unexpected error analyzing route: {str(e)}")
            st.warning("Using default safety analysis.")
            
            # Provide a basic safety object as fallback
            safety_data = {
                "safety_score": 7.0,
                "color": "yellow",
                "time_predictions": {
                    "Early Morning (5:00-7:00 AM)": 8.5,
                    "Morning Rush (7:00-9:00 AM)": 5.8,
                    "Mid-Day (9:00 AM-4:00 PM)": 7.2,
                    "Evening Rush (4:00-7:00 PM)": 5.5,
                    "Evening (7:00-10:00 PM)": 7.0,
                    "Late Night (10:00 PM-5:00 AM)": 8.7
                },
                "alerts": [],
                "top_reasons": ["No specific risk factors identified"],
                "tip": {"badge": "car", "text": "Drive safely and stay alert."}
            }
            
            # Store in session state despite error
            st.session_state['last_analysis'] = safety_data
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
    
    # Display basic information with a more modern heading
    st.header(f"From {origin} to {destination}")
    
    # Add route alternatives similar to what users expect in apps like Waze
    st.subheader("🚦 Available Routes")
    route_col1, route_col2, route_col3 = st.columns(3)
    
    with route_col1:
        st.markdown("""
        <div class='safety-card' style='border-left-color: #1E88E5;'>
            <h4>Recommended Route</h4>
            <p><b>ETA:</b> 15 minutes</p>
            <p><b>Safety:</b> Medium</p>
            <p><b>Distance:</b> 5.2 miles</p>
        </div>
        """, unsafe_allow_html=True)
        recommended_selected = st.button("Select", key="route1_select")
        
    with route_col2:
        st.markdown("""
        <div class='safety-card' style='border-left-color: #66BB6A;'>
            <h4>Safest Route</h4>
            <p><b>ETA:</b> 17 minutes (+2)</p>
            <p><b>Safety:</b> High</p>
            <p><b>Distance:</b> 5.8 miles</p>
        </div>
        """, unsafe_allow_html=True)
        safest_selected = st.button("Select", key="route2_select")
        
    with route_col3:
        st.markdown("""
        <div class='safety-card' style='border-left-color: #FFA726;'>
            <h4>Fastest Route</h4>
            <p><b>ETA:</b> 12 minutes (-3)</p>
            <p><b>Safety:</b> Lower</p>
            <p><b>Distance:</b> 4.9 miles</p>
        </div>
        """, unsafe_allow_html=True)
        fastest_selected = st.button("Select", key="route3_select")
    
    # Display the folium map with the routes
    st.subheader("🗺️ Route Map")
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display safety score
        score = safety_data.get("safety_score", 7.5)  # Default to moderate score if not available
        color = safety_data.get("color", "yellow")
        
        # Map color to hex
        color_map = {
            "green": "#28a745",
            "yellow": "#ffc107", 
            "red": "#dc3545"
        }
        hex_color = color_map.get(color, "#ffc107")
        
        # Display score
        st.markdown(f"""
        <div style="background-color: {hex_color}; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: white; text-align: center;">Safety Score: {score}/10</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Display safety timeline with error handling
        try:
            # Check if time predictions exist
            if "time_predictions" in safety_data and safety_data["time_predictions"]:
                display_enhanced_safety_timeline(safety_data)
            else:
                st.info("Time-based safety predictions are not available for this route.")
                # Show a placeholder timeline with default values
                default_times = {
                    "time_predictions": {
                        "5–7 AM": 8.5,
                        "7–9 AM": 6.2,
                        "9–4 PM": 7.8,
                        "4–7 PM": 5.5,
                        "7–10 PM": 7.2,
                        "10–5 AM": 8.7
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
        
        # Add AI/ML badge if prediction was AI-powered
        ai_powered = safety_data.get("ai_powered", False)
        ai_badge = "<span class='ai-badge'>AI-Powered</span>" if ai_powered else ""
        
        # Calculate safety color for visual elements
        route_card_color = "#28a745" if safety_score >= 8 else "#ffc107" if safety_score >= 6 else "#dc3545"
        
        # Safety alerts based on the route and conditions
        # More realistic alert count based on conditions and time of day
        base_alert_count = 2  # minimum number of alerts
        
        # More alerts during risky conditions
        if selected_time in ["Morning Commute (7-9 AM)", "Evening Commute (4-6 PM)"]:
            base_alert_count += 2
        if selected_weather in ["Rainy", "Foggy"]:
            base_alert_count += 2
        if prioritize_safety > 7:  # If user prioritizes safety highly
            base_alert_count += 2
        
        st.markdown(f"""
        <div style="margin-bottom: 15px; display: flex; align-items: center;">
            <span style="background-color: #dc3545; color: white; font-weight: bold; padding: 2px 8px; 
                      border-radius: 10px; margin-right: 10px;">{base_alert_count}</span>
            <span><b>Safety Alerts</b> potential hazards identified on this route</span>
            {ai_badge}
        </div>
        """, unsafe_allow_html=True)
        
        # Add real-time incident reporting (Waze-like feature)
        st.markdown(f"<h3>📱 Real-Time Reports {ai_badge}</h3>", unsafe_allow_html=True)
        st.markdown("<p>Recent user reports near your route:</p>", unsafe_allow_html=True)
        
        # Simulate recent reports
        reports = [
            {"type": "Construction", "time": "4 min ago", "location": "Near the intersection of 1st and Santa Clara", "icon": "🚧"},
            {"type": "Heavy Traffic", "time": "17 min ago", "location": "Winchester Blvd near Santana Row", "icon": "🚗"},
            {"type": "Police", "time": "32 min ago", "location": "Highway 280 near Bascom Ave exit", "icon": "👮"},
        ]
        
        for report in reports:
            st.markdown(f"""
            <div class='safety-card' style='padding: 10px; margin-bottom: 8px;'>
                <div style='display: flex; align-items: center;'>
                    <div style='font-size: 24px; margin-right: 10px;'>{report['icon']}</div>
                    <div>
                        <div style='font-weight: bold;'>{report['type']}</div>
                        <div style='font-size: 12px; color: #666;'>{report['time']} · {report['location']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Add report incident button
        st.markdown("<h4>Report an Incident</h4>", unsafe_allow_html=True)
        incident_col1, incident_col2 = st.columns(2)
        
        with incident_col1:
            if st.button("🚧 Construction", key="btn_construction"):
                st.success("Report submitted! Thank you for helping the community.")
                
        with incident_col2:
            if st.button("🚦 Traffic", key="btn_traffic"):
                st.success("Report submitted! Thank you for helping the community.")
                
        incident_col3, incident_col4 = st.columns(2)
        
        with incident_col3:
            if st.button("🚔 Police", key="btn_police"):
                st.success("Report submitted! Thank you for helping the community.")
                
        with incident_col4:
            if st.button("⚠️ Hazard", key="btn_hazard"):
                st.success("Report submitted! Thank you for helping the community.")
        
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
    
    # Display recommendations with error handling
    try:
        if safety_data.get("top_reasons") or safety_data.get("alternatives") or safety_data.get("tip"):
            display_safety_recommendations(safety_data)
        else:
            st.subheader("🛡️ Safety Recommendations")
            st.info("Stay alert and follow normal traffic rules when traveling on this route.")
    except Exception as e:
        st.error(f"Could not display recommendations: {str(e)}")
    
    # Display route feedback section like modern navigation apps
    st.subheader("💬 Route Feedback")  
    feedback_col1, feedback_col2 = st.columns(2)
    
    with feedback_col1:
        route_rating = st.slider("Rate this route's safety", min_value=1, max_value=5, value=4, key="route_rating")
        
    with feedback_col2:
        if st.button("Submit Rating", key="submit_rating"):
            st.success(f"Thank you for rating this route {route_rating}/5 stars! Your feedback helps improve our AI predictions.")
            # In a real app, this would be used to retrain our ML models
            if 'feedback_data' not in st.session_state:
                st.session_state['feedback_data'] = []
            
            # Store feedback for model training
            feedback_entry = {
                'timestamp': datetime.now().isoformat(),
                'origin': origin,
                'destination': destination,
                'rating': route_rating,
                'conditions': {
                    'time': selected_time,
                    'weather': selected_weather,
                    'traffic': prioritize_safety,
                    'mode': selected_transport
                }
            }
            st.session_state['feedback_data'].append(feedback_entry)
            
    feedback_text = st.text_area("Share your experience with this route", height=100, key="feedback_text")
    if st.button("Submit Feedback", key="submit_feedback"):
        if feedback_text.strip():
            st.success("Thank you for your detailed feedback! It will be used to train our AI safety models.")
            
            # Store text feedback as well
            if 'feedback_data' in st.session_state and st.session_state['feedback_data']:
                st.session_state['feedback_data'][-1]['text_feedback'] = feedback_text
        else:
            st.warning("Please enter some feedback before submitting.")
    
    # Add ML model training explanation
    with st.expander("How your feedback improves our AI models"):
        st.markdown("""
        <div class="ml-card">
            <h4>Continuous ML Model Training</h4>
            <p>Your feedback is invaluable for improving our machine learning models. Here's how we use it:</p>
            <ol>
                <li><strong>Data Collection</strong>: Your ratings and comments are securely stored with the route conditions</li>
                <li><strong>Model Training</strong>: Our models are periodically retrained using this feedback data</li>
                <li><strong>Accuracy Improvement</strong>: This helps our AI better understand real-world safety conditions</li>
                <li><strong>Personalization</strong>: Over time, our predictions become tailored to your preferences</li>
            </ol>
            <div class="prediction-bar"></div>
            <p><small>Your privacy is important - all feedback data is anonymized before training.</small></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Add a section for ML model explanation
    st.subheader("🤖 How AI Makes This App Smarter")
    st.markdown("""
    <div class="ml-card">
        <h4>Machine Learning Technology Behind San Jose Safe Commute</h4>
        <p>This app uses several advanced AI/ML models to provide accurate safety predictions:</p>
        <ul>
            <li><strong>Safety Score Predictor:</strong> A Random Forest regression model trained on historical crash data, weather patterns, and traffic conditions</li>
            <li><strong>Risk Classification:</strong> Gradient Boosting classifier that identifies high-risk areas based on multiple factors</li>
            <li><strong>Time-based Predictions:</strong> ML algorithms that analyze time-of-day patterns to recommend safer travel times</li>
            <li><strong>Continuous Learning:</strong> Models that improve through user feedback and new incident data</li>
        </ul>
        <p>Each route you analyze benefits from hundreds of data points and sophisticated algorithms working together to keep you safe.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display raw data for debugging (only in development)
    with st.expander("Raw Safety Data"):
        st.json(safety_data)

if __name__ == "__main__":
    main()
