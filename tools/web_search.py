from __future__ import annotations
import os
from typing import Any
from tavily import TavilyClient
from schemas.models import WebSearchOutput, WebSearchResult
from tools.registry import Tool
def _client() -> TavilyClient:
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY not set. Get one free at https://tavily.com")
    return TavilyClient(api_key=key)
def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    resp = _client().search(
        query=query,
        max_results=max_results,
        include_answer=True,
        search_depth="advanced",
    )
    out = WebSearchOutput(
        query=query,
        answer=resp.get("answer"),
        results=[
            WebSearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", "")[:500],
                score=float(r.get("score", 0.0)),
            )
            for r in resp.get("results", [])
        ],
    )
    return out.model_dump(mode="json")
TOOL = Tool(
    name="web_search",
    description=(
        "Search the web for up-to-date information. Use this for any query "
        "about current events, company news, market data, regulatory changes, "
        "or anything not in your training data. Supports Arabic and English."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query. Be specific. Can be Arabic or English.",
            },
            "max_results": {
                "type": "integer",
                "description": "How many results to return (1-10).",
                "default": 5,
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["query"],
    },
    handler=web_search,
)