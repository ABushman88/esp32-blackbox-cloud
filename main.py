from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
import pytz
import os
import sqlite3

app = FastAPI()

# Timezone
central_tz = pytz.timezone("US/Central")

# Database
conn = sqlite3.connect("telemetry.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    temperature REAL,
    humidity REAL,
    timestamp TEXT,
    last_seen TEXT
)
""")
conn.commit()

# Static folder
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Receive telemetry
@app.post("/telemetry")
async def receive_telemetry(request: Request):
    data = await request.json()
    now_ct = datetime.now(central_tz).strftime("%Y-%m-%d %H:%M:%S")

    if "temperature" in data and "humidity" in data and "device_id" in data:
        cursor.execute(
            "INSERT INTO telemetry (device_id, temperature, humidity, timestamp, last_seen) VALUES (?, ?, ?, ?, ?)",
            (data["device_id"], data["temperature"], data["humidity"], now_ct, now_ct)
        )
        conn.commit()
        return {"status": "logged"}
    else:
        return {"status": "error", "message": "missing fields"}

# Serve telemetry
@app.get("/data")
async def get_data():
    cursor.execute("""
        SELECT device_id, temperature, humidity, timestamp
        FROM telemetry
        ORDER BY id DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    rows.reverse()

    # Last seen per device
    cursor.execute("""
        SELECT device_id, MAX(last_seen)
        FROM telemetry
        GROUP BY device_id
    """)
    last_seen_rows = cursor.fetchall()

    now = datetime.now(central_tz)
    status = {}

    for device, last_seen in last_seen_rows:
        last_seen_dt = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S")
        delta = now - last_seen_dt
        status[device] = "online" if delta < timedelta(seconds=15) else "offline"

    return JSONResponse({
        "timestamps": [r[3] for r in rows],
        "device_ids": [r[0] for r in rows],
        "temperatures": [r[1] for r in rows],
        "humidities": [r[2] for r in rows],
        "status": status
    })

# Serve dashboard
@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return f.read()

