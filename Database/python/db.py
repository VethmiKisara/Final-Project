"""Database helper for SQLAlchemy engine and session maker."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://rtmd_user:change_me@localhost:5432/rtmd")

# Use a pool suitable for high-write workloads
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=10, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session():
    """Yield a SQLAlchemy session."""
    return SessionLocal()
