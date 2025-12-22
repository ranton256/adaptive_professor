"""Tests for session management."""

import pytest

from src.session import (
    KnowledgeLevel,
    LectureSession,
    clear_all_sessions,
    create_session,
    delete_session,
    get_session,
    update_session,
)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Clean up sessions before and after each test."""
    clear_all_sessions()
    yield
    clear_all_sessions()


def test_create_session_returns_session():
    """Creating a session should return a LectureSession."""
    outline = ["Intro", "Main", "Conclusion"]
    session = create_session("Test Topic", outline)

    assert isinstance(session, LectureSession)
    assert session.topic == "Test Topic"
    assert session.outline == outline


def test_create_session_generates_unique_id():
    """Each session should have a unique ID."""
    session1 = create_session("Topic 1", ["Slide 1"])
    session2 = create_session("Topic 2", ["Slide 1"])

    assert session1.session_id != session2.session_id


def test_get_session_returns_created_session():
    """Should be able to retrieve a created session."""
    session = create_session("Test", ["Slide"])
    retrieved = get_session(session.session_id)

    assert retrieved is not None
    assert retrieved.session_id == session.session_id


def test_get_session_returns_none_for_unknown_id():
    """Should return None for unknown session ID."""
    result = get_session("nonexistent-id")
    assert result is None


def test_update_session_persists_changes():
    """Updating a session should persist the changes."""
    session = create_session("Test", ["Slide 1", "Slide 2", "Slide 3"])
    session.current_index = 2

    update_session(session)
    retrieved = get_session(session.session_id)

    assert retrieved.current_index == 2


def test_delete_session_removes_session():
    """Deleting a session should remove it from storage."""
    session = create_session("Test", ["Slide"])
    session_id = session.session_id

    result = delete_session(session_id)

    assert result is True
    assert get_session(session_id) is None


def test_delete_nonexistent_session_returns_false():
    """Deleting a nonexistent session should return False."""
    result = delete_session("nonexistent")
    assert result is False


def test_session_total_slides():
    """Session should report correct total slides."""
    session = create_session("Test", ["A", "B", "C", "D"])
    assert session.total_slides == 4


def test_session_current_title():
    """Session should return correct current title."""
    session = create_session("Test", ["First", "Second", "Third"])

    assert session.current_title == "First"

    session.current_index = 1
    assert session.current_title == "Second"


def test_session_has_next():
    """Session should correctly report if there's a next slide."""
    session = create_session("Test", ["A", "B", "C"])

    assert session.has_next is True

    session.current_index = 1
    assert session.has_next is True

    session.current_index = 2
    assert session.has_next is False


def test_session_has_previous():
    """Session should correctly report if there's a previous slide."""
    session = create_session("Test", ["A", "B", "C"])

    assert session.has_previous is False

    session.current_index = 1
    assert session.has_previous is True

    session.current_index = 2
    assert session.has_previous is True


def test_session_default_knowledge_level():
    """Session should default to intermediate knowledge level."""
    session = create_session("Test", ["Slide"])
    assert session.knowledge_level == KnowledgeLevel.INTERMEDIATE
