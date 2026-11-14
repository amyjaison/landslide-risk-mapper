/**
 * Interactive GIS Map Module for Landslide Risk Mapper
 * Built with Leaflet.js
 */

const MapModule = (() => {
  let map = null;
  let currentMarker = null;

  // Layer groups for independent toggling
  const layers = {
    vulnerabilityGrid: L.layerGroup(),
    slopeGrid: L.layerGroup(),
    rainfallGrid: L.layerGroup(),
    terrainGrid: L.layerGroup(),
    historicalLandslides: L.layerGroup()
  };

  // Base tile layers
  const baseMaps = {
    "OpenStreetMap Standard": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }),
    "OpenTopoMap (Topography)": L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      maxZoom: 17,
      attribution: 'Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap'
    }),
    "Esri Satellite Imagery": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }),
    "CartoDB Positron (Clean)": L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 20,
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    })
  };

  function initMap(centerLat = 11.5273, centerLon = 76.1264, zoom = 12) {
    if (map) return map;

    map = L.map('map-view', {
      center: [centerLat, centerLon],
      zoom: zoom,
      layers: [baseMaps["OpenTopoMap (Topography)"], layers.vulnerabilityGrid, layers.historicalLandslides],
      zoomControl: true
    });

    // Layer control for switching basemaps and toggling individual thematic layers
    const overlays = {
      "<span style='font-weight:700; color:#b91c1c;'>⚠️ Combined Vulnerability Grid</span>": layers.vulnerabilityGrid,
      "⛰️ Slope Analysis Layer": layers.slopeGrid,
      "🌧️ Rainfall Isohyet Layer": layers.rainfallGrid,
      "🗺️ Terrain & Elevation Layer": layers.terrainGrid,
      "📍 Historical Landslides (NASA GLC)": layers.historicalLandslides
    };

    L.control.layers(baseMaps, overlays, { collapsed: false, position: 'topright' }).addTo(map);

    // Click anywhere on map to analyze that location
    map.on('click', (e) => {
      const { lat, lng } = e.latlng;
      if (window.DashboardModule) {
        window.DashboardModule.analyzeCoordinates(lat, lng, `Custom Point (${lat.toFixed(4)}, ${lng.toFixed(4)})`);
      }
    });

    return map;
  }

  function setLocationMarker(lat, lon, label) {
    if (!map) return;
    if (currentMarker) {
      map.removeLayer(currentMarker);
    }

    const pinIcon = L.divIcon({
      className: 'custom-map-pin',
      html: `
        <div style="
          background: #1b4332;
          border: 3px solid #ffffff;
          box-shadow: 0 4px 10px rgba(0,0,0,0.35);
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          font-size: 16px;
        ">🎯</div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    currentMarker = L.marker([lat, lon], { icon: pinIcon }).addTo(map);
    currentMarker.bindPopup(`<b>${label || 'Selected Location'}</b><br>Lat: ${lat.toFixed(4)}<br>Lon: ${lon.toFixed(4)}`).openPopup();
  }

  function renderGridLayers(gridGeojson) {
    layers.vulnerabilityGrid.clearLayers();
    layers.slopeGrid.clearLayers();
    layers.rainfallGrid.clearLayers();
    layers.terrainGrid.clearLayers();

    if (!gridGeojson || !gridGeojson.features) return;

    // 1. Combined Vulnerability Layer
    L.geoJSON(gridGeojson, {
      style: (feature) => {
        const score = feature.properties.vulnerability_score;
        let fillColor = '#22c55e';
        if (score > 75) fillColor = '#ef4444';
        else if (score > 50) fillColor = '#f97316';
        else if (score > 25) fillColor = '#eab308';

        return {
          fillColor: fillColor,
          weight: 1,
          opacity: 0.8,
          color: '#ffffff',
          fillOpacity: 0.65
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties;
        layer.bindTooltip(`
          <div style="font-size:0.8rem; line-height:1.4;">
            <strong>${p.risk_level}</strong><br>
            Composite Score: <b>${p.vulnerability_score}/100</b><br>
            Slope: ${p.slope_deg}° | Elev: ${p.elevation}m<br>
            72h Rain: ${p.rainfall_mm}mm
          </div>
        `, { sticky: true });

        layer.on('click', () => {
          if (window.DashboardModule) {
            window.DashboardModule.analyzeCoordinates(p.lat, p.lon, `Grid Cell (${p.lat.toFixed(4)}, ${p.lon.toFixed(4)})`);
          }
        });
      }
    }).addTo(layers.vulnerabilityGrid);

    // 2. Slope Thematic Layer
    L.geoJSON(gridGeojson, {
      style: (feature) => {
        const deg = feature.properties.slope_deg;
        let color = '#22c55e'; // 0-15 Low
        if (deg > 45) color = '#7f1d1d'; // Extreme
        else if (deg > 30) color = '#ea580c'; // High
        else if (deg > 15) color = '#eab308'; // Moderate

        return {
          fillColor: color,
          weight: 1,
          opacity: 0.7,
          color: '#334155',
          fillOpacity: 0.55
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties;
        layer.bindTooltip(`Slope: <b>${p.slope_deg}°</b> (Score: ${p.slope_score})`, { sticky: true });
      }
    }).addTo(layers.slopeGrid);

    // 3. Rainfall Isohyet Layer
    L.geoJSON(gridGeojson, {
      style: (feature) => {
        const rain = feature.properties.rainfall_mm;
        let color = '#bae6fd';
        if (rain > 150) color = '#1e3a8a';
        else if (rain > 75) color = '#0284c7';
        else if (rain > 25) color = '#38bdf8';

        return {
          fillColor: color,
          weight: 1,
          opacity: 0.6,
          color: '#ffffff',
          fillOpacity: 0.5
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties;
        layer.bindTooltip(`72h Rain: <b>${p.rainfall_mm} mm</b> (Score: ${p.rainfall_score})`, { sticky: true });
      }
    }).addTo(layers.rainfallGrid);

    // 4. Terrain & Hypsometric Relief Layer
    L.geoJSON(gridGeojson, {
      style: (feature) => {
        const elev = feature.properties.elevation;
        let color = '#a3e635'; // Low elevation
        if (elev > 2500) color = '#f8fafc'; // Alpine snow peak
        else if (elev > 1800) color = '#78350f'; // High mountain
        else if (elev > 1000) color = '#b45309'; // Moderate mountain
        else if (elev > 500) color = '#d97706'; // Hills / Uplands
        else if (elev > 200) color = '#84cc16'; // Rolling plain

        return {
          fillColor: color,
          weight: 1,
          opacity: 0.65,
          color: '#475569',
          fillOpacity: 0.55
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties;
        layer.bindTooltip(`Elevation: <b>${p.elevation} m</b> | Terrain Score: <b>${p.terrain_score}</b>`, { sticky: true });
      }
    }).addTo(layers.terrainGrid);
  }

  function renderHistoricalLandslides(records) {
    layers.historicalLandslides.clearLayers();
    if (!records || !records.length) return;

    records.forEach((rec) => {
      const lat = rec.lat;
      const lon = rec.lon;
      if (lat === undefined || lon === undefined) return;

      const hazardIcon = L.divIcon({
        className: 'historical-landslide-marker',
        html: `
          <div style="
            background: #b91c1c;
            color: #ffffff;
            border: 2px solid #ffffff;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
            cursor: pointer;
          " title="${rec.name}">⚠️</div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const distInfo = rec.distance_km !== undefined ? `<br><b>Distance to Focus:</b> ${rec.distance_km} km` : '';
      const popupHtml = `
        <div style="max-width: 280px; font-size: 0.82rem; line-height: 1.4;">
          <h4 style="margin: 0 0 6px 0; color: #991b1b; font-size: 0.95rem;">${rec.name}</h4>
          <b>Date:</b> ${rec.date}<br>
          <b>Location:</b> ${rec.region || rec.country}<br>
          <b>Trigger:</b> ${rec.trigger}<br>
          <b>Classification:</b> ${rec.landslide_category || rec.hazard_type}<br>
          <b>Impact:</b> ${rec.fatalities || 0} Fatalities, ${rec.injuries || 0} Injuries<br>
          <b>Data Source:</b> ${rec.source}${distInfo}
          <p style="margin: 6px 0 0 0; font-size: 0.78rem; color: #475569;">${rec.description || ''}</p>
        </div>
      `;

      L.marker([lat, lon], { icon: hazardIcon })
        .bindPopup(popupHtml)
        .addTo(layers.historicalLandslides);
    });
  }

  function setView(lat, lon, zoom = 12) {
    if (map) {
      map.flyTo([lat, lon], zoom, { duration: 1.2 });
    }
  }

  return {
    initMap,
    setLocationMarker,
    renderGridLayers,
    renderHistoricalLandslides,
    setView
  };
})();

window.MapModule = MapModule;

