import os
import json
import requests

from config import Config
from backend.elevation import ElevationService
from backend.slope_analysis import SlopeAnalysisService
from backend.rainfall_analysis import RainfallAnalysisService
from backend.terrain_analysis import TerrainAnalysisService
from backend.risk_calculation import RiskCalculationEngine
from backend.historical_data import HistoricalLandslideService
from ml_model.predictor import MLPredictor


class DataLoaderService:

    def __init__(self):
        self.elevation_service = ElevationService()
        self.slope_service = SlopeAnalysisService()
        self.rainfall_service = RainfallAnalysisService()
        self.terrain_service = TerrainAnalysisService()
        self.risk_engine = RiskCalculationEngine()
        self.historical_service = HistoricalLandslideService()

        # Machine Learning model
        self.ml_predictor = MLPredictor()

    def process_location(
        self,
        lat,
        lon,
        weights=None,
        radius_km=100,
        weather_mode="auto"
    ):
        """
        Complete landslide-risk pipeline.

        1. Elevation & DEM
        2. Slope calculation
        3. Rainfall retrieval
        4. Terrain classification
        5. Historical landslide evidence
        6. Existing multi-criteria risk calculation
        7. Random Forest ML prediction
        8. Spatial GeoJSON grid
        """

        # ============================================================
        # 1. ELEVATION
        # ============================================================

        elev_data = self.elevation_service.fetch_elevation_grid(
            lat,
            lon,
            grid_size=9,
            step_deg=0.002
        )

        # ============================================================
        # 2. SLOPE
        # ============================================================

        slope_data = self.slope_service.calculate_slope(
            elev_data["elevation_matrix"],
            elev_data["lats"],
            elev_data["lons"]
        )

        # ============================================================
        # 3. RAINFALL
        # ============================================================

        rain_data = self.rainfall_service.fetch_rainfall_data(
            lat,
            lon,
            mode=weather_mode
        )

        # ============================================================
        # 4. TERRAIN
        # ============================================================

        terrain_data = self.terrain_service.analyze_terrain(
            elev_data["elevation_matrix"],
            elev_data["center_elevation"],
            slope_data["center_slope_deg"],
            elev_data["relief"]
        )

        # ============================================================
        # 5. HISTORICAL LANDSLIDE EVIDENCE
        # ============================================================

        historical_nearby = self.historical_service.get_nearby(
            lat,
            lon,
            radius_km=radius_km
        )

        nearest_km = (
            historical_nearby[0]["distance_km"]
            if historical_nearby
            else None
        )

        # ============================================================
        # 6. EXISTING MULTI-CRITERIA RISK
        # ============================================================

        risk_data = self.risk_engine.calculate_score(
            slope_score=slope_data["slope_score"],
            rainfall_score=rain_data["rainfall_score"],
            terrain_score=terrain_data["terrain_score"],
            custom_weights=weights,
            historical_count=len(historical_nearby),
            nearest_historical_km=nearest_km,
            rainfall_intensity=rain_data.get(
                "max_hourly_intensity_mm"
            ),
            data_quality={
                "elevation_fallback": elev_data.get(
                    "is_fallback",
                    False
                ),
                "rainfall_fallback": rain_data.get(
                    "is_fallback",
                    False
                ),
                "rainfall_simulation": rain_data.get(
                    "is_simulation",
                    False
                )
            }
        )

        # ============================================================
        # 7. RANDOM FOREST ML PREDICTION
        # ============================================================

        ml_prediction = None

        # Always expose model availability
        risk_data["ml_model_available"] = (
            self.ml_predictor.available
        )

        if self.ml_predictor.available:

            try:

                # The trained Random Forest model uses:
                #   slope_deg
                #   elevation_m
                #
                # rainfall_mm is passed because the existing
                # application interface expects it, but the
                # current trained model does not use rainfall.

                ml_prediction = self.ml_predictor.predict(
                    slope_deg=float(
                        slope_data["center_slope_deg"]
                    ),
                    rainfall_mm=float(
                        rain_data["total_7day_mm"]
                    ),
                    elevation_m=float(
                        elev_data["center_elevation"]
                    )
                )

                if ml_prediction:

                    # ------------------------------------------------
                    # ML MODEL BECOMES THE PRIMARY RISK SCORE
                    # ------------------------------------------------

                    risk_data["vulnerability_score"] = (
                        ml_prediction["score"]
                    )

                    risk_data["risk_level"] = (
                        ml_prediction["risk_level"]
                    )

                    risk_data["risk_color"] = (
                        ml_prediction["risk_color"]
                    )

                    risk_data["model_version"] = (
                        "3.0-random-forest"
                    )

                    risk_data["ml_model_used"] = True

                    risk_data["ml_prediction"] = (
                        ml_prediction
                    )

                    # ------------------------------------------------
                    # ML-BASED EXPLANATION
                    # ------------------------------------------------

                    probability_percent = (
                        ml_prediction["score"]
                    )

                    risk_data["explanation"] = (
                        f"Random Forest susceptibility "
                        f"assessment: {ml_prediction['risk_level']} "
                        f"with a predicted susceptibility score "
                        f"of {probability_percent:.1f}/100. "
                        f"The model uses terrain slope and "
                        f"elevation as its trained predictors. "
                        f"Recent rainfall and terrain information "
                        f"are also displayed separately as "
                        f"supporting environmental indicators."
                    )

                    # Make it clear that the old 40/35/25
                    # weighted formula is NOT the primary score.
                    risk_data["ml_primary"] = True

                    risk_data["ml_features_used"] = [
                        "slope_deg",
                        "elevation_m"
                    ]

                    # Keep the original weighted values available
                    # for comparison / charts if needed.
                    risk_data["legacy_risk_score"] = (
                        risk_data.get(
                            "vulnerability_score_legacy",
                            None
                        )
                    )

            except Exception as e:

                # ------------------------------------------------
                # ML FAILED
                # ------------------------------------------------

                risk_data["ml_model_used"] = False
                risk_data["ml_primary"] = False
                risk_data["ml_error"] = (
                    f"{type(e).__name__}: {str(e)}"
                )

                risk_data["model_version"] = (
                    "2.0-interaction-aware"
                )

        else:

            # ----------------------------------------------------
            # MODEL UNAVAILABLE
            # ----------------------------------------------------

            risk_data["ml_model_used"] = False
            risk_data["ml_primary"] = False

            risk_data["ml_error"] = (
                "Random Forest model is unavailable."
            )

            risk_data["model_version"] = (
                "2.0-interaction-aware"
            )

        # ============================================================
        # 8. SPATIAL GEOJSON GRID
        # ============================================================

        grid_geojson = (
            self.risk_engine.generate_spatial_grid_geojson(
                elev_data["elevation_matrix"],
                slope_data["slope_matrix"],
                rain_data,
                terrain_data,
                elev_data["lats"],
                elev_data["lons"],
                weights=weights
            )
        )

        # ============================================================
        # 9. HISTORICAL LANDSLIDES GEOJSON
        # ============================================================

        historical_geojson = (
            self.historical_service.to_geojson(
                historical_nearby
            )
        )

        # ============================================================
        # 10. RETURN COMPLETE RESULT
        # ============================================================

        return {

            # --------------------------------------------------------
            # QUERY
            # --------------------------------------------------------

            "query": {
                "latitude": round(lat, 5),
                "longitude": round(lon, 5)
            },

            # --------------------------------------------------------
            # ELEVATION
            # --------------------------------------------------------

            "elevation": {
                "center_elevation_m": elev_data[
                    "center_elevation"
                ],
                "min_elevation_m": elev_data[
                    "min_elevation"
                ],
                "max_elevation_m": elev_data[
                    "max_elevation"
                ],
                "relief_m": elev_data["relief"],
                "source": elev_data["source"],
                "geotiff_path": elev_data["geotiff_path"],
                "is_fallback": elev_data["is_fallback"]
            },

            # --------------------------------------------------------
            # SLOPE
            # --------------------------------------------------------

            "slope": {
                "center_slope_deg": slope_data[
                    "center_slope_deg"
                ],
                "mean_slope_deg": slope_data[
                    "mean_slope_deg"
                ],
                "max_slope_deg": slope_data[
                    "max_slope_deg"
                ],
                "slope_category": slope_data[
                    "slope_category"
                ],
                "slope_score": slope_data[
                    "slope_score"
                ],
                "color": slope_data["color"],
                "description": slope_data[
                    "description"
                ],
                "explanation": slope_data[
                    "explanation"
                ]
            },

            # --------------------------------------------------------
            # RAINFALL
            # --------------------------------------------------------

            "rainfall": {
                "rain_24h_mm": rain_data[
                    "rain_24h_mm"
                ],
                "rain_48h_mm": rain_data[
                    "rain_48h_mm"
                ],
                "rain_72h_mm": rain_data[
                    "rain_72h_mm"
                ],
                "total_7day_mm": rain_data[
                    "total_7day_mm"
                ],
                "max_hourly_intensity_mm": rain_data[
                    "max_hourly_intensity_mm"
                ],
                "rainfall_score": rain_data[
                    "rainfall_score"
                ],
                "rainfall_category": rain_data[
                    "rainfall_category"
                ],
                "rainfall_color": rain_data[
                    "rainfall_color"
                ],
                "rainfall_description": rain_data[
                    "rainfall_description"
                ],
                "intensity_indicator": rain_data[
                    "intensity_indicator"
                ],
                "dates": rain_data["dates"],
                "daily_precipitation": rain_data[
                    "daily_precipitation"
                ],
                "source": rain_data["source"],
                "is_fallback": rain_data[
                    "is_fallback"
                ],
                "is_simulation": rain_data.get(
                    "is_simulation",
                    False
                )
            },

            # --------------------------------------------------------
            # TERRAIN
            # --------------------------------------------------------

            "terrain": {
                "terrain_type": terrain_data[
                    "terrain_type"
                ],
                "terrain_score": terrain_data[
                    "terrain_score"
                ],
                "tri": terrain_data["tri"],
                "tri_category": terrain_data[
                    "tri_category"
                ],
                "aspect_deg": terrain_data[
                    "aspect_deg"
                ],
                "aspect_cardinal": terrain_data[
                    "aspect_cardinal"
                ],
                "description": terrain_data[
                    "description"
                ]
            },

            # --------------------------------------------------------
            # RISK
            # --------------------------------------------------------

            "risk": risk_data,

            # --------------------------------------------------------
            # SPATIAL GRID
            # --------------------------------------------------------

            "grid_geojson": grid_geojson,

            # --------------------------------------------------------
            # HISTORICAL DATA
            # --------------------------------------------------------

            "historical": {
                "count": len(historical_nearby),
                "records": historical_nearby,
                "geojson": historical_geojson
            }
        }

    def search_locations(self, query):
        """
        Search for locations worldwide.

        Search order:
        1. Decimal coordinates
        2. Built-in known locations
        3. Fuzzy matching for known locations
        4. Global OpenStreetMap Nominatim search

        This allows users to enter locations such as:
        - Wayanad
        - Bhutan
        - Canada
        - Tokyo
        - London
        - Paris
        - Nepal
        - Any other valid place name worldwide
        """

        import difflib

        query_str = (query or "").strip()

        if not query_str:
            return []

        # ============================================================
        # 1. DECIMAL COORDINATES
        # ============================================================

        parts = query_str.replace(";", ",").split(",")

        if len(parts) == 2:

            try:

                lat = float(parts[0].strip())
                lon = float(parts[1].strip())

                if (
                    -90 <= lat <= 90
                    and -180 <= lon <= 180
                ):

                    return [{
                        "display_name": (
                            f"Coordinate Location "
                            f"({lat:.4f}, {lon:.4f})"
                        ),
                        "lat": lat,
                        "lon": lon,
                        "type": "coordinate"
                    }]

            except ValueError:
                pass

        # ============================================================
        # 2. BUILT-IN GAZETTEER
        # ============================================================

        results = []
        seen_coords = set()

        gazetteer = [

            {
                "name": (
                    "Wayanad (Chooralmala / Meppadi), "
                    "Kerala, India"
                ),
                "aliases": [
                    "wayanad",
                    "waynad",
                    "wynaad",
                    "meppadi",
                    "chooralmala",
                    "mundakkai",
                    "vellarimala",
                    "kerala"
                ],
                "lat": 11.5273,
                "lon": 76.1264,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Kedarnath, Uttarakhand, India"
                ),
                "aliases": [
                    "kedarnath",
                    "kedar",
                    "rudraprayag",
                    "mandakini",
                    "uttarakhand"
                ],
                "lat": 30.7346,
                "lon": 79.0669,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Shimla & Solan, Himachal Pradesh, India"
                ),
                "aliases": [
                    "shimla",
                    "solan",
                    "summer hill",
                    "himachal",
                    "himachal pradesh"
                ],
                "lat": 31.1048,
                "lon": 77.1734,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Munnar & Pettimudi, Idukki, Kerala, India"
                ),
                "aliases": [
                    "munnar",
                    "pettimudi",
                    "idukki",
                    "devikulam"
                ],
                "lat": 10.1652,
                "lon": 77.0118,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Irshalwadi, Raigad, Maharashtra, India"
                ),
                "aliases": [
                    "irshalwadi",
                    "irshalgad",
                    "raigad",
                    "khalapur"
                ],
                "lat": 18.9221,
                "lon": 73.2386,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Malin Village, Pune, Maharashtra, India"
                ),
                "aliases": [
                    "malin",
                    "ambegaon",
                    "pune hills"
                ],
                "lat": 19.1601,
                "lon": 73.6847,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Chamoli / Joshimath, Uttarakhand, India"
                ),
                "aliases": [
                    "chamoli",
                    "joshimath",
                    "rishiganga",
                    "tapovan"
                ],
                "lat": 30.5564,
                "lon": 79.5670,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Shirur Ankola, Karnataka, India"
                ),
                "aliases": [
                    "shirur",
                    "ankola",
                    "uttara kannada",
                    "nh66"
                ],
                "lat": 14.6562,
                "lon": 74.3325,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Oso Landslide Site, Washington, USA"
                ),
                "aliases": [
                    "oso",
                    "snohomish",
                    "stillaguamish",
                    "washington"
                ],
                "lat": 48.2825,
                "lon": -121.8486,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Sindhupalchok / Jure, Nepal"
                ),
                "aliases": [
                    "sindhupalchok",
                    "jure",
                    "sunkoshi",
                    "nepal"
                ],
                "lat": 27.7667,
                "lon": 85.8667,
                "type": "landslide_hotspot"
            },

            {
                "name": (
                    "Bengaluru (Bangalore), Karnataka, India"
                ),
                "aliases": [
                    "bengaluru",
                    "bangalore"
                ],
                "lat": 12.9716,
                "lon": 77.5946,
                "type": "city"
            },

            {
                "name": (
                    "New Delhi / NCR, India"
                ),
                "aliases": [
                    "delhi",
                    "new delhi",
                    "ncr"
                ],
                "lat": 28.6139,
                "lon": 77.2090,
                "type": "city"
            },

            {
                "name": (
                    "Mumbai, Maharashtra, India"
                ),
                "aliases": [
                    "mumbai",
                    "bombay"
                ],
                "lat": 19.0760,
                "lon": 72.8777,
                "type": "city"
            },

            {
                "name": (
                    "Pune, Maharashtra, India"
                ),
                "aliases": [
                    "pune",
                    "poona"
                ],
                "lat": 18.5204,
                "lon": 73.8567,
                "type": "city"
            },

            {
                "name": (
                    "Chennai, Tamil Nadu, India"
                ),
                "aliases": [
                    "chennai",
                    "madras"
                ],
                "lat": 13.0827,
                "lon": 80.2707,
                "type": "city"
            },

            {
                "name": (
                    "Kolkata, West Bengal, India"
                ),
                "aliases": [
                    "kolkata",
                    "calcutta"
                ],
                "lat": 22.5726,
                "lon": 88.3639,
                "type": "city"
            },

            {
                "name": (
                    "Kochi (Cochin), Kerala, India"
                ),
                "aliases": [
                    "kochi",
                    "cochin",
                    "ernakulam"
                ],
                "lat": 9.9312,
                "lon": 76.2673,
                "type": "city"
            },

            {
                "name": (
                    "Thiruvananthapuram, Kerala, India"
                ),
                "aliases": [
                    "thiruvananthapuram",
                    "trivandrum"
                ],
                "lat": 8.5241,
                "lon": 76.9366,
                "type": "city"
            },

            {
                "name": (
                    "Manali, Himachal Pradesh, India"
                ),
                "aliases": [
                    "manali",
                    "kullu"
                ],
                "lat": 32.2432,
                "lon": 77.1892,
                "type": "mountain_hub"
            }
        ]

        q_lower = query_str.lower()

        # ============================================================
        # 3. EXACT / PARTIAL GAZETTEER MATCH
        # ============================================================

        for item in gazetteer:

            matched = False

            for alias in item["aliases"]:

                if (
                    q_lower == alias
                    or alias in q_lower
                    or q_lower in alias
                ):
                    matched = True
                    break

            if (
                not matched
                and q_lower in item["name"].lower()
            ):
                matched = True

            if matched:

                coord_key = (
                    round(item["lat"], 3),
                    round(item["lon"], 3)
                )

                if coord_key not in seen_coords:

                    seen_coords.add(coord_key)

                    results.append({
                        "display_name": item["name"],
                        "lat": item["lat"],
                        "lon": item["lon"],
                        "type": item["type"]
                    })

        # ============================================================
        # 4. FUZZY MATCHING
        # ============================================================

        all_aliases = [
            alias
            for item in gazetteer
            for alias in item["aliases"]
        ]

        close_matches = difflib.get_close_matches(
            q_lower,
            all_aliases,
            n=2,
            cutoff=0.7
        )

        for match in close_matches:

            for item in gazetteer:

                if match in item["aliases"]:

                    coord_key = (
                        round(item["lat"], 3),
                        round(item["lon"], 3)
                    )

                    if coord_key not in seen_coords:

                        seen_coords.add(coord_key)

                        results.append({
                            "display_name": (
                                f"{item['name']} "
                                f"(Did you mean '{match}'?)"
                            ),
                            "lat": item["lat"],
                            "lon": item["lon"],
                            "type": item["type"]
                        })

        # ============================================================
        # 5. GLOBAL OPENSTREETMAP NOMINATIM SEARCH
        # ============================================================

        try:

            url = (
                "https://nominatim.openstreetmap.org/search"
            )

            headers = {
                "User-Agent": (
                    "LandslideRiskMapper/1.0 "
                    "(Hackathon Educational GIS Tool)"
                ),
                "Accept": "application/json",
                "Accept-Language": "en"
            }

            params = {
                "q": query_str,
                "format": "jsonv2",
                "limit": 6,
                "addressdetails": 1,
                "dedupe": 1
            }

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:

                items = response.json()

                for item in items:

                    try:

                        la = float(item.get("lat"))
                        lo = float(item.get("lon"))

                    except (
                        TypeError,
                        ValueError
                    ):
                        continue

                    if not (
                        -90 <= la <= 90
                        and -180 <= lo <= 180
                    ):
                        continue

                    coord_key = (
                        round(la, 3),
                        round(lo, 3)
                    )

                    if coord_key in seen_coords:
                        continue

                    seen_coords.add(coord_key)

                    results.append({
                        "display_name": (
                            item.get(
                                "display_name",
                                query_str
                            )
                        ),
                        "lat": la,
                        "lon": lo,
                        "type": item.get(
                            "type",
                            "location"
                        )
                    })

            else:

                # Do not crash the application if
                # Nominatim temporarily rejects the request.
                pass

        except requests.RequestException:

            # Network/geocoder failure should not
            # break the application.
            pass

        except Exception:

            # Any unexpected geocoding issue should
            # not break the application.
            pass

        # ============================================================
        # 6. BACKUP GEOCODERS
        # ============================================================
        # Nominatim often rejects requests from shared cloud hosts
        # (such as Render). If it gave us nothing, try other free
        # geocoders instead of returning an empty list.

        if not results:
            for geocoder in (self._geocode_open_meteo, self._geocode_photon):
                try:
                    for la, lo, name, kind in geocoder(query_str):
                        coord_key = (round(la, 3), round(lo, 3))
                        if coord_key in seen_coords:
                            continue
                        seen_coords.add(coord_key)
                        results.append({
                            "display_name": name,
                            "lat": la,
                            "lon": lo,
                            "type": kind
                        })
                except Exception:
                    continue
                if results:
                    break

        return results

    @staticmethod
    def _geocode_open_meteo(query_str):
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query_str, "count": 6, "language": "en"},
            headers={"User-Agent": "LandslideRiskMapper/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        out = []
        for it in resp.json().get("results", []) or []:
            parts = [it.get("name"), it.get("admin1"), it.get("country")]
            out.append((
                float(it["latitude"]), float(it["longitude"]),
                ", ".join(p for p in parts if p),
                it.get("feature_code", "location"),
            ))
        return out

    @staticmethod
    def _geocode_photon(query_str):
        resp = requests.get(
            "https://photon.komoot.io/api/",
            params={"q": query_str, "limit": 6, "lang": "en"},
            headers={"User-Agent": "LandslideRiskMapper/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        out = []
        for f in resp.json().get("features", []):
            lo, la = f["geometry"]["coordinates"][:2]
            pr = f.get("properties", {})
            parts = [pr.get("name"), pr.get("state"), pr.get("country")]
            out.append((float(la), float(lo), ", ".join(p for p in parts if p), pr.get("osm_value", "location")))
        return out
