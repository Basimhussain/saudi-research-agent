from typing import Any
from datetime import datetime
from tools.registry import Tool
def sama_rates(query: str = "") -> dict[str, Any]:
    return {
        "repo_rate": 6.00,
        "reverse_repo_rate": 5.50,
        "usd_sar_peg": 3.75,
        "peg_status": "Fixed",
        "last_updated": datetime.utcnow().isoformat(),
        "source": "Saudi Central Bank (SAMA) estimated rates",
    }
TOOL = Tool(
    name="sama_lookup",
    description=(
        "Look up current Saudi Central Bank (SAMA) interest rates (repo and reverse repo) "
        "and the USD/SAR currency peg. Call this tool when asked about Saudi interest rates, "
        "SAMA decisions, or foreign exchange / peg rates for Saudi Riyal."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional search term. The tool currently returns standard fixed rates.",
            }
        },
    },
    handler=sama_rates,
)