import json
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from app import load_data, aggregate_by_state_and_site, train_model, predict_deaths, STATE_NAME_TO_ABBR

app = Flask(__name__, template_folder='templates', static_folder='static')

RAW_DATA = None
AGGREGATED = None
MODEL = None
STATE_ENCODER = None
SITE_ENCODER = None
METRICS = None


def init_data():
    global RAW_DATA, AGGREGATED, MODEL, STATE_ENCODER, SITE_ENCODER, METRICS
    csv_path = Path(__file__).parent / 'United States and Puerto Rico Cancer Statistics, 1999-2021 Mortality.csv'
    RAW_DATA = load_data(csv_path)
    AGGREGATED = aggregate_by_state_and_site(RAW_DATA)
    MODEL, STATE_ENCODER, SITE_ENCODER, r2, mae, rmse = train_model(AGGREGATED)
    METRICS = {'r2': r2, 'mae': mae, 'rmse': rmse}


@app.before_request
def ensure_data():
    if RAW_DATA is None:
        init_data()


@app.route('/')
def index():
    sites = sorted({row['Leading Cancer Site'] for row in AGGREGATED})
    return render_template('dashboard.html', sites=json.dumps(sites))


@app.route('/api/map-data', methods=['POST'])
def get_map_data():
    selected_site = request.json.get('site')
    filtered = [row for row in AGGREGATED if row['Leading Cancer Site'] == selected_site and row['State Abbrev']]
    data = [{'state': row['State'], 'abbr': row['State Abbrev'], 'deaths': row['Total Deaths']} for row in filtered]
    return jsonify({'data': data, 'metrics': METRICS})


@app.route('/api/predict', methods=['POST'])
def make_prediction():
    state = request.json.get('state')
    site = request.json.get('site')
    predicted = predict_deaths(MODEL, state, site, STATE_ENCODER, SITE_ENCODER)
    actual = next(
        (row['Total Deaths'] for row in AGGREGATED
         if row['State'] == state and row['Leading Cancer Site'] == site),
        None,
    )
    return jsonify({'predicted': predicted, 'actual': actual})


@app.route('/api/sites', methods=['GET'])
def get_sites():
    sites = sorted({row['Leading Cancer Site'] for row in AGGREGATED})
    return jsonify({'sites': sites})


@app.route('/api/dataset-stats', methods=['GET'])
def get_dataset_stats():
    return jsonify({
        'total_rows': len(RAW_DATA),
        'state_site_pairs': len(AGGREGATED),
        'unique_sites': len({row['Leading Cancer Site'] for row in AGGREGATED}),
    })


if __name__ == '__main__':
    init_data()
    app.run(debug=True, port=5000)
