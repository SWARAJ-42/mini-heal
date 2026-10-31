from app.agent_tools import (
    get_container_status,
    check_health,
)


def test_get_container_status():
    result = get_container_status()

    assert "success" in result

    if result["success"]:
        assert result["container"] == "miniheal-api"
        assert result["status"] in {
            "running",
            "exited",
            "created",
            "restarting",
            "paused",
            "dead",
        }


def test_check_health():
    result = check_health()

    assert "success" in result

    if result["success"]:
        assert isinstance(result["http_status"], int)
        assert "body" in result