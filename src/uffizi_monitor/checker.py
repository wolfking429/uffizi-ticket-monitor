from __future__ import annotations

from datetime import date
import os
import re

from playwright.sync_api import Page, sync_playwright

from .availability import Slot, parse_slots


class SiteBlockedError(RuntimeError):
    """Raised when the official site rejects automated browser access."""


ITALIAN_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}


def month_offset(month_heading: str, target: date) -> int:
    match = re.fullmatch(r"\s*([A-Za-zÀ-ÿ]+)\s+(\d{4})\s*", month_heading)
    if not match:
        raise ValueError("Could not read the visible calendar month")
    month_name, year_text = match.groups()
    month = ITALIAN_MONTHS.get(month_name.casefold())
    if month is None:
        raise ValueError("Could not read the Italian calendar month")
    year = int(year_text)
    offset = (target.year - year) * 12 + target.month - month
    if offset < 0:
        raise ValueError("Target date is before the visible calendar month")
    return offset


def raise_if_site_blocked(text: str) -> None:
    lowered = " ".join(text.casefold().split())
    indicators = (
        "automation detected",
        "you have been blocked",
        "unable to access this website",
        "checking your browser",
    )
    if any(indicator in lowered for indicator in indicators):
        raise SiteBlockedError(
            "The official ticket site blocked this browser session; no inventory result "
            "was inferred"
        )


def extract_performance_region(body_text: str) -> str:
    start_marker = "Hai selezionato il giorno"
    end_marker = "Numero massimo di biglietti acquistabili"
    start = body_text.find(start_marker)
    end = body_text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise RuntimeError("The selected-day ticket area could not be found")
    return body_text[start:end]


def read_slots_from_page(page: Page, event_url: str, target: date) -> tuple[Slot, ...]:
    page.goto(event_url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(8_000)
    body = page.locator("body").inner_text(timeout=10_000)
    raise_if_site_blocked(body)

    page.get_by_role("heading", name="Seleziona la Data").wait_for(
        state="visible", timeout=20_000
    )
    month = page.locator('span[x-text="getMonthName(month)"]').inner_text()
    year = page.locator('span[x-text="year"]').inner_text()
    forward_steps = month_offset(f"{month} {year}", target)

    arrows = page.locator("button.transition.ease-in-out.duration-100.inline-flex")
    if arrows.count() != 2:
        raise RuntimeError("The calendar navigation controls could not be identified")
    next_month = arrows.nth(1)
    for _ in range(forward_steps):
        next_month.click(timeout=10_000)
        page.wait_for_timeout(800)

    expected_month = next(
        name for name, number in ITALIAN_MONTHS.items() if number == target.month
    )
    visible_month = page.locator('span[x-text="getMonthName(month)"]').inner_text()
    visible_year = page.locator('span[x-text="year"]').inner_text()
    if visible_month.casefold() != expected_month or int(visible_year) != target.year:
        raise RuntimeError("The calendar did not reach the requested month")

    day = page.locator('div[x-text="date"]').filter(
        has_text=re.compile(rf"^{target.day}$")
    )
    if day.count() != 1:
        raise RuntimeError("The requested date could not be uniquely identified")
    day.click(timeout=10_000)

    page.get_by_text("Hai selezionato il giorno", exact=False).wait_for(
        state="visible", timeout=20_000
    )
    body = page.locator("body").inner_text(timeout=10_000)
    raise_if_site_blocked(body)
    return parse_slots(extract_performance_region(body))


def check_slots(event_url: str, target: date) -> tuple[Slot, ...]:
    headless = os.environ.get("BROWSER_HEADLESS", "1") != "0"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page(locale="it-IT", viewport={"width": 1440, "height": 1200})
        try:
            return read_slots_from_page(page, event_url, target)
        except Exception:
            page.screenshot(path="failure.png", full_page=True)
            raise
        finally:
            browser.close()

