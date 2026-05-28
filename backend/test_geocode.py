import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

LOCATIONS = [
  "Abhayankar nagar bus stop", "Agrasen Square", "Airport", "Airport South", "Ajni", "Ajni Square",
  "Ambazari Lake", "Ambedkar Square", "Automotive Square", "Aychit Mandir Bus Stop", "Ayodhya T-point",
  "Chhatrapati Square", "Chitaroli Square", "Chitroli Square", "Congress Nagar", "Cotton Market",
  "Deekshabhoomi", "Dosar Vaisya Square", "Dr. Babasaheb Ambedkar International Airport", "Empress Mall",
  "Friends Colony Bus Stop", "Futala Lake", "GMC", "Gaddi Godam Square", "Gorewada Zoo", "Indora Square",
  "Institute of Engineers", "Itwari Junction", "Jaiprakash Nagar", "Jamtha", "Jhasi Rani Square", "Kadvi Square",
  "Kalamna", "Kasturchand Park", "Khapri", "Khurana", "Koradi Naka", "LAD College", "Lokmanya Nagar",
  "Mhalgi Nagar Square", "Nagpur Junction", "Nagpur Railway Station", "Nari Road", "New Airport",
  "Prajapati Nagar", "Rachna Ring Road", "Rahate Colony", "Raman Science Centre", "SVPCET",
  "Sanjay Gandhi Nagar", "Seminary Hills", "Shankar Nagar Square", "Sitabuldi", "Sitabuldi City Bus Stand",
  "Sitabuldi Fort", "Subhash Nagar", "Takalghat", "Telephone Exchange", "Ujjwal Nagar", "VNIT", "Vaishnodevi Square",
  "Vasudev Nagar", "Vayusena Nagar", "Zaveri Nursing Home, Nagpur", "Zero Mile", "Zero Mile Stone"
]

geo = Nominatim(user_agent="vneuron_api_test", timeout=10)
not_found = []

for loc in LOCATIONS:
    try:
        res = geo.geocode(f"{loc}, Nagpur, India")
        if not res:
            not_found.append(loc)
    except Exception as e:
        not_found.append(loc)
    time.sleep(0.1)

print("NOT FOUND:", json.dumps(not_found, indent=2))
