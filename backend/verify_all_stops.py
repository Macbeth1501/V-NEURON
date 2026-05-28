"""
Verify coordinates for every stop in the geojson files + known extras.
Outputs two dicts: FOUND (from geojson) and MISSING (need manual coords).
"""
import json
import time

# ── Pull all stops from geojson files ─────────────────────────────────────────
names = set()
with open("data/nagpur_bus_stops.geojson") as f:
    d = json.load(f)
    for feat in d["features"]:
        name = feat["properties"].get("name")
        if name:
            names.add(name)

with open("data/nagpur_metro.geojson") as f:
    d = json.load(f)
    for feat in d["features"]:
        name = feat["properties"].get("name")
        if name:
            names.add(name)

exclude = {
    "North South Corridor (Orange Line)", "East West Corridor (Aqua Line)",
    "Platform 1", "Bus Stop", "Nagpur Main Bus Stand", "Railway Station",
    "Sitabuldi (Aqua Line)", "Sitabuldi (Orange Line)", "Nag mandir",
    "Nagpur Junction railway station", "নাগপুর রেলওয়ে স্টেশন",
    "नागपुर रेल्वे स्टेशन", "Bus Area", "Khapri Depot - Bus Terminal",
    "Prop. Elevated Metro Route 1", "Bus Stand City Bus", "KTPS Colony Gate No.2",
    "KTPS Gate No.1",
}
stops = sorted([n for n in names if n not in exclude])

# ── Additional hand-curated places ────────────────────────────────────────────
extra_places = [
    # Colleges
    "G.H. Raisoni College of Engineering", "Ramdeobaba College of Engineering",
    "YCCE", "G. S. College of Commerce", "Dharampeth Science College",
    "Hislop College", "Institute of Science", "RKNEC",
    "Nagpur University (RTM)", "Priyadarshini College of Engineering",
    "Symbiosis International University", "KDK College",
    # Hospitals
    "AIIMS Nagpur", "Orange City Hospital", "Wockhardt Hospital",
    "Kingsway Hospital", "Alexis Hospital", "Mayo Hospital (IGGMCH)",
    "Lata Mangeshkar Hospital", "KIMS Kingsway Hospital",
    # Shopping / Malls
    "Empress Mall", "Eternity Mall", "Lokmat Square Mall",
    # Popular Areas / Landmarks
    "Maharaj Bagh Zoo", "Raman Science Centre", "Deekshabhoomi",
    "Sadar", "Dharampeth", "Itwari", "Manish Nagar", "Hingna",
    "Jamtha", "Takalghat", "Kamptee", "Fetri", "Khapri",
    "Gondkhairi", "Bhandara Road", "Wardhaman Nagar", "Trimurti Nagar",
    "Pratap Nagar", "Jaripatka", "Gittikhadan", "Wathoda",
    "Sonegaon", "Pardi", "Nandanvan"
]

all_names = sorted(set(stops) | set(extra_places))

# ── Check against built-in geojson coords ────────────────────────────────────
geojson_coords = {}
for path in ["data/nagpur_bus_stops.geojson", "data/nagpur_metro.geojson"]:
    with open(path) as f:
        d = json.load(f)
        for feat in d["features"]:
            name = feat["properties"].get("name")
            if name and feat.get("geometry", {}).get("type") == "Point":
                c = feat["geometry"]["coordinates"]
                geojson_coords[name.strip().lower()] = (c[1], c[0])

in_geojson = []
need_manual = []
for name in all_names:
    if name.lower() in geojson_coords:
        in_geojson.append((name, geojson_coords[name.lower()]))
    else:
        need_manual.append(name)

print("=== IN GEOJSON ===")
for n, c in in_geojson:
    print(f"  \"{n.lower()}\": {c},")

print(f"\n=== NEED MANUAL COORDS ({len(need_manual)}) ===")
for n in need_manual:
    print(f"  {n}")
