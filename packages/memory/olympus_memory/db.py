# packages/memory/olympus_memory/db.py
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Public helpers expected by tests and callers that import `olympus_memory`
# These are light wrappers around sqlite3 to ensure WAL mode and a base
# schema exists, separate from the richer MemoryDB below.
_ENV_DB_PATH_KEYS = ("OLYMPUS_DB_PATH", "OLYMPUS_DB")

def _db_path_from_env() -> str:
    for k in _ENV_DB_PATH_KEYS:
        v = os.getenv(k)
        if v:
            return v
    return DEFAULT_DB_PATH

def get_connection(readonly: bool = False) -> sqlite3.Connection:
    """
    Return a sqlite3 connection to the configured DB path, enabling WAL.
    When readonly=True, opens in read-only mode when possible.
    """
    path = _db_path_from_env()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if readonly:
        uri = f"file:{path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    else:
        conn = sqlite3.connect(path, check_same_thread=False)
    # Ensure row factory is tuple by default for simple tests
    with conn:
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
    return conn

def ensure_base_schema() -> None:
    """
    Create a minimal base schema used by tests, including schema_migrations.
    Idempotent.
    """
    conn = get_connection(readonly=False)
    try:
        with conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER NOT NULL)"
            )
    finally:
        conn.close()

DEFAULT_DB_PATH = os.getenv(
    "OLYMPUS_DB_PATH",
    os.getenv("OLYMPUS_DB", os.path.abspath(".data/olympus.db")),
)

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER NOT NULL
);

INSERT INTO schema_version(version) SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM schema_version);

CREATE TABLE IF NOT EXISTS plans (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  state TEXT NOT NULL,
  budget_json TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS steps (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  name TEXT NOT NULL,
  state TEXT NOT NULL,
  attempts INTEGER NOT NULL,
  max_retries INTEGER NOT NULL,
  capability_json TEXT NOT NULL,
  input_json TEXT NOT NULL,
  output_json TEXT,
  error TEXT,
  deps_json TEXT NOT NULL,
  guard_json TEXT NOT NULL,
  started_at INTEGER,
  ended_at INTEGER,
  FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  ts INTEGER NOT NULL,
  type TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  step_id TEXT,
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_plan ON events(plan_id, ts);

CREATE TABLE IF NOT EXISTS cache_items (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  meta_json TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  expires_at INTEGER
);

CREATE TABLE IF NOT EXISTS facts (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  data_json TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relations (
  id TEXT PRIMARY KEY,
  src_id TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  type TEXT NOT NULL,
  data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS embeddings (
  id TEXT PRIMARY KEY,
  dim INTEGER NOT NULL,
  vector BLOB NOT NULL,
  meta_json TEXT NOT NULL
);
"""


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


class MemoryDB:
    """Lightweight SQLite store for plans, steps, events, cache, and knowledge graph."""

    def __init__(self, path: str = DEFAULT_DB_PATH):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = _dict_factory
        with self._conn:
            self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # ----------------- Plans & Steps -----------------
    def upsert_plan(self, plan_dict: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO plans(id,title,state,budget_json,metadata_json,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                     title=excluded.title, state=excluded.state,
                     budget_json=excluded.budget_json, metadata_json=excluded.metadata_json,
                     updated_at=excluded.updated_at
                """,
                (
                    plan_dict["id"],
                    plan_dict["title"],
                    plan_dict["state"],
                    json.dumps(plan_dict["budget"]),
                    json.dumps(plan_dict.get("metadata", {})),
                    plan_dict["created_at"],
                    plan_dict["updated_at"],
                ),
            )

    def upsert_step(self, step_dict: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO steps(id,plan_id,name,state,attempts,max_retries,
                                     capability_json,input_json,output_json,error,
                                     deps_json,guard_json,started_at,ended_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                     plan_id=excluded.plan_id, name=excluded.name, state=excluded.state,
                     attempts=excluded.attempts, max_retries=excluded.max_retries,
                     capability_json=excluded.capability_json, input_json=excluded.input_json,
                     output_json=excluded.output_json, error=excluded.error,
                     deps_json=excluded.deps_json, guard_json=excluded.guard_json,
                     started_at=excluded.started_at, ended_at=excluded.ended_at
                """,
                (
                    step_dict["id"],
                    step_dict["plan_id"],
                    step_dict["name"],
                    step_dict["state"],
                    step_dict["attempts"],
                    step_dict.get("max_retries", 0),
                    json.dumps(step_dict["capability"]),
                    json.dumps(step_dict.get("input", {})),
                    json.dumps(step_dict.get("output")) if step_dict.get("output") is not None else None,
                    step_dict.get("error"),
                    json.dumps(step_dict.get("deps", [])),
                    json.dumps(step_dict.get("guard", {})),
                    step_dict.get("started_at"),
                    step_dict.get("ended_at"),
                ),
            )

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
            if not row:
                return None
            row["budget"] = json.loads(row.pop("budget_json"))
            row["metadata"] = json.loads(row.pop("metadata_json"))
            return row

    def get_steps(self, plan_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM steps WHERE plan_id=? ORDER BY id", (plan_id,)).fetchall()
            for r in rows:
                r["capability"] = json.loads(r.pop("capability_json"))
                r["input"] = json.loads(r.pop("input_json"))
                r["deps"] = json.loads(r.pop("deps_json"))
                r["guard"] = json.loads(r.pop("guard_json"))
                if r.get("output_json") is not None:
                    r["output"] = json.loads(r.pop("output_json"))
                else:
                    r["output"] = None
            return rows

    # ----------------- Events (append-only transcript) -----------------
    def append_event(self, ev: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO events(id,ts,type,plan_id,step_id,payload_json)
                   VALUES(?,?,?,?,?,?)""",
                (
                    ev["id"],
                    ev["ts"],
                    ev["type"],
                    ev["plan_id"],
                    ev.get("step_id"),
                    json.dumps(ev.get("payload", {})),
                ),
            )

    def events_for_plan(self, plan_id: str) -> Iterable[Dict[str, Any]]:
        with self._lock:
            for r in self._conn.execute(
                "SELECT * FROM events WHERE plan_id=? ORDER BY ts ASC", (plan_id,)
            ):
                r["payload"] = json.loads(r.pop("payload_json"))
                yield r

    # ----------------- Cache (CAG) -----------------
    def cache_get(self, key: str, now_ms: Optional[int] = None) -> Optional[Dict[str, Any]]:
        now_ms = now_ms or int(time.time() * 1000)
        with self._lock:
            row = self._conn.execute("SELECT * FROM cache_items WHERE key=?", (key,)).fetchone()
            if not row:
                return None
            if row["expires_at"] is not None and row["expires_at"] < now_ms:
                # expired: delete
                with self._conn:
                    self._conn.execute("DELETE FROM cache_items WHERE key=?", (key,))
                return None
            return {
                "key": row["key"],
                "value": json.loads(row["value_json"]),
                "meta": json.loads(row["meta_json"]),
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
            }

    def cache_put(self, key: str, value: Dict[str, Any], ttl_ms: Optional[int], meta: Optional[Dict[str, Any]] = None) -> None:
        now_ms = int(time.time() * 1000)
        exp = None if ttl_ms is None else now_ms + ttl_ms
        meta = meta or {}
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO cache_items(key,value_json,meta_json,created_at,expires_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(key) DO UPDATE SET
                     value_json=excluded.value_json,
                     meta_json=excluded.meta_json,
                     created_at=excluded.created_at,
                     expires_at=excluded.expires_at
                """,
                (key, json.dumps(value), json.dumps(meta), now_ms, exp),
            )

    # ----------------- Facts / Entities / Relations / Embeddings -----------------
    def add_fact(self, fact_id: str, kind: str, data: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO facts(id,kind,data_json,created_at) VALUES(?,?,?,?)",
                (fact_id, kind, json.dumps(data), int(time.time() * 1000)),
            )

    def upsert_entity(self, ent_id: str, ent_type: str, data: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO entities(id,type,data_json) VALUES(?,?,?)",
                (ent_id, ent_type, json.dumps(data)),
            )

    def upsert_relation(self, rel_id: str, src_id: str, dst_id: str, rel_type: str, data: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO relations(id,src_id,dst_id,type,data_json) VALUES(?,?,?,?,?)",
                (rel_id, src_id, dst_id, rel_type, json.dumps(data)),
            )

    def put_embedding(self, emb_id: str, vector: bytes, dim: int, meta: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO embeddings(id,dim,vector,meta_json) VALUES(?,?,?,?)",
                (emb_id, dim, vector, json.dumps(meta)),
            )
