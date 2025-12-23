"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.components.slides import InteractiveControl, SlideContent, SlidePayload
from src.config import settings
from src.database import init_db
from src.llm import SlideGenerationContext, get_llm_provider
from src.session import SlideState, create_session, get_session, update_session
from src.url_validator import ValidationResult, validate_and_filter_references


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="A2UI Adaptive Professor - Interactive Learning Deck",
    version="0.1.0",
    lifespan=lifespan,
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


def get_generation_context(session) -> SlideGenerationContext:
    """Build generation context from session state."""
    return SlideGenerationContext(
        topic=session.topic,
        slide_title=session.outline[session.current_index],
        slide_index=session.current_index,
        total_slides=session.total_slides,
        outline=session.outline,
        is_first=session.is_first,
        is_last=session.is_last,
    )


def build_slide_payload(session, slide_state: SlideState) -> SlidePayload:
    """Build a slide payload from session and slide state."""
    return SlidePayload(
        slide_id=f"slide_{session.current_index + 1:02d}",
        session_id=session.session_id,
        layout="default",
        content=slide_state.content,
        interactive_controls=slide_state.controls,  # LLM-generated controls!
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
    session = await create_session(request.topic, outline)

    # Generate first slide with contextual controls
    context = get_generation_context(session)
    generated = llm.generate_slide(context)

    # Store slide state
    slide_state = SlideState(content=generated.content, controls=generated.controls)
    session.slides[0] = slide_state
    await update_session(session)

    return build_slide_payload(session, slide_state)


@app.post("/api/lecture/{session_id}/action", response_model=SlidePayload)
async def perform_action(session_id: str, request: ActionRequest) -> SlidePayload:
    """Perform an action on the current lecture session."""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    llm = get_llm()

    if request.action == "advance_main_thread":
        if not session.has_next:
            raise HTTPException(status_code=400, detail="No more slides")

        # Exit deep dive if we were in one
        session.in_deep_dive = False
        session.deep_dive_parent_index = None
        session.deep_dive_concept = None

        session.current_index += 1

        # Generate slide if not already cached
        if session.current_index not in session.slides:
            context = get_generation_context(session)
            generated = llm.generate_slide(context)
            session.slides[session.current_index] = SlideState(
                content=generated.content, controls=generated.controls
            )

        await update_session(session)
        return build_slide_payload(session, session.slides[session.current_index])

    elif request.action == "go_previous":
        if not session.has_previous:
            raise HTTPException(status_code=400, detail="No previous slide")

        # Exit deep dive if we were in one
        session.in_deep_dive = False
        session.deep_dive_parent_index = None
        session.deep_dive_concept = None

        session.current_index -= 1
        await update_session(session)
        return build_slide_payload(session, session.slides[session.current_index])

    elif request.action == "clarify_slide":
        current_state = session.slides[session.current_index]
        context = get_generation_context(session)
        generated = llm.clarify_slide(current_state.content, context)
        session.slides[session.current_index] = SlideState(
            content=generated.content, controls=generated.controls
        )
        await update_session(session)
        return build_slide_payload(session, session.slides[session.current_index])

    elif request.action == "deep_dive":
        if not request.params or "concept" not in request.params:
            raise HTTPException(status_code=400, detail="deep_dive requires 'concept' parameter")

        concept = request.params["concept"]
        parent_context = get_generation_context(session)

        # Mark that we're in a deep dive
        session.in_deep_dive = True
        session.deep_dive_parent_index = session.current_index
        session.deep_dive_concept = concept

        # Generate deep dive slide
        generated = llm.handle_deep_dive(session.topic, concept, parent_context)

        # Store as a special "deep dive" slide (use negative index or special key)
        deep_dive_key = -1  # Special key for current deep dive
        session.slides[deep_dive_key] = SlideState(
            content=generated.content, controls=generated.controls
        )

        await update_session(session)

        # Return the deep dive slide
        return SlidePayload(
            slide_id=f"deep_dive_{concept.replace(' ', '_')}",
            session_id=session.session_id,
            layout="deep_dive",
            content=generated.content,
            interactive_controls=generated.controls,
            slide_index=session.current_index,  # Keep showing parent index
            total_slides=session.total_slides,
        )

    elif request.action == "return_to_main":
        # Return to a main slide from any detour (deep dive, example, quiz)
        # Get the target slide index from params, or use current index
        if request.params and "slide_index" in request.params:
            session.current_index = request.params["slide_index"]

        # Clear deep dive state if we were in one
        session.in_deep_dive = False
        session.deep_dive_parent_index = None
        session.deep_dive_concept = None

        await update_session(session)
        return build_slide_payload(session, session.slides[session.current_index])

    elif request.action == "show_example":
        # Generate an example for the current slide content
        current_state = session.slides.get(session.current_index) or session.slides.get(-1)
        if not current_state:
            raise HTTPException(status_code=400, detail="No current slide")

        context = get_generation_context(session)
        example_type = request.params.get("type", "code") if request.params else "code"

        try:
            generated = llm.generate_example(current_state.content, context, example_type)
        except Exception as e:
            # If LLM fails, return an error slide instead of crashing
            error_content = SlideContent(
                title="Example Generation Failed",
                text=f"Sorry, I couldn't generate an example. Error: {str(e)[:200]}",
            )
            error_controls = [
                InteractiveControl(
                    label="Return to Slide",
                    action="return_to_main",
                    params={"slide_index": session.current_index},
                ),
                InteractiveControl(label="Try Again", action="show_example"),
            ]
            return SlidePayload(
                slide_id=f"example_error_{session.current_index}",
                session_id=session.session_id,
                layout="example",
                content=error_content,
                interactive_controls=error_controls,
                slide_index=session.current_index,
                total_slides=session.total_slides,
            )

        # Store as example slide
        example_key = -2  # Special key for example slides
        session.slides[example_key] = SlideState(
            content=generated.content, controls=generated.controls
        )
        await update_session(session)

        return SlidePayload(
            slide_id=f"example_{session.current_index}",
            session_id=session.session_id,
            layout="example",
            content=generated.content,
            interactive_controls=generated.controls,
            slide_index=session.current_index,
            total_slides=session.total_slides,
        )

    elif request.action == "quiz_me":
        # Generate a quiz question for the current content
        current_state = session.slides.get(session.current_index) or session.slides.get(-1)
        if not current_state:
            raise HTTPException(status_code=400, detail="No current slide")

        context = get_generation_context(session)

        try:
            generated = llm.generate_quiz(current_state.content, context)
        except Exception as e:
            error_content = SlideContent(
                title="Quiz Generation Failed",
                text=f"Sorry, I couldn't generate a quiz. Error: {str(e)[:200]}",
            )
            error_controls = [
                InteractiveControl(
                    label="Return to Slide",
                    action="return_to_main",
                    params={"slide_index": session.current_index},
                ),
                InteractiveControl(label="Try Again", action="quiz_me"),
            ]
            return SlidePayload(
                slide_id=f"quiz_error_{session.current_index}",
                session_id=session.session_id,
                layout="quiz",
                content=error_content,
                interactive_controls=error_controls,
                slide_index=session.current_index,
                total_slides=session.total_slides,
            )

        # Store as quiz slide
        quiz_key = -3  # Special key for quiz slides
        session.slides[quiz_key] = SlideState(
            content=generated.content, controls=generated.controls
        )
        await update_session(session)

        return SlidePayload(
            slide_id=f"quiz_{session.current_index}",
            session_id=session.session_id,
            layout="quiz",
            content=generated.content,
            interactive_controls=generated.controls,
            slide_index=session.current_index,
            total_slides=session.total_slides,
        )

    elif request.action == "quiz_answer":
        # Handle quiz answer selection
        if not request.params:
            raise HTTPException(status_code=400, detail="quiz_answer requires params")

        answer = request.params.get("answer", "?")
        is_correct = request.params.get("correct", False)
        explanation = request.params.get("explanation", "")

        # Build result content
        if is_correct:
            result_title = f"Correct! ({answer})"
            result_text = f"**Well done!** {explanation}"
        else:
            result_title = f"Incorrect ({answer})"
            result_text = f"**Not quite.** {explanation}"

        result_content = SlideContent(title=result_title, text=result_text)
        result_controls = [
            InteractiveControl(
                label="Return to Slide",
                action="return_to_main",
                params={"slide_index": session.current_index},
            ),
            InteractiveControl(label="Try Another Question", action="quiz_me"),
            InteractiveControl(label="Continue Lecture", action="advance_main_thread"),
        ]

        return SlidePayload(
            slide_id=f"quiz_result_{session.current_index}",
            session_id=session.session_id,
            layout="quiz_result",
            content=result_content,
            interactive_controls=result_controls,
            slide_index=session.current_index,
            total_slides=session.total_slides,
        )

    elif request.action == "extend_lecture":
        # Generate more slides to continue learning
        new_titles = llm.extend_lecture_outline(session.topic, session.outline)

        # Append new titles to the outline
        session.outline.extend(new_titles)

        # Move to the next slide (first of the new ones)
        session.current_index += 1

        # Generate the new slide
        context = get_generation_context(session)
        generated = llm.generate_slide(context)
        session.slides[session.current_index] = SlideState(
            content=generated.content, controls=generated.controls
        )

        await update_session(session)
        return build_slide_payload(session, session.slides[session.current_index])

    elif request.action == "show_references":
        # Generate references with URL validation and regeneration if needed
        MAX_REGENERATION_ATTEMPTS = 3
        best_result: ValidationResult | None = None
        best_generated = None

        for _attempt in range(MAX_REGENERATION_ATTEMPTS):
            # Generate a references slide with curated learning resources
            generated = llm.generate_references(
                session.topic, session.outline, session.current_index
            )

            # Validate all URLs and filter out broken ones
            result = await validate_and_filter_references(generated.content.text)

            # Keep track of best result (most valid links)
            if best_result is None or result.valid_links > best_result.valid_links:
                best_result = result
                best_generated = generated

            # If we have enough valid links, use this result
            if not result.needs_regeneration:
                break

        # Use the best result we got
        assert best_result is not None and best_generated is not None

        # Create content with only valid links (broken links removed entirely)
        validated_content = SlideContent(
            title=best_generated.content.title,
            text=best_result.filtered_text,
        )

        # Store as references slide
        references_key = -4  # Special key for references slides
        session.slides[references_key] = SlideState(
            content=validated_content, controls=best_generated.controls
        )
        await update_session(session)

        return SlidePayload(
            slide_id=f"references_{session.current_index}",
            session_id=session.session_id,
            layout="references",
            content=validated_content,
            interactive_controls=best_generated.controls,
            slide_index=session.current_index,
            total_slides=session.total_slides,
        )

    elif request.action == "show_concept_map":
        # Generate an interactive concept map of the topic
        generated = llm.generate_concept_map(session.topic, session.outline, session.current_index)

        # Store as concept map slide
        concept_map_key = -5  # Special key for concept map slides
        session.slides[concept_map_key] = SlideState(
            content=generated.content, controls=generated.controls
        )
        await update_session(session)

        return SlidePayload(
            slide_id=f"concept_map_{session.current_index}",
            session_id=session.session_id,
            layout="concept_map",
            content=generated.content,
            interactive_controls=generated.controls,
            slide_index=session.current_index,
            total_slides=session.total_slides,
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
