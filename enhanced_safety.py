"""
Enhanced safety analysis functions for San Jose Safe Commute.
Provides advanced safety metrics and visualizations for commute routes.
"""

import streamlit as st
import folium
import pandas as pd
import numpy as np
from datetime import datetime
import random

def get_enhanced_safety_analysis(origin, destination, time_of_day, weather, traffic_density, mode):
    """
    Generate enhanced safety analysis for a route.
    
    Args:
        origin: Starting location
        destination: Ending location
        time_of_day: Time of travel (morning, evening, etc.)
        weather: Weather conditions
        traffic_density: Traffic density level
        
    Returns:
        Dictionary with safety metrics and analysis
    """
    # Generate a safety score between 1-10 based on inputs
    base_score = 7.0  # Start with a reasonable score
    
    # Time factor
    time_factors = {
        'morning_rush': -0.8,
        'evening_rush': -1.0,
        'midday': 0.5,
        'night': -1.2,
        'early_morning': -0.3,
        'late_night': -1.5,
        'current': 0  # Neutral for current time
    }
    time_factor = time_factors.get(time_of_day, 0)
    
    # Weather factor
    weather_factors = {
        'clear': 0.5,
        'cloudy': 0.2,
        'rain': -0.7,
        'fog': -1.0,
        'snow': -1.5,
        'storm': -2.0
    }
    weather_factor = weather_factors.get(weather, 0)
    
    # Traffic factor
    traffic_factors = {
        'low': 0.8,
        'medium': -0.2,
        'high': -1.0
    }
    traffic_factor = traffic_factors.get(traffic_density, 0)
    
    # Mode factor
    mode_factors = {
        'driving': 0,       # Neutral for driving
        'walking': 0.5,     # Walking generally safer from accidents but more vulnerable
        'bicycling': -0.8,  # Cycling has higher risk in traffic
        'transit': 0.3      # Public transit generally safer
    }
    mode_factor = mode_factors.get(mode, 0)
    
    # Calculate final score with a slight random factor for variation
    random_factor = random.uniform(-0.3, 0.3)
    safety_score = base_score + time_factor + weather_factor + traffic_factor + mode_factor + random_factor
    
    # Ensure score stays within 1-10 range
    safety_score = max(1.0, min(10.0, safety_score))
    
    # Determine safety level
    if safety_score >= 8.0:
        safety_level = "High"
        color = "green"
    elif safety_score >= 6.0:
        safety_level = "Moderate"
        color = "yellow"
    elif safety_score >= 4.0:
        safety_level = "Caution"
        color = "orange"
    else:
        safety_level = "Low"
        color = "red"
    
    # Generate risk factors
    risk_factors = []
    if time_factor < 0:
        risk_factors.append(f"Travel during {time_of_day.replace('_', ' ')} increases risks")
    if weather_factor < 0:
        risk_factors.append(f"{weather.capitalize()} weather conditions impact visibility and road safety")
    if traffic_factor < 0:
        risk_factors.append(f"{traffic_density.capitalize()} traffic density increases accident probability")
    if mode_factor < 0:
        if mode == 'bicycling':
            risk_factors.append("Cycling in urban areas requires extra caution due to traffic interaction")
        elif mode == 'walking':
            risk_factors.append("Pedestrians should use designated crossings and remain visible to traffic")
    
    # If no risk factors identified, add a positive note
    if not risk_factors:
        risk_factors.append("Current conditions are favorable for travel")
    
    # Return analysis results
    analysis = {
        "safety_score": round(safety_score, 1),
        "safety_level": safety_level,
        "color": color,
        "risk_factors": risk_factors,
        "recommendations": get_safety_recommendations(safety_score, time_of_day, weather, traffic_density, mode),
        "hotspots": generate_sample_hotspots(),
        "historical_data": generate_historical_data()
    }
    
    return analysis

def display_enhanced_safety_timeline(analysis):
    """
    Display a safety timeline visualization based on analysis results.
    
    Args:
        analysis: Dictionary with safety analysis results
    """
    st.subheader("📊 Safety Timeline")
    
    # Sample data for timeline
    hours = ["6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", "12 PM", 
             "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM"]
    
    # Generate safety scores throughout the day
    if analysis:
        base_score = analysis.get("safety_score", 7.0)
        
        # Time-based pattern with morning and evening rush hours being less safe
        scores = []
        for hour in hours:
            if "AM" in hour and int(hour.split()[0]) in [7, 8, 9]:
                # Morning rush - lower scores
                score = base_score - random.uniform(1.0, 2.0)
            elif "PM" in hour and int(hour.split()[0]) in [4, 5, 6]:
                # Evening rush - lower scores
                score = base_score - random.uniform(1.2, 2.2)
            else:
                # Other times - better scores
                score = base_score + random.uniform(0.2, 1.0)
            
            # Keep within range
            score = max(1.0, min(10.0, score))
            scores.append(round(score, 1))
        
        # Create a timeline chart
        timeline_data = pd.DataFrame({
            "Hour": hours,
            "Safety Score": scores
        })
        
        # Use Streamlit's line chart
        st.line_chart(timeline_data.set_index("Hour"))
        
        # Highlight best time to travel
        best_hour_index = scores.index(max(scores))
        st.info(f"🕒 **Recommended travel time**: {hours[best_hour_index]} (Safety Score: {scores[best_hour_index]}/10)")

def enhance_safety_map(m, analysis, origin_coords, dest_coords):
    """
    Enhance the safety map with safety-related features.
    
    Args:
        m: Folium map object
        analysis: Dictionary with safety analysis results
        origin_coords: Origin coordinates (lat, lng)
        dest_coords: Destination coordinates (lat, lng)
    
    Returns:
        Enhanced map object
    """
    if not analysis or not origin_coords or not dest_coords:
        return m
    
    # Add hotspots to the map
    if "hotspots" in analysis:
        for hotspot in analysis["hotspots"]:
            folium.CircleMarker(
                location=[hotspot["lat"], hotspot["lng"]],
                radius=hotspot["intensity"] * 5,  # Scale the circle size based on intensity
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.4,
                popup=f"Safety Hotspot: {hotspot['description']} (Risk: {hotspot['intensity']}/10)"
            ).add_to(m)
    
    # Add alternative routes if they exist
    if "alternative_routes" in analysis:
        for i, route in enumerate(analysis.get("alternative_routes", [])):
            if "path" in route and len(route["path"]) > 1:
                route_color = "green" if route.get("is_safer", False) else "blue"
                folium.PolyLine(
                    route["path"],
                    color=route_color,
                    weight=3,
                    opacity=0.7,
                    popup=f"Alternative Route {i+1}: Safety Score {route.get('safety_score', 'N/A')}"
                ).add_to(m)
    
    return m

def display_safety_recommendations(analysis):
    """
    Display safety recommendations based on analysis.
    
    Args:
        analysis: Dictionary with safety analysis results
    """
    if not analysis:
        return
    
    st.subheader("🛡️ Safety Recommendations")
    
    recommendations = analysis.get("recommendations", [])
    if recommendations:
        for i, rec in enumerate(recommendations):
            st.markdown(f"**{i+1}.** {rec}")
    else:
        st.info("No specific safety recommendations for this route at the current time.")

# Helper functions
def get_safety_recommendations(safety_score, time_of_day, weather, traffic_density, mode):
    """Generate safety recommendations based on conditions."""
    recommendations = []
    
    # Base recommendations
    recommendations.append("Allow extra time for your journey to avoid rushing")
    
    # Time-based recommendations
    if time_of_day in ["morning_rush", "evening_rush"]:
        recommendations.append("Consider alternative routes to avoid peak traffic congestion")
    
    if time_of_day in ["night", "late_night"]:
        recommendations.append("Ensure headlights are on and be vigilant for pedestrians in dark conditions")
    
    # Weather-based recommendations
    if weather in ["rain", "fog", "snow", "storm"]:
        if mode == "driving":
            recommendations.append(f"Reduce speed in {weather} conditions and increase following distance")
        elif mode in ["bicycling", "walking"]:
            recommendations.append(f"Consider alternative transportation in {weather} conditions")
    
    if weather == "fog":
        if mode == "driving":
            recommendations.append("Use low-beam headlights in fog for better visibility")
        else:
            recommendations.append("Wear bright or reflective clothing in fog for better visibility")
    
    # Traffic-based recommendations
    if traffic_density == "high":
        if mode == "driving":
            recommendations.append("Stay in your lane and avoid frequent lane changes in heavy traffic")
        elif mode == "bicycling":
            recommendations.append("Consider using dedicated bike lanes or alternative routes to avoid heavy traffic")
        elif mode == "walking":
            recommendations.append("Use pedestrian crossings and be extra cautious when crossing busy streets")
        elif mode == "transit":
            recommendations.append("Expect delays in public transit during heavy traffic periods")
    
    # Safety score based recommendations
    if safety_score < 5.0:
        recommendations.append("Consider delaying trip if possible until conditions improve")
    
    # Mode-specific recommendations
    if mode == "driving":
        recommendations.append("Maintain a safe following distance and avoid distracted driving")
    elif mode == "bicycling":
        recommendations.append("Use hand signals, wear a helmet, and follow traffic laws for cyclists")
    elif mode == "walking":
        recommendations.append("Stay on sidewalks and use crosswalks whenever possible")
    elif mode == "transit":
        recommendations.append("Plan your journey in advance and check for service updates")
    
    # Return 3-5 recommendations
    if len(recommendations) > 5:
        recommendations = recommendations[:5]
    
    return recommendations

def generate_sample_hotspots():
    """Generate sample safety hotspots for demonstration."""
    return [
        {"lat": 37.3352, "lng": -121.8811, "intensity": 7.5, "description": "High traffic intersection near SJSU"},
        {"lat": 37.3639, "lng": -121.9289, "intensity": 8.2, "description": "Construction zone near airport"},
        {"lat": 37.3199, "lng": -121.9450, "intensity": 6.8, "description": "Congestion around Santana Row"},
        {"lat": 37.3229, "lng": -121.9052, "intensity": 7.2, "description": "Road work on Coleman Ave"}
    ]

def generate_historical_data():
    """Generate sample historical safety data for demonstration."""
    return {
        "accident_rate": "2.3 incidents per month",
        "peak_hours": "7-9 AM, 4-6 PM",
        "average_score": "6.8/10",
        "historical_trend": "Improving",
        "construction_info": "2 active projects along route"
    }
