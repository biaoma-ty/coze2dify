from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from api.endpoints import sync as sync_endpoints
from config import settings
from db.database import engine
from db import models as _db_models  # noqa: F401


def project_alembic_config() -> Config:
    config = Config(str(Path(__file__).resolve().with_name("alembic.ini")))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def expected_schema_heads() -> tuple[str, ...]:
    return tuple(ScriptDirectory.from_config(project_alembic_config()).get_heads())


def current_schema_heads() -> tuple[str, ...]:
    with engine.connect() as connection:
        return tuple(MigrationContext.configure(connection).get_current_heads())


def ensure_project_ready() -> None:
    expected_heads = expected_schema_heads()
    current_heads = current_schema_heads()

    if not current_heads:
        raise RuntimeError(
            "Project database is not migrated. Run `python -m alembic upgrade head` before starting the API."
        )

    if set(current_heads) != set(expected_heads):
        raise RuntimeError(
            "Project database schema is out of date "
            f"(current: {', '.join(current_heads)}; expected: {', '.join(expected_heads)}). "
            "Run `python -m alembic upgrade head` before starting the API."
        )

    sync_endpoints.restore_schedules()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_project_ready()
    yield


app = FastAPI(
    title="Coze2Dify",
    description="Coze to Dify workflow migration tool",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
