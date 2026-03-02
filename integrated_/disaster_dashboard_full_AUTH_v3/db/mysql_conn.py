from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error
from .db_config import DB_CONFIG


@contextmanager
def get_conn():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def fetchall_dict(cur):
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]