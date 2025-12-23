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

    def simplify_slide(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Simplify the content and regenerate contextual controls."""
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

Return a JSON object with:
1. "content": {{"title": "...", "text": "2-4 educational sentences"}}
2. "controls": An array of interactive options. Each control has:
   - "label": The button text (be specific and contextual!)
   - "action": One of ["advance_main_thread", "deep_dive", "simplify_slide", "show_example", "quiz_me", "extend_lecture", "show_references"]
   - "params": Optional object with context (e.g., {{"concept": "specific term from this slide"}})

IMPORTANT for controls:
- If there's a next slide, include a "Next: [next topic]" button (action: advance_main_thread)
- If this is the last slide, include a "Continue Learning" button (action: extend_lecture)
- Identify 1-2 key concepts/terms from YOUR content that could be deep-dived (action: deep_dive, params: {{"concept": "..."}})
- Always include a "Simplify This" option (action: simplify_slide)
- Optionally include "Show Example" or "Quiz Me" if appropriate for the content
- Always include "View References" button (action: show_references) to let students find more resources

Example response:
{{
  "content": {{
    "title": "The Borrow Checker",
    "text": "Rust's borrow checker enforces memory safety at compile time. It tracks ownership and ensures references don't outlive their data. This prevents common bugs like use-after-free and data races."
  }},
  "controls": [
    {{"label": "Next: Lifetimes", "action": "advance_main_thread"}},
    {{"label": "Deep Dive: Ownership Rules", "action": "deep_dive", "params": {{"concept": "ownership rules"}}}},
    {{"label": "Deep Dive: Data Races", "action": "deep_dive", "params": {{"concept": "data races"}}}},
    {{"label": "Show Code Example", "action": "show_example", "params": {{"type": "borrow_checker_error"}}}},
    {{"label": "Simplify This", "action": "simplify_slide"}}
  ]
}}

Return ONLY the JSON object."""


def get_simplify_prompt(content: SlideContent, next_title: str | None) -> str:
    return f"""Rewrite this educational content for a complete beginner (5th grade reading level).
Use simpler words, shorter sentences, and add a helpful analogy if possible.

Original title: {content.title}
Original text: {content.text}

{"Next slide will be: " + next_title if next_title else "This is the final slide."}

Return a JSON object with simplified content AND new contextual controls:
{{
  "content": {{"title": "...", "text": "simplified explanation with analogy"}},
  "controls": [
    {{"label": "Next: [topic]", "action": "advance_main_thread"}},
    {{"label": "Deep Dive: [concept]", "action": "deep_dive", "params": {{"concept": "..."}}}},
    {{"label": "Quiz Me", "action": "quiz_me"}}
  ]
}}

Keep controls relevant to the simplified content. Always include navigation if there's a next slide.
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
    {{"label": "Simplify This", "action": "simplify_slide"}}
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

1. For DATA VISUALIZATION and SIMULATIONS:
   - Use JavaScript with Chart.js format for interactive charts
   - Generate data programmatically when showing trends, simulations, or comparisons
   - Your code MUST set a `chartConfig` variable with the Chart.js configuration
   - Supported chart types: 'line', 'bar', 'pie', 'doughnut', 'scatter'
   - Example:
   ```javascript
   // Simulate exponential decay
   const times = [];
   const values = [];
   let value = 100;
   for (let t = 0; t < 50; t++) {{
     times.push(t);
     values.push(value);
     value *= 0.95;
   }}

   chartConfig = {{
     type: 'line',
     data: {{
       labels: times,
       datasets: [{{
         label: 'Decay over time',
         data: values,
         borderColor: 'rgb(75, 192, 192)',
         tension: 0.1
       }}]
     }},
     options: {{
       scales: {{
         y: {{ title: {{ display: true, text: 'Value' }} }},
         x: {{ title: {{ display: true, text: 'Time (s)' }} }}
       }}
     }}
   }};
   ```

2. For SCIENCE topics with EQUATIONS:
   - Use LaTeX for equations: $E = mc^2$ or $$\\frac{{dN}}{{dt}} = -\\lambda N$$
   - Use step-by-step numbered explanations with LaTeX formulas
   - For reactions: $^1H + ^1H \\rightarrow ^2H + e^+ + \\nu_e$

3. For PROGRAMMING topics:
   - Use JavaScript/TypeScript code that could run in a browser
   - Use working code examples with comments

4. For PROCESSES or WORKFLOWS:
   - Use Mermaid flowcharts with SIMPLE labels (no special chars, no parentheses in labels)
   - Node labels must be quoted if they contain spaces: A["Step One"]
   - Example: ```mermaid\\nflowchart LR\\n  A["Step 1"] --> B["Step 2"]\\n```

5. For HIERARCHIES or STRUCTURES:
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
    {{"label": "Simplify This", "action": "simplify_slide"}}
  ]
}}

The first control MUST be "Return to: {content.title}" to let them go back.
Return ONLY the JSON object."""


def get_references_prompt(topic: str, outline: list[str], current_index: int) -> str:
    covered_slides = outline[: current_index + 1]
    covered_str = "\n".join(f"- {t}" for t in covered_slides)
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
    {{"label": "Return to Lecture", "action": "return_to_main", "params": {{"slide_index": {current_index}}}}},
    {{"label": "Continue Learning", "action": "advance_main_thread"}}
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

    def simplify_slide(
        self, content: SlideContent, context: SlideGenerationContext
    ) -> GeneratedSlide:
        """Simplify the content and regenerate contextual controls."""
        next_title = (
            context.outline[context.slide_index + 1]
            if context.slide_index < len(context.outline) - 1
            else None
        )
        response = self.model.generate_content(get_simplify_prompt(content, next_title))
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

    def simplify_slide(
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
            messages=[{"role": "user", "content": get_simplify_prompt(content, next_title)}],
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

        # Always have simplify
        controls.append(InteractiveControl(label="Simplify This", action="simplify_slide"))

        # Quiz option for non-intro/conclusion slides
        if context.slide_index not in [0, context.total_slides - 1]:
            controls.append(InteractiveControl(label="Quiz Me", action="quiz_me"))

        # Always offer references
        controls.append(InteractiveControl(label="View References", action="show_references"))

        content = SlideContent(
            title=context.slide_title,
            text=f"This is the content for slide {context.slide_index + 1} about {context.topic}. "
            f"Here we explore {context.slide_title.lower()} in detail, covering key aspects of {concept}.",
        )

        return GeneratedSlide(content=content, controls=controls)

    def simplify_slide(
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

        simplified_content = SlideContent(
            title=f"{content.title} (Simplified)",
            text=f"Simple version: {content.text[:100]}... "
            "Think of it like a simple everyday example that makes this concept easy to understand.",
        )

        return GeneratedSlide(content=simplified_content, controls=controls)

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
            InteractiveControl(label="Simplify This", action="simplify_slide"),
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
            InteractiveControl(label="Simplify This", action="simplify_slide"),
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
        controls = [
            InteractiveControl(
                label="Return to Lecture",
                action="return_to_main",
                params={"slide_index": current_index},
            ),
            InteractiveControl(label="Continue Learning", action="advance_main_thread"),
        ]

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
