# Cycling Trip Planner Agent

An AI-powered agent that helps cyclists plan multi-day bike trips through natural conversation. Built with FastAPI, Claude (Anthropic), Pydantic, and a Streamlit frontend with interactive maps.

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

# Run the API server
uvicorn main:app --reload

# In a separate terminal, run the Streamlit UI
streamlit run chat_ui.py
```

The API will be available at `http://localhost:8000`. The chat UI will open at `http://localhost:8501`.

## Features

- **Conversational trip planning** — Chat naturally about your cycling trip and the agent gathers your preferences, then builds a complete day-by-day itinerary.
- **Preference confirmation gate** — Before planning, the agent must confirm daily distance, daily budget, accommodation type, and difficulty. If values are missing, it asks the user to confirm defaults or provide custom values.
- **New-trip preference reuse** — When a new trip starts in the same session, the agent asks whether to reuse the previous trip's preferences.
- **Flexible preference parsing** — Understands natural phrasing (e.g. `around 100km a day`), mixed accommodation patterns (`camping but hostel every 4th night`), and travel timing expressions.
- **Interactive map** — Route line with clickable waypoint markers showing weather, accommodation, and day info. Expandable day-by-day details below the map.
- **Weather safety checks** — The agent assesses weather conditions before presenting any plan, warning about rain, extreme temperatures, or strong winds.
- **7 planning tools** — 4 core (route, weather, elevation, accommodation) + 3 optional bonus tools (points of interest, visa requirements, budget estimation).
- **Server-side guardrails** — Tool ordering is enforced: route must be fetched before other tools, weather before accommodation.
- **Swap-ready architecture** — All tools use Python Protocol classes, so mock implementations can be replaced with real APIs without changing calling code.

## Pre-Built Routes

The mock route provider includes routes for:

| Route | Distance |
|-------|----------|
| Amsterdam → Copenhagen | 810 km |
| Paris → Amsterdam | 505 km |
| Berlin → Prague | 350 km |
| London → Edinburgh | 660 km |
| London → Bristol | 190 km |
| London → Brighton | 90 km |
| Edinburgh → Inverness | 255 km |
| London → Paris | 460 km |
| Rome → Florence | 280 km |
| Barcelona → Valencia | 350 km |
| Lisbon → Porto | 315 km |
| Munich → Vienna | 430 km |

All routes work in both directions. Unknown routes get a fallback heuristic.

## Usage

### Chat UI (recommended)

Run both the API server and Streamlit frontend, then chat in the browser. The map and day-by-day details appear on the right as the trip is planned.

### API directly

```bash
# Start a conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to cycle from London to Edinburgh in July"}'

# Continue with the returned session_id
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I prefer hostels and a moderate budget", "session_id": "<session_id>"}'
```

## Architecture

```
chat_ui.py            # Streamlit frontend (chat + map + day-by-day details)
main.py               # Uvicorn entrypoint
src/
  models.py           # All Pydantic models (route, weather, accommodation, etc.)
  agent/              # Agent logic
    orchestrator.py   # Core loop: Claude API calls, tool interception, response handling
    planner_policy.py # Deterministic planning slots + core-tool completion policy
    guardrails.py     # Server-side tool ordering validation
    session.py        # In-memory conversation state per session
    system_prompt.py  # Agent persona and planning instructions
    tool_definitions.py # Claude tool_use schema definitions
  tools/              # Swap-ready tool system
    protocol.py       # Protocol interfaces (structural subtyping)
    mock_route.py     # Mock route provider (12 pre-built European routes)
    mock_weather.py   # Mock weather provider (seasonal data)
    mock_accommodation.py # Mock accommodation (camping, hostel, hotel)
    mock_elevation.py # Mock elevation/difficulty profiles
    mock_poi.py       # Mock points of interest
    mock_visa.py      # Mock visa requirements (EU/Schengen rules)
    mock_budget.py    # Mock budget estimation
  api/                # FastAPI layer
    app.py            # App factory
    routes.py         # POST /chat endpoint
    dependencies.py   # Dependency injection
tests/                # 106 pytest tests
```

### Tools

**Core tools** (always used when building a trip plan):

| Tool | Description |
|------|-------------|
| `get_route` | Cycling route with waypoints, distance, and estimated days |
| `get_weather` | Weather conditions for a location in a given month |
| `get_elevation_profile` | Terrain difficulty, elevation gain, and max elevation |
| `find_accommodation` | Camping, hostel, and hotel options with prices and ratings |

**Bonus tools** (offered to the user after the core plan is presented):

| Tool | Description |
|------|-------------|
| `get_points_of_interest` | Historical sites, nature spots, food markets, viewpoints near waypoints |
| `check_visa_requirements` | Visa rules for countries along the route based on nationality |
| `estimate_budget` | Daily and total cost breakdown with money-saving tips |

### Key Design Decisions

**Hybrid orchestration** — Claude decides which tools to call via the tool_use API, but the server intercepts every tool call to apply guardrails before execution. This gives Claude's conversational flexibility with server-side ordering guarantees.

**Swap-ready tools** — Each tool is defined as a Python `Protocol` (structural subtyping). Mock implementations can be replaced with real API clients (Google Maps, OpenWeatherMap, etc.) without changing any calling code — the new class just needs to implement the same method signature.

**In-memory sessions** — Conversation state is stored in a dict keyed by session ID. Simple for the current scope; can be swapped to SQLite or Redis when persistence is needed.

**Manual tool loop** — Instead of using an auto-executing tool runner, the orchestrator manually loops: call Claude → intercept tool requests → validate via guardrails → execute → send results back. This is required for the guardrail interception step. A max-turns safety net (15 iterations) prevents infinite loops.

**Data-driven dispatch** — Tool routing uses a declarative registry (`_TOOL_DISPATCH`) mapping tool names to their input model, provider, method, and session flag. Adding a new tool is a single dict entry rather than a new code branch.

**Session lifecycle** — Sessions track a `last_active` timestamp and are automatically cleaned up after 1 hour of inactivity, preventing memory leaks in long-running deployments.

**Context window management** — The orchestrator trims conversation history to a rolling window of 40 messages, preserving the first user message (trip context) and the most recent turns.

**Deterministic policy layer** — In addition to prompt guidance, the server extracts typed planning slots (`start`, `end`, `month`, daily distance, daily budget, accommodation strategy, difficulty), enforces preference confirmation before planning, clarifies approximate travel timing (e.g. seasons), and enforces missing required core tools before allowing a final itinerary response.

## API Response & Frontend Data

The `POST /chat` endpoint returns a `ChatResponse` with four fields:

```json
{
  "session_id": "abc123",
  "response": "Here's your trip plan...",
  "tools_used": ["get_route", "get_weather", "get_elevation_profile", "find_accommodation"],
  "trip_data": { ... }
}
```

`trip_data` is a dict containing structured output accumulated from tool calls in the session. Use this to build frontend features (maps, cards, charts) without parsing Claude's text.

### Core tool keys

**`get_route`** — Route line and waypoint markers:
```json
{
  "start": "Amsterdam",
  "end": "Copenhagen",
  "total_distance_km": 810.0,
  "estimated_days": 9,
  "waypoints": [
    { "name": "Amsterdam", "latitude": 52.3676, "longitude": 4.9041, "day": 1 },
    { "name": "Bremen", "latitude": 53.0793, "longitude": 8.8017, "day": 5 }
  ]
}
```

**`get_weather`** — List of weather results (one per location checked):
```json
[
  {
    "location": "Amsterdam",
    "month": "june",
    "avg_temp_celsius": 17.5,
    "rain_chance_percent": 35.0,
    "wind_speed_kmh": 18.0,
    "summary": "Mild and pleasant with occasional showers."
  }
]
```

**`get_elevation_profile`** — Terrain difficulty for the route:
```json
{
  "start": "Amsterdam",
  "end": "Copenhagen",
  "total_elevation_gain_m": 1200.0,
  "max_elevation_m": 85.0,
  "difficulty": "easy",
  "profile_summary": "Mostly flat terrain along the North Sea coast..."
}
```

**`find_accommodation`** — List of results (one per waypoint searched):
```json
[
  {
    "location": "Bremen",
    "accommodations": [
      {
        "name": "Bremen City Camping",
        "type": "camping",
        "price_per_night": 12.0,
        "rating": 3.8
      },
      {
        "name": "Bremen Backpackers",
        "type": "hostel",
        "price_per_night": 28.0,
        "rating": 4.2
      }
    ]
  }
]
```

### Optional tool keys

**`get_points_of_interest`** — List of results (one per waypoint searched):
```json
[
  {
    "location": "Bremen",
    "points_of_interest": [
      {
        "name": "Bremen Town Musicians Statue",
        "category": "historical",
        "description": "Famous fairy-tale statue in the old town.",
        "latitude": 53.0763,
        "longitude": 8.8075
      }
    ]
  }
]
```

**`check_visa_requirements`** — Visa rules for crossed borders:
```json
{
  "nationality": "british",
  "countries": ["Netherlands", "Germany", "Denmark"],
  "requirements": [
    {
      "country": "Netherlands",
      "visa_required": false,
      "details": "EU/Schengen zone — no visa needed for short stays."
    }
  ]
}
```

**`estimate_budget`** — Cost breakdown:
```json
{
  "currency": "EUR",
  "budget_level": "moderate",
  "daily_breakdown": {
    "accommodation": 28.0,
    "food": 25.0,
    "transport": 5.0,
    "activities": 10.0,
    "misc": 5.0,
    "total": 73.0
  },
  "total_estimate": {
    "days": 9,
    "total": 657.0
  },
  "tips": ["Book hostels in advance for better rates", "..."]
}
```

### Accumulation across turns

`trip_data` in each API response contains the session's accumulated tool data. The Streamlit UI currently merges this into `st.session_state.trip_data` as well, so if you keep this behavior, prefer deduping list-type keys (`get_weather`, `find_accommodation`, `get_points_of_interest`) to avoid double-appending.

## Running Tests

```bash
pytest tests/ -v
# 106 tests covering models, tools, guardrails, planner policy, orchestrator multi-step flow, and API endpoints
```

### Test Coverage

| Test File | Count | What It Covers |
|-----------|-------|----------------|
| `test_models.py` | 21 | Pydantic model validation, field bounds, enum values, defaults |
| `test_tools.py` | 34 | All 7 mock tool providers, protocol compliance, filtering logic |
| `test_guardrails.py` | 12 | Tool ordering rules — what's blocked and when |
| `test_orchestrator.py` | 22 | **Multi-step reasoning**: full planning flow across 4+ tool calls, guardrail self-correction, deterministic preference confirmation, travel timing clarification, structured constraints, deterministic core-tool enforcement, session state accumulation, max-turns safety, error handling, message history |
| `test_planner_policy.py` | 13 | Slot extraction, mixed accommodation parsing, travel timing parsing, confirmation parsing, defaults, input enrichment, and core-tool completion policy |
| `test_api.py` | 4 | API endpoint, session persistence, response format, validation errors |

## What I Would Build With More Time

- **Real API integrations** — Replace mocks with Google Maps (routing between the waypoints using start/end lon and lat), OpenWeatherMap (weather), and booking APIs (accommodation). The Protocol pattern makes this a drop-in swap.
- **Persistent storage** — SQLite or PostgreSQL for conversation history and saved trip plans.
- **Streaming responses** — Use Claude's streaming API + SSE to stream the agent's response in real-time.
- **Trip export** — GPX file export for loading routes into cycling GPS devices.
- **User accounts** — Save and revisit past trip plans.
- **Personalised customisation** — Make trip customisable by adding stops along the way or changing the countries that the user crosses through on the way to the destination
