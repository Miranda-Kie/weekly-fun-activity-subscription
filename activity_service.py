from datetime import datetime, timedelta

from models import Activity
from providers.base import ActivityProvider


class ActivityAggregator:
    def __init__(self, providers: list[ActivityProvider]) -> None:
        self._providers = providers

    def collect(self, lat: float, lon: float, radius_miles: int) -> list[Activity]:
        all_activities: list[Activity] = []
        for provider in self._providers:
            try:
                all_activities.extend(provider.fetch(lat, lon, radius_miles))
            except Exception as exc:
                print(f"Warning: {provider.name} failed — {exc}")

        this_week = self._filter_this_week(all_activities)
        return self._dedupe_and_sort(this_week)

    def _filter_this_week(self, activities: list[Activity]) -> list[Activity]:
        today = datetime.now().date()
        week_end = today + timedelta(days=7)

        filtered: list[Activity] = []
        for activity in activities:
            if activity.date is None:
                continue
            event_day = activity.date.date()
            if today <= event_day <= week_end:
                filtered.append(activity)
        return filtered

    def _dedupe_and_sort(self, activities: list[Activity]) -> list[Activity]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[Activity] = []

        for activity in activities:
            key = (activity.title.lower(), activity.venue.lower(), activity.date_label)
            if key in seen:
                continue
            seen.add(key)
            unique.append(activity)

        return sorted(unique, key=lambda item: item.date or datetime.max)
