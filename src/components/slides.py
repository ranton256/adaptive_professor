"""Slide component models for A2UI."""

from pydantic import BaseModel


class InteractiveControl(BaseModel):
    """A button or control rendered on a slide."""

    label: str
    action: str
    params: dict | None = None


class SlideContent(BaseModel):
    """Content payload for a slide."""

    title: str
    text: str
    diagram_code: str | None = None


class SlidePayload(BaseModel):
    """Complete A2UI slide payload."""

    type: str = "render_slide"
    slide_id: str
    layout: str = "default"
    content: SlideContent
    interactive_controls: list[InteractiveControl] = []
    allow_freeform_input: bool = True
