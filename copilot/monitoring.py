"""Operational monitoring: measuring whether human review is real.

An override rate cannot tell accurate AI from rubber-stamping. Two measurements can:

* **Canaries.** A small share of drafts in the review queue are deliberately wrong (a changed
  recommendation or payout) and indistinguishable from real drafts. The share of canaries the
  adjusters catch estimates the probability that a real AI error is caught.
* **Unannounced re-review** of a random sample of *accepted* recommendations estimates how
  many wrong drafts became decisions.

Both come with Wilson 95% confidence intervals. When a measurement crosses a threshold defined
in the incident procedure, ``Monitor.check`` opens an incident, which pauses the affected
component (see ``copilot.controls``).

Canaries are never sent to claimants: a decision on a canary is intercepted and the real claim
is re-queued.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from copilot.controls import Controls, Incident
from copilot.fairness import Disparity


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


@dataclass
class Thresholds:
    min_canary_catch: float = 0.80        # incident if the upper CI bound falls below this
    max_accepted_error: float = 0.02      # incident if the lower CI bound rises above this
    max_citation_failure: float = 0.05    # share of generated drafts rejected by the guardrails


@dataclass
class Monitor:
    controls: Controls
    thresholds: Thresholds = field(default_factory=Thresholds)
    reviewed: int = 0
    overridden: int = 0
    canaries: int = 0
    canaries_caught: int = 0
    resampled: int = 0
    resampled_errors: int = 0
    generated: int = 0
    generated_rejected: int = 0

    def record_review(self, overridden: bool, canary: bool = False) -> None:
        if canary:
            self.canaries += 1
            self.canaries_caught += overridden
        else:
            self.reviewed += 1
            self.overridden += overridden

    def record_resample(self, decision_was_wrong: bool) -> None:
        self.resampled += 1
        self.resampled_errors += decision_was_wrong

    def record_generation(self, rejected: bool) -> None:
        self.generated += 1
        self.generated_rejected += rejected

    @property
    def override_rate(self) -> float:
        return self.overridden / self.reviewed if self.reviewed else float("nan")

    def canary_catch(self) -> tuple[float, tuple[float, float]]:
        n = self.canaries
        return (self.canaries_caught / n if n else float("nan"), wilson(self.canaries_caught, n))

    def accepted_error(self) -> tuple[float, tuple[float, float]]:
        n = self.resampled
        return (self.resampled_errors / n if n else float("nan"), wilson(self.resampled_errors, n))

    def check(self, disparities: list[Disparity] = ()) -> list[Incident]:
        opened = []
        _, (_, catch_hi) = self.canary_catch()
        if self.canaries >= 20 and catch_hi < self.thresholds.min_canary_catch:
            opened.append(Incident("review_quality", "copilot",
                                   f"canary catch rate CI upper bound {catch_hi:.2f}"))
        _, (err_lo, _) = self.accepted_error()
        if self.resampled >= 30 and err_lo > self.thresholds.max_accepted_error:
            opened.append(Incident("accepted_errors", "copilot", f"accepted-error CI lower bound {err_lo:.3f}"))
        if self.generated >= 50:
            lo, _ = wilson(self.generated_rejected, self.generated)
            if lo > self.thresholds.max_citation_failure:
                opened.append(Incident("misleading_rationale", "llm_drafter",
                                       f"guardrail rejection rate CI lower bound {lo:.3f}"))
        for d in disparities:
            if d.flagged:
                opened.append(Incident("fairness_disparity", "fraud_model",
                                       f"{d.attribute}={d.group}: FPR ratio {d.ratio:.2f} (CI {d.ci[0]:.2f}-{d.ci[1]:.2f})"))
        for incident in opened:
            self.controls.open_incident(incident)
        return opened
