import numpy as np

class TerrainAnalysisService:
    def __init__(self):
        pass

    def analyze_terrain(self, elevation_matrix, center_elevation, slope_deg, relief):
        """
        Derives terrain characteristics:
        - Topographic Roughness Index (TRI)
        - Geomorphological classification
        - Normalized Terrain Score (0–100)
        - Geomorphic vulnerability description
        """
        Z = np.array(elevation_matrix, dtype=np.float64)
        nrows, ncols = Z.shape
        center_r, center_c = nrows // 2, ncols // 2

        # Topographic Roughness Index (Riley et al. 1999)
        # TRI is the mean absolute elevation difference between center cell and its 8 neighbors
        if nrows >= 3 and ncols >= 3:
            neighborhood = Z[center_r-1:center_r+2, center_c-1:center_c+2]
            center_val = Z[center_r, center_c]
            diffs = np.abs(neighborhood - center_val)
            # exclude center itself (diff = 0)
            tri = float(np.sum(diffs) / 8.0)
        else:
            tri = float(relief / 4.0)

        # Classification based on elevation, relief, and slope
        terrain_type, terrain_desc, base_terrain_score = self._classify_morphometry(
            center_elevation, slope_deg, relief, tri
        )

        # Aspect estimation (direction slope faces: N, NE, E, SE, S, SW, W, NW)
        aspect_deg, aspect_label = self._calculate_aspect(Z, center_r, center_c)

        # Normalize terrain score (0–100)
        terrain_score = min(100.0, max(5.0, base_terrain_score))

        return {
            "elevation_m": round(float(center_elevation), 1),
            "relief_m": round(float(relief), 1),
            "tri": round(tri, 1),
            "tri_category": self._classify_tri(tri),
            "terrain_type": terrain_type,
            "terrain_score": round(terrain_score, 1),
            "aspect_deg": round(aspect_deg, 1) if aspect_deg is not None else None,
            "aspect_cardinal": aspect_label,
            "description": terrain_desc
        }

    def _calculate_aspect(self, Z, r, c):
        """Calculate aspect in degrees (0-360) and cardinal direction."""
        try:
            if r < 1 or r >= Z.shape[0]-1 or c < 1 or c >= Z.shape[1]-1:
                return None, "Indeterminate"
            dz_dx = ((Z[r-1, c+1] + 2*Z[r, c+1] + Z[r+1, c+1]) - (Z[r-1, c-1] + 2*Z[r, c-1] + Z[r+1, c-1])) / 8.0
            dz_dy = ((Z[r+1, c-1] + 2*Z[r+1, c] + Z[r+1, c+1]) - (Z[r-1, c-1] + 2*Z[r-1, c] + Z[r-1, c+1])) / 8.0

            aspect_rad = np.arctan2(dz_dy, -dz_dx)
            aspect_deg = np.degrees(aspect_rad)
            if aspect_deg < 0:
                aspect_deg += 360.0

            cardinals = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            idx = int((aspect_deg + 11.25) / 22.5) % 16
            return aspect_deg, cardinals[idx]
        except Exception:
            return None, "Variable"

    def _classify_tri(self, tri):
        """Terrain Ruggedness Index classification (Riley et al.)."""
        if tri < 15:
            return "Level / Smooth"
        elif tri < 35:
            return "Gently Rugged"
        elif tri < 80:
            return "Moderately Rugged"
        elif tri < 150:
            return "Highly Rugged"
        else:
            return "Extremely Rugged"

    def _classify_morphometry(self, elev, slope, relief, tri):
        """
        Classifies terrain into geomorphological units and assigns baseline vulnerability score.
        """
        if elev > 2000 and (slope > 22 or relief > 120):
            return (
                "High Alpine / Steep Glaciated Mountain",
                "Rugged high-altitude Himalayan terrain characterized by unstable moraines, permafrost thaw, and fractured bedrock.",
                88.0
            )
        elif slope > 22 or relief > 100:
            return (
                "Steep Mountainous Escarpment",
                "High-relief escarpment with steep ravines. High gravitational potential energy accelerates mass flows upon regolith liquefaction.",
                82.0
            )
        elif 10 <= slope <= 22 or relief > 50:
            return (
                "Dissected Hillslopes & Ravines",
                "Moderate to steep hillsides with active drainage incision, subject to transitional slides along soil-rock interfaces.",
                58.0
            )
        elif 4 <= slope < 10 and relief > 25:
            return (
                "Rolling Uplands / Plateau Edges",
                "Rolling undulations with moderate stability. Vulnerable primarily at localized channel cutbanks and terrace margins.",
                32.0
            )
        elif elev > 800 and slope < 5:
            return (
                "Elevated Plateau / Tableland",
                "Broad tableland with gentle top surface; low immediate hazard except near cliff perimeters.",
                18.0
            )
        elif slope < 5 and relief < 30:
            return (
                "Alluvial Plain / Valley Floor",
                "Low-lying flat depositional plain with minimal shear stress. Very low landslide susceptibility.",
                8.0
            )
        else:
            return (
                "Undulating Terrain",
                "Gentle terrain with balanced shear resistance and drainage.",
                20.0
            )
