"""Monte Carlo test of what monitoring can and cannot reveal about human review.

Each run draws an unknown "true world" from wide ranges, because the real values are unknown
until a pilot measures them:

* AI error rate e         ~ U(1%, 15%)
* share of drafts really reviewed d ~ U(5%, 100%)
* chance a real review catches an AI error c ~ U(60%, 95%)
* chance a real review overrides a correct draft f ~ U(0%, 5%)

It then simulates a month of operation (2,000 real drafts, 60 hidden canaries, 100 accepted
decisions re-reviewed) and compares what each monitoring signal reports with the truth. This is
a simulation of the monitoring design, not evidence about real adjusters; that needs a pilot.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr


def simulate(runs: int = 2000, drafts: int = 2000, canaries: int = 60, resample: int = 100,
             seed: int = 0) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    e = rng.uniform(0.01, 0.15, runs)
    d = rng.uniform(0.05, 1.0, runs)
    c = rng.uniform(0.60, 0.95, runs)
    f = rng.uniform(0.0, 0.05, runs)
    catch = d * c                                   # P(an AI error is caught)
    wrong = rng.binomial(drafts, e)
    caught = rng.binomial(wrong, catch)
    false_override = rng.binomial(drafts - wrong, d * f)
    override_rate = (caught + false_override) / drafts
    pass_through = (wrong - caught) / drafts        # wrong drafts that became decisions
    canary_est = rng.binomial(canaries, catch) / canaries
    accepted = drafts - caught - false_override
    wrong_among_accepted = (wrong - caught) / np.maximum(accepted, 1)
    resample_est = rng.binomial(resample, wrong_among_accepted) / resample * accepted / drafts
    return {"e": e, "d": d, "c": c, "f": f, "catch": catch, "override_rate": override_rate,
            "pass_through": pass_through, "canary_est": canary_est, "resample_est": resample_est}


def summarise(sim: dict[str, np.ndarray]) -> dict:
    band = (sim["override_rate"] > 0.025) & (sim["override_rate"] < 0.035)
    return {
        "runs": int(len(sim["e"])),
        "spearman_override_vs_harm": round(float(spearmanr(sim["override_rate"], sim["pass_through"])[0]), 3),
        "spearman_canary_vs_catch": round(float(spearmanr(sim["canary_est"], sim["catch"])[0]), 3),
        "spearman_resample_vs_harm": round(float(spearmanr(sim["resample_est"], sim["pass_through"])[0]), 3),
        "canary_mean_abs_error": round(float(np.mean(np.abs(sim["canary_est"] - sim["catch"]))), 3),
        "harm_range_at_3pct_override": [round(float(np.min(sim["pass_through"][band])), 4),
                                        round(float(np.max(sim["pass_through"][band])), 4)],
        "runs_at_3pct_override": int(band.sum()),
    }
