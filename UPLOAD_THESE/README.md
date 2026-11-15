# Landslide Risk Mapper — Web-Based GIS Geospatial Tool

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/framework-Flask-black.svg)](https://flask.palletsprojects.com/)
[![Leaflet.js](https://img.shields.io/badge/gis-Leaflet.js-brightgreen.svg)](https://leafletjs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end interactive Geographic Information System (GIS) and multi-criteria vulnerability assessment platform designed for disaster management agencies, civil protection teams, and regional planners. The platform ingests elevation rasters (SRTM / ALOS DEM), antecedent precipitation (CHIRPS / Open-Meteo), and historical landslide archives (NASA Global Landslide Catalog) to compute normalized landslide vulnerability indices on an interactive map.

---

## 1. Project Overview

- **Project Name:** Landslide Risk Mapper
- **Problem Statement:** In mountainous and hilly landscapes, extreme precipitation events trigger catastrophic shallow debris flows, translational slides, and mudflows. Public safety officials often lack lightweight, interactive screening tools that rapidly fuse local slope gradients, antecedent rainfall saturation, and terrain morphometry into transparent, actionable hazard indices.
- **Solution:** A responsive full-stack GIS web application featuring 2D gradient slope calculations using finite differences, dynamic rainfall tracking (72h antecedent saturation, 24h peak bursts), configurable multi-criteria weighted overlay calculations, interactive spatial GeoJSON layers, and proximity lookups against documented NASA Global Landslide Catalog events.

---

## 2. Key Features

- **Interactive Full-Screen GIS Map:**
  - Powered by Leaflet.js with multi-basemap support (OpenTopoMap, Esri Satellite Imagery, OpenStreetMap, CartoDB Positron).
  - Click-anywhere inspection: clicking any coordinate triggers instant local elevation, slope, and vulnerability analysis.
  - Color-coded thematic risk overlays: Low (Green), Moderate (Yellow), High (Orange), Very High (Red).
- **2D Gradient Slope Analysis:**
  - Reads digital elevation models using `rasterio` and computes slope in degrees: $\theta = \arctan(\sqrt{(dz/dx)^2 + (dz/dy)^2}) \times \frac{180}{\pi}$.
  - Classifies slopes into standard geomechanical bins:
    - 0–15°: Gentle / Low slope
    - 15–30°: Moderate slope
    - 30–45°: High slope (critical threshold for shallow debris flows)
    - >45°: Very high / cliff face (rockfall and catastrophic detachment)
  - Exports local GeoTIFF elevation rasters.
- **Antecedent Rainfall & Pore-Pressure Tracking:**
  - Ingests 72-hour antecedent precipitation, 24-hour peak bursts, and 7-day cumulative hyetographs from satellite reanalysis.
  - Derived rainfall intensity indicator and pore-pressure hazard scoring.
  - Dual-mode operation: Live satellite observations vs. Documented Disaster Peak Simulation (e.g. July 2024 Wayanad 372 mm downpour).
- **Terrain Morphometry & Ruggedness:**
  - Topographic Roughness Index (TRI) following Riley et al.
  - Geomorphic classification (Alpine Peaks, Mountain Escarpments, Dissected Ravines, Rolling Uplands, Alluvial Plains).
- **Weighted Overlay Landslide Vulnerability Engine:**
  - Formula:
    $$\text{Vulnerability Score} = (\text{Slope Score} \times 0.40) + (\text{Rainfall Score} \times 0.35) + (\text{Terrain Score} \times 0.25)$$
  - Continuous normalization to 0–100 with dynamic weight adjustment sliders in the UI.
  - Transparent narrative explanation detailing the primary hazard driver and contributing factor points.
- **NASA Global Landslide Catalog Ground-Truthing:**
  - Historical records with dates, triggers, fatalities, and distances from the queried location.
- **Location Geocoder & Demo Scenarios:**
  - Auto-suggest search for cities, villages, districts, or decimal coordinates (e.g. `11.53, 76.13`).
  - One-click presets: Wayanad (Kerala), Kedarnath (Uttarakhand), Shimla (Himachal Pradesh), Oso (Washington), and New Delhi Plains (low-risk control baseline).

---

## 3. Technology Stack

- **Backend:**
  - Python 3.11 (the version Render uses)
  - Flask 3.1.3 (RESTful API & Web Application)
  - Flask-CORS 6.0.5
  - Rasterio 1.4.3 (GeoTIFF generation, geospatial affine transforms, CRS handling)
  - GeoPandas 1.0.1 & Shapely 2.0.7 (Vector geometry, GeoJSON feature collections)
  - NumPy 2.0.2 & SciPy 1.13.1 (2D gradient calculations, hypsometric interpolation)
  - Pandas 2.3.3
  - Requests 2.32.5 (External API client with disk caching)
- **Frontend:**
  - HTML5 & CSS3 (Custom earth-tone theme, responsive grid)
  - Vanilla JavaScript (ES6+ modular architecture)
  - Leaflet.js 1.9.4 (Interactive GIS mapping, custom overlays, tooltips)
  - Chart.js 4.4.1 (Factor contribution bar chart, 7-day rainfall hyetograph)
- **Geospatial Data Sources:**
  - Shuttle Radar Topography Mission (SRTM) & ALOS DEM
  - Open-Meteo Precipitation & Weather API (CHIRPS / ERA5 reanalysis)
  - NASA Global Landslide Catalog (GLC)
  - OpenStreetMap & OpenTopoMap Cartographic Basemaps

---

## 4. System Architecture

```
                    ┌───────────────────────────────────────────────┐
                    │               Browser Client                  │
                    │   (Leaflet.js + Chart.js + Dynamic Dashboard) │
                    └───────────────────────┬───────────────────────┘
                                            │ HTTP / JSON API
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │          Flask Application (app.py)           │
                    │       Routes & Controller (routes.py)         │
                    └───────────────────────┬───────────────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
│     Elevation &       │       │       Rainfall        │       │   Historical Data     │
│   Slope Services      │       │       Service         │       │       Service         │
│ (elevation.py,        │       │ (rainfall_analysis.py)│       │ (historical_data.py)  │
│  slope_analysis.py)   │       └───────────┬───────────┘       └───────────┬───────────┘
└───────────┬───────────┘                   │                               │
            │                               │                               │
            ▼                               ▼                               ▼
    Rasterio GeoTIFF /              Open-Meteo Live /                   NASA GLC
       SRTM Grids                 CHIRPS Satellite Data              GeoJSON Records
            │                               │                               │
            └───────────────────────┬───────┴───────────────────────────────┘
                                    ▼
                    ┌───────────────────────────────────────────────┐
                    │   Risk Calculation Engine (risk_calculation)  │
                    │   - Weighted Overlay: 40% Slope, 35% Rain,    │
                    │     25% Terrain                               │
                    │   - Classification: Low/Mod/High/Very High    │
                    │   - Factor Contribution Breakdown & Rationale │
                    └───────────────────────────────────────────────┘
```

---

## 5. Folder Structure

```
landslide-risk-mapper/
├── app.py                      # Flask application entry point
├── config.py                   # Central configuration & threshold definitions
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive documentation
├── .env.example                # Environment configuration template
│
├── backend/
│   ├── __init__.py
│   ├── routes.py               # REST API endpoints & HTML page routes
│   ├── data_loader.py          # Unified GIS orchestration pipeline & search
│   ├── elevation.py            # SRTM DEM retrieval & Rasterio GeoTIFF generation
│   ├── slope_analysis.py       # 2D gradient slope calculations & classification
│   ├── rainfall_analysis.py    # 72h antecedent rainfall & intensity indicator
│   ├── terrain_analysis.py     # Topographic Roughness Index & landform morphometry
│   ├── risk_calculation.py     # Multi-criteria weighted overlay engine
│   └── historical_data.py      # NASA Global Landslide Catalog queries
│
├── frontend/
│   ├── templates/
│   │   ├── index.html          # Main GIS interactive dashboard
│   │   ├── about.html          # Problem statement & solution overview
│   │   ├── methodology.html    # Formula, mathematics & scientific rationale
│   │   └── data_sources.html   # Geospatial dataset documentation
│   │
│   └── static/
│       ├── css/
│       │   └── style.css       # Earth-tone responsive styling
│       ├── js/
│       │   ├── map.js          # Leaflet map, layer toggles & popups
│       │   ├── dashboard.js    # Location search, sliders & metrics controller
│       │   └── charts.js       # Chart.js visualization components
│       └── images/
│
├── data/
│   ├── elevation/              # Cached DEM GeoTIFF rasters (.tif)
│   ├── rainfall/               # Cached precipitation responses (.json)
│   ├── historical/             # NASA GLC historical dataset (nasa_glc_records.json)
│   └── sample/                 # Pre-computed offline demonstration benchmarks
│
└── tests/
    ├── test_risk.py            # Unit tests for weighted overlay & categories
    ├── test_slope.py           # Unit tests for 2D slope finite differences
    └── test_api.py             # Integration tests for all Flask API endpoints
```

---

## 6. Mathematical Methodology & Risk Classification

### Weighted Overlay Formula
$$\text{Landslide Vulnerability Score} = (S_{\text{slope}} \times w_{\text{slope}}) + (S_{\text{rainfall}} \times w_{\text{rainfall}}) + (S_{\text{terrain}} \times w_{\text{terrain}})$$

- Default Weights: $w_{\text{slope}} = 0.40$, $w_{\text{rainfall}} = 0.35$, $w_{\text{terrain}} = 0.25$ ($w_s + w_r + w_t = 1.0$)
- All factor scores are normalized to $[0, 100]$.

### Risk Classification Tiers

| Score Range | Category | Color | Geotechnical Meaning |
|---|---|---|---|
| **0 – 25.0** | **Low Risk** | Green (`#22c55e`) | Gentle relief, minimal shear stress, low antecedent moisture. Stable baseline. |
| **>25.0 – 50.0** | **Moderate Risk** | Yellow (`#eab308`) | Moderate gradient or rainfall accumulation; conditional stability under prolonged rain. |
| **>50.0 – 75.0** | **High Risk** | Orange (`#f97316`) | Steep slopes exceeding soil friction angles; high saturation and elevated pore pressure. |
| **>75.0 – 100.0** | **Very High Risk** | Red (`#ef4444`) | Precipitous terrain and torrential rainfall; critical screening alert for rapid mass wasting. |

---

## 7. Installation Instructions

### Prerequisites
- Python 3.11 (the version pinned in .python-version; newer versions may fail to install the pinned packages)
- `pip` package manager
- Internet access for initial package downloads and live API queries (offline fallback active if offline)

### macOS / Linux Installation

```bash
# 1. Clone or navigate to the project directory
cd /path/to/landslide-risk-mapper

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows Installation (PowerShell / Command Prompt)

```powershell
# 1. Navigate to the project directory
cd C:\path\to\landslide-risk-mapper

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 8. How to Run the Application

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Start the Flask web application
python app.py
```

The application will start on:
- **Local URL:** `http://127.0.0.1:5050`
- **Network URL:** `http://0.0.0.0:5050`

Open your web browser and navigate to `http://127.0.0.1:5050`.

---

## 9. REST API Documentation

| Endpoint | Method | Query Parameters | Description |
|---|---|---|---|
| `/api/health` | `GET` | None | Service status, version, and active default weights. |
| `/api/search` | `GET` | `location` (string) | Reverse geocoding via Nominatim & curated presets. |
| `/api/demo-locations` | `GET` | None | Curated demo sites with descriptions and expected risk. |
| `/api/location` | `GET` | `lat`, `lon`, `w_slope`, `w_rain`, `w_terrain`, `weather_mode`, `radius` | Full analysis: elevation, slope, rainfall, terrain, risk score, GeoJSON grid, and nearby historical slides. |
| `/api/slope` | `GET` | `lat`, `lon` | Local elevation profile, 2D slope angle, and classification. |
| `/api/rainfall` | `GET` | `lat`, `lon`, `weather_mode` | 24h/48h/72h rainfall, 7-day hyetograph, and intensity indicator. |
| `/api/terrain` | `GET` | `lat`, `lon` | Elevation, relief, Topographic Roughness Index (TRI), and morphometry. |
| `/api/risk` | `GET` | `lat`, `lon`, `w_slope`, `w_rain`, `w_terrain` | Weighted overlay vulnerability score and detailed explanation. |
| `/api/historical` | `GET` | `lat`, `lon`, `radius` | Proximity search across the NASA Global Landslide Catalog. |

---

## 10. Automated Testing

Run the automated test suite covering unit calculations, slope finite difference gradients, and Flask API routes:

```bash
./venv/bin/python -m unittest discover tests
```

Expected output:
```
Ran 16 tests in 0.095s

OK
```

---

## 11. Hackathon Demonstration Guide (For Judges)

1. **Open the Dashboard:** Navigate to `http://127.0.0.1:5050`.
2. **Explore Preset Scenarios:**
   - Use the **"⚡ Quick Demo Scenarios"** dropdown in the top navbar:
     - **Wayanad, Kerala (High Risk / 67.0):** Observe the steep Western Ghats escarpment slopes and historical twin landslides from July 2024.
     - **Kedarnath, Uttarakhand (Very High Risk / 79.6):** Observe glaciated high Himalayan relief exceeding 3,500m with 44° valley flank slopes.
     - **New Delhi Plains (Low Risk / 4.0):** Observe flat alluvial terrain with low slope (<2°) confirming the baseline safety validation.
3. **Toggle Precipitation Scenarios:**
   - In the map toolbar, switch between:
     - **"🔴 Disaster Peak / Monsoon Event"**: Uses documented disaster rainfall benchmarks (e.g. 370 mm monsoon cloudburst).
     - **"🟢 Live Satellite Observations"**: Queries real-time Open-Meteo satellite observations for today's weather.
4. **Interact with Map Layers:**
   - In the top-right Leaflet layer control, toggle the **Combined Vulnerability Grid**, **Slope Analysis Layer**, **Rainfall Layer**, and **Historical Landslides (NASA GLC)** independently.
   - Switch basemaps to **Esri Satellite Imagery** or **OpenTopoMap**.
   - Click anywhere on the map to trigger an on-the-fly multi-criteria calculation for that custom point.
5. **Adjust Weights in Real-Time:**
   - In the right sidebar, adjust the **Slope**, **Rainfall**, and **Terrain** sliders and watch the risk score, factor contribution bars, and Chart.js graphs recalculate live.

---

## 12. Limitations & Responsible Use

> **CRITICAL DISCLAIMER:** The Landslide Risk Mapper is a screening-level GIS decision-support tool. It computes multi-criteria spatial vulnerability indices from satellite elevation and regional rainfall reanalysis. It is **NOT** a site-specific geotechnical deterministic model and **DOES NOT** predict the exact date, time, or localized occurrence of slope failure. It does not replace on-site geological borehole surveys, inclinometer instrumentation, or official warnings from national meteorological or geological agencies (e.g., GSI, IMD, USGS).



## 13. Model Improvements (v2.0)

The risk engine has been upgraded from a plain weighted sum to an **interaction-aware susceptibility model** while preserving the original API and dashboard.

### What was improved
- **Continuous slope susceptibility curve:** avoids abrupt score changes at category boundaries and better distinguishes shallow-slide/debris-flow slopes from very steep rock faces.
- **Slope × rainfall trigger synergy:** adds a small, capped interaction term only when both factors are elevated.
- **Peak-intensity adjustment:** high short-duration rainfall receives a bounded trigger bonus.
- **Historical evidence:** nearby documented landslides are used as supporting evidence based primarily on distance; the effect is capped.
- **Data-quality confidence:** every full analysis reports a confidence score/label based on live vs fallback/simulated inputs.
- **Rainfall observation handling:** the live API path now uses completed daily observations rather than mixing a partial current day with forecast values.
- **Backward-compatible API:** existing `vulnerability_score`, `risk_level`, `factor_scores`, `factor_contributions`, and map GeoJSON fields remain available.

### Important accuracy note
This project does **not** claim a statistically validated percentage accuracy because the supplied repository contains a small curated historical catalog rather than a sufficiently large labelled training dataset with matched terrain and rainfall observations. The v2 changes therefore improve physical consistency, robustness, transparency, and calibration without pretending that a synthetic label set is ground truth.


## Real ML upgrade
A trainable Random Forest module is included under `ml_model/`. Run `python ml_model/train_model.py` to download the cited Mendeley dataset, train and validate the model, and create the runtime artifact. The existing transparent risk engine remains available as a fallback.

## 14. Stage 2 Phase 1 Deployment

This repository is prepared for deployment as a Flask Web Service. The production server uses Gunicorn. See `DEPLOYMENT.md` for the exact GitHub and Render steps.

Before publishing, run `python ml_model/train_model.py` and commit the generated files in `ml_model/artifacts/` so the deployed application uses the trained Random Forest model.
