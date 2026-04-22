from __future__ import annotations
from tools.registry import Tool

PILLARS = {
    "vibrant_society": {
        "title": "A Vibrant Society",
        "description": "Culture, entertainment, sports, Hajj/Umrah capacity, heritage.",
        "kpis": [
            "Triple annual Umrah visitors to 30 million",
            "Double UNESCO heritage sites",
            "Raise household spending on culture and entertainment",
        ],
        "keywords": [
            "culture", "tourism", "entertainment", "hajj", "umrah", "heritage",
            "sports", "museum", "hospitality", "hotel", "events", "religious",
            "pilgrimage", "media", "film",
        ],
    },
    "thriving_economy": {
        "title": "A Thriving Economy",
        "description": "Diversify away from oil — SMEs, FDI, logistics, mining, manufacturing, women in workforce.",
        "kpis": [
            "Non-oil government revenue SAR 1 trillion",
            "SME contribution to GDP at 35%",
            "Women's labor force participation at 30%",
            "FDI at 5.7% of GDP",
        ],
        "keywords": [
            "sme", "small business", "manufacturing", "mining", "logistics",
            "freight", "warehousing", "petrochemicals", "fintech", "technology",
            "startup", "fdi", "investment", "export", "employment", "women",
            "non-oil", "industry",
        ],
    },
    "ambitious_nation": {
        "title": "An Ambitious Nation",
        "description": "Government effectiveness, e-gov, transparency, non-profit sector growth.",
        "kpis": [
            "Raise Government Effectiveness Index ranking",
            "Non-profit share of GDP from <1% to 5%",
            "1 million volunteers per year",
        ],
        "keywords": [
            "government", "e-government", "digital services", "transparency",
            "governance", "regulation", "non-profit", "volunteering", "public sector",
        ],
    },
}

PROGRAMS = {
    "neom": {
        "name": "NEOM",
        "focus": "Cognitive cities, renewable energy, advanced manufacturing, tourism in Tabuk.",
        "keywords": ["neom", "tabuk", "the line", "oxagon", "trojena", "smart city"],
    },
    "red_sea": {
        "name": "Red Sea Project",
        "focus": "Regenerative luxury tourism on the west coast.",
        "keywords": ["red sea", "luxury tourism", "islands", "coastal"],
    },
    "qiddiya": {
        "name": "Qiddiya",
        "focus": "Entertainment, sports and culture megaproject south of Riyadh.",
        "keywords": ["qiddiya", "entertainment city", "theme park", "motorsport"],
    },
    "roshn": {
        "name": "ROSHN",
        "focus": "Large residential communities to raise home ownership.",
        "keywords": ["roshn", "housing", "home ownership", "residential community"],
    },
    "green_initiative": {
        "name": "Saudi Green Initiative",
        "focus": "Net zero by 2060, 50% renewable electricity by 2030, reforestation.",
        "keywords": [
            "renewable", "solar", "wind", "hydrogen", "net zero", "carbon",
            "green", "sustainability", "esg", "reforestation",
        ],
    },
    "fsdp": {
        "name": "Financial Sector Development Program",
        "focus": "Capital markets depth, fintech growth, cashless payments.",
        "keywords": [
            "fintech", "capital markets", "banking", "payments", "cashless",
            "insurance", "tadawul", "sukuk",
        ],
    },
    "nidlp": {
        "name": "National Industrial Development & Logistics Program",
        "focus": "Industry, mining, energy, logistics — KSA as a global logistics hub.",
        "keywords": [
            "logistics", "industrial", "manufacturing", "mining", "energy",
            "supply chain", "ports", "shipping", "freight",
        ],
    },
    "hcdp": {
        "name": "Human Capability Development Program",
        "focus": "Education reform, upskilling Saudi workforce.",
        "keywords": ["education", "training", "upskilling", "workforce", "talent", "university", "vocational"],
    },
}


def _hits(text, keywords):
    matched = [k for k in keywords if k in text]
    return len(matched), matched


def vision2030_align(business_activity, sector=None):
    if not business_activity or not business_activity.strip():
        return {"error": "business_activity is required"}

    text = f"{business_activity} {sector or ''}".lower()

    pillars = []
    for p in PILLARS.values():
        score, matched = _hits(text, p["keywords"])
        if score:
            pillars.append({
                "pillar": p["title"],
                "description": p["description"],
                "match_score": score,
                "matched_keywords": matched,
                "relevant_kpis": p["kpis"],
            })
    pillars.sort(key=lambda x: x["match_score"], reverse=True)

    programs = []
    for prog in PROGRAMS.values():
        score, matched = _hits(text, prog["keywords"])
        if score:
            programs.append({
                "program": prog["name"],
                "focus": prog["focus"],
                "match_score": score,
                "matched_keywords": matched,
            })
    programs.sort(key=lambda x: x["match_score"], reverse=True)

    if not pillars and not programs:
        alignment = "low"
        rationale = "No Vision 2030 keyword overlap. Reframe around non-oil growth, localization, sustainability, tourism, or digital transformation."
    elif pillars and pillars[0]["match_score"] >= 3:
        alignment = "high"
        rationale = f"Strong fit with the '{pillars[0]['pillar']}' pillar."
    else:
        alignment = "moderate"
        rationale = "Partial fit — see matched keywords."

    return {
        "business_activity": business_activity,
        "sector": sector,
        "alignment": alignment,
        "rationale": rationale,
        "pillar_matches": pillars,
        "flagship_program_matches": programs,
        "source": "Vision 2030 public docs (local knowledge base).",
    }


TOOL = Tool(
    name="vision2030_align",
    description=(
        "Score a business activity or sector against Saudi Vision 2030. "
        "Returns matched pillars (Vibrant Society, Thriving Economy, Ambitious "
        "Nation), relevant KPIs, and matched flagship programs (NEOM, Red Sea, "
        "Qiddiya, ROSHN, Saudi Green Initiative, FSDP, NIDLP, HCDP)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "business_activity": {"type": "string", "description": "e.g. 'solar farm operator'."},
            "sector": {"type": "string", "description": "e.g. 'Energy', 'Tourism'."},
        },
        "required": ["business_activity"],
    },
    handler=vision2030_align,
)
