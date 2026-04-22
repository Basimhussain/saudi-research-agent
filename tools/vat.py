from __future__ import annotations
from typing import Any
from schemas.models import VATCalculation
from tools.registry import Tool
DEFAULT_RATE = 0.15
def vat_calc(amount: float, direction: str = "add_vat", rate: float = DEFAULT_RATE) -> dict[str, Any]:
    if direction not in {"add_vat", "extract_vat"}:
        return {"error": f"direction must be 'add_vat' or 'extract_vat', got {direction!r}"}
    if amount < 0:
        return {"error": "amount must be non-negative"}
    if not 0 <= rate <= 1:
        return {"error": "rate must be between 0 and 1 (e.g. 0.15 for 15%)"}
    if direction == "add_vat":
        base = amount
        vat = round(base * rate, 2)
        total = round(base + vat, 2)
    else:  
        total = amount
        base = round(total / (1 + rate), 2)
        vat = round(total - base, 2)
    result = VATCalculation(
        base_amount=base,
        vat_rate=rate,
        vat_amount=vat,
        total_amount=total,
        direction=direction,  
    )
    return result.model_dump(mode="json")
TOOL = Tool(
    name="vat_calc",
    description=(
        "Calculate Saudi Arabia VAT (ZATCA). Standard rate is 15%. "
        "Use direction='add_vat' to add VAT to a net amount, or "
        "direction='extract_vat' to back out VAT from a VAT-inclusive total."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Amount in SAR."},
            "direction": {
                "type": "string",
                "enum": ["add_vat", "extract_vat"],
                "default": "add_vat",
            },
            "rate": {
                "type": "number",
                "description": "VAT rate as a decimal. Defaults to 0.15.",
                "default": 0.15,
            },
        },
        "required": ["amount"],
    },
    handler=vat_calc,
)