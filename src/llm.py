"""LLM integration for content generation."""

import json
from dataclasses import dataclass
from typing import Protocol

import anthropic
import google.generativeai as genai

from src.components.slides import InteractiveControl, SlideContent
from src.config import settings


@dataclass
class SlideGenerationContext:
    """Context for generating a slide with appropriate controls."""

    topic: str
    slide_title: str
    slide_index: int
    total_slides: int
    outline: list[str]  # Full outline for context
    is_first: bool
    is_last: bool


@dataclass
class GeneratedSlide:
    """A slide with LLM-generated content and contextual controls."""

    content: SlideContent
    controls: list[InteractiveControl]


class LLMProvider(Protocol):
    """Protocol for LLM providers to enable testing."""

    def generate_lecture_outline(self, topic: str) -> list[str]:
        """Generate a list of slide titles for the topic."""
        ...

    def extend_lecture_outline(self, topic: str, existing_titles: list[str]) -> list[str]:
        """Generate additional slide titles to continue the lecture."""
        ...

    def generate_slide(self, context: SlideGenerationContext) -> GeneratedSlide:
        """Generate slide content with contextual interactive controls."""
        ...

    def clarify_slide(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Clarify the content with better explanations and contextual controls."""
        ...

    def handle_deep_dive(
        self, topic: str, concept: str, parent_context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Generate a deep-dive slide for a specific concept."""
        ...

    def generate_example(
        self, content: SlideContent, context: SlideGenerationContext, example_type: str
    ) -> GeneratedSlide:
        """Generate an example for the current slide content."""
        ...

    def generate_quiz(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Generate a quiz question for the current content."""
        ...

    def generate_references(
        self, topic: str, outline: list[str], current_index: int
    ) -> GeneratedSlide:
        """Generate a references slide with curated learning resources."""
        ...

    def generate_concept_map(
        self, topic: str, outline: list[str], current_index: int
    ) -> GeneratedSlide:
        """Generate an interactive concept map of the topic."""
        ...

    def regenerate_slide(
        self, context: SlideGenerationContext, feedback: str | None = None
    ) -> GeneratedSlide:
        """Regenerate a slide, optionally incorporating user feedback."""
        ...


# Shared prompts for consistency across providers
def get_outline_prompt(topic: str) -> str:
    return f"""Create a lecture outline for the topic: "{topic}"

Generate exactly 5 slide titles that would form the beginning of a coherent educational presentation.
The first slide should be an introduction. Do NOT include a conclusion slide - the lecture can continue.

Return ONLY a JSON array of strings, no other text. Example:
["Introduction to Topic", "Core Concept 1", "Core Concept 2", "Advanced Topic", "Practical Applications"]"""


def get_extend_outline_prompt(topic: str, existing_titles: list[str]) -> str:
    titles_str = "\n".join(f"- {t}" for t in existing_titles)
    return f"""Continue the lecture outline for the topic: "{topic}"

The lecture has already covered these slides:
{titles_str}

Generate 4 MORE slide titles that would naturally continue this lecture, going deeper into the topic.
These should cover new aspects, advanced concepts, or related topics not yet discussed.
Do NOT include a conclusion slide - the lecture can always continue.

Return ONLY a JSON array of strings (the new slides only), no other text. Example:
["Advanced Concept 1", "Real-World Application", "Common Pitfalls", "Best Practices"]"""


def get_slide_prompt(context: SlideGenerationContext, next_title: str | None) -> str:
    last_slide_note = """This is currently the last prepared slide.
Include a "Continue Learning" button (action: extend_lecture) to let students explore more about this topic."""

    return f"""You are an adaptive professor creating slide {context.slide_index + 1} of {context.total_slides} for a lecture on "{context.topic}".

Current slide title: "{context.slide_title}"
{"Next slide will be: " + next_title if next_title else last_slide_note}

Generate the slide content AND contextual interactive controls that a student might want.

This is slide {context.slide_index + 1} of {context.total_slides}.
{"This is the FIRST slide - no Previous button needed." if context.is_first else "This is NOT the first slide - include a Previous button."}

Return a JSON object with:
1. "content": {{"title": "...", "text": "2-4 educational sentences"}}
2. "controls": An array of interactive options. Each control has:
   - "label": The button text (be specific and contextual!)
   - "action": One of ["advance_main_thread", "go_previous", "deep_dive", "clarify_slide", "regenerate_slide", "show_example", "quiz_me", "extend_lecture", "show_references", "show_concept_map"]
   - "params": Optional object with context (e.g., {{"concept": "specific term from this slide"}})

IMPORTANT for controls:
- If there's a next slide, include a "Next: [next topic]" button (action: advance_main_thread)
- If this is the last slide, include a "Continue Learning" button (action: extend_lecture)
- If NOT the first slide, ALWAYS include a "Previous" button (action: go_previous)
- Identify 1-2 key concepts/terms from YOUR content that could be deep-dived (action: deep_dive, params: {{"concept": "..."}})
- Always include a "Clarify This" option (action: clarify_slide) for students who want more explanation
- Always include a "Regenerate" button (action: regenerate_slide) to let students request a different version
- Optionally include "Show Example" or "Quiz Me" if appropriate for the content
- Always include "View References" button (action: show_references) to let students find more resources
- Always include "Concept Map" button (action: show_concept_map) for visualizing topic structure

Example response (for slide 2 of 6):
{{
  "content": {{
    "title": "The Borrow Checker",
    "text": "Rust's borrow checker enforces memory safety at compile time. It tracks ownership and ensures references don't outlive their data. This prevents common bugs like use-after-free and data races."
  }},
  "controls": [
    {{"label": "Next: Lifetimes", "action": "advance_main_thread"}},
    {{"label": "Previous", "action": "go_previous"}},
    {{"label": "Deep Dive: Ownership Rules", "action": "deep_dive", "params": {{"concept": "ownership rules"}}}},
    {{"label": "Deep Dive: Data Races", "action": "deep_dive", "params": {{"concept": "data races"}}}},
    {{"label": "Show Code Example", "action": "show_example", "params": {{"type": "borrow_checker_error"}}}},
    {{"label": "Clarify This", "action": "clarify_slide"}},
    {{"label": "Regenerate", "action": "regenerate_slide"}}
  ]
}}

Return ONLY the JSON object."""


def get_clarify_prompt(content: SlideContent, next_title: str | None) -> str:
    return f"""Clarify and expand on this educational content to make it more accessible.

Original title: {content.title}
Original text: {content.text}

{"Next slide will be: " + next_title if next_title else "This is the final slide."}

Your task:
1. Define any technical terms or jargon that might be unclear
2. Break down complex concepts into clear, logical steps
3. Add a relevant analogy from the SAME DOMAIN or a related technical field (not childish comparisons)
4. Explain WHY this concept matters or how it connects to the bigger picture
5. Keep the intellectual level appropriate - clarify, don't dumb down

IMPORTANT: Do NOT use childish analogies like "think of it like legos" or "imagine you're sharing toys".
Use analogies from related technical domains, historical examples, or real-world applications.

Return a JSON object with clarified content AND contextual controls:
{{
  "content": {{"title": "[Original Title] - Clarified", "text": "Clear explanation with defined terms and relevant analogy"}},
  "controls": [
    {{"label": "Next: [topic]", "action": "advance_main_thread"}},
    {{"label": "Previous", "action": "go_previous"}},
    {{"label": "Deep Dive: [concept]", "action": "deep_dive", "params": {{"concept": "..."}}}},
    {{"label": "Quiz Me", "action": "quiz_me"}},
    {{"label": "Regenerate", "action": "regenerate_slide"}}
  ]
}}

Keep controls relevant to the clarified content. Include navigation buttons as appropriate.
Always include "Regenerate" button to let students request a different version.
Return ONLY the JSON object."""


def get_deep_dive_prompt(topic: str, concept: str, parent_context: SlideGenerationContext) -> str:
    return f"""You are creating a "deep dive" detour slide for a lecture on "{topic}".

The student clicked to learn more about: "{concept}"
They were on slide: "{parent_context.slide_title}"

Create an in-depth explanation of "{concept}" with contextual controls.

Return a JSON object:
{{
  "content": {{
    "title": "Deep Dive: {concept}",
    "text": "3-5 sentences providing deeper explanation of this concept"
  }},
  "controls": [
    {{"label": "Return to: {parent_context.slide_title}", "action": "return_to_main", "params": {{"slide_index": {parent_context.slide_index}}}}},
    {{"label": "Deep Dive: [sub-concept]", "action": "deep_dive", "params": {{"concept": "..."}}}},
    {{"label": "Show Example", "action": "show_example"}},
    {{"label": "Clarify This", "action": "clarify_slide"}}
  ]
}}

The first control MUST be "Return to: {parent_context.slide_title}" to let them go back.
Return ONLY the JSON object."""


def get_example_prompt(
    content: SlideContent, context: SlideGenerationContext, example_type: str
) -> str:
    return f"""You are creating an example to illustrate a concept from a lecture on "{context.topic}".

Current slide: "{content.title}"
Content: "{content.text}"
Example type requested: {example_type}

Create a practical example that illustrates the concepts from this slide.

IMPORTANT - Choose the RIGHT format for the domain:

1. For LANGUAGE, GRAMMAR, VOCABULARY, and LINGUISTIC topics:
   - Use PLAIN TEXT with markdown tables - NO CODE
   - Use markdown tables for declensions, conjugations, and vocabulary lists
   - Example for Greek noun declension:
   | Case | Singular | Plural |
   |------|----------|--------|
   | Nominative | πατήρ | πατέρες |
   | Genitive | πατρός | πατέρων |
   | Dative | πατρί | πατράσι |
   - Include pronunciation guides in parentheses
   - Add explanatory notes about patterns or irregularities
   - NEVER generate JavaScript code for language examples

2. For DATA VISUALIZATION and SIMULATIONS:
   - Use JavaScript with Chart.js format for interactive charts
   - Generate data programmatically when showing trends, simulations, or comparisons
   - Your code MUST set a `chartConfig` variable with the Chart.js configuration
   - Supported chart types: 'line', 'bar', 'pie', 'doughnut', 'scatter'
   - Example:
   ```javascript
   chartConfig = {{
     type: 'line',
     data: {{
       labels: [1, 2, 3, 4, 5],
       datasets: [{{ label: 'Values', data: [10, 20, 15, 25, 30] }}]
     }}
   }};
   ```

3. For SCIENCE topics with EQUATIONS:
   - Use LaTeX for equations: $E = mc^2$ or $$\\frac{{dN}}{{dt}} = -\\lambda N$$
   - Use step-by-step numbered explanations with LaTeX formulas
   - For reactions: $^1H + ^1H \\rightarrow ^2H + e^+ + \\nu_e$

4. For PROGRAMMING topics:
   - Use JavaScript/TypeScript code that could run in a browser
   - Use working code examples with comments

5. For PROCESSES or WORKFLOWS:
   - Use Mermaid flowcharts with SIMPLE labels (no special chars, no parentheses in labels)
   - Node labels must be quoted if they contain spaces: A["Step One"]
   - Example: ```mermaid\\nflowchart LR\\n  A["Step 1"] --> B["Step 2"]\\n```

6. For HIERARCHIES or STRUCTURES:
   - Use Mermaid with simple alphanumeric labels only
   - Always quote labels: A["Label Here"]

MERMAID RULES (if using mermaid):
- NO special characters (¹²³, Greek letters, etc.) in node labels
- NO parentheses inside node labels
- ALWAYS quote labels with spaces: A["My Label"]
- Keep labels short and simple

CHART.JS RULES (if using charts):
- MUST declare chartConfig variable (not const, just chartConfig = ...)
- Use 'line' for trends, 'bar' for comparisons, 'pie'/'doughnut' for distributions
- Include descriptive labels and axis titles
- Use rgb() colors: 'rgb(75, 192, 192)', 'rgb(255, 99, 132)', etc.

DO NOT use Python unless the topic is specifically about Python programming.
Prefer Chart.js for numerical simulations and data trends.
Prefer LaTeX formulas for showing individual equations.

Return a JSON object:
{{
  "content": {{
    "title": "Example: [descriptive title]",
    "text": "The example content using appropriate format (chart.js, mermaid, latex, or browser-runnable code)"
  }},
  "controls": [
    {{"label": "Return to: {content.title}", "action": "return_to_main", "params": {{"slide_index": {context.slide_index}}}}},
    {{"label": "Another Example", "action": "show_example"}},
    {{"label": "Clarify This", "action": "clarify_slide"}}
  ]
}}

The first control MUST be "Return to: {content.title}" to let them go back.
Return ONLY the JSON object."""


def get_concept_map_prompt(topic: str, outline: list[str], current_index: int) -> str:
    covered_slides = outline[: current_index + 1]
    covered_str = "\n".join(f"- {t}" for t in covered_slides)
    return f"""You are creating an interactive concept map for a lecture on "{topic}".

The lecture has covered these topics so far:
{covered_str}

Create a structured concept map showing the key concepts and their relationships.
The map should help students understand how concepts connect.

IMPORTANT: Generate a JSON concept map structure, NOT Mermaid syntax.
The concept map has:
- "root": The central topic (string)
- "branches": Array of main branches, each with "name" and optional "children"

Example structure:
{{
  "root": "Rust Programming",
  "branches": [
    {{
      "name": "Ownership",
      "children": [
        {{"name": "Move Semantics"}},
        {{"name": "Borrowing"}}
      ]
    }},
    {{
      "name": "Type System",
      "children": [
        {{"name": "Structs"}},
        {{"name": "Enums"}}
      ]
    }},
    {{"name": "Concurrency"}}
  ]
}}

Guidelines:
- Keep node labels SHORT (1-4 words)
- Focus on MAIN concepts only (4-8 branches)
- Each branch can have 0-4 children
- Branch names should be specific to the topic

Return a JSON object:
{{
  "content": {{
    "title": "Concept Map: {topic}",
    "text": "```conceptmap\\n<concept_map_json_here>\\n```"
  }},
  "controls": [
    {{"label": "Return to Lecture", "action": "return_to_main", "params": {{"slide_index": {current_index}}}}},
    {{"label": "Deep Dive: [concept]", "action": "deep_dive", "params": {{"concept": "..."}}}},
    {{"label": "View References", "action": "show_references"}}
  ]
}}

The text should contain ONLY a conceptmap code block with valid JSON inside.
Include 2-3 Deep Dive controls for the most important concepts shown in the map.
Return ONLY the JSON object."""


def get_references_prompt(topic: str, outline: list[str], current_index: int) -> str:
    covered_slides = outline[: current_index + 1]
    covered_str = "\n".join(f"- {t}" for t in covered_slides)
    is_last_slide = current_index >= len(outline) - 1

    # Build controls based on position in lecture
    controls = [
        f'{{"label": "Return to Lecture", "action": "return_to_main", "params": {{"slide_index": {current_index}}}}}'
    ]
    if not is_last_slide:
        next_title = (
            outline[current_index + 1] if current_index + 1 < len(outline) else "next topic"
        )
        controls.append(f'{{"label": "Next: {next_title}", "action": "advance_main_thread"}}')
    else:
        controls.append('{"label": "Extend Lecture", "action": "extend_lecture"}')

    controls_str = ",\n    ".join(controls)

    return f"""You are creating a references slide for a lecture on "{topic}".

The lecture has covered these topics so far:
{covered_str}

Generate a curated list of high-quality learning resources. Include:
1. Official documentation or authoritative sources
2. Tutorials and guides for beginners
3. In-depth articles or papers for advanced learners
4. Video resources if relevant
5. Interactive tools or playgrounds if available

IMPORTANT: Use REAL, well-known resources that actually exist. For programming topics, reference
official docs, MDN, freeCodeCamp, etc. For science, reference educational institutions, Wikipedia, etc.

Return a JSON object:
{{
  "content": {{
    "title": "References & Further Reading",
    "text": "A formatted markdown list of resources with links, organized by category. Use real URLs."
  }},
  "controls": [
    {controls_str}
  ]
}}

Format the text like:
### Official Documentation
- [Resource Name](https://real-url.com) - Brief description

### Tutorials
- [Tutorial Name](https://real-url.com) - Brief description

Return ONLY the JSON object."""


def get_quiz_prompt(content: SlideContent, context: SlideGenerationContext) -> str:
    return f"""You are creating a quiz question to test understanding of a concept from a lecture on "{context.topic}".

Current slide: "{content.title}"
Content: "{content.text}"

Create a thoughtful quiz question that tests understanding of the key concepts.
IMPORTANT: Do NOT reveal the answer in the text. The answer will be revealed when the user clicks their choice.

Return a JSON object:
{{
  "content": {{
    "title": "Quiz: {content.title}",
    "text": "Present a clear question about the material. Include the question only, NOT the answer options (they go in controls)."
  }},
  "controls": [
    {{"label": "A) [first option text]", "action": "quiz_answer", "params": {{"answer": "A", "correct": false, "explanation": "Why A is wrong"}}}},
    {{"label": "B) [second option text]", "action": "quiz_answer", "params": {{"answer": "B", "correct": true, "explanation": "Why B is correct"}}}},
    {{"label": "C) [third option text]", "action": "quiz_answer", "params": {{"answer": "C", "correct": false, "explanation": "Why C is wrong"}}}},
    {{"label": "D) [fourth option text]", "action": "quiz_answer", "params": {{"answer": "D", "correct": false, "explanation": "Why D is wrong"}}}},
    {{"label": "Skip Question", "action": "return_to_main", "params": {{"slide_index": {context.slide_index}}}}}
  ]
}}

The answer options A, B, C, D MUST be controls with action "quiz_answer". Exactly ONE should have "correct": true.
Return ONLY the JSON object."""


def clean_json_response(response_text: str) -> str:
    """Clean LLM response text to extract JSON.

    LLMs often wrap JSON in markdown code blocks like ```json ... ```
    """
    text = response_text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        # Find the end of the first line (e.g., ```json)
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        # Remove trailing ```
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def get_retry_prompt(original_prompt: str, error_message: str, failed_response: str) -> str:
    """Generate a retry prompt with error context."""
    return f"""{original_prompt}

IMPORTANT: Your previous response failed to parse. Here's what went wrong:
Error: {error_message}

Your previous response was:
{failed_response[:500]}

Please fix the issue and return ONLY valid JSON. Common issues:
- Mermaid diagrams with special characters (use simple labels, no superscripts)
- Missing quotes around strings
- Trailing commas
- Invalid escape sequences

Return ONLY the corrected JSON object, no explanations."""


def get_regenerate_prompt(context: SlideGenerationContext, feedback: str | None) -> str:
    """Generate a prompt for regenerating a slide with optional feedback."""
    next_title = (
        context.outline[context.slide_index + 1]
        if context.slide_index < len(context.outline) - 1
        else None
    )

    feedback_section = ""
    if feedback:
        feedback_section = f"""
USER FEEDBACK: The user has requested regeneration with this feedback:
"{feedback}"

Please address this feedback in your new version. This might mean:
- Explaining concepts differently
- Adding or removing detail
- Using different examples
- Changing the tone or level of technical depth
- Fixing factual issues the user identified
"""

    # Build navigation guidance
    nav_guidance = ""
    if context.slide_index > 0:
        nav_guidance += '- Include a "Previous" button (action: go_previous)\n'
    if next_title:
        nav_guidance += f'- Include "Next: {next_title}" button (action: advance_main_thread)\n'
    else:
        nav_guidance += '- Include "Continue Learning" button (action: extend_lecture)\n'

    return f"""You are regenerating a slide for a lecture on "{context.topic}".

Current slide: "{context.slide_title}" (slide {context.slide_index + 1} of {context.total_slides})
{"Next slide will be: " + next_title if next_title else "This is the final slide."}
{feedback_section}
Create a DIFFERENT version of this slide. Maintain the same topic but use a fresh approach -
different examples, different structure, or different emphasis.

Include contextual interactive controls:
- ALWAYS include a "Regenerate" button (action: regenerate_slide) for requesting another version
{nav_guidance}- Include "Clarify This" (action: clarify_slide)
- Optionally include 1-2 "Deep Dive" buttons for key concepts (action: deep_dive, params: {{"concept": "..."}})

Return a JSON object:
{{
  "content": {{
    "title": "The slide title",
    "text": "The main content with markdown formatting"
  }},
  "controls": [
    {{"label": "Regenerate", "action": "regenerate_slide"}},
    {{"label": "Next: [topic]", "action": "advance_main_thread"}},
    ...
  ]
}}

Return ONLY the JSON object."""


def parse_slide_response(response_text: str) -> GeneratedSlide:
    """Parse LLM response into GeneratedSlide."""
    cleaned = clean_json_response(response_text)
    data = json.loads(cleaned)
    content = SlideContent(title=data["content"]["title"], text=data["content"]["text"])
    controls = [
        InteractiveControl(label=c["label"], action=c["action"], params=c.get("params"))
        for c in data["controls"]
    ]
    return GeneratedSlide(content=content, controls=controls)


class GeminiProvider:
    """Google Gemini-based LLM provider (default)."""

    def __init__(self, api_key: str | None = None):
        genai.configure(api_key=api_key or settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def generate_lecture_outline(self, topic: str) -> list[str]:
        """Generate a list of slide titles for the topic."""
        response = self.model.generate_content(get_outline_prompt(topic))
        cleaned = clean_json_response(response.text)
        return json.loads(cleaned)

    def extend_lecture_outline(self, topic: str, existing_titles: list[str]) -> list[str]:
        """Generate additional slide titles to continue the lecture."""
        response = self.model.generate_content(get_extend_outline_prompt(topic, existing_titles))
        cleaned = clean_json_response(response.text)
        return json.loads(cleaned)

    def generate_slide(self, context: SlideGenerationContext) -> GeneratedSlide:
        """Generate slide content with contextual interactive controls."""
        next_title = (
            context.outline[context.slide_index + 1]
            if context.slide_index < len(context.outline) - 1
            else None
        )
        response = self.model.generate_content(get_slide_prompt(context, next_title))
        return parse_slide_response(response.text)

    def clarify_slide(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Simplify the content and regenerate contextual controls."""
        next_title = (
            context.outline[context.slide_index + 1]
            if context.slide_index < len(context.outline) - 1
            else None
        )
        response = self.model.generate_content(get_clarify_prompt(content, next_title))
        return parse_slide_response(response.text)

    def handle_deep_dive(
        self, topic: str, concept: str, parent_context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Generate a deep-dive slide for a specific concept."""
        response = self.model.generate_content(get_deep_dive_prompt(topic, concept, parent_context))
        return parse_slide_response(response.text)

    def generate_example(
        self, content: SlideContent, context: SlideGenerationContext, example_type: str
    ) -> GeneratedSlide:
        """Generate an example for the current slide content with retry on failure."""
        prompt = get_example_prompt(content, context, example_type)
        response = self.model.generate_content(prompt)

        try:
            return parse_slide_response(response.text)
        except Exception as first_error:
            # Retry with error context
            retry_prompt = get_retry_prompt(prompt, str(first_error), response.text)
            retry_response = self.model.generate_content(retry_prompt)
            return parse_slide_response(retry_response.text)

    def generate_quiz(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Generate a quiz question for the current content with retry on failure."""
        prompt = get_quiz_prompt(content, context)
        response = self.model.generate_content(prompt)

        try:
            return parse_slide_response(response.text)
        except Exception as first_error:
            # Retry with error context
            retry_prompt = get_retry_prompt(prompt, str(first_error), response.text)
            retry_response = self.model.generate_content(retry_prompt)
            return parse_slide_response(retry_response.text)

    def generate_references(
        self, topic: str, outline: list[str], current_index: int
    ) -> GeneratedSlide:
        """Generate a references slide with curated learning resources."""
        prompt = get_references_prompt(topic, outline, current_index)
        response = self.model.generate_content(prompt)
        return parse_slide_response(response.text)

    def generate_concept_map(
        self, topic: str, outline: list[str], current_index: int
    ) -> GeneratedSlide:
        """Generate an interactive concept map of the topic."""
        prompt = get_concept_map_prompt(topic, outline, current_index)
        response = self.model.generate_content(prompt)
        return parse_slide_response(response.text)

    def regenerate_slide(
        self, context: SlideGenerationContext, feedback: str | None = None
    ) -> GeneratedSlide:
        """Regenerate a slide with optional user feedback."""
        prompt = get_regenerate_prompt(context, feedback)
        response = self.model.generate_content(prompt)
        return parse_slide_response(response.text)


class AnthropicProvider:
    """Anthropic Claude-based LLM provider."""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    def generate_lecture_outline(self, topic: str) -> list[str]:
        """Generate a list of slide titles for the topic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": get_outline_prompt(topic)}],
        )
        cleaned = clean_json_response(response.content[0].text)
        return json.loads(cleaned)

    def extend_lecture_outline(self, topic: str, existing_titles: list[str]) -> list[str]:
        """Generate additional slide titles to continue the lecture."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": get_extend_outline_prompt(topic, existing_titles)}
            ],
        )
        cleaned = clean_json_response(response.content[0].text)
        return json.loads(cleaned)

    def generate_slide(self, context: SlideGenerationContext) -> GeneratedSlide:
        """Generate slide content with contextual interactive controls."""
        next_title = (
            context.outline[context.slide_index + 1]
            if context.slide_index < len(context.outline) - 1
            else None
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": get_slide_prompt(context, next_title)}],
        )
        return parse_slide_response(response.content[0].text)

    def clarify_slide(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Simplify the content and regenerate contextual controls."""
        next_title = (
            context.outline[context.slide_index + 1]
            if context.slide_index < len(context.outline) - 1
            else None
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": get_clarify_prompt(content, next_title)}],
        )
        return parse_slide_response(response.content[0].text)

    def handle_deep_dive(
        self, topic: str, concept: str, parent_context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Generate a deep-dive slide for a specific concept."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "user", "content": get_deep_dive_prompt(topic, concept, parent_context)}
            ],
        )
        return parse_slide_response(response.content[0].text)

    def generate_example(
        self, content: SlideContent, context: SlideGenerationContext, example_type: str
    ) -> GeneratedSlide:
        """Generate an example for the current slide content with retry on failure."""
        prompt = get_example_prompt(content, context, example_type)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return parse_slide_response(response.content[0].text)
        except Exception as first_error:
            # Retry with error context
            retry_prompt = get_retry_prompt(prompt, str(first_error), response.content[0].text)
            retry_response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": retry_prompt}],
            )
            return parse_slide_response(retry_response.content[0].text)

    def generate_quiz(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Generate a quiz question for the current content with retry on failure."""
        prompt = get_quiz_prompt(content, context)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return parse_slide_response(response.content[0].text)
        except Exception as first_error:
            # Retry with error context
            retry_prompt = get_retry_prompt(prompt, str(first_error), response.content[0].text)
            retry_response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": retry_prompt}],
            )
            return parse_slide_response(retry_response.content[0].text)

    def generate_references(
        self, topic: str, outline: list[str], current_index: int
    ) -> GeneratedSlide:
        """Generate a references slide with curated learning resources."""
        prompt = get_references_prompt(topic, outline, current_index)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_slide_response(response.content[0].text)

    def generate_concept_map(
        self, topic: str, outline: list[str], current_index: int
    ) -> GeneratedSlide:
        """Generate an interactive concept map of the topic."""
        prompt = get_concept_map_prompt(topic, outline, current_index)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_slide_response(response.content[0].text)

    def regenerate_slide(
        self, context: SlideGenerationContext, feedback: str | None = None
    ) -> GeneratedSlide:
        """Regenerate a slide with optional user feedback."""
        prompt = get_regenerate_prompt(context, feedback)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_slide_response(response.content[0].text)


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def generate_lecture_outline(self, topic: str) -> list[str]:
        """Return mock slide titles."""
        return [
            f"Introduction to {topic}",
            f"Core Concepts of {topic}",
            "Key Principles",
            "Practical Applications",
            "Common Challenges",
        ]

    def extend_lecture_outline(self, topic: str, existing_titles: list[str]) -> list[str]:
        """Return additional mock slide titles."""
        extension_num = len(existing_titles) // 5 + 1
        return [
            f"Advanced Topic {extension_num}.1",
            f"Advanced Topic {extension_num}.2",
            f"Real-World Examples {extension_num}",
            f"Expert Insights {extension_num}",
        ]

    def generate_slide(self, context: SlideGenerationContext) -> GeneratedSlide:
        """Return mock slide with contextual controls."""
        # Extract a "concept" from the title for deep dive options
        words = context.slide_title.split()
        concept = words[-1] if words else "concept"

        controls = []

        # Contextual next button or continue learning
        if not context.is_last:
            next_title = context.outline[context.slide_index + 1]
            controls.append(
                InteractiveControl(label=f"Next: {next_title}", action="advance_main_thread")
            )
        else:
            # On last slide, offer to continue learning
            controls.append(InteractiveControl(label="Continue Learning", action="extend_lecture"))

        # Previous button (not on first slide)
        if not context.is_first:
            controls.append(InteractiveControl(label="Previous", action="go_previous"))

        # Deep dive option based on content
        controls.append(
            InteractiveControl(
                label=f"Deep Dive: {concept}",
                action="deep_dive",
                params={"concept": concept.lower()},
            )
        )

        # Always have clarify and regenerate
        controls.append(InteractiveControl(label="Clarify This", action="clarify_slide"))
        controls.append(InteractiveControl(label="Regenerate", action="regenerate_slide"))

        # Quiz option for non-intro/conclusion slides
        if context.slide_index not in [0, context.total_slides - 1]:
            controls.append(InteractiveControl(label="Quiz Me", action="quiz_me"))

        # Always offer references and concept map
        controls.append(InteractiveControl(label="View References", action="show_references"))
        controls.append(InteractiveControl(label="Concept Map", action="show_concept_map"))

        content = SlideContent(
            title=context.slide_title,
            text=f"This is the content for slide {context.slide_index + 1} about {context.topic}. "
            f"Here we explore {context.slide_title.lower()} in detail, covering key aspects of {concept}.",
        )

        return GeneratedSlide(content=content, controls=controls)

    def clarify_slide(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Return simplified mock content with updated controls."""
        controls = []

        if not context.is_last:
            next_title = context.outline[context.slide_index + 1]
            controls.append(
                InteractiveControl(label=f"Next: {next_title}", action="advance_main_thread")
            )

        if not context.is_first:
            controls.append(InteractiveControl(label="Previous", action="go_previous"))

        controls.append(InteractiveControl(label="Quiz Me", action="quiz_me"))
        controls.append(InteractiveControl(label="Regenerate", action="regenerate_slide"))

        clarified_content = SlideContent(
            title=f"{content.title} - Clarified",
            text=f"Clarified version: {content.text[:100]}... "
            "Here's a clearer explanation with defined terms and real-world context.",
        )

        return GeneratedSlide(content=clarified_content, controls=controls)

    def handle_deep_dive(
        self, topic: str, concept: str, parent_context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Generate a mock deep-dive slide."""
        controls = [
            InteractiveControl(
                label=f"Return to: {parent_context.slide_title}",
                action="return_to_main",
                params={"slide_index": parent_context.slide_index},
            ),
            InteractiveControl(
                label="Deep Dive: Sub-concept",
                action="deep_dive",
                params={"concept": f"sub-{concept}"},
            ),
            InteractiveControl(label="Clarify This", action="clarify_slide"),
        ]

        content = SlideContent(
            title=f"Deep Dive: {concept.title()}",
            text=f"Let's explore {concept} in more detail. This concept is fundamental to understanding "
            f"{topic}. It relates to {parent_context.slide_title} by providing deeper insight.",
        )

        return GeneratedSlide(content=content, controls=controls)

    def generate_example(
        self, content: SlideContent, context: SlideGenerationContext, example_type: str
    ) -> GeneratedSlide:
        """Generate a mock example slide."""
        controls = [
            InteractiveControl(
                label=f"Return to: {content.title}",
                action="return_to_main",
                params={"slide_index": context.slide_index},
            ),
            InteractiveControl(label="Another Example", action="show_example"),
            InteractiveControl(label="Clarify This", action="clarify_slide"),
        ]

        example_content = SlideContent(
            title=f"Example: {content.title}",
            text=f"Here's a practical example of {content.title.lower()}:\n\n"
            f"```\n# Example code demonstrating the concept\ndef example():\n    pass\n```\n\n"
            "This example shows how the concept works in practice.",
        )

        return GeneratedSlide(content=example_content, controls=controls)

    def generate_quiz(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Generate a mock quiz slide with interactive answer buttons."""
        controls = [
            InteractiveControl(
                label="A) A fundamental building block",
                action="quiz_answer",
                params={
                    "answer": "A",
                    "correct": False,
                    "explanation": "While related, this doesn't capture the main purpose.",
                },
            ),
            InteractiveControl(
                label="B) The core mechanism for the concept",
                action="quiz_answer",
                params={
                    "answer": "B",
                    "correct": True,
                    "explanation": "This directly addresses the core concept and its purpose.",
                },
            ),
            InteractiveControl(
                label="C) An optional enhancement",
                action="quiz_answer",
                params={
                    "answer": "C",
                    "correct": False,
                    "explanation": "This is not optional; it's fundamental to the concept.",
                },
            ),
            InteractiveControl(
                label="D) A debugging tool",
                action="quiz_answer",
                params={
                    "answer": "D",
                    "correct": False,
                    "explanation": "This is unrelated to the main purpose of the concept.",
                },
            ),
            InteractiveControl(
                label="Skip Question",
                action="return_to_main",
                params={"slide_index": context.slide_index},
            ),
        ]

        quiz_content = SlideContent(
            title=f"Quiz: {content.title}",
            text=f"What is the main purpose of {content.title.lower()}?",
        )

        return GeneratedSlide(content=quiz_content, controls=controls)

    def generate_references(
        self, topic: str, outline: list[str], current_index: int
    ) -> GeneratedSlide:
        """Generate a mock references slide."""
        is_last_slide = current_index >= len(outline) - 1

        controls = [
            InteractiveControl(
                label="Return to Lecture",
                action="return_to_main",
                params={"slide_index": current_index},
            ),
        ]

        # Add contextual navigation control
        if not is_last_slide:
            next_title = outline[current_index + 1] if current_index + 1 < len(outline) else "Next"
            controls.append(
                InteractiveControl(label=f"Next: {next_title}", action="advance_main_thread")
            )
        else:
            controls.append(InteractiveControl(label="Extend Lecture", action="extend_lecture"))

        references_content = SlideContent(
            title="References & Further Reading",
            text=f"""### Official Documentation
- [Wikipedia: {topic}](https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}) - Encyclopedia overview

### Tutorials
- [Learn {topic}](https://example.com/learn) - Beginner-friendly tutorial

### Advanced Resources
- [Deep Dive into {topic}](https://example.com/advanced) - For advanced learners

### Video Resources
- [Introduction to {topic}](https://youtube.com/watch) - Video explanation""",
        )

        return GeneratedSlide(content=references_content, controls=controls)

    def generate_concept_map(
        self, topic: str, outline: list[str], current_index: int
    ) -> GeneratedSlide:
        """Generate a mock concept map slide."""
        # Extract key concepts from outline
        concepts = [title.split()[-1] for title in outline[: current_index + 1]]

        controls = [
            InteractiveControl(
                label="Return to Lecture",
                action="return_to_main",
                params={"slide_index": current_index},
            ),
            InteractiveControl(
                label=f"Deep Dive: {concepts[0] if concepts else 'Concepts'}",
                action="deep_dive",
                params={"concept": concepts[0].lower() if concepts else "concepts"},
            ),
            InteractiveControl(label="View References", action="show_references"),
        ]

        # Build a JSON concept map structure
        import json as json_module

        concept_map_data = {
            "root": topic,
            "branches": [
                {
                    "name": "Core Concepts",
                    "children": [{"name": "Fundamentals"}, {"name": "Principles"}],
                },
                {
                    "name": "Applications",
                    "children": [{"name": "Practice"}, {"name": "Examples"}],
                },
                {
                    "name": "Advanced",
                    "children": [{"name": "Deep Topics"}, {"name": "Extensions"}],
                },
            ],
        }

        concept_map_content = SlideContent(
            title=f"Concept Map: {topic}",
            text="Explore the relationships between key concepts in this topic.",
            diagram_code=json_module.dumps(concept_map_data, indent=2),
        )

        return GeneratedSlide(content=concept_map_content, controls=controls)

    def regenerate_slide(
        self, context: SlideGenerationContext, feedback: str | None = None
    ) -> GeneratedSlide:
        """Regenerate a mock slide with optional feedback."""
        controls = [
            InteractiveControl(label="Regenerate", action="regenerate_slide"),
            InteractiveControl(label="Clarify This", action="clarify_slide"),
        ]

        # Add navigation controls based on position
        if context.slide_index > 0:
            controls.append(InteractiveControl(label="Previous", action="go_previous"))

        if context.slide_index < context.total_slides - 1:
            next_title = context.outline[context.slide_index + 1]
            controls.append(
                InteractiveControl(label=f"Next: {next_title}", action="advance_main_thread")
            )

        feedback_note = (
            f" (Regenerated with feedback: {feedback})" if feedback else " (Regenerated)"
        )

        regenerated_content = SlideContent(
            title=f"{context.slide_title}{feedback_note}",
            text=f"This is a regenerated version of the slide about {context.slide_title}. "
            "The content has been revised to provide a fresh perspective on the topic.",
        )

        return GeneratedSlide(content=regenerated_content, controls=controls)


def get_llm_provider(use_mock: bool = False) -> LLMProvider:
    """Get the appropriate LLM provider based on configuration.

    Priority: Mock (for testing) > Gemini (default) > Anthropic > Mock (fallback)
    """
    if use_mock:
        return MockLLMProvider()

    # Check for Gemini first (default)
    if settings.gemini_api_key:
        return GeminiProvider()

    # Fall back to Anthropic if available
    if settings.anthropic_api_key:
        return AnthropicProvider()

    # No API keys configured, use mock
    return MockLLMProvider()
