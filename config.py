import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_TRUTHY = {"1", "true", "yes"}


def _env_bool(name: str, default: str = "no") -> bool:
    return os.getenv(name, default).strip().lower() in _TRUTHY


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required in .env")
    return value


@dataclass(frozen=True)
class Settings:
    location: str
    search_radius_miles: int
    email_to: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    ticketmaster_api_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            location=_require("LOCATION"),
            search_radius_miles=int(os.getenv("SEARCH_RADIUS_MILES", "25")),
            email_to=_require("EMAIL_TO"),
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=_require("SMTP_USER"),
            smtp_password=_require("SMTP_PASSWORD"),
            ticketmaster_api_key=_require("TICKETMASTER_API_KEY"),
        )


@dataclass(frozen=True)
class SqlSettings:
    server: str
    database: str
    driver: str
    user: str | None
    password: str | None
    trusted_connection: bool
    is_azure: bool
    encrypt: bool
    trust_server_certificate: bool

    @classmethod
    def from_env(cls) -> "SqlSettings":
        server = os.getenv("SQL_SERVER", "localhost").strip()
        user = os.getenv("SQL_USER", "").strip() or None
        password = os.getenv("SQL_PASSWORD", "").strip() or None
        is_azure = ".database.windows.net" in server.lower() or _env_bool("SQL_AZURE")

        if is_azure and (not user or not password):
            raise ValueError(
                "SQL_USER and SQL_PASSWORD are required for Azure SQL Database"
            )

        use_trusted = _env_bool("SQL_TRUSTED_CONNECTION", "yes") and not user and not is_azure

        return cls(
            server=server,
            database=os.getenv("SQL_DATABASE", "WeeklyFunActivities").strip(),
            driver=os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server").strip(),
            user=user,
            password=password,
            trusted_connection=use_trusted,
            is_azure=is_azure,
            encrypt=_env_bool("SQL_ENCRYPT", "yes" if is_azure else "no"),
            trust_server_certificate=_env_bool("SQL_TRUST_SERVER_CERTIFICATE"),
        )

    def connection_string(self, database: str | None = None) -> str:
        parts = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={database or self.database}",
        ]
        if self.trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.user}")
            parts.append(f"PWD={self.password}")
        if self.encrypt:
            parts.append("Encrypt=yes")
        if self.trust_server_certificate:
            parts.append("TrustServerCertificate=yes")
        return ";".join(parts) + ";"
