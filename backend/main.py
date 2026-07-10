import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env", override=False)
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.graph import build_graph

load_dotenv()

THREAD_ID = "research-session"


def _get_interrupt(graph, config) -> str | None:
    state = graph.get_state(config)
    if not state.next:
        return None
    for task in state.tasks:
        if task.interrupts:
            return task.interrupts[0].value
    return None


def _run_turn(graph, input_, config) -> None:
    for chunk in graph.stream(input_, config, stream_mode="updates"):
        for node_name in chunk:
            if node_name != "__interrupt__":
                print(f"  [{node_name}]", flush=True)

    interrupt_msg = _get_interrupt(graph, config)
    if interrupt_msg:
        print(f"\nAssistant: {interrupt_msg}")
        clarification = input("You: ").strip()
        _run_turn(graph, Command(resume=clarification), config)
    else:
        state = graph.get_state(config)
        messages = state.values.get("messages", [])
        if messages:
            print(f"\nAssistant: {messages[-1].content}\n")


def main() -> None:
    graph = build_graph()
    config = {"configurable": {"thread_id": THREAD_ID}}

    print("Research Assistant (try asking about Apple or Tesla)")
    print("Type 'quit' to exit\n")

    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            break

        state_update = {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "research_attempts": 0,
        }
        _run_turn(graph, state_update, config)


if __name__ == "__main__":
    main()
