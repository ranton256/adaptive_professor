# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Adaptive Professor is an A2UI (Agent-to-User Interface) application that creates interactive, branching learning experiences. Users can upload PDFs or specify topics, and the agent delivers "lectures" as streamed UI components with context-aware navigation options (Deep Dive, Simplify, Quiz Me) and freeform questioning.

## Development Methodology

This project uses **Behavior-Driven Development (BDD)**. Feature requirements are defined as Gherkin specifications in `features/*.feature` before implementation. When implementing new features:

1. Write/update Gherkin scenarios in `features/`
2. Implement step definitions in `tests/bdd/`
3. Write unit tests alongside implementation
4. Ensure all tests pass before committing

## Development Commands

### Backend (Python)

```bash
# Install all dependencies (creates .venv automatically)
uv sync --all-extras

# Run the FastAPI backend server
uv run uvicorn src.main:app --reload --port 8000

# Run backend tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Lint and format
uv run ruff check src tests
uv run ruff format src tests
```

### Frontend (JavaScript/TypeScript)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Lint and format
npm run lint
npm run format
```

### Pre-commit Hooks

Pre-commit hooks are configured to run automatically. To run manually:

```bash
# Run on staged files
uv run pre-commit run

# Run on all files
uv run pre-commit run --all-files
```

Hooks run: ruff (lint/format), pytest, eslint, prettier, vitest

## Architecture

**State Model**: Presentations are modeled as graphs, not linear lists. The ADK state machine maintains a `MainThread` backbone with ephemeral `SubThreads` spawned by user interactions (questions, deep dives).

**Directory Structure**:
```
├── src/                    # Python backend
│   ├── agent/              # ADK state machine, tools, prompts
│   ├── components/         # Pydantic models for A2UI components
│   ├── config.py           # Settings from environment
│   └── main.py             # FastAPI entry point
├── tests/                  # Python tests
│   └── bdd/                # BDD step definitions
├── features/               # Gherkin feature files
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/            # Next.js app router pages
│       ├── components/     # React components
│       └── lib/            # API client, utilities
```

**A2UI Protocol**: The agent sends JSONL payloads defining both content and permissible actions per state. UI components stream progressively (skeleton < 100ms, content via tokens).

**Adding Components**:
1. Define Pydantic model in `src/components/`
2. Add corresponding TypeScript interface in `frontend/src/lib/api.ts`
3. Create React component in `frontend/src/components/`
4. Register in A2UI Registry (`src/main.py`)
5. Update agent prompts to expose the capability

## Configuration

Copy `.env.example` to `.env` and configure:
- `LLM_PROVIDER` - "anthropic" or "openai"
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- `A2UI_RENDERER_URL` - Frontend URL (default: http://localhost:3000)

Frontend uses `NEXT_PUBLIC_API_URL` (default: http://localhost:8000)

## Testing Strategy

- **Unit tests**: `tests/test_*.py` (backend), `src/**/*.test.tsx` (frontend)
- **BDD tests**: `tests/bdd/` with step definitions mapping to `features/*.feature`
- **Integration tests**: Test full API flows through FastAPI TestClient

All tests must pass before commits (enforced by pre-commit hooks).
