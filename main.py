from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz

app = FastAPI()

# Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store telemetry readings
telemetry_data = []

# Central USA timezone
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
    if len(telemetry_data) > 100:  # keep only last 100 readings
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

            /* Cards */
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
                <h2 id="latestTemp1">-- °C</h2>
                <p>ESP32 #1 Temperature</p>
            </div>
            <div class="card">
                <h2 id="latestHum1">-- %</h2>
                <p>ESP32 #1 Humidity</p>
            </div>
            <div class="card">
                <h2 id="latestTemp2">-- °C</h2>
                <p>ESP32 #2 Temperature</p>
            </div>
            <div class="card">
                <h2 id="latestHum2">-- %</h2>
                <p>ESP32 #2 Humidity</p>
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
    
    async function updateCharts(chartTemp, chartHum) {
        const data = await fetchData();
    
        // Filter indices for each device
        const device1 = data.device_ids.map((id, i) => id === "esp32_blackbox_1" ? i : null).filter(i => i !== null);
        const device2 = data.device_ids.map((id, i) => id === "esp32_blackbox_2" ? i : null).filter(i => i !== null);
    
        // Latest readings for cards
        if(device1.length) {
            const last1 = device1[device1.length - 1];
            document.getElementById('latestTemp1').innerText = data.temperatures[last1].toFixed(1) + " °C";
            document.getElementById('latestHum1').innerText = data.humidities[last1].toFixed(1) + " %";
        }
        if(device2.length) {
            const last2 = device2[device2.length - 1];
            document.getElementById('latestTemp2').innerText = data.temperatures[last2].toFixed(1) + " °C";
            document.getElementById('latestHum2').innerText = data.humidities[last2].toFixed(1) + " %";
        }
    
        // Chart data
        chartTemp.data.labels = data.timestamps;
        chartTemp.data.datasets[0].data = device1.length ? device1.map(i => data.temperatures[i]) : [];
        chartTemp.data.datasets[1].data = device2.length ? device2.map(i => data.temperatures[i]) : [];
        chartTemp.update();
    
        chartHum.data.labels = data.timestamps;
        chartHum.data.datasets[0].data = device1.length ? device1.map(i => data.humidities[i]) : [];
        chartHum.data.datasets[1].data = device2.length ? device2.map(i => data.humidities[i]) : [];
        chartHum.update();
    
        // Table (latest 100 readings)
        const tbody = document.querySelector("#dataTable tbody");
        tbody.innerHTML = "";
        data.timestamps.slice().reverse().forEach((time, idx) => {
            const row = `<tr>
                <td>${time}</td>
                <td>${data.device_ids[idx]}</td>
                <td>${data.temperatures[idx]}</td>
                <td>${data.humidities[idx]}</td>
            </tr>`;
            tbody.innerHTML += row;
        });
    }
    
    // Chart setup
    const ctxTemp = document.getElementById('tempChart').getContext('2d');
    const ctxHum = document.getElementById('humChart').getContext('2d');
    
    const chartTemp = new Chart(ctxTemp, {
        type: 'line',
        data: { labels: [], datasets: [
            { label: 'ESP32 #1 Temp', data: [], borderColor: 'red', backgroundColor: 'rgba(255,0,0,0.1)', fill: true, tension: 0.4 },
            { label: 'ESP32 #2 Temp', data: [], borderColor: 'green', backgroundColor: 'rgba(0,255,0,0.1)', fill: true, tension: 0.4 }
        ]},
        options: { responsive: true, animation: { duration: 300 }, scales: { x: { display: true }, y: { beginAtZero: false } } }
    });
    
    const chartHum = new Chart(ctxHum, {
        type: 'line',
        data: { labels: [], datasets: [
            { label: 'ESP32 #1 Hum', data: [], borderColor: 'blue', backgroundColor: 'rgba(0,0,255,0.1)', fill: true, tension: 0.4 },
            { label: 'ESP32 #2 Hum', data: [], borderColor: 'orange', backgroundColor: 'rgba(255,165,0,0.1)', fill: true, tension: 0.4 }
        ]},
        options: { responsive: true, animation: { duration: 300 }, scales: { x: { display: true }, y: { beginAtZero: true } } }
    });
    
    // Update every 5 seconds
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
    device_ids = [entry['device_id'] for entry in telemetry_data]
    return {"timestamps": timestamps, "temperatures": temperatures, "humidities": humidities, "device_ids": device_ids}



