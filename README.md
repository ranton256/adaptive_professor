# A2UI Adaptive Professor 🎓

## CONCEPT

###  The "Adaptive Professor" (Interactive Learning Deck)

**The Concept:** A presentation that isn't just a monologue, but a dialogue. The Agent acts as a professor, and the user is a student who can stop the lecture at any point to ask questions, demand simpler explanations, or chase rabbit holes—without disrupting the flow.

**The Input:** A complex PDF (e.g., "The History of the Roman Senate") or a raw topic ("Teach me about Rust memory safety").

**The User Flow:**

1. **The "Lecture" Begins:** The Agent generates the first slide. It contains the core bullet points and a diagram.
2. **The "Choice" Architecture:** Instead of just a `[Next Slide]` button, the Agent analyzes the content and dynamically renders context-aware option buttons:
   - `[Next Slide]` (Advance the linear narrative)
   - `[Deep Dive: The Gracchi Brothers]` (Triggered by a specific entity mentioned on the slide)
   - `[Simplify]` (Rewrite this slide for a 5th-grade reading level)
   - `[Quiz Me]` (Generate a quick check-for-understanding interaction)
3. **The "Raise Hand" Feature:** The user types a freeform question: *"But how did they fund the army?"*
4. **The Generative Pivot:** The Agent pauses the planned sequence. It instantly researches the economic structure of the Roman army, generates a new visual slide answering that specific question, and inserts it as a "detour" before returning to the main track.

The A2UI "Magic": Branching Narratives

Most slide decks are a linked list ($A \rightarrow B \rightarrow C$). A2UI turns the deck into a graph. The Agent maintains a "Main Thread" of the presentation but can spawn ephemeral "Sub-Threads" based on user interaction. The UI isn't hardcoded; the buttons themselves are generative content.

The "How" (Technical Implementation)

This requires the ADK to send a payload that defines both the content and the permissible actions for that specific state.

JSON

```
{
  "type": "render_slide",
  "slide_id": "slide_04_rust_ownership",
  "layout": "split_content_diagram",
  "content": {
    "title": "The Borrow Checker",
    "text": "Rules that govern how memory is managed...",
    "diagram_code": "mermaid_graph_definition..."
  },
  "interactive_controls": [
    { 
      "label": "Next: Lifetimes", 
      "action": "advance_main_thread" 
    },
    { 
      "label": "Show Code Example", 
      "action": "branch_to_example", 
      "params": { "context": "borrow_checker_error" } 
    },
    { 
      "label": "Explain Metaphor", 
      "action": "overlay_explanation", 
      "params": { "style": "analogy" } 
    }
  ],
  "allow_freeform_input": true
}
```

Why Engineers Will Love This:

It solves the "One Size Fits All" problem of documentation and training. A Senior Engineer might click [Next] rapidly, while a Junior Engineer hits [Show Code Example] and [Explain Metaphor] on every slide. The same Agent serves both users a completely different UI experience.

## 📰 Press Release

For Immediate Release

Internal Engineering Blog

### The End of "One-Size-Fits-All" Learning: Introducing the Adaptive Professor

**SEATTLE** — We’ve all been there: sitting through a presentation that moves too fast, or conversely, one that belabors points we already know. Static slide decks and pre-recorded videos treat every learner the same, regardless of their background or curiosity. Today, we are releasing the **Adaptive Professor**, a reference implementation of the A2UI (Agent-to-User Interface) protocol that fundamentally changes how we consume technical knowledge.

The Adaptive Professor is not a slide generator; it is a **live teaching environment**. Users start by uploading a PDF (e.g., "Intro to Kubernetes" or "The History of Rome") or simply stating a topic. The Agent then begins a "lecture," streaming UI components that look like slides. However, unlike a standard deck, the user remains in control.

At any point, a user can click "Deep Dive" to spawn a sub-branch of slides exploring a niche topic, request a "Simplify" action to rewrite the current slide for a different experience level, or type a freeform question like *"Wait, how does this relate to our legacy architecture?"* The Agent pauses, researches the answer, and inserts a custom visual explanation directly into the slide flow before resuming the main thread.

"We realized that the best learning happens in office hours, not the lecture hall," says the Lead Architect of the A2UI project. "The Adaptive Professor scales that 'office hours' experience infinitely. It uses A2UI to dynamically render the interface the student needs *right now*—whether that’s a code snippet, a diagram, or a conceptual analogy."

This project serves as the gold standard for building complex, stateful applications using the Agent Development Kit (ADK) and A2UI. It demonstrates the power of escaping the chat box and embracing Generative UI.

------

## ❓ Frequently Asked Questions (FAQ)

### User FAQ

Q: Is this just generating a PowerPoint file I can download?

No. The "slides" are ephemeral UI components streamed in real-time. This allows the Agent to change the content of a slide while you are looking at it. For example, if you click "Show Python Example," the Agent swaps the generic code block for a Python-specific one instantly.

Q: What happens if I ask a question the document doesn't answer?

The Agent is connected to external tools (Web Search, Internal Wiki). If you ask a question outside the source material (e.g., "How does this concept apply to the game engine Unity?"), the Agent creates a "Detour Thread." It researches the answer, generates a new set of slides for that specific context, and presents them to you. Once satisfied, you click "Return to Lecture."

Q: Can I skip ahead?

Yes. The Agent understands the semantic structure of the topic. You can ask it to "Skip to the section on memory safety," and it will dynamically reorganize the remaining queue of slides.

### Technical FAQ

Q: How is the state managed?

We use the ADK's durable state machine. The presentation is modeled as a graph, not a list. The MainThread is the backbone. User interruptions create SubThreads. The Agent tracks the user's current_context and knowledge_level to decide which A2UI components to render next.

Q: Why use A2UI instead of a standard React frontend?

A standard frontend requires hard-coding every possible interaction path. Because the "Adaptive Professor" supports infinite branching (users can ask anything), we need the UI to be generated programmatically by the LLM. A2UI allows the backend to dictate that "Now we need a Quiz Component" or "Now we need a Split-Pane Code Viewer" without client-side changes.

Q: How do we handle latency?

The A2UI protocol streams JSONL. The "skeleton" of the slide renders immediately ( < 100ms), while the heavy text and diagram content stream in via tokens. This creates a "perceived latency" similar to a fast web app.

------

## 🛠 Developer Setup

We use **`uv`** for lightning-fast Python package management and resolution. Please do not use `pip` or `poetry` directly; stick to the workflows defined below to ensure deterministic environments.

### Prerequisites

- **Python:** 3.12 or higher
- **uv:** Installed globally (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **OpenAI/Anthropic API Key:** Set in your `.env`

### 1. Clone and Initialize

The project is configured via `pyproject.toml`.

Bash

```
git clone https://github.com/your-org/a2ui-adaptive-professor.git
cd a2ui-adaptive-professor

# Sync dependencies and create virtualenv automatically
uv sync
```

### 2. Configuration (`.env`)

Copy the example environment file and add your keys.

Bash

```
cp .env.example .env
```

Ensure your `.env` includes:

Ini, TOML

```
LLM_PROVIDER="anthropic" # or openai
ANTHROPIC_API_KEY="sk-..."
A2UI_RENDERER_URL="http://localhost:3000" # URL of your frontend harness
```

### 3. Project Structure

The logic is strictly separated between the Agent brain and the UI definitions.

Plaintext

```
├── src/
│   ├── agent/
│   │   ├── graph.py          # The ADK State Machine (Main vs Detour threads)
│   │   ├── tools.py          # RAG and Web Search tools
│   │   └── prompts.py        # System prompts for the "Professor" persona
│   ├── components/           # Pydantic models for A2UI components
│   │   ├── slides.py         # SlideLayout, BulletList, CodeBlock
│   │   └── interactive.py    # QuizWidget, DeepDiveButton
│   └── main.py               # Entry point
├── pyproject.toml            # Dependency manifest (managed by uv)
└── uv.lock                   # Lockfile
```

### 4. Running the Agent

We use `uv run` to execute the application within the isolated environment.

Bash

```
# Start the backend server (FastAPI + ADK)
uv run uvicorn src.main:app --reload --port 8000
```

### 5. Running the Simulation

To test the "Adaptive" capabilities without a frontend, use the CLI simulator:

Bash

```
uv run python -m src.cli_sim
```

Input: "Teach me about Rust Ownership."

Output: You will see the raw A2UI JSON payloads streaming in the console, simulating the slide renders.

### 6. Adding New UI Components

If you want the Agent to support a new type of visualization (e.g., a "3D Molecule Viewer"):

1. Define the model in `src/components/visuals.py`.
2. Register the component in the A2UI Registry in `src/main.py`.
3. Update `src/agent/prompts.py` to make the Agent aware it has this new capability.

### Dependencies

Key libraries managed in `pyproject.toml`:

- `fastapi`: API Server
- `langgraph`: State orchestration
- `pydantic-ai`: Structure enforcement
- `a2ui-python`: Official SDK for payload generation