# Data Protection Impact Assessment (outline)

Structured after GDPR Art. 35(7) for the Claims Copilot as designed in the assessment. It shows
what a DPIA has to cover; it is not legal advice and would need the insurer's DPO before any
processing of real data.

## 1. Description of the processing

- **Purpose:** support claims adjusters by checking claim documents, scoring fraud indicators
  and drafting a cited summary and recommendation. Decisions are made by staff.
- **Data subjects:** policyholders, other drivers, passengers, witnesses.
- **Data:** claim forms, repair estimates, police reports, medical documentation
  (special-category health data, Art. 9), fraud-indicator scores.
- **Recipients:** adjusters, supervisors, fraud investigators, auditors, and the model provider
  as processor.
- **Retention:** the insurer's claims retention schedule; audit-log retention as the AI Act
  requires where it applies (classification is open, see the README).

## 2. Why a DPIA is required

Evaluation and scoring (fraud indicator), special-category data at scale, and decision support
that may fall under Art. 22 if review becomes nominal. Any one would justify a DPIA; together
they make it clearly necessary.

## 3. Necessity and proportionality

- The fraud indicator should use claim behaviour; features that encode where people live carry
  historical investigation bias (see the fairness analysis).
- Health data should be used only where it is needed for the decision, and AI-generated
  summaries that mention it need the same access controls as the medical record.
- The generative component should be grounded in the policy wording and should have no
  authority to decide, pay or contact the claimant.

## 4. Risks to data subjects and measures

| Risk | Measure |
| --- | --- |
| Decision effectively automated (Art. 22) | named human decisions, logged override reasons, unannounced re-review of accepted recommendations |
| Unfair fraud flags for some groups | subgroup false-positive testing on an audited sample before each release; authority to pause the model |
| Disclosure of health data | role-based access matched to sensitivity; access-log audits |
| Leakage via prompt injection | documents treated as untrusted input; security testing before the pilot |
| Hallucinated terms | retrieval-grounded generation tied to the claimant's policy; citations checked |
| Errors left uncorrected | immutable, attributable audit log; clear ownership (see governance) |

## 5. Open points before a pilot

- Lawful basis for health data (Art. 9(2)) and for fraud scoring, confirmed by the DPO.
- A data processing agreement and transfer assessment for the model provider.
- Fairness validation on real, audited claims.
- Evidence from a restricted pilot that review is meaningful.
