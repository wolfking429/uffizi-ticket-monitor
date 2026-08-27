from datetime import date

import pytest

from uffizi_monitor.checker import (
    SiteBlockedError,
    extract_performance_region,
    month_offset,
    raise_if_site_blocked,
)


@pytest.mark.parametrize(
    ("month_heading", "target", "expected"),
    [
        ("febbraio 2031", date(2031, 4, 15), 2),
        ("aprile 2031", date(2031, 4, 15), 0),
        ("dicembre 2030", date(2031, 2, 1), 2),
    ],
)
def test_month_offset_understands_italian_months(
    month_heading: str, target: date, expected: int
) -> None:
    assert month_offset(month_heading, target) == expected


def test_rejects_target_dates_before_visible_month() -> None:
    with pytest.raises(ValueError, match="before"):
        month_offset("aprile 2031", date(2031, 3, 30))


def test_extracts_only_selected_day_performance_area() -> None:
    body = """
    Seleziona la Data
    Hai selezionato il giorno 15 aprile 2031, ora scegli l'orario
    08:30\n(2)\n09:00\n(3)
    Numero massimo di biglietti acquistabili per questo evento: 10
    Other page content 12:00 (999)
    """

    region = extract_performance_region(body)

    assert "08:30" in region
    assert "09:00" in region
    assert "12:00" not in region


@pytest.mark.parametrize(
    "text",
    [
        "Automation detected. Please use a browser not controlled by scripts.",
        "Sorry, you have been blocked. You are unable to access this website.",
        "Checking your browser... Please allow up to a few seconds.",
    ],
)
def test_detects_web_application_firewall_pages(text: str) -> None:
    with pytest.raises(SiteBlockedError):
        raise_if_site_blocked(text)


def test_normal_ticket_page_is_not_treated_as_blocked() -> None:
    raise_if_site_blocked("Seleziona la Data aprile 2031")
