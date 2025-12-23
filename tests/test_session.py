"""Tests for session management."""

from src.session import (
    KnowledgeLevel,
    LectureSession,
    create_session,
    delete_session,
    get_session,
    update_session,
)


async def test_create_session_returns_session():
    """Creating a session should return a LectureSession."""
    outline = ["Intro", "Main", "Conclusion"]
    session = await create_session("Test Topic", outline)

    assert isinstance(session, LectureSession)
    assert session.topic == "Test Topic"
    assert session.outline == outline


async def test_create_session_generates_unique_id():
    """Each session should have a unique ID."""
    session1 = await create_session("Topic 1", ["Slide 1"])
    session2 = await create_session("Topic 2", ["Slide 1"])

    assert session1.session_id != session2.session_id


async def test_get_session_returns_created_session():
    """Should be able to retrieve a created session."""
    session = await create_session("Test", ["Slide"])
    retrieved = await get_session(session.session_id)

    assert retrieved is not None
    assert retrieved.session_id == session.session_id


async def test_get_session_returns_none_for_unknown_id():
    """Should return None for unknown session ID."""
    result = await get_session("nonexistent-id")
    assert result is None


async def test_update_session_persists_changes():
    """Updating a session should persist the changes."""
    session = await create_session("Test", ["Slide 1", "Slide 2", "Slide 3"])
    session.current_index = 2

    await update_session(session)
    retrieved = await get_session(session.session_id)

    assert retrieved.current_index == 2


async def test_delete_session_removes_session():
    """Deleting a session should remove it from storage."""
    session = await create_session("Test", ["Slide"])
    session_id = session.session_id

    result = await delete_session(session_id)

    assert result is True
    assert await get_session(session_id) is None


async def test_delete_nonexistent_session_returns_false():
    """Deleting a nonexistent session should return False."""
    result = await delete_session("nonexistent")
    assert result is False


async def test_session_total_slides():
    """Session should report correct total slides."""
    session = await create_session("Test", ["A", "B", "C", "D"])
    assert session.total_slides == 4


async def test_session_current_title():
    """Session should return correct current title."""
    session = await create_session("Test", ["First", "Second", "Third"])

    assert session.current_title == "First"

    session.current_index = 1
    assert session.current_title == "Second"


async def test_session_has_next():
    """Session should correctly report if there's a next slide."""
    session = await create_session("Test", ["A", "B", "C"])

    assert session.has_next is True

    session.current_index = 1
    assert session.has_next is True

    session.current_index = 2
    assert session.has_next is False


async def test_session_has_previous():
    """Session should correctly report if there's a previous slide."""
    session = await create_session("Test", ["A", "B", "C"])

    assert session.has_previous is False

    session.current_index = 1
    assert session.has_previous is True

    session.current_index = 2
    assert session.has_previous is True


async def test_session_default_knowledge_level():
    """Session should default to intermediate knowledge level."""
    session = await create_session("Test", ["Slide"])
    assert session.knowledge_level == KnowledgeLevel.INTERMEDIATE
