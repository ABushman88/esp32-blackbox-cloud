from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import pytz

app = FastAPI()
telemetry_data = []

central_tz = pytz.timezone("US/Central")

# Serve static files (html, js, css)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/telemetry")
async def receive_telemetry(request: Request):
    data = await request.json()
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
    with open("static/index.html") as f:
        return f.read()
