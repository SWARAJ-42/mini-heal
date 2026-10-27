import logging
import time

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, Integer, String, select, text
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database import Base, SessionLocal, engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miniheal")

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    completed: bool
    created_at: datetime


def get_db():
    with SessionLocal() as db:
        yield db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="MiniHeal", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request, call_next):
    started_at = time.perf_counter()

    response = await call_next(request)

    duration_ms = round(
        (time.perf_counter() - started_at) * 1000,
        2,
    )

    logger.info(
        "request method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response



@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        logger.exception("Health check failed: database unavailable")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "unavailable",
            },
        )


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
):
    task = Task(title=payload.title.strip())

    if not task.title:
        raise HTTPException(
            status_code=422,
            detail="Title cannot be blank",
        )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return db.scalars(
        select(Task).order_by(Task.id)
    ).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task