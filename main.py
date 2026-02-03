from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
import pytz

app = FastAPI()
telemetry_data = []

central_tz = pytz.timezone("US/Central")

@app.post("/telemetry")
async def receive_telemetry(data: dict):
    now_ct = datetime.now(central_tz)
    data["timestamp"] = now_ct.strftime("%Y-%m-%d %H:%M:%S")

    if "temperature" in data and "humidity" in data and "device_id" in data:
        telemetry_data.append(data)
        if len(telemetry_data) > 100:  # keep last 100 readings
            telemetry_data.pop(0)
        return {"status": "logged"}
    else:
        return {"status": "error", "message": "missing fields"}

@app.get("/data")
async def get_data():
    return JSONResponse({
        "timestamps": [d["timestamp"] for d in telemetry_data],
        "device_ids": [d["device_id"] for d in telemetry_data],
        "temperatures": [d["temperature"] for d in telemetry_data],
        "humidities": [d["humidity"] for d in telemetry_data],
    })

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Blackbox Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color:#121212; color:#fff; font-family: Arial,sans-serif; }
        h1,h2 { color:#f0f0f0; }
        table { border-collapse: collapse; width: 100%; background-color:#1e1e1e; }
        table th, table td { border:1px solid #333; padding:6px 10px; color:#fff; }
        table th { background-color:#2c2c2c; }
        canvas { background-color:#1e1e1e; }
    </style>
</head>
<body>
<h1>ESP32 Blackbox Dashboard</h1>
<div>
    <h2>Latest Readings</h2>
    <div>ESP32 #1: <span id="latestTemp1">--</span>, Hum: <span id="latestHum1">--</span></div>
    <div>ESP32 #2: <span id="latestTemp2">--</span>, Hum: <span id="latestHum2">--</span></div>
</div>
<canvas id="tempChart" height="100"></canvas>
<canvas id="humChart" height="100"></canvas>
<table border="1" id="dataTable">
<thead>
<tr><th>Time</th><th>Device</th><th>Temp (°C)</th><th>Humidity (%)</th></tr>
</thead>
<tbody></tbody>
</table>
<script>
// JS code here (same as your Chart.js code)
async function fetchData() {
    const response = await fetch('/data');
    return await response.json();
}

async function updateCharts(chartTemp, chartHum) {
    const data = await fetchData();
    const device1 = data.device_ids.map((id,i)=>id==="esp32_blackbox_1"?i:null).filter(i=>i!==null);
    const device2 = data.device_ids.map((id,i)=>id==="esp32_blackbox_2"?i:null).filter(i=>i!==null);

    if(device1.length){
        const last1=device1[device1.length-1];
        document.getElementById('latestTemp1').innerText=data.temperatures[last1].toFixed(1)+" °C";
        document.getElementById('latestHum1').innerText=data.humidities[last1].toFixed(1)+" %";
    }
    if(device2.length){
        const last2=device2[device2.length-1];
        document.getElementById('latestTemp2').innerText=data.temperatures[last2].toFixed(1)+" °C";
        document.getElementById('latestHum2').innerText=data.humidities[last2].toFixed(1)+" %";
    }

    chartTemp.data.labels = data.timestamps;
    chartTemp.data.datasets[0].data = device1.length?device1.map(i=>data.temperatures[i]):[];
    chartTemp.data.datasets[1].data = device2.length?device2.map(i=>data.temperatures[i]):[];
    chartTemp.update();

    chartHum.data.labels = data.timestamps;
    chartHum.data.datasets[0].data = device1.length?device1.map(i=>data.humidities[i]):[];
    chartHum.data.datasets[1].data = device2.length?device2.map(i=>data.humidities[i]):[];
    chartHum.update();

    const tbody = document.querySelector("#dataTable tbody");
    tbody.innerHTML = "";
    data.timestamps.slice().reverse().forEach((time, idx) => {
        tbody.innerHTML += `<tr>
            <td>${time}</td>
            <td>${data.device_ids[idx]}</td>
            <td>${data.temperatures[idx]}</td>
            <td>${data.humidities[idx]}</td>
        </tr>`;
    });
}

const ctxTemp=document.getElementById('tempChart').getContext('2d');
const ctxHum=document.getElementById('humChart').getContext('2d');

const chartTemp=new Chart(ctxTemp,{
    type:'line',
    data:{labels:[],datasets:[
        {label:'ESP32 #1 Temp',data:[],borderColor:'red',backgroundColor:'rgba(255,0,0,0.3)',fill:true,tension:0.4},
        {label:'ESP32 #2 Temp',data:[],borderColor:'lime',backgroundColor:'rgba(0,255,0,0.3)',fill:true,tension:0.4}
    ]},
    options:{responsive:true,animation:{duration:300},scales:{x:{ticks:{color:'#fff'},grid:{color:'#333'}},y:{ticks:{color:'#fff'},grid:{color:'#333'}}}}
});

const chartHum=new Chart(ctxHum,{
    type:'line',
    data:{labels:[],datasets:[
        {label:'ESP32 #1 Hum',data:[],borderColor:'cyan',backgroundColor:'rgba(0,255,255,0.3)',fill:true,tension:0.4},
        {label:'ESP32 #2 Hum',data:[],borderColor:'orange',backgroundColor:'rgba(255,165,0,0.3)',fill:true,tension:0.4}
    ]},
    options:{responsive:true,animation:{duration:300},scales:{x:{ticks:{color:'#fff'},grid:{color:'#333'}},y:{ticks:{color:'#fff'},grid:{color:'#333'}}}}
});

setInterval(()=>updateCharts(chartTemp,chartHum),5000);
updateCharts(chartTemp,chartHum);
</script>
</body>
</html>
"""
