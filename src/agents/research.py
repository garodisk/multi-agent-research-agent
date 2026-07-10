import os

from langchain_core.messages import HumanMessage
from tavily import TavilyClient

from ..data import lookup_company
from ..llm import get_llm
from ..state import State

_SYNTHESIZE_PROMPT = """\
You are a research analyst. Synthesize the information below to answer the user's query.

User Query: {query}
Search Results: {search_results}
Mock Data (if available): {mock_data}

Provide a clear, factual research summary that directly addresses the query.
Then rate your confidence (0-10) based on how completely the data answers it.

Format exactly as:
FINDINGS: <your research summary>
CONFIDENCE: <integer 0-10>"""


def research_agent(state: State) -> dict:
    query = state["query"]

    search_results = _tavily_search(query)
    mock_data = lookup_company(query)

    prompt = _SYNTHESIZE_PROMPT.format(
        query=query,
        search_results=search_results or "No search results available.",
        mock_data=mock_data or "No mock data available.",
    )

    response = get_llm().invoke([HumanMessage(content=prompt)])
    findings, confidence = _parse_response(response.content)

    return {
        "research_findings": findings,
        "confidence_score": confidence,
    }


def _tavily_search(query: str) -> str | None:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None
    try:
        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=f"{query} company news financials",
            max_results=4,
            search_depth="basic",
        )
        items = results.get("results", [])
        return "\n\n".join(
            f"[{r['title']}]\n{r['content']}" for r in items if r.get("content")
        )
    except Exception:
        return None


def _parse_response(content: str) -> tuple[str, int]:
    confidence = 5
    findings = content

    if "CONFIDENCE:" in content:
        conf_start = content.index("CONFIDENCE:") + len("CONFIDENCE:")
        try:
            confidence = max(0, min(10, int(content[conf_start:].strip().split()[0])))
        except (ValueError, IndexError):
            confidence = 5
        findings_section = content[: content.index("CONFIDENCE:")].strip()
    else:
        findings_section = content

    if "FINDINGS:" in findings_section:
        findings = findings_section[findings_section.index("FINDINGS:") + len("FINDINGS:"):].strip()

    return findings, confidence
