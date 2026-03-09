from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from db.database import Base, engine
from db import models as _db_models  # noqa: F401

app = FastAPI(title="Coze2Dify", description="Coze to Dify workflow migration tool", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def ensure_project_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}
