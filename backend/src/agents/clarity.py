from langchain_core.messages import HumanMessage, AIMessage

from langgraph.types import interrupt

from ..llm import get_llm
from ..state import State

_PROMPT = """\
You are the CLARITY agent for a company research assistant.
Decide if the user's CURRENT query can be researched, or if it is too vague to act on.

FULL CONVERSATION HISTORY:
{conversation}

CURRENT USER QUERY: {query}

Rules — respond "clear" if ANY of these is true:
- The current query explicitly names a specific company or organization
- The conversation history above mentions a specific company, AND the current query is a follow-up \
(uses "it", "its", "they", "their", "this", "the company", or asks about products/CEO/stock/history/employees/anything researchable)

Respond "needs_clarification" ONLY if NO company appears anywhere in the conversation history \
AND the current query does not name one either.

Respond with ONLY one word: "clear" or "needs_clarification"."""


def _format_conversation(messages: list) -> str:
    lines = []
    # Exclude the current (last) HumanMessage — it's the query itself
    for msg in messages[:-1]:
        if isinstance(msg, HumanMessage):
            lines.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            lines.append(f"Assistant: {msg.content[:250]}")
    if not lines:
        return "(no prior conversation — this is the first message)"
    return "\n".join(lines[-8:])


def clarity_agent(state: State) -> dict:
    query = state["query"]
    messages = state.get("messages", [])

    conversation = _format_conversation(messages)
    prompt = _PROMPT.format(conversation=conversation, query=query)
    verdict = get_llm().invoke([HumanMessage(content=prompt)]).content.strip().lower()

    print(f"[clarity] query={query!r} history_len={len(messages)} verdict={verdict!r}")

    if "needs_clarification" in verdict:
        clarification = interrupt("Which specific company are you asking about?")
        return {
            "query": clarification,
            "clarity_status": "clear",
            "messages": [HumanMessage(content=clarification)],
            "research_attempts": 0,
        }

    return {"clarity_status": "clear", "research_attempts": 0}
