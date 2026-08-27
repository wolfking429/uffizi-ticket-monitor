from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import json
import smtplib
from typing import Callable
from urllib.request import Request, urlopen

from .availability import Slot


PUSHPLUS_ENDPOINT = "https://www.pushplus.plus/send"


@dataclass(frozen=True)
class Alert:
    target_date: str
    matching_slots: tuple[Slot, ...]
    event_url: str
    is_test: bool = False

    @property
    def subject(self) -> str:
        prefix = "【测试通知】" if self.is_test else "【乌菲兹有票】"
        return f"{prefix}{self.target_date} 早场门票提醒"

    @property
    def body(self) -> str:
        slots = "\n".join(
            f"- {slot.time}（余票 {slot.available}）" for slot in self.matching_slots
        )
        test_note = "\n这是测试消息，不代表真实余票。\n" if self.is_test else ""
        return (
            f"日期：{self.target_date}\n"
            f"符合条件的时段：\n{slots}\n"
            f"{test_note}"
            f"购票链接：{self.event_url}\n"
            "请尽快自行下单；本程序不会代购或付款。"
        )


def send_pushplus(
    alert: Alert,
    token: str,
    *,
    opener: Callable[..., object] | None = None,
) -> None:
    payload = json.dumps(
        {
            "token": token,
            "title": alert.subject,
            "content": alert.body.replace("\n", "<br>"),
            "template": "html",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        PUSHPLUS_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    open_request = opener or urlopen
    with open_request(request, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("code") != 200:
        raise RuntimeError("PushPlus rejected the notification")


def send_email(
    alert: Alert,
    *,
    smtp_user: str,
    smtp_auth_code: str,
    recipient: str,
    smtp_factory: Callable[..., object] | None = None,
) -> None:
    message = EmailMessage()
    message["Subject"] = alert.subject
    message["From"] = smtp_user
    message["To"] = recipient
    message.set_content(alert.body)

    factory = smtp_factory or smtplib.SMTP_SSL
    with factory("smtp.163.com", 465, timeout=20) as smtp:
        smtp.login(smtp_user, smtp_auth_code)
        smtp.send_message(message)

