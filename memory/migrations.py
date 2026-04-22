from __future__ import annotations


def _v1(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              BIGSERIAL PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role            TEXT NOT NULL,
            content_json    JSONB NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC)")


def _v2(cur):
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(conversation_id, created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_content_gin ON messages USING GIN (content_json jsonb_path_ops)")


MIGRATIONS = [
    (1, "initial schema", _v1),
    (2, "message indexes", _v2),
]


def apply_migrations(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version     INT PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    cur.execute("SELECT version FROM schema_version")
    done = {r[0] if isinstance(r, tuple) else r["version"] for r in cur.fetchall()}
    applied = []
    for v, desc, fn in MIGRATIONS:
        if v in done:
            continue
        fn(cur)
        cur.execute("INSERT INTO schema_version (version, description) VALUES (%s, %s)", (v, desc))
        applied.append(v)
    return applied
