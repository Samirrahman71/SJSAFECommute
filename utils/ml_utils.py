"""
Machine Learning Utilities for San Jose Safe Commute
Provides helper functions for ML model integration and data processing
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os
import json
import sys
from pathlib import Path

# Add parent directory to import path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ml_models import safety_model, risk_classifier, generate_time_predictions

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_safety_time_predictions(origin, destination, current_safety_score, risk_factors):
    """
    Generate safety predictions for different times of day using ML models
    
    Args:
        origin: Starting location
        destination: Ending location
        current_safety_score: Current calculated safety score
        risk_factors: Dictionary of risk factors
        
    Returns:
        Dictionary with time periods and corresponding safety scores
    """
    try:
        # Add origin and destination to features
        features = risk_factors.copy()
        features['origin'] = origin
        features['destination'] = destination
        
        # Generate predictions
        predictions = generate_time_predictions(safety_model, features, current_safety_score)
        return predictions
        
    except Exception as e:
        logger.error(f"Error in get_safety_time_predictions: {str(e)}")
        
        # Fallback to heuristic predictions if ML fails
        return {
            "Early Morning (5-7 AM)": min(current_safety_score + 1.0, 10.0),
            "Morning Rush (7-9 AM)": max(current_safety_score - 1.0, 1.0),
            "Mid-Day (9 AM-4 PM)": min(current_safety_score + 0.5, 10.0),
            "Evening Rush (4-7 PM)": max(current_safety_score - 1.2, 1.0),
            "Evening (7-10 PM)": current_safety_score,
            "Late Night (10 PM-5 AM)": max(current_safety_score - 0.8, 1.0)
        }

def predict_route_safety(origin, destination, time_of_day, weather, traffic_density, mode):
    """
    Use ML models to predict route safety score and risk factors
    
    Args:
        origin: Starting location
        destination: Ending location
        time_of_day: Selected time of day
        weather: Weather conditions
        traffic_density: Traffic density level (0-10)
        mode: Transportation mode
        
    Returns:
        Dictionary with safety analysis
    """
    try:
        # Current day of week
        day_of_week = datetime.now().strftime("%A")
        
        # Build feature set
        features = {
            'origin': origin,
            'destination': destination,
            'time_of_day': time_of_day,
            'weather': weather,
            'traffic_density': traffic_density,
            'day_of_week': day_of_week,
            'transport_mode': mode
        }
        
        # Get safety score prediction
        safety_score = safety_model.predict(features)
        safety_score = round(float(safety_score), 1)
        
        # Get risk classification
        risk_prediction = risk_classifier.predict_risk(features)
        
        # Generate time-based predictions
        time_predictions = generate_time_predictions(safety_model, features, safety_score)
        
        # Determine safety category
        if safety_score >= 8.0:
            safety_category = "high"
            color = "green"
        elif safety_score >= 6.0:
            safety_category = "medium"
            color = "yellow"
        else:
            safety_category = "low"
            color = "red"
        
        # Generate alerts based on risk prediction
        alerts = []
        if risk_prediction['risk_level'] == 'high':
            alerts.append({
                "type": "High Risk Area",
                "description": "This route passes through areas with historically high crash rates"
            })
        
        if weather.lower() in ['rainy', 'foggy', 'snow', 'storm']:
            alerts.append({
                "type": "Weather Warning",
                "description": f"Current {weather} conditions increase risk by approximately 30%"
            })
            
        if 'rush' in time_of_day.lower():
            alerts.append({
                "type": "Rush Hour Alert",
                "description": "Rush hour traffic significantly increases crash probability"
            })
        
        # Format the time predictions for the UI
        formatted_predictions = {}
        for time_label, score in time_predictions.items():
            formatted_predictions[time_label] = round(float(score), 1)
        
        # Build complete analysis object
        analysis = {
            "safety_score": safety_score,
            "color": color,
            "safety_category": safety_category,
            "time_predictions": formatted_predictions,
            "risk_level": risk_prediction['risk_level'],
            "risk_probability": risk_prediction['probability'],
            "alerts": alerts,
            "top_reasons": [
                f"Traffic density is {traffic_density}",
                f"Weather conditions: {weather}",
                f"Time of day: {time_of_day}"
            ],
            "ai_powered": True
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in predict_route_safety: {str(e)}")
        
        # Return a basic fallback analysis
        return {
            "safety_score": 7.0,
            "color": "yellow",
            "safety_category": "medium",
            "time_predictions": {
                "Early Morning (5-7 AM)": 8.5,
                "Morning Rush (7-9 AM)": 6.0,
                "Mid-Day (9 AM-4 PM)": 7.5,
                "Evening Rush (4-7 PM)": 5.5,
                "Evening (7-10 PM)": 7.0,
                "Late Night (10 PM-5 AM)": 6.5
            },
            "risk_level": "medium",
            "risk_probability": 0.6,
            "alerts": [
                {
                    "type": "General Caution",
                    "description": "Exercise normal caution on this route"
                }
            ],
            "top_reasons": [
                f"Traffic density is {traffic_density}",
                f"Weather conditions: {weather}",
                f"Time of day: {time_of_day}"
            ],
            "ai_powered": False
        }

def analyze_accident_hotspots(df):
    """
    Use ML to identify and analyze accident hotspots from crash data
    
    Args:
        df: DataFrame with crash data
        
    Returns:
        Dictionary with hotspot analysis
    """
    try:
        # Ensure we have the necessary columns
        if df is None or len(df) == 0 or 'location' not in df.columns:
            return {"hotspots": [], "error": "Insufficient data for hotspot analysis"}
        
        # Group crashes by location
        location_counts = df['location'].value_counts()
        
        # Get top 10 hotspots
        top_hotspots = location_counts.head(10)
        
        # Create hotspot objects
        hotspots = []
        for location, count in top_hotspots.items():
            # Filter for crashes at this location
            location_crashes = df[df['location'] == location]
            
            # Calculate average severity at this location
            avg_severity = location_crashes['severity'].mean() if 'severity' in location_crashes.columns else None
            
            # Calculate most common times
            if 'datetime' in location_crashes.columns:
                # Extract hour
                location_crashes['hour'] = location_crashes['datetime'].dt.hour
                peak_hour = location_crashes['hour'].value_counts().idxmax()
                
                # Extract day of week
                location_crashes['day'] = location_crashes['datetime'].dt.day_name()
                peak_day = location_crashes['day'].value_counts().idxmax()
            else:
                peak_hour = None
                peak_day = None
            
            # Build hotspot object
            hotspot = {
                "location": location,
                "crash_count": int(count),
                "avg_severity": float(round(avg_severity, 1)) if avg_severity is not None else None,
                "peak_hour": int(peak_hour) if peak_hour is not None else None,
                "peak_day": peak_day
            }
            
            hotspots.append(hotspot)
        
        # Return analysis
        return {
            "hotspots": hotspots,
            "total_analyzed": len(df),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_accident_hotspots: {str(e)}")
        return {"hotspots": [], "error": str(e)}

def validate_ml_model_inputs(origin, destination, time_of_day, weather, traffic_density, mode):
    """
    Validate and sanitize inputs for ML models
    
    Args:
        origin: Starting location
        destination: Ending location
        time_of_day: Selected time of day
        weather: Weather conditions
        traffic_density: Traffic density level
        mode: Transportation mode
        
    Returns:
        Tuple of (is_valid, sanitized_inputs or error_message)
    """
    errors = []
    
    # Validate required string inputs
    if not origin or not isinstance(origin, str):
        errors.append("Origin location is required")
    
    if not destination or not isinstance(destination, str):
        errors.append("Destination location is required")
    
    # Validate time of day format
    valid_times = [
        "Current Time",
        "Early Morning (5-7 AM)",
        "Morning Commute (7-9 AM)",
        "Midday (11 AM-1 PM)",
        "Evening Commute (4-6 PM)",
        "Late Night (10 PM-12 AM)"
    ]
    
    if not time_of_day or time_of_day not in valid_times:
        errors.append(f"Invalid time of day. Must be one of: {', '.join(valid_times)}")
    
    # Validate weather
    valid_weather = ["Clear", "Cloudy", "Rainy", "Foggy"]
    if not weather or weather not in valid_weather:
        errors.append(f"Invalid weather condition. Must be one of: {', '.join(valid_weather)}")
    
    # Validate traffic density
    try:
        traffic_density = int(traffic_density)
        if traffic_density < 0 or traffic_density > 10:
            errors.append("Traffic density must be between 0 and 10")
    except (ValueError, TypeError):
        errors.append("Traffic density must be a number between 0 and 10")
    
    # Validate mode and map UI values to expected values
    ui_to_api_mode = {
        "Car": "driving",
        "Public Transit": "transit",
        "Walking": "walking",
        "Cycling": "bicycling"
    }
    
    if not mode or mode not in ui_to_api_mode.keys():
        errors.append(f"Invalid transportation mode. Must be one of: {', '.join(ui_to_api_mode.keys())}")
    else:
        # Map the UI mode to the API mode
        mode = ui_to_api_mode.get(mode, "driving")
    
    # Return validation result
    if errors:
        return (False, errors)
    
    # Sanitize and return valid inputs
    return (True, {
        "origin": origin.strip(),
        "destination": destination.strip(),
        "time_of_day": time_of_day,
        "weather": weather,
        "traffic_density": traffic_density,
        "mode": mode  # This now contains the mapped value
    })
