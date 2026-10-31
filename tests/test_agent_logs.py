
from types import SimpleNamespace

from app.agent_tools import get_recent_logs


def test_get_recent_logs_success(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout="INFO: Application started\n",
            stderr="WARNING: Something happened\n",
        )

    monkeypatch.setattr(
        "app.agent_tools.subprocess.run",
        fake_run,
    )

    result = get_recent_logs()

    assert result["success"] is True
    assert "Application started" in result["logs"]
    assert "Something happened" in result["logs"]


def test_get_recent_logs_failure(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="No such container",
        )

    monkeypatch.setattr(
        "app.agent_tools.subprocess.run",
        fake_run,
    )

    result = get_recent_logs()

    assert result["success"] is False
    assert "No such container" in result["error"]


def test_get_recent_logs_timeout(monkeypatch):
    import subprocess

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="docker logs",
            timeout=10,
        )

    monkeypatch.setattr(
        "app.agent_tools.subprocess.run",
        fake_run,
    )

    result = get_recent_logs()

    assert result["success"] is False
    assert "timed out" in result["error"]
