"""Direct test of multi-turn conversation memory without HTTP/UI."""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env", override=False)

from langchain_core.messages import HumanMessage
from src.graph import build_graph


def run_turn(graph, thread_id: str, message: str, turn: int) -> None:
    print(f"\n{'='*60}")
    print(f"TURN {turn}: {message!r}")
    print(f"{'='*60}")
    config = {"configurable": {"thread_id": thread_id}}
    input_ = {
        "messages": [HumanMessage(content=message)],
        "query": message,
        "research_attempts": 0,
    }
    agents = []
    for chunk in graph.stream(input_, config, stream_mode="updates"):
        for node, data in chunk.items():
            if node == "__interrupt__":
                print(f"  >>> INTERRUPT: {data}")
                continue
            agents.append(node)
            if node == "research" and isinstance(data, dict):
                print(f"  [research] confidence={data.get('confidence_score')}")
            if node == "validator" and isinstance(data, dict):
                print(f"  [validator] result={data.get('validation_result')}")
    state = graph.get_state(config)
    interrupted = any(t.interrupts for t in state.tasks)
    print(f"  agents: {' -> '.join(agents)}")
    print(f"  interrupted: {interrupted}")
    if not interrupted and state.values.get("messages"):
        answer = state.values["messages"][-1].content
        print(f"  ANSWER: {answer[:200]}...")


def main():
    graph = build_graph()
    thread = "test-thread-multiturn"

    run_turn(graph, thread, "What's happening with Apple?", 1)
    run_turn(graph, thread, "any new products released?", 2)
    run_turn(graph, thread, "who is the CEO?", 3)
    run_turn(graph, thread, "what about Tesla?", 4)
    run_turn(graph, thread, "how is it doing financially?", 5)


if __name__ == "__main__":
    main()
