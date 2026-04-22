from __future__ import annotations
import json
import logging
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

log = logging.getLogger(__name__)

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    title       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,
    content_json    TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
"""


def _env_int(name, default):
    v = os.environ.get(name)
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


class MemoryStore:
    def __init__(self, path=None, db_type=None, dsn=None):
        self.db_type = (db_type or os.environ.get("DB_TYPE", "sqlite")).lower()
        self._pool = None

        if self.db_type == "postgres":
            self.dsn = dsn or os.environ.get("DATABASE_URL")
            if not self.dsn:
                raise ValueError("DATABASE_URL must be set for DB_TYPE=postgres")
            self.path = self.dsn
            self._pool_min = _env_int("DB_POOL_MIN", 1)
            self._pool_max = _env_int("DB_POOL_MAX", 10)
            self._connect_timeout = _env_int("DB_CONNECT_TIMEOUT", 5)
            self._stmt_timeout = _env_int("DB_STATEMENT_TIMEOUT_MS", 30000)
            self._retries = _env_int("DB_RETRY_ATTEMPTS", 5)
            self._retry_base = float(os.environ.get("DB_RETRY_BASE_DELAY") or 0.5)
            self._sslmode = os.environ.get("DB_SSLMODE", "prefer")
            self._app_name = os.environ.get("DB_APPLICATION_NAME", "saudi-research-agent")
            self._init_postgres()
        else:
            self.path = path or os.environ.get("DB_PATH", "./agent_memory.db")
            with self._sqlite() as c:
                c.executescript(SQLITE_SCHEMA)

    def _build_pool(self):
        from psycopg2.pool import ThreadedConnectionPool
        return ThreadedConnectionPool(
            minconn=self._pool_min,
            maxconn=self._pool_max,
            dsn=self.dsn,
            connect_timeout=self._connect_timeout,
            sslmode=self._sslmode,
            application_name=self._app_name,
            options=f"-c statement_timeout={self._stmt_timeout}",
        )

    def _init_postgres(self):
        from memory.migrations import apply_migrations
        self._pool = self._retry(self._build_pool, op="init_pool")
        with self._pg() as cur:
            applied = apply_migrations(cur)
        if applied:
            log.info("applied migrations: %s", applied)

    def _retry(self, fn, *args, op="db", **kw):
        import psycopg2
        err = None
        for i in range(1, self._retries + 1):
            try:
                return fn(*args, **kw)
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                err = e
                if i == self._retries:
                    break
                wait = self._retry_base * (2 ** (i - 1))
                log.warning("%s failed (%d/%d): %s, retry in %.2fs", op, i, self._retries, e, wait)
                time.sleep(wait)
        raise RuntimeError(f"{op} failed after {self._retries} attempts: {err}")

    @contextmanager
    def _sqlite(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    @contextmanager
    def _pg(self) -> Iterator[Any]:
        from psycopg2.extras import RealDictCursor
        conn = self._retry(self._pool.getconn, op="getconn")
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self):
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None

    def healthcheck(self):
        t0 = time.perf_counter()
        try:
            if self.db_type == "postgres":
                with self._pg() as cur:
                    cur.execute("SELECT version() AS v, NOW() AS now")
                    row = cur.fetchone()
                    cur.execute("SELECT COALESCE(MAX(version), 0) AS v FROM schema_version")
                    sv = cur.fetchone()
                return {
                    "ok": True,
                    "db_type": "postgres",
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                    "server_version": row["v"].split(" ")[1] if row else None,
                    "server_time": row["now"].isoformat() if row else None,
                    "schema_version": sv["v"] if sv else 0,
                    "pool": {"min": self._pool_min, "max": self._pool_max},
                }
            with self._sqlite() as c:
                c.execute("SELECT 1")
            return {
                "ok": True,
                "db_type": "sqlite",
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                "path": self.path,
            }
        except Exception as e:
            return {"ok": False, "db_type": self.db_type, "error": str(e)}

    def new_conversation(self, title=None):
        cid = str(uuid.uuid4())
        now = datetime.utcnow()
        if self.db_type == "postgres":
            with self._pg() as cur:
                cur.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (%s, %s, %s, %s)",
                    (cid, title, now, now),
                )
        else:
            with self._sqlite() as c:
                c.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (cid, title, now.isoformat(), now.isoformat()),
                )
        return cid

    def list_conversations(self, limit=20):
        if self.db_type == "postgres":
            with self._pg() as cur:
                cur.execute(
                    "SELECT id, title, created_at, updated_at FROM conversations "
                    "ORDER BY updated_at DESC LIMIT %s",
                    (limit,),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ]
        with self._sqlite() as c:
            rows = c.execute(
                "SELECT id, title, created_at, updated_at FROM conversations "
                "ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def append_message(self, conversation_id, role, content):
        now = datetime.utcnow()
        payload = json.dumps(content, ensure_ascii=False, default=str)
        if self.db_type == "postgres":
            with self._pg() as cur:
                cur.execute(
                    "INSERT INTO messages (conversation_id, role, content_json, created_at) "
                    "VALUES (%s, %s, %s::jsonb, %s)",
                    (conversation_id, role, payload, now),
                )
                cur.execute(
                    "UPDATE conversations SET updated_at = %s WHERE id = %s",
                    (now, conversation_id),
                )
        else:
            with self._sqlite() as c:
                c.execute(
                    "INSERT INTO messages (conversation_id, role, content_json, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (conversation_id, role, payload, now.isoformat()),
                )
                c.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now.isoformat(), conversation_id),
                )

    def load_messages(self, conversation_id):
        if self.db_type == "postgres":
            with self._pg() as cur:
                cur.execute(
                    "SELECT role, content_json FROM messages "
                    "WHERE conversation_id = %s ORDER BY id ASC",
                    (conversation_id,),
                )
                rows = cur.fetchall()
            out = []
            for r in rows:
                c = r["content_json"]
                out.append({"role": r["role"], "content": c if isinstance(c, (dict, list)) else json.loads(c)})
            return out
        with self._sqlite() as c:
            rows = c.execute(
                "SELECT role, content_json FROM messages "
                "WHERE conversation_id = ? ORDER BY id ASC",
                (conversation_id,),
            ).fetchall()
        return [{"role": r["role"], "content": json.loads(r["content_json"])} for r in rows]
