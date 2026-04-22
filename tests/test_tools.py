from __future__ import annotations
from tools.vat import vat_calc
from tools.report import generate_report
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