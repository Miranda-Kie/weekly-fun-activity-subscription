import requests


class Geocoder:
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    def geocode(self, location: str) -> tuple[float, float, str]:
        response = requests.get(
            self.NOMINATIM_URL,
            params={"q": location, "format": "json", "limit": 1},
            headers={"User-Agent": "WeeklyFunActivities/1.0"},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            raise ValueError(f"Could not find location: {location}")

        result = results[0]
        return float(result["lat"]), float(result["lon"]), result.get("display_name", location)
