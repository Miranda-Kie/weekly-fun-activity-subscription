from abc import ABC, abstractmethod

from models import Activity


class ActivityProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def fetch(self, lat: float, lon: float, radius_miles: int) -> list[Activity]:
        pass
