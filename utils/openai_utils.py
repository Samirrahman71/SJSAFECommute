import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
def get_openai_client():
    """Get the OpenAI client with proper API key configuration."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    # Create a simple client with just the API key
    client = OpenAI(api_key=api_key)
    return client

def get_commute_insights(
    route_info, 
    traffic_conditions, 
    weather_conditions, 
    incidents,
    model="gpt-4o",
    temperature=0.5,
    max_tokens=300
):
    """
    Generate commute insights using OpenAI.
    
    Args:
        route_info: String describing the route (e.g., "Home → Office at 8:00 AM")
        traffic_conditions: String describing current traffic 
        weather_conditions: String describing weather on the route
        incidents: String describing any incidents on the route
        model: OpenAI model to use
        temperature: Controls randomness (0-1)
        max_tokens: Maximum length of response
        
    Returns:
        String containing the AI-generated commute insights
    """
    client = get_openai_client()
    
    system_prompt = """You are "SJCAPP Commute Guru," a friendly, expert assistant for San Jose commuters.
Provide clear, concise route insights based on the provided traffic, weather, and incident data.

Structure your response as follows:
1. **Risk Summary** (2 sentences): Briefly assess the overall risk and impact on commute time.
2. **Smart Tips** (3 bullet points): Actionable recommendations to reduce delays and improve safety.
3. **Route Analysis** (1 paragraph): Why this route makes sense (or doesn't) based on current conditions.
4. **Alternative Option** (1-2 sentences): Suggest one thoughtful alternative (scenic, bike-friendly, or lower-risk).

Your tone should be casual but professional, focus on being helpful rather than alarmist, and prioritize safety.
Include specific references to San Jose landmarks and roads mentioned in the input.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
Route: {route_info}
Traffic: {traffic_conditions}  
Weather: {weather_conditions}  
Incidents: {incidents}
"""}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating commute insights: {str(e)}"
