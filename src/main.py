"""FastAPI application entry point."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.components.slides import InteractiveControl, SlideContent, SlidePayload
from src.config import settings
from src.llm import get_llm_provider
from src.session import create_session, get_session, update_session

app = FastAPI(
    title=settings.app_name,
    description="A2UI Adaptive Professor - Interactive Learning Deck",
    version="0.1.0",
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.a2ui_renderer_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM provider instance
_llm_provider = None


def get_llm():
    """Get or create LLM provider instance."""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = get_llm_provider()
    return _llm_provider


def set_llm_provider(provider):
    """Set the LLM provider (for testing)."""
    global _llm_provider
    _llm_provider = provider


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


class StartLectureRequest(BaseModel):
    """Request to start a new lecture."""

    topic: str


class ActionRequest(BaseModel):
    """Request to perform an action on the current slide."""

    action: str
    params: dict | None = None


def build_slide_payload(session, content: SlideContent) -> SlidePayload:
    """Build a slide payload with appropriate controls."""
    controls = []

    # Add navigation controls based on position
    if session.has_next:
        controls.append(InteractiveControl(label="Next", action="advance_main_thread"))
    if session.has_previous:
        controls.append(InteractiveControl(label="Previous", action="go_previous"))

    # Always allow simplification
    controls.append(InteractiveControl(label="Simplify", action="simplify_slide"))

    return SlidePayload(
        slide_id=f"slide_{session.current_index + 1:02d}",
        session_id=session.session_id,
        layout="default",
        content=content,
        interactive_controls=controls,
        slide_index=session.current_index,
        total_slides=session.total_slides,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", service=settings.app_name)


@app.post("/api/lecture/start", response_model=SlidePayload)
async def start_lecture(request: StartLectureRequest) -> SlidePayload:
    """Start a new lecture session and return the first slide."""
    llm = get_llm()

    # Generate lecture outline
    outline = llm.generate_lecture_outline(request.topic)

    # Create session
    session = create_session(request.topic, outline)

    # Generate first slide content
    first_title = outline[0]
    content = llm.generate_slide_content(request.topic, first_title, 0)
    session.slides[0] = content
    update_session(session)

    return build_slide_payload(session, content)


@app.post("/api/lecture/{session_id}/action", response_model=SlidePayload)
async def perform_action(session_id: str, request: ActionRequest) -> SlidePayload:
    """Perform an action on the current lecture session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    llm = get_llm()

    if request.action == "advance_main_thread":
        if not session.has_next:
            raise HTTPException(status_code=400, detail="No more slides")

        session.current_index += 1

        # Generate slide content if not already cached
        if session.current_index not in session.slides:
            title = session.outline[session.current_index]
            content = llm.generate_slide_content(session.topic, title, session.current_index)
            session.slides[session.current_index] = content

        update_session(session)
        return build_slide_payload(session, session.slides[session.current_index])

    elif request.action == "go_previous":
        if not session.has_previous:
            raise HTTPException(status_code=400, detail="No previous slide")

        session.current_index -= 1
        update_session(session)
        return build_slide_payload(session, session.slides[session.current_index])

    elif request.action == "simplify_slide":
        current_content = session.slides[session.current_index]
        simplified = llm.simplify_content(current_content)
        session.slides[session.current_index] = simplified
        update_session(session)
        return build_slide_payload(session, simplified)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
