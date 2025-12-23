"""Database initialization and connection management for SQLite persistence."""

from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

# Database file location
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "sessions.db"

# For testing, we can override this
_db_path: Path | str = DB_PATH


def set_db_path(path: Path | str) -> None:
    """Set the database path.

    For testing, use 'file::memory:?cache=shared' for shared in-memory database.
    """
    global _db_path
    _db_path = path


def get_db_path() -> Path | str:
    """Get the current database path."""
    return _db_path


# SQL Schema
SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    outline TEXT NOT NULL,
    current_index INTEGER DEFAULT 0,
    knowledge_level TEXT DEFAULT 'intermediate',
    in_deep_dive INTEGER DEFAULT 0,
    deep_dive_parent_index INTEGER,
    deep_dive_concept TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS slides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    slide_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    controls TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    UNIQUE(session_id, slide_index)
);

CREATE INDEX IF NOT EXISTS idx_slides_session ON slides(session_id);
"""


async def init_db() -> None:
    """Initialize the database with schema."""
    db_path = get_db_path()

    # Create data directory if using file-based DB
    if isinstance(db_path, Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # Use uri=True to support shared cache in-memory databases
    async with aiosqlite.connect(db_path, uri=True) as db:
        # Enable foreign keys
        await db.execute("PRAGMA foreign_keys = ON")
        # Execute schema
        await db.executescript(SCHEMA)
        await db.commit()


@asynccontextmanager
async def get_db():
    """Get a database connection as async context manager."""
    db_path = get_db_path()
    # Use uri=True to support shared cache in-memory databases
    async with aiosqlite.connect(db_path, uri=True) as db:
        # Enable foreign keys for each connection
        await db.execute("PRAGMA foreign_keys = ON")
        # Return rows as dicts
        db.row_factory = aiosqlite.Row
        yield db


async def clear_all_data() -> None:
    """Clear all data from the database (for testing)."""
    async with get_db() as db:
        await db.execute("DELETE FROM slides")
        await db.execute("DELETE FROM sessions")
        await db.commit()
