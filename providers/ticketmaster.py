from datetime import datetime, timedelta, timezone

import requests

from models import Activity
from providers.base import ActivityProvider


class TicketmasterProvider(ActivityProvider):
    SEARCH_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "Ticketmaster"

    def fetch(self, lat: float, lon: float, radius_miles: int) -> list[Activity]:
        if not self._api_key:
            return []

        start = datetime.now(timezone.utc)
        end = start + timedelta(days=7)

        response = requests.get(
            self.SEARCH_URL,
            params={
                "apikey": self._api_key,
                "latlong": f"{lat},{lon}",
                "radius": radius_miles,
                "unit": "miles",
                "sort": "date,asc",
                "size": 25,
                "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            timeout=30,
        )
        response.raise_for_status()

        activities: list[Activity] = []
        for event in response.json().get("_embedded", {}).get("events", []):
            venue = (event.get("_embedded") or {}).get("venues", [{}])[0]
            when = (event.get("dates") or {}).get("start", {}).get("localDateTime")
            if not when:
                when = (event.get("dates") or {}).get("start", {}).get("localDate")
            parsed = None
            if when:
                parsed = datetime.fromisoformat(when)

            classifications = event.get("classifications") or []
            category = "Event"
            if classifications:
                segment = classifications[0].get("segment", {}).get("name")
                genre = classifications[0].get("genre", {}).get("name")
                category = genre or segment or category

            activities.append(
                Activity(
                    title=event.get("name", "Untitled event"),
                    category=category,
                    date=parsed,
                    venue=venue.get("name") or venue.get("city", {}).get("name") or "TBA",
                    url=event.get("url"),
                    source=self.name,
                    image_url=self._pick_image_url(event.get("images", [])),
                )
            )
        return activities

    @staticmethod
    def _pick_image_url(images: list[dict]) -> str | None:
        if not images:
            return None

        landscape = [img for img in images if img.get("ratio") == "16_9" and img.get("url")]
        if landscape:
            return min(landscape, key=lambda img: abs(img.get("width", 0) - 640)).get("url")

        for image in images:
            if image.get("url"):
                return image["url"]
        return None
