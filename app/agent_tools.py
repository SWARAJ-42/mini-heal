import subprocess
import urllib.error
import urllib.request


from app import config
from app.config import PROJECT_ROOT

from pathlib import Path



ALLOWED_SOURCE_FILES = {
    "app/main.py": PROJECT_ROOT / "app" / "main.py",
    "app/database.py": PROJECT_ROOT / "app" / "database.py",
    "app/config.py": PROJECT_ROOT / "app" / "config.py",
}


def inspect_source_file(file_path: str) -> dict:
    """Read a specific allowlisted source file."""

    if file_path not in ALLOWED_SOURCE_FILES:
        return {
            "success": False,
            "error": "This source file is not allowlisted.",
        }

    path = ALLOWED_SOURCE_FILES[file_path]

    try:
        if not path.is_file():
            return {
                "success": False,
                "error": "Source file does not exist.",
            }

        # Avoid returning unexpectedly large files.
        if path.stat().st_size > 20_000:
            return {
                "success": False,
                "error": "Source file exceeds the 20 KB limit.",
            }

        content = path.read_text(encoding="utf-8")

        return {
            "success": True,
            "file_path": file_path,
            "content": content,
        }

    except OSError as error:
        return {
            "success": False,
            "error": f"Unable to read source file: {error}",
        }



def get_container_status() -> dict:
    """Return the status of the MiniHeal Docker container."""

    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Status}}",
                config.CONTAINER_NAME,
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip(),
            }

        return {
            "success": True,
            "container": config.CONTAINER_NAME,
            "status": result.stdout.strip(),
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Docker command timed out"}


def check_health() -> dict:
    """Check the MiniHeal health endpoint."""

    try:
        with urllib.request.urlopen(
            config.HEALTH_URL,
            timeout=5,
        ) as response:
            return {
                "success": True,
                "http_status": response.status,
                "body": response.read(4096).decode("utf-8"),
            }

    except urllib.error.HTTPError as error:
        return {
            "success": True,
            "http_status": error.code,
            "body": error.read(4096).decode("utf-8"),
        }

    except (urllib.error.URLError, TimeoutError) as error:
        return {
            "success": False,
            "error": str(error),
        }


def get_recent_logs() -> dict:
    """Retrieve the last 50 lines of the configured container logs."""

    try:
        result = subprocess.run(
            [
                "docker",
                "logs",
                "--tail",
                "50",
                config.CONTAINER_NAME,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip()[:1000],
            }

        # Docker can write logs to both stdout and stderr.
        logs = "\n".join(
            part.strip()
            for part in (result.stdout, result.stderr)
            if part.strip()
        )

        return {
            "success": True,
            "container": config.CONTAINER_NAME,
            "logs": logs[-12000:],
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Docker log retrieval timed out.",
        }
