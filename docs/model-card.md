# Model card: illustrative fraud indicator

Used only in the fairness analysis; it is not a production model.

- **Type:** logistic regression on standardised structured features (`analysis/fraud.py`).
- **Output:** a flag for the top 10% of scores, meant for supervisor review, never a decision.
- **Default features:** prior claims, new policy (< 90 days), days to report, police attended,
  estimate-to-value ratio, log estimate, vehicle age, log vehicle value.
- **Excluded by default:** area and postcode risk score.

## What the audit found (synthetic data)

- Trained on historical investigation outcomes with area features, honest claimants from area B
  are flagged about **7.6×** as often as those from area A.
- Without area and postcode, the gap is still **1.36×** (95% CI 1.21–1.52): vehicle age and
  value predict area (cross-validated AUC ≈ 0.76) and carry the bias.
- **Per-area thresholds equalised on a 2,000-claim audited sample** remove the gap (1.00×).
- **Retraining on that audited sample** is unstable: 0.77× on the test set (unfair in the other
  direction), and between 0.76× and 1.07× across five draws of the sample.

Both mitigations need a randomly selected, fully investigated audit sample: historical
outcomes cannot be used as ground truth. See `results/metrics.json` for all numbers.
