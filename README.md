# MiniHeal

Run commands from the project root.

## Configuration

Edit `.env` to change runtime settings. For a new checkout, copy
`.env.example` to `.env` first. `app/config.py` loads this file using the
project's location, so loading it does not depend on the working directory.
Existing environment variables take priority over `.env`. Restart the app or
rerun a script after changing settings.

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | Application title and name used in incident reports |
| `CONTAINER_NAME` | Existing Docker container to inspect |
| `HEALTH_URL` | Full health endpoint URL to check |
| `DATABASE_URL` | SQLAlchemy database connection URL |
| `MINIHEAL_SIMULATE_DB_FAILURE` | `1` enables simulated failure; `0` disables it |
| `OPENAI_API_KEY` | API key required for AI investigation |
| `OPENAI_MODEL` | Model used for AI investigation |

Changing `CONTAINER_NAME` or `HEALTH_URL` changes the monitoring target; it
does not rename a Docker container or change the API server's listening port.
The default SQLite path is relative to the process's working directory.

## Run locally

```powershell
uv sync
uv run uvicorn app.main:app --reload
```

Inspect the configured container and health endpoint:

```powershell
uv run -m scripts.diagnose
uv run -m scripts.investigate
```

After setting `OPENAI_API_KEY` in `.env`, run AI investigation on the sample
incident evidence:

```powershell
uv run -m scripts.try_ai_investigator
```

Use `-m` for these scripts so Python can resolve the `app` package. When
running the Docker image, pass settings with `docker run --env-file .env ...`;
the image does not contain your local `.env` file.