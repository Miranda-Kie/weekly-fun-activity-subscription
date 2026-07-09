import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template

from config import Settings
from models import Activity

EMAIL_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: Georgia, serif; color: #1a1a1a; line-height: 1.5; max-width: 640px; margin: 0 auto; padding: 24px; }
    h1 { font-size: 24px; margin-bottom: 4px; }
    .subtitle { color: #666; margin-bottom: 24px; }
    .activity { border-left: 4px solid #e85d4c; padding: 12px 16px; margin-bottom: 16px; background: #faf7f5; overflow: hidden; }
    .event-image { display: block; width: 100%; max-width: 100%; height: auto; border-radius: 6px; margin-bottom: 12px; }
    .title { font-size: 18px; font-weight: bold; margin: 0 0 4px; }
    .meta { color: #555; font-size: 14px; margin: 0; }
    .badge { display: inline-block; background: #2d6a4f; color: white; font-size: 11px; padding: 2px 8px; border-radius: 999px; margin-right: 6px; }
    a { color: #c0392b; }
    .weather { color: #2c5282; font-size: 13px; margin-top: 6px; }
    .empty { color: #888; font-style: italic; }
  </style>
</head>
<body>
  <h1>Your weekly fun activities</h1>
  <p class="subtitle">{{ location }} · {{ week_label }}</p>

  {% if activities %}
    {% for activity in activities %}
    <div class="activity">
      {% if activity.image_url %}
      <img src="{{ activity.image_url }}" alt="{{ activity.title }}" class="event-image">
      {% endif %}
      <p class="title">{{ activity.title }}</p>
      <p class="meta">
        <span class="badge">{{ activity.category }}</span>
        <span class="badge">{{ activity.source }}</span><br>
        {{ activity.date_label }} · {{ activity.venue }}
        {% if activity.weather %}<br><span class="weather">Forecast: {{ activity.weather }}</span>{% endif %}
        {% if activity.url %}<br><a href="{{ activity.url }}">Details</a>{% endif %}
      </p>
    </div>
    {% endfor %}
  {% else %}
    <p class="empty">No dated events found for the next 7 days. Add a Ticketmaster API key in .env.</p>
  {% endif %}
</body>
</html>
""")


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_digest(self, activities: list[Activity], location_label: str) -> None:
        week_start = datetime.now()
        week_end = week_start + timedelta(days=7)
        subject = f"Weekly fun activities near {location_label.split(',')[0]}"
        html = EMAIL_TEMPLATE.render(
            activities=activities,
            location=location_label,
            week_label=f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}",
        )

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self._settings.smtp_user
        message["To"] = self._settings.email_to
        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port) as server:
            server.starttls()
            server.login(self._settings.smtp_user, self._settings.smtp_password)
            server.sendmail(
                self._settings.smtp_user,
                [self._settings.email_to],
                message.as_string(),
            )

        print(f"Email sent to {self._settings.email_to} with {len(activities)} activities.")
