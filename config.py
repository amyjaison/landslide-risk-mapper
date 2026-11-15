import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')  # set SECRET_KEY on Render
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'  # off unless FLASK_DEBUG=1
    PORT = int(os.environ.get('PORT', 5050))
    HOST = os.environ.get('HOST', '0.0.0.0')

    # Data directories
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    ELEVATION_DIR = os.path.join(DATA_DIR, 'elevation')
    RAINFALL_DIR = os.path.join(DATA_DIR, 'rainfall')
    HISTORICAL_DIR = os.path.join(DATA_DIR, 'historical')
    SAMPLE_DIR = os.path.join(DATA_DIR, 'sample')
    CACHE_DIR = os.path.join(DATA_DIR, 'cache')

    # Weighted Overlay Weights (Must sum to 1.0)
    WEIGHT_SLOPE = float(os.environ.get('WEIGHT_SLOPE', 0.40))
    WEIGHT_RAINFALL = float(os.environ.get('WEIGHT_RAINFALL', 0.35))
    WEIGHT_TERRAIN = float(os.environ.get('WEIGHT_TERRAIN', 0.25))

    # Risk Categories
    RISK_LEVELS = [
        {"name": "Low Risk", "min": 0, "max": 25, "color": "#22c55e", "code": "LOW", "description": "Terrain is stable with gentle slopes and low recent rainfall."},
        {"name": "Moderate Risk", "min": 26, "max": 50, "color": "#eab308", "code": "MODERATE", "description": "Moderate slope or rainfall. Precautionary monitoring advised during monsoons."},
        {"name": "High Risk", "min": 51, "max": 75, "color": "#f97316", "code": "HIGH", "description": "Steep slopes combined with elevated rainfall. Significant susceptibility to slope instability."},
        {"name": "Very High Risk", "min": 76, "max": 100, "color": "#ef4444", "code": "VERY_HIGH", "description": "Extremely steep gradients and heavy precipitation. Immediate hazard screening alert."}
    ]

    # Slope Classification
    SLOPE_CLASSES = [
        {"name": "Gentle / Low (0–15°)", "min": 0, "max": 15, "score": 15, "color": "#22c55e", "description": "Flat to gently undulating; minimal gravitational shear stress."},
        {"name": "Moderate (15–30°)", "min": 15, "max": 30, "score": 45, "color": "#eab308", "description": "Rolling hills; vulnerability increases significantly if soil is saturated."},
        {"name": "High (30–45°)", "min": 30, "max": 45, "score": 80, "color": "#f97316", "description": "Steep mountain slopes; critical threshold for shallow debris flows."},
        {"name": "Very High (>45°)", "min": 45, "max": 90, "score": 100, "color": "#ef4444", "description": "Cliff and precipitous faces; high risk of rockfalls and rapid mass wasting."}
    ]

    # Curated Demonstration Locations for Hackathon judges
    DEMO_LOCATIONS = [
        {
            "id": "wayanad",
            "name": "Wayanad (Chooralmala / Meppadi), Kerala, India",
            "lat": 11.5273,
            "lon": 76.1264,
            "region": "Western Ghats, India",
            "description": "Epicenter of catastrophic 2024 debris flows triggered by extreme monsoon rainfall (over 300 mm in 24 hrs) on steep tropical slopes.",
            "expected_risk": "Very High Risk"
        },
        {
            "id": "kedarnath",
            "name": "Kedarnath, Uttarakhand, India",
            "lat": 30.7346,
            "lon": 79.0669,
            "region": "Garhwal Himalayas, India",
            "description": "High altitude glaciated Himalayan valley subject to extreme orographic rain, steep moraines, and flash floods (2013 tragedy).",
            "expected_risk": "Very High Risk"
        },
        {
            "id": "shimla",
            "name": "Shimla & Solan, Himachal Pradesh, India",
            "lat": 31.1048,
            "lon": 77.1734,
            "region": "Lower Himalayas, India",
            "description": "Densely populated hilly urban center prone to slope failures along road cuts and saturated clayey soils during monsoon.",
            "expected_risk": "High Risk"
        },
        {
            "id": "oso",
            "name": "Oso Landslide Site, Washington, USA",
            "lat": 48.2825,
            "lon": -121.8486,
            "region": "Cascade Foothills, USA",
            "description": "Site of the deadliest single landslide event in US history (2014) involving river undercutting and glacial sediments.",
            "expected_risk": "High Risk"
        },
        {
            "id": "delhi",
            "name": "New Delhi / NCR Plains, India",
            "lat": 28.6139,
            "lon": 77.2090,
            "region": "Indo-Gangetic Plain",
            "description": "Alluvial low-lying flat terrain, demonstrating screening-level Low Risk baseline validation.",
            "expected_risk": "Low Risk"
        }
    ]
