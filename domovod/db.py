"""Подключение к базе данных (напрямую через SQLModel/SQLAlchemy).

`reflex.Model` и встроенные alembic-миграции Reflex объявлены устаревшими
(deprecated начиная с 0.9.2), поэтому здесь используется обычный SQLModel-движок.
"""

from __future__ import annotations

import os

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///domovod.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)


def init_db() -> None:
    """Создаёт таблицы, если их ещё нет (для демо — без миграций)."""
    from . import models  # noqa: F401  регистрирует модели в SQLModel.metadata

    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
