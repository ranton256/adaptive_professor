"""
Adapter layer to convert internal domain models to A2UI messages.
"""

from src.a2ui_core import (
    A2UIAction,
    A2UIMessage,
    ButtonComponent,
    CodeComponent,
    CodeExecutionComponent,
    ConceptMapComponent,
    ContainerComponent,
    MarkdownComponent,
    TextComponent,
)

# We still import the domain models from slides.py for now,
# but they will eventually be purely internal domain objects, not API schemas.
from src.components.slides import InteractiveControl, SlidePayload


def map_variant_from_action(action: str) -> str:
    """Map internal action types to button variants."""
    if action in ["advance_main_thread", "extend_lecture"]:
        return "primary"
    elif action in ["deep_dive", "show_concept_map"]:
        return "secondary"
    elif action in ["quiz_me", "show_example"]:
        return "outline"
    elif action in ["return_to_main"]:
        return "ghost"
    elif action == "regenerate_slide":
        return "danger"
    return "secondary"


def convert_controls(controls: list[InteractiveControl]) -> ContainerComponent:
    """Convert list of internal controls to a button container."""
    buttons = []
    for control in controls:
        buttons.append(
            ButtonComponent(
                label=control.label,
                action=A2UIAction(name=control.action, parameters=control.params or {}),
                variant=map_variant_from_action(control.action),
            )
        )

    return ContainerComponent(
        layout="horizontal",
        style={"gap": "0.5rem", "flexWrap": "wrap", "marginTop": "1rem"},
        children=buttons,
    )


def domain_to_a2ui(payload: SlidePayload) -> A2UIMessage:
    """
    Convert the legacy SlidePayload into a standard A2UI Message.
    This preserves the exact same visual structure but uses the official protocol.
    """

    metadata = {
        "session_id": payload.session_id,
        "slide_index": payload.slide_index,
        "total_slides": payload.total_slides,
        "slide_id": payload.slide_id,
        "layout": payload.layout,
    }

    # 2. Main Content Area
    children = []

    # Title
    children.append(TextComponent(content=payload.content.title, variant="h2"))

    # Special handling based on layout/content
    if payload.layout == "concept_map" and payload.content.diagram_code:
        # If it's a concept map slide, render the map
        children.append(ConceptMapComponent(mermaid_code=payload.content.diagram_code))
        # Add any explanation text below
        if payload.content.text:
            children.append(MarkdownComponent(content=payload.content.text))

    elif payload.layout == "example" and payload.content.diagram_code:
        # "example" layout with diagram_code usually means code to execute/show
        children.append(
            CodeExecutionComponent(
                code=payload.content.diagram_code,
                language="javascript",  # internal default for now
            )
        )
        # Add explanation text
        if payload.content.text:
            children.append(MarkdownComponent(content=payload.content.text))

    else:
        # Standard Slide
        children.append(MarkdownComponent(content=payload.content.text))

        # If there is diagram code but NOT picked up above (fallback)
        if payload.content.diagram_code and payload.layout not in ["concept_map", "example"]:
            children.append(CodeComponent(code=payload.content.diagram_code, language="text"))

    # 3. Interactive Controls
    if payload.interactive_controls:
        children.append(convert_controls(payload.interactive_controls))

    # Root Container
    root = ContainerComponent(
        layout="vertical", style={"gap": "1.5rem", "padding": "1rem"}, children=children
    )

    return A2UIMessage(root=root, meta=metadata)
