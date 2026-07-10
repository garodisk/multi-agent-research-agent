from langchain_core.messages import HumanMessage

from ..llm import get_llm
from ..state import State

_PROMPT = """\
Evaluate whether this research sufficiently answers the user's query.

User Query: {query}
Research Findings: {findings}

Is the research SUFFICIENT (addresses the question with useful detail) or
INSUFFICIENT (missing key information or doesn't answer the question)?

Respond with ONLY one word: "sufficient" or "insufficient"."""


def validator_agent(state: State) -> dict:
    query = state["query"]
    findings = state.get("research_findings", "")
    attempts = state.get("research_attempts", 0) + 1

    response = get_llm().invoke(
        [HumanMessage(content=_PROMPT.format(query=query, findings=findings))]
    )
    verdict = response.content.strip().lower()
    result = "sufficient" if "sufficient" in verdict else "insufficient"

    return {
        "validation_result": result,
        "research_attempts": attempts,
    }
