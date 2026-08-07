import requests
import polyline
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c

def getPlaces(lat, lon):
    API_KEY = "AIzaSyCWu_AOIPvSm6DjvmpuIJTwNdQROPO-DrA"

    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.location,places.formattedAddress"
    }
    data = {
        "includedTypes": ["hospital"],
        # "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat, 
                    "longitude": lon
                },
                "radius": 5000.0
            }
        }
}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result= []
            for i in response.json()['places']:
                name = i['displayName']['text']
                dlat = i['location']['latitude']
                dlon = i['location']['longitude']
                result.append({
                    'name': name,
                    'lat': dlat,
                    'lon': dlon
                })

            result = sorted(result, key= lambda x: haversine(lat, lon, x['lat'], x['lon']))
            return result[:5]
        else:
            return "API Error"

    except Exception as e:
        return e

def decodePolyline(encodedPolyline: str):
    coordinates = polyline.decode(encodedPolyline)
    return coordinates

def getRoute(lat, lon, dlat, dlon):
    API_KEY = "AIzaSyCWu_AOIPvSm6DjvmpuIJTwNdQROPO-DrA"

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.staticDuration,routes.distanceMeters,routes.polyline.encodedPolyline"
    }
    data = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": lat,
                    "longitude": lon
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": dlat,
                    "longitude": dlon
                }
            }
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": False
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            route=response.json()['routes']
            sortedRoute= sorted(route, key=lambda x: x['distanceMeters'])
            distance = float(sortedRoute[0]['distanceMeters'])
            staticDuration = int(sortedRoute[0]['staticDuration'][:-1])/60
            duration = int(sortedRoute[0]['duration'][:-1])/60
            encodedPolyline = sortedRoute[0].get('polyline')['encodedPolyline']
            laneCoordinates = decodePolyline(encodedPolyline)

            return {
                'distance': distance,
                'staticDuration': staticDuration,
                'duration': duration,
                'congestionRatio': round(duration/staticDuration, 2),
                'laneCoordinates': laneCoordinates
            }
        else:
            return "API Error"
    except Exception as e:
        return e

def getWeather(lat, lon):
    API_KEY = "d0cc7592f738b79121a8dd0c4c53317b"

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            rain = data.get("rain", None)
            features = {
                "rain": rain["1h"] if rain else None,
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "visibility": data.get("visibility", 0),
                "weather": data["weather"][0]["main"],
                "description": data["weather"][0]["description"]
            }
            return features
        else:
            return "API Error"
    except Exception as e:
        return e
