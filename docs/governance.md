# Governance: who owns what, and how it is enforced

The assessment found that no existing function owned GenAI-specific risk for the copilot. This
document assigns ownership and links each control to the code that enforces it. It is a
proposal for a pilot, not an adopted policy.

## Roles

| Role | Holds | Can | Cannot |
| --- | --- | --- | --- |
| Adjuster | signed staff token | view cases (incl. health data), record decisions, override with a reason | sign off their own escalated claim |
| Supervisor | signed staff token | everything an adjuster can, sign off escalated claims, pause a component | resume a paused component |
| Fraud investigator | signed staff token | view cases without health data | decide claims |
| Auditor | signed staff token | view decisions and the audit log | read case content above *internal* |
| AI Governance function | signed staff token | pause and resume components, close incidents | decide claims |
| Copilot / fraud model | no token | prepare drafts and flags | record or communicate any decision |

Enforced in `copilot/identity.py`, `copilot/workflow.py`, `copilot/access.py`, `copilot/controls.py`.

## Responsibility (RACI)

R = responsible, A = accountable, C = consulted, I = informed.

| Activity | Exec mgmt | Claims mgmt | AI dev team | IT ops | Compliance / DPO | Risk mgmt | Internal audit | AI Governance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Deployment decision | A | C | C | I | C | C | I | R |
| Review-time standards for adjusters | I | A/R | C | – | C | C | I | C |
| Fairness validation before each release | I | I | R | – | C | C | I | A |
| DPIA and legal basis | I | C | C | C | A/R | C | I | C |
| Audit-log integrity and anchoring | I | – | C | A/R | I | I | C | I |
| Monitoring programme (canaries, re-review, fairness) | I | C | R | C | I | C | I | A |
| Incident response and component pause | I | C | R | C | C | C | I | A |
| Model retraining and change control | I | C | R | C | C | C | I | A |
| Independent assurance of the above | I | I | I | I | I | I | A/R | C |

Deployment needs **joint sign-off** by Compliance/DPO, risk management (model risk) and the AI
Governance function.

## Monitoring thresholds (`copilot/monitoring.py`)

| Signal | How it is measured | Incident when | Component paused |
| --- | --- | --- | --- |
| Review quality | share of hidden canaries (deliberately wrong drafts) caught | upper 95% bound < 80% (≥ 20 canaries) | copilot (manual handling) |
| Accepted errors | unannounced re-review of accepted decisions | lower 95% bound > 2% (≥ 30 re-reviews) | copilot |
| Misleading rationale | share of generated drafts rejected by output checks | lower 95% bound > 5% (≥ 50 drafts) | llm_drafter (template fallback) |
| Fairness | false-positive rate ratio by group on an audited sample | 95% interval outside 0.8–1.25 | fraud_model |

The override rate is reported but is **not** a trigger: in simulation it carries no information
about how many wrong drafts become decisions (see the README).

## Incident procedure (`copilot/controls.py`)

1. A trigger above opens an incident and pauses the affected component automatically
   (authority delegated in advance). Supervisors can also pause manually.
2. Claims keep flowing without the paused component: no fraud score, template drafts, or fully
   manual handling.
3. The AI Governance function investigates, closes the incident with a written resolution,
   and only then can resume the component. Every step is in the audit log.
