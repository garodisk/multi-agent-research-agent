# multi-agent-workflow

A LangGraph multi-agent research assistant built for the **Turing interview** exercise. Four specialized agents collaborate with human-in-the-loop clarification, live Tavily search, stateful multi-turn memory, and a Next.js chat UI deployed on Vercel + Render.

---

## Live Demo

- **Chat UI (Vercel):** https://multi-agent-research-agent-zh13-kappa.vercel.app
- **Backend API (Render):** https://multi-agent-research-backend-cskw.onrender.com
- **GitHub:** https://github.com/garodisk/multi-agent-research-agent

> Note: The Render free tier sleeps after inactivity, so the very first message may take ~30 s while the backend cold-starts. Subsequent messages are fast.

---

## Deliverables Checklist

| # | Requirement | Status |
|---|---|---|
| 1 | Working LangGraph with 4 agents | Done — Clarity, Research, Validator, Synthesis |
| 2 | State schema with all required fields | Done — 7 fields in `backend/src/state.py` |
| 3 | 3 conditional routing functions | Done — `_route_research`, `_route_validator`, interrupt in Clarity |
| 4 | Validator → Research feedback loop with attempt counter | Done — up to 3 attempts, tracked in `research_attempts` |
| 5 | Interrupt mechanism for unclear queries | Done — `langgraph.types.interrupt()` in Clarity agent |
| 6 | Multi-turn conversation with memory | Done — `MemorySaver` checkpointer keyed on `thread_id` |
| 7 | 2 example conversation turns | Done — see Example Conversations below |
| 8 | Software engineering best practices | Done — typed state, single-responsibility agents, clear module layout |
| 9 | README with run instructions | Done — see Running Locally |
| 10 | Assumptions documented | Done — see Assumptions |
| 11 | Beyond Expected Deliverable | Done — see final section |

---

## Architecture

Four agents connected in a LangGraph `StateGraph` with a `MemorySaver` checkpointer:

- **Clarity Agent** — reads the entire conversation history + current query, decides if the query can be researched. Fires `interrupt()` if no company anywhere in the context.
- **Research Agent** — LLM-rewrites the current query into a self-contained search query (e.g. `"its recent products?"` after Tesla → `"Tesla recent products"`), then runs Tavily live search + mock data lookup, and self-rates confidence 0-10.
- **Validator Agent** — decides if findings sufficiently answer the query. Loops back to Research up to 3 times if insufficient.
- **Synthesis Agent** — writes the final response using the research findings, scoped to the correct company (not the earlier dominant one).

### Routing

| From | To | Condition |
|---|---|---|
| Clarity | INTERRUPT | No company in history AND no company in query |
| Clarity | Research | `clarity_status = clear` |
| Research | Validator | `confidence_score < 6` |
| Research | Synthesis | `confidence_score >= 6` (fast path) |
| Validator | Research | `insufficient` AND `research_attempts < 3` |
| Validator | Synthesis | `sufficient` OR `research_attempts >= 3` |

---

## State Schema

`backend/src/state.py`

| Field | Type | Description |
|---|---|---|
| messages | `list[BaseMessage]` | Full conversation history, append-only via `add_messages` |
| query | `str` | Current user query, updated on clarification resume |
| clarity_status | `"clear" \| "needs_clarification"` | Set by Clarity Agent |
| research_findings | `str` | Findings from Research Agent |
| confidence_score | `int` 0-10 | Research Agent self-rating |
| validation_result | `"sufficient" \| "insufficient"` | Validator verdict |
| research_attempts | `int` | Retry counter for the loop |

---

## Project Structure

```
/
├── app/                       ← Next.js frontend (Vercel root)
│   ├── page.tsx               ← Chat UI
│   └── api/
│       ├── chat/route.ts      ← proxy → backend /chat
│       └── clarify/route.ts   ← proxy → backend /clarify
├── package.json
├── vercel.json
├── workflow.html              ← Architecture guide (HTML)
├── README.md
└── backend/                   ← Python LangGraph service (Render root)
    ├── src/
    │   ├── state.py
    │   ├── data.py            ← mock data (Apple, Tesla)
    │   ├── llm.py             ← OpenRouter LLM factory
    │   ├── graph.py           ← StateGraph wiring + routing
    │   └── agents/
    │       ├── clarity.py
    │       ├── research.py
    │       ├── validator.py
    │       └── synthesis.py
    ├── api.py                 ← FastAPI /chat, /clarify, /health
    ├── main.py                ← CLI entry point
    ├── test_multiturn.py      ← Multi-turn regression test
    ├── pyproject.toml
    └── uv.lock
```

---

## Running Locally (with your own API keys)

### Prerequisites
- Python 3.11+, [uv](https://github.com/astral-sh/uv) package manager
- Node.js 18+
- API keys: OpenRouter (required), Tavily (optional but recommended), LangSmith (optional)

### 1. Clone and install
```bash
git clone https://github.com/garodisk/multi-agent-research-agent.git
cd multi-agent-research-agent

# Backend deps
cd backend
uv sync

# Frontend deps
cd ..
npm install
```

### 2. Create `backend/.env`
```env
OPENROUTER_API_KEY=sk-or-...           # required — get one at https://openrouter.ai
TAVILY_API_KEY=tvly-...                # optional — get one at https://tavily.com
MODEL_NAME=openai/gpt-4o-mini          # any OpenRouter-supported model

# Optional LangSmith tracing
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=turing-interview
```

### 3. Create `.env.local` at repo root (for local frontend)
```env
BACKEND_URL=http://localhost:8000
```

### 4. Run

Terminal 1 — backend:
```bash
cd backend
uv run uvicorn api:app --port 8000
```

Terminal 2 — frontend:
```bash
npm run dev
```

Open http://localhost:3000

### Alternative: CLI-only
```bash
cd backend
uv run python main.py
```

### Alternative: Run the multi-turn regression test
```bash
cd backend
uv run python test_multiturn.py
```
This script runs a 5-turn Apple → competitors → Tesla → follow-up conversation directly through the graph (no HTTP layer) and asserts the pronoun follow-up correctly resolves to the most recently discussed company.

---

## Multi-Turn Conversation and Memory

- `MemorySaver` stores the full LangGraph state per `thread_id`. The Next.js UI generates a UUID `thread_id` per browser session (fresh on `+ New Chat`).
- Every FastAPI request re-uses the same `thread_id`, so `MemorySaver` restores the checkpoint and merges the new `HumanMessage` via the `add_messages` reducer.
- Both Clarity and Research agents **receive the full formatted conversation** in their LLM prompts — not a single "current_company" variable. That means they handle:
  - implicit pronouns ("its CEO", "how old is this company")
  - company switches mid-conversation ("what about Tesla?" after Apple)
  - **recency** — "its products?" after mentioning Tesla resolves to Tesla, not to Apple even if Apple dominated earlier turns.

---

## Example Conversations

### Conversation 1 — vague query triggers interrupt, then multi-turn context resolves follow-ups
```
You: Tell me about a big tech company
[clarity]  →  INTERRUPT
Assistant (clarification): Which specific company are you asking about?
You (clarification reply): Apple
[clarity → research(★9) → synthesis]
Assistant: Apple Inc. has been making significant moves recently…

You: What about their main competitors?
[clarity → research(★8) → synthesis]
Assistant: Apple's main competitors include Samsung, Google, and Microsoft…

You: how is Tesla doing?
[clarity → research(★9) → synthesis]
Assistant: Tesla is currently navigating a challenging financial landscape…

You: its recent products?
[clarity → research(★8) → synthesis]     ← enriched query = "Tesla recent products"
Assistant: Tesla's recent product developments include Cybertruck deliveries ramping up, Model 3/Y price cuts, FSD v12 rollout…
```

### Conversation 2 — low confidence triggers validator loop
```
You: Tell me about Stripe
[clarity → research(★4) → validator(insufficient, attempt=1)
        → research(★7) → validator(sufficient) → synthesis]
Assistant: Stripe is a leading fintech company founded in 2010…
```

---

## Deployment

Both services are deployed and live at the URLs at the top of this file.

### Frontend on Vercel
1. Push repo to GitHub
2. Import at vercel.com — framework auto-detects Next.js at repo root
3. Add environment variable: `BACKEND_URL = https://<your-render-url>.onrender.com`
4. Deploy

### Backend on Render (no Docker needed)
1. New Web Service → connect the same GitHub repo
2. **Root Directory:** `backend`
3. **Build Command:** `pip install uv && uv sync`
4. **Start Command:** `uv run uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Environment variables: `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `MODEL_NAME`, `LANGCHAIN_API_KEY`, `LANGCHAIN_TRACING_V2`, `LANGCHAIN_PROJECT`

---

## Assumptions

- Company name matching in mock data uses case-insensitive substring search
- `research_attempts` resets to 0 at the start of each user turn
- When `interrupt` fires, the user's clarification reply is added as a `HumanMessage` to history so downstream agents see it as the actual query
- LLM `temperature=0` for deterministic routing decisions
- Tavily search fails gracefully if `TAVILY_API_KEY` is missing (falls back to mock data only)
- Validator loop caps at 3 attempts regardless of `validation_result` to prevent infinite loops
- `MemorySaver` is in-process memory — conversation state is lost if the backend restarts. For persistent state across restarts, swap for `SqliteSaver` or `PostgresSaver` (drop-in replacement).

---

## Beyond Expected Deliverable

Items marked **★** were not asked for but were added to showcase production readiness:

- **★ Live cloud deployment** — Frontend on Vercel, backend on Render, both wired up with environment variables and CORS. Try the demo link at the top.
- **★ Live web search via Tavily** — Research Agent queries the real web in addition to the mock data table.
- **★ FastAPI REST backend** — `api.py` exposes `/chat`, `/clarify`, `/health`, and `/debug/{thread_id}` endpoints so any client (web, mobile, curl) can drive the graph.
- **★ Modern Next.js chat UI** — Full React chat interface with typing indicators, suggested prompts, and an inline amber clarification card that appears when the interrupt fires.
- **★ Recency-aware context handling** — Both Clarity and Research agents receive the full formatted conversation. Pronouns resolve to the *most recently discussed* company, not the topically dominant one. This is verified by `backend/test_multiturn.py`.
- **★ Thread isolation** — Each browser session gets its own UUID `thread_id`, and clicking `+ New Chat` mints a new one so conversations don't leak across sessions.
- **★ OpenRouter integration** — Model-agnostic — set `MODEL_NAME` to swap between GPT-4o, Claude, Llama, etc.
- **★ LangSmith tracing** — All agent runs traced to the `turing-interview` project. Each turn shows the exact prompt, LLM output, and routing decision.
- **★ Multi-turn regression test** — `backend/test_multiturn.py` drives the graph directly (no HTTP) through a 5-turn Apple → Tesla scenario and asserts the recency behavior. Runnable in CI.
- **★ Graceful degradation** — Missing Tavily key falls back to mock data; missing LangSmith key just skips tracing; the graph never crashes on missing optional dependencies.
