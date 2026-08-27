from __future__ import annotations

from datetime import date

import pytest

from uffizi_monitor.availability import Slot
from uffizi_monitor.config import Config
from uffizi_monitor.main import run_monitor


def config() -> Config:
    return Config(
        event_url="https://tickets.example/event/abc",
        target_date=date(2031, 4, 15),
        target_times=("08:15", "08:30", "08:45", "09:00"),
        min_tickets=2,
        pushplus_token="push-secret",
        smtp_user="sender@163.com",
        smtp_auth_code="smtp-secret",
        alert_email="receiver@example.com",
    )


def test_no_matching_slot_sends_nothing() -> None:
    sent = []

    result = run_monitor(
        config(),
        checker=lambda *_: (Slot("08:15", 1), Slot("10:45", 99)),
        push_sender=lambda *args, **kwargs: sent.append("push"),
        email_sender=lambda *args, **kwargs: sent.append("email"),
    )

    assert result == "no_match"
    assert sent == []


def test_matching_slots_send_both_channels_on_every_run() -> None:
    sent = []
    kwargs = {
        "checker": lambda *_: (Slot("08:30", 4), Slot("09:00", 2)),
        "push_sender": lambda alert, token: sent.append(("push", alert)),
        "email_sender": lambda alert, **options: sent.append(("email", alert)),
    }

    assert run_monitor(config(), **kwargs) == "alerted"
    assert run_monitor(config(), **kwargs) == "alerted"
    assert [channel for channel, _ in sent] == ["push", "email", "push", "email"]
    assert all(not alert.is_test for _, alert in sent)


def test_retries_checker_three_times_before_succeeding() -> None:
    attempts = []

    def flaky_checker(*_: object) -> tuple[Slot, ...]:
        attempts.append(1)
        if len(attempts) < 3:
            raise RuntimeError("temporary failure")
        return (Slot("10:45", 3),)

    result = run_monitor(config(), checker=flaky_checker, sleeper=lambda _: None)

    assert result == "no_match"
    assert len(attempts) == 3


def test_raises_after_three_failed_checks() -> None:
    attempts = []

    def broken_checker(*_: object) -> tuple[Slot, ...]:
        attempts.append(1)
        raise RuntimeError("website unavailable")

    with pytest.raises(RuntimeError, match="website unavailable"):
        run_monitor(config(), checker=broken_checker, sleeper=lambda _: None)

    assert len(attempts) == 3


def test_test_notification_does_not_run_checker_and_is_labelled() -> None:
    sent = []

    result = run_monitor(
        config(),
        test_notification=True,
        checker=lambda *_: pytest.fail("checker must not run in notification test mode"),
        push_sender=lambda alert, token: sent.append(alert),
        email_sender=lambda alert, **options: sent.append(alert),
    )

    assert result == "test_alerted"
    assert len(sent) == 2
    assert all(alert.is_test for alert in sent)
