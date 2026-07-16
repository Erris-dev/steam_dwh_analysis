"""SQLAlchemy engine for the Steam data warehouse."""

from sqlalchemy import Engine, create_engine

from app.config import settings

engine: Engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    # Postgres drops idle connections; check one is alive before handing it out.
    pool_pre_ping=True,
)
