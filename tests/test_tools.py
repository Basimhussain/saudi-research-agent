from __future__ import annotations
from tools.vat import vat_calc
from tools.report import generate_report
from tools.cr import cr_lookup
from tools.vision2030 import vision2030_align
from tools.finance import finance
from schemas.models import ResearchReport
def test_vat_add():
    r = vat_calc(amount=100, direction="add_vat")
    assert r["base_amount"] == 100
    assert r["vat_amount"] == 15.0
    assert r["total_amount"] == 115.0
def test_vat_extract():
    r = vat_calc(amount=115, direction="extract_vat")
    assert r["base_amount"] == 100.0
    assert r["vat_amount"] == 15.0
def test_vat_bad_direction():
    r = vat_calc(amount=100, direction="nonsense")
    assert "error" in r
def test_report_validation_ok():
    r = generate_report(
        query="test",
        language="en",
        summary="This is a test summary that is clearly longer than fifty characters to pass validation.",
        key_findings=["finding one"],
    )
    assert r["status"] == "ok"
    ResearchReport(**r["report"])
def test_report_validation_fails_short_summary():
    r = generate_report(
        query="test",
        language="en",
        summary="too short",
        key_findings=["x"],
    )
    assert r.get("error") == "validation_failed"
def test_report_validation_fails_bad_language():
    r = generate_report(
        query="test",
        language="fr",
        summary="This is a test summary that is clearly longer than fifty characters to pass validation.",
        key_findings=["finding one"],
    )
    assert r.get("error") == "validation_failed"


def test_cr_lookup_known():
    r = cr_lookup("1010000001")
    assert r["name_en"] == "Saudi Arabian Oil Company"
    assert r["status"] == "Active"
    assert "isic_codes" in r


def test_cr_lookup_unknown():
    r = cr_lookup("9999999999")
    assert r.get("error") == "not_found"


def test_cr_lookup_invalid_format():
    r = cr_lookup("abc")
    assert r.get("error") == "invalid_cr_number"


def test_vision2030_high_alignment_tourism():
    r = vision2030_align(
        business_activity="Luxury tourism resort and entertainment venue on the Red Sea",
        sector="Tourism",
    )
    assert r["alignment"] in {"high", "moderate"}
    assert r["pillar_matches"], "expected at least one pillar match"


def test_vision2030_flagship_match():
    r = vision2030_align(business_activity="solar and hydrogen renewable energy project")
    programs = [p["program"] for p in r["flagship_program_matches"]]
    assert "Saudi Green Initiative" in programs


def test_vision2030_low_alignment():
    r = vision2030_align(business_activity="asdfghjkl")
    assert r["alignment"] == "low"


def test_vision2030_missing_activity():
    r = vision2030_align(business_activity="")
    assert "error" in r


def test_finance_vat_dispatch():
    r = finance(operation="vat", amount=200, direction="add_vat")
    assert r["vat_amount"] == 30.0


def test_finance_sama_dispatch():
    r = finance(operation="sama")
    assert r["usd_sar_peg"] == 3.75


def test_finance_unknown_operation():
    r = finance(operation="bogus")
    assert r.get("error") == "unknown_operation"
