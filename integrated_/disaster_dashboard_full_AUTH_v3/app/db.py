import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_SessionLocal = None

def init_db(app):
    global _engine, _SessionLocal
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    _engine = create_engine(uri, pool_pre_ping=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    # Ensure upload dir exists
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

def get_db_session():
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized. Call init_db(app) first.")
    return _SessionLocal()
