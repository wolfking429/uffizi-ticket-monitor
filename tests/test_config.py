import pytest

from uffizi_monitor.config import Config, ConfigError


def valid_environment() -> dict[str, str]:
    return {
        "EVENT_URL": "https://tickets.example/event/abc",
        "TARGET_DATE": "2031-04-15",
        "TARGET_TIMES": "08:15,08:30,08:45,09:00",
        "MIN_TICKETS": "2",
        "PUSHPLUS_TOKEN": "pushplus-secret",
        "SMTP_USER": "traveller@example.com",
        "SMTP_AUTH_CODE": "smtp-secret",
        "ALERT_EMAIL": "traveller@example.com",
    }


def test_loads_valid_configuration() -> None:
    config = Config.from_mapping(valid_environment())

    assert config.target_date.isoformat() == "2031-04-15"
    assert config.target_times == ("08:15", "08:30", "08:45", "09:00")
    assert config.min_tickets == 2


@pytest.mark.parametrize(
    ("key", "replacement"),
    [
        ("TARGET_DATE", "15/04/2031"),
        ("TARGET_TIMES", "08:15,not-a-time"),
        ("MIN_TICKETS", "0"),
        ("ALERT_EMAIL", "not-an-email"),
    ],
)
def test_rejects_invalid_values_without_leaking_secrets(
    key: str, replacement: str
) -> None:
    environment = valid_environment()
    environment[key] = replacement

    with pytest.raises(ConfigError) as caught:
        Config.from_mapping(environment)

    message = str(caught.value)
    assert "pushplus-secret" not in message
    assert "smtp-secret" not in message


def test_reports_missing_variable_by_name_only() -> None:
    environment = valid_environment()
    del environment["SMTP_AUTH_CODE"]

    with pytest.raises(ConfigError, match="SMTP_AUTH_CODE") as caught:
        Config.from_mapping(environment)

    assert "pushplus-secret" not in str(caught.value)
