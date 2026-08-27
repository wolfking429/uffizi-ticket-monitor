from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import date
import os
import time

from .availability import Slot, find_matching_slots
from .checker import check_slots
from .config import Config
from .notifiers import Alert, send_email, send_pushplus


CheckFunction = Callable[[str, date], tuple[Slot, ...]]


def _send_all(
    config: Config,
    alert: Alert,
    push_sender: Callable[..., None],
    email_sender: Callable[..., None],
) -> None:
    errors: list[Exception] = []
    try:
        push_sender(alert, config.pushplus_token)
    except Exception as exc:
        errors.append(exc)
        print(f"PushPlus notification failed: {type(exc).__name__}")

    try:
        email_sender(
            alert,
            smtp_user=config.smtp_user,
            smtp_auth_code=config.smtp_auth_code,
            recipient=config.alert_email,
        )
    except Exception as exc:
        errors.append(exc)
        print(f"Email notification failed: {type(exc).__name__}")

    if errors:
        raise RuntimeError("One or more notification channels failed") from errors[0]


def run_monitor(
    config: Config,
    *,
    test_notification: bool = False,
    checker: CheckFunction = check_slots,
    push_sender: Callable[..., None] = send_pushplus,
    email_sender: Callable[..., None] = send_email,
    sleeper: Callable[[float], None] = time.sleep,
) -> str:
    if test_notification:
        test_slot = Slot(config.target_times[0], config.min_tickets)
        alert = Alert(
            target_date=config.target_date.isoformat(),
            matching_slots=(test_slot,),
            event_url=config.event_url,
            is_test=True,
        )
        _send_all(config, alert, push_sender, email_sender)
        return "test_alerted"

    if date.today() > config.target_date:
        print("Target date has passed; check skipped")
        return "expired"

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            slots = checker(config.event_url, config.target_date)
            break
        except Exception as exc:
            last_error = exc
            print(f"Availability check attempt {attempt}/3 failed: {type(exc).__name__}")
            if attempt < 3:
                sleeper(5)
    else:
        assert last_error is not None
        raise last_error

    matches = find_matching_slots(slots, config.target_times, config.min_tickets)
    if not matches:
        print("No matching ticket slots")
        return "no_match"

    alert = Alert(
        target_date=config.target_date.isoformat(),
        matching_slots=matches,
        event_url=config.event_url,
    )
    _send_all(config, alert, push_sender, email_sender)
    print(f"Alert sent for {len(matches)} matching slot(s)")
    return "alerted"


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor museum ticket availability")
    parser.add_argument(
        "--test-notification",
        action="store_true",
        help="Send clearly labelled test messages without checking inventory",
    )
    args = parser.parse_args()
    config = Config.from_mapping(os.environ)
    run_monitor(config, test_notification=args.test_notification)


if __name__ == "__main__":
    main()

