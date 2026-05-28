# V-NEURON 🚦
**Unified Omnimodal Urban Navigation and Routing System for Nagpur**

V-NEURON is a state-of-the-art multimodal routing engine and interactive visualization platform designed specifically for Nagpur, Maharashtra. It consolidates Nagpur's road network, walking pathways, metro rail infrastructure (Orange & Aqua lines), and bus transit stops into a single, unified, weighted routing graph.

By evaluating journeys across both free-flow (Off-Peak) and congested (Peak-Hour) traffic scenarios, V-NEURON provides high-fidelity route planning, transfer indexing, real-time vehicle tracking simulation, and a stateful Agentic AI Chatbot assistant.

---

## 🏗 Project Architecture

The project is structured as a clean, fast monorepo:

```
V-NEURON/
├── README.md                  # Master project handbook (this file)
├── .gitignore                 # Unified git exclusion rules
├── .env.example               # Template configuration file
├── Project Title-2-RRSC.pdf   # Research & academic documentation
│
├── backend/                   # FastAPI Routing Engine & AI Agent API
│   ├── api.py                 # REST API server (endpoints, sessions, CORS)
│   ├── routing_engine.py      # Core Dijkstra/shortest-path NetworkX logic
│   ├── config.py              # Single source of truth (speeds, coordinates, paths)
│   ├── pipeline.py            # Data pipeline to ingest OSM & build graphml networks
│   ├── requirements.txt       # Python environment dependencies
│   ├── locations.json         # Extracted routing interest points
│   └── data/                  # Precompiled Nagpur multimodal routing graphs
│
└── frontend/                  # React + Vite Interactive Map Client
    ├── src/                   # React source files (Map rendering, simulation)
    │   ├── App.jsx            # Main view, dynamic Leaflet markers, AI Agent Integration
    │   ├── index.css          # Premium stylesheets & glassmorphic panels
    │   └── main.jsx           # App entrypoint
    ├── package.json           # React dependencies & scripts
    └── vite.config.js         # Vite bundler configuration
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: Version 3.10 or higher
- **Node.js**: Version 18.0 or higher
- **Groq API Key**: Needed to power the backend agentic routing assistant (chatbot).

---

### 2. Backend & Data Pipeline Setup

Navigate to the `backend` directory:
```bash
cd backend
```

#### A. Set up Virtual Environment & Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### B. Setup Environment Config
Copy the `.env.example` from the root of the project to your backend directory:
```bash
cp ../.env.example .env
```
*Modify `.env` to include your Groq API key: `GROQ_API_KEY=your_api_key_here`*

#### C. Launch FastAPI Server
```bash
python api.py
```
The REST API server will launch at **`http://localhost:8000`**. Preloaded station names are printed on console startup.

---

### 3. Frontend React Client Setup

Open a new terminal window and navigate to the `frontend` directory:
```bash
cd frontend
```

#### A. Install Node Modules
```bash
npm install
```

#### B. Run React App in Development Mode
```bash
npm run dev
```
Open **`http://localhost:5173`** in your browser to interact with the application.

---

## 🤖 Agentic AI Chatbot (Groq Backend)
The application includes a stateful **AI Assistant** sidepanel powered by Llama-3.1 via the Groq SDK on the backend:
- Users converse with the assistant in natural language (e.g., *"Take me from VNIT to airport south, and run it in rush hour"*).
- The backend matches and snaps locations against the 105 Nagpur transit stop cache, setting parameters like `source`, `destination`, `isPeakHour`, and `travelMode`.
- **Auto-Routing**: Once the chatbot extracts both the starting and ending points, it automatically computes the path and renders it on the Leaflet map instantly.
- **Session Memory**: In-memory sessions track conversation history, allowing users to make follow-up queries (e.g., *"Now make it walking only"*).

---

## 📡 Live Route Tracking Simulator
Once a route is calculated, the **Route Tracking Simulator** panel floats into view:
- **Real-Time Animation**: Pressing **Start tracking** triggers a red tracking marker representing a transit vehicle to move step-by-step along the route path.
- **Simulated Telemetry**: Displays current vehicle speed (e.g., 55 km/h on Metro, 5 km/h on walkways), current mode of travel (🚇 Metro, 🚗 Driving, 🚶 Walking), remaining distance, and ETA countdown.
- **Time Dilation**: Speed up the simulation (1x, 2x, 5x, 10x) using the playback multiplier controls.
