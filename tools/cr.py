from __future__ import annotations
from datetime import datetime
from tools.registry import Tool

_RECORDS = {
    "1010000001": {
        "cr_number": "1010000001",
        "name_en": "Saudi Arabian Oil Company",
        "name_ar": "شركة الزيت العربية السعودية",
        "legal_form": "Joint Stock Company",
        "city": "Dhahran",
        "region": "Eastern Province",
        "status": "Active",
        "issue_date": "1988-11-13",
        "expiry_date": "2028-11-12",
        "capital_sar": 60000000000,
        "activities": ["Crude petroleum extraction", "Refining", "Petrochemicals"],
        "isic_codes": ["0610", "1920", "2011"],
    },
    "1010000002": {
        "cr_number": "1010000002",
        "name_en": "Saudi Basic Industries Corporation",
        "name_ar": "الشركة السعودية للصناعات الأساسية",
        "legal_form": "Joint Stock Company",
        "city": "Riyadh",
        "region": "Riyadh",
        "status": "Active",
        "issue_date": "1976-09-06",
        "expiry_date": "2030-09-05",
        "capital_sar": 30000000000,
        "activities": ["Petrochemicals", "Fertilizers", "Metals"],
        "isic_codes": ["2011", "2012", "2410"],
    },
    "4030000003": {
        "cr_number": "4030000003",
        "name_en": "Jeddah Logistics Company",
        "name_ar": "شركة جدة للخدمات اللوجستية",
        "legal_form": "Limited Liability Company",
        "city": "Jeddah",
        "region": "Makkah",
        "status": "Active",
        "issue_date": "2012-04-18",
        "expiry_date": "2027-04-17",
        "capital_sar": 5000000,
        "activities": ["Freight forwarding", "Warehousing", "Customs clearance"],
        "isic_codes": ["5210", "5229"],
    },
    "2050000099": {
        "cr_number": "2050000099",
        "name_en": "Dammam Marine Services",
        "name_ar": "شركة الدمام للخدمات البحرية",
        "legal_form": "Limited Liability Company",
        "city": "Dammam",
        "region": "Eastern Province",
        "status": "Suspended",
        "issue_date": "2005-07-22",
        "expiry_date": "2024-07-21",
        "capital_sar": 2000000,
        "activities": ["Marine support services"],
        "isic_codes": ["5222"],
    },
}


def cr_lookup(cr_number):
    n = str(cr_number).strip()
    if not n.isdigit() or len(n) != 10:
        return {"error": "invalid_cr_number", "message": "CR number must be 10 digits."}
    rec = _RECORDS.get(n)
    if not rec:
        return {
            "error": "not_found",
            "cr_number": n,
            "message": f"No record for CR {n}.",
            "hint": "Try 1010000001, 1010000002, 4030000003, or 2050000099.",
        }
    return {**rec, "source": "MoC CR registry (offline fixture)", "as_of": datetime.utcnow().isoformat()}


TOOL = Tool(
    name="cr_lookup",
    description=(
        "Look up a Saudi Commercial Registration by its 10-digit CR number. "
        "Returns Arabic/English legal name, legal form, city, status, issue "
        "and expiry dates, paid-up capital, and licensed activities."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "cr_number": {"type": "string", "description": "10-digit CR number."},
        },
        "required": ["cr_number"],
    },
    handler=cr_lookup,
)
