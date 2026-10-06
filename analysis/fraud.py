"""Fraud-indicator model: a separate, structured statistical model.

It is deliberately not part of the generative component. It sees structured claim features only
and outputs a flag for supervisor review, never a decision.

Feature groups
--------------
* ``BEHAVIOUR_FEATURES`` - claim behaviour that drives true fraud in the synthetic data.
* ``VEHICLE_FEATURES`` - legitimate-looking vehicle attributes that happen to correlate with area
  (older, cheaper cars in area B). They are the hidden proxies the fairness audit must find.
* ``PROXY_FEATURES`` - explicit area and postcode features.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from analysis.synthetic import Claim

BEHAVIOUR_FEATURES = ["prior_claims", "new_policy", "days_to_report", "police_attended",
                      "estimate_to_value", "log_estimate"]
VEHICLE_FEATURES = ["vehicle_age", "log_value"]
PROXY_FEATURES = ["postcode_risk_score", "area_b"]
DEFAULT_FEATURES = BEHAVIOUR_FEATURES + VEHICLE_FEATURES


def features(c: Claim) -> dict[str, float]:
    return {
        "prior_claims": c.prior_claims,
        "new_policy": float(c.policy_age_days < 90),
        "days_to_report": c.days_to_report,
        "police_attended": float(c.police_attended),
        "estimate_to_value": c.repair_estimate / c.vehicle_value,
        "log_estimate": math.log1p(c.repair_estimate),
        "vehicle_age": c.vehicle_age,
        "log_value": math.log1p(c.vehicle_value),
        "postcode_risk_score": c.postcode_risk_score,
        "area_b": float(c.area == "B"),
    }


def matrix(claims: list[Claim], cols: list[str]) -> np.ndarray:
    return np.array([[features(c)[k] for k in cols] for c in claims])


def group_of(c: Claim, attribute: str) -> str:
    return getattr(c, attribute)


@dataclass
class FraudModel:
    cols: list[str]
    flag_rate: float = 0.10
    label: str = "historical_label"

    def __post_init__(self):
        self.group_thresholds: dict[str, float] | None = None
        self.threshold_attribute: str | None = None

    def fit(self, claims: list[Claim]) -> "FraudModel":
        y = np.array([getattr(c, self.label) for c in claims])
        self.model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        self.model.fit(matrix(claims, self.cols), y)
        self.threshold = float(np.quantile(self.scores(claims), 1 - self.flag_rate))
        return self

    def scores(self, claims: list[Claim]) -> np.ndarray:
        return self.model.predict_proba(matrix(claims, self.cols))[:, 1]

    def flags(self, claims: list[Claim]) -> np.ndarray:
        s = self.scores(claims)
        if self.group_thresholds:
            t = np.array([self.group_thresholds.get(group_of(c, self.threshold_attribute), self.threshold)
                          for c in claims])
            return s >= t
        return s >= self.threshold

    def equalise_fpr(self, audit_sample: list[Claim], target_fpr: float, attribute: str = "area") -> "FraudModel":
        """Per-group thresholds giving the same false-positive rate on an audited sample.

        Needs ground-truth outcomes for the sample (a randomly selected, fully investigated set
        of claims), not the biased historical labels.
        """
        s = self.scores(audit_sample)
        self.group_thresholds, self.threshold_attribute = {}, attribute
        for g in sorted({group_of(c, attribute) for c in audit_sample}):
            neg = np.array([sc for sc, c in zip(s, audit_sample) if group_of(c, attribute) == g and not c.true_fraud])
            if len(neg):
                self.group_thresholds[g] = float(np.quantile(neg, 1 - target_fpr))
        return self
