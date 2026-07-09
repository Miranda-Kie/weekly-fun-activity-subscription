from dataclasses import dataclass, replace
from datetime import date

import requests

from models import Activity

WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Foggy",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with hail",
}


@dataclass(frozen=True)
class DayForecast:
    description: str
    high_c: float
    low_c: float
    precip_chance: int | None

    @property
    def label(self) -> str:
        rain = (
            f" · {self.precip_chance}% rain"
            if self.precip_chance is not None
            else ""
        )
        return (
            f"{self.description} · High {self.high_c:.0f}°C / "
            f"Low {self.low_c:.0f}°C{rain}"
        )


class WeatherService:
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def fetch_weekly_forecast(self, lat: float, lon: float) -> dict[date, DayForecast]:
        response = requests.get(
            self.FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": (
                    "weathercode,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=30,
        )
        response.raise_for_status()
        daily = response.json().get("daily", {})

        forecasts: dict[date, DayForecast] = {}
        dates = daily.get("time", [])
        for index, day in enumerate(dates):
            code = daily.get("weathercode", [None])[index]
            forecasts[date.fromisoformat(day)] = DayForecast(
                description=WMO_DESCRIPTIONS.get(code, "Mixed conditions"),
                high_c=daily.get("temperature_2m_max", [0])[index],
                low_c=daily.get("temperature_2m_min", [0])[index],
                precip_chance=daily.get("precipitation_probability_max", [None])[index],
            )
        return forecasts

    def attach_to_activities(
        self,
        activities: list[Activity],
        lat: float,
        lon: float,
    ) -> list[Activity]:
        try:
            forecasts = self.fetch_weekly_forecast(lat, lon)
        except Exception as exc:
            print(f"Warning: Weather forecast failed — {exc}")
            return activities

        enriched: list[Activity] = []
        for activity in activities:
            if activity.date is None:
                enriched.append(activity)
                continue
            forecast = forecasts.get(activity.date.date())
            if forecast is None:
                enriched.append(activity)
                continue
            enriched.append(replace(activity, weather=forecast.label))
        return enriched
