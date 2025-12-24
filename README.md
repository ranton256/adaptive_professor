# Adaptive Professor

An AI-powered interactive learning platform that transforms static presentations into dynamic, branching educational experiences. Users can explore topics through context-aware navigation, request deep dives into specific concepts, and receive personalized content that adapts to their learning needs in real-time.

## Concept

The "Adaptive Professor" is a presentation that isn't just a monologue, but a dialogue. The Agent acts as a professor, and the user is a student who can stop the lecture at any point to ask questions, demand simpler explanations, or chase rabbit holes—without disrupting the flow.

**The Input:** A complex PDF (e.g., "The History of the Roman Senate") or a raw topic ("Teach me about Rust memory safety").

**The User Flow:**

1. **The "Lecture" Begins:** The Agent generates the first slide with core bullet points and a diagram.
2. **The "Choice" Architecture:** Instead of just a `[Next Slide]` button, the Agent analyzes the content and dynamically renders context-aware option buttons:
   - `[Next Slide]` (Advance the linear narrative)
   - `[Deep Dive: The Gracchi Brothers]` (Triggered by a specific entity mentioned on the slide)
   - `[Simplify]` (Rewrite this slide for a 5th-grade reading level)
   - `[Quiz Me]` (Generate a quick check-for-understanding interaction)
3. **The "Raise Hand" Feature:** The user types a freeform question: *"But how did they fund the army?"*
4. **The Generative Pivot:** The Agent pauses the planned sequence, researches the answer, generates a new visual slide, and inserts it as a "detour" before returning to the main track.

### The A2UI "Magic": Branching Narratives

Most slide decks are a linked list (A → B → C). A2UI turns the deck into a graph. The Agent maintains a "Main Thread" of the presentation but can spawn ephemeral "Sub-Threads" based on user interaction. The UI isn't hardcoded; the buttons themselves are generative content.

## Features

- **Interactive Slide Navigation** - AI-generated context-aware navigation buttons that adapt to content
- **Deep Dive Exploration** - Spawn sub-threads to explore specific concepts without losing your place
- **Content Adaptation** - Clarify, simplify, or regenerate slides based on your comprehension level
- **Quiz Generation** - On-demand assessment questions with feedback
- **Code Examples** - Executable code demonstrations for technical topics
- **Concept Maps** - Interactive visualizations of topic relationships
- **Curated References** - Validated learning resources with working links
- **Multi-LLM Support** - Works with Google Gemini (default), Anthropic Claude, or OpenAI

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- API key for your preferred LLM provider

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/adaptive_professor.git
   cd adaptive_professor
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Install backend dependencies**
   ```bash
   uv sync --all-extras
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the Application

Start both the backend and frontend:

```bash
# Terminal 1 - Backend (port 8000)
uv run uvicorn src.main:app --reload --port 8000

# Terminal 2 - Frontend (port 3000)
cd frontend
npm run dev
```

Open http://localhost:3000 in your browser.

## Configuration

Configure the application via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (`gemini`, `anthropic`, `openai`) | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `A2UI_RENDERER_URL` | Frontend URL | `http://localhost:3000` |

Frontend configuration (in `frontend/.env.local`):

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## Architecture

Adaptive Professor uses an A2UI (Agent-to-User Interface) architecture where the AI agent controls both content and available user actions.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│  FastAPI Server │────▶│   LLM Provider  │
│   (React/TS)    │◀────│    (Python)     │◀────│ (Gemini/Claude) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │     SQLite      │
                        │   (Sessions)    │
                        └─────────────────┘
```

### Project Structure

```
adaptive_professor/
├── src/                    # Python backend
│   ├── main.py             # FastAPI entry point & API routes
│   ├── llm.py              # LLM provider abstraction
│   ├── session.py          # Lecture session management
│   ├── database.py         # SQLite persistence
│   ├── config.py           # Environment configuration
│   ├── url_validator.py    # Reference link validation
│   ├── a2ui_core.py        # Vendored A2UI Core Types
│   └── a2ui_adapter.py     # Domain -> A2UI Adapter
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/            # Next.js app router
│       ├── components/     # React components
│       └── lib/            # API client & utilities
│           ├── a2ui-types.ts    # Frontend A2UI types
│           └── a2ui-renderer.tsx # Generic A2UI Renderer
├── tests/                  # Backend tests
│   └── bdd/                # BDD step definitions
├── features/               # Gherkin feature specifications
└── pyproject.toml          # Python project configuration
```

### A2UI Protocol

The Agent sends standard A2UI Message payloads (JSON). The UI is fully generic and renders whatever component tree the backend sends.

```json
{
  "type": "render",
  "meta": {
    "slide_id": "slide_04_rust_ownership",
    "session_id": "abc123",
    "slide_index": 3,
    "total_slides": 10
  },
  "root": {
    "type": "container",
    "layout": "vertical",
    "children": [
      {
        "type": "text",
        "content": "The Borrow Checker",
        "variant": "h2"
      },
      {
        "type": "markdown",
        "content": "Rules that govern how memory is managed..."
      },
      {
        "type": "container",
        "layout": "horizontal",
        "children": [
            { 
              "type": "button", 
              "label": "Next: Lifetimes", 
              "action": { "type": "action", "name": "advance_main_thread", "parameters": {} },
              "variant": "primary"
            },
            { 
              "type": "button", 
              "label": "Show Code Example", 
              "action": { "type": "action", "name": "show_example", "parameters": {} },
              "variant": "secondary"
            }
        ]
      }
    ]
  }
}
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/lecture/start` | Start a new lecture session |
| `POST` | `/api/lecture/{session_id}/action` | Perform an action on current slide |

### Actions

| Action | Description |
|--------|-------------|
| `advance_main_thread` | Move to next slide |
| `go_previous` | Return to previous slide |
| `deep_dive` | Explore a specific concept |
| `return_to_main` | Return from deep dive to main lecture |
| `clarify_slide` | Regenerate with clearer explanation |
| `regenerate_slide` | Generate alternative version with feedback |
| `show_example` | Generate code/practical example |
| `quiz_me` | Generate assessment question |
| `show_references` | Display learning resources |
| `show_concept_map` | Show topic visualization |
| `extend_lecture` | Generate additional slides |

## Development

### Running Tests

```bash
# Backend tests
uv run pytest

# Backend tests with coverage
uv run pytest --cov

# Frontend tests
cd frontend && npm test

# Frontend tests in watch mode
cd frontend && npm run test:watch
```

### Linting & Formatting

```bash
# Backend
uv run ruff check src tests
uv run ruff format src tests

# Frontend
cd frontend
npm run lint
npm run format
```

### Pre-commit Hooks

Pre-commit hooks run automatically on commit. To run manually:

```bash
uv run pre-commit run --all-files
```

## Development Methodology

This project uses **Behavior-Driven Development (BDD)**:

1. Define feature specifications in `features/*.feature` (Gherkin format)
2. Implement step definitions in `tests/bdd/`
3. Write unit tests alongside implementation
4. Ensure all tests pass before committing

## FAQ

### User FAQ

**Q: Is this just generating a PowerPoint file I can download?**

No. The "slides" are ephemeral UI components streamed in real-time. This allows the Agent to change the content of a slide while you are looking at it. For example, if you click "Show Python Example," the Agent swaps the generic code block for a Python-specific one instantly.

**Q: What happens if I ask a question the document doesn't answer?**

The Agent is connected to external tools (Web Search, Internal Wiki). If you ask a question outside the source material (e.g., "How does this concept apply to the game engine Unity?"), the Agent creates a "Detour Thread." It researches the answer, generates a new set of slides for that specific context, and presents them to you. Once satisfied, you click "Return to Lecture."

**Q: Can I skip ahead?**

Yes. The Agent understands the semantic structure of the topic. You can ask it to "Skip to the section on memory safety," and it will dynamically reorganize the remaining queue of slides.

### Technical FAQ

**Q: How is the state managed?**

The presentation is modeled as a graph, not a list. The MainThread is the backbone. User interruptions create SubThreads. The Agent tracks the user's `current_context` and `knowledge_level` to decide which A2UI components to render next.

**Q: Why use A2UI instead of a standard React frontend?**

A standard frontend requires hard-coding every possible interaction path. Because the "Adaptive Professor" supports infinite branching (users can ask anything), we need the UI to be generated programmatically by the LLM. A2UI allows the backend to dictate "Now we need a Quiz Component" or "Now we need a Split-Pane Code Viewer" without client-side changes.

**Q: How do we handle latency?**

The A2UI protocol streams JSONL. The "skeleton" of the slide renders immediately (<100ms), while the heavy text and diagram content stream in via tokens. This creates a "perceived latency" similar to a fast web app.

## Technology Stack

**Backend:**
- FastAPI - Web framework
- Pydantic - Data validation
- aiosqlite - Async SQLite persistence
- google-generativeai / anthropic - LLM clients

**Frontend:**
- Next.js 16 - React framework
- React 19 - UI library
- Tailwind CSS 4 - Styling
- react-markdown - Content rendering
- KaTeX - Math rendering

**Development:**
- pytest / vitest - Testing
- pytest-bdd - BDD testing
- ruff - Python linting/formatting
- ESLint / Prettier - JS/TS linting/formatting

## License

MIT License
