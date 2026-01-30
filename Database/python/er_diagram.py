"""Optional: generate ER diagram from SQLAlchemy models (requires graphviz and sqlalchemy_schemadisplay).

Usage:
    pip install sqlalchemy_schemadisplay graphviz
    python er_diagram.py
"""
import os

try:
    from sqlalchemy import create_engine
    from sqlalchemy_schemadisplay import create_schema_graph
    from sqlalchemy.orm import registry
except Exception as exc:  # pragma: no cover - optional dependency
    raise SystemExit("Required packages for ER diagram are not installed. Install sqlalchemy_schemadisplay and graphviz.") from exc

from models import Base


def main():
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://rtmd_user:change_me@localhost:5432/rtmd")
    engine = create_engine(db_url)

    graph = create_schema_graph(metadata=Base.metadata)
    out = "er_diagram.png"
    graph.write_png(out)
    print(f"ER diagram written to {out}")


if __name__ == "__main__":
    main()
