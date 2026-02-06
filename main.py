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

# --- Database Helpers ---
DB_PATH = "telemetry.db"

def get_db():
    """Create a new SQLite connection per request."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize DB
conn = get_db()
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
conn.close()

# Static folder
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Receive Telemetry ---
@app.post("/telemetry")
async def receive_telemetry(request: Request):
    data = await request.json()
    now_ct = datetime.now(central_tz).strftime("%Y-%m-%d %H:%M:%S")

    required = {"device_id", "temperature", "humidity"}
    if not required.issubset(data):
        return {"status": "error", "message": "missing fields"}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO telemetry (device_id, temperature, humidity, timestamp, last_seen)
        VALUES (?, ?, ?, ?, ?)
    """, (data["device_id"], data["temperature"], data["humidity"], now_ct, now_ct))

    conn.commit()
    conn.close()

    return {"status": "logged"}


# --- Serve Telemetry Data ---
@app.get("/data")
async def get_data():
    conn = get_db()
    cursor = conn.cursor()

    # Last 100 readings
    cursor.execute("""
        SELECT device_id, temperature, humidity, timestamp
        FROM telemetry
        ORDER BY id DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    rows = list(rows)[::-1]  # reverse chronological

    # Last seen per device
    cursor.execute("""
        SELECT device_id, MAX(last_seen) AS last_seen
        FROM telemetry
        GROUP BY device_id
    """)
    last_seen_rows = cursor.fetchall()

    conn.close()

    now = datetime.now(central_tz)
    status = {}

    for row in last_seen_rows:
        if row["last_seen"] is None:
            status[row["device_id"]] = "offline"
            continue
        
        last_seen_dt = central_tz.localize(
            datetime.strptime(row["last_seen"], "%Y-%m-%d %H:%M:%S")
        )
        
        delta = now - last_seen_dt
        status[row["device_id"]] = "online" if delta < timedelta(seconds=15) else "offline"

    return JSONResponse({
        "timestamps": [r["timestamp"] for r in rows],
        "device_ids": [r["device_id"] for r in rows],
        "temperatures": [r["temperature"] for r in rows],
        "humidities": [r["humidity"] for r in rows],
        "status": status
    })


# --- Serve Dashboard ---
@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return f.read()
