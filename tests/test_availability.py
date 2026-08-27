import pytest

from uffizi_monitor.availability import (
    ParseError,
    Slot,
    find_matching_slots,
    parse_slots,
)


def test_parses_times_and_counts_from_ticket_text() -> None:
    text = """
    Hai selezionato il giorno 15/04/2031
    08:15\n(0)\n08:30 (2)\n08:45\n(7)\n09:00 (1)
    Numero massimo di biglietti acquistabili
    """

    assert parse_slots(text) == (
        Slot(time="08:15", available=0),
        Slot(time="08:30", available=2),
        Slot(time="08:45", available=7),
        Slot(time="09:00", available=1),
    )


def test_filters_by_target_time_and_minimum_quantity() -> None:
    slots = (
        Slot("08:15", 3),
        Slot("08:30", 1),
        Slot("08:45", 2),
        Slot("09:15", 8),
    )

    assert find_matching_slots(slots, ("08:15", "08:30", "08:45", "09:00"), 2) == (
        Slot("08:15", 3),
        Slot("08:45", 2),
    )


def test_raises_when_page_shape_is_unrecognised() -> None:
    with pytest.raises(ParseError, match="time slots"):
        parse_slots("The site layout changed and there are no recognisable slots")
