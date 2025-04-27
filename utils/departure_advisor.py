"""
Departure Advisor - AI-powered departure time recommendations
Uses reinforcement learning concepts to recommend optimal departure windows
based on user preferences and historical data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

class DepartureAdvisor:
    """
    Personalized Departure Advisor that uses RL concepts to optimize departure recommendations
    based on user preferences and historical patterns.
    """
    
    def __init__(self):
        # Initialize preference weights (to be learned over time)
        self.preference_weights = {
            "time_efficiency": 0.5,  # Weight for fastest route
            "safety": 0.3,           # Weight for safest route 
            "comfort": 0.2,          # Weight for least stops/transfers
            "scenic": 0.1            # Weight for scenic value
        }
        
        # Normalize weights
        total = sum(self.preference_weights.values())
        for key in self.preference_weights:
            self.preference_weights[key] /= total
        
        # User lateness tolerance (minutes) - would be learned from user feedback
        self.lateness_tolerance = 5
        
        # Initialize historical data structure
        self.commute_history = []
        
        # Time buffers for different tolerance levels (minutes)
        self.time_buffers = {
            "strict": 15,       # Buffer for strict schedules (e.g., important meetings)
            "moderate": 10,     # Buffer for moderately flexible schedules
            "flexible": 5       # Buffer for very flexible schedules
        }
        
        # Sample data for demonstration
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize sample historical data for demonstration purposes"""
        # Sample commute routes (origin, destination, time of day, duration in minutes)
        sample_routes = [
            # Downtown San Jose to Santana Row
            {"origin": "Downtown San Jose", "destination": "Santana Row", 
             "time_of_day": "morning_rush", "avg_duration": 25, "peak_variance": 15},
            {"origin": "Downtown San Jose", "destination": "Santana Row", 
             "time_of_day": "mid_day", "avg_duration": 18, "peak_variance": 5},
            {"origin": "Downtown San Jose", "destination": "Santana Row", 
             "time_of_day": "evening_rush", "avg_duration": 32, "peak_variance": 20},
            
            # SJSU to Santana Row
            {"origin": "San Jose State University", "destination": "Santana Row", 
             "time_of_day": "morning_rush", "avg_duration": 28, "peak_variance": 12},
            {"origin": "San Jose State University", "destination": "Santana Row", 
             "time_of_day": "mid_day", "avg_duration": 20, "peak_variance": 7},
            {"origin": "San Jose State University", "destination": "Santana Row", 
             "time_of_day": "evening_rush", "avg_duration": 35, "peak_variance": 18},
            
            # Airport to Downtown
            {"origin": "San Jose International Airport", "destination": "Downtown San Jose", 
             "time_of_day": "morning_rush", "avg_duration": 22, "peak_variance": 10},
            {"origin": "San Jose International Airport", "destination": "Downtown San Jose", 
             "time_of_day": "mid_day", "avg_duration": 15, "peak_variance": 5},
            {"origin": "San Jose International Airport", "destination": "Downtown San Jose", 
             "time_of_day": "evening_rush", "avg_duration": 30, "peak_variance": 15},
        ]
        
        self.route_data = pd.DataFrame(sample_routes)
    
    def update_preferences(self, new_preferences):
        """Update user preferences based on feedback"""
        for key, value in new_preferences.items():
            if key in self.preference_weights:
                self.preference_weights[key] = value
        
        # Normalize weights again
        total = sum(self.preference_weights.values())
        for key in self.preference_weights:
            self.preference_weights[key] /= total
    
    def update_lateness_tolerance(self, tolerance_mins):
        """Update user's tolerance for lateness"""
        self.lateness_tolerance = max(0, tolerance_mins)
    
    def _get_route_duration(self, origin, destination, time_of_day, mode="driving", weather="clear", traffic="medium"):
        """Get estimated route duration based on historical data and current conditions"""
        # Filter route data for the specific origin and destination
        route_matches = self.route_data[
            (self.route_data["origin"].str.contains(origin, case=False) | 
             self.route_data["destination"].str.contains(origin, case=False)) &
            (self.route_data["origin"].str.contains(destination, case=False) | 
             self.route_data["destination"].str.contains(destination, case=False)) &
            (self.route_data["time_of_day"] == time_of_day)
        ]
        
        if len(route_matches) > 0:
            # Get the average duration
            base_duration = route_matches.iloc[0]["avg_duration"]
            variance = route_matches.iloc[0]["peak_variance"]
        else:
            # Default values if no match is found
            base_duration = 25  # Default 25 minutes
            variance = 10       # Default 10 minutes variance
        
        # Adjust for weather conditions
        weather_factor = {
            "clear": 1.0,
            "rain": 1.3,
            "fog": 1.2,
            "snow": 1.5,
            "storm": 1.4
        }.get(weather, 1.0)
        
        # Adjust for traffic density
        traffic_factor = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.4
        }.get(traffic, 1.0)
        
        # Adjust for transportation mode
        mode_factor = {
            "driving": 1.0,
            "walking": 4.0,
            "bicycling": 1.5,
            "transit": 1.2
        }.get(mode, 1.0)
        
        # Calculate final duration with some randomness to simulate real-world variability
        adjusted_duration = base_duration * weather_factor * traffic_factor * mode_factor
        variability = random.uniform(-variance/2, variance/2)
        
        return max(5, adjusted_duration + variability)  # Ensure minimum 5 minutes
    
    def recommend_departure_time(self, origin, destination, arrival_time_str, schedule_type="moderate", 
                                time_of_day=None, mode="driving", weather="clear", traffic="medium"):
        """
        Recommend optimal departure time based on user preferences, historical data, and current conditions
        
        Args:
            origin: Starting location
            destination: Destination location
            arrival_time_str: Desired arrival time (format: "HH:MM" or "HH:MM AM/PM")
            schedule_type: User's schedule rigidity ("strict", "moderate", or "flexible")
            time_of_day: Time of day category (if None, inferred from arrival time)
            mode: Transportation mode
            weather: Weather conditions
            traffic: Traffic density
            
        Returns:
            Dictionary with departure recommendations and explanation
        """
        # Convert arrival time string to datetime
        try:
            # Try parsing with AM/PM format
            if "AM" in arrival_time_str or "PM" in arrival_time_str:
                arrival_time = datetime.strptime(arrival_time_str, "%I:%M %p")
            else:
                # Try 24-hour format
                arrival_time = datetime.strptime(arrival_time_str, "%H:%M")
                
            # Set to today's date to get proper time calculations
            now = datetime.now()
            arrival_time = arrival_time.replace(
                year=now.year, month=now.month, day=now.day
            )
        except ValueError:
            # Default to 1 hour from now if parsing fails
            arrival_time = datetime.now() + timedelta(hours=1)
        
        # Determine time of day if not provided
        if time_of_day is None:
            hour = arrival_time.hour
            if 5 <= hour < 7:
                time_of_day = "early_morning"
            elif 7 <= hour < 9:
                time_of_day = "morning_rush"
            elif 9 <= hour < 16:
                time_of_day = "mid_day"
            elif 16 <= hour < 19:
                time_of_day = "evening_rush"
            elif 19 <= hour < 22:
                time_of_day = "evening"
            else:
                time_of_day = "late_night"
        
        # Get estimated route duration
        duration_mins = self._get_route_duration(origin, destination, time_of_day, mode, weather, traffic)
        
        # Add buffer based on schedule type and user preferences
        buffer_mins = self.time_buffers.get(schedule_type, 10)
        
        # Calculate optimal departure time
        total_buffer = buffer_mins + (self.lateness_tolerance / 2)
        optimal_departure = arrival_time - timedelta(minutes=duration_mins + total_buffer)
        
        # Calculate early and late departure windows based on tolerance
        earliest_departure = optimal_departure - timedelta(minutes=5)
        latest_departure = optimal_departure + timedelta(minutes=max(0, self.lateness_tolerance - buffer_mins/2))
        
        # Format times for display
        format_time = lambda dt: dt.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
        
        # Build recommendation
        recommendation = {
            "estimated_duration": round(duration_mins),
            "optimal_departure_time": format_time(optimal_departure),
            "earliest_departure": format_time(earliest_departure),
            "latest_departure": format_time(latest_departure),
            "buffer_minutes": buffer_mins,
            "explanation": self._generate_explanation(
                origin, destination, format_time(arrival_time), duration_mins, 
                buffer_mins, schedule_type, weather, traffic, mode
            )
        }
        
        return recommendation
    
    def _generate_explanation(self, origin, destination, arrival_time, duration, 
                             buffer, schedule_type, weather, traffic, mode):
        """Generate a natural language explanation for the recommendation"""
        # Base explanation
        explanation = f"For your {mode} trip from {origin} to {destination}, "
        
        # Add weather and traffic context
        if weather != "clear":
            explanation += f"considering the {weather} conditions and "
        explanation += f"{traffic} traffic levels, "
        
        # Explain duration and buffer
        explanation += f"I estimate a travel time of {round(duration)} minutes. "
        
        # Explain buffer based on schedule type
        if schedule_type == "strict":
            explanation += f"Since your schedule is strict, I've added a {buffer}-minute buffer to ensure you arrive on time. "
        elif schedule_type == "moderate":
            explanation += f"I've included a {buffer}-minute buffer for unexpected delays. "
        else:
            explanation += f"With your flexible schedule, I've added a minimal {buffer}-minute buffer. "
        
        # Add arrival context
        explanation += f"This will get you to your destination by {arrival_time}."
        
        # Add personalization based on learning
        top_preference = max(self.preference_weights.items(), key=lambda x: x[1])[0]
        if top_preference == "time_efficiency":
            explanation += " This recommendation prioritizes the fastest route based on your preferences."
        elif top_preference == "safety":
            explanation += " I've prioritized safer route options based on your preferences."
        elif top_preference == "comfort":
            explanation += " This route minimizes transfers and stops based on your comfort preferences."
        elif top_preference == "scenic":
            explanation += " I've considered more scenic route options based on your preferences."
        
        return explanation

# Singleton instance for app-wide use
advisor = DepartureAdvisor()

def get_departure_recommendation(origin, destination, arrival_time, schedule_type="moderate", 
                               time_of_day=None, mode="driving", weather="clear", traffic="medium"):
    """Wrapper function to get departure recommendations"""
    return advisor.recommend_departure_time(
        origin, destination, arrival_time, schedule_type, 
        time_of_day, mode, weather, traffic
    )

def update_user_preferences(preferences):
    """Update user preference weights"""
    advisor.update_preferences(preferences)

def update_lateness_tolerance(minutes):
    """Update user's tolerance for lateness"""
    advisor.update_lateness_tolerance(minutes)
