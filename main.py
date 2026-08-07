lat=22.729189
lon=88.496305

# lat=26.72001
# lon=88.42851

import services
import time, json

# places = services.getPlaces(lat, lon)
print(services.getWeather(lat, lon))

# if type(places) == type([]):
#     for place in places:
#         print("Name: ", place['name'], end="\n")
#         print(json.dumps(services.getRoute(lat, lon, place['lat'], place['lon']))) 
#         break