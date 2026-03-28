from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
Session = sessionmaker(bind=engine)


def get_engine():
    return engine


def run_sql(query: str, params: dict = None):
    """Execute a raw SQL statement (DDL or DML)."""
    with engine.connect() as conn:
        conn.execute(text(query), params or {})
        conn.commit()


def query_df(query: str, params: dict = None) -> pd.DataFrame:
    """Run a SELECT query and return a DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


def table_exists(table_name: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :t)"
        ), {"t": table_name})
        return result.scalar()


def get_table_count(table_name: str) -> int:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()
