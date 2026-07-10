from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .agents.clarity import clarity_agent
from .agents.research import research_agent
from .agents.synthesis import synthesis_agent
from .agents.validator import validator_agent
from .state import State


def _route_research(state: State) -> str:
    return "synthesis" if state.get("confidence_score", 0) >= 6 else "validator"


def _route_validator(state: State) -> str:
    if state.get("validation_result") == "sufficient" or state.get("research_attempts", 0) >= 3:
        return "synthesis"
    return "research"


def build_graph():
    builder = StateGraph(State)

    builder.add_node("clarity", clarity_agent)
    builder.add_node("research", research_agent)
    builder.add_node("validator", validator_agent)
    builder.add_node("synthesis", synthesis_agent)

    builder.add_edge(START, "clarity")
    builder.add_edge("clarity", "research")
    builder.add_conditional_edges("research", _route_research)
    builder.add_conditional_edges("validator", _route_validator)
    builder.add_edge("synthesis", END)

    return builder.compile(checkpointer=MemorySaver())
