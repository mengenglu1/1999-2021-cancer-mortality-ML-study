# Cancer Mortality Prediction Portfolio

## Project overview
This portfolio project uses the uploaded `United States and Puerto Rico Cancer Statistics, 1999-2021 Mortality.csv` dataset to build a practical machine learning application for predicting cancer mortality by state and by leading cancer site.

The user-facing app is built with Streamlit and includes:
- an interactive U.S. heat map that responds to state clicks and colors states by relative cancer mortality
- a top menu for choosing a leading cancer site
- model predictions of total cancer deaths for the selected state/site combination
- a dataset and model summary designed to showcase data science skills to employers

## Key skills demonstrated
- Data cleaning and preprocessing from raw CSV input
- Feature engineering and regression modeling with scikit-learn
- Interactive visualization with Plotly and Streamlit
- Business-oriented storytelling and dashboard design for hiring managers

## What this app does
1. Loads the mortality dataset and aggregates total deaths by state and leading cancer site.
2. Trains a Random Forest regression model to estimate total cancer deaths per combination.
3. Displays an interactive U.S. map where clicking a state retrieves a prediction.
4. Shows real values and model performance metrics for transparency and interpretability.

## Run the app

### Option 1: Streamlit (Recommended for quick testing)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```
3. Open the local URL shown by Streamlit in your browser (typically `http://localhost:8501`).

### Option 2: Flask + HTML (Better interactivity and visual responsiveness)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the Flask app:
   ```bash
   python app_flask.py
   ```
3. Open your browser to `http://localhost:5000`.
   - This version provides smoother interactions and better visual updates.
   - Click states on the map to see predictions update in real-time.

## Features

### Streamlit version (`app.py`)
- Interactive Plotly choropleth map with heat gradient coloring
- Cancer site selector at the top
- Real-time predictions when states are clicked
- Model performance metrics displayed
- Desktop and mobile responsive

### Flask version (`app_flask.py`)
- Clean, modern HTML/CSS dashboard with a professional design
- More responsive state click detection
- Interactive state-by-state predictions
- Manual state selector as backup
- Real-time data fetching via REST API

## Project structure
```
.
├── app.py                           # Streamlit application
├── app_flask.py                     # Flask application
├── templates/
│   └── dashboard.html              # Flask HTML template
├── static/
│   ├── style.css                   # Dashboard styling
│   └── script.js                   # Interactive map logic
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── United States and Puerto Rico Cancer Statistics, 1999-2021 Mortality.csv
```

