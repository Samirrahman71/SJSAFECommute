# San Jose Safe Commute App (SJCAPP)

A smart Streamlit application designed to help San Jose commuters assess traffic risks and plan safer commutes using AI-powered analytics.

## Features

### 🎯 Risk Assessment
- Real-time risk score calculation
- Time-based risk factors (rush hours, late night, etc.)
- Weather impact analysis
- Interactive route safety visualization

### 📊 Analytics Dashboard
- Neighborhood safety analysis
- Time period risk patterns
- Weather impact statistics
- Traffic density visualization

### 🗺️ Route Planning
- Google Maps integration for address lookup
- Interactive safety map
- Dynamic route recommendations
- Time-sensitive alerts

### 🔔 Safety Recommendations
- Context-aware safety tips
- Time-based precautions
- Weather-specific guidance
- Emergency contact suggestions

## Tech Stack
- Python 3.x
- Streamlit
- Plotly
- Folium (for maps)
- Google Maps API
- pandas & numpy

## Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/Samirrahman71/SJCAPP.git
   cd SJCAPP
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file
   - Add your Google Maps API key:
     ```
     GOOGLE_MAPS_API_KEY=your_api_key_here
     ```

4. Run the app:
   ```bash
   streamlit run 1_🏠_Home.py
   ```

## Development
- Built with Streamlit for rapid prototyping
- Modular design with separate pages for analytics
- Session state management for persistent data
- Responsive UI with real-time updates

## Deployment
- Deployable to Streamlit Cloud
- Environment variables for secure API key management
- Continuous integration ready
