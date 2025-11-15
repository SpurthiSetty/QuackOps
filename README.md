# QuackOps — Drone Control & GPS Tracking

Autonomous drone delivery system for Stevens campus. Combines AI vision, MAVLink navigation, and a real-time web dashboard.

## Table of contents
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [How to run](#how-to-run)
  - [1. PX4 simulator (Docker)](#1-px4-simulator-docker)
  - [2. Backend (FastAPI + MAVSDK)](#2-backend-fastapi--mavsdk)
  - [3. Frontend (Node.js)](#3-frontend-nodejs)
- [API endpoints](#api-endpoints)
- [What you'll see](#what-youll-see)
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
UI served at: http://localhost:3000

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

## Troubleshooting
- Verify Docker is running and PX4 logs show a MAVLink endpoint (udp://localhost:14540).  
- Ensure backend can reach the simulator (same host or correct UDP forwarding).  
- Check browser console/network tab for WebSocket or HTTP errors.
