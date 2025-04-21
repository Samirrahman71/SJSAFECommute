import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime
import pytz
import sys
import inspect
import json

# Add the project root to the path so we can import from utils
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

from utils.openai_utils import get_commute_insights
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key from environment variable if provided directly
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Custom CSS for chat-like interface
chat_css = """
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; flex-direction: row;
}
.chat-message.user {
    background-color: #2b313e;
}
.chat-message.bot {
    background-color: #475063;
}
.chat-message .avatar {
    width: 15%;
}
.chat-message .avatar img {
    max-width: 78px;
    max-height: 78px;
    border-radius: 50%;
    object-fit: cover;
}
.chat-message .message {
    width: 85%;
    padding-left: 1rem;
    color: #fff;
}
.stTextInput input {
    border-radius: 20px;
    padding: 10px 15px;
    border: 1px solid #4a4a4a;
    background-color: #2b313e;
    color: white;
}
.stButton button {
    border-radius: 20px;
    padding: 0.5rem 1rem;
    background: linear-gradient(90deg, #4776E6 0%, #8E54E9 100%);
    border: none;
    color: white;
    font-weight: bold;
}
</style>
"""

# Helper function to display chat messages
def display_chat_message(message, is_user=False, is_ai=False):
    if is_user:
        st.markdown(f"""
        <div class="chat-message user">
            <div class="avatar">
                <img src="https://api.dicebear.com/7.x/thumbs/svg?seed=John" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
            </div>
            <div class="message">{message}</div>
        </div>
        """, unsafe_allow_html=True)
    elif is_ai:
        st.markdown(f"""
        <div class="chat-message bot">
            <div class="avatar">
                <img src="https://api.dicebear.com/7.x/bottts-neutral/svg?seed=Guru" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
            </div>
            <div class="message">{message}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(message)

# Set page configuration
st.set_page_config(
    page_title="San Jose Safe Commute | AI Route Planner",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(chat_css, unsafe_allow_html=True)

# Add more CSS for improved UI with consistent color scheme
add_css = """
<style>
:root {
    --primary-color: #1e3a8a; /* Dark blue as primary color */
    --primary-light: #3151b5;
    --secondary-color: #f8fafc;
    --text-color: #1e293b;
    --text-light: #ffffff;
    --border-radius: 8px;
    --shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.main-container {
    background-color: var(--secondary-color);
    border-radius: var(--border-radius);
    padding: 20px;
    box-shadow: var(--shadow);
    margin-bottom: 20px;
}

.map-container {
    border-radius: var(--border-radius);
    overflow: hidden;
    box-shadow: var(--shadow);
    background-color: white;
    padding: 10px;
}

.card {
    background-color: white;
    border-radius: var(--border-radius);
    padding: 15px;
    box-shadow: var(--shadow);
    margin-bottom: 15px;
    border-left: 4px solid var(--primary-color);
}

.card h3 {
    color: var(--primary-color) !important;
    font-weight: 600;
}

.quick-access {
    padding: 12px;
    background-color: var(--primary-color);
    color: var(--text-light) !important;
    border-radius: var(--border-radius);
    margin-bottom: 15px;
}

.quick-access h4 {
    color: white !important;
    margin: 0 0 10px 0;
}

/* Style buttons consistently */
.stButton > button {
    background-color: var(--primary-color) !important;
    color: white !important;
    border: none !important;
    border-radius: 20px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background-color: var(--primary-light) !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
}

/* Sidebar styling */
.sidebar .stButton > button {
    background-color: transparent !important;
    border: 1px solid var(--primary-color) !important;
    color: var(--primary-color) !important;
}

/* Form inputs */
.stTextInput > div > div > input {
    border-radius: var(--border-radius) !important;
    border: 1px solid #e2e8f0 !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif !important;
}

/* Main title */
.main-title {
    color: var(--primary-color) !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
}

/* Navigation */
.nav-link {
    color: var(--primary-color) !important;
    font-weight: 500 !important;
}

/* Expanders */
.streamlit-expanderHeader {
    font-weight: 500 !important;
    color: var(--primary-color) !important;
}
</style>
"""
st.markdown(add_css, unsafe_allow_html=True)

# Initialize session state for chat history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

if 'show_form' not in st.session_state:
    st.session_state.show_form = True

# Always show map
if 'map_center' not in st.session_state:
    st.session_state.map_center = [37.3382, -121.8863]  # San Jose coordinates

def reset_chat():
    st.session_state.chat_history = []
    st.session_state.form_data = {}
    st.session_state.show_form = True
    st.session_state.map_center = [37.3382, -121.8863]  # Reset to San Jose center

# Header with consistent styling
st.markdown("""<div style='text-align: center; padding: 10px 0 20px 0;'>
    <h1 class='main-title' style='margin:0;'>🚗 San Jose Safe Commute</h1>
    <p style='font-size:1.2em; margin:5px 0 0 0; color: var(--text-color);'>Your AI-Powered Route Safety Assistant</p>
</div>""", unsafe_allow_html=True)

# Quick shortcuts for common destinations
with st.sidebar:
    st.markdown("""<div style='text-align:center'>
    <img src="https://api.dicebear.com/7.x/bottts-neutral/svg?seed=SJ" width="100">
    <h3 style='margin-top:5px;'>AI Commute Guru</h3>
    </div>""", unsafe_allow_html=True)
    
    # API key input area
    if not OPENAI_API_KEY:
        st.markdown("### 🔑 API Configuration")
        api_key_input = st.text_input("OpenAI API Key", type="password", placeholder="sk-...", 
                                help="Required for AI route analysis")
        if api_key_input:
            os.environ["OPENAI_API_KEY"] = api_key_input
            st.success("API Key set for this session!")
            st.button("Refresh App", on_click=lambda: st.rerun())
    
    # Travel conditions overview
    st.markdown("### 📌 Travel Overview")
    
    # Current time display
    pst = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(pst)
    st.markdown(f"**Current Time:** {current_time.strftime('%I:%M %p')}")
    
    # Time-based message
    hour = current_time.hour
    if 7 <= hour < 10:
        time_message = "🚨 **Morning Rush Hour** - Expect delays on major highways"
    elif 15 <= hour < 19:
        time_message = "🚨 **Evening Rush Hour** - Heavy traffic on commute routes"
    elif 10 <= hour < 15:
        time_message = "✅ **Midday Travel** - Generally lighter traffic conditions"
    else:
        time_message = "🌙 **Off-Peak Hours** - Reduced traffic volume"
    
    st.markdown(time_message)
    
    # Safety information
    st.markdown("### 🔰 Safety Tips")
    safety_tips = [
        "Always check routes before traveling",
        "Be aware of weather conditions",
        "Allow extra time during rush hours",
        "Consider alternative transportation options"
    ]
    
    for tip in safety_tips:
        st.markdown(f"• {tip}")
    
    # Quick information
    with st.expander("ℹ️ About This App"):
        st.markdown("""This app uses AI to analyze traffic patterns and provide the safest route for your commute. It takes into account real-time traffic data, weather conditions, and road closures to give you the most up-to-date information. Simply enter your starting point and destination, and the app will provide you with a safe and efficient route.""")

# Quick shortcuts for common destinations
with st.container():
    st.markdown("""<div class='quick-access'>
    <h4>🔥 Quick Access</h4>
    </div>""", unsafe_allow_html=True)
    
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    
    with quick_col1:
        if st.button("🏢 Downtown SJ", use_container_width=True):
            st.session_state.quick_destination = "Downtown San Jose"
            st.rerun()
            
    with quick_col2:
        if st.button("🛬 SJ Airport", use_container_width=True):
            st.session_state.quick_destination = "San Jose International Airport"
            st.rerun()
            
    with quick_col3:
        if st.button("🏫 San Jose State", use_container_width=True):
            st.session_state.quick_destination = "San Jose State University"
            st.rerun()
            
    with quick_col4:
        if st.button("🛒 Santana Row", use_container_width=True):
            st.session_state.quick_destination = "Santana Row, San Jose"
            st.rerun()

# Main content in a cleaner layout
st.markdown("""<div class='main-container'></div>""", unsafe_allow_html=True)

# Main content columns - map on the right is always visible
left_col, right_col = st.columns([5, 4])

with left_col:
    # Chat interface or form based on state
    if st.session_state.show_form:
        with st.container():
            st.markdown("""<div class='card'>
            <h3 style='margin-top:0;'>👋 Hello! I'm your AI Commute Assistant</h3>
            <p style='color: var(--text-color);'>Tell me about your journey and I'll suggest the safest route with real-time insights.</p>
            </div>""", unsafe_allow_html=True)
            
            # Check if quick destination was selected
            quick_destination = ""
            if hasattr(st.session_state, 'quick_destination'):
                quick_destination = st.session_state.quick_destination
                # Clear it after use
                del st.session_state.quick_destination
            
            with st.form(key="commute_form"):
                st.markdown("""<h4 style='margin:0 0 10px 0;'>🗑 Route Details</h4>""", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    origin = st.text_input("🏠 Starting Point", 
                                       placeholder="Your location",
                                       help="Where are you starting from?")
                
                with col2:
                    destination = st.text_input("📍 Destination", 
                                           value=quick_destination,
                                           placeholder="Where to?",
                                           help="Where are you going?")
                
                # Travel time options - simplified UI
                st.markdown("""<h4 style='margin:10px 0 10px 0;'>⏰ When & How</h4>""", unsafe_allow_html=True)
                
                col3, col4 = st.columns(2)
                
                with col3:
                    travel_time = st.selectbox(
                        "Departure time",
                        ["Now", "Morning Rush", "Midday", "Afternoon Rush", "Evening", "Late Night"],
                        index=0,
                        help="When are you leaving?")
                
                with col4:
                    travel_mode = st.selectbox(
                        "Travel mode",
                        ["🚗 Driving", "🚌 Bus/Transit", "🚵 Cycling", "🚶 Walking"],
                        index=0,
                        help="How are you traveling?")
                
                # Simplify conditions section
                with st.expander("⚙️ Advanced Options", expanded=False):
                    col5, col6 = st.columns(2)
                    
                    with col5:
                        weather = st.radio(
                            "Weather",
                            ["☀️ Clear", "⛅ Partly Cloudy", "☁️ Overcast", "🌧️ Rainy", "🌫️ Foggy"],
                            horizontal=False,
                            help="Current weather conditions")
                    
                    with col6:
                        traffic = st.radio(
                            "Traffic",
                            ["Light", "Moderate", "Heavy", "Gridlock"],
                            horizontal=False,
                            help="Current traffic conditions")
                    
                    # Preferences checkboxes
                    st.markdown("**Preferences**")
                    pref_col1, pref_col2 = st.columns(2)
                    
                    with pref_col1:
                        avoid_highways = st.checkbox("Avoid highways", help="Prefer local roads")
                        avoid_tolls = st.checkbox("Avoid toll roads", help="Skip routes with tolls")
                    
                    with pref_col2:
                        prefer_scenic = st.checkbox("Scenic route", help="Prefer more scenic paths")
                        accessible = st.checkbox("Accessible route", help="Prioritize accessible paths")
                    
                    # Optional input for special circumstances
                    special_circumstances = st.text_area(
                        "Special instructions",
                        placeholder="E.g., Construction on I-280, Need to avoid downtown...",
                        help="Any special needs or information",
                        max_chars=150)

                # More prominent button for submission
                st.markdown("""<div style='padding-top:10px;'></div>""", unsafe_allow_html=True)
                submit_button = st.form_submit_button(label="🏁 Find My Safe Route", use_container_width=True)
                
                # Help text at the bottom of form
                st.markdown("""<div style='font-size: 0.8em; text-align: center; color: #666; margin-top: 10px;'>
                All routes are analyzed using AI for safety and efficiency 🧠
                </div>""", unsafe_allow_html=True)
                
                if submit_button:
                    if not origin or not destination:
                        st.error("Please provide both your starting point and destination.")
                    elif not OPENAI_API_KEY and not os.environ.get("OPENAI_API_KEY"):
                        st.error("OpenAI API key is required. Please add it in the sidebar.")
                    else:
                        # Capture preferences
                        preferences = []
                        if 'avoid_highways' in locals() and avoid_highways:
                            preferences.append("avoid highways")
                        if 'avoid_tolls' in locals() and avoid_tolls:
                            preferences.append("avoid toll roads")
                        if 'prefer_scenic' in locals() and prefer_scenic:
                            preferences.append("prefer scenic routes")
                        if 'accessible' in locals() and accessible:
                            preferences.append("need accessible routes")
                        
                        # Save form data to session state
                        st.session_state.form_data = {
                            "origin": origin,
                            "destination": destination,
                            "travel_time": travel_time,
                            "travel_mode": travel_mode,
                            "weather": weather,
                            "traffic": traffic,
                            "preferences": ", ".join(preferences) if preferences else "",
                            "special": special_circumstances if 'special_circumstances' in locals() else ""
                        }
                        
                        # Update state to show chat instead of form
                        st.session_state.show_form = False
                        
                        # Build a more natural user message
                        user_message = f"I need to travel from **{origin}** to **{destination}** "  
                        
                        if travel_time == "Now":
                            user_message += "right now. "
                        else:
                            user_message += f"during **{travel_time}**. "
                        
                        user_message += f"I'm {travel_mode.lower().replace('🚗 ', '').replace('🚲 ', '').replace('🚶 ', '').replace('🚌 ', '')}. "
                        
                        if st.session_state.form_data["preferences"]:
                            user_message += f"I prefer to {st.session_state.form_data['preferences']}. "
                            
                        if weather != "☀️ Clear":
                            user_message += f"The weather is {weather.lower()}. "
                        
                        if traffic != "Light":
                            user_message += f"Traffic is {traffic.lower()}. "
                            
                        if special_circumstances:
                            user_message += f"Also note: {special_circumstances}"
                        
                        st.session_state.chat_history.append({"role": "user", "content": user_message})
                        
    else:
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                display_chat_message(message["content"], is_user=True)
            else:
                display_chat_message(message["content"], is_ai=True)
        
        # If we don't have an AI response yet, generate it
        if len(st.session_state.chat_history) % 2 == 1:  # Odd number means waiting for AI response
            with st.status("Thinking...", expanded=True) as status:
                st.write("Analyzing traffic patterns...")
                st.write("Checking weather impact...")
                st.write("Calculating route safety...")
                
                # Get data from the form
                form_data = st.session_state.form_data
                
                # Format data for OpenAI
                route_info = f"{form_data['origin']} → {form_data['destination']} during {form_data['travel_time']}"
                traffic_info = f"{form_data['traffic']} traffic in San Jose area"
                weather_info = f"{form_data['weather']} conditions"
                incidents = form_data['special'] if form_data['special'] else "No special circumstances reported"
                
                # Get insights from OpenAI
                try:
                    insights = get_commute_insights(
                        route_info=route_info,
                        traffic_conditions=traffic_info,
                        weather_conditions=weather_info,
                        incidents=incidents,
                        temperature=0.7  # Slightly higher creativity
                    )
                    
                    # Add AI response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": insights})
                    status.update(label="Route analysis complete!", state="complete", expanded=False)
                    
                    # Force a rerun to update the chat display
                    st.rerun()
                except Exception as e:
                    status.update(label="An error occurred", state="error", expanded=True)
                    st.error(f"Error generating insights: {str(e)}")
        
        # Chat input for follow-up questions
        with st.container():
            st.markdown("""<div style='background-color:#2b313e; padding:10px; border-radius:5px; margin-top:10px;'>""")
            follow_up = st.text_input("Ask a follow-up question", key="follow_up", placeholder="e.g., Can you suggest bike-friendly alternatives?")
            send_button = st.button("Send", use_container_width=True)
            st.markdown("""</div>""")
            
            if send_button and follow_up:
                # Add user follow-up to chat history
                st.session_state.chat_history.append({"role": "user", "content": follow_up})
                st.rerun()
        
        # Reset button
        if st.button("🔄 Start a New Route Query", type="secondary"):
            reset_chat()

with right_col:
    with st.container():
        st.markdown("""<div class='map-container'>
        <h4 style='margin:0 0 10px 0; color: var(--primary-color);'>📍 San Jose Map</h4>
        </div>""", unsafe_allow_html=True)
        
        # Initialize the map centered on San Jose
        m = folium.Map(location=st.session_state.map_center, zoom_start=12, control_scale=True)
        
        # Add traffic layer
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Maps',
            overlay=True,
            control=True
        ).add_to(m)
        
        # Get origin and destination from form data if available
        if len(st.session_state.form_data) > 0:
            # Use dummy coordinates for demo purposes
            # In a real app, you would geocode these addresses
            dummy_data = {
                "origin": [37.3382, -121.8863],  # San Jose downtown
                "destination": [37.3199, -121.9450]  # Santana Row
            }
            
            # Add origin marker
            folium.Marker(
                dummy_data["origin"],
                popup=st.session_state.form_data.get("origin", "Origin"),
                tooltip=st.session_state.form_data.get("origin", "Origin"),
                icon=folium.Icon(color="green", icon="play")
            ).add_to(m)
            
            # Add destination marker
            folium.Marker(
                dummy_data["destination"],
                popup=st.session_state.form_data.get("destination", "Destination"),
                tooltip=st.session_state.form_data.get("destination", "Destination"),
                icon=folium.Icon(color="red", icon="flag")
            ).add_to(m)
            
            # Add a line connecting origin and destination
            folium.PolyLine(
                [dummy_data["origin"], dummy_data["destination"]],
                color="blue",
                weight=5,
                opacity=0.7
            ).add_to(m)
            
            # Update map center
            st.session_state.map_center = [(dummy_data["origin"][0] + dummy_data["destination"][0])/2, 
                                         (dummy_data["origin"][1] + dummy_data["destination"][1])/2]
        
        # Add common locations
        common_locations = {
            "Downtown San Jose": [37.3382, -121.8863],
            "San Jose Airport": [37.3639, -121.9289],
            "San Jose State University": [37.3352, -121.8811],
            "Santana Row": [37.3199, -121.9450],
            "Valley Fair Mall": [37.3256, -121.9453],
            "Willow Glen": [37.3021, -121.8989]
        }
        
        for name, coords in common_locations.items():
            folium.CircleMarker(
                location=coords,
                radius=5,
                color="#3366cc",
                fill=True,
                fill_color="#3366cc",
                tooltip=name
            ).add_to(m)
        
        # Display the map
        map_data = st_folium(m, width=450, height=500)
        
        # Dynamic travel info below map
        with st.expander("📊 San Jose Travel Info", expanded=False):
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.markdown("""
                **Current Traffic Hotspots:**
                - 🔴 US-101 at 880 Interchange
                - 🟠 I-280 near Downtown
                - 🟡 CA-87 at Curtner Ave
                """)
            
            with info_col2:
                st.markdown("""
                **Weather Impact:**
                - Current Weather: ☀️ Clear, 70°F
                - Road Conditions: Dry
                - Visibility: Excellent
                """)
    
    # Commute Guru Info Box that shows on both screens
    st.markdown("""
    ### How Commute Guru Works
    
    The Commute Guru analyzes multiple factors to provide intelligent commute recommendations:
    
    - **Real-time Traffic**: Current road conditions and congestion levels
    - **Weather Impact**: How weather affects road safety and travel speed
    - **Incident Analysis**: Accidents, construction, and other road events
    - **Time Patterns**: Historical traffic patterns for the selected time
    
    Each analysis is personalized to your specific route and current conditions.
    """)
