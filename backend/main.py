from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.mavsdk_client import MAVSDKClient

app = FastAPI()
# ✅ Enable CORS for the frontend port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MAVSDKClient()

@app.post("/connect")
async def connect():
    await client.connect()
    return {"status": "connected"}

@app.post("/arm")
async def arm():
    await client.arm()
    return {"status": "armed"}

@app.post("/takeoff")
async def takeoff():
    await client.takeoff()
    return {"status": "takeoff initiated"}

@app.post("/land")
async def land():
    await client.land()
    return {"status": "landing"}
