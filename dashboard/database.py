from __future__ import annotations

import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine


def default_database_url() -> str:
    return os.getenv("DASHBOARD_DATABASE_URL", "sqlite:///./agentic_dashboard.db")


def create_db_engine(database_url: str | None = None):
    url = database_url or default_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


def init_db(engine) -> None:
    SQLModel.metadata.create_all(engine)


def get_session(engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
