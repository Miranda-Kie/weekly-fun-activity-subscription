# Weekly Fun Activities

A small Python app that finds **dated events happening in the next 7 days** near you and emails you a digest.

Uses the **Ticketmaster** API to find dated events.

## Showcase Presentation

📄 [View project presentation (PDF)](presentation.pdf)

## Setup

1. **Install dependencies**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure**

   Copy `.env.example` to `.env` and fill in:

   | Variable | Required | Description |
   |----------|----------|-------------|
   | `LOCATION` | Yes | City name, e.g. `Toronto, ON` |
   | `EMAIL_TO` | Yes | Where to send the digest |
   | `SMTP_USER` / `SMTP_PASSWORD` | Yes | Email account (Gmail app password works) |
   | `TICKETMASTER_API_KEY` | Yes | Free at [developer.ticketmaster.com](https://developer.ticketmaster.com/) |
   | `SQL_SERVER` | Yes | Azure: `your-server.database.windows.net` |
   | `SQL_DATABASE` | Yes | Database name, e.g. `WeeklyFunActivities` |
   | `SQL_USER` / `SQL_PASSWORD` | Yes (Azure) | SQL admin credentials from Azure Portal |
   | `SQL_TRUSTED_CONNECTION` | No | `no` for Azure (default when using SQL auth) |

3. **Run**

   ```bash
   python main.py
   ```

## Schedule weekly (Windows)

A scheduled task sends the email **every Monday at 8:00 AM**.

To set it up manually, or recreate it:

```powershell
schtasks /Create /TN "Weekly Fun Activities" /TR "C:\path\to\weekly fun activities\run_weekly.bat" /SC WEEKLY /D MON /ST 08:00 /F
```

To change the time, delete and recreate with a different `/ST` value (24-hour format, e.g. `09:30`).

To remove the schedule:

```powershell
schtasks /Delete /TN "Weekly Fun Activities" /F
```

You can also manage it in **Task Scheduler** → `Weekly Fun Activities`.

## Architecture

Each data source is an `ActivityProvider` subclass:

- `TicketmasterProvider` — concerts, sports, theatre

Only events with a date in the next 7 days are included in the email. Each event includes a weather forecast for that day (via [Open-Meteo](https://open-meteo.com/), no API key needed).

## Database

Activities and email send history are stored in **Azure SQL Database** (or local SQL Server) using `pyodbc`.

| Table | Stores |
|-------|--------|
| `activities` | Event details, weather, image URL, location, and when it was saved |
| `email_runs` | Timestamp, location, activity count, and recipient for each email sent |

### Azure SQL setup

1. Create a database in [Azure Portal](https://portal.azure.com) (e.g. `WeeklyFunActivities`)
2. Under **SQL server → Networking**, allow your client IP (or enable access for Azure services if running in cloud)
3. Add these to `.env`:

```
SQL_SERVER=your-server.database.windows.net
SQL_DATABASE=WeeklyFunActivities
SQL_USER=your-sql-admin
SQL_PASSWORD=your-sql-password
SQL_DRIVER=ODBC Driver 17 for SQL Server
SQL_TRUSTED_CONNECTION=no
```

The app creates tables automatically on first run. Create the database itself in Azure Portal before running.

### Local SQL Server (optional)

For local development, use `SQL_SERVER=localhost\\SQLEXPRESS` with `SQL_TRUSTED_CONNECTION=yes`. The app can auto-create the local database.

Add your own provider by extending `providers/base.py` and registering it in `main.py`.

## pyodbc

[pyodbc](https://github.com/mkleehammer/pyodbc) is a Python library that connects to SQL Server. It acts as a bridge between Python and the ODBC driver already installed on Windows (`ODBC Driver 17 for SQL Server`). All database code lives in `database.py` — the rest of the app doesn't need to know about it.
