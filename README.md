# multi-agent-workflow

A LangGraph multi-agent research assistant built for the **turing-interview** exercise. Four specialized agents collaborate with human-in-the-loop clarification, live Tavily search, stateful multi-turn memory, and a Next.js chat UI deployable to Vercel.

---

## Deliverables Checklist

| # | Requirement | Status |
|---|---|---|
| 1 | Working LangGraph with 4 agents | Done - Clarity, Research, Validator, Synthesis |
| 2 | State schema with all required fields | Done - 7 fields in backend/src/state.py |
| 3 | 3 conditional routing functions | Done - _route_research, _route_validator, interrupt inside Clarity |
| 4 | Feedback loop Validator back to Research with attempt counter | Done - loops up to 3x, tracked in research_attempts |
| 5 | Interrupt mechanism for unclear queries | Done - langgraph.types.interrupt() in Clarity agent |
| 6 | Multi-turn conversation with memory | Done - MemorySaver checkpointer, state persists per thread_id |
| 7 | 2 example conversation turns | Done - see Example Conversations below |
| 8 | Software engineering best practices | Done - typed state, single-responsibility agents, clear module separation |
| 9 | README with run instructions | Done - see Running the System below |
| 10 | Assumptions documented | Done - see Assumptions below |
| 11 | Beyond Expected Deliverable | Done - see last section |

---

## Architecture

Four agents connected in a LangGraph StateGraph with MemorySaver checkpointer:

- Clarity Agent checks if the query names a specific company; fires interrupt() if vague
- Research Agent runs Tavily live search + mock data lookup, scores confidence 0-10
- Validator Agent checks if findings fully answer the query, loops back up to 3 times
- Synthesis Agent uses full conversation history to write the final response

### Routing Logic

| From | To | Condition |
|---|---|---|
| Clarity | INTERRUPT | No company name detected |
| Clarity | Research | clarity_status = clear |
| Research | Validator | confidence_score < 6 |
| Research | Synthesis | confidence_score >= 6 (fast path) |
| Validator | Research | insufficient AND attempts < 3 |
| Validator | Synthesis | sufficient OR attempts >= 3 |

---

## State Schema

| Field | Type | Description |
|---|---|---|
| messages | list[BaseMessage] | Full conversation history, append-only via add_messages |
| query | str | Current query, updated after clarification |
| clarity_status | clear or needs_clarification | Set by Clarity Agent |
| research_findings | str | Synthesized research output |
| confidence_score | int 0-10 | Research Agent self-rating |
| validation_result | sufficient or insufficient | Validator verdict |
| research_attempts | int | Retry counter, resets to 0 each new turn |

---

## Project Structure

    /                          <- Next.js frontend (Vercel root)
    +-- app/
    |   +-- page.tsx           <- Chat UI
    |   +-- api/chat/route.ts  <- proxy to Python backend
    |   +-- api/clarify/route.ts
    +-- package.json
    +-- vercel.json
    +-- workflow.html
    +-- README.md
    +-- backend/               <- Python LangGraph backend
        +-- src/
        |   +-- state.py
        |   +-- data.py        <- mock data (Apple, Tesla)
        |   +-- llm.py
        |   +-- graph.py
        |   +-- agents/
        |       +-- clarity.py
        |       +-- research.py
        |       +-- validator.py
        |       +-- synthesis.py
        +-- api.py             <- FastAPI server
        +-- main.py            <- CLI entry point
        +-- pyproject.toml
        +-- uv.lock

---

## Setup

### 1. Install Python dependencies

    cd backend
    uv sync

### 2. Create backend/.env

    OPENROUTER_API_KEY=sk-or-...
    TAVILY_API_KEY=tvly-...
    MODEL_NAME=openai/gpt-4o-mini
    LANGCHAIN_API_KEY=lsv2_...
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_PROJECT=turing-interview

### 3. Install frontend dependencies

    npm install

### 4. Create .env.local at repo root

    BACKEND_URL=http://localhost:8000

---

## Running the System

### Option A: Chat UI (recommended)

Terminal 1 - Python backend:

    cd backend
    uv run uvicorn api:app --port 8000 --reload

Terminal 2 - Next.js frontend:

    npm run dev

Open http://localhost:3000

### Option B: CLI

    cd backend
    uv run python main.py


---

## Memory and Multi-Turn Conversation

The system uses LangGraph's built-in MemorySaver checkpointer (in-memory SQLite-backed store) to persist state across turns. Each browser session gets a unique thread_id (UUID). The FastAPI backend holds a single graph instance; MemorySaver stores the full checkpoint per thread_id so messages accumulate correctly across API calls.

- New turn: graph starts from START, new message appended to history via add_messages reducer
- Interrupt/resume: graph pauses mid-execution, resumes from the interrupted node
- Follow-up questions: Synthesis Agent receives the full messages list so it can reference prior context

---

## Example Conversations

### Conversation 1 - Vague query triggers interrupt, then follow-up uses memory

Turn 1a - vague query, interrupt fires:

    You: Tell me about a big tech company
    [clarity]
    Assistant: Your query is a bit vague - which specific company are you asking about?
    You: Apple
    [clarity] [research confidence=9] [synthesis]
    Assistant: Apple Inc. has been making significant moves recently. The company launched
    its Vision Pro headset and hit a record  in services revenue. Apple Intelligence
    AI is being integrated across iOS 18, and the company is expanding manufacturing in India...

Turn 1b - follow-up uses full conversation history:

    You: What about their main competitors?
    [clarity] [research confidence=8] [synthesis]
    Assistant: Building on what we discussed about Apple, their main competitors include
    Samsung (hardware), Google (services/AI), and Microsoft (enterprise). Samsung leads
    in global smartphone market share while Google competes directly on AI assistant features...

### Conversation 2 - Low confidence triggers validator loop

Turn 2a - unknown company, validator loops:

    You: Tell me about Stripe
    [clarity] [research confidence=4] [validator: insufficient, attempt=1]
           [research confidence=7] [validator: sufficient] [synthesis]
    Assistant: Stripe is a leading fintech company founded in 2010. While our data is
    limited compared to publicly traded companies, Stripe is valued at ~ and processes
    hundreds of billions in payments annually. Key developments include...

Turn 2b - follow-up in same session:

    You: Who are their main investors?
    [clarity] [research confidence=6] [synthesis]
    Assistant: Following up on Stripe from our earlier conversation - their major investors
    include Sequoia Capital, Andreessen Horowitz, and General Catalyst...


---

## Deploying to Vercel

1. Push repo to GitHub
2. Import at vercel.com - Root Directory is auto-detected as / (Next.js)
3. Add environment variable: BACKEND_URL = your deployed backend URL
4. Deploy the Python backend separately (Railway, Render, Fly.io) and point BACKEND_URL to it

---

## Assumptions

- Company name matching uses case-insensitive substring search in mock data
- research_attempts resets to 0 at the start of each new conversation turn
- When interrupt fires, the clarification text is added as a HumanMessage to message history
- LLM temperature is 0 for deterministic routing decisions
- Tavily search fails gracefully if TAVILY_API_KEY is missing (falls back to mock data only)
- The validator loop exits at 3 attempts regardless of validation_result to prevent infinite loops
- MemorySaver is in-process memory - state is lost if the backend server restarts

---

## Beyond Expected Deliverable

- **Live web search via Tavily**: Research Agent queries the real web instead of static mock data only
- **Dual data sources**: Combines Tavily live results with curated mock data (Apple, Tesla)
- **FastAPI REST backend**: api.py exposes the graph as /chat, /clarify, /health endpoints
- **Next.js chat UI**: Full React chat interface with real-time agent trace visualization
- **Agent trace visualization**: UI shows clarity -> research (*9) -> synthesis with confidence scores
- **Human-in-the-loop in UI**: Clarification prompts appear as amber cards with inline input
- **OpenRouter integration**: Model-agnostic - set MODEL_NAME to swap LLMs
- **LangSmith tracing**: All agent runs traced to turing-interview project automatically
- **Multi-turn memory in UI**: MemorySaver persists conversation state per UUID session
- **Suggested prompts**: UI shows clickable examples covering all 3 routing paths
