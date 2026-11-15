/**
 * Main Dashboard Controller for Landslide Risk Mapper
 * Random Forest ML Version
 */

const DashboardModule = (() => {

  let currentLat = 11.5273;
  let currentLon = 76.1264;
  let currentPlaceName = "Wayanad (Chooralmala / Meppadi), Kerala";
  let currentWeatherMode = "monsoon_event";
  let searchDebounceTimer = null;

  // ---------------------------------------------------------
  // INITIALIZE
  // ---------------------------------------------------------

  function init() {
    setupEventListeners();

    if (
      window.MapModule &&
      typeof window.MapModule.initMap === "function"
    ) {
      window.MapModule.initMap(currentLat, currentLon, 12);
    }

    analyzeCoordinates(
      currentLat,
      currentLon,
      currentPlaceName
    );
  }

  // ---------------------------------------------------------
  // EVENT LISTENERS
  // ---------------------------------------------------------

  function setupEventListeners() {

    // Search
    const searchInput =
      document.getElementById("search-input");

    const suggestionsBox =
      document.getElementById("search-suggestions");

    if (searchInput) {

      searchInput.addEventListener("input", function (event) {

        clearTimeout(searchDebounceTimer);

        const query =
          event.target.value.trim();

        if (query.length < 2) {

          if (suggestionsBox) {
            suggestionsBox.style.display = "none";
          }

          return;
        }

        searchDebounceTimer = setTimeout(
          function () {
            fetchSearchSuggestions(query);
          },
          300
        );
      });

      searchInput.addEventListener("keydown", function (event) {

        if (event.key !== "Enter") {
          return;
        }

        event.preventDefault();

        const query =
          searchInput.value.trim();

        if (!query) {
          return;
        }

        clearTimeout(searchDebounceTimer);

        if (suggestionsBox) {
          suggestionsBox.style.display = "none";
        }

        executeImmediateSearch(query);
      });
    }

    // Close suggestions
    document.addEventListener("click", function (event) {

      if (
        suggestionsBox &&
        !suggestionsBox.contains(event.target) &&
        event.target !== searchInput
      ) {
        suggestionsBox.style.display = "none";
      }
    });

    // Legend tabs
    const legendTabs =
      document.querySelectorAll(".legend-tab-btn");

    legendTabs.forEach(function (button) {

      button.addEventListener("click", function () {

        const targetType =
          button.getAttribute("data-legend");

        legendTabs.forEach(function (item) {
          item.classList.remove("active");
        });

        button.classList.add("active");

        document
          .querySelectorAll(".legend-panel")
          .forEach(function (panel) {
            panel.classList.remove("active");
          });

        const activePanel =
          document.getElementById(
            "legend-panel-" + targetType
          );

        if (activePanel) {
          activePanel.classList.add("active");
        }

        const titleMap = {
          risk: "Landslide Vulnerability",
          slope: "Slope Gradient Legend",
          rain: "Precipitation Legend",
          terrain: "Elevation & Relief"
        };

        const titleElement =
          document.getElementById(
            "legend-active-title"
          );

        if (
          titleElement &&
          titleMap[targetType]
        ) {
          titleElement.textContent =
            titleMap[targetType];
        }
      });
    });

    // Demo scenarios
    const demoSelect =
      document.getElementById(
        "demo-scenario-select"
      );

    if (demoSelect) {

      demoSelect.addEventListener(
        "change",
        function (event) {

          const value =
            event.target.value;

          if (!value) {
            return;
          }

          const parts =
            value.split("|");

          const lat =
            parseFloat(parts[0]);

          const lon =
            parseFloat(parts[1]);

          const name =
            parts.slice(2).join("|");

          if (
            Number.isNaN(lat) ||
            Number.isNaN(lon)
          ) {
            return;
          }

          analyzeCoordinates(
            lat,
            lon,
            name
          );
        }
      );
    }

    // Weather mode
    const weatherModeSelect =
      document.getElementById(
        "weather-mode-select"
      );

    if (weatherModeSelect) {

      weatherModeSelect.addEventListener(
        "change",
        function (event) {

          currentWeatherMode =
            event.target.value;

          analyzeCoordinates(
            currentLat,
            currentLon,
            currentPlaceName
          );
        }
      );
    }
  }

  // ---------------------------------------------------------
  // LOADING
  // ---------------------------------------------------------

  function showLoading(show) {

    const overlay =
      document.getElementById(
        "loading-overlay"
      );

    if (overlay) {
      overlay.style.display =
        show ? "flex" : "none";
    }
  }

  // ---------------------------------------------------------
  // SEARCH SUGGESTIONS
  // ---------------------------------------------------------

  function fetchSearchSuggestions(query) {

    const suggestionsBox =
      document.getElementById(
        "search-suggestions"
      );

    fetch(
      "/api/search?location=" +
      encodeURIComponent(query)
    )
      .then(function (response) {

        if (!response.ok) {
          throw new Error(
            "HTTP error " + response.status
          );
        }

        return response.json();
      })

      .then(function (data) {

        if (
          !suggestionsBox ||
          !data.results ||
          data.results.length === 0
        ) {

          if (suggestionsBox) {
            suggestionsBox.style.display = "none";
          }

          return;
        }

        suggestionsBox.innerHTML = "";

        data.results.forEach(function (item) {

          const div =
            document.createElement("div");

          div.className = "search-item";

          const displayName =
            item.display_name || "Unknown location";

          const shortName =
            displayName.split(",")[0];

          div.innerHTML =
            "<strong>" +
            shortName +
            "</strong>" +
            "<span class=\"search-item-sub\">" +
            displayName +
            "</span>";

          div.addEventListener(
            "click",
            function () {

              const lat =
                parseFloat(item.lat);

              const lon =
                parseFloat(item.lon);

              if (
                Number.isNaN(lat) ||
                Number.isNaN(lon)
              ) {
                return;
              }

              const input =
                document.getElementById(
                  "search-input"
                );

              if (input) {
                input.value = shortName;
              }

              suggestionsBox.style.display =
                "none";

              analyzeCoordinates(
                lat,
                lon,
                displayName
              );
            }
          );

          suggestionsBox.appendChild(div);
        });

        suggestionsBox.style.display = "block";
      })

      .catch(function (error) {
        console.error(
          "Search error:",
          error
        );
      });
  }

  // ---------------------------------------------------------
  // SEARCH
  // ---------------------------------------------------------

  function executeImmediateSearch(query) {

    showLoading(true);

    fetch(
      "/api/search?location=" +
      encodeURIComponent(query)
    )
      .then(function (response) {

        if (!response.ok) {
          throw new Error(
            "HTTP error " + response.status
          );
        }

        return response.json();
      })

      .then(function (data) {

        showLoading(false);

        if (
          data.results &&
          data.results.length > 0
        ) {

          const top =
            data.results[0];

          analyzeCoordinates(
            parseFloat(top.lat),
            parseFloat(top.lon),
            top.display_name
          );

        } else {

          alert(
            'No locations found for "' +
            query +
            '". Try searching a city, mountain region, ' +
            'or coordinates such as "11.53, 76.13".'
          );
        }
      })

      .catch(function (error) {

        showLoading(false);

        console.error(
          "Search failed:",
          error
        );

        alert(
          "Search failed: " +
          error.message
        );
      });
  }

  // ---------------------------------------------------------
  // ANALYZE LOCATION
  // ---------------------------------------------------------

  function analyzeCoordinates(
    lat,
    lon,
    placeName
  ) {

    currentLat = parseFloat(lat);
    currentLon = parseFloat(lon);

    if (
      Number.isNaN(currentLat) ||
      Number.isNaN(currentLon)
    ) {

      alert(
        "Invalid latitude or longitude."
      );

      return;
    }

    if (placeName) {
      currentPlaceName = placeName;
    }

    showLoading(true);

    // No old 40/35/25 weights.
    // Random Forest ML score comes from the backend.

    const params =
      new URLSearchParams({
        lat: currentLat.toFixed(5),
        lon: currentLon.toFixed(5),
        weather_mode: currentWeatherMode
      });

    fetch(
      "/api/location?" +
      params.toString()
    )
      .then(function (response) {

        if (!response.ok) {
          throw new Error(
            "HTTP error " + response.status
          );
        }

        return response.json();
      })

      .then(function (payload) {

        showLoading(false);

        if (!payload.success) {
          throw new Error(
            payload.error ||
            "Failed to process location"
          );
        }

        const data =
          payload.data;

        updateDashboardUI(data);

        // Map
        if (
          window.MapModule &&
          typeof window.MapModule.setView === "function"
        ) {
          window.MapModule.setView(
            currentLat,
            currentLon,
            12
          );
        }

        if (
          window.MapModule &&
          typeof window.MapModule.setLocationMarker === "function"
        ) {
          window.MapModule.setLocationMarker(
            currentLat,
            currentLon,
            currentPlaceName
          );
        }

        if (
          window.MapModule &&
          typeof window.MapModule.renderGridLayers === "function" &&
          data.grid_geojson
        ) {
          window.MapModule.renderGridLayers(
            data.grid_geojson
          );
        }

        if (
          window.MapModule &&
          typeof window.MapModule.renderHistoricalLandslides === "function" &&
          data.historical
        ) {
          window.MapModule.renderHistoricalLandslides(
            data.historical.records || []
          );
        }

        // ---------------------------------------------------
        // CHARTS
        // ---------------------------------------------------

        // Environmental Factor Distribution
        updateEnvironmentalFactorChart(data);

        if (window.ChartsModule) {

          // Rainfall chart
          if (
            typeof window.ChartsModule
              .initOrUpdateRainfallChart === "function" &&
            data.rainfall
          ) {
            window.ChartsModule
              .initOrUpdateRainfallChart(
                data.rainfall.dates || [],
                data.rainfall.daily_precipitation || []
              );
          }

          // Regional risk distribution
          if (
            typeof window.ChartsModule
              .initOrUpdateRiskDistributionChart === "function" &&
            data.grid_geojson
          ) {
            window.ChartsModule
              .initOrUpdateRiskDistributionChart(
                data.grid_geojson.features || []
              );
          }
        }
      })

      .catch(function (error) {

        showLoading(false);

        console.error(
          "Analysis error:",
          error
        );

        alert(
          "Error processing location: " +
          error.message
        );
      });
  }

  // ---------------------------------------------------------
  // ENVIRONMENTAL FACTOR CHART
  // ---------------------------------------------------------

  function updateEnvironmentalFactorChart(data) {

    const canvas =
      document.getElementById("factor-chart");

    if (
      !canvas ||
      typeof Chart === "undefined"
    ) {
      return;
    }

    const factorScores =
      data.risk &&
      data.risk.factor_scores
        ? data.risk.factor_scores
        : {};

    const values = [
      Number(factorScores.slope || 0),
      Number(factorScores.rainfall || 0),
      Number(factorScores.terrain || 0)
    ];

    if (window.environmentFactorChart) {
      window.environmentFactorChart.destroy();
    }

    window.environmentFactorChart =
      new Chart(
        canvas,
        {
          type: "bar",

          data: {
            labels: [
              "Slope",
              "Rainfall",
              "Terrain"
            ],

            datasets: [
              {
                label: "Environmental Indicator",
                data: values,
                borderWidth: 1,
                borderRadius: 6
              }
            ]
          },

          options: {
            responsive: true,
            maintainAspectRatio: false,

            scales: {

              y: {
                beginAtZero: true,
                max: 100,

                title: {
                  display: true,
                  text: "Indicator Score"
                },

                ticks: {
                  stepSize: 20
                }
              },

              x: {
                grid: {
                  display: false
                }
              }
            },

            plugins: {

              legend: {
                display: false
              },

              tooltip: {

                callbacks: {

                  label: function (context) {

                    return (
                      " Score: " +
                      Number(context.raw).toFixed(1) +
                      "/100"
                    );
                  }
                }
              }
            }
          }
        }
      );
  }

  // ---------------------------------------------------------
  // UPDATE DASHBOARD
  // ---------------------------------------------------------

  // Warn the user whenever any input is estimated instead of measured.
  function updateDataNotice(data) {
    const box = document.getElementById("data-notice");
    if (!box) { return; }

    const notes = [];
    if (data.elevation && data.elevation.is_fallback) {
      notes.push(
        "Elevation could not be fetched, so an approximate offline " +
        "terrain model was used. The score may be inaccurate."
      );
    }
    if (data.rainfall && data.rainfall.is_fallback) {
      notes.push(
        "Live rainfall could not be fetched, so typical regional " +
        "rainfall was used."
      );
    }
    if (data.rainfall && data.rainfall.is_simulation) {
      notes.push(
        "Rainfall shown is a simulated disaster-peak scenario, " +
        "not current weather."
      );
    }

    if (notes.length) {
      box.textContent = "\u26A0\uFE0F " + notes.join(" ");
      box.style.display = "block";
    } else {
      box.textContent = "";
      box.style.display = "none";
    }
  }

  function updateDashboardUI(data) {

    updateDataNotice(data);

    // Location
    const locationName =
      document.getElementById(
        "dash-location-name"
      );

    if (locationName) {
      locationName.textContent =
        currentPlaceName;
    }

    const locationCoords =
      document.getElementById(
        "dash-location-coords"
      );

    if (
      locationCoords &&
      data.query
    ) {
      locationCoords.textContent =
        "Lat: " +
        Number(data.query.latitude).toFixed(5) +
        "° N, Lon: " +
        Number(data.query.longitude).toFixed(5) +
        "° E";
    }

    // -------------------------------------------------------
    // MAIN ML SCORE
    // -------------------------------------------------------

    const score =
      Number(
        data.risk &&
        data.risk.vulnerability_score
      ) || 0;

    const scoreElement =
      document.getElementById(
        "dash-risk-score"
      );

    if (scoreElement) {
      scoreElement.textContent =
        Math.round(score);

      scoreElement.style.color =
        data.risk.risk_color ||
        "#22c55e";
    }

    // Risk badge
    const badgeElement =
      document.getElementById(
        "dash-risk-badge"
      );

    if (badgeElement) {
      badgeElement.textContent =
        data.risk.risk_level ||
        "Unknown Risk";

      badgeElement.style.backgroundColor =
        data.risk.risk_color ||
        "#64748b";
    }

    // Meter
    const meterElement =
      document.getElementById(
        "dash-meter-fill"
      );

    if (meterElement) {

      meterElement.style.width =
        Math.min(
          100,
          Math.max(0, score)
        ) + "%";

      meterElement.style.backgroundColor =
        data.risk.risk_color ||
        "#22c55e";
    }

    // -------------------------------------------------------
    // ELEVATION
    // -------------------------------------------------------

    if (data.elevation) {

      const elevation =
        document.getElementById(
          "dash-elev"
        );

      if (elevation) {
        elevation.textContent =
          data.elevation.center_elevation_m +
          " m";
      }

      const relief =
        document.getElementById(
          "dash-relief"
        );

      if (relief) {
        relief.textContent =
          "Relief: ±" +
          data.elevation.relief_m +
          "m";
      }
    }

    // -------------------------------------------------------
    // SLOPE
    // -------------------------------------------------------

    if (data.slope) {

      const slope =
        document.getElementById(
          "dash-slope"
        );

      if (slope) {
        slope.textContent =
          data.slope.center_slope_deg +
          "°";
      }

      const slopeCategory =
        document.getElementById(
          "dash-slope-cat"
        );

      if (slopeCategory) {
        slopeCategory.textContent =
          data.slope.slope_category;
      }
    }

    // -------------------------------------------------------
    // RAINFALL
    // -------------------------------------------------------

    if (data.rainfall) {

      const rain =
        document.getElementById(
          "dash-rain-72h"
        );

      if (rain) {
        rain.textContent =
          data.rainfall.rain_72h_mm +
          " mm";
      }

      const rainIntensity =
        document.getElementById(
          "dash-rain-intensity"
        );

      if (rainIntensity) {
        rainIntensity.textContent =
          data.rainfall.intensity_indicator +
          " (24h: " +
          data.rainfall.rain_24h_mm +
          "mm)";
      }
    }

    // -------------------------------------------------------
    // TERRAIN
    // -------------------------------------------------------

    if (data.terrain) {

      const terrain =
        document.getElementById(
          "dash-terrain-type"
        );

      if (terrain) {
        terrain.textContent =
          data.terrain.terrain_type;
      }

      const tri =
        document.getElementById(
          "dash-tri"
        );

      if (tri) {
        tri.textContent =
          "TRI: " +
          data.terrain.tri +
          " (" +
          data.terrain.tri_category +
          ")";
      }
    }

    // -------------------------------------------------------
    // RANDOM FOREST ML CARD
    // -------------------------------------------------------

    const ml =
      data.risk &&
      data.risk.ml_prediction;

    if (ml) {

      const mlScore =
        document.getElementById(
          "ml-risk-score"
        );

      if (mlScore) {
        mlScore.textContent =
          Math.round(
            Number(ml.score) || score
          );
      }

      const mlBadge =
        document.getElementById(
          "ml-risk-badge"
        );

      if (mlBadge) {

        mlBadge.textContent =
          ml.risk_level ||
          data.risk.risk_level ||
          "Unknown Risk";

        mlBadge.style.backgroundColor =
          ml.risk_color ||
          data.risk.risk_color ||
          "#64748b";
      }

      const mlSlope =
        document.getElementById(
          "ml-slope-value"
        );

      if (
        mlSlope &&
        data.slope
      ) {
        mlSlope.textContent =
          data.slope.center_slope_deg +
          "°";
      }

      const mlElevation =
        document.getElementById(
          "ml-elevation-value"
        );

      if (
        mlElevation &&
        data.elevation
      ) {
        mlElevation.textContent =
          data.elevation.center_elevation_m +
          " m";
      }
    }

    // -------------------------------------------------------
    // EXPLANATION
    // -------------------------------------------------------

    const explanation =
      document.getElementById(
        "dash-explanation-text"
      );

    if (explanation) {
      explanation.textContent =
        data.risk.explanation ||
        "Risk assessment generated using environmental data and the Random Forest machine-learning model.";
    }

    // -------------------------------------------------------
    // DATA SOURCES
    // -------------------------------------------------------

    if (data.elevation) {

      const demBadge =
        document.getElementById(
          "source-dem-badge"
        );

      if (demBadge) {
        demBadge.textContent =
          data.elevation.source;
      }
    }

    if (data.rainfall) {

      const rainBadge =
        document.getElementById(
          "source-rain-badge"
        );

      if (rainBadge) {
        rainBadge.textContent =
          data.rainfall.source;
      }
    }

    // -------------------------------------------------------
    // HISTORICAL TABLE
    // -------------------------------------------------------

    if (
      data.historical &&
      Array.isArray(data.historical.records)
    ) {
      renderHistoricalTable(
        data.historical.records
      );
    }
  }

  // ---------------------------------------------------------
  // HISTORICAL TABLE
  // ---------------------------------------------------------

  function renderHistoricalTable(records) {

    const tbody =
      document.getElementById(
        "historical-records-tbody"
      );

    const countBadge =
      document.getElementById(
        "historical-count-badge"
      );

    if (!tbody) {
      return;
    }

    if (countBadge) {
      countBadge.textContent =
        (records ? records.length : 0) +
        " within 150 km";
    }

    if (
      !records ||
      records.length === 0
    ) {

      tbody.innerHTML =
        "<tr>" +
        "<td colspan=\"5\" style=\"text-align:center; color:#94a3b8; padding:1rem;\">" +
        "No historical NASA GLC landslide records documented within 150 km radius." +
        "</td>" +
        "</tr>";

      return;
    }

    tbody.innerHTML = "";

    records
      .slice(0, 5)
      .forEach(function (record) {

        const row =
          document.createElement("tr");

        row.innerHTML =
          "<td><strong>" +
          (record.name || "Unknown") +
          "</strong></td>" +

          "<td>" +
          (record.date || "N/A") +
          "</td>" +

          "<td>" +
          "<span style=\"font-size:0.78rem; background:#fee2e2; color:#991b1b; padding:2px 6px; border-radius:4px;\">" +
          (record.hazard_type || "Landslide") +
          "</span>" +
          "</td>" +

          "<td>" +
          (record.trigger || "N/A") +
          "</td>" +

          "<td><b>" +
          (record.fatalities || 0) +
          "</b></td>";

        tbody.appendChild(row);
      });
  }

  // ---------------------------------------------------------
  // PUBLIC FUNCTIONS
  // ---------------------------------------------------------

  return {
    init: init,
    analyzeCoordinates: analyzeCoordinates
  };

})();


// Make dashboard available globally
window.DashboardModule =
  DashboardModule;


// Start when page loads
document.addEventListener(
  "DOMContentLoaded",
  DashboardModule.init
);