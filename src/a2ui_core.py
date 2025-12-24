"""
Core A2UI Type Definitions.
Since the official package is not yet available on PyPI, this module acts as the
'vendored' implementation of the A2UI protocol specifications.
"""

from typing import Any, Literal, Union

from pydantic import BaseModel, Field


class A2UIAction(BaseModel):
    """An action that can be triggered by a user interaction."""

    type: str = "action"
    name: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class A2UIComponent(BaseModel):
    """Base class for all A2UI components."""

    type: str
    id: str | None = None
    style: dict[str, Any] | None = None


class TextComponent(A2UIComponent):
    """A simple text component."""

    type: Literal["text"] = "text"
    content: str
    variant: Literal["h1", "h2", "h3", "body", "caption"] = "body"


class MarkdownComponent(A2UIComponent):
    """A component that renders Markdown content."""

    type: Literal["markdown"] = "markdown"
    content: str


class ButtonComponent(A2UIComponent):
    """A generic button component."""

    type: Literal["button"] = "button"
    label: str
    action: A2UIAction
    variant: Literal["primary", "secondary", "outline", "ghost", "danger"] = "primary"
    disabled: bool = False


class ContainerComponent(A2UIComponent):
    """A container to group other components."""

    type: Literal["container"] = "container"
    layout: Literal["vertical", "horizontal", "grid"] = "vertical"
    children: list[
        Union[
            "TextComponent",
            "MarkdownComponent",
            "ButtonComponent",
            "ContainerComponent",
            "CodeComponent",
            "ImageComponent",
            "ConceptMapComponent",
            "CodeExecutionComponent",
        ]
    ]


class CodeComponent(A2UIComponent):
    """A component to display syntax-highlighted code."""

    type: Literal["code"] = "code"
    code: str
    language: str = "text"
    show_line_numbers: bool = True


class ImageComponent(A2UIComponent):
    """A component to display an image."""

    type: Literal["image"] = "image"
    src: str
    alt: str
    caption: str | None = None


class ConceptMapComponent(A2UIComponent):
    """A component to display a concept map."""

    type: Literal["concept_map"] = "concept_map"
    mermaid_code: str | None = None
    json_data: str | None = None


class CodeExecutionComponent(A2UIComponent):
    """A component to execute and visualize code."""

    type: Literal["code_execution"] = "code_execution"
    code: str
    language: str = "javascript"


# Union type for all supported components
Component = (
    TextComponent
    | MarkdownComponent
    | ButtonComponent
    | ContainerComponent
    | CodeComponent
    | ImageComponent
    | ConceptMapComponent
    | CodeExecutionComponent
)

ContainerComponent.model_rebuild()


class A2UIMessage(BaseModel):
    """The root payload sent from Agent to User."""

    type: Literal["render"] = "render"
    root: Component
    meta: dict[str, Any] = Field(default_factory=dict)
