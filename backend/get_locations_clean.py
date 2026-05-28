import json
import config

names = {"SVPCET", "VNIT", "GMC", "Empress Mall", "Futala Lake", "Deekshabhoomi", "Dr. Babasaheb Ambedkar International Airport", "Nagpur Railway Station", "Sitabuldi Fort", "Raman Science Centre", "Kasturchand Park", "Ambazari Lake", "Seminary Hills", "Gorewada Zoo", "Zero Mile Stone"}

for x in config.ORANGE_LINE + config.AQUA_LINE:
    names.add(x)

with open('data/nagpur_bus_stops.geojson') as f:
    d1 = json.load(f)
    for f in d1['features']:
        name = f['properties'].get('name')
        if name:
            names.add(name)

with open('data/nagpur_metro.geojson') as f:
    d2 = json.load(f)
    for f in d2['features']:
        name = f['properties'].get('name')
        if name:
            names.add(name)

# Exclude some noisy names
exclude = {"North South Corridor (Orange Line)", "East West Corridor (Aqua Line)", "Platform 1", "Bus Stop", "Nagpur Main Bus Stand", "Railway Station", "Sitabuldi (Aqua Line)", "Sitabuldi (Orange Line)", "Nag mandir", "Nagpur Junction railway station", "\u0928\u093e\u0917\u092a\u0941\u0930 \u0930\u0947\u0932\u094d\u0935\u0947 \u0938\u094d\u091f\u0947\u0936\u0928"}
locations = sorted([n for n in names if n not in exclude])
print(locations)
