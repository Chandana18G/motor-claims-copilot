import numpy as np

from analysis import automation_bias, fairness
from analysis.fraud import BEHAVIOUR_FEATURES, FraudModel
from analysis.synthetic import generate_claims


def test_true_fraud_is_independent_of_area():
    claims = generate_claims(n=40_000, seed=1)
    a = np.mean([c.true_fraud for c in claims if c.area == "A"])
    b = np.mean([c.true_fraud for c in claims if c.area == "B"])
    assert abs(a - b) < 0.006


def test_historical_labels_are_biased_towards_area_b():
    claims = generate_claims(n=40_000, seed=1)
    def recorded(area):
        frauds = [c for c in claims if c.area == area and c.true_fraud]
        return np.mean([c.historical_label for c in frauds])
    assert recorded("B") > recorded("A") + 0.3


def test_audit_flags_a_clear_disparity_and_not_parity():
    rng = np.random.default_rng(0)
    groups = np.array(["A"] * 5000 + ["B"] * 5000)
    y = np.zeros(10_000, bool)
    unfair = np.concatenate([rng.random(5000) < 0.05, rng.random(5000) < 0.15])
    fair = rng.random(10_000) < 0.10
    assert fairness.audit(unfair, y, groups, "g", n_boot=300)[1][0].flagged
    assert not fairness.audit(fair, y, groups, "g", n_boot=300)[1][0].flagged


def test_model_without_area_information_passes_on_unbiased_labels():
    claims = generate_claims(n=20_000, seed=5, scrutiny_gap=0.0, young_scrutiny_gap=0.0)
    model = FraudModel(BEHAVIOUR_FEATURES).fit(claims[:14_000])
    test = claims[14_000:]
    _, disp = fairness.audit(model.flags(test), np.array([c.true_fraud for c in test]),
                             np.array([c.area for c in test]), "area", n_boot=300)
    assert not disp[0].flagged


def test_override_rate_carries_no_signal_but_re_review_does():
    summary = automation_bias.summarise(automation_bias.simulate(runs=1000, seed=1))
    assert abs(summary["spearman_override_vs_harm"]) < 0.15
    assert summary["spearman_resample_vs_harm"] > 0.7
