from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


class ParseError(RuntimeError):
    """Raised when the ticket page no longer contains recognisable slots."""


@dataclass(frozen=True)
class Slot:
    time: str
    available: int


_SLOT_PATTERN = re.compile(
    r"(?<!\d)([01]\d|2[0-3]):([0-5]\d)\s*\(\s*(\d+)\s*\)",
    re.MULTILINE,
)


def parse_slots(text: str) -> tuple[Slot, ...]:
    slots = tuple(
        Slot(time=f"{hour}:{minute}", available=int(count))
        for hour, minute, count in _SLOT_PATTERN.findall(text)
    )
    if not slots:
        raise ParseError("No recognisable time slots were found on the page")
    return slots


def find_matching_slots(
    slots: Iterable[Slot], target_times: Iterable[str], min_tickets: int
) -> tuple[Slot, ...]:
    wanted = set(target_times)
    return tuple(
        slot for slot in slots if slot.time in wanted and slot.available >= min_tickets
    )

