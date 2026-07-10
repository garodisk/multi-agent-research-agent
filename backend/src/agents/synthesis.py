from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..llm import get_llm
from ..state import State

_SYSTEM = (
    "You are a helpful research assistant that provides clear, accurate information about companies. "
    "Answer the user's most recent question using the provided research findings. "
    "The findings are already focused on the correct company for this question — trust them "
    "over any earlier conversation topics."
)

_PROMPT = """\
Answer the user's most recent question using ONLY the research findings below.
Do not describe a different company just because it was discussed earlier.

User's current question: {query}

Research findings (already scoped to the correct company for this question):
{findings}

Write a helpful, well-structured response based on these findings."""


def synthesis_agent(state: State) -> dict:
    query = state["query"]
    findings = state.get("research_findings", "No findings available.")

    response = get_llm().invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=_PROMPT.format(query=query, findings=findings)),
    ])
    return {"messages": [AIMessage(content=response.content)]}
