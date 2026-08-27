from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_workflow_runs_every_ten_minutes_and_can_be_started_manually() -> None:
    workflow = (ROOT / ".github" / "workflows" / "monitor.yml").read_text(
        encoding="utf-8"
    )

    assert "3,13,23,33,43,53 * * * *" in workflow
    assert "workflow_dispatch:" in workflow
    assert "test_notification:" in workflow
    assert "timeout-minutes: 5" in workflow


def test_workflow_reads_all_private_settings_from_github_secrets() -> None:
    workflow = (ROOT / ".github" / "workflows" / "monitor.yml").read_text(
        encoding="utf-8"
    )
    expected = (
        "EVENT_URL",
        "TARGET_DATE",
        "TARGET_TIMES",
        "MIN_TICKETS",
        "PUSHPLUS_TOKEN",
        "SMTP_USER",
        "SMTP_AUTH_CODE",
        "ALERT_EMAIL",
    )

    for name in expected:
        assert f"${{{{ secrets.{name} }}}}" in workflow

    assert "tickets.uffizi.it/event/" not in workflow
    assert "2031-04-15" not in workflow
    assert "@163.com" not in workflow


def test_readme_warns_to_rotate_exposed_credentials() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "重新生成" in readme
    assert "SMTP 授权码" in readme
    assert "登录密码" in readme
    assert "SiteBlockedError" in readme
