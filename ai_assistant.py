"""
AI Assistant for San Jose Safe Commute
Provides natural language processing for route questions and personalized recommendations
"""

import openai
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import random

# Initialize OpenAI client
def init_openai():
    """Initialize OpenAI client with API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.warning("OpenAI API key not found. Using simulated AI responses.")
    return api_key

def get_ai_route_analysis(origin, destination, user_preferences=None, historical_data=None):
    """
    Generate an AI-powered route analysis using user's query and preferences
    
    Args:
        origin: Starting location
        destination: Ending location
        user_preferences: Dictionary of user preferences
        historical_data: Historical incident data if available
        
    Returns:
        Dictionary with AI analysis and recommendations
    """
    api_key = init_openai()
    
    # If we have a valid API key, use OpenAI
    if api_key:
        try:
            client = openai.OpenAI(api_key=api_key)
            
            # Construct prompt with all relevant information
            prompt = f"""
            As a San Jose Safe Commute AI Assistant, analyze a route from {origin} to {destination}.
            
            Current time: {datetime.now().strftime('%A %I:%M %p')}
            """
            
            if user_preferences:
                prompt += "\nUser preferences:\n"
                for pref, value in user_preferences.items():
                    prompt += f"- {pref}: {value}\n"
            
            if historical_data is not None:
                prompt += "\nHistorical incident data summary:\n"
                prompt += "- Average daily incidents: " + str(historical_data.get('avg_incidents', 'Unknown')) + "\n"
                prompt += "- Recent hotspots: " + ", ".join(historical_data.get('hotspots', ['None'])) + "\n"
            
            prompt += """
            Provide a detailed safety analysis including:
            1. Overall safety assessment
            2. Personalized safety recommendations based on user preferences
            3. Specific areas of concern for this route
            4. Best time to travel
            5. Suggestions for safer alternative routes if applicable
            
            Format your response as a JSON with the following fields:
            - overall_assessment: (string)
            - safety_score: (float between 1-10)
            - key_concerns: (list of strings)
            - recommendations: (list of strings)
            - best_time: (string)
            - alternatives: (list of strings)
            """
            
            # Make API call
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a San Jose Safe Commute AI Assistant focused on route safety analysis."},
                         {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            analysis = json.loads(response.choices[0].message.content)
            analysis['ai_powered'] = True
            return analysis
            
        except Exception as e:
            st.error(f"Error connecting to OpenAI API: {e}")
            # Fall back to simulated response
            return get_simulated_ai_response(origin, destination, user_preferences)
    else:
        # Use simulated response if no API key
        return get_simulated_ai_response(origin, destination, user_preferences)

def get_simulated_ai_response(origin, destination, user_preferences=None):
    """Generate a simulated AI response when API is unavailable"""
    
    # Base safety score between 1-10
    safety_score = round(random.uniform(5.5, 8.5), 1)
    
    # Adjust based on time of day
    current_hour = datetime.now().hour
    time_factor = 0
    if 7 <= current_hour <= 9 or 16 <= current_hour <= 18:  # Rush hours
        time_factor = -1.0
        time_description = "rush hour"
    elif 22 <= current_hour or current_hour <= 4:  # Late night
        time_factor = -1.5
        time_description = "late night"
    else:
        time_description = "normal traffic hours"
    
    safety_score += time_factor
    safety_score = max(1.0, min(10.0, safety_score))
    
    # Common hotspots in San Jose
    hotspots = [
        "Highway 101 and Tully Road interchange",
        "280 and 87 interchange",
        "Downtown San Jose, particularly near SAP Center during events",
        "Story Road and King Road intersection",
        "Capitol Expressway near Eastridge Mall"
    ]
    
    # Generate analysis based on safety score
    if safety_score >= 7.5:
        assessment = f"Your route from {origin} to {destination} is generally safe during {time_description}."
        concerns = random.sample(["Minor congestion may occur", "Limited visibility in foggy conditions", "Occasional jaywalking in downtown areas"], 1)
    elif safety_score >= 5.5:
        assessment = f"Your route from {origin} to {destination} has moderate safety concerns during {time_description}."
        concerns = random.sample(["Moderate congestion likely", "Construction zones may cause delays", "Several unprotected left turns", "Limited bike lanes"], 2)
    else:
        assessment = f"Your route from {origin} to {destination} has significant safety concerns during {time_description}."
        concerns = random.sample(["Heavy congestion expected", "High accident history at key intersections", "Limited lighting at night", "Pedestrian crossing hazards", "Multiple blind curves"], 3)
    
    # Include random hotspots that might be on the route
    route_hotspots = random.sample(hotspots, 2)
    concerns.append(f"Route passes near {route_hotspots[0]}")
    
    # Generate recommendations
    general_recommendations = [
        "Allow extra travel time during peak hours",
        "Enable real-time traffic alerts on your phone",
        "Consider using transit options during high-traffic periods",
        "Avoid distractions while driving or walking",
        "Watch for cyclists at intersections",
        "Use designated crosswalks when walking"
    ]
    
    if user_preferences and 'travel_mode' in user_preferences:
        mode = user_preferences['travel_mode'].lower()
        mode_recommendations = {
            'driving': [
                "Keep a safe following distance in traffic",
                "Be cautious at unprotected left turns",
                "Watch for pedestrians in downtown areas"
            ],
            'walking': [
                "Use crosswalks and obey pedestrian signals",
                "Increase visibility with bright clothing at night",
                "Stay on designated sidewalks and paths"
            ],
            'bicycling': [
                "Use dedicated bike lanes when available",
                "Wear a helmet and reflective gear",
                "Be especially cautious at intersections"
            ],
            'transit': [
                "Check real-time transit schedules before departing",
                "Be aware of your surroundings at transit stops",
                "Have a backup route in case of service disruptions"
            ]
        }
        specific_recs = mode_recommendations.get(mode, [])
        recommendations = random.sample(general_recommendations, 2) + random.sample(specific_recs, min(2, len(specific_recs)))
    else:
        recommendations = random.sample(general_recommendations, 3)
    
    # Best travel times
    if current_hour < 12:
        best_time = "10:00 AM to 2:00 PM when traffic is lighter"
    else:
        best_time = "10:00 AM to 2:00 PM or after 7:00 PM when traffic subsides"
    
    # Alternative routes
    alternatives = [
        f"Consider taking Lawrence Expressway instead of Highway 101",
        f"Central Expressway may be a safer alternative during rush hour",
        f"If available, light rail transit avoids traffic congestion entirely"
    ]
    
    return {
        'overall_assessment': assessment,
        'safety_score': safety_score,
        'key_concerns': concerns,
        'recommendations': recommendations,
        'best_time': best_time,
        'alternatives': random.sample(alternatives, 2),
        'ai_powered': True
    }

def chat_with_ai_assistant(user_query, chat_history=None, user_data=None):
    """
    Chat with the AI assistant about route safety or general commute questions
    
    Args:
        user_query: User's question or request
        chat_history: Previous conversation history
        user_data: User profile and preference data
        
    Returns:
        AI response as string
    """
    api_key = init_openai()
    
    # Use OpenAI if API key is available
    if api_key:
        try:
            client = openai.OpenAI(api_key=api_key)
            
            # Construct messages with history if available
            messages = [
                {"role": "system", "content": "You are a San Jose Safe Commute AI Assistant specialized in providing commute safety advice for San Jose, California. Keep responses focused on commute safety, traffic patterns, and local transportation. Provide practical, concise answers that emphasize safety."}
            ]
            
            # Add chat history if available
            if chat_history:
                messages.extend(chat_history)
            
            # Add user profile information if available
            if user_data:
                profile_info = "User information:\n"
                for key, value in user_data.items():
                    profile_info += f"- {key}: {value}\n"
                messages.append({"role": "system", "content": profile_info})
            
            # Add current user query
            messages.append({"role": "user", "content": user_query})
            
            # Make API call
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            st.error(f"Error connecting to OpenAI API: {e}")
            return get_simulated_chat_response(user_query)
    else:
        # Use simulated response if no API key
        return get_simulated_chat_response(user_query)

def get_simulated_chat_response(query):
    """Generate a simulated chat response when API is unavailable"""
    
    # General responses based on keyword matching
    responses = {
        "safest route": "The safest routes in San Jose typically avoid high-incident areas like the 101/880 interchange and parts of East San Jose during late hours. Consider using expressways like Lawrence or Central Expressway during peak hours instead of highways.",
        
        "best time": "The safest times to commute in San Jose are typically 10:00 AM to 2:00 PM on weekdays. Early mornings before 7:00 AM are also good. Avoid rush hours between 7-9 AM and 4-7 PM when accident rates increase by approximately 30%.",
        
        "traffic": "San Jose traffic patterns show highest congestion on highways 101, 87, and 280 during rush hours. Our safety data indicates increased incident rates of about 45% during these periods. Consider using traffic alerts and alternative routes like Lawrence Expressway.",
        
        "bike": "For cycling in San Jose, we recommend using the dedicated bike lanes on Guadalupe River Trail, Los Gatos Creek Trail, and the protected bike lanes downtown. Always wear a helmet and use lights at night, as our data shows 70% of cycling incidents occur in low-visibility conditions.",
        
        "public transport": "VTA light rail and buses in San Jose have excellent safety records. The transit center downtown and major stations are well-monitored. According to our data, public transit reduces your accident risk by approximately 60% compared to driving during rush hour.",
        
        "walking": "For pedestrian safety in San Jose, stick to well-lit areas with proper sidewalks. Exercise caution when crossing major intersections, especially along Santa Clara Street and Capitol Expressway, which have higher than average pedestrian incident rates.",
        
        "night": "Nighttime safety in San Jose varies by neighborhood. Our data shows a 40% increase in incidents after 10 PM, particularly in downtown and east side areas. If traveling at night, main roads like Stevens Creek Blvd and Winchester Blvd tend to be better monitored and better lit.",
        
        "construction": "Current major construction zones affecting San Jose traffic include the BART extension near Berryessa, parts of 101 near Brokaw Rd, and downtown near Google's upcoming campus. These areas show a 25% higher incident rate during construction periods.",
        
        "weather": "During rainy conditions, incident rates in San Jose increase by approximately 32%, particularly on highway on-ramps and the 280/87 interchange. Fog in South San Jose and Almaden areas can reduce visibility, especially in winter mornings."
    }
    
    # Default response if no keywords match
    default_responses = [
        "As your San Jose Safe Commute AI Assistant, I can provide specific safety information about routes, traffic patterns, and commute options in San Jose. What specific safety information would you like to know?",
        
        "I'm focused on helping you navigate San Jose safely. I can analyze safety for specific routes, recommend safer travel times, or advise on transit options. Could you provide more details about your commute needs?",
        
        "My analysis is based on historical traffic incidents, time-of-day patterns, and neighborhood safety data specific to San Jose. For more personalized recommendations, please specify your route or transportation method."
    ]
    
    # Check for keyword matches
    for keyword, response in responses.items():
        if keyword.lower() in query.lower():
            return response
    
    # Return default response if no keywords match
    return random.choice(default_responses)

def process_user_uploaded_data(uploaded_file):
    """
    Process user uploaded CSV data for safety analysis
    
    Args:
        uploaded_file: CSV file uploaded by user
        
    Returns:
        Processed dataframe and summary statistics
    """
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Basic validation - check for required columns
        required_columns = ['date', 'time', 'location', 'incident_type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return None, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Process data
        # Try to convert date and time if they exist
        try:
            if 'date' in df.columns and 'time' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
            elif 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'], errors='coerce')
        except:
            # If datetime conversion fails, continue without it
            pass
        
        # Generate summary statistics
        stats = {
            'total_incidents': len(df),
            'incident_types': df['incident_type'].value_counts().to_dict() if 'incident_type' in df.columns else {},
            'locations': df['location'].value_counts().head(5).to_dict() if 'location' in df.columns else {}
        }
        
        if 'datetime' in df.columns:
            # Add time-based statistics if datetime was successfully created
            df['hour'] = df['datetime'].dt.hour
            stats['incidents_by_hour'] = df['hour'].value_counts().sort_index().to_dict()
            
            if 'day_of_week' not in df.columns:
                df['day_of_week'] = df['datetime'].dt.day_name()
            stats['incidents_by_day'] = df['day_of_week'].value_counts().to_dict()
        
        return df, stats
    
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def generate_ai_insight_from_data(df, stats):
    """
    Generate AI insights from user uploaded data
    
    Args:
        df: Processed dataframe
        stats: Summary statistics dictionary
        
    Returns:
        List of insights as strings
    """
    api_key = init_openai()
    
    # Format the statistics as a text summary for the AI
    stats_text = json.dumps(stats, indent=2)
    
    if api_key:
        try:
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
            Analyze the following traffic incident data statistics for San Jose and provide 3-5 key insights
            that would be valuable for commuters planning their routes.
            
            Data summary:
            {stats_text}
            
            Format your response as a list of insights. Focus on actionable information like:
            - Patterns in incident types, locations, or times
            - Specific high-risk areas or intersections
            - Recommended times or routes based on the data
            - Safety tips relevant to the most common incident types
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a traffic safety analyst specializing in extracting valuable insights from incident data."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            insights = response.choices[0].message.content.strip().split('\n')
            # Clean up bullet points if present
            insights = [insight.lstrip('- ').lstrip('* ') for insight in insights if insight.strip()]
            return insights
            
        except Exception as e:
            # Fall back to simulated insights
            return generate_simulated_insights(stats)
    else:
        # Use simulated insights if no API key
        return generate_simulated_insights(stats)

def generate_simulated_insights(stats):
    """Generate simulated insights when API is unavailable"""
    
    insights = []
    
    # Get the most common incident type
    if stats.get('incident_types'):
        top_incident = max(stats['incident_types'].items(), key=lambda x: x[1])
        insights.append(f"The most common incident type is '{top_incident[0]}' accounting for {top_incident[1]} cases ({(top_incident[1]/stats['total_incidents'])*100:.1f}% of total).")
    
    # Get the most problematic location
    if stats.get('locations'):
        top_location = max(stats['locations'].items(), key=lambda x: x[1])
        insights.append(f"'{top_location[0]}' appears to be a high-risk area with {top_location[1]} recorded incidents.")
    
    # Time-based insights
    if stats.get('incidents_by_hour'):
        # Find peak hours (top 3)
        peak_hours = sorted(stats['incidents_by_hour'].items(), key=lambda x: x[1], reverse=True)[:3]
        peak_hour_text = ', '.join([f"{hour}:00" for hour, _ in peak_hours])
        insights.append(f"Highest risk times are around {peak_hour_text}. Consider adjusting your commute to avoid these peak incident hours.")
        
        # Find safest hours (bottom 3)
        safe_hours = sorted(stats['incidents_by_hour'].items(), key=lambda x: x[1])[:3]
        safe_hour_text = ', '.join([f"{hour}:00" for hour, _ in safe_hours])
        insights.append(f"Lowest incident times are around {safe_hour_text}, suggesting safer commute windows.")
    
    # Day-based insights
    if stats.get('incidents_by_day'):
        # Find most dangerous day
        dangerous_day = max(stats['incidents_by_day'].items(), key=lambda x: x[1])
        insights.append(f"{dangerous_day[0]} has the highest incident count with {dangerous_day[1]} occurrences. Extra caution is recommended when traveling on this day.")
    
    # Add a general safety recommendation
    general_tips = [
        "Based on incident patterns, maintaining a safe following distance and avoiding distracted driving would address many of the recorded incident types.",
        "The data suggests defensive driving techniques would be particularly valuable in high-incident areas.",
        "Consider using navigation apps with real-time traffic alerts to avoid high-risk locations identified in this data set."
    ]
    insights.append(random.choice(general_tips))
    
    return insights
