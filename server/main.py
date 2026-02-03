from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI()

class Telemetry(BaseModel):
    device_id: str
    temperature: float
    humidity: float

@app.get("/")
def root():
    return {"status": "Blackbox online"}

@app.post("/telemetry")
def receive_data(data: Telemetry):
    print("DATA:", data)
    return {"status": "logged", "timestamp": time.time()}
