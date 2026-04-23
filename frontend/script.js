const ws = new WebSocket('ws://localhost:8000/ws');
const statusEl = document.getElementById('status');
const valAngle = document.getElementById('val-angle');
const valDist = document.getElementById('val-distance');
const valConf = document.getElementById('val-confidence');
const valLabel = document.getElementById('val-label');

const imgRaw = document.getElementById('video-raw');
const imgEdge = document.getElementById('video-edge');
const imgSpec = document.getElementById('video-spec');

// --- CHARTS ---
const radarCtx = document.getElementById('radarChart').getContext('2d');
const fftCtx = document.getElementById('fftChart').getContext('2d');

const radarChart = new Chart(radarCtx, {
    type: 'radar',
    data: {
        labels: Array.from({length: 37}, (_, i) => i * 5),
        datasets: [{
            label: 'Distance (cm)',
            data: new Array(37).fill(0),
            backgroundColor: 'rgba(88, 166, 255, 0.2)',
            borderColor: '#58a6ff',
            pointRadius: 0
        }]
    },
    options: {
        scales: { r: { min: 0, max: 200, ticks: { display: false } } },
        plugins: { legend: { display: false } },
        animation: false
    }
});

const fftChart = new Chart(fftCtx, {
    type: 'line',
    data: {
        labels: Array.from({length: 16}, (_, i) => i),
        datasets: [{
            label: 'Amplitude',
            data: new Array(16).fill(0),
            borderColor: '#3fb950',
            borderWidth: 2,
            pointRadius: 0,
            fill: true,
            backgroundColor: 'rgba(63, 185, 80, 0.1)'
        }]
    },
    options: {
        scales: { y: { beginAtZero: true }, x: { display: false } },
        plugins: { legend: { display: false } },
        animation: false
    }
});

ws.onopen = () => {
    statusEl.innerText = 'ONLINE';
    statusEl.className = 'status online';
};

ws.onclose = () => {
    statusEl.innerText = 'OFFLINE';
    statusEl.className = 'status offline';
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Update Telemetry
    valAngle.innerText = `${data.telemetry.angle}°`;
    valDist.innerText = `${data.telemetry.distance} cm`;
    valConf.innerText = `${Math.round(data.telemetry.confidence * 100)}%`;
    valLabel.innerText = data.telemetry.label ? data.telemetry.label.toUpperCase() : "NONE";
    
    // Update Images
    imgRaw.src = `data:image/jpeg;base64,${data.images.original}`;
    imgEdge.src = `data:image/jpeg;base64,${data.images.edges}`;
    imgSpec.src = `data:image/jpeg;base64,${data.images.spectrum}`;
    
    // Update Radar Chart
    const idx = Math.floor(data.telemetry.angle / 5);
    radarChart.data.datasets[0].data[idx] = data.telemetry.distance;
    radarChart.update();
    
    // Update FFT Chart
    if (data.telemetry.signal_fft.length > 0) {
        fftChart.data.datasets[0].data = data.telemetry.signal_fft;
        fftChart.update();
    }
};
