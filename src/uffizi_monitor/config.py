from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Mapping


class ConfigError(ValueError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    event_url: str
    target_date: date
    target_times: tuple[str, ...]
    min_tickets: int
    pushplus_token: str
    smtp_user: str
    smtp_auth_code: str
    alert_email: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "Config":
        required = (
            "EVENT_URL",
            "TARGET_DATE",
            "TARGET_TIMES",
            "MIN_TICKETS",
            "PUSHPLUS_TOKEN",
            "SMTP_USER",
            "SMTP_AUTH_CODE",
            "ALERT_EMAIL",
        )
        missing = [key for key in required if not values.get(key, "").strip()]
        if missing:
            raise ConfigError(f"Missing required configuration: {', '.join(missing)}")

        event_url = values["EVENT_URL"].strip()
        if not event_url.startswith("https://"):
            raise ConfigError("EVENT_URL must be an HTTPS URL")

        try:
            target_date = date.fromisoformat(values["TARGET_DATE"].strip())
        except ValueError as exc:
            raise ConfigError("TARGET_DATE must use YYYY-MM-DD") from exc

        target_times = tuple(
            item.strip() for item in values["TARGET_TIMES"].split(",") if item.strip()
        )
        if not target_times:
            raise ConfigError("TARGET_TIMES must contain at least one time")
        for target_time in target_times:
            try:
                datetime.strptime(target_time, "%H:%M")
            except ValueError as exc:
                raise ConfigError("TARGET_TIMES must contain HH:MM values") from exc

        try:
            min_tickets = int(values["MIN_TICKETS"])
        except ValueError as exc:
            raise ConfigError("MIN_TICKETS must be a positive integer") from exc
        if min_tickets < 1:
            raise ConfigError("MIN_TICKETS must be a positive integer")

        smtp_user = values["SMTP_USER"].strip()
        alert_email = values["ALERT_EMAIL"].strip()
        if "@" not in smtp_user or "@" not in alert_email:
            raise ConfigError("SMTP_USER and ALERT_EMAIL must be email addresses")

        return cls(
            event_url=event_url,
            target_date=target_date,
            target_times=target_times,
            min_tickets=min_tickets,
            pushplus_token=values["PUSHPLUS_TOKEN"].strip(),
            smtp_user=smtp_user,
            smtp_auth_code=values["SMTP_AUTH_CODE"].strip(),
            alert_email=alert_email,
        )

