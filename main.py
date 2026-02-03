from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import pytz
import os
import sqlite3

app = FastAPI()

# ----------------------------
# Database setup
# ----------------------------
DB_PATH = "telemetry.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    temperature REAL,
    humidity REAL,
    timestamp TEXT
)
""")

conn.commit()

# ----------------------------
# Timezone
# ----------------------------
central_tz = pytz.timezone("US/Central")

# ----------------------------
# Static files
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ----------------------------
# Telemetry ingestion
# ----------------------------
@app.post("/telemetry")
async def receive_telemetry(request: Request):
    data = await request.json()
    now_ct = datetime.now(central_tz).strftime("%Y-%m-%d %H:%M:%S")

    if "temperature" in data and "humidity" in data and "device_id" in data:
        cursor.execute(
            "INSERT INTO telemetry (device_id, temperature, humidity, timestamp) VALUES (?, ?, ?, ?)",
            (data["device_id"], data["temperature"], data["humidity"], now_ct)
        )
        conn.commit()
        return {"status": "logged"}
    else:
        return {"status": "error", "message": "missing fields"}

# ----------------------------
# Dashboard data
# ----------------------------
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

    return JSONResponse({
        "timestamps": [r[3] for r in rows],
        "device_ids": [r[0] for r in rows],
        "temperatures": [r[1] for r in rows],
        "humidities": [r[2] for r in rows],
    })

# ----------------------------
# Serve dashboard
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "<h1>Dashboard not found</h1>"
