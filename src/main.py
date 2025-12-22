"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.components.slides import InteractiveControl, SlideContent, SlidePayload
from src.config import settings

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


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


class StartLectureRequest(BaseModel):
    """Request to start a new lecture."""

    topic: str


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", service=settings.app_name)


@app.post("/api/lecture/start", response_model=SlidePayload)
async def start_lecture(request: StartLectureRequest) -> SlidePayload:
    """Start a new lecture session and return the first slide."""
    # Hello world implementation - returns a simple welcome slide
    return SlidePayload(
        slide_id="slide_01_welcome",
        layout="title",
        content=SlideContent(
            title=f"Welcome to: {request.topic}",
            text="Let's begin our learning journey. Click Next to continue.",
        ),
        interactive_controls=[
            InteractiveControl(label="Next", action="advance_main_thread"),
            InteractiveControl(label="Simplify", action="simplify_slide"),
        ],
    )
