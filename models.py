from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Activity:
    title: str
    category: str
    date: datetime | None
    venue: str
    url: str | None
    source: str
    description: str | None = None
    weather: str | None = None
    image_url: str | None = None

    @property
    def date_label(self) -> str:
        if self.date is None:
            return "Date TBA"
        return self.date.strftime("%a, %b %d · %I:%M %p")
