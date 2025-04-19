<div align="center">

# 🚗 San Jose Safe Commute | Route Planner

An AI‑powered Streamlit app to help San Jose commuters plan safer routes by combining Google Maps autocomplete, Folium maps, and a simple risk‑scoring model based on time of day and historical data.

---

## 🔍 Features

- **Autocomplete Inputs**  
  Suggests “San Jose, CA”–focused start & end locations via Google Maps Places Autocomplete.
- **Interactive Route Map**  
  Displays origin & destination markers, draws the route, and auto‑fits bounds.
- **Safety Scoring**  
  Calculates a 1–10 “Route Safety Score” based on time‑of‑day risk factors (late night, rush hour, etc.) and random variability (placeholder for a real ML model).
- **Contextual Warnings & Tips**  
  Shows tailored messages & precautionary recommendations by score tier.
- **Historical Hotspot Table**  
  Presents sample accident‑hotspot data for San Jose.
- **Feedback Form**  
  Collect user suggestions via a simple Streamlit form.

---

## 📦 Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/your‑username/san‑jose‑safe‑commute.git
   cd san‑jose‑safe‑commute
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

### ⚙️ Setup Google Maps API Key

- Create a `.env` file in the project root
- Add your key:
   ```env
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```
- Other Environment Variables: (No other secrets required for this prototype.)

---

## 🚀 Running the App
```bash
streamlit run app.py
```
Then open http://localhost:8501 in your browser.

---

## 📝 Usage
- Enter your starting location and destination in the sidebar (autocomplete suggestions will appear).
- Click “Calculate Route Safety” to:
  - Compute and display current time (PST) and safety score.
  - Show contextual warnings (late night, rush hour, etc.).
  - Get actionable recommendations based on the score.
  - View the interactive Folium map and the historical hotspots table.
  - Submit feedback via the form at the bottom.

---

## 🛠️ Code Structure
- `app.py`  
  Main Streamlit app including layout, inputs, session state, and map rendering.
- `risk_model.py` (placeholder)  
  Contains `basic_predict_risk()` for computing a mock risk score.
- `requirements.txt`  
  Lists all Python dependencies.

---

## 🤝 Contributing
- Fork the repository
- Create your feature branch (`git checkout -b feature/YourFeature`)
- Commit your changes (`git commit -m 'Add YourFeature'`)
- Push to the branch (`git push origin feature/YourFeature`)
- Open a Pull Request 🚀

## Installation

```bash
# Clone the repository
git clone https://github.com/Samirrahman71/SJCAPP.git
cd SJCAPP

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your API keys to .env

# Launch application
streamlit run 1_🏠_Home.py
```

## Usage

### Risk Assessment
```python
# Example risk calculation
risk_score = model.predict_proba(features)[[0, 1]]
```

### Route Planning
```python
# Generate safe route
safe_route = route_optimizer.find_safest_path(
    origin=start_point,
    destination=end_point,
    time=current_time
)
```

## Deployment

### Cloud Deployment
- Streamlit Cloud for web interface
- Docker containerization available
- CI/CD pipeline integration

### Performance Optimization
- Caching for frequent calculations
- Async processing for real-time updates
- Load balancing for scale

## Contributing

We welcome contributions from:
- ML Engineers
- Traffic Safety Experts
- Urban Planning Specialists
- Community Safety Advocates

### Development Process
1. Fork the repository
2. Create feature branch
3. Implement changes
4. Submit pull request

## License

MIT License - See [LICENSE](LICENSE) for details

## Acknowledgments

- City of San Jose Open Data Portal
- San Jose Department of Transportation
- Community Safety Partners

---

<div align="center">
Built with ❤️ for San Jose Community Safety
</div>
