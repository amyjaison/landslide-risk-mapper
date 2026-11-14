from flask import Blueprint, request, jsonify, render_template
from config import Config
from backend.data_loader import DataLoaderService
from backend.elevation import ElevationService
from backend.slope_analysis import SlopeAnalysisService
from backend.rainfall_analysis import RainfallAnalysisService
from backend.terrain_analysis import TerrainAnalysisService
from backend.risk_calculation import RiskCalculationEngine
from backend.historical_data import HistoricalLandslideService
from ml_model.predictor import MLPredictor

api_bp = Blueprint('api', __name__)
web_bp = Blueprint('web', __name__)

# Initialize services
data_loader = DataLoaderService()
elevation_svc = ElevationService()
slope_svc = SlopeAnalysisService()
rainfall_svc = RainfallAnalysisService()
terrain_svc = TerrainAnalysisService()
risk_engine = RiskCalculationEngine()
historical_svc = HistoricalLandslideService()
ml_predictor = MLPredictor()

def parse_lat_lon(req):
    """Extract and validate latitude and longitude query parameters."""
    lat_str = req.args.get('lat')
    lon_str = req.args.get('lon')
    if lat_str is None or lon_str is None:
        return None, None, "Missing 'lat' or 'lon' query parameter."
    try:
        lat = float(lat_str)
        lon = float(lon_str)
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return None, None, "Coordinates out of bounds: lat must be [-90, 90], lon [-180, 180]."
        return lat, lon, None
    except ValueError:
        return None, None, "Invalid numerical value for 'lat' or 'lon'."

def parse_weights(req):
    """Extract optional custom weights from query parameters."""
    w_slope = req.args.get('w_slope')
    w_rain = req.args.get('w_rain')
    w_terrain = req.args.get('w_terrain')
    if w_slope is not None and w_rain is not None and w_terrain is not None:
        try:
            return {
                "slope": float(w_slope),
                "rainfall": float(w_rain),
                "terrain": float(w_terrain)
            }
        except ValueError:
            pass
    return None

# ================= API ENDPOINTS =================

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Landslide Risk Mapper API",
        "version": "2.0.0",
        "model_version": risk_engine.MODEL_VERSION,
        "weights": risk_engine.weights
    })

@api_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('location', '')
    if not query:
        return jsonify({"success": False, "error": "Query parameter 'location' is required", "results": []}), 400
    results = data_loader.search_locations(query)
    return jsonify({
        "success": True,
        "query": query,
        "count": len(results),
        "results": results
    })

@api_bp.route('/demo-locations', methods=['GET'])
def demo_locations():
    return jsonify({
        "success": True,
        "locations": Config.DEMO_LOCATIONS
    })

@api_bp.route('/location', methods=['GET'])
def full_location_analysis():
    lat, lon, err = parse_lat_lon(request)
    if err:
        return jsonify({"success": False, "error": err}), 400

    weights = parse_weights(request)
    radius_km = float(request.args.get('radius', 150))
    weather_mode = request.args.get('weather_mode', 'auto')

    try:
        data = data_loader.process_location(lat, lon, weights=weights, radius_km=radius_km, weather_mode=weather_mode)
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500

@api_bp.route('/slope', methods=['GET'])
def slope():
    lat, lon, err = parse_lat_lon(request)
    if err:
        return jsonify({"success": False, "error": err}), 400

    elev_data = elevation_svc.fetch_elevation_grid(lat, lon, grid_size=9)
    slope_data = slope_svc.calculate_slope(elev_data["elevation_matrix"], elev_data["lats"], elev_data["lons"])

    return jsonify({
        "success": True,
        "lat": lat,
        "lon": lon,
        "slope": slope_data,
        "elevation_summary": {
            "center": elev_data["center_elevation"],
            "relief": elev_data["relief"],
            "source": elev_data["source"]
        }
    })

@api_bp.route('/rainfall', methods=['GET'])
def rainfall():
    lat, lon, err = parse_lat_lon(request)
    if err:
        return jsonify({"success": False, "error": err}), 400

    weather_mode = request.args.get('weather_mode', 'auto')
    rain_data = rainfall_svc.fetch_rainfall_data(lat, lon, mode=weather_mode)
    return jsonify({
        "success": True,
        "rainfall": rain_data
    })

@api_bp.route('/terrain', methods=['GET'])
def terrain():
    lat, lon, err = parse_lat_lon(request)
    if err:
        return jsonify({"success": False, "error": err}), 400

    elev_data = elevation_svc.fetch_elevation_grid(lat, lon, grid_size=9)
    slope_data = slope_svc.calculate_slope(elev_data["elevation_matrix"], elev_data["lats"], elev_data["lons"])
    terrain_data = terrain_svc.analyze_terrain(
        elev_data["elevation_matrix"],
        elev_data["center_elevation"],
        slope_data["center_slope_deg"],
        elev_data["relief"]
    )

    return jsonify({
        "success": True,
        "lat": lat,
        "lon": lon,
        "terrain": terrain_data
    })

@api_bp.route('/risk', methods=['GET'])
def risk():
    lat, lon, err = parse_lat_lon(request)
    if err:
        return jsonify({"success": False, "error": err}), 400

    weights = parse_weights(request)
    elev_data = elevation_svc.fetch_elevation_grid(lat, lon, grid_size=9)
    slope_data = slope_svc.calculate_slope(elev_data["elevation_matrix"], elev_data["lats"], elev_data["lons"])
    rain_data = rainfall_svc.fetch_rainfall_data(lat, lon)
    terrain_data = terrain_svc.analyze_terrain(
        elev_data["elevation_matrix"],
        elev_data["center_elevation"],
        slope_data["center_slope_deg"],
        elev_data["relief"]
    )

    nearby = historical_svc.get_nearby(lat, lon, radius_km=150)
    nearest_km = nearby[0]["distance_km"] if nearby else None

    risk_result = risk_engine.calculate_score(
        slope_score=slope_data["slope_score"],
        rainfall_score=rain_data["rainfall_score"],
        terrain_score=terrain_data["terrain_score"],
        custom_weights=weights,
        historical_count=len(nearby),
        nearest_historical_km=nearest_km,
        rainfall_intensity=rain_data.get("max_hourly_intensity_mm"),
        data_quality={
            "elevation_fallback": elev_data.get("is_fallback", False),
            "rainfall_fallback": rain_data.get("is_fallback", False),
            "rainfall_simulation": rain_data.get("is_simulation", False),
        }
    )

    ml_result = ml_predictor.predict(
        slope_deg=slope_data["center_slope_deg"],
        rainfall_mm=rain_data["total_7day_mm"],
        elevation_m=elev_data["center_elevation"]
    ) if ml_predictor.available else None
    if ml_result:
        risk_result["ml_prediction"] = ml_result

    return jsonify({
        "success": True,
        "lat": lat,
        "lon": lon,
        "risk": risk_result
    })

@api_bp.route('/historical', methods=['GET'])
def historical():
    lat, lon, err = parse_lat_lon(request)
    radius_km = float(request.args.get('radius', 300))

    if err:
        # Return all catalog records if coordinates omitted
        records = historical_svc.get_all()
        return jsonify({
            "success": True,
            "count": len(records),
            "records": records,
            "geojson": historical_svc.to_geojson(records)
        })

    nearby = historical_svc.get_nearby(lat, lon, radius_km=radius_km)
    return jsonify({
        "success": True,
        "lat": lat,
        "lon": lon,
        "radius_km": radius_km,
        "count": len(nearby),
        "records": nearby,
        "geojson": historical_svc.to_geojson(nearby)
    })

# ================= WEB TEMPLATE ROUTES =================

@web_bp.route('/')
def home():
    return render_template('index.html', demo_locations=Config.DEMO_LOCATIONS)

@web_bp.route('/favicon.ico')
def favicon():
    return ('', 204)

@web_bp.route('/about')
def about():
    return render_template('about.html')

@web_bp.route('/methodology')
def methodology():
    return render_template('methodology.html')

@web_bp.route('/data-sources')
def data_sources():
    return render_template('data_sources.html')
