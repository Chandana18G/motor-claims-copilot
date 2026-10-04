"""Reproducible compute and carbon estimate for the prototype.

Measured: CPU seconds for preparing claims and for retraining the fraud model, timed on the
machine running the evaluation. Assumed (edit the constants to your setting):

* POWER_PER_CORE_W - average power drawn per busy CPU core, including memory.
* PUE - data-centre power usage effectiveness.
* GRID_KG_PER_KWH - carbon intensity of the electricity used.

Not included: drafting with a hosted language model. Its energy per request is not published,
so any figure would be a guess; the LLM drafter's share has to be estimated separately once a
provider reports it.
"""

from __future__ import annotations

import time

POWER_PER_CORE_W = 15.0
PUE = 1.2
GRID_KG_PER_KWH = 0.38


def kg_co2(cpu_seconds: float) -> float:
    kwh = cpu_seconds * POWER_PER_CORE_W * PUE / 3_600_000
    return kwh * GRID_KG_PER_KWH


def measure(fn, *args, **kwargs) -> tuple[object, float]:
    start = time.process_time()
    result = fn(*args, **kwargs)
    return result, time.process_time() - start


def report(prepare_seconds: float, claims: int, retrain_seconds: float) -> dict:
    per_claim = prepare_seconds / claims
    return {
        "assumptions": {"power_per_core_w": POWER_PER_CORE_W, "pue": PUE, "grid_kg_per_kwh": GRID_KG_PER_KWH},
        "cpu_ms_per_claim": round(per_claim * 1000, 2),
        "g_co2_per_1000_claims": round(kg_co2(per_claim * 1000) * 1000, 4),
        "fraud_model_retrain_cpu_s": round(retrain_seconds, 2),
        "g_co2_per_retrain": round(kg_co2(retrain_seconds) * 1000, 5),
        "excludes": "hosted LLM drafting (no published energy per request)",
    }
