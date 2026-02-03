from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

# Allow your browser / phone to access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store telemetry in memory (list of dicts)
telemetry_data = []

@app.get("/", response_class=JSONResponse)
def status():
    return {"status": "Blackbox online"}

@app.post("/telemetry")
async def receive_telemetry(request: Request):
    data = await request.json()
    # Add timestamp
    data["timestamp"] = datetime.now().isoformat()
    telemetry_data.append(data)
    # Keep only last 50 readings to avoid memory bloat
    if len(telemetry_data) > 50:
        telemetry_data.pop(0)
    return {"status": "logged"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = "<h1>ESP32 Blackbox Dashboard</h1>"
    html += "<table border='1' cellpadding='5'><tr><th>Time</th><th>Device</th><th>Temperature (°C)</th><th>Humidity (%)</th></tr>"
    for entry in reversed(telemetry_data):
        html += f"<tr><td>{entry['timestamp']}</td><td>{entry['device_id']}</td><td>{entry['temperature']}</td><td>{entry['humidity']}</td></tr>"
    html += "</table>"
    return html
