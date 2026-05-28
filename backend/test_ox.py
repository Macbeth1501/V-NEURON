import osmnx as ox
print("osmnx version:", ox.__version__)

try:
    metro = ox.features_from_point((21.1458, 79.0882), tags={"railway": ["subway", "light_rail", "station"]}, dist=20000)
    print("Metro features:", len(metro))
except Exception as e:
    print("Error:", e)
