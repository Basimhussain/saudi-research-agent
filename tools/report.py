from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from schemas.models import ResearchReport
from tools.registry import Tool
def generate_report(**kwargs: Any) -> dict[str, Any]:
    try:
        report = ResearchReport(**kwargs)
    except ValidationError as e:
        return {"error": "validation_failed", "details": e.errors()}
    return {"status": "ok", "report": report.model_dump(mode="json")}
TOOL = Tool(
    name="generate_report",
    description=(
        "Emit the final research report in a validated structured format. "
        "Call this exactly once, at the end, when you have gathered enough "
        "information to answer the user's question. If validation fails, "
        "fix the fields and call again."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The original user question."},
            "language": {
                "type": "string",
                "enum": ["ar", "en"],
                "description": "Language of the report, matching the user's query.",
            },
            "summary": {
                "type": "string",
                "description": "2-4 sentence executive summary. Minimum 50 characters.",
            },
            "key_findings": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Bullet-style key findings. At least one.",
            },
            "figures": {
                "type": "object",
                "description": "Named numeric/textual figures, e.g. {'Aramco PE': '15.2'}.",
                "additionalProperties": {"type": "string"},
            },
            "citations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "url": {"type": "string"},
                        "note": {"type": "string"},
                    },
                    "required": ["source"],
                },
            },
            "caveats": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Limitations, data freshness notes, uncertainty.",
            },
        },
        "required": ["query", "language", "summary", "key_findings"],
    },
    handler=generate_report,
)