import sys

from activity_service import ActivityAggregator
from config import Settings, SqlSettings
from database import ActivityStore
from email_service import EmailService
from geocoding import Geocoder
from providers import TicketmasterProvider
from weather_service import WeatherService


def main() -> int:
    try:
        settings = Settings.from_env()
        sql_settings = SqlSettings.from_env()
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        print("Copy .env.example to .env and fill in your details.")
        return 1

    geocoder = Geocoder()
    lat, lon, label = geocoder.geocode(settings.location)
    print(f"Searching within {settings.search_radius_miles} mi of {label}...")

    providers = [TicketmasterProvider(settings.ticketmaster_api_key)]
    activities = ActivityAggregator(providers).collect(lat, lon, settings.search_radius_miles)
    activities = WeatherService().attach_to_activities(activities, lat, lon)
    print(f"Found {len(activities)} activities.")

    try:
        with ActivityStore.connect(sql_settings) as store:
            store.save_activities(activities, label)
            print(f"Stored {len(activities)} activities in SQL Server.")
            EmailService(settings).send_digest(activities, label)
            store.log_email_run(label, len(activities), settings.email_to)
    except ConnectionError as exc:
        print(f"Database error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
