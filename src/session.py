"""Session management for lecture state with SQLite persistence."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from src.components.slides import InteractiveControl, SlideContent
from src.database import get_db


class KnowledgeLevel(str, Enum):
    """Knowledge level for content adaptation."""

    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"
    BEGINNER = "beginner"


@dataclass
class SlideState:
    """State of a single slide including content and controls."""

    content: SlideContent
    controls: list[InteractiveControl]


@dataclass
class LectureSession:
    """Represents an active lecture session."""

    session_id: str
    topic: str
    outline: list[str]  # List of slide titles
    slides: dict[int, SlideState] = field(default_factory=dict)  # Generated slides by index
    current_index: int = 0
    knowledge_level: KnowledgeLevel = KnowledgeLevel.INTERMEDIATE
    # Track if we're in a deep-dive detour
    in_deep_dive: bool = False
    deep_dive_parent_index: int | None = None
    deep_dive_concept: str | None = None

    @property
    def total_slides(self) -> int:
        """Total number of slides in the lecture."""
        return len(self.outline)

    @property
    def current_title(self) -> str:
        """Get the title of the current slide."""
        if self.in_deep_dive and self.deep_dive_concept:
            return f"Deep Dive: {self.deep_dive_concept}"
        return self.outline[self.current_index]

    @property
    def has_next(self) -> bool:
        """Check if there's a next slide."""
        return self.current_index < self.total_slides - 1

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous slide."""
        return self.current_index > 0

    @property
    def is_first(self) -> bool:
        """Check if on first slide."""
        return self.current_index == 0

    @property
    def is_last(self) -> bool:
        """Check if on last slide."""
        return self.current_index == self.total_slides - 1


def _serialize_slide_content(content: SlideContent) -> str:
    """Serialize SlideContent to JSON string."""
    return json.dumps(
        {"title": content.title, "text": content.text, "diagram_code": content.diagram_code}
    )


def _deserialize_slide_content(data: str) -> SlideContent:
    """Deserialize JSON string to SlideContent."""
    parsed = json.loads(data)
    return SlideContent(
        title=parsed["title"],
        text=parsed["text"],
        diagram_code=parsed.get("diagram_code"),
    )


def _serialize_controls(controls: list[InteractiveControl]) -> str:
    """Serialize list of InteractiveControl to JSON string."""
    return json.dumps(
        [{"label": c.label, "action": c.action, "params": c.params} for c in controls]
    )


def _deserialize_controls(data: str) -> list[InteractiveControl]:
    """Deserialize JSON string to list of InteractiveControl."""
    parsed = json.loads(data)
    return [
        InteractiveControl(label=c["label"], action=c["action"], params=c.get("params"))
        for c in parsed
    ]


async def create_session(topic: str, outline: list[str]) -> LectureSession:
    """Create a new lecture session."""
    session_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO sessions (session_id, topic, outline, current_index, knowledge_level,
                                  in_deep_dive, deep_dive_parent_index, deep_dive_concept,
                                  created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                topic,
                json.dumps(outline),
                0,
                KnowledgeLevel.INTERMEDIATE.value,
                0,
                None,
                None,
                now,
                now,
            ),
        )
        await db.commit()

    return LectureSession(
        session_id=session_id,
        topic=topic,
        outline=outline,
    )


async def get_session(session_id: str) -> LectureSession | None:
    """Retrieve a session by ID."""
    async with get_db() as db:
        # Get session data
        cursor = await db.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        # Get slides for this session
        cursor = await db.execute(
            "SELECT slide_index, content, controls FROM slides WHERE session_id = ?",
            (session_id,),
        )
        slide_rows = await cursor.fetchall()

    # Build slides dict
    slides: dict[int, SlideState] = {}
    for slide_row in slide_rows:
        slide_index = slide_row["slide_index"]
        slides[slide_index] = SlideState(
            content=_deserialize_slide_content(slide_row["content"]),
            controls=_deserialize_controls(slide_row["controls"]),
        )

    return LectureSession(
        session_id=row["session_id"],
        topic=row["topic"],
        outline=json.loads(row["outline"]),
        slides=slides,
        current_index=row["current_index"],
        knowledge_level=KnowledgeLevel(row["knowledge_level"]),
        in_deep_dive=bool(row["in_deep_dive"]),
        deep_dive_parent_index=row["deep_dive_parent_index"],
        deep_dive_concept=row["deep_dive_concept"],
    )


async def update_session(session: LectureSession) -> None:
    """Update a session in storage."""
    now = datetime.now(UTC).isoformat()

    async with get_db() as db:
        # Update session data
        await db.execute(
            """
            UPDATE sessions
            SET topic = ?, outline = ?, current_index = ?, knowledge_level = ?,
                in_deep_dive = ?, deep_dive_parent_index = ?, deep_dive_concept = ?,
                updated_at = ?
            WHERE session_id = ?
            """,
            (
                session.topic,
                json.dumps(session.outline),
                session.current_index,
                session.knowledge_level.value,
                1 if session.in_deep_dive else 0,
                session.deep_dive_parent_index,
                session.deep_dive_concept,
                now,
                session.session_id,
            ),
        )

        # Upsert slides (INSERT OR REPLACE)
        for slide_index, slide_state in session.slides.items():
            await db.execute(
                """
                INSERT OR REPLACE INTO slides (session_id, slide_index, content, controls)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    slide_index,
                    _serialize_slide_content(slide_state.content),
                    _serialize_controls(slide_state.controls),
                ),
            )

        await db.commit()


async def delete_session(session_id: str) -> bool:
    """Delete a session. Returns True if session existed."""
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def clear_all_sessions() -> None:
    """Clear all sessions. Useful for testing."""
    async with get_db() as db:
        await db.execute("DELETE FROM slides")
        await db.execute("DELETE FROM sessions")
        await db.commit()
