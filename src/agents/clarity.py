from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from ..llm import get_llm
from ..state import State

_PROMPT = """\
Analyze this research query. Is it specific enough to research a particular company?

CLEAR: The query names a specific company (Apple, Tesla, Google, etc.) with understandable intent.
NEEDS_CLARIFICATION: No company is named, or the query is too vague to act on.

Query: {query}

Respond with ONLY one word: "clear" or "needs_clarification"."""


def clarity_agent(state: State) -> dict:
    query = state["query"]
    response = get_llm().invoke([HumanMessage(content=_PROMPT.format(query=query))])
    verdict = response.content.strip().lower()

    if "needs_clarification" in verdict:
        clarification = interrupt(
            "Your query is a bit vague — which specific company are you asking about?"
        )
        return {
            "query": clarification,
            "clarity_status": "clear",
            "messages": [HumanMessage(content=clarification)],
            "research_attempts": 0,
        }

    return {"clarity_status": "clear", "research_attempts": 0}
