"""Session management for lecture state."""

import uuid
from dataclasses import dataclass, field
from enum import Enum

from src.components.slides import SlideContent


class KnowledgeLevel(str, Enum):
    """Knowledge level for content adaptation."""

    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"
    BEGINNER = "beginner"


@dataclass
class LectureSession:
    """Represents an active lecture session."""

    session_id: str
    topic: str
    outline: list[str]  # List of slide titles
    slides: dict[int, SlideContent] = field(default_factory=dict)  # Generated slides by index
    current_index: int = 0
    knowledge_level: KnowledgeLevel = KnowledgeLevel.INTERMEDIATE

    @property
    def total_slides(self) -> int:
        """Total number of slides in the lecture."""
        return len(self.outline)

    @property
    def current_title(self) -> str:
        """Get the title of the current slide."""
        return self.outline[self.current_index]

    @property
    def has_next(self) -> bool:
        """Check if there's a next slide."""
        return self.current_index < self.total_slides - 1

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous slide."""
        return self.current_index > 0


# In-memory session storage
_sessions: dict[str, LectureSession] = {}


def create_session(topic: str, outline: list[str]) -> LectureSession:
    """Create a new lecture session."""
    session_id = str(uuid.uuid4())
    session = LectureSession(
        session_id=session_id,
        topic=topic,
        outline=outline,
    )
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> LectureSession | None:
    """Retrieve a session by ID."""
    return _sessions.get(session_id)


def update_session(session: LectureSession) -> None:
    """Update a session in storage."""
    _sessions[session.session_id] = session


def delete_session(session_id: str) -> bool:
    """Delete a session. Returns True if session existed."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def clear_all_sessions() -> None:
    """Clear all sessions. Useful for testing."""
    _sessions.clear()
