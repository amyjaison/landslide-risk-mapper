import os
import json
import math
from config import Config

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees). Returns distance in km.
    """
    R = 6371.0 # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class HistoricalLandslideService:
    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(Config.HISTORICAL_DIR, 'nasa_glc_records.json')
        self.records = []
        self._load_records()

    def _load_records(self):
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
            else:
                self.records = []
        except Exception as e:
            print(f"[Warning] Failed to load historical records from {self.data_path}: {e}")
            self.records = []

    def get_all(self):
        """Return all historical records in catalog."""
        return self.records

    def get_nearby(self, lat, lon, radius_km=300):
        """
        Return historical events within radius_km, sorted by distance.
        """
        results = []
        for rec in self.records:
            r_lat = rec.get('lat')
            r_lon = rec.get('lon')
            if r_lat is not None and r_lon is not None:
                dist = haversine_distance(lat, lon, r_lat, r_lon)
                if dist <= radius_km:
                    rec_copy = dict(rec)
                    rec_copy['distance_km'] = round(dist, 1)
                    results.append(rec_copy)
        results.sort(key=lambda x: x['distance_km'])
        return results

    def to_geojson(self, records=None):
        """Convert list of records into GeoJSON FeatureCollection."""
        if records is None:
            records = self.records
        features = []
        for r in records:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [r["lon"], r["lat"]]
                },
                "properties": {
                    "id": r["id"],
                    "name": r["name"],
                    "country": r.get("country", "Unknown"),
                    "region": r.get("region", ""),
                    "date": r.get("date", "Unknown"),
                    "hazard_type": r.get("hazard_type", "Landslide"),
                    "trigger": r.get("trigger", "Rainfall"),
                    "fatalities": r.get("fatalities", 0),
                    "injuries": r.get("injuries", 0),
                    "category": r.get("landslide_category", "Debris Flow"),
                    "source": r.get("source", "NASA Global Landslide Catalog"),
                    "description": r.get("description", ""),
                    "distance_km": r.get("distance_km")
                }
            })
        return {
            "type": "FeatureCollection",
            "features": features
        }

