from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    current_company: str
    clarity_status: Literal["clear", "needs_clarification"]
    research_findings: str
    confidence_score: int
    validation_result: Literal["sufficient", "insufficient"]
    research_attempts: int
