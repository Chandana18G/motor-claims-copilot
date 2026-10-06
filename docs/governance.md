# Governance: closing the accountability gap

The assessment's central structural finding is that the insurer already has mature governance,
but **no existing function owns GenAI-specific risk** for the Claims Copilot: not Legal and
Compliance, not the DPO, not the general model-risk team. That gap multiplies every other risk,
because errors that nobody owns are not corrected. This document sets out how to close it. It is
a proposal, not an adopted policy.

## Ownership

Responsibility is distributed across functions that already exist, plus one new coordinating
function:

| Function | Owns |
| --- | --- |
| Executive management | the deployment decision |
| Claims management | review conditions for adjusters, including protected review time |
| AI development team | technical evidence: validation, fairness testing, model changes |
| IT operations | integrity and retention of the audit log |
| Legal & Compliance, DPO | the open regulatory questions (AI Act classification, Art. 22, DPIA) |
| Risk management | ongoing monitoring |
| Internal audit | independent assurance; its independence gives its findings weight |
| **AI Governance function (new)** | coordinating all of the above for GenAI-specific risk |

## Responsibility across nine activities (RACI)

R = responsible, A = accountable, C = consulted, I = informed.

| Activity | Exec mgmt | Claims mgmt | AI dev team | IT ops | Compliance / DPO | Risk mgmt | Internal audit | AI Governance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Deployment decision | A | C | C | I | C | C | I | R |
| Review-time standards for adjusters | I | A/R | C | – | C | C | I | C |
| Fairness validation before each release | I | I | R | – | C | C | I | A |
| DPIA and legal basis | I | C | C | C | A/R | C | I | C |
| Audit-log integrity | I | – | C | A/R | I | I | C | I |
| Monitoring programme | I | C | R | C | I | C | I | A |
| Incident response and pausing the system | I | C | R | C | C | C | I | A |
| Model retraining and change control | I | C | R | C | C | C | I | A |
| Independent assurance of the above | I | I | I | I | I | I | A/R | C |

## Sign-off

Because no single function owns the risk today, deployment approval should be a **joint
sign-off** by Legal & Compliance, the DPO, model risk and the AI Governance function.

## One monitoring programme

| Signal | Why |
| --- | --- |
| Override and acceptance rates | context only: the simulation in the README shows the override rate carries no information about how many wrong drafts become decisions |
| **Unannounced re-review of accepted recommendations** | the signal that does track harm (Spearman ρ ≈ 0.84 in simulation) |
| Fraud-model false-positive rate by subgroup, on an audited sample | averages hide unfair flagging; historical outcomes are themselves biased |
| Access-log audits | health data in AI summaries needs the same protection as the medical record |

## Incident response

Defined triggers, each with a named person authorised to pause that part of the system while it
is investigated:

1. a detected fairness disparity in the fraud indicator,
2. a confirmed privacy incident,
3. a confirmed case of the AI's rationale being misleading.

Claims keep flowing while a component is paused: without the fraud score, or handled manually.
