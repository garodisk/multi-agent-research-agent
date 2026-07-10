from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..llm import get_llm
from ..state import State

_SYSTEM = (
    "You are a helpful research assistant. You have access to the prior conversation for "
    "continuity, so you may naturally reference earlier discussion (e.g. 'as mentioned above'). "
    "IMPORTANT: When answering the user's CURRENT question, always use the research findings "
    "provided in the final user message — those findings are already scoped to the specific "
    "company the current question is about. Do not describe a different company just because "
    "it was discussed at length earlier in the conversation."
)

_PROMPT = """\
Answer this question using the research findings below.

Current question: {query}

Research findings (already scoped to the correct company for this question):
{findings}

Write a helpful, well-structured response based on these findings. You may reference the earlier
conversation for continuity, but the findings above are the source of truth for the current answer."""


def synthesis_agent(state: State) -> dict:
    query = state["query"]
    findings = state.get("research_findings", "No findings available.")
    history = state.get("messages", [])

    llm_messages: list = [SystemMessage(content=_SYSTEM)]
    # Include prior conversation turns (exclude current HumanMessage — we frame it below)
    for msg in history[:-1]:
        llm_messages.append(msg)
    llm_messages.append(HumanMessage(content=_PROMPT.format(query=query, findings=findings)))

    response = get_llm().invoke(llm_messages)
    return {"messages": [AIMessage(content=response.content)]}
