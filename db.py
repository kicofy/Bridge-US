import os
import sqlite3
from typing import Any, Dict, List, Optional

from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash

import uuid


SECTION_ALIASES_TO_CODE: Dict[str, str] = {
    # English labels -> codes
    "First week": "first_week",
    "Housing & move-in": "housing_move_in",
    "Food & groceries": "food_groceries",
    "Transportation": "transportation",
    "Life admin": "life_admin",
    "Safety & scams": "safety_scams",
    # Chinese labels -> codes
    "落地第一周": "first_week",
    "找房与入住": "housing_move_in",
    "食物与超市": "food_groceries",
    "交通出行": "transportation",
    "办事与生活": "life_admin",
    "安全与诈骗": "safety_scams",
}

SUPPORTED_LANGS = {"en", "zh"}


def get_db() -> sqlite3.Connection:
    db: Optional[sqlite3.Connection] = g.get("db")
    if db is None:
        db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        db.row_factory = sqlite3.Row
        g.db = db
    return db


def close_db(_exc: BaseException | None = None) -> None:
    db: Optional[sqlite3.Connection] = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    os.makedirs(os.path.dirname(current_app.config["DATABASE_PATH"]), exist_ok=True)

    db = sqlite3.connect(current_app.config["DATABASE_PATH"])
    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              uid TEXT NOT NULL UNIQUE,
              email TEXT NOT NULL UNIQUE,
              username TEXT NOT NULL,
              password_hash TEXT NOT NULL,
              lang TEXT NOT NULL DEFAULT 'en',
              is_admin INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        # Lightweight schema evolution for early MVP (SQLite)
        # Add users fields if missing (safe for existing DBs created before new columns existed).
        existing_user_cols = {r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()}
        if "is_admin" not in existing_user_cols:
            db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              city TEXT,
              section TEXT NOT NULL,
              status TEXT NOT NULL,
              source_lang TEXT NOT NULL DEFAULT 'en',
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        # Lightweight schema evolution for early MVP (SQLite)
        # Add author fields if missing (safe for existing DBs).
        existing_cols = {r[1] for r in db.execute("PRAGMA table_info(posts)").fetchall()}
        if "author_name" not in existing_cols:
            db.execute("ALTER TABLE posts ADD COLUMN author_name TEXT")
        if "author_handle" not in existing_cols:
            db.execute("ALTER TABLE posts ADD COLUMN author_handle TEXT")
        if "author_user_id" not in existing_cols:
            db.execute("ALTER TABLE posts ADD COLUMN author_user_id INTEGER")
        if "reviewed_by_user_id" not in existing_cols:
            db.execute("ALTER TABLE posts ADD COLUMN reviewed_by_user_id INTEGER")
        if "review_note" not in existing_cols:
            db.execute("ALTER TABLE posts ADD COLUMN review_note TEXT")
        if "reviewed_at" not in existing_cols:
            db.execute("ALTER TABLE posts ADD COLUMN reviewed_at TEXT")

        # Normalize any old/free-text sections to stable codes (safe for early MVP)
        for alias, code in SECTION_ALIASES_TO_CODE.items():
            db.execute("UPDATE posts SET section = ? WHERE section = ?", (code, alias))
        db.commit()
    finally:
        db.close()


def list_approved_posts(
    *, limit: int = 50, city: Optional[str] = None, section: Optional[str] = None
) -> List[Dict[str, Any]]:
    db = get_db()
    q = """
    SELECT id, title, city, section, source_lang, created_at, author_name, author_handle
    FROM posts
    WHERE status = 'approved'
    """
    args: List[Any] = []

    if city:
        q += " AND lower(coalesce(city,'')) = lower(?)"
        args.append(city.strip())

    if section:
        q += " AND section = ?"
        args.append(section)

    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)

    rows = db.execute(q, tuple(args)).fetchall()
    return [dict(r) for r in rows]


def get_post_by_id(post_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    row = db.execute(
        """
        SELECT id, title, content, city, section, status, source_lang, created_at, updated_at, author_name, author_handle, author_user_id
        FROM posts
        WHERE id = ?
        """,
        (post_id,),
    ).fetchone()
    return dict(row) if row else None


def create_user(*, email: str, username: str, password: str, lang: str) -> Dict[str, Any]:
    email = email.strip().lower()
    username = username.strip()
    lang = (lang or "en").strip()
    if lang not in SUPPORTED_LANGS:
        lang = "en"

    uid = str(uuid.uuid4())
    password_hash = generate_password_hash(password)

    db = get_db()
    db.execute(
        """
        INSERT INTO users (uid, email, username, password_hash, lang)
        VALUES (?, ?, ?, ?, ?)
        """,
        (uid, email, username, password_hash, lang),
    )
    db.commit()
    return get_user_by_email(email)  # type: ignore[return-value]


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    row = db.execute(
        """
        SELECT id, uid, email, username, lang, created_at, password_hash
        FROM users
        WHERE email = ?
        """,
        (email.strip().lower(),),
    ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    row = db.execute(
        """
        SELECT id, uid, email, username, lang, is_admin, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def set_admin_by_email(email: str) -> bool:
    db = get_db()
    cur = db.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email.strip().lower(),))
    db.commit()
    return cur.rowcount > 0


def list_pending_posts(limit: int = 100) -> List[Dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, title, city, section, source_lang, created_at, author_name, author_handle, author_user_id
        FROM posts
        WHERE status = 'pending_review'
        ORDER BY id ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def review_post(*, post_id: int, decision: str, reviewer_user_id: int, note: str = "") -> None:
    if decision not in {"approved", "rejected"}:
        raise ValueError("invalid decision")
    db = get_db()
    db.execute(
        """
        UPDATE posts
        SET status = ?,
            reviewed_by_user_id = ?,
            review_note = ?,
            reviewed_at = datetime('now')
        WHERE id = ?
        """,
        (decision, reviewer_user_id, note.strip() or None, post_id),
    )
    db.commit()


def verify_user_password(*, email: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email(email)
    if not user:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    # Strip password_hash before returning
    user.pop("password_hash", None)
    return user


def create_post(
    *,
    title: str,
    content: str,
    section: str,
    city: Optional[str],
    source_lang: str,
    author_name: Optional[str],
    author_handle: Optional[str],
    author_user_id: Optional[int],
    status: str = "pending_review",
) -> int:
    title = title.strip()
    content = content.strip()
    section = section.strip()
    city = (city or "").strip() or None
    source_lang = (source_lang or "en").strip()
    if source_lang not in SUPPORTED_LANGS:
        source_lang = "en"

    db = get_db()
    cur = db.execute(
        """
        INSERT INTO posts (title, content, city, section, status, source_lang, author_name, author_handle, author_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, content, city, section, status, source_lang, author_name, author_handle, author_user_id),
    )
    db.commit()
    return int(cur.lastrowid)


def list_user_posts_in_section(
    *, user_id: int, section: str, limit: int = 50, exclude_status: str = "approved"
) -> List[Dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, title, city, section, source_lang, created_at, author_name, author_handle, status
        FROM posts
        WHERE author_user_id = ?
          AND section = ?
          AND status != ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, section, exclude_status, limit),
    ).fetchall()
    return [dict(r) for r in rows]


