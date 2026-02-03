from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

telemetry_data = []
central_tz = pytz.timezone("America/Chicago")

@app.get("/", response_class=JSONResponse)
def status():
    return {"status": "Blackbox online"}

@app.post("/telemetry")
async def receive_telemetry(request: Request):
    data = await request.json()
    now_ct = datetime.now(central_tz)
    data["timestamp"] = now_ct.strftime("%Y-%m-%d %H:%M:%S")
    telemetry_data.append(data)
    if len(telemetry_data) > 50:
        telemetry_data.pop(0)
    return {"status": "logged"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Blackbox Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; background: #f0f2f5; margin: 20px; }
            h1 { text-align: center; color: #333; margin-bottom: 20px; }

            /* Card Styles */
            .card-container { display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }
            .card { background: #fff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 20px 30px; text-align: center; min-width: 150px; }
            .card h2 { margin: 0; font-size: 2rem; }
            .card p { margin: 5px 0 0 0; color: #666; }

            /* Charts */
            canvas { background: #fff; border-radius: 10px; padding: 10px; margin: 10px auto; display: block; }

            /* Table */
            table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; background: #fff; border-radius: 10px; overflow: hidden; }
            th, td { padding: 6px 8px; border-bottom: 1px solid #ddd; text-align: center; }
            th { background: #e8e8e8; }
        </style>
    </head>
    <body>
        <h1>ESP32 Blackbox Dashboard</h1>

        <div class="card-container">
            <div class="card">
                <h2 id="latestTemp">-- °C</h2>
                <p>Temperature</p>
            </div>
            <div class="card">
                <h2 id="latestHum">-- %</h2>
                <p>Humidity</p>
            </div>
        </div>

        <canvas id="tempChart" width="800" height="300"></canvas>
        <canvas id="humChart" width="800" height="300"></canvas>

        <table id="dataTable">
            <thead>
                <tr><th>Time (CST/CDT)</th><th>Device</th><th>Temp (°C)</th><th>Humidity (%)</th></tr>
            </thead>
            <tbody></tbody>
        </table>

        <script>
            async function fetchData() {
                const response = await fetch('/data');
                return await response.json();
            }

            function updateCards(data) {
                if(data.timestamps.length > 0) {
                    const latestIdx = data.timestamps.length - 1;
                    document.getElementById('latestTemp').innerText = data.temperatures[latestIdx].toFixed(1) + ' °C';
                    document.getElementById('latestHum').innerText = data.humidities[latestIdx].toFixed(1) + ' %';
                }
            }

            function updateTable(data) {
                const tbody = document.querySelector("#dataTable tbody");
                tbody.innerHTML = "";
                data.timestamps.slice().reverse().forEach((time, idx) => {
                    const row = `<tr>
                        <td>${time}</td>
                        <td>esp32_blackbox</td>
                        <td>${data.temperatures[idx]}</td>
                        <td>${data.humidities[idx]}</td>
                    </tr>`;
                    tbody.innerHTML += row;
                });
            }

            async function updateCharts(chartTemp, chartHum) {
                const data = await fetchData();

                chartTemp.data.labels = data.timestamps;
                chartTemp.data.datasets[0].data = data.temperatures;
                chartTemp.update();

                chartHum.data.labels = data.timestamps;
                chartHum.data.datasets[0].data = data.humidities;
                chartHum.update();

                updateCards(data);
                updateTable(data);
            }

            const ctxTemp = document.getElementById('tempChart').getContext('2d');
            const ctxHum = document.getElementById('humChart').getContext('2d');

            const chartTemp = new Chart(ctxTemp, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Temperature (°C)', data: [], borderColor: 'red', fill: true, tension: 0.4, backgroundColor: 'rgba(255,0,0,0.1)' }] },
                options: { responsive: true, animation: { duration: 300 }, scales: { x: { display: true }, y: { beginAtZero: false } } }
            });

            const chartHum = new Chart(ctxHum, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Humidity (%)', data: [], borderColor: 'blue', fill: true, tension: 0.4, backgroundColor: 'rgba(0,0,255,0.1)' }] },
                options: { responsive: true, animation: { duration: 300 }, scales: { x: { display: true }, y: { beginAtZero: true } } }
            });

            // Update everything every 5 seconds
            setInterval(() => updateCharts(chartTemp, chartHum), 5000);


