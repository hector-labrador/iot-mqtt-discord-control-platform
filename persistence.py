
from __future__ import annotations
import datetime as dt
import logging
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
import config

logger = logging.getLogger(__name__)
Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    device_type: Mapped[str] = mapped_column(String)          # sensor|switch|clock
    last_state: Mapped[str | None] = mapped_column(String, nullable=True)
    last_updated: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[str] = mapped_column(String)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    condition: Mapped[str] = mapped_column(String)   # Python expr usando `event`
    action: Mapped[str] = mapped_column(String)      # Python code usando `controller`

_engine = create_engine(f"sqlite:///{config.SQLITE_DB}", echo=config.DEBUG)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)

def init_db() -> None:
    logger.info("Inicializando SQLite DB en %s", config.SQLITE_DB)
    Base.metadata.create_all(bind=_engine)

def get_session() -> Session:
    return SessionLocal()