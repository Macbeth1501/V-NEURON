import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import geopandas as gpd
from shapely.geometry import Point
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

import config

from contextlib import asynccontextmanager
import json

# Global variables to store loaded graphs and geocoding cache
graphs = {"off_peak": None, "peak_hour": None}
local_coords = {}
location_display = {} # key: lowercase name, value: original case-preserved name

# ── All known places with manually verified coordinates ───────────────────────
# These supplement the GeoJSON files and are merged into local_coords at startup.
MANUAL_COORDS = {
    # Transit stops (from geojson — authoritative)
    "abhayankar nagar bus stop": (21.1256207, 79.058625),
    "agrasen square": (21.1510532, 79.1029132),
    "airport": (21.0862162, 79.0637884),
    "airport south": (21.0790559, 79.0605257),
    "ajni": (21.1269226, 79.0825751),
    "ajni square": (21.1182122, 79.0721071),
    "ambazari lake": (21.1286919, 79.0457448),
    "ambedkar square": (21.148325, 79.1294936),
    "automotive square": (21.1857923, 79.1195065),
    "aychit mandir bus stop": (21.1468486, 79.1127131),
    "ayodhya t-point": (21.1157788, 79.11068),
    "bamhni": (20.922678, 79.3646285),
    "bansi nagar": (21.1161997, 79.0126033),
    "bharatwada": (21.2314215, 79.0167127),
    "bhiwapur": (20.7697169, 79.5116593),
    "borkhedi": (20.8604733, 78.9744835),
    "bus stop hatodi": (21.3328392, 79.359771),
    "bus stop khaparkheda": (21.2681397, 79.3944765),
    "bus stop barshi": (21.2746246, 79.378502),
    "bus stop dudhala": (21.2988296, 79.3737279),
    "bus stop lohdongri": (21.3259469, 79.3606137),
    "bus stop lohdongri camp": (21.3154768, 79.3653144),
    "bus stop nimkheda": (21.2599676, 79.4127832),
    "bus stop sangrampur": (21.360057, 79.3534696),
    "buti bori": (20.918487, 79.0132806),
    "bypass bus stand": (21.1430, 79.0860),
    "chacher": (21.2418625, 79.3553585),
    "chhatrapati square": (21.109139, 79.0696114),
    "chitaroli square": (21.1496469, 79.110395),
    "chitroli square": (21.1496469, 79.110395),
    "congress nagar": (21.1281984, 79.0825531),
    "cotton market": (21.1459896, 79.0897729),
    "dighori buzurg": (21.1090118, 79.2307301),
    "dosar vaisya square": (21.1529727, 79.094916),
    "friends colony bus stop": (21.178535, 79.0457779),
    "futala lake": (21.1565, 79.0345),
    "gaddi godam square": (21.1616305, 79.083725),
    "godhani": (21.2115803, 79.0686347),
    "gumgaon": (20.9939251, 79.0301263),
    "indora square": (21.1736873, 79.1007283),
    "institute of engineers": (21.1383147, 79.0700943),
    "itwari junction": (21.1575034, 79.1188261),
    "jaiprakash nagar": (21.1036395, 79.068179),
    "jhasi rani square": (21.1407181, 79.0778268),
    "kadvi square": (21.1686674, 79.0924243),
    "kalamna": (21.1678546, 79.1409074),
    "kalmeshwar": (21.2295891, 78.9152033),
    "kalmeshwar bus stand msrtc": (21.232261, 78.9175232),
    "kamptee": (21.2108564, 79.1959787),
    "kamptee msrtc bus stand": (21.2122325, 79.1977984),
    "kanhan junction": (21.224885, 79.2368087),
    "kapri kheda": (21.2687954, 79.1184683),
    "kasturchand park": (21.1543646, 79.081477),
    "khapa bus stand": (21.4162697, 78.9832557),
    "khapri": (21.0493478, 79.0478446),
    "khurana": (21.1463323, 79.0699144),
    "kohli": (21.2735481, 78.8078808),
    "koradi naka": (21.2074257, 79.0774049),
    "kuhi": (21.0071063, 79.3503025),
    "lad college": (21.1329162, 79.054798),
    "lokmanya nagar": (21.1108046, 79.001754),
    "metpanjra": (21.2729792, 78.6755625),
    "mhalgi nagar square": (21.1071117, 79.1191744),
    "nagpur junction": (21.1522721, 79.0887006),
    "nagpur railway station": (21.1513782, 79.0904167),
    "nari road": (21.1795001, 79.1097781),
    "new airport": (21.0660407, 79.0558315),
    "nimkheda bus stop": (21.260365, 79.4129571),
    "pachgav bus stop": (21.0328675, 79.1718692),
    "panjara": (21.2324197, 79.0838514),
    "patansaongi": (21.3453155, 79.0099028),
    "prajapati nagar": (21.1501485, 79.148823),
    "rachna ring road": (21.121523, 79.0294117),
    "rahate colony": (21.1276692, 79.0756888),
    "ramtek": (21.3935847, 79.2999141),
    "rewral": (21.2608836, 79.4679735),
    "salwa": (21.2362496, 79.2929081),
    "sanjay gandhi nagar": (21.1067453, 79.1165376),
    "saoner junction": (21.3877213, 78.9264484),
    "seloo road": (20.7770798, 78.7157668),
    "shankar nagar square": (21.1362125, 79.0616442),
    "sindi": (20.8156785, 78.8832426),
    "sitabuldi": (21.1414478, 79.0824843),
    "sitabuldi city bus stand": (21.1414478, 79.0824843),
    "sitabuldi fort": (21.1428, 79.0838),
    "sonkhamb": (21.2764003, 78.7365593),
    "subhash nagar": (21.1233162, 79.0420532),
    "takli bansali p.h.": (21.3559993, 78.9914647),
    "telephone exchange": (21.148814, 79.1182431),
    "tharsa": (21.2563431, 79.4147925),
    "tuljapur": (20.8002764, 78.8076452),
    "ujjwal nagar": (21.0963504, 79.0663192),
    "umred": (20.8512333, 79.3312153),
    "vaishnodevi square": (21.1480272, 79.1364057),
    "vasudev nagar": (21.1187853, 79.0194659),
    "vayusena nagar": (21.1616785, 79.0409214),
    "waroda bus stop": (21.26402, 78.9105355),
    "waygaon": (20.8788141, 79.2931115),
    "zaveri nursing home, nagpur": (21.1699068, 79.1101322),
    "zero mile": (21.1466946, 79.0806347),
    "zero mile stone": (21.1466946, 79.0806347),
    # Extras: verified manually
    "vnit": (21.1232, 79.0515),
    "gmc": (21.1275, 79.0975),
    "medical square": (21.1543, 79.0978),
    "medical college square": (21.1543, 79.0978),
    "laxmi nagar square": (21.1395, 79.1150),
    "ramdaspeth": (21.1415, 79.0670),
    "gandhibagh": (21.1520, 79.0975),
    "wardhaman nagar square": (21.1062, 79.0945),
    "byramji town": (21.1575, 79.0910),
    "dharampeth square": (21.1378, 79.0526),
    "reshimbagh": (21.1340, 79.0832),
    "law college square": (21.1415, 79.0628),
    "shankar nagar": (21.1362, 79.0616),
    "civil lines": (21.1478, 79.0748),
    "svpcet": (20.9934, 79.0271),
    "gorewada zoo": (21.1895, 79.0203),
    "seminary hills": (21.1685, 79.0493),
    "jamtha": (21.0160, 79.0255),
    "takalghat": (20.9320, 78.9615),
    "deekshabhoomi": (21.1248, 79.0611),
    "empress mall": (21.1480, 79.0794),
    "eternity mall": (21.1195, 78.9965),
    "lokmat square mall": (21.1510, 79.0783),
    "maharaj bagh zoo": (21.1432, 79.0740),
    "raman science centre": (21.1295, 79.0558),
    "sadar": (21.1610, 79.0743),
    "dharampeth": (21.1378, 79.0526),
    "itwari": (21.1511, 79.1130),
    "manish nagar": (21.0963, 79.0655),
    "hingna": (21.0940, 78.9830),
    "fetri": (21.1012, 79.0438),
    "bhandara road": (21.1468, 79.1210),
    "wardhaman nagar": (21.1062, 79.0945),
    "trimurti nagar": (21.1065, 79.0575),
    "pratap nagar": (21.1320, 79.1055),
    "jaripatka": (21.1385, 79.1054),
    "gittikhadan": (21.1542, 79.1348),
    "wathoda": (21.0792, 79.1195),
    "sonegaon": (21.1020, 79.0430),
    "pardi": (21.1205, 79.1165),
    "nandanvan": (21.1087, 79.0760),
    "gondkhairi": (21.2325, 78.9430),
    # Colleges
    "g.h. raisoni college of engineering": (21.1165, 78.9950),
    "ramdeobaba college of engineering": (21.1768, 79.0610),
    "ycce": (21.0954, 78.9774),
    "g. s. college of commerce": (21.1448, 79.0558),
    "dharampeth science college": (21.1417, 79.0560),
    "hislop college": (21.1481, 79.0716),
    "institute of science": (21.1396, 79.0789),
    "rknec": (21.1788, 79.0595),
    "nagpur university (rtm)": (21.1340, 79.0452),
    "priyadarshini college of engineering": (21.1155, 79.0003),
    "symbiosis international university": (20.9920, 79.0250),
    "kdk college": (21.1940, 79.0802),
    # Hospitals
    "aiims nagpur": (21.0475, 79.0205),
    "orange city hospital": (21.1278, 79.0601),
    "wockhardt hospital": (21.1365, 79.0602),
    "kingsway hospital": (21.1495, 79.0837),
    "kims kingsway hospital": (21.1495, 79.0837),
    "alexis hospital": (21.1895, 79.0678),
    "mayo hospital (iggmch)": (21.1561, 79.0945),
    "lata mangeshkar hospital": (21.1182, 79.0477),
    "st bus depot": (21.1447, 79.0835),
    "parshivani msrtc bus stand": (21.3050, 79.4210),
    "saoner bus stand": (21.3835, 78.9283),
    "umred colliery siding": (20.8490, 79.3215),
}

def load_local_coordinates():
    """Load coordinates for known metro stations and bus stops into a local dictionary cache."""
    # Load Metro Stations
    try:
        if os.path.exists(config.METRO_GEOJSON):
            with open(config.METRO_GEOJSON) as f:
                data = json.load(f)
                for feature in data.get("features", []):
                    if feature.get("geometry", {}).get("type") == "Point":
                        coords = feature["geometry"]["coordinates"] # [lon, lat]
                        name = feature["properties"].get("name")
                        if name:
                            name_clean = name.strip()
                            local_coords[name_clean.lower()] = (coords[1], coords[0])
                            location_display[name_clean.lower()] = name_clean
    except Exception as e:
        print("Error loading metro coordinates for local cache:", e)

    # Load Bus Stops
    try:
        if os.path.exists(config.BUS_GEOJSON):
            with open(config.BUS_GEOJSON) as f:
                data = json.load(f)
                for feature in data.get("features", []):
                    if feature.get("geometry", {}).get("type") == "Point":
                        coords = feature["geometry"]["coordinates"] # [lon, lat]
                        name = feature["properties"].get("name")
                        if name:
                            name_clean = name.strip()
                            local_coords[name_clean.lower()] = (coords[1], coords[0])
                            location_display[name_clean.lower()] = name_clean
    except Exception as e:
        print("Error loading bus coordinates for local cache:", e)
    
    # Merge manual coords — fills gaps not in GeoJSON (colleges, hospitals, areas etc.)
    for key, coords in MANUAL_COORDS.items():
        if key not in local_coords:  # GeoJSON takes priority if both exist
            local_coords[key] = coords
            # Reconstruct a display name: title-case the key
            location_display[key] = key.title()

    print(f"Preloaded {len(local_coords)} geocoding coordinate entries.")

def load_graphs():
    """Load graphs into memory."""
    try:
        graphs["off_peak"] = ox.load_graphml(config.OMNIMODAL_FINAL)
        graphs["peak_hour"] = ox.load_graphml(config.CALIBRATED_NETWORK)
        print("Graphs loaded successfully.")
    except Exception as e:
        print(f"Error loading graphs: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    load_graphs()
    load_local_coordinates()
    yield
    # Shutdown actions (none)

# Initialize app with lifespan handler
app = FastAPI(title="V-NEURON API", description="Routing engine API wrapper", lifespan=lifespan)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import difflib

def find_best_match(query: str, choices: list[str]) -> str | None:
    """Perform robust fuzzy and substring matching against predefined locations."""
    if not query:
        return None
    query_clean = query.strip().lower()
    
    # 1. Exact match (case-insensitive)
    if query_clean in choices:
        return query_clean
        
    # 2. Substring matching: choice in query or query in choice
    for choice in choices:
        if choice in query_clean or query_clean in choice:
            return choice

    # 3. Fuzzy character-level matching (typos)
    matches = difflib.get_close_matches(query_clean, choices, n=1, cutoff=0.6)
    if matches:
        return matches[0]

    # 4. Token overlap (common words)
    words = set(query_clean.split())
    best_choice = None
    max_overlap = 0
    for choice in choices:
        choice_words = set(choice.split())
        overlap = len(choice_words.intersection(words))
        if overlap > max_overlap:
            max_overlap = overlap
            best_choice = choice
    if max_overlap >= 1:
        return best_choice

    return None

def geocode(address: str):
    """Convert a place name to (lat, lon) using local cache or Nominatim fallback."""
    addr_clean = address.strip().lower()
    if addr_clean in local_coords:
        return local_coords[addr_clean]

    # Manual fallback: accurate coords from geojson + hand-curated extras
    manual_fallbacks = {
        # ── Transit stops from geojson (authoritative) ──────────────────────
        "abhayankar nagar bus stop": (21.1256207, 79.058625),
        "agrasen square": (21.1510532, 79.1029132),
        "airport": (21.0862162, 79.0637884),
        "airport south": (21.0790559, 79.0605257),
        "ajni": (21.1269226, 79.0825751),
        "ajni square": (21.1182122, 79.0721071),
        "ambazari lake": (21.1286919, 79.0457448),
        "ambedkar square": (21.148325, 79.1294936),
        "automotive square": (21.1857923, 79.1195065),
        "aychit mandir bus stop": (21.1468486, 79.1127131),
        "ayodhya t-point": (21.1157788, 79.11068),
        "bamhni": (20.922678, 79.3646285),
        "bansi nagar": (21.1161997, 79.0126033),
        "bharatwada": (21.2314215, 79.0167127),
        "bhiwapur": (20.7697169, 79.5116593),
        "borkhedi": (20.8604733, 78.9744835),
        "bus stop hatodi": (21.3328392, 79.359771),
        "bus stop khaparkheda": (21.2681397, 79.3944765),
        "bus stop barshi": (21.2746246, 79.378502),
        "bus stop dudhala": (21.2988296, 79.3737279),
        "bus stop lohdongri": (21.3259469, 79.3606137),
        "bus stop lohdongri camp": (21.3154768, 79.3653144),
        "bus stop nimkheda": (21.2599676, 79.4127832),
        "bus stop sangrampur": (21.360057, 79.3534696),
        "buti bori": (20.918487, 79.0132806),
        "bypass bus stand": (21.1430, 79.0860),
        "chacher": (21.2418625, 79.3553585),
        "chhatrapati square": (21.109139, 79.0696114),
        "chitaroli square": (21.1496469, 79.110395),
        "chitroli square": (21.1496469, 79.110395),
        "congress nagar": (21.1281984, 79.0825531),
        "cotton market": (21.1459896, 79.0897729),
        "dighori buzurg": (21.1090118, 79.2307301),
        "dosar vaisya square": (21.1529727, 79.094916),
        "friends colony bus stop": (21.178535, 79.0457779),
        "futala lake": (21.1565, 79.0345),
        "gaddi godam square": (21.1616305, 79.083725),
        "godhani": (21.2115803, 79.0686347),
        "gumgaon": (20.9939251, 79.0301263),
        "indora square": (21.1736873, 79.1007283),
        "institute of engineers": (21.1383147, 79.0700943),
        "itwari junction": (21.1575034, 79.1188261),
        "jaiprakash nagar": (21.1036395, 79.068179),
        "jhasi rani square": (21.1407181, 79.0778268),
        "kadvi square": (21.1686674, 79.0924243),
        "kalamna": (21.1678546, 79.1409074),
        "kalmeshwar": (21.2295891, 78.9152033),
        "kalmeshwar bus stand msrtc": (21.232261, 78.9175232),
        "kamptee": (21.2108564, 79.1959787),
        "kamptee msrtc bus stand": (21.2122325, 79.1977984),
        "kanhan junction": (21.224885, 79.2368087),
        "kapri kheda": (21.2687954, 79.1184683),
        "kasturchand park": (21.1543646, 79.081477),
        "khapa bus stand": (21.4162697, 78.9832557),
        "khapri": (21.0493478, 79.0478446),
        "khurana": (21.1463323, 79.0699144),
        "kohli": (21.2735481, 78.8078808),
        "koradi naka": (21.2074257, 79.0774049),
        "kuhi": (21.0071063, 79.3503025),
        "lad college": (21.1329162, 79.054798),
        "lokmanya nagar": (21.1108046, 79.001754),
        "metpanjra": (21.2729792, 78.6755625),
        "mhalgi nagar square": (21.1071117, 79.1191744),
        "nagpur junction": (21.1522721, 79.0887006),
        "nagpur railway station": (21.1513782, 79.0904167),
        "nari road": (21.1795001, 79.1097781),
        "new airport": (21.0660407, 79.0558315),
        "nimkheda bus stop": (21.260365, 79.4129571),
        "pachgav bus stop": (21.0328675, 79.1718692),
        "panjara": (21.2324197, 79.0838514),
        "patansaongi": (21.3453155, 79.0099028),
        "prajapati nagar": (21.1501485, 79.148823),
        "rachna ring road": (21.121523, 79.0294117),
        "rahate colony": (21.1276692, 79.0756888),
        "ramtek": (21.3935847, 79.2999141),
        "rewral": (21.2608836, 79.4679735),
        "salwa": (21.2362496, 79.2929081),
        "sanjay gandhi nagar": (21.1067453, 79.1165376),
        "saoner junction": (21.3877213, 78.9264484),
        "seloo road": (20.7770798, 78.7157668),
        "shankar nagar square": (21.1362125, 79.0616442),
        "sindi": (20.8156785, 78.8832426),
        "sitabuldi": (21.1414478, 79.0824843),
        "sitabuldi city bus stand": (21.1414478, 79.0824843),
        "sitabuldi fort": (21.1428, 79.0838),
        "sonkhamb": (21.2764003, 78.7365593),
        "subhash nagar": (21.1233162, 79.0420532),
        "takli bansali p.h.": (21.3559993, 78.9914647),
        "telephone exchange": (21.148814, 79.1182431),
        "tharsa": (21.2563431, 79.4147925),
        "tuljapur": (20.8002764, 78.8076452),
        "ujjwal nagar": (21.0963504, 79.0663192),
        "umred": (20.8512333, 79.3312153),
        "vaishnodevi square": (21.1480272, 79.1364057),
        "vasudev nagar": (21.1187853, 79.0194659),
        "vayusena nagar": (21.1616785, 79.0409214),
        "waroda bus stop": (21.26402, 78.9105355),
        "waygaon": (20.8788141, 79.2931115),
        "zaveri nursing home, nagpur": (21.1699068, 79.1101322),
        "zero mile": (21.1466946, 79.0806347),
        "zero mile stone": (21.1466946, 79.0806347),
        # ── Extras needing manual pinning ────────────────────────────────────
        "vnit": (21.1232, 79.0515),
        "gmc": (21.1275, 79.0975),
        "svpcet": (20.9934, 79.0271),
        "gorewada zoo": (21.1895, 79.0203),
        "seminary hills": (21.1685, 79.0493),
        "jamtha": (21.0160, 79.0255),
        "takalghat": (20.9320, 78.9615),
        "deekshabhoomi": (21.1248, 79.0611),
        "empress mall": (21.1480, 79.0794),
        "eternity mall": (21.1195, 78.9965),
        "lokmat square mall": (21.1510, 79.0783),
        "maharaj bagh zoo": (21.1432, 79.0740),
        "raman science centre": (21.1295, 79.0558),
        "sadar": (21.1610, 79.0743),
        "dharampeth": (21.1378, 79.0526),
        "itwari": (21.1511, 79.1130),
        "manish nagar": (21.0963, 79.0655),
        "hingna": (21.0940, 78.9830),
        "fetri": (21.1012, 79.0438),
        "bhandara road": (21.1468, 79.1210),
        "wardhaman nagar": (21.1062, 79.0945),
        "trimurti nagar": (21.1065, 79.0575),
        "pratap nagar": (21.1320, 79.1055),
        "jaripatka": (21.1385, 79.1054),
        "gittikhadan": (21.1542, 79.1348),
        "wathoda": (21.0792, 79.1195),
        "sonegaon": (21.1020, 79.0430),
        "pardi": (21.1205, 79.1165),
        "nandanvan": (21.1087, 79.0760),
        "gondkhairi": (21.2325, 78.9430),
        # Colleges
        "g.h. raisoni college of engineering": (21.1165, 78.9950),
        "ramdeobaba college of engineering": (21.1768, 79.0610),
        "ycce": (21.0954, 78.9774),
        "g. s. college of commerce": (21.1448, 79.0558),
        "dharampeth science college": (21.1417, 79.0560),
        "hislop college": (21.1481, 79.0716),
        "institute of science": (21.1396, 79.0789),
        "rknec": (21.1788, 79.0595),
        "nagpur university (rtm)": (21.1340, 79.0452),
        "priyadarshini college of engineering": (21.1155, 79.0003),
        "symbiosis international university": (20.9920, 79.0250),
        "kdk college": (21.1940, 79.0802),
        # Hospitals
        "aiims nagpur": (21.0475, 79.0205),
        "orange city hospital": (21.1278, 79.0601),
        "wockhardt hospital": (21.1365, 79.0602),
        "kingsway hospital": (21.1495, 79.0837),
        "kims kingsway hospital": (21.1495, 79.0837),
        "alexis hospital": (21.1895, 79.0678),
        "mayo hospital (iggmch)": (21.1561, 79.0945),
        "lata mangeshkar hospital": (21.1182, 79.0477),
        "st bus depot": (21.1447, 79.0835),
        "parshivani msrtc bus stand": (21.3050, 79.4210),
        "saoner bus stand": (21.3835, 78.9283),
        "umred colliery siding": (20.8490, 79.3215),
    }
    
    if addr_clean in manual_fallbacks:
        return manual_fallbacks[addr_clean]

    geo = Nominatim(user_agent="vneuron_api", timeout=10)
    try:
        loc = geo.geocode(f"{address}, Nagpur, India")
        if loc:
            return loc.latitude, loc.longitude
    except GeocoderTimedOut:
        pass
    return None

def project_point(lat, lon):
    gs = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(config.CRS_PROJECTED)
    return gs[0].x, gs[0].y

def compute_route(G, orig_latlon, dest_latlon, travelMode="all"):
    ox_x, ox_y = project_point(*orig_latlon)
    dx, dy = project_point(*dest_latlon)
    on = ox.distance.nearest_nodes(G, X=ox_x, Y=ox_y)
    dn = ox.distance.nearest_nodes(G, X=dx, Y=dy)
    
    if travelMode == "path":
        valid_edges = []
        for u, v, k, data in G.edges(keys=True, data=True):
            hw = data.get("highway", "")
            if isinstance(hw, list):
                hw = hw[0]
            hw = str(hw).lower()
            if "subway" not in hw and "rail" not in hw:
                valid_edges.append((u, v, k))
        routing_G = G.edge_subgraph(valid_edges)
    else:
        routing_G = G

    try:
        route = nx.shortest_path(routing_G, on, dn, weight="travel_time")
        route_gdf = ox.routing.route_to_gdf(routing_G, route)
        dist_km = nx.path_weight(routing_G, route, weight="length") / 1000
        time_min = nx.path_weight(routing_G, route, weight="travel_time") / 60
        return route, route_gdf, dist_km, time_min
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None, None, None, None

class RouteRequest(BaseModel):
    source: str
    destination: str
    isPeakHour: bool = False
    travelMode: str = "all"  # 'all' or 'path'

class ChatRequest(BaseModel):
    prompt: str
    session_id: str

# Retrieve API key
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key)

# In-memory storage for chat sessions
chat_sessions = {}
chat_parameters = {}

def compute_route_response(source: str, destination: str, isPeakHour: bool, travelMode: str):
    if graphs["off_peak"] is None or graphs["peak_hour"] is None:
        return None, "Graphs not loaded. Please run backend pipeline or check data folder."

    orig_coords = geocode(source)
    dest_coords = geocode(destination)

    if not orig_coords:
        return None, f"Could not geocode source location: {source}"
    if not dest_coords:
        return None, f"Could not geocode destination location: {destination}"

    G = graphs["peak_hour"] if isPeakHour else graphs["off_peak"]

    route, route_gdf, dist_km, time_min = compute_route(G, orig_coords, dest_coords, travelMode)

    if route is None:
        return None, f"No routing path found between '{source}' and '{destination}'."

    # Reproject coords to WGS84 (EPSG:4326) for the Leaflet map
    route_gdf = route_gdf.to_crs("EPSG:4326")
    
    segments = []
    for _, row in route_gdf.iterrows():
        if row.geometry is None:
            continue
        coords = list(row.geometry.coords)
        latlons = [[y, x] for x, y in coords]
        
        highway_type = row.get("highway", "road")
        if isinstance(highway_type, list):
            highway_type = highway_type[0]

        segments.append({
            "coordinates": latlons,
            "highway": str(highway_type),
            "distance_m": row.get("length", 0),
            "travel_time_s": row.get("travel_time", 0)
        })

    return {
        "source": source,
        "destination": destination,
        "origin_coords": orig_coords,
        "destination_coords": dest_coords,
        "metrics": {
            "distance_km": round(dist_km, 2),
            "time_min": round(time_min, 1)
        },
        "segments": segments
    }, None

@app.post("/route")
def get_route(req: RouteRequest):
    result, error = compute_route_response(
        source=req.source,
        destination=req.destination,
        isPeakHour=req.isPeakHour,
        travelMode=req.travelMode
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    session_id = req.session_id
    prompt = req.prompt.strip()

    # Initialize session if not existing
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
        chat_parameters[session_id] = {
            "source": None,
            "destination": None,
            "isPeakHour": False,
            "travelMode": "all"
        }

    history = chat_sessions[session_id]
    params = chat_parameters[session_id]

    # Preload the predefined locations list for the prompt
    locations_list = sorted(list(local_coords.keys()))
    if not locations_list:
        locations_list = sorted([
            "vnit", "airport", "sitabuldi", "ajni", "svpcet", "railway station", "airport south"
        ])
    locations_str = ", ".join([f'"{name}"' for name in locations_list])

    system_prompt = f"""You are V-NEURON's Agentic Navigation Assistant for Nagpur, India.
Your task is to help the user calculate multimodal transit routes (combining metro, bus, walking, and driving) and chat about their journey.

PREDEFINED LOCATIONS in Nagpur System (You should map user selections to these names if they match):
{locations_str}

CURRENT PARAMETERS for this user:
- Source: {params['source']}
- Destination: {params['destination']}
- Time Scenario: {"Peak Hour" if params['isPeakHour'] else "Normal Hour"}
- Travel Mode: {params['travelMode']}

Instructions:
1. Maintain a helpful, friendly, and professional conversation.
2. If the user mentions a starting point (origin) or end point (destination):
   - If it matches a PREDEFINED LOCATION, extract it and map it to that EXACT name.
   - If it is ANY OTHER location in Nagpur (e.g. "VNIT", "Gittikhadan", "Jamtha", "Takalghat", a specific hospital, or landmark), extract the name exactly as mentioned by the user. Do not restrict to predefined locations.
3. If they change the time scenario (e.g., peak/rush hour, normal hour, traffic), set isPeakHour (true/false).
4. If they change the travel mode (e.g., road only/no transit vs all modes), set travelMode ("path" or "all").
5. Return ONLY a valid JSON object. Do not include markdown backticks or any other text.

JSON Structure:
{{
   "reply": "Conversational reply. If both source and destination are set, inform them you are calculating the route.",
   "source": "Extracted location name or null",
   "destination": "Extracted location name or null",
   "isPeakHour": true/false,
   "travelMode": "all"/"path"
}}
"""

    # Add user message to history
    history.append({"role": "user", "content": prompt})

    # Prepare messages payload
    messages_payload = [{"role": "system", "content": system_prompt}] + history[-8:]

    try:
        completion = groq_client.chat.completions.create(
            messages=messages_payload,
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content or "{}"
        
        # Clean up any potential markdown wraps
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)

        # Update stored parameters with fuzzy matching to preloaded locations
        if "source" in parsed and parsed["source"]:
            matched_source = find_best_match(parsed["source"], list(local_coords.keys()))
            if matched_source:
                params["source"] = location_display[matched_source]
            else:
                params["source"] = parsed["source"]
        if "destination" in parsed and parsed["destination"]:
            matched_dest = find_best_match(parsed["destination"], list(local_coords.keys()))
            if matched_dest:
                params["destination"] = location_display[matched_dest]
            else:
                params["destination"] = parsed["destination"]
        if "isPeakHour" in parsed and parsed["isPeakHour"] is not None:
            params["isPeakHour"] = parsed["isPeakHour"]
        if "travelMode" in parsed and parsed["travelMode"]:
            params["travelMode"] = parsed["travelMode"]

        reply_text = parsed.get("reply", "Analyzing your routing request...")
        route_data = None
        routing_error = None

        # Check if we can calculate the route
        if params["source"] and params["destination"]:
            route_data, routing_error = compute_route_response(
                source=params["source"],
                destination=params["destination"],
                isPeakHour=params["isPeakHour"],
                travelMode=params["travelMode"]
            )
            if routing_error:
                reply_text += f"\n\n*(Routing note: {routing_error})*"

        # Append assistant reply to session history
        history.append({"role": "assistant", "content": reply_text})

        return {
            "reply": reply_text,
            "source": params["source"],
            "destination": params["destination"],
            "isPeakHour": params["isPeakHour"],
            "travelMode": params["travelMode"],
            "routeData": route_data
        }

    except Exception as e:
        print("Chat endpoint error:", e)
        err_msg = f"Sorry, I encountered an issue while processing: {str(e)}"
        history.append({"role": "assistant", "content": err_msg})
        return {
            "reply": err_msg,
            "source": params["source"],
            "destination": params["destination"],
            "isPeakHour": params["isPeakHour"],
            "travelMode": params["travelMode"],
            "routeData": None
        }

@app.get("/markers")
def get_markers():
    """Return all metro stations and bus stops to be displayed on the map."""
    import json
    markers = []
    
    # Load Metro Stations
    try:
        with open(config.METRO_GEOJSON) as f:
            data = json.load(f)
            for feature in data.get("features", []):
                if feature["geometry"]["type"] == "Point":
                    coords = feature["geometry"]["coordinates"] # [lon, lat]
                    name = feature["properties"].get("name", "Metro Station")
                    markers.append({
                        "id": f"metro_{feature.get('id', len(markers))}",
                        "name": name,
                        "position": [coords[1], coords[0]],
                        "type": "metro"
                    })
    except Exception as e:
        print("Error loading metro markers:", e)

    # Load Bus Stops
    try:
        with open(config.BUS_GEOJSON) as f:
            data = json.load(f)
            for feature in data.get("features", []):
                if feature["geometry"]["type"] == "Point":
                    coords = feature["geometry"]["coordinates"] # [lon, lat]
                    name = feature["properties"].get("name", "Bus Stop")
                    markers.append({
                        "id": f"bus_{feature.get('id', len(markers))}",
                        "name": name,
                        "position": [coords[1], coords[0]],
                        "type": "bus"
                    })
    except Exception as e:
        print("Error loading bus markers:", e)
    
    return {"markers": markers}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
