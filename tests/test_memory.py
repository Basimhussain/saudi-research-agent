from __future__ import annotations
import os
import tempfile
from memory.store import MemoryStore


def test_sqlite_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        store = MemoryStore(path=db, db_type="sqlite")
        cid = store.new_conversation(title="hello")
        store.append_message(cid, "user", {"text": "hi"})
        store.append_message(cid, "assistant", {"text": "how can I help"})
        msgs = store.load_messages(cid)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == {"text": "hi"}
        convs = store.list_conversations()
        assert any(c["id"] == cid for c in convs)


def test_postgres_requires_dsn(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    try:
        MemoryStore(db_type="postgres")
    except ValueError as e:
        assert "DATABASE_URL" in str(e)
    else:
        raise AssertionError("expected ValueError when DATABASE_URL missing")
