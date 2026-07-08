from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base


DEFAULT_DATABASE_URL = "postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen"


def create_engine_from_url(database_url: str = DEFAULT_DATABASE_URL, **kwargs: object) -> Engine:
    options = {"future": True}
    options.update(kwargs)
    return create_engine(database_url, **options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(engine)
