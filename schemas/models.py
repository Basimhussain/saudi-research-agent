from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    score: float = Field(ge=0.0, le=1.0)
class WebSearchOutput(BaseModel):
    query: str
    results: list[WebSearchResult]
    answer: str | None = None  
class TadawulQuote(BaseModel):
    ticker: str  
    name: str
    currency: str = "SAR"
    price: float
    change_pct: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    as_of: datetime
class VATCalculation(BaseModel):
    base_amount: float
    vat_rate: float = 0.15  
    vat_amount: float
    total_amount: float
    direction: Literal["add_vat", "extract_vat"]
    currency: str = "SAR"
class Citation(BaseModel):
    source: str
    url: str | None = None
    note: str | None = None
class ResearchReport(BaseModel):
    query: str
    language: Literal["ar", "en"]
    summary: str = Field(min_length=50)
    key_findings: list[str] = Field(min_length=1)
    figures: dict[str, str] = Field(default_factory=dict)  
    citations: list[Citation] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)