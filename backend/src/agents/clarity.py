from langchain_core.messages import HumanMessage

from langgraph.types import interrupt

from ..llm import get_llm
from ..state import State

_EXTRACT_PROMPT = """\
Does this query explicitly name a specific company?

Query: {query}

Reply with ONLY the company name if one is explicitly mentioned (e.g. "Tesla", "Apple", "Google").
Reply with ONLY the word "none" if no company is named in the query."""


def clarity_agent(state: State) -> dict:
    query = state["query"]
    current_company = state.get("current_company", "")

    response = get_llm().invoke([HumanMessage(content=_EXTRACT_PROMPT.format(query=query))])
    named = response.content.strip()

    if named.lower() != "none" and named:
        # User named a company — use it (handles new company replacing old)
        return {"clarity_status": "clear", "current_company": named, "research_attempts": 0}

    if current_company:
        # No new company named but one is already established — continue with it
        return {"clarity_status": "clear", "research_attempts": 0}

    # No company anywhere — ask
    clarification = interrupt(
        "Which specific company are you asking about?"
    )
    return {
        "query": clarification,
        "clarity_status": "clear",
        "current_company": clarification,
        "messages": [HumanMessage(content=clarification)],
        "research_attempts": 0,
    }
