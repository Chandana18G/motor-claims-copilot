"""Subgroup fairness audit for the fraud indicator.

The primary metric is the false-positive rate by group: how often honest claimants are flagged.
Every rate comes with a bootstrap 95% confidence interval, and a disparity is only reported when
the interval for the ratio between groups excludes parity by a margin (default: outside
0.8-1.25). The audit also measures how well the model's own features predict each protected
attribute (proxy strength), because removing the attribute itself does not remove its proxies.

Ground truth (``true_fraud``) is needed for false-positive rates. In operation that means a
randomly selected, fully investigated audit sample; historical investigation outcomes are
themselves biased and cannot serve as ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_predict

PARITY_BAND = (0.8, 1.25)


@dataclass
class GroupRates:
    group: str
    n: int
    fpr: float
    fpr_ci: tuple[float, float]
    tpr: float
    flag_rate: float


@dataclass
class Disparity:
    attribute: str
    reference: str
    group: str
    ratio: float
    ci: tuple[float, float]

    @property
    def flagged(self) -> bool:
        lo, hi = self.ci
        return lo > PARITY_BAND[1] or hi < PARITY_BAND[0]


def _fpr(flags: np.ndarray, y: np.ndarray) -> float:
    neg = ~y
    return float(flags[neg].mean()) if neg.any() else float("nan")


def audit(flags: np.ndarray, y_true: np.ndarray, groups: np.ndarray, attribute: str,
          n_boot: int = 1000, seed: int = 0) -> tuple[list[GroupRates], list[Disparity]]:
    rng = np.random.default_rng(seed)
    flags, y_true, groups = np.asarray(flags, bool), np.asarray(y_true, bool), np.asarray(groups)
    names = sorted(set(groups.tolist()))
    idx = {g: np.flatnonzero(groups == g) for g in names}
    boot = {g: np.empty(n_boot) for g in names}
    for g in names:
        neg = idx[g][~y_true[idx[g]]]
        draws = rng.integers(0, len(neg), size=(n_boot, len(neg)))
        boot[g] = flags[neg][draws].mean(axis=1)
    rates = []
    for g in names:
        i = idx[g]
        pos = i[y_true[i]]
        rates.append(GroupRates(
            g, len(i), _fpr(flags[i], y_true[i]),
            (float(np.quantile(boot[g], 0.025)), float(np.quantile(boot[g], 0.975))),
            float(flags[pos].mean()) if len(pos) else float("nan"), float(flags[i].mean())))
    reference = max(names, key=lambda g: len(idx[g]))
    disparities = []
    for g in names:
        if g == reference:
            continue
        ratio_boot = boot[g] / np.maximum(boot[reference], 1e-9)
        ratio = _fpr(flags[idx[g]], y_true[idx[g]]) / max(_fpr(flags[idx[reference]], y_true[idx[reference]]), 1e-9)
        disparities.append(Disparity(attribute, reference, g, ratio,
                                     (float(np.quantile(ratio_boot, 0.025)), float(np.quantile(ratio_boot, 0.975)))))
    return rates, disparities


def proxy_strength(x: np.ndarray, groups: np.ndarray, positive) -> float:
    """Cross-validated AUC of predicting group membership from the model's features.

    0.5 means the features carry no information about the group; values well above 0.5 mean
    the model can reconstruct the group even if it is not an input.
    """
    y = np.asarray(groups) == positive
    p = cross_val_predict(LogisticRegression(max_iter=1000), x, y, cv=5, method="predict_proba")[:, 1]
    return float(roc_auc_score(y, p))
