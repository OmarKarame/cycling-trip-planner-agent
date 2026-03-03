# Cycling Trip Planner Agent

An AI-powered agent that helps cyclists plan multi-day bike trips through natural conversation. Built with FastAPI, Claude (Anthropic), and Pydantic.

## Quick Start

```bash
# Clone and enter the project
git clone https://github.com/OmarKarame/cycling-trip-planner-agent.git
cd cycling-trip-planner

# Create a virtual environment and install
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Set your Anthropic API key
cp .env.example .env
# Edit .env and add your key

# Run the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Usage

```bash
# Start a conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to cycle from Amsterdam to Copenhagen in June"}'

# Continue with the returned session_id
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I prefer camping but a hostel every 3rd night", "session_id": "<session_id>"}'
```

## Architecture

```
src/
  agent/              # Agent logic
    orchestrator.py   # Core loop: Claude API calls, tool interception, response handling
    guardrails.py     # Server-side tool ordering validation
    session.py        # In-memory conversation state per session
    system_prompt.py  # Agent persona and planning instructions
    tool_definitions.py # Claude tool_use schema definitions
  tools/              # Swap-ready tool system
    protocol.py       # Protocol interfaces (structural subtyping)
    mock_*.py         # Mock implementations for each tool
  api/                # FastAPI layer
    app.py            # App factory
    routes.py         # POST /chat endpoint
    dependencies.py   # Dependency injection
tests/                # pytest suite
main.py               # Uvicorn entrypoint
```

### Key Decisions

**Hybrid orchestration** — Claude decides which tools to call via the tool_use API, but the server intercepts every tool call to apply guardrails before execution. For example, the route must be fetched before accommodations or elevation can be looked up. This gives us Claude's conversational flexibility with our ordering guarantees.

**Swap-ready tools** — Each tool is defined as a Python `Protocol` (structural subtyping). Mock implementations can be replaced with real API clients (Google Maps, OpenWeatherMap, etc.) without changing any calling code — the new class just needs to implement the same method signature.

**In-memory sessions** — Conversation state is stored in a dict keyed by session ID. Simple for the current scope; can be swapped to SQLite or Redis when persistence is needed.

**Manual tool loop** — Instead of using an auto-executing tool runner, the orchestrator manually loops: call Claude, intercept tool requests, validate, execute, send results back. This is required for the guardrail interception step.

## Running Tests

```bash
pytest tests/ -v
```

## What I Would Build With More Time

- **Real API integrations** — Replace mocks with Google Maps (routing and places of interest), OpenWeatherMap (weather), and booking APIs (accommodation). The Protocol pattern makes this a drop-in swap.
- **Persistent storage** — SQLite or PostgreSQL for conversation history and saved trip plans.
- **Structured trip output** — Return a JSON trip object alongside chat text so a frontend can render maps, itineraries, and daily breakdowns.
- **Streaming responses** — Use Claude's streaming API + SSE to stream the agent's response in real-time.
- **Frontend app** — React/Next.js UI with an interactive map showing the route, daily segments, and accommodation markers.
- **Trip export** — GPX file export for loading routes into cycling GPS devices.
