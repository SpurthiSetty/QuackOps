# QuackOps — Drone Control & GPS Tracking

Autonomous drone delivery system for Stevens campus. Combines AI vision, MAVLink navigation, and a real-time web dashboard.

## Table of contents
- [Project structure](#project-structure)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [How to run](#how-to-run)
  - [1. PX4 simulator (Docker)](#1-px4-simulator-docker)
  - [2. Backend (FastAPI + MAVSDK)](#2-backend-fastapi--mavsdk)
  - [3. Frontend (Node.js)](#3-frontend-nodejs)
- [API endpoints](#api-endpoints)
- [What you'll see](#what-youll-see)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)

## Project structure
```
QuackOps/
├── frontend/        # Node.js + Express + Socket.IO + Leaflet UI
│   ├── app.js
│   └── public/
│       └── index.html
├── backend/         # FastAPI + MAVSDK service
│   ├── main.py
│   ├── services/
│   │   └── mavsdk_client.py
│   └── requirements.txt
└── README.md
```

## System Architecture

### Overview
QuackOps is a multi-layer autonomous drone system that separates concerns across three main components:

```
┌─────────────────────────────────────────────────────────┐
│  Browser UI (Port 3001)                                  │
│  • Leaflet map with real-time GPS tracking              │
│  • Drone control buttons (Connect, Arm, Takeoff, Land)  │
│  • WebSocket client for live telemetry                  │
└─────────────────────────────────────────────────────────┘
         ↓ HTTP POST                    ↑ WebSocket
         ↓ (drone commands)             ↑ (GPS updates)
┌─────────────────────────────────────────────────────────┐
│  Frontend Server (Node.js + Express - Port 3001)        │
│  • Serves static HTML/JS/CSS files                      │
│  • Socket.IO server for real-time communication         │
│  • UDP listener (port 11123) for GPS2IP NMEA data       │
│  • Parses NMEA sentences → broadcasts to browsers       │
└─────────────────────────────────────────────────────────┘
         ↓ HTTP POST (CORS-enabled)
┌─────────────────────────────────────────────────────────┐
│  Backend API (FastAPI + MAVSDK - Port 8000)             │
│  • REST endpoints for drone commands                    │
│  • MAVSDK Python client (async)                         │
│  • Translates HTTP requests → MAVLink protocol          │
└─────────────────────────────────────────────────────────┘
         ↓ MAVLink over UDP (port 14540)
┌─────────────────────────────────────────────────────────┐
│  PX4 Flight Controller (Docker)                         │
│  • Gazebo-based physics simulation                      │
│  • Autopilot firmware (ArduPilot/PX4)                   │
│  • Broadcasts telemetry via MAVLink                     │
└─────────────────────────────────────────────────────────┘
```

---

### How the Backend Works with MAVSDK

#### 1. **MAVSDK Overview**
MAVSDK is a high-level API that abstracts the MAVLink protocol (the communication standard for drones). Instead of manually crafting low-level MAVLink messages, MAVSDK provides simple Python methods like `arm()`, `takeoff()`, and `land()`.

**Key Components:**
- **MAVLink Protocol**: Binary messaging protocol used by most autopilots (PX4, ArduPilot)
- **MAVSDK Library**: Python wrapper that handles MAVLink encoding/decoding
- **System Object**: Represents a connected drone/vehicle

#### 2. **Backend Architecture**

**File: `backend/main.py`**
```python
from fastapi import FastAPI
from services.mavsdk_client import MAVSDKClient

app = FastAPI()
client = MAVSDKClient()  # Single drone instance

@app.post("/connect")
async def connect():
    await client.connect()  # Establishes MAVLink connection
    return {"status": "connected"}

@app.post("/arm")
async def arm():
    await client.arm()  # Sends MAVLink ARM command
    return {"status": "armed"}
```

**File: `backend/services/mavsdk_client.py`**
```python
from mavsdk import System

class MAVSDKClient:
    def __init__(self):
        self.drone = System()  # Creates drone instance

    async def connect(self):
        # Connects to PX4 via UDP on port 14540
        await self.drone.connect(system_address="udp://:14540")

    async def arm(self):
        # Sends MAVLink COMMAND_LONG(400) - ARM/DISARM
        await self.drone.action.arm()

    async def takeoff(self):
        # Sends MAVLink COMMAND_LONG(22) - TAKEOFF
        await self.drone.action.takeoff()
```

#### 3. **MAVLink Communication Flow**

**Example: Takeoff Command**

1. **User clicks "Takeoff" button** in browser
2. **Frontend sends HTTP POST**:
   ```javascript
   fetch('http://localhost:8000/takeoff', { method: 'POST' })
   ```

3. **Backend receives request** → calls `client.takeoff()`

4. **MAVSDK translates to MAVLink**:
   ```
   MAVLink Message:
   - Message ID: COMMAND_LONG (76)
   - Command: MAV_CMD_NAV_TAKEOFF (22)
   - Target System: 1
   - Target Component: 1
   ```

5. **Message sent over UDP** to `localhost:14540`

6. **PX4 receives MAVLink packet**:
   - Validates command
   - Checks flight mode and safety
   - Executes motor commands

7. **PX4 sends acknowledgment** back via MAVLink:
   ```
   MAVLink Message:
   - Message ID: COMMAND_ACK (77)
   - Result: MAV_RESULT_ACCEPTED (0)
   ```

8. **MAVSDK awaits response** → completes Python async call

9. **Backend returns JSON** to frontend:
   ```json
   {"status": "takeoff initiated"}
   ```

#### 4. **Why MAVSDK Instead of Raw MAVLink?**

**Without MAVSDK (raw MAVLink):**
```python
# Manual message construction
msg = MAVLink_command_long_message(
    target_system=1,
    target_component=1,
    command=22,  # MAV_CMD_NAV_TAKEOFF
    confirmation=0,
    param1=0, param2=0, param3=0, param4=0,
    param5=0, param6=0, param7=10  # altitude
)
connection.send(msg)
```

**With MAVSDK:**
```python
await drone.action.takeoff()  # One line!
```

MAVSDK handles:
- Message encoding/decoding
- Sequence numbers
- CRC checksums
- Connection management
- Async/await patterns
- Error handling

#### 5. **Advanced MAVSDK Features (Future Enhancements)**

**Telemetry Streaming:**
```python
async for position in drone.telemetry.position():
    print(f"Lat: {position.latitude_deg}, Lon: {position.longitude_deg}")
    # Could broadcast to frontend via WebSocket
```

**Mission Planning:**
```python
mission_items = [
    MissionItem(40.7440, -74.0255, 10, 5, True, float('nan'), ...),
    MissionItem(40.7445, -74.0250, 10, 5, True, float('nan'), ...),
]
await drone.mission.upload_mission(mission_items)
await drone.mission.start_mission()
```

**Geofencing:**
```python
await drone.geofence.upload_geofence([polygon_points])
```

---

### Data Flow Examples

#### Example 1: Arming the Drone
```
User clicks "Arm" button
    ↓
Frontend: POST http://localhost:8000/arm
    ↓
Backend: client.arm()
    ↓
MAVSDK: Encode MAVLink COMMAND_LONG(400)
    ↓
UDP: Send to localhost:14540
    ↓
PX4: Receive → Validate → Arm motors
    ↓
PX4: Send COMMAND_ACK back
    ↓
MAVSDK: Decode acknowledgment
    ↓
Backend: Return {"status": "armed"}
    ↓
Frontend: Display "Drone Armed" status
```

#### Example 2: GPS Tracking (Parallel System)
```
GPS2IP app (phone)
    ↓
UDP NMEA sentences → localhost:11123
    ↓
Frontend Server: Parse NMEA (RMC/GGA)
    ↓
Socket.IO: Broadcast GPS coordinates
    ↓
Browser: Update Leaflet map marker
```

**Note:** GPS tracking is independent of the drone control system. It uses a separate UDP stream and doesn't interact with MAVSDK.

---

### Port Reference

| Component | Port | Protocol | Purpose |
|-----------|------|----------|---------|
| Frontend UI | 3001 | HTTP/WebSocket | Serve web dashboard |
| Backend API | 8000 | HTTP | Drone command REST API |
| PX4 MAVLink | 14540 | UDP | Flight controller communication |
| GPS2IP | 11123 | UDP | NMEA GPS data stream |

---

### Security & CORS

Since frontend (3001) and backend (8000) run on different ports, CORS headers are required:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Only allow our frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This prevents unauthorized websites from sending drone commands while allowing legitimate requests from our dashboard.

---

### Computer Vision Integration (Future)

**File: `drone/vision/aruco.py`**

The ArUco marker detection module will enable:
- **Precision landing**: Detect visual markers on landing pads
- **Object tracking**: Follow specific targets
- **Obstacle avoidance**: Identify hazards in flight path

**Integration approach:**
1. Camera feed → OpenCV processing
2. Detect ArUco marker ID 42
3. Calculate position offset
4. Send corrections via MAVSDK:
   ```python
   await drone.offboard.set_position_ned(PositionNedYaw(x, y, z, yaw))
   ```

Currently runs standalone for testing; future versions will integrate with backend telemetry.

## Prerequisites
- Docker (for PX4 SITL)
- Python 3.8+ and pip (backend)
- Node.js and npm (frontend)
- Network access between simulator and backend (UDP localhost:14540 by default)

## How to run

You must run three components in parallel:
1. PX4 flight simulator (Docker)
2. Backend (FastAPI + MAVSDK)
3. Frontend (Node.js + Express)

### 1. PX4 simulator (Docker)
Requires Docker. In a terminal:
```bash
docker run --rm -it jonasvautherin/px4-gazebo-headless:1.16.0
```
PX4 broadcasts MAVLink on udp://localhost:14540 by default. Look for logs like:
INFO  [commander] Ready for takeoff!

### 2. Backend (FastAPI + MAVSDK)
Open a second terminal:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Server will be available at: http://localhost:8000

### 3. Frontend (Node.js)
Open a third terminal:
```bash
cd frontend
npm install
npm start
```
UI served at: http://localhost:3001

## API endpoints
Use POST requests to control the drone:
- POST /connect  — connect to PX4
- POST /arm      — arm the drone
- POST /takeoff  — request takeoff
- POST /land     — request landing

Example: curl -X POST http://localhost:8000/takeoff

## What you'll see
- Map centered on Stevens campus (Leaflet)
- Live GPS coordinate updates via WebSockets
- Status banner (e.g., "Drone in Flight" / "No Drone in Flight")
- Control buttons: Connect, Arm, Takeoff, Land — these call the backend endpoints

## CI/CD Pipeline

### Automated Build & Release
The GitHub Actions workflow (`.github/workflows/quackops-ci-cd.yml`) automatically:

1. **Version Management**
   - Auto-increments patch version (e.g., v2.0.0 → v2.0.1)
   - Creates Git tags on every push to `main`

2. **Component Testing**
   - **Frontend**: Installs npm dependencies, validates Node.js code
   - **Backend**: Installs Python packages (FastAPI, MAVSDK), runs pytest
   - **Vision**: Validates OpenCV/ArUco installation and syntax

3. **Integration Verification**
   - Pulls PX4 SITL Docker image
   - Confirms all components can communicate
   - Verifies dependency compatibility

4. **Release Artifacts**
   - Bundles all built components into a tarball
   - Creates GitHub Release with version tag
   - Uploads build artifacts for distribution

### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main`

### What Gets Built
- Node.js frontend (Express + Socket.IO)
- Python backend (FastAPI + MAVSDK 1.6.0)
- Computer vision module (OpenCV + ArUco)

All dependencies installed via pip/npm—no manual C++ compilation required.

## Troubleshooting
- Verify Docker is running and PX4 logs show a MAVLink endpoint (udp://localhost:14540).  
- Ensure backend can reach the simulator (same host or correct UDP forwarding).  
- Check browser console/network tab for WebSocket or HTTP errors.
