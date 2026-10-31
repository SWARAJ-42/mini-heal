
from app.agent_tools import inspect_source_file
from app.ai_investigator import execute_tool


def test_inspect_allowed_source_file():
    result = inspect_source_file("app/main.py")

    assert result["success"] is True
    assert result["file_path"] == "app/main.py"
    assert len(result["content"]) > 0


def test_reject_unlisted_file():
    result = inspect_source_file(".env")

    assert result["success"] is False


def test_reject_path_traversal():
    result = inspect_source_file("../../.env")

    assert result["success"] is False


def test_dispatch_source_inspection():
    result = execute_tool(
        "inspect_source_file",
        '{"file_path": "app/database.py"}',
    )

    assert result["success"] is True
    assert result["file_path"] == "app/database.py"


def test_reject_extra_source_arguments():
    result = execute_tool(
        "inspect_source_file",
        '{"file_path": "app/main.py", "other": "value"}',
    )

    assert result["success"] is False
