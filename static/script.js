let currentSite = null;
let selectedState = null;
let mapData = null;

async function init() {
    try {
        const [sitesRes, statsRes] = await Promise.all([
            fetch('/api/sites').then(r => r.json()),
            fetch('/api/dataset-stats').then(r => r.json())
        ]);

        populateSiteSelect(sitesRes.sites);
        updateMetrics(statsRes);
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

function populateSiteSelect(sites) {
    const select = document.getElementById('cancer-site-select');
    select.innerHTML = '';
    sites.forEach(site => {
        const option = document.createElement('option');
        option.value = site;
        option.textContent = site;
        select.appendChild(option);
    });
    if (sites.length > 0) {
        select.value = sites[0];
        currentSite = sites[0];
        updateMap();
    }
}

function populateStateSelect(states) {
    const select = document.getElementById('state-select');
    const currentValue = select.value;
    select.innerHTML = '<option value="">Select a state...</option>';
    states.forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        select.appendChild(option);
    });
    if (currentValue) {
        select.value = currentValue;
    }
}

function updateMetrics(stats) {
    document.getElementById('metric-rows').textContent = stats.total_rows.toLocaleString();
    document.getElementById('metric-pairs').textContent = stats.state_site_pairs.toLocaleString();
}

async function updateMap() {
    const site = document.getElementById('cancer-site-select').value;
    currentSite = site;
    selectedState = null;
    document.getElementById('state-select').value = '';

    try {
        const response = await fetch('/api/map-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ site })
        });
        const result = await response.json();

        mapData = result.data;
        updateMetricsFromResult(result.metrics);
        renderChoropleth(result.data, site);
        populateStateSelect(result.data.map(d => d.state));
        hidePredictionPanel();
    } catch (error) {
        console.error('Error updating map:', error);
    }
}

function updateMetricsFromResult(metrics) {
    document.getElementById('metric-r2').textContent = metrics.r2.toFixed(3);
    document.getElementById('metric-mae').textContent = Math.round(metrics.mae).toLocaleString();
}

function renderChoropleth(data, site) {
    const sortedData = [...data].sort((a, b) => a.deaths - b.deaths);
    const maxDeaths = Math.max(...data.map(d => d.deaths));
    const minDeaths = Math.min(...data.map(d => d.deaths));

    const trace = {
        type: 'choropleth',
        locations: data.map(d => d.abbr),
        z: data.map(d => d.deaths),
        locationmode: 'USA-states',
        colorscale: 'YlOrRd',
        text: data.map(d => `${d.state}: ${d.deaths.toLocaleString()}`),
        hovertemplate: '<b>%{text}</b><extra></extra>',
        marker: { line: { color: 'white', width: 0.5 } },
    };

    const layout = {
        title: {
            text: `Predicted cancer mortality totals by state for ${site}`,
            font: { size: 14 }
        },
        geo: {
            scope: 'usa',
            projection: { type: 'albers usa' },
            showland: true,
            landcolor: '#f0f0f0'
        },
        margin: { l: 0, r: 0, t: 40, b: 0 },
        height: 500,
    };

    const mapElement = document.getElementById('choropleth-map');
    Plotly.newPlot(mapElement, [trace], layout, { responsive: true });
    mapElement.on('plotly_click', handleMapClick);
}

function handleMapClick(data) {
    if (data.points && data.points.length > 0) {
        const location = data.points[0].location;
        const state = mapData.find(d => d.abbr === location)?.state;
        if (state) {
            selectedState = state;
            document.getElementById('state-select').value = state;
            showPrediction(state);
        }
    }
}

function handleStateSelect() {
    const state = document.getElementById('state-select').value;
    if (state) {
        selectedState = state;
        showPrediction(state);
    } else {
        selectedState = null;
        hidePredictionPanel();
    }
}

async function showPrediction(state) {
    if (!currentSite || !state) return;

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state, site: currentSite })
        });
        const result = await response.json();

        document.getElementById('result-state').textContent = state;
        document.getElementById('result-site').textContent = currentSite;
        document.getElementById('result-predicted').textContent = 
            result.predicted !== null ? result.predicted.toLocaleString() : '—';
        document.getElementById('result-actual').textContent = 
            result.actual !== null ? result.actual.toLocaleString() : '—';

        document.getElementById('prediction-panel').style.display = 'block';
        document.getElementById('info-panel').style.display = 'none';
    } catch (error) {
        console.error('Error making prediction:', error);
    }
}

function hidePredictionPanel() {
    document.getElementById('prediction-panel').style.display = 'none';
    document.getElementById('info-panel').style.display = 'block';
}

document.addEventListener('DOMContentLoaded', init);
