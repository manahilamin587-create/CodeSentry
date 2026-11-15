import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "codesentry.db"  # backend/codesentry.db


@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL,
                finding_json TEXT NOT NULL,
                proposal_json TEXT NOT NULL,
                original_source TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                decided_at TEXT
            )
            """
        )


def save_proposal(project_path: str, finding_json: str, proposal_json: str) -> int:
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO proposals (project_path, finding_json, proposal_json, status, created_at) "
            "VALUES (?, ?, ?, 'pending', ?)",
            (project_path, finding_json, proposal_json, _now()),
        )
        return cur.lastrowid


def get_proposal(proposal_id: int) -> dict | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        return dict(row) if row else None


def set_status(proposal_id: int, status: str, original_source: str | None = None) -> None:
    with _db() as conn:
        conn.execute(
            "UPDATE proposals SET status = ?, decided_at = ?, "
            "original_source = COALESCE(?, original_source) WHERE id = ?",
            (status, _now(), original_source, proposal_id),
        )