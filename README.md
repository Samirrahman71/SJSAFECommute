<div align="center">

# 🚗 San Jose Safe Commute | AI Safety Navigator

An advanced AI-powered Streamlit app to help San Jose commuters plan safer routes by integrating real crash data analysis, machine learning risk prediction, and interactive safety visualizations.

---

## 🔍 Features

- **AI-Powered Route Safety Analysis**  
  Utilizes natural language processing and machine learning to analyze route safety with personalized recommendations.

- **Real Crash Data Integration**  
  Incorporates actual San Jose crash data (2011-2021) using statistical pattern recognition to identify risk factors.

- **Interactive Safety Visualization**  
  Displays comprehensive safety analytics with AI-generated insights about crash patterns, hotspots, and contributing factors.

- **ML Risk Prediction Model**  
  Employs ensemble learning techniques combining gradient boosting and logistic regression to calculate route-specific risk scores.

- **Temporal Pattern Recognition**  
  Uses time series analysis to identify high-risk travel periods based on historical incident data.

- **Smart Route Recommendations**  
  Generates alternative route suggestions optimized for safety using a custom-built path-finding algorithm.

- **Natural Language Safety Assistant**  
  Features an AI chat interface that can answer route-specific safety questions using contextual understanding.

- **Autocomplete Location Inputs**  
  Suggests San Jose-focused locations via Google Maps Places API integration.

---

## 📦 Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/Samirrahman71/SJCAPP.git
   cd SJCAPP
   ```
2. **Create & activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate         # macOS/Linux
   venv\Scripts\activate            # Windows
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### ⚙️ API Key Configuration

- Create a `.env` file in the project root
- Add the following keys:
   ```env
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here  # For AI assistant features
   ```
- Note: The app will function without the OpenAI API key but will use simulated AI responses instead of the full AI capabilities.

---

## 🚀 Running the App
```bash
streamlit run 1_🏠_Home.py
```
Then open http://localhost:8501 in your browser.

---

## 📝 Usage

### Home Page
- Enter your starting and destination locations in San Jose
- Select transportation mode, time of day, and weather conditions
- Get an AI-powered safety analysis with personalized recommendations
- View interactive map with safety hotspots and alternate routes

### Crash Data Analysis
- Explore comprehensive visualizations of actual San Jose crash data
- View AI-generated insights about crash patterns and risk factors
- Analyze trends by time, location, and contributing factors
- Access advanced safety analytics customized for San Jose commuters

### Analytics Dashboard
- View city-wide safety metrics and trends
- Explore neighborhood-specific safety profiles
- Understand temporal patterns affecting commute risk
- Track changes in safety conditions over time

---

## 🛠️ Code Structure

### Main Application Files
- `1_🏠_Home.py`  
  Main Streamlit app with route safety analysis, interactive map, and user inputs.
- `pages/2_📊_Analytics_Dashboard.py`  
  Data visualization dashboard with city-wide safety analytics.
- `pages/3_🔍_Crash_Data_Analysis.py`  
  Real crash data analysis with AI-generated insights.

### Core Components
- `enhanced_safety.py`  
  Contains advanced safety scoring algorithms and visualization tools.
- `ai_assistant.py`  
  Implements the natural language processing interface and AI chat capabilities.
- `utils/custom_data_processor.py`  
  Processes and analyzes crash data using statistical methods.

### Data Resources
- `utils/sample_incident_data.csv`  
  Sample incident data for demonstration purposes.
- `utils/crashdata2011-2021.csv`  
  Real San Jose crash data spanning 10 years.

### Configuration
- `.env.example`  
  Template for environment variables configuration.
- `requirements.txt`  
  Lists all Python dependencies.

---

## 🤝 Contributing
- Fork the repository
- Create your feature branch (`git checkout -b feature/YourFeature`)
- Commit your changes (`git commit -m 'Add YourFeature'`)
- Push to the branch (`git push origin feature/YourFeature`)
- Open a Pull Request 🚀

## 🧠 AI & Machine Learning Methods

This application incorporates several advanced AI and machine learning techniques:

### Predictive Modeling
- **Ensemble Learning**: Combines multiple prediction models for more accurate safety scores
- **Gradient Boosting**: Used for feature importance in crash risk factor analysis
- **Logistic Regression**: Implements probabilistic classification of route safety levels

### Data Processing
- **Statistical Pattern Recognition**: Identifies significant patterns in crash data
- **Spatial Clustering**: Detects high-risk areas and accident hotspots
- **Time Series Analysis**: Analyzes temporal patterns in accident occurrence

### Natural Language Processing
- **Contextual Understanding**: Processes natural language queries about route safety
- **Response Generation**: Creates personalized safety recommendations
- **Intent Recognition**: Identifies user safety concerns from conversational input

### Example Code (Safety Prediction)
```python
def calculate_safety_score(route_features, time_features, weather_features):
    # Feature engineering
    combined_features = np.concatenate([route_features, time_features, weather_features])
    
    # Apply ensemble model for prediction
    base_score = ensemble_model.predict(combined_features)
    
    # Apply confidence adjustment
    confidence = ensemble_model.predict_proba(combined_features).max()
    
    # Return final score and confidence level
    return adjusted_score, confidence
```

### Example Code (Risk Hotspot Identification)
```python
def identify_risk_hotspots(latitude, longitude, radius=1.0):
    # Find incidents within radius
    nearby_incidents = spatial_index.query_radius(
        point=(latitude, longitude),
        radius=radius
    )
    
    # Calculate risk factors
    if len(nearby_incidents) > threshold:
        return cluster_incidents(nearby_incidents)
    else:
        return []
```

## 🚀 Deployment

### Current Deployment
- Deployed on Streamlit Cloud: [sjsafecommute.streamlit.app](https://sjsafecommute.streamlit.app/)
- Automatic updates via GitHub integration

### Cloud Architecture
- Streamlit Cloud for web interface hosting
- Data processing optimization for faster analytics
- Session state management for user preferences

### Performance Features
- Data caching for quick response times
- Optimized visualizations for mobile and desktop
- Progressive loading of computationally intensive analyses

## 🤝 Contributing

We welcome contributions from:
- Machine Learning & AI Engineers
- Traffic Safety Experts & Data Scientists
- Urban Planning Specialists
- User Experience Designers
- San Jose Community Safety Advocates

### Development Process
1. Fork the repository
2. Create feature branch (`git checkout -b feature/YourFeature`)
3. Implement changes with appropriate tests
4. Update documentation to reflect new capabilities
5. Submit pull request with detailed description

### Priority Enhancements
- Advanced ML model training with expanded crash data
- Real-time safety alerts integration
- Enhanced mobile responsiveness
- Multi-language support for diverse San Jose community

## License

MIT License - See [LICENSE](LICENSE) for details

## 📊 Data Sources

- **San Jose Crash Data (2011-2021)**: Comprehensive traffic incident records
- **San Jose Department of Transportation**: Road safety infrastructure data
- **California Highway Patrol**: Traffic accident reports and statistics
- **San Jose Open Data Portal**: Geographical and urban planning information

## 🙏 Acknowledgments

- City of San Jose Department of Transportation
- San Jose State University Computer Science Department
- Silicon Valley Traffic Safety Coalition
- Open Source Machine Learning Community

---

<div align="center">
Built with ❤️ and AI for San Jose Community Safety
</div>
