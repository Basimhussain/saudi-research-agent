from __future__ import annotations
from tools.registry import Tool
from tools.vat import vat_calc
from tools.tadawul import tadawul_lookup
from tools.sama import sama_rates


def finance(operation, **kwargs):
    op = (operation or "").strip().lower()
    if op == "vat":
        return vat_calc(
            amount=kwargs.get("amount"),
            direction=kwargs.get("direction", "add_vat"),
            rate=kwargs.get("rate", 0.15),
        )
    if op == "tadawul":
        ident = kwargs.get("identifier")
        if not ident:
            return {"error": "identifier is required for operation='tadawul'"}
        return tadawul_lookup(identifier=ident)
    if op == "sama":
        return sama_rates(query=kwargs.get("query", ""))
    return {"error": "unknown_operation", "message": f"operation must be vat|tadawul|sama, got {operation!r}"}


TOOL = Tool(
    name="finance_calc",
    description=(
        "Saudi finance calculations and lookups. Pick an operation:\n"
        "  vat      — ZATCA 15% VAT. args: amount, direction (add_vat|extract_vat), rate\n"
        "  tadawul  — live Saudi Exchange quote. args: identifier (name, 4-digit code, or ticker)\n"
        "  sama     — SAMA policy rates and USD/SAR peg. args: query (optional)"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["vat", "tadawul", "sama"]},
            "amount": {"type": "number", "description": "VAT: amount in SAR."},
            "direction": {"type": "string", "enum": ["add_vat", "extract_vat"]},
            "rate": {"type": "number", "description": "VAT rate (default 0.15)."},
            "identifier": {"type": "string", "description": "Tadawul identifier."},
            "query": {"type": "string", "description": "SAMA search term."},
        },
        "required": ["operation"],
    },
    handler=finance,
)
