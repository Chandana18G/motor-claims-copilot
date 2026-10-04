"""Synthetic motor policy wordings, split into citable clauses.

The wording is invented for this prototype. Each clause has a stable id so that drafts can
cite it and the citation checker can verify the quoted span.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Clause:
    clause_id: str
    policy_id: str
    title: str
    text: str


@dataclass(frozen=True)
class Policy:
    policy_id: str
    product: str
    excess: float
    vehicle_value_cap: float
    covers_rental: bool
    clauses: tuple[Clause, ...]


def _clauses(policy_id: str, rows: list[tuple[str, str, str]]) -> tuple[Clause, ...]:
    return tuple(Clause(f"{policy_id}-{cid}", policy_id, title, text) for cid, title, text in rows)


_COMMON = [
    ("2.1", "Collision damage",
     "We will pay for accidental damage to your vehicle caused by a collision with another "
     "vehicle, a fixed object or an animal, less the policy excess."),
    ("2.2", "Settlement limit",
     "The most we will pay for damage to your vehicle is its market value at the time of the "
     "loss."),
    ("2.3", "Glass damage",
     "We will pay to repair or replace broken glass in the windscreen, sunroof or windows. A "
     "glass-only claim does not affect your no claims discount."),
    ("2.4", "Fire and theft",
     "We will pay for loss of or damage to your vehicle caused by fire, lightning, explosion, "
     "theft or attempted theft."),
    ("2.5", "Recovery after an accident",
     "After an accident we will pay the reasonable cost of moving your vehicle to the nearest "
     "suitable repairer or to a safe place."),
    ("2.6", "Malicious damage",
     "We will pay for damage deliberately caused by another person, provided it is reported to "
     "the police within 48 hours."),
    ("2.7", "Lost keys",
     "If your keys are lost or stolen we will pay towards replacing the locks, keys and "
     "immobiliser of your vehicle."),
    ("4.1", "Unlicensed driver exclusion",
     "We will not pay any claim arising while the vehicle is driven by a person who does not "
     "hold a valid driving licence."),
    ("4.2", "Impairment exclusion",
     "We will not pay any claim arising while the driver is under the influence of alcohol or "
     "drugs above the legal limit."),
    ("4.3", "Commercial use exclusion",
     "We will not pay any claim arising while the vehicle is used for hire, reward or courier "
     "delivery unless business use is shown on the schedule."),
    ("4.4", "Wear and tear exclusion",
     "We will not pay for wear and tear, mechanical or electrical breakdown, or damage to tyres "
     "caused by braking, punctures or cuts."),
    ("4.5", "Racing exclusion",
     "We will not pay any claim arising while the vehicle is used for racing, pace-making or "
     "speed testing, including on track days."),
    ("4.6", "Territorial limits",
     "Cover applies only while the vehicle is in the European Union, Norway, Switzerland or the "
     "United Kingdom."),
    ("5.1", "Late notification",
     "You must tell us about any incident within 30 days. If you tell us later we may ask for "
     "further evidence before we decide the claim."),
    ("5.2", "Police report",
     "Where the police attended the incident you must provide the police report reference."),
    ("5.3", "Fraudulent claims",
     "If any claim is fraudulent or deliberately exaggerated we will not pay it and we may "
     "cancel the policy."),
    ("5.4", "Supporting evidence",
     "You must give us the documents and information we reasonably ask for, including repair "
     "invoices and photographs of the damage."),
    ("6.1", "Personal injury",
     "Medical expenses for injuries to you or your passengers are covered up to 5,000 EUR per "
     "person when supported by medical documentation."),
    ("7.1", "No claims discount",
     "A claim we pay for an accident that was your fault will reduce your no claims discount at "
     "the next renewal."),
]

_RENTAL = [
    ("3.1", "Replacement vehicle",
     "While your vehicle is being repaired after a covered claim we will pay for a replacement "
     "vehicle for up to 14 days."),
]

_NEW_FOR_OLD = [
    ("3.2", "New car replacement",
     "If your vehicle is less than 12 months old and is written off, we will replace it with a "
     "new vehicle of the same make and model."),
]


POLICIES: dict[str, Policy] = {
    "BASIC": Policy("BASIC", "Third party, fire and theft plus collision", 500.0, 15_000.0, False,
                    _clauses("BASIC", _COMMON)),
    "COMFORT": Policy("COMFORT", "Comprehensive", 300.0, 30_000.0, True,
                      _clauses("COMFORT", _COMMON + _RENTAL)),
    "PREMIUM": Policy("PREMIUM", "Comprehensive with new-for-old", 150.0, 60_000.0, True,
                      _clauses("PREMIUM", _COMMON + _RENTAL + _NEW_FOR_OLD)),
}


GUIDELINES: tuple[Clause, ...] = (
    Clause("GL-1", "GUIDELINES", "High-value escalation",
           "Any claim with a repair estimate above 10,000 EUR must be reviewed by a supervisor."),
    Clause("GL-2", "GUIDELINES", "Fraud referral",
           "Claims flagged by the fraud indicator are reviewed by a supervisor and may be "
           "referred to the special investigations unit."),
    Clause("GL-3", "GUIDELINES", "Conflicting evidence",
           "Where documents conflict on a material fact the handler must request further "
           "information before deciding."),
)


def clause_by_id(clause_id: str) -> Clause:
    for clause in GUIDELINES:
        if clause.clause_id == clause_id:
            return clause
    for policy in POLICIES.values():
        for clause in policy.clauses:
            if clause.clause_id == clause_id:
                return clause
    raise KeyError(clause_id)
