# Model card: fraud indicator

- **Type:** logistic regression on standardised structured features (`copilot/fraud.py`).
- **Output:** a flag for the top 10% of scores; flagged claims go to a supervisor. It never
  decides a claim.
- **Default features:** prior claims, new policy (< 90 days), days to report, police attended,
  estimate-to-value ratio, log estimate, vehicle age, log vehicle value.
- **Excluded:** area and postcode risk score (they encode historical investigation bias).

## Known issue: hidden proxies

Vehicle age and value correlate with area in the synthetic data (cross-validated AUC of
predicting area from the default features ≈ 0.76). Trained on historical investigation
outcomes, the default model still flags honest claimants from area B about 1.6× as often as
area A. Two mitigations remove the gap in the evaluation:

1. per-area thresholds equalised on an audited sample with true outcomes, or
2. training on an audited, randomly selected sample (2,000 claims was enough here; 250 to 1,000
   gave unstable results).

Both need a randomly selected, fully investigated audit sample. Historical outcomes cannot be
used as ground truth.

## Evaluation data

Synthetic only (`copilot/synthetic.py`). No result here describes real claimants. See
`results/metrics.json`, stage `5_fairness`, for the numbers with confidence intervals.
