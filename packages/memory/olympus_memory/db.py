import os
import psycopg2
from typing import Optional


def get_connection() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        dbname=os.environ.get("POSTGRES_DB", "cognitive"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
    )
    return conn


def ensure_base_schema(conn: Optional[psycopg2.extensions.connection] = None) -> None:
    own = False
    if conn is None:
        conn = get_connection()
        own = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  id SERIAL PRIMARY KEY,
                  version VARCHAR(255) UNIQUE NOT NULL,
                  applied_at TIMESTAMPTZ NOT NULL DEFAULT (now())
                );
                """
            )
        conn.commit()
    finally:
        if own:
            conn.close()


def apply_migrations(conn: Optional[psycopg2.extensions.connection] = None) -> None:
    own = False
    if conn is None:
        conn = get_connection()
        own = True
    try:
        ensure_base_schema(conn)
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        with conn.cursor() as cur:
            cur.execute("SELECT version FROM schema_migrations")
            applied_migrations = set(row[0] for row in cur.fetchall())

        for migration_file in sorted(os.listdir(migrations_dir)):
            if migration_file.endswith(".sql") and migration_file not in applied_migrations:
                with open(os.path.join(migrations_dir, migration_file), "r") as f:
                    sql = f.read()
                    with conn.cursor() as cur:
                        cur.execute(sql)
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)", (migration_file,)
                    )
        conn.commit()
    finally:
        if own:
            conn.close()