from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz

app = FastAPI()

# Allow your browser / phone to access
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
    # Generate the page with Chart.js for live graph
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Blackbox Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>ESP32 Blackbox Dashboard</h1>
        <canvas id="tempChart" width="800" height="400"></canvas>
        <canvas id="humChart" width="800" height="400"></canvas>
        <script>
            async function fetchData() {
                const response = await fetch('/data');
                return await response.json();
            }

            async function updateCharts(chartTemp, chartHum) {
                const data = await fetchData();
                chartTemp.data.labels = data.timestamps;
                chartTemp.data.datasets[0].data = data.temperatures;
                chartTemp.update();

                chartHum.data.labels = data.timestamps;
                chartHum.data.datasets[0].data = data.humidities;
                chartHum.update();
            }

            const ctxTemp = document.getElementById('tempChart').getContext('2d');
            const ctxHum = document.getElementById('humChart').getContext('2d');

            const chartTemp = new Chart(ctxTemp, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Temperature (°C)',
                        data: [],
                        borderColor: 'red',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    animation: false,
                    scales: { x: { display: true }, y: { beginAtZero: false } }
                }
            });

            const chartHum = new Chart(ctxHum, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Humidity (%)',
                        data: [],
                        borderColor: 'blue',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    animation: false,
                    scales: { x: { display: true }, y: { beginAtZero: true } }
                }
            });

            // Update charts every 5 seconds
            setInterval(() => updateCharts(chartTemp, chartHum), 5000);
            updateCharts(chartTemp, chartHum);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.get("/data", response_class=JSONResponse)
def get_data():
    # Provide data for Chart.js
    timestamps = [entry['timestamp'] for entry in telemetry_data]
    temperatures = [entry['temperature'] for entry in telemetry_data]
    humidities = [entry['humidity'] for entry in telemetry_data]
    return {"timestamps": timestamps, "temperatures": temperatures, "humidities": humidities}
