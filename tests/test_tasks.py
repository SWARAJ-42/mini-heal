
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db


@pytest.fixture
def client():
    # Give each test its own in-memory SQLite database.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        with TestSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def test_create_and_list_task(client):
    response = client.post(
        "/tasks",
        json={"title": "Learn testing"},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Learn testing"

    task_id = response.json()["id"]

    list_response = client.get("/tasks")

    assert list_response.status_code == 200
    assert any(
        task["id"] == task_id
        for task in list_response.json()
    )


def test_missing_task_returns_404(client):
    response = client.get("/tasks/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_blank_title_is_rejected(client):
    response = client.post(
        "/tasks",
        json={"title": "   "},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Title cannot be blank"


def test_title_over_200_characters_is_rejected(client):
    response = client.post(
        "/tasks",
        json={"title": "a" * 201},
    )

    assert response.status_code == 422


def test_missing_title_is_rejected(client):
    response = client.post("/tasks", json={})

    assert response.status_code == 422


def test_new_task_defaults_to_incomplete(client):
    response = client.post(
        "/tasks",
        json={"title": "Write tests"},
    )

    assert response.status_code == 201
    assert response.json()["completed"] is False
