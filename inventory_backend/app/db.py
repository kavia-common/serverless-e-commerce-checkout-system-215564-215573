import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, DeclarativeBase


# PUBLIC_INTERFACE
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models used across the application."""


def _get_database_url() -> str:
    """
    Resolve the database URL from environment, falling back to SQLite file-based DB.
    Environment variable used: DATABASE_URL
    """
    # Do NOT hardcode in code, we read from env; orchestrator will provide real values.
    return os.getenv("DATABASE_URL", "sqlite:///./inventory.db")


# Create SQLAlchemy engine; For SQLite ensure check_same_thread is false for threaded flask dev server
DATABASE_URL = _get_database_url()
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, **engine_kwargs)

# Configure session factory and scoped session for request context usage
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


@contextmanager
def session_scope() -> Generator:
    """
    Provide a transactional scope around a series of operations.

    Yields:
        SQLAlchemy session bound to current context.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# PUBLIC_INTERFACE
def init_db(create_all: bool = True) -> None:
    """Initialize database, optionally creating all tables."""
    if create_all:
        # Import models to ensure they are registered with Base.metadata
        from .models import product, order  # noqa: F401
        Base.metadata.create_all(bind=engine)
