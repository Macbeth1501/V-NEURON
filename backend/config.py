"""
config.py — Single source of truth for all V-NEURON settings.
All paths, speeds, penalties, and constants are defined here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# ── File Paths ────────────────────────────────────────────────────────────────
DATA_DIR = "data"
ROADS_GRAPHML         = f"{DATA_DIR}/nagpur_roads.graphml"
ROADS_PROJECTED       = f"{DATA_DIR}/nagpur_roads_projected.graphml"
METRO_GEOJSON         = f"{DATA_DIR}/nagpur_metro.geojson"
BUS_GEOJSON           = f"{DATA_DIR}/nagpur_bus_stops.geojson"
METRO_PROJ_GEOJSON    = f"{DATA_DIR}/nagpur_metro_projected.geojson"
BUS_PROJ_GEOJSON      = f"{DATA_DIR}/nagpur_bus_projected.geojson"
MULTIMODAL_BASE       = f"{DATA_DIR}/vneuron_multimodal_base.graphml"
OMNIMODAL_FINAL       = f"{DATA_DIR}/vneuron_omnimodal_final.graphml"
CALIBRATED_NETWORK    = f"{DATA_DIR}/vneuron_calibrated_network.graphml"

# ── Map Area ──────────────────────────────────────────────────────────────────
CENTER_LATLON = (21.1458, 79.0882)
RADIUS_M = 45000
CRS_PROJECTED = "EPSG:32644"  # UTM Zone 44N — correct for Nagpur

# ── Speed Profiles (km/h) ─────────────────────────────────────────────────────
SPEEDS_FREE_FLOW = {
    "motorway": 80, "trunk": 60, "primary": 50,
    "secondary": 40, "tertiary": 30, "residential": 20,
}

SPEEDS_PEAK_HOUR = {
    "motorway": 15, "trunk": 10, "primary": 8,
    "secondary": 7, "tertiary": 5, "residential": 4,
}

# ── Transit Parameters ────────────────────────────────────────────────────────
METRO_SPEED_KMH     = 33       # Nagpur Metro average speed
WALKING_SPEED_MPS   = 1.25     # ~4.5 km/h
BOARDING_PENALTY_S  = 300      # 5-minute boarding penalty per transit transfer
METRO_ID_BASE       = 1_000_000_000_000  # Offset to avoid OSM node ID conflicts

# ── Nagpur Metro Lines ────────────────────────────────────────────────────────
ORANGE_LINE = [
    "Automotive Square", "Nari Road", "Indora Square", "Kadvi Square",
    "Gaddi Godam Square", "Kasturchand Park", "Zero Mile", "Sitabuldi",
    "Congress Nagar", "Rahate Colony", "Ajni Square", "Chhatrapati Square",
    "Jaiprakash Nagar", "Ujjwal Nagar", "Airport", "Airport South",
    "New Airport", "Khapri",
]

AQUA_LINE = [
    "Prajapati Nagar", "Vaishnodevi Square", "Ambedkar Square",
    "Telephone Exchange", "Chitaroli Square", "Agrasen Square",
    "Dosar Vaisya Square", "Nagpur Junction railway station",
    "Cotton Market", "Sitabuldi", "Jhasi Rani Square",
    "Institute of Engineers", "Shankar Nagar Square", "LAD College",
    "Ambazari Lake", "Subhash Nagar", "Vasudev Nagar",
    "Rachna Ring Road", "Lokmanya Nagar",
]
