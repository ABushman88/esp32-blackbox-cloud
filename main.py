from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz

app = FastAPI()

# CORS
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
            body { font-family: Arial, sans-serif; background: #f4f4f9; margin: 20px; }
            h1 { text-align: center; color: #333; }
            canvas { background: #fff; border: 1px solid #ccc; border-radius: 8px; margin: 10px auto; display: block; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }
            th, td { padding: 6px 8px; border: 1px solid #ccc; text-align: center; }
            th { background: #e2e2e2; }
        </style>
    </head>
    <body>
        <h1>ESP32 Blackbox Dashboard</h1>
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
                const labels = data.timestamps;
                chartTemp.data.labels = labels;
                chartTemp.data.datasets[0].data = data.temperatures;
                chartTemp.update();

                chartHum.data.labels = labels;
                chartHum.data.datasets[0].data = data.humidities;
                chartHum.update();

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

            setInterval(() => updateCharts(chartTemp, chartHum), 5000);
            updateCharts(chartTemp, chartHum);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.get("/data", response_class=JSONResponse)
def get_data():
    timestamps = [entry['timestamp'] for entry in telemetry_data]
    temperatures = [entry['temperature'] for entry in telemetry_data]
    humidities = [entry['humidity'] for entry in telemetry_data]
    return {"timestamps": timestamps, "temperatures": temperatures, "humidities": humidities}

