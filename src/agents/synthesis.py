from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..llm import get_llm
from ..state import State

_SYSTEM = (
    "You are a helpful research assistant that provides clear, accurate information "
    "about companies. Use the conversation history to handle follow-up questions naturally."
)

_PROMPT = """\
Research findings for the user's query:

Query: {query}
Findings: {findings}

Provide a helpful, well-structured response. If findings are limited, acknowledge it.
For follow-up questions, reference earlier context from the conversation."""


def synthesis_agent(state: State) -> dict:
    query = state["query"]
    findings = state.get("research_findings", "No findings available.")
    history = state.get("messages", [])

    llm_messages = [SystemMessage(content=_SYSTEM)]
    # Include prior conversation turns for context (exclude the current HumanMessage)
    for msg in history[:-1]:
        llm_messages.append(msg)
    llm_messages.append(HumanMessage(content=_PROMPT.format(query=query, findings=findings)))

    response = get_llm().invoke(llm_messages)
    return {"messages": [AIMessage(content=response.content)]}
