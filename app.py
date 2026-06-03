import csv
from pathlib import Path

import plotly.express as px
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from streamlit_plotly_events import plotly_events

STATE_NAME_TO_ABBR = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI',
    'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME',
    'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
    'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
    'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI',
    'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',
    'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
    'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}

DATA_FILE = Path(__file__).parent / 'United States and Puerto Rico Cancer Statistics, 1999-2021 Mortality.csv'


def normalize(value: str) -> str:
    if value is None:
        return ''
    return value.strip().strip("'").strip()


def load_data(source_path):
    data = []
    with open(source_path, encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 8:
                continue
            note, site, site_code, state, state_code, age_group, age_code, deaths = (
                normalize(row[0]), normalize(row[1]), normalize(row[2]), normalize(row[3]),
                normalize(row[4]), normalize(row[5]), normalize(row[6]), normalize(row[7])
            )
            if not state or not site or not deaths:
                continue
            try:
                death_count = int(deaths.replace(',', ''))
            except ValueError:
                continue
            state_abbrev = STATE_NAME_TO_ABBR.get(state, '')
            data.append({
                'site': site,
                'site_code': site_code,
                'state': state,
                'state_code': state_code,
                'state_abbrev': state_abbrev,
                'age_group': age_group,
                'age_group_code': age_code,
                'deaths': death_count,
                'notes': note,
            })
    return data


def aggregate_by_state_and_site(rows):
    totals = {}
    for row in rows:
        key = (row['state'], row['site'])
        totals[key] = totals.get(key, 0) + row['deaths']
    aggregated = []
    for (state, site), total in totals.items():
        aggregated.append({
            'State': state,
            'State Abbrev': STATE_NAME_TO_ABBR.get(state, ''),
            'Leading Cancer Site': site,
            'Total Deaths': total,
        })
    return aggregated


def train_model(aggregated):
    unique_states = sorted({row['State'] for row in aggregated})
    unique_sites = sorted({row['Leading Cancer Site'] for row in aggregated})
    state_encoder = {state: i for i, state in enumerate(unique_states)}
    site_encoder = {site: i for i, site in enumerate(unique_sites)}

    X = [[state_encoder[row['State']], site_encoder[row['Leading Cancer Site']]] for row in aggregated]
    y = [row['Total Deaths'] for row in aggregated]

    model = RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)
    model.fit(X, y)

    predictions = model.predict(X)
    r2 = model.score(X, y)
    mae = mean_absolute_error(y, predictions)
    mse = mean_squared_error(y, predictions)
    rmse = mse ** 0.5

    return model, state_encoder, site_encoder, r2, mae, rmse


def predict_deaths(model, state, site, state_encoder, site_encoder):
    if state not in state_encoder or site not in site_encoder:
        return None
    features = [[state_encoder[state], site_encoder[site]]]
    return int(round(model.predict(features)[0]))


def build_choropleth(filtered, selected_site):
    if not filtered:
        return None
    fig = px.choropleth(
        filtered,
        locations='State Abbrev',
        locationmode='USA-states',
        color='Total Deaths',
        hover_name='State',
        hover_data={'State Abbrev': False, 'Total Deaths': True},
        custom_data=['State', 'State Abbrev'],
        color_continuous_scale='YlOrRd',
        scope='usa',
        labels={'Total Deaths': 'Total Deaths'},
    )
    fig.update_traces(marker_line_color='white', marker_line_width=0.5, hovertemplate='<b>%{customdata[0]}</b><br>Total Deaths: %{z}<extra></extra>')
    fig.update_layout(
        margin={'r': 0, 't': 30, 'l': 0, 'b': 0},
        clickmode='event+select',
        title=f'Predicted cancer mortality totals by state for {selected_site}',
    )
    return fig


def main():
    st.set_page_config(page_title='Cancer Mortality Predictor', layout='wide')
    st.title('Cancer Mortality Forecasting Dashboard')
    st.write(
        'Explore the 1999–2021 cancer mortality dataset with an interactive U.S. map. '
        'Select a leading cancer site, click a state, and view model-based predictions of total deaths for that state and cancer type.'
    )

    raw_rows = load_data(DATA_FILE)
    aggregated = aggregate_by_state_and_site(raw_rows)
    model, state_encoder, site_encoder, r2, mae, rmse = train_model(aggregated)

    available_sites = sorted({row['Leading Cancer Site'] for row in aggregated})
    selected_site = st.selectbox('Select the leading cancer site', available_sites)

    top_metrics, _, model_metrics = st.columns([2, 1, 2])
    top_metrics.metric('Dataset rows', len(raw_rows))
    top_metrics.metric('State-site pairs', len(aggregated))
    model_metrics.metric('Model R² (training)', f'{r2:.3f}')
    model_metrics.metric('Mean Absolute Error', f'{mae:.0f}')
    model_metrics.metric('RMSE', f'{rmse:.0f}')

    st.markdown('---')
    map_col, info_col = st.columns([3, 1])

    current_site_rows = [row for row in aggregated if row['Leading Cancer Site'] == selected_site and row['State Abbrev']]

    if not current_site_rows:
        st.warning('No data available for this cancer site.')
        return

    with map_col:
        st.subheader('Interactive U.S. cancer mortality map')
        choropleth_fig = build_choropleth(current_site_rows, selected_site)
        if choropleth_fig is None:
            st.warning('No geographic map data available for this selection.')
        else:
            clicked = plotly_events(choropleth_fig, click_event=True, override_height=650, key='choropleth_map')
            selected_state = None
            if clicked and isinstance(clicked, list) and len(clicked) > 0:
                point_data = clicked[0]
                if isinstance(point_data, dict):
                    if 'location' in point_data and point_data['location']:
                        selected_state = next(
                            (row['State'] for row in current_site_rows if row['State Abbrev'] == point_data['location']),
                            None,
                        )
                    elif 'customdata' in point_data and point_data['customdata']:
                        custom = point_data['customdata']
                        if isinstance(custom, (list, tuple)) and len(custom) >= 1:
                            selected_state = custom[0]
                    elif 'points' in point_data and isinstance(point_data['points'], list) and point_data['points']:
                        subpoint = point_data['points'][0]
                        if isinstance(subpoint, dict):
                            if 'location' in subpoint and subpoint['location']:
                                selected_state = next(
                                    (row['State'] for row in current_site_rows if row['State Abbrev'] == subpoint['location']),
                                    None,
                                )
                            elif 'customdata' in subpoint and subpoint['customdata']:
                                custom = subpoint['customdata']
                                if isinstance(custom, (list, tuple)) and len(custom) >= 1:
                                    selected_state = custom[0]
                            elif 'pointNumber' in subpoint:
                                point_index = subpoint.get('pointNumber')
                                if isinstance(point_index, int) and 0 <= point_index < len(current_site_rows):
                                    selected_state = current_site_rows[point_index]['State']
                    elif 'pointNumber' in point_data:
                        point_index = point_data.get('pointNumber')
                        if isinstance(point_index, int) and 0 <= point_index < len(current_site_rows):
                            selected_state = current_site_rows[point_index]['State']

            state_selector = st.selectbox('Or choose a state manually',
                                          [''] + sorted({row['State'] for row in aggregated}), index=0)
            if state_selector and not selected_state:
                selected_state = state_selector

    with info_col:
        if selected_state:
            predicted_value = predict_deaths(model, selected_state, selected_site, state_encoder, site_encoder)
            actual_value = next(
                (row['Total Deaths'] for row in aggregated
                 if row['State'] == selected_state and row['Leading Cancer Site'] == selected_site),
                None,
            )
            st.markdown('---')
            st.subheader('✓ Prediction Results')
            st.metric('State', selected_state)
            if predicted_value is not None:
                st.metric('Predicted deaths', f'{predicted_value:,}')
            if actual_value is not None:
                st.metric('Actual aggregated deaths', f'{actual_value:,}')
        else:
            st.info('👉 Click a state on the map or select one from the dropdown to view a prediction.')


if __name__ == '__main__':
    main()