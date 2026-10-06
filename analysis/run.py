"""Run both supporting analyses and write results/metrics.json and figures/.

    python -m analysis.run

All claims are synthetic (see analysis/synthetic.py). Results illustrate the assessment's
arguments; they describe no real insurer or claimant population.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from analysis import automation_bias, fairness, figures
from analysis.fraud import BEHAVIOUR_FEATURES, DEFAULT_FEATURES, PROXY_FEATURES, FraudModel, matrix
from analysis.synthetic import generate_claims

ROOT = Path(__file__).resolve().parent.parent
ATTRIBUTES = ("area", "age_band", "sex")


def _audit_model(model: FraudModel, test) -> dict:
    y = np.array([c.true_fraud for c in test])
    flags = model.flags(test)
    out = {"auc_true_labels": round(float(roc_auc_score(y, model.scores(test))), 4),
           "flag_rate": round(float(flags.mean()), 4)}
    for attr in ATTRIBUTES:
        rates, disp = fairness.audit(flags, y, np.array([getattr(c, attr) for c in test]), attr, n_boot=1000)
        out[attr] = {"rates": {r.group: {"fpr": round(r.fpr, 4), "ci": [round(v, 4) for v in r.fpr_ci],
                                         "tpr": round(r.tpr, 4), "n": r.n} for r in rates},
                     "disparities": [{"group": d.group, "vs": d.reference, "ratio": round(d.ratio, 3),
                                      "ci": [round(v, 3) for v in d.ci], "flagged": d.flagged} for d in disp]}
    return out


def run_fairness() -> dict:
    claims = generate_claims(n=40_000, seed=11)
    train, test = claims[:28_000], claims[28_000:]
    audit_sample = random.Random(3).sample(train, 2_000)
    full = FraudModel(DEFAULT_FEATURES + PROXY_FEATURES).fit(train)
    base_fpr = float(np.mean(full.flags(test)[~np.array([c.true_fraud for c in test])]))
    variants = {
        "Historical labels, all features": full,
        "Area and postcode removed": FraudModel(DEFAULT_FEATURES).fit(train),
        "Thresholds equalised on audit sample": FraudModel(DEFAULT_FEATURES).fit(train).equalise_fpr(audit_sample, base_fpr),
        "Trained on audit sample (2,000)": FraudModel(DEFAULT_FEATURES, label="true_fraud").fit(audit_sample),
    }
    out = {"variants": {name: _audit_model(m, test) for name, m in variants.items()},
           "test_claims": len(test), "true_fraud_rate": round(float(np.mean([c.true_fraud for c in test])), 4)}

    sub = test[:6000]
    groups = np.array([c.area for c in sub])
    out["proxy_strength_auc_area"] = {
        "all features": round(fairness.proxy_strength(matrix(sub, DEFAULT_FEATURES + PROXY_FEATURES), groups, "B"), 3),
        "area and postcode removed": round(fairness.proxy_strength(matrix(sub, DEFAULT_FEATURES), groups, "B"), 3),
        "behaviour features only": round(fairness.proxy_strength(matrix(sub, BEHAVIOUR_FEATURES), groups, "B"), 3)}

    # Null controls with unbiased labels: a model that cannot see area should not be flagged
    # (the audit's false-alarm rate); a model that sees area directly can still pick up noise.
    flagged = {"behaviour_only": 0, "with_area_features": 0}
    for seed in range(10):
        cl = generate_claims(n=20_000, seed=100 + seed, scrutiny_gap=0.0, young_scrutiny_gap=0.0)
        te = cl[14_000:]
        y, g = np.array([c.true_fraud for c in te]), np.array([c.area for c in te])
        for key, cols in (("behaviour_only", BEHAVIOUR_FEATURES), ("with_area_features", DEFAULT_FEATURES + PROXY_FEATURES)):
            _, disp = fairness.audit(FraudModel(cols).fit(cl[:14_000]).flags(te), y, g, "area", n_boot=500, seed=seed)
            flagged[key] += any(d.flagged for d in disp)
    out["null_control_unbiased_labels"] = {k: f"{v}/10 models flagged" for k, v in flagged.items()}

    # Replication of the age-band result across seeds.
    replication = {}
    for seed in (11, 77, 78):
        cl = generate_claims(n=40_000, seed=seed)
        te = cl[28_000:]
        _, disp = fairness.audit(FraudModel(BEHAVIOUR_FEATURES).fit(cl[:28_000]).flags(te),
                                 np.array([c.true_fraud for c in te]), np.array([c.age_band for c in te]),
                                 "age_band", n_boot=300)
        replication[seed] = {d.group: round(d.ratio, 3) for d in disp}
    out["age_band_replication"] = replication

    sizes = {}
    y = np.array([c.true_fraud for c in test])
    for size in (250, 500, 1000, 2000):
        ratios, aucs = [], []
        for draw in range(5):
            m = FraudModel(DEFAULT_FEATURES, label="true_fraud").fit(random.Random(50 + draw).sample(train, size))
            _, disp = fairness.audit(m.flags(test), y, np.array([c.area for c in test]), "area", n_boot=200)
            ratios.append(disp[0].ratio)
            aucs.append(roc_auc_score(y, m.scores(test)))
        sizes[size] = {"fpr_ratio_mean": round(float(np.mean(ratios)), 3),
                       "fpr_ratio_range": [round(float(min(ratios)), 3), round(float(max(ratios)), 3)],
                       "auc_mean": round(float(np.mean(aucs)), 3)}
    out["audit_sample_size"] = sizes

    feature_sets = (("all_features", DEFAULT_FEATURES + PROXY_FEATURES),
                    ("area_removed", DEFAULT_FEATURES), ("behaviour_only", BEHAVIOUR_FEATURES))
    sweep = []
    for gap in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
        ratios: dict[str, list[float]] = {label: [] for label, _ in feature_sets}
        for seed in (21, 22, 23):
            cl = generate_claims(n=20_000, seed=seed, scrutiny_gap=gap)
            te = cl[14_000:]
            neg = np.array([not c.true_fraud for c in te])
            b = np.array([c.area == "B" for c in te])
            for label, cols in feature_sets:
                f = FraudModel(cols).fit(cl[:14_000]).flags(te)
                ratios[label].append(f[neg & b].mean() / max(f[neg & ~b].mean(), 1e-9))
        sweep.append({"scrutiny_gap": gap, **{k: round(float(np.mean(v)), 3) for k, v in ratios.items()}})
    out["feedback_sweep"] = sweep
    return out


def main() -> None:
    sim = automation_bias.simulate()
    results = {"fairness": run_fairness(), "automation_bias": automation_bias.summarise(sim)}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "metrics.json").write_text(json.dumps(results, indent=2, default=str))
    figures.render_all(results, sim, ROOT / "figures")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
