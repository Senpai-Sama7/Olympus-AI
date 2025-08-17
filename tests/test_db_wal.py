from olympus_memory import get_connection


def test_sqlite_wal(monkeypatch, tmp_path):
    p = tmp_path / "db.sqlite"
    monkeypatch.setenv("OLYMPUS_DB_PATH", str(p))
    conn = get_connection()
    try:
        row = conn.execute("PRAGMA journal_mode;").fetchone()
        assert row is not None
        assert str(row[0]).lower() == "wal"
    finally:
        conn.close()
