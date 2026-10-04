# Data Protection Impact Assessment (draft for a pilot)

Structured after GDPR Art. 35(7). This is a working draft for the prototype's design, prepared
to show what a DPIA has to cover; it is not legal advice and would need review by the
insurer's DPO before any processing of real data.

## 1. Description of the processing

- **Purpose:** support claims adjusters by extracting claim facts, retrieving policy wording,
  computing coverage rules and drafting a cited summary. Decisions are made by staff.
- **Data subjects:** policyholders, other drivers, passengers, witnesses.
- **Data:** claim forms, repair estimates, police reports (confidential), medical notes
  (special-category health data, Art. 9), fraud-indicator scores.
- **Recipients:** adjusters, supervisors, fraud investigators (no health data by default),
  auditors (metadata), and, if the LLM drafter is enabled, the model provider as processor.
- **Retention:** as the insurer's claims retention schedule; audit-log retention as required by
  the AI Act deployer obligations where they apply (classification is open, see the README).

## 2. Why a DPIA is required

Evaluation and scoring (fraud indicator), special-category data at scale, and decision support
that may meet Art. 22 if review becomes nominal. Any one would justify a DPIA; together they
make it clearly necessary.

## 3. Necessity and proportionality

- Fraud scoring uses structured claim behaviour only; area and postcode features are excluded
  because the audit showed they carry historical investigation bias.
- Health data is used only to compute the medical payout; drafts that mention it inherit the
  special-category label and are withheld from roles without clearance.
- The LLM drafter receives validated facts and the rule outcome; it cannot change the outcome.
  It can be switched off (template drafter) without stopping claims handling.

## 4. Risks to data subjects and measures

| Risk | Measure | Where |
| --- | --- | --- |
| Decision effectively automated (Art. 22) | named-human decisions, override reasons, canary monitoring of review quality | `workflow.py`, `monitoring.py` |
| Unfair fraud flags for some groups | subgroup FPR audit with CIs, audited sample, automatic pause on disparity | `fairness.py`, `controls.py` |
| Disclosure of health data | sensitivity labels, role clearance, logged views | `access.py`, `workflow.py` |
| Leakage via prompt injection | pattern guard, policy-scoped retrieval, output checks reject leaks and changed outcomes | `guard.py`, `retrieval.py`, `drafter.py` |
| Hallucinated terms or amounts | verbatim citation checks, causal-clause check, amount whitelist | `drafter.py` |
| Tampering with records | keyed hash chain with external anchors | `audit.py` |

## 5. Residual risks to resolve before a pilot

- Lawful basis for health data (Art. 9(2)) and for fraud scoring must be confirmed by the DPO.
- A data processing agreement and transfer assessment for the model provider.
- Real-data fairness validation on an audited sample; the prototype's results are synthetic.
- Review-quality evidence from a restricted pilot (canary catch rate) before wider rollout.
