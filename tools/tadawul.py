from __future__ import annotations
from datetime import datetime
from typing import Any
import yfinance as yf
from schemas.models import TadawulQuote
from tools.registry import Tool
ALIASES: dict[str, str] = {
    "aramco": "2222.SR",
    "saudi aramco": "2222.SR",
    "أرامكو": "2222.SR",
    "ارامكو": "2222.SR",
    "sabic": "2010.SR",
    "سابك": "2010.SR",
    "stc": "7010.SR",
    "الاتصالات السعودية": "7010.SR",
    "al rajhi": "1120.SR",
    "al rajhi bank": "1120.SR",
    "الراجحي": "1120.SR",
    "snb": "1180.SR",
    "saudi national bank": "1180.SR",
    "الأهلي": "1180.SR",
    "maaden": "1211.SR",
    "معادن": "1211.SR",
    "almarai": "2280.SR",
    "المراعي": "2280.SR",
    "riyad bank": "1010.SR",
    "بنك الرياض": "1010.SR",
    "alinma": "1150.SR",
    "alinma bank": "1150.SR",
    "الإنماء": "1150.SR",
    "الانماء": "1150.SR",
    "sabb": "1060.SR",
    "ساب": "1060.SR",
    "acwa power": "2082.SR",
    "أكوا باور": "2082.SR",
    "اكوا باور": "2082.SR",
    "mobily": "7020.SR",
    "موبايلي": "7020.SR",
    "bsf": "1050.SR",
    "banque saudi fransi": "1050.SR",
    "الفرنسي": "1050.SR",
    "anb": "1080.SR",
    "arab national bank": "1080.SR",
    "البنك العربي": "1080.SR",
    "savola": "2050.SR",
    "صافولا": "2050.SR",
    "sipchem": "2310.SR",
    "سبكيم": "2310.SR",
    "yansab": "2290.SR",
    "ينساب": "2290.SR",
    "sabic agri": "2020.SR",
    "سافكو": "2020.SR",
    "dar al arkan": "4300.SR",
    "دار الأركان": "4300.SR",
    "دار الاركان": "4300.SR",
    "albilad": "1140.SR",
    "bank albilad": "1140.SR",
    "بنك البلاد": "1140.SR",
    "bupa": "8210.SR",
    "bupa arabia": "8210.SR",
    "بوبا": "8210.SR",
    "tawuniya": "8010.SR",
    "التعاونية": "8010.SR",
    "jarir": "4190.SR",
    "jarir marketing": "4190.SR",
    "جرير": "4190.SR",
    "saudi electricity": "5110.SR",
    "sec": "5110.SR",
    "الكهرباء": "5110.SR",
    "الشركة السعودية للكهرباء": "5110.SR",
}
def _resolve_ticker(identifier: str) -> str:
    raw = identifier.strip().lower()
    if raw in ALIASES:
        return ALIASES[raw]
    if raw.isdigit() and len(raw) == 4:
        return f"{raw}.SR"
    if raw.endswith(".sr"):
        return raw.upper()
    return identifier
def tadawul_lookup(identifier: str) -> dict[str, Any]:
    ticker_str = _resolve_ticker(identifier)
    tk = yf.Ticker(ticker_str)
    info = tk.info or {}
    hist = tk.history(period="2d")
    if hist.empty and not info.get("regularMarketPrice"):
        return {
            "error": f"No market data found for {identifier!r} (resolved to {ticker_str}).",
            "hint": "Try a 4-digit Tadawul code (e.g. '2222') or English name.",
        }
    price = info.get("regularMarketPrice")
    if price is None and not hist.empty:
        price = float(hist["Close"].iloc[-1])
    change_pct = None
    if len(hist) >= 2:
        prev, curr = float(hist["Close"].iloc[-2]), float(hist["Close"].iloc[-1])
        if prev:
            change_pct = (curr - prev) / prev * 100
    quote = TadawulQuote(
        ticker=ticker_str.upper(),
        name=info.get("longName") or info.get("shortName") or ticker_str,
        price=float(price) if price is not None else 0.0,
        change_pct=change_pct,
        market_cap=info.get("marketCap"),
        pe_ratio=info.get("trailingPE"),
        as_of=datetime.utcnow(),
    )
    return quote.model_dump(mode="json")
TOOL = Tool(
    name="tadawul_lookup",
    description=(
        "Look up a live quote for a company listed on the Saudi Exchange (Tadawul). "
        "Accepts an English or Arabic company name (e.g. 'Aramco', 'سابك'), a "
        "4-digit Tadawul code (e.g. '2222'), or a yfinance ticker (e.g. '2222.SR'). "
        "Returns price, change %, market cap, and P/E where available."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "identifier": {
                "type": "string",
                "description": "Company name, Tadawul code, or ticker.",
            }
        },
        "required": ["identifier"],
    },
    handler=tadawul_lookup,
)