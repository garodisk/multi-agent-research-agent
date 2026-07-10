from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import interrupt

from ..llm import get_llm
from ..state import State

_PROMPT = """\
You are deciding whether a research query is clear enough to act on.

{history_section}Current query: {query}

Rules (apply in order):
1. If the conversation history above mentions ANY specific company, and the current query uses pronouns or implicit references \
("this", "it", "its", "their", "they", "the company", "how old", "tell me more", "what about", etc.) — respond "clear". \
The company is already established by context.
2. If the query explicitly names a specific company — respond "clear".
3. Only respond "needs_clarification" if there is NO conversation history AND no company can be inferred from the query itself.

Respond with ONLY one word: "clear" or "needs_clarification"."""


def clarity_agent(state: State) -> dict:
    query = state["query"]
    messages = state.get("messages", [])

    # Build a short history string from prior turns for context
    history_lines = []
    for msg in messages[:-1]:  # exclude the current message
        if isinstance(msg, HumanMessage):
            history_lines.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            history_lines.append(f"Assistant: {msg.content[:120]}...")

    history_section = ""
    if history_lines:
        history_section = "Conversation history:\n" + "\n".join(history_lines[-6:]) + "\n\n"

    prompt = _PROMPT.format(history_section=history_section, query=query)
    response = get_llm().invoke([HumanMessage(content=prompt)])
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
