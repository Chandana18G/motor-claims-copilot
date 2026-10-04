"""Rule engine checked against cases worked out by hand from the policy wording.

The expected numbers are written out explicitly (not computed with the engine's formula), so
these tests catch a wrong formula, not just an inconsistent one.

Policy facts used: BASIC excess 500 EUR, cap 15,000; COMFORT excess 300, cap 30,000;
PREMIUM excess 150, cap 60,000; medical limit 5,000 per person (6.1); late notification after
30 days (5.1); supervisor review above 10,000 EUR (GL-1).
"""

from datetime import date

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from copilot.extraction import Extracted
from copilot.rules import evaluate


def ex(policy="BASIC", estimate=2_000.0, value=8_000.0, licensed=True, alcohol=False,
       business=False, medical=None):
    return Extracted(claim_id="C00001", policy_id=policy, incident_date=date(2025, 5, 1),
                     repair_estimate=estimate, form_estimate=estimate, vehicle_value=value,
                     driver_licensed=licensed, alcohol_positive=alcohol, commercial_use=business,
                     medical_amount=medical)


GOLDEN = [
    # id, extracted, days, fraud, recommendation, payable damage, payable medical, clauses, escalate
    ("simple", ex(), 3, False, "approve", 1_500.00, 0, {"BASIC-2.1"}, False),
    ("below excess", ex(estimate=400.0), 3, False, "approve", 0.00, 0, {"BASIC-2.1"}, False),
    ("capped at value", ex("COMFORT", 12_000.0, 9_000.0), 3, False, "approve", 8_700.00, 0,
     {"COMFORT-2.1", "COMFORT-2.2", "GL-1"}, True),
    ("capped at policy max", ex("PREMIUM", 70_000.0, 80_000.0), 3, False, "approve", 59_850.00, 0,
     {"PREMIUM-2.1", "PREMIUM-2.2", "GL-1"}, True),
    ("unlicensed", ex(licensed=False), 3, False, "deny", 0.00, 0, {"BASIC-4.1"}, False),
    ("alcohol", ex("COMFORT", alcohol=True), 3, False, "deny", 0.00, 0, {"COMFORT-4.2"}, False),
    ("business use", ex("PREMIUM", business=True), 3, False, "deny", 0.00, 0, {"PREMIUM-4.3"}, False),
    ("late", ex("COMFORT", 3_000.0), 45, False, "request_information", 2_700.00, 0,
     {"COMFORT-2.1", "COMFORT-5.1"}, False),
    ("exactly 30 days is on time", ex(), 30, False, "approve", 1_500.00, 0, {"BASIC-2.1"}, False),
    ("medical over limit", ex("COMFORT", 1_000.0, medical=7_200.0), 3, False, "approve", 700.00, 5_000.00,
     {"COMFORT-2.1", "COMFORT-6.1"}, False),
    ("medical under limit", ex("PREMIUM", 1_000.0, medical=1_234.50), 3, False, "approve", 850.00, 1_234.50,
     {"PREMIUM-2.1", "PREMIUM-6.1"}, False),
    ("exactly 10,000 is not escalated", ex("COMFORT", 10_000.0, 20_000.0), 3, False, "approve", 9_700.00, 0,
     {"COMFORT-2.1"}, False),
    ("fraud flag escalates but does not decide", ex(), 3, True, "approve", 1_500.00, 0,
     {"BASIC-2.1", "GL-2"}, True),
    ("unknown policy", ex("GOLD"), 3, False, "request_information", 0.00, 0, {"GL-3"}, False),
]


@pytest.mark.parametrize("case", GOLDEN, ids=[g[0] for g in GOLDEN])
def test_golden(case):
    _, e, days, fraud, rec, damage, medical, clauses, escalate = case
    out = evaluate(e, days, fraud)
    assert out.recommendation == rec
    assert out.payable_damage == pytest.approx(damage)
    assert out.payable_medical == pytest.approx(medical)
    assert {b.clause_id for b in out.bases} == clauses
    assert out.escalate == escalate


money = st.floats(min_value=0, max_value=200_000, allow_nan=False).map(lambda v: round(v, 2))


@settings(max_examples=300, deadline=None)
@given(policy=st.sampled_from(["BASIC", "COMFORT", "PREMIUM"]), estimate=money, value=money,
       licensed=st.booleans(), alcohol=st.booleans(), business=st.booleans())
def test_properties(policy, estimate, value, licensed, alcohol, business):
    out = evaluate(ex(policy, estimate, value or None, licensed, alcohol, business), 3, False)
    excluded = (not licensed) or alcohol or business
    assert (out.recommendation == "deny") == excluded
    assert 0 <= out.payable_damage <= estimate
    if excluded:
        assert out.payable_damage == 0


@settings(max_examples=200, deadline=None)
@given(policy=st.sampled_from(["BASIC", "COMFORT", "PREMIUM"]), a=money, b=money, value=money)
def test_payout_never_falls_when_estimate_rises(policy, a, b, value):
    lo, hi = sorted((a, b))
    assert evaluate(ex(policy, lo, value or None), 3, False).payable_damage <= \
        evaluate(ex(policy, hi, value or None), 3, False).payable_damage
