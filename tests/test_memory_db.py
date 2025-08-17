from olympus_memory import ensure_base_schema, get_connection


def test_ensure_base_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "olympus.db"
    monkeypatch.setenv("OLYMPUS_DB_PATH", str(db_path))
    ensure_base_schema()
    conn = get_connection(readonly=True)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
        ).fetchall()
        assert rows
    finally:
        conn.close()
