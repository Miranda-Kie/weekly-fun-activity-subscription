from datetime import datetime
from typing import Self

import pyodbc

from config import SqlSettings
from models import Activity

CREATE_TABLES_SQL = """
IF OBJECT_ID('dbo.activities', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.activities (
        id INT IDENTITY(1,1) PRIMARY KEY,
        title NVARCHAR(500) NOT NULL,
        category NVARCHAR(100) NOT NULL,
        event_date DATETIME2 NULL,
        venue NVARCHAR(300) NOT NULL,
        url NVARCHAR(1000) NULL,
        source NVARCHAR(50) NOT NULL,
        description NVARCHAR(MAX) NULL,
        weather NVARCHAR(500) NULL,
        image_url NVARCHAR(1000) NULL,
        location NVARCHAR(300) NOT NULL,
        stored_at DATETIME2 NOT NULL,
        CONSTRAINT uq_activity UNIQUE (title, venue, event_date, source)
    );
END

IF OBJECT_ID('dbo.email_runs', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.email_runs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        sent_at DATETIME2 NOT NULL,
        location NVARCHAR(300) NOT NULL,
        activity_count INT NOT NULL,
        email_to NVARCHAR(320) NOT NULL
    );
END
"""

UPSERT_ACTIVITY_SQL = """
IF EXISTS (
    SELECT 1 FROM dbo.activities
    WHERE title = ? AND venue = ? AND event_date = ? AND source = ?
)
    UPDATE dbo.activities
    SET category = ?, url = ?, description = ?, weather = ?, image_url = ?,
        location = ?, stored_at = ?
    WHERE title = ? AND venue = ? AND event_date = ? AND source = ?
ELSE
    INSERT INTO dbo.activities (
        title, category, event_date, venue, url, source,
        description, weather, image_url, location, stored_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


class ActivityStore:
    """Saves activities and email history to SQL Server via pyodbc."""

    def __init__(self, connection: pyodbc.Connection) -> None:
        self._connection = connection

    @classmethod
    def connect(cls, sql_settings: SqlSettings) -> Self:
        if not sql_settings.is_azure:
            cls._ensure_local_database(sql_settings)

        try:
            connection = pyodbc.connect(sql_settings.connection_string())
        except pyodbc.Error as exc:
            raise ConnectionError(cls._connection_help(sql_settings)) from exc

        connection.autocommit = True
        store = cls(connection)
        store._ensure_tables()
        return store

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _connection_help(sql_settings: SqlSettings) -> str:
        if sql_settings.is_azure:
            return (
                "Could not connect to Azure SQL. Check SQL_SERVER, SQL_USER, "
                "SQL_PASSWORD, and add your IP under Azure Portal -> "
                "SQL server -> Networking -> Firewall rules."
            )
        return (
            "Could not connect to SQL Server. Check SQL_SERVER in .env "
            "(e.g. localhost\\SQLEXPRESS or your-server.database.windows.net)."
        )

    @staticmethod
    def _ensure_local_database(sql_settings: SqlSettings) -> None:
        with pyodbc.connect(sql_settings.connection_string("master")) as connection:
            connection.autocommit = True
            connection.cursor().execute(
                f"""
                IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = ?)
                BEGIN
                    CREATE DATABASE [{sql_settings.database}];
                END
                """,
                sql_settings.database,
            )

    def _ensure_tables(self) -> None:
        self._connection.cursor().execute(CREATE_TABLES_SQL)

    def save_activities(self, activities: list[Activity], location: str) -> int:
        stored_at = datetime.now()
        cursor = self._connection.cursor()

        for activity in activities:
            key = (activity.title, activity.venue, activity.date, activity.source)
            details = (
                activity.category,
                activity.url,
                activity.description,
                activity.weather,
                activity.image_url,
                location,
                stored_at,
            )
            insert = (
                activity.title,
                activity.category,
                activity.date,
                activity.venue,
                activity.url,
                activity.source,
                activity.description,
                activity.weather,
                activity.image_url,
                location,
                stored_at,
            )
            cursor.execute(UPSERT_ACTIVITY_SQL, *key, *details, *key, *insert)

        return len(activities)

    def log_email_run(self, location: str, activity_count: int, email_to: str) -> None:
        self._connection.cursor().execute(
            """
            INSERT INTO dbo.email_runs (sent_at, location, activity_count, email_to)
            VALUES (?, ?, ?, ?)
            """,
            datetime.now(),
            location,
            activity_count,
            email_to,
        )

    def close(self) -> None:
        self._connection.close()
