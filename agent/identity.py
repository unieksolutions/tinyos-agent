"""User identity and authentication module — SQLite + bcrypt."""

import hashlib
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Use hashlib-based password hashing as fallback when bcrypt is not available.
# bcrypt is preferred but not in Debian bookworm's base Python packages.
try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False


DB_PATH = "/opt/tinyos-agent/data/users.db"


@dataclass
class User:
    id: int
    name: str
    has_password: bool
    created_at: str
    last_seen: str


def _get_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Get or create the user database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_seen TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt (preferred) or SHA-256 fallback."""
    if _HAS_BCRYPT:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    else:
        salt = os.urandom(16).hex()
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"sha256:{salt}:{hashed}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    if _HAS_BCRYPT and stored_hash.startswith("$2"):
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    elif stored_hash.startswith("sha256:"):
        parts = stored_hash.split(":", 2)
        if len(parts) != 3:
            return False
        _, salt, expected = parts
        actual = hashlib.sha256((salt + password).encode()).hexdigest()
        return actual == expected
    return False


def lookup_user(name: str, db_path: str = DB_PATH) -> Optional[User]:
    """Look up a user by name (case-insensitive). Returns None if not found."""
    conn = _get_db(db_path)
    try:
        row = conn.execute(
            "SELECT id, name, password_hash, created_at, last_seen FROM users WHERE name = ?",
            (name,),
        ).fetchone()
        if row:
            return User(
                id=row[0],
                name=row[1],
                has_password=bool(row[2]),
                created_at=row[3],
                last_seen=row[4],
            )
        return None
    finally:
        conn.close()


def create_user(name: str, password: Optional[str] = None, db_path: str = DB_PATH) -> User:
    """Create a new user. Optionally set a password."""
    conn = _get_db(db_path)
    try:
        pw_hash = _hash_password(password) if password else None
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO users (name, password_hash, created_at, last_seen) VALUES (?, ?, ?, ?)",
            (name, pw_hash, now, now),
        )
        conn.commit()
        return lookup_user(name, db_path)
    finally:
        conn.close()


def authenticate(name: str, password: str, db_path: str = DB_PATH) -> bool:
    """Authenticate a user by name and password. Returns True on success."""
    conn = _get_db(db_path)
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE name = ?",
            (name,),
        ).fetchone()
        if not row or not row[0]:
            return False
        return _verify_password(password, row[0])
    finally:
        conn.close()


def update_last_seen(name: str, db_path: str = DB_PATH):
    """Update the last_seen timestamp for a user."""
    conn = _get_db(db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE users SET last_seen = ? WHERE name = ?", (now, name))
        conn.commit()
    finally:
        conn.close()


def set_password(name: str, password: str, db_path: str = DB_PATH) -> bool:
    """Set or update a user's password. Returns True on success."""
    conn = _get_db(db_path)
    try:
        pw_hash = _hash_password(password)
        cursor = conn.execute(
            "UPDATE users SET password_hash = ? WHERE name = ?",
            (pw_hash, name),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def list_users(db_path: str = DB_PATH) -> list:
    """List all users (for admin/debug)."""
    conn = _get_db(db_path)
    try:
        rows = conn.execute(
            "SELECT id, name, password_hash, created_at, last_seen FROM users ORDER BY id"
        ).fetchall()
        return [
            User(id=r[0], name=r[1], has_password=bool(r[2]), created_at=r[3], last_seen=r[4])
            for r in rows
        ]
    finally:
        conn.close()
