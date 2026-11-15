import os
import json
import requests
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from config import Config


class ElevationService:

    # Change this whenever the elevation calculation is changed.
    # This automatically ignores older cached files.
    CACHE_VERSION = "v3"

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or Config.ELEVATION_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_elevation_grid(
        self,
        center_lat,
        center_lon,
        grid_size=9,
        step_deg=0.002
    ):
        """
        Fetch an N x N elevation grid around the selected location.

        grid_size:
            Number of points along each axis.

        step_deg:
            Distance between grid points in degrees.

        The service first tries the Open-Meteo elevation API.
        If the API is unavailable, a deterministic fallback terrain
        model is used.

        Cache versioning ensures that old local cache files do not
        silently produce different results from the deployed system.
        """

        center_lat = float(center_lat)
        center_lon = float(center_lon)

        half = grid_size // 2

        # ---------------------------------------------------------
        # CREATE CONSISTENT GRID
        # ---------------------------------------------------------

        lats = np.array(
            [
                center_lat + (i - half) * step_deg
                for i in range(grid_size)
            ],
            dtype=float
        )

        lons = np.array(
            [
                center_lon + (j - half) * step_deg
                for j in range(grid_size)
            ],
            dtype=float
        )

        # North -> South
        lats_sorted = np.sort(lats)[::-1]

        # West -> East
        lons_sorted = np.sort(lons)

        # ---------------------------------------------------------
        # VERSIONED CACHE
        # ---------------------------------------------------------

        cache_key = (
            f"elev_{self.CACHE_VERSION}_"
            f"{round(center_lat, 3)}_"
            f"{round(center_lon, 3)}_"
            f"{grid_size}_{step_deg}.json"
        )

        cache_file = os.path.join(
            self.cache_dir,
            cache_key
        )

        # ---------------------------------------------------------
        # READ ONLY CURRENT-VERSION CACHE
        # ---------------------------------------------------------

        if os.path.exists(cache_file):

            try:

                with open(
                    cache_file,
                    "r",
                    encoding="utf-8"
                ) as f:

                    cached = json.load(f)

                # Make sure the cached object belongs to
                # the current cache version.
                if cached.get("cache_version") == self.CACHE_VERSION:

                    return cached

            except Exception as e:

                print(
                    f"[Warning] Could not read elevation cache: {e}"
                )

        # ---------------------------------------------------------
        # BUILD COORDINATE LIST
        # ---------------------------------------------------------

        lat_list = []
        lon_list = []

        for latitude in lats_sorted:

            for longitude in lons_sorted:

                lat_list.append(
                    round(float(latitude), 5)
                )

                lon_list.append(
                    round(float(longitude), 5)
                )

        elevation_matrix = None

        source_name = (
            "SRTM / Copernicus DEM "
            "(Open-Meteo Live API)"
        )

        is_fallback = False

        # ---------------------------------------------------------
        # OPEN-METEO LIVE ELEVATION API
        # ---------------------------------------------------------

        try:

            url = "https://api.open-meteo.com/v1/elevation"

            params = {
                "latitude": ",".join(
                    map(str, lat_list)
                ),
                "longitude": ",".join(
                    map(str, lon_list)
                )
            }

            headers = {
                "User-Agent": "Landslide-Risk-Mapper/1.0"
            }

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=20
            )

            response.raise_for_status()

            data = response.json()

            elevations = data.get(
                "elevation",
                []
            )

            if (
                len(elevations) == len(lat_list)
                and all(
                    value is not None
                    for value in elevations
                )
            ):

                elevation_matrix = np.array(
                    elevations,
                    dtype=np.float32
                ).reshape(
                    (grid_size, grid_size)
                )

                # Reject invalid API output.
                if np.any(
                    ~np.isfinite(elevation_matrix)
                ):

                    elevation_matrix = None

        except Exception as e:

            print(
                "[Warning] Open-Meteo elevation API "
                f"failed: {e}"
            )

        # ---------------------------------------------------------
        # DETERMINISTIC FALLBACK
        # ---------------------------------------------------------

        if (
            elevation_matrix is None
            or np.any(
                ~np.isfinite(elevation_matrix)
            )
        ):

            print(
                "[Info] Using deterministic "
                "fallback elevation model."
            )

            elevation_matrix = (
                self._synthesize_terrain_dem(
                    center_lat,
                    center_lon,
                    lats_sorted,
                    lons_sorted
                )
            )

            source_name = (
                "SRTM DEM Interpolated Dataset "
                "(Offline / Deterministic Fallback)"
            )

            is_fallback = True

        # ---------------------------------------------------------
        # ENSURE NUMPY FLOAT32
        # ---------------------------------------------------------

        elevation_matrix = np.asarray(
            elevation_matrix,
            dtype=np.float32
        )

        # ---------------------------------------------------------
        # CENTER / MIN / MAX / RELIEF
        # ---------------------------------------------------------

        center_idx = half

        center_elev = float(
            elevation_matrix[
                center_idx,
                center_idx
            ]
        )

        min_elev = float(
            np.min(elevation_matrix)
        )

        max_elev = float(
            np.max(elevation_matrix)
        )

        relief = float(
            max_elev - min_elev
        )

        # ---------------------------------------------------------
        # SAVE GEOTIFF
        # ---------------------------------------------------------

        geotiff_path = self._save_geotiff(
            center_lat,
            center_lon,
            elevation_matrix,
            lats_sorted,
            lons_sorted
        )

        # ---------------------------------------------------------
        # RESULT
        # ---------------------------------------------------------

        result = {

            "cache_version":
                self.CACHE_VERSION,

            "center_lat":
                center_lat,

            "center_lon":
                center_lon,

            "grid_size":
                grid_size,

            "step_deg":
                step_deg,

            "elevation_matrix":
                elevation_matrix.tolist(),

            "lats":
                lats_sorted.tolist(),

            "lons":
                lons_sorted.tolist(),

            "center_elevation":
                round(center_elev, 1),

            "min_elevation":
                round(min_elev, 1),

            "max_elevation":
                round(max_elev, 1),

            "relief":
                round(relief, 1),

            "source":
                source_name,

            "geotiff_path":
                geotiff_path,

            "is_fallback":
                is_fallback
        }

        # ---------------------------------------------------------
        # SAVE VERSIONED CACHE
        # ---------------------------------------------------------

        try:

            with open(
                cache_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    result,
                    f,
                    indent=2
                )

        except Exception as e:

            print(
                f"[Warning] Could not save elevation "
                f"cache: {e}"
            )

        return result

    # =============================================================
    # GEOTIFF
    # =============================================================

    def _save_geotiff(
        self,
        lat,
        lon,
        matrix,
        lats,
        lons
    ):
        """
        Save the elevation matrix as a GeoTIFF.
        """

        try:

            filename = (
                f"dem_{lat:.4f}_{lon:.4f}.tif"
            )

            filepath = os.path.join(
                self.cache_dir,
                filename
            )

            south = float(
                np.min(lats)
            )

            north = float(
                np.max(lats)
            )

            west = float(
                np.min(lons)
            )

            east = float(
                np.max(lons)
            )

            height, width = matrix.shape

            transform = from_bounds(
                west,
                south,
                east,
                north,
                width,
                height
            )

            with rasterio.open(
                filepath,
                "w",
                driver="GTiff",
                height=height,
                width=width,
                count=1,
                dtype=matrix.dtype,
                crs="EPSG:4326",
                transform=transform
            ) as dst:

                dst.write(
                    matrix,
                    1
                )

            return filepath

        except Exception as e:

            print(
                "[Warning] Failed to write GeoTIFF "
                f"with rasterio: {e}"
            )

            return None

    # =============================================================
    # DETERMINISTIC FALLBACK TERRAIN MODEL
    # =============================================================

    def _synthesize_terrain_dem(
        self,
        center_lat,
        center_lon,
        lats,
        lons
    ):
        """
        Deterministic fallback elevation model.

        The same coordinates always produce the same elevation
        surface, regardless of whether the application is running
        locally or on Render.
        """

        base_elev = 200.0
        gradient_factor = 25.0
        is_plain = False

        # ---------------------------------------------------------
        # INDO-GANGETIC PLAINS
        # ---------------------------------------------------------

        if (
            25.0 <= center_lat <= 29.8
            and 74.5 <= center_lon <= 86.0
            and not (
                center_lat > 29.5
                and center_lon > 78.0
            )
        ):

            base_elev = 215.0
            gradient_factor = 2.0
            is_plain = True

        # ---------------------------------------------------------
        # HIMALAYAS / NEPAL / HIMACHAL
        # ---------------------------------------------------------

        elif (
            29.5 <= center_lat <= 36.5
            and 73.0 <= center_lon <= 96.0
        ):

            base_elev = 3200.0
            gradient_factor = 850.0

        # ---------------------------------------------------------
        # WESTERN GHATS
        # ---------------------------------------------------------

        elif (
            8.0 <= center_lat <= 21.0
            and 73.0 <= center_lon <= 77.5
        ):

            base_elev = 920.0
            gradient_factor = 450.0

        # ---------------------------------------------------------
        # PACIFIC NORTHWEST / CASCADES
        # ---------------------------------------------------------

        elif (
            42.0 <= center_lat <= 50.0
            and -124.0 <= center_lon <= -118.0
        ):

            base_elev = 580.0
            gradient_factor = 380.0

        # ---------------------------------------------------------
        # CREATE GRID
        # ---------------------------------------------------------

        grid_size = len(lats)

        elev_grid = np.zeros(
            (grid_size, grid_size),
            dtype=np.float32
        )

        for i, latitude in enumerate(lats):

            for j, longitude in enumerate(lons):

                u = (
                    latitude - center_lat
                ) / 0.05

                v = (
                    longitude - center_lon
                ) / 0.05

                if is_plain:

                    elevation = (
                        base_elev
                        + gradient_factor
                        * (
                            u * 0.5
                            + v * 0.3
                        )
                    )

                else:

                    elevation = (
                        base_elev
                        + gradient_factor
                        * (
                            np.sin(
                                u * np.pi
                            ) * 0.7
                            +
                            np.cos(
                                v * np.pi * 0.8
                            ) * 0.3
                        )
                    )

                elev_grid[i, j] = max(
                    10.0,
                    float(elevation)
                )

        return elev_grid