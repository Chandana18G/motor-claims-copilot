"""Synthetic motor claims with a controllable historical investigation bias.

Nothing here describes real people. The generator exists so that the fairness audit can be run
against known ground truth.

Bias model
----------
``true_fraud`` depends on claim behaviour only and is independent of ``area``, ``age_band``,
``sex`` and the vehicle. The *historical label* that a model would be trained on is what past
investigations found: claims from area ``B`` were investigated much more often, and drivers aged
18-25 somewhat more often, so their frauds were caught (and recorded) more often. ``sex`` has no
scrutiny bias and serves as a null control. Area-B vehicles are older and cheaper on average, so
vehicle features act as proxies for area even after area itself is removed.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, timedelta

# Product: (share of claims, vehicle value cap in EUR)
PRODUCTS = {"BASIC": (0.45, 15_000.0), "COMFORT": (0.40, 30_000.0), "PREMIUM": (0.15, 60_000.0)}
SCRUTINY_BASE = 0.25
YOUNG_SCRUTINY_GAP = 0.15


@dataclass
class Claim:
    claim_id: str
    product: str
    area: str
    age_band: str
    sex: str
    incident_date: date
    report_date: date
    repair_estimate: float
    vehicle_value: float
    vehicle_age: int
    police_attended: bool
    prior_claims: int
    policy_age_days: int
    postcode_risk_score: float
    true_fraud: bool
    historical_label: bool

    @property
    def days_to_report(self) -> int:
        return (self.report_date - self.incident_date).days


def generate_claims(n: int = 4000, seed: int = 7, scrutiny_gap: float = 0.5,
                    young_scrutiny_gap: float = YOUNG_SCRUTINY_GAP) -> list[Claim]:
    """Generate ``n`` claims.

    ``scrutiny_gap`` is how much more often area-B claims were investigated in the past
    (0 = equal scrutiny, no label bias); ``young_scrutiny_gap`` the same for drivers aged 18-25.
    """
    rng = random.Random(seed)
    claims: list[Claim] = []
    start = date(2025, 1, 1)
    for i in range(n):
        product = rng.choices(list(PRODUCTS), weights=[w for w, _ in PRODUCTS.values()])[0]
        cap = PRODUCTS[product][1]
        area = "B" if rng.random() < 0.35 else "A"
        age_band = rng.choices(["18-25", "26-60", "61+"], weights=[0.18, 0.64, 0.18])[0]
        sex = rng.choice(["F", "M"])
        vehicle_age = max(0, int(rng.gauss(9.0 if area == "B" else 6.0, 3.0)))
        vehicle_value = round(max(2_000.0, cap * math.exp(-0.07 * vehicle_age) * rng.uniform(0.35, 0.95)), -2)
        prior_claims = min(4, int(rng.expovariate(1.6)))
        policy_age_days = rng.randint(10, 2_000)
        postcode_risk = min(1.0, max(0.0, rng.gauss(0.62 if area == "B" else 0.38, 0.12)))

        # True fraud depends on behaviour only.
        score = -3.6 + 0.55 * prior_claims + (1.0 if policy_age_days < 90 else 0.0)
        incident_date = start + timedelta(days=rng.randint(0, 540))
        late = rng.random() < 0.12
        score += 0.9 if late else 0.0
        police_attended = rng.random() < 0.4
        score += -0.6 if police_attended else 0.3
        true_fraud = rng.random() < 1 / (1 + math.exp(-score))

        severity = rng.lognormvariate(7.6, 0.6)
        if true_fraud:
            severity *= rng.uniform(1.3, 2.2)
        repair_estimate = round(min(severity, vehicle_value * 0.95), 2)
        report_date = incident_date + timedelta(days=rng.randint(31, 90) if late else rng.randint(0, 10))

        p_investigated = (SCRUTINY_BASE + (scrutiny_gap if area == "B" else 0.0)
                          + (young_scrutiny_gap if age_band == "18-25" else 0.0))
        historical_label = true_fraud and rng.random() < min(1.0, p_investigated)

        claims.append(Claim(
            claim_id=f"C{i:05d}", product=product, area=area, age_band=age_band, sex=sex,
            incident_date=incident_date, report_date=report_date, repair_estimate=repair_estimate,
            vehicle_value=vehicle_value, vehicle_age=vehicle_age, police_attended=police_attended,
            prior_claims=prior_claims, policy_age_days=policy_age_days,
            postcode_risk_score=round(postcode_risk, 3), true_fraud=true_fraud,
            historical_label=historical_label))
    return claims
