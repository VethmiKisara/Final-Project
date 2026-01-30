"""Create the PostgreSQL database schema using SQLAlchemy models."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base  # relative import


def get_database_url():
    return os.getenv("DATABASE_URL", "postgresql+psycopg2://rtmd_user:change_me@localhost:5432/rtmd")


def main():
    db_url = get_database_url()
    engine = create_engine(db_url, echo=False, future=True)
    print(f"Creating database schema on {db_url}")
    Base.metadata.create_all(engine)
    print("Schema created successfully")


if __name__ == "__main__":
    main()
