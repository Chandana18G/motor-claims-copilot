"""Deterministic rule engine for the parts of a claim that must be exact.

Coverage exclusions, excess, settlement limits and escalation thresholds are computed by code,
never generated. Each outcome carries the clause it rests on so the draft can cite it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from copilot.access import Sensitivity
from copilot.extraction import Extracted
from copilot.policies import POLICIES

HIGH_VALUE_THRESHOLD = 10_000.0
LATE_NOTIFICATION_DAYS = 30
MEDICAL_LIMIT = 5_000.0


@dataclass
class Basis:
    clause_id: str
    finding: str
    label: Sensitivity = Sensitivity.INTERNAL


@dataclass
class RuleOutcome:
    recommendation: str  # approve | deny | request_information (a recommendation only)
    payable_damage: float = 0.0
    payable_medical: float = 0.0
    bases: list[Basis] = field(default_factory=list)
    escalate: bool = False
    escalation_reasons: list[str] = field(default_factory=list)


def evaluate(ex: Extracted, days_to_report: int | None, fraud_flag: bool) -> RuleOutcome:
    policy = POLICIES[ex.policy_id] if ex.policy_id in POLICIES else None
    if policy is None:
        return RuleOutcome("request_information", bases=[Basis("GL-3", "Policy number could not be matched")])
    pid = policy.policy_id
    out = RuleOutcome("approve")

    if ex.driver_licensed is False:
        out.recommendation = "deny"
        out.bases.append(Basis(f"{pid}-4.1", "The claim form states the driver was not licensed"))
    if ex.alcohol_positive:
        out.recommendation = "deny"
        out.bases.append(Basis(f"{pid}-4.2", "The police report records a positive alcohol test", Sensitivity.CONFIDENTIAL))
    if ex.commercial_use:
        out.recommendation = "deny"
        out.bases.append(Basis(f"{pid}-4.3", "The claim form states the vehicle was used for business"))

    if out.recommendation != "deny":
        repair = ex.repair_estimate or 0.0
        limit = min(ex.vehicle_value or policy.vehicle_value_cap, policy.vehicle_value_cap)
        out.payable_damage = round(max(0.0, min(repair, limit) - policy.excess), 2)
        out.bases.append(Basis(f"{pid}-2.1", f"Collision damage is covered less the {policy.excess:.0f} EUR excess"))
        if repair > limit:
            out.bases.append(Basis(f"{pid}-2.2", f"Settlement is capped at the market value of {limit:.2f} EUR"))
        if ex.medical_amount:
            out.payable_medical = round(min(ex.medical_amount, MEDICAL_LIMIT), 2)
            out.bases.append(Basis(f"{pid}-6.1", f"Medical costs of {ex.medical_amount:.2f} EUR are covered up to {MEDICAL_LIMIT:.0f} EUR",
                                    Sensitivity.SPECIAL_CATEGORY))
        if days_to_report is not None and days_to_report > LATE_NOTIFICATION_DAYS:
            out.recommendation = "request_information"
            out.bases.append(Basis(f"{pid}-5.1", f"The incident was reported after {days_to_report} days"))

    if (ex.repair_estimate or 0) > HIGH_VALUE_THRESHOLD:
        out.escalate = True
        out.escalation_reasons.append("high value")
        out.bases.append(Basis("GL-1", "Repair estimate exceeds 10,000 EUR"))
    if fraud_flag:
        out.escalate = True
        out.escalation_reasons.append("fraud indicator")
        out.bases.append(Basis("GL-2", "The claim was flagged by the fraud indicator", Sensitivity.CONFIDENTIAL))
    return out
