"""Direct test of multi-turn conversation memory without HTTP/UI.

Covers the tricky case where Apple dominates history and Tesla is
mentioned briefly — a pronoun follow-up should refer to Tesla.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env", override=False)

from langchain_core.messages import HumanMessage
from src.graph import build_graph


def run_turn(graph, thread_id: str, message: str, turn: int) -> str:
    print(f"\n{'='*60}\nTURN {turn}: {message!r}\n{'='*60}")
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
                continue
            agents.append(node)
    state = graph.get_state(config)
    print(f"  agents: {' -> '.join(agents)}")
    if state.values.get("messages"):
        answer = state.values["messages"][-1].content
        print(f"  ANSWER: {answer[:250]}...")
        return answer
    return ""


def main():
    graph = build_graph()
    thread = "test-recency"

    run_turn(graph, thread, "What's happening with Apple?", 1)
    run_turn(graph, thread, "what are their competitors and products?", 2)
    run_turn(graph, thread, "which is the strongest?", 3)
    run_turn(graph, thread, "how is tesla doing?", 4)
    answer = run_turn(graph, thread, "its recent products?", 5)

    print("\n" + "="*60)
    print("VERDICT")
    print("="*60)
    lower = answer.lower()
    if "tesla" in lower and lower.count("tesla") > lower.count("apple"):
        print("PASS: Turn 5 correctly answered about Tesla, not Apple")
    else:
        print("FAIL: Turn 5 got confused — answered about wrong company")
        print(f"  tesla mentions={lower.count('tesla')}, apple mentions={lower.count('apple')}")


if __name__ == "__main__":
    main()
