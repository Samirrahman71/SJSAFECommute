import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import requests

st.set_page_config(page_title="San Jose Safe Commute App", layout="centered", initial_sidebar_state="collapsed")
st.title("San Jose Safe Commute App")

st.markdown("""
A minimalist, AI-powered app to help San Jose commuters assess traffic risks and plan safer commutes.
""")

# --- User Inputs ---
origin = st.text_input("Enter your starting location")
destination = st.text_input("Enter your destination")

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
