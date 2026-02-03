from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import pytz
import os

app = FastAPI()
telemetry_data = []

# Set timezone to Central US
central_tz = pytz.timezone("US/Central")

# Serve static files (html, js, css) from the 'static' folder
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Receive telemetry POST requests from ESP32
@app.post("/telemetry")
async def receive_telemetry(request: Request):
    data = await request.json()
    now_ct = datetime.now(central_tz)
    data["timestamp"] = now_ct.strftime("%Y-%m-%d %H:%M:%S")

    if "temperature" in data and "humidity" in data and "device_id" in data:
        telemetry_data.append(data)
        # Keep only the last 100 readings to avoid memory issues
        if len(telemetry_data) > 100:
            telemetry_data.pop(0)
        return {"status": "logged"}
    else:
        return {"status": "error", "message": "missing fields"}

# Serve telemetry data as JSON
@app.get("/data")
async def get_data():
    return JSONResponse({
        "timestamps": [d["timestamp"] for d in telemetry_data],
        "device_ids": [d["device_id"] for d in telemetry_data],
        "temperatures": [d["temperature"] for d in telemetry_data],
        "humidities": [d["humidity"] for d in telemetry_data],
    })

# Serve the dashboard HTML
@app.get("/", response_class=HTMLResponse)
async def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)

