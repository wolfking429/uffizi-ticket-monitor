from __future__ import annotations

import json

from uffizi_monitor.availability import Slot
from uffizi_monitor.notifiers import Alert, send_email, send_pushplus


class FakeResponse:
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return b'{"code":200,"msg":"ok"}'


class FakeSmtp:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        self.connection = (host, port, timeout)
        self.login_args: tuple[str, str] | None = None
        self.message = None

    def __enter__(self) -> "FakeSmtp":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def login(self, user: str, password: str) -> None:
        self.login_args = (user, password)

    def send_message(self, message: object) -> None:
        self.message = message


def sample_alert(test: bool = False) -> Alert:
    return Alert(
        target_date="2031-04-15",
        matching_slots=(Slot("08:30", 3), Slot("09:00", 2)),
        event_url="https://tickets.example/event/abc",
        is_test=test,
    )


def test_pushplus_payload_contains_slots_and_purchase_link() -> None:
    captured = {}

    def opener(request: object, timeout: int) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    send_pushplus(sample_alert(), "secret-token", opener=opener)

    request = captured["request"]
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["token"] == "secret-token"
    assert "08:30（余票 3）" in payload["content"]
    assert "09:00（余票 2）" in payload["content"]
    assert "https://tickets.example/event/abc" in payload["content"]
    assert captured["timeout"] == 20


def test_email_logs_in_with_auth_code_and_sends_utf8_message() -> None:
    created: list[FakeSmtp] = []

    def factory(host: str, port: int, timeout: int) -> FakeSmtp:
        smtp = FakeSmtp(host, port, timeout)
        created.append(smtp)
        return smtp

    send_email(
        sample_alert(),
        smtp_user="sender@163.com",
        smtp_auth_code="smtp-auth-code",
        recipient="receiver@example.com",
        smtp_factory=factory,
    )

    smtp = created[0]
    assert smtp.connection == ("smtp.163.com", 465, 20)
    assert smtp.login_args == ("sender@163.com", "smtp-auth-code")
    assert smtp.message["To"] == "receiver@example.com"
    assert "08:30" in smtp.message.get_content()
    assert "smtp-auth-code" not in smtp.message.as_string()


def test_test_notification_is_clearly_labelled() -> None:
    alert = sample_alert(test=True)

    assert "测试" in alert.subject
    assert "不代表真实余票" in alert.body
