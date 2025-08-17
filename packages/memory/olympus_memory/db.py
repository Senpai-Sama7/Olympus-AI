import os
import sqlite3
from typing import Optional


def _db_path() -> str:
	return os.environ.get("OLYMPUS_DB_PATH", os.path.join(os.getcwd(), "data", "olympus.db"))


def get_connection(readonly: bool = False) -> sqlite3.Connection:
	path = _db_path()
	os.makedirs(os.path.dirname(path), exist_ok=True)
	uri = f"file:{path}?mode={'ro' if readonly else 'rwc'}"
	conn = sqlite3.connect(uri, uri=True, isolation_level=None)
	# Reliability pragmas
	try:
		conn.execute("PRAGMA journal_mode=WAL;")
		conn.execute("PRAGMA synchronous=NORMAL;")
		conn.execute("PRAGMA busy_timeout=5000;")
	except Exception:
		pass
	return conn


def ensure_base_schema(conn: Optional[sqlite3.Connection] = None) -> None:
	own = False
	if conn is None:
		conn = get_connection()
		own = True
	try:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS schema_migrations (
			  id INTEGER PRIMARY KEY AUTOINCREMENT,
			  version TEXT UNIQUE NOT NULL,
			  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
			);
			"""
		)
	finally:
		if own:
			conn.close()
