from flask import Flask, render_template, request, jsonify

import requests
import polyline

app = Flask(__name__)

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjgwZWFhYzEyNWZkZjRjMzliNTc1YzA1ZjJjNzc5ZGUxIiwiaCI6Im11cm11cjY0In0="

def geocode(place: str):
    """Return (lat, lon) for a place using Nominatim."""
    if "," in place:  # user entered lat,lon
        try:
            lat, lon = map(float, place.split(","))
            return lat, lon
        except:
            return None
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.requote_uri(place)}"
    try:
        r = requests.get(url, headers={"User-Agent": "OptimalPathApp/1.0"}, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print("Geocode error:", e)
    return None

def ors_request(coords, profile="driving-car"):
    """Call ORS API for directions with alternatives."""
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {
        "coordinates": coords,
        "alternative_routes": {
            "target_count": 2,   # 1 optimal + 1 alternative
            "share_factor": 0.6
        },
        "instructions": True  # Ensure instructions included
    }
    try:
        url = f"https://api.openrouteservice.org/v2/directions/{profile}/geojson"
        r = requests.post(url, headers=headers, json=body, timeout=40)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("ORS request error:", e)
        return None

# Splash page route: shows animation before main page
@app.route("/")
def splash():
    return render_template("splash.html")

# Main map page route
@app.route("/main")
def index():
    return render_template("index.html")

@app.route("/route", methods=["POST"])
def route():
    data = request.get_json()
    start_place = data.get("start", "").strip()
    end_place = data.get("end", "").strip()
    mode = data.get("mode", "driving-car")

    start_coords = geocode(start_place)
    end_coords = geocode(end_place)
    if not start_coords or not end_coords:
        return jsonify({"error": "❌ Could not find location(s). Try again."}), 400

    coords = [[start_coords[1], start_coords[0]], [end_coords[1], end_coords[0]]]
    ors_data = ors_request(coords, profile=mode)

    if not ors_data or "features" not in ors_data:
        return jsonify({"error": "❌ No route found", "ors_response": ors_data}), 400

    routes = []
    for idx, feature in enumerate(ors_data["features"]):
        props = feature["properties"]
        summary = props.get("summary", {})
        distance_km = summary.get("distance", 0) / 1000
        duration_min = summary.get("duration", 0) / 60

        geometry = feature["geometry"]["coordinates"]
        # ORS GeoJSON provides [lon, lat] pairs → Convert to [lat, lon]
        route_coords = [[lat, lon] for lon, lat in geometry]

        # Extract steps
        steps = []
        segments = props.get("segments", [])
        for segment in segments:
            for step in segment.get("steps", []):
                wp_index = step["way_points"][0]
                if wp_index < len(route_coords):
                    latlng = route_coords[wp_index]
                    steps.append({
                        "lat": latlng[0],
                        "lon": latlng[1],
                        "instruction": step["instruction"],
                        "distance": step["distance"],
                        "duration": step["duration"]
                    })

        routes.append({
            "id": idx + 1,
            "distance": round(distance_km, 2),
            "duration": round(duration_min, 1),
            "geometry": route_coords,
            "steps": steps
        })

    routes = sorted(routes, key=lambda x: x["duration"])

    return jsonify({
        "start": {"lat": start_coords[0], "lon": start_coords[1], "place": start_place},
        "end": {"lat": end_coords[0], "lon": end_coords[1], "place": end_place},
        "mode": mode,
        "routes": routes
    })

if __name__ == "__main__":
    app.run(debug=True)
