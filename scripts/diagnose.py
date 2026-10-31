
import json
import subprocess
import urllib.error
import urllib.request


from app import config


def get_container_status():
    result = subprocess.run(
        [
            "docker", "inspect",
            "--format", "{{.State.Status}}",
            config.CONTAINER_NAME,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0:
        return "unknown"

    return result.stdout.strip()


def get_health():
    try:
        with urllib.request.urlopen(
            config.HEALTH_URL, timeout=3
        ) as response:
            body = json.loads(response.read())
            return {
                "reachable": True,
                "http_status": response.status,
                "body": body,
            }

    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read())
        except (ValueError, OSError):
            body = {}

        return {
            "reachable": True,
            "http_status": exc.code,
            "body": body,
        }

    except (urllib.error.URLError, TimeoutError, OSError):
        return {
            "reachable": False,
            "http_status": None,
            "body": {},
        }


def diagnose(container_status, health):
    if container_status != "running":
        return "CONTAINER_NOT_RUNNING"

    if not health["reachable"]:
        return "SERVICE_UNREACHABLE"

    if health["http_status"] != 200:
        return "HEALTH_CHECK_FAILED"

    if health["body"].get("database") != "ok":
        return "DATABASE_UNHEALTHY"

    return "HEALTHY"


def main():
    container_status = get_container_status()
    health = get_health()

    report = {
        "container": container_status,
        "health": health,
        "diagnosis": diagnose(container_status, health),
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
