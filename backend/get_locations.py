import json
import config

names = set()
for x in config.ORANGE_LINE + config.AQUA_LINE:
    names.add(x)

with open('data/nagpur_bus_stops.geojson') as f:
    d1 = json.load(f)
    for f in d1['features']:
        if f['properties'].get('name'):
            names.add(f['properties']['name'])

with open('data/nagpur_metro.geojson') as f:
    d2 = json.load(f)
    for f in d2['features']:
        if f['properties'].get('name'):
            names.add(f['properties']['name'])

locations = sorted(list(names))
print(f"Total locations: {len(locations)}")
with open('locations.json', 'w') as f:
    json.dump(locations, f)
