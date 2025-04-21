# San Jose Safe Commute App

## Overview

An AI-powered app that helps San Jose residents plan safer commutes by analyzing historical crash data and providing personalized route safety recommendations. The app uses advanced ML models to predict safety scores and risk levels for different routes at different times of day.

## Technologies Used

- **Streamlit**: For the web interface and interactive elements
- **OpenAI API**: Powers the AI assistant and safety analysis features
- **Google Maps API**: For location autocomplete and route visualization
- **Pandas & NumPy**: For data processing and analysis
- **Plotly**: For interactive data visualizations
- **Machine Learning**: Custom safety score prediction and risk classification models

## Key Features

- **Route Safety Analysis**: Calculates safety scores for routes based on historical data
- **Interactive Maps**: Visualizes safety hotspots and alternative routes
- **AI Safety Assistant**: Answers safety-related questions about commuting in San Jose
- **Crash Data Analysis**: Interactive visualizations of traffic incident patterns
- **Responsive Design**: Optimized for both mobile and desktop use

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Samirrahman71/SJSAFECommute.git

# Install dependencies
pip install -r requirements.txt

# Create a .env file with your API keys
echo "GOOGLE_MAPS_API_KEY=your_key_here" > .env
echo "OPENAI_API_KEY=your_key_here" >> .env

# Run the app
streamlit run 1_🏠_Home.py
```

## Project Structure

- **Main App**: Entry point with route safety analysis features
- **Crash Data Analysis**: In-depth analysis of historical crash data
- **Utils Directory**: Helper functions for data processing, ML models, and API integrations
- **Models Directory**: Pre-trained machine learning models for safety prediction

## Recent Updates

- All times now displayed in 12-hour format for better readability
- Enhanced error handling for improved reliability
- Improved UI responsiveness for mobile devices
- Streamlined data processing pipeline for faster predictions

## Live Demo

Check out the live app: [sjsafecommute.streamlit.app](https://sjsafecommute.streamlit.app/)

## License

MIT
