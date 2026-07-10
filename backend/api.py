import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ensure src/ is importable when running from any directory
sys.path.insert(0, str(Path(__file__).parent))
# find .env in backend/ or parent directory
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env", override=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.graph import build_graph

app = FastAPI(title="Multi-Agent Research API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ClarifyRequest(BaseModel):
    clarification: str
    thread_id: str = "default"


def _execute(input_, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    agents_run: list[dict] = []

    for chunk in graph.stream(input_, config, stream_mode="updates"):
        for node_name, node_data in chunk.items():
            if node_name == "__interrupt__":
                continue
            step: dict = {"agent": node_name}
            if node_name == "research" and isinstance(node_data, dict):
                step["confidence"] = node_data.get("confidence_score", 0)
            if node_name == "validator" and isinstance(node_data, dict):
                step["result"] = node_data.get("validation_result", "")
                step["attempts"] = node_data.get("research_attempts", 0)
            agents_run.append(step)

    state = graph.get_state(config)

    for task in state.tasks:
        if task.interrupts:
            return {
                "type": "clarification_needed",
                "prompt": task.interrupts[0].value,
                "agents_run": agents_run,
            }

    values = state.values
    messages = values.get("messages", [])
    content = messages[-1].content if messages else ""

    return {"type": "response", "content": content, "trace": agents_run}


@app.post("/chat")
async def chat(req: ChatRequest):
    state_update = {
        "messages": [HumanMessage(content=req.message)],
        "query": req.message,
        "current_company": "",
        "research_attempts": 0,
    }
    return _execute(state_update, req.thread_id)


@app.post("/clarify")
async def clarify(req: ClarifyRequest):
    return _execute(Command(resume=req.clarification), req.thread_id)


@app.get("/health")
async def health():
    return {"status": "ok", "model": os.getenv("MODEL_NAME", "openai/gpt-4o-mini")}


@app.get("/debug/{thread_id}")
async def debug_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    msgs = [{"type": type(m).__name__, "content": m.content[:100]} for m in state.values.get("messages", [])]
    return {"message_count": len(msgs), "messages": msgs, "next": list(state.next)}
