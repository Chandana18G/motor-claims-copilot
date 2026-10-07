# Claims Copilot: Responsible Generative AI for Motor Insurance

**Author:** [Chandana Gurusiddappa](https://chandana18g.github.io) · [LinkedIn](https://www.linkedin.com/in/chandana-gurusiddappa-785563223/) · [GitHub](https://github.com/Chandana18G)

A Responsible AI assessment of a generative-AI copilot for motor insurance claims handling:
**should it be trusted with a real claim, and under what conditions?** The assessment works
through stakeholders, five ethical lenses, the EU AI Act and the GDPR, a risk analysis and a
governance design. Two small analyses on synthetic data test its central claims.

> **Verdict:** a plausible and defensible Responsible AI design, but responsible deployment is
> not yet confirmed until evidence, governance and monitoring requirements are demonstrated.

## Contents

- [The system](#the-system)
- [Why it matters](#why-it-matters)
- [Stakeholders](#stakeholders)
- [Ethics: five lenses, one convergence](#ethics-five-lenses-one-convergence)
- [Regulation](#regulation)
- [Risks](#risks)
- [Human-in-the-loop is not human-in-control](#human-in-the-loop-is-not-human-in-control)
- [Fairness: averages hide who gets flagged](#fairness-averages-hide-who-gets-flagged)
- [Privacy, security and sustainability](#privacy-security-and-sustainability)
- [Governance](#governance)
- [Path to deployment](#path-to-deployment)
- [Verdict](#verdict)
- [About the analyses](#about-the-analyses)

## The system

![One claim's journey through the Claims Copilot](figures/architecture.png)

A claim arrives through the portal, email or phone. The system checks the documents (police
report, repair estimate, medical documentation) for completeness. A **separate statistical
fraud model** scores the claim; keeping fraud detection apart from text generation is a
deliberate design decision. The generative AI, grounded in the claimant's policy wording and the
insurer's guidelines through retrieval-augmented generation, drafts a summary, a
recommendation and an evidence-citing rationale.

The adjuster accepts, edits or overrides the draft, and every override reason is logged.
High-value and fraud-flagged claims go to a supervisor. Only the human decision (approve, deny,
request information or refer to the special investigations unit) reaches the claimant, and every
step is recorded in an immutable audit log.

The boundary is **architectural, not a policy promise**: the AI has no permission to approve a
claim, authorise a payout or contact the claimant.

## Why it matters

Today an adjuster works through police reports, repair estimates, medical documentation and the
policy wording, and writes a rationale largely from scratch for every claim. That is the
bottleneck the copilot addresses.

But the claimant, and any third party, never interacts with the AI and has almost no visibility
into how it shaped their outcome. A system that is faster but less fair, or more efficient but
less accountable, is not a neutral trade-off. It **redistributes risk onto the people least able
to see or contest it**.

## Stakeholders

| Influence over the system | Operate it | Affected by it |
| --- | --- | --- |
| Executive and claims management, AI development team, compliance, DPO, risk management, internal audit | Claims adjusters and supervisors: they run it day to day but did not design it | Claimants and third parties (the other driver, witnesses, treating physicians): no influence at all |

This asymmetry creates three tensions that run through the whole assessment:

- **Efficiency vs. fairness**
- **Fraud prevention vs. privacy**
- **Automation benefit vs. accountability.** The adjuster risks becoming a *moral crumple zone*,
  carrying full formal responsibility for a decision they did not really originate.

In each tension, the people with the least power absorb the cost when things tilt toward
efficiency.

## Ethics: five lenses, one convergence

| Lens | What it surfaces |
| --- | --- |
| **Utilitarianism** | The efficiency gains are real, but an aggregate calculation breaks down when the harm of a false fraud flag and the benefit of speed fall on different, non-overlapping groups. |
| **Deontology** | Because the AI cannot communicate a decision, a human decision-maker stays where the duty is discharged. But automation bias can violate that duty while formally respecting it, if the adjuster ratifies a pattern-based suggestion instead of considering this claimant. |
| **Virtue ethics** | What would a wise, experienced adjuster do with a fluent recommendation under caseload pressure? The design gives judgement a channel (logged overrides) but cannot manufacture it. |
| **UDHR** | Art. 7 (equality): the fraud model may inherit uneven historical scrutiny. Art. 8 (effective remedy): the claimant's explanation is mediated twice, by the AI and then the adjuster. Art. 12 (privacy): a health condition becomes more exposed once folded into a plain-language summary. |
| **Ubuntu** | Does the system sustain the relationship between insurer, adjuster and claimant, or reduce it to rubber-stamping a decision the pattern-matching already made? |

Five different logics converge on one question: **does the claimant stay visible in the
process?**

## Regulation

**EU AI Act.** Annex III lists insurance as high-risk only for risk assessment and pricing in
*life and health* insurance. It names neither claims handling nor motor insurance, so there is a
real argument this system falls outside the high-risk category, while guidance treats claims
processing as a grey zone. I leave the classification open rather than assume high-risk status
by default.
- If it is high-risk, **Art. 14(4)(b)** applies almost word for word: overseers must stay aware of
  automation bias when a system "provides recommendations for decisions to be taken by natural
  persons".
- **Art. 26** sets out the deployer's obligations: competent, trained overseers, real monitoring
  and log retention.

**GDPR.**
- A **DPIA is very likely mandatory under Art. 35**: evaluation and scoring, special-category
  data and potentially automated decision-making stack together. An outline is in
  [`docs/dpia.md`](docs/dpia.md).
- **Art. 22** turns on the CJEU *SCHUFA* test: whether the adjuster's decision "draws strongly
  upon" the AI's draft. That depends on how the system is used, not how it was designed.
- **Art. 25** (data protection by design and by default) anchors the privacy safeguards.

## Risks

![Qualitative risk landscape](figures/risk_matrix.png)

1. **Automation bias** comes first. It is the precondition for several other risks, and it is
   invisible in the system's own records: an accepted recommendation looks the same in the audit
   log whether it was scrutinised or rubber-stamped.
2. **The accountability gap** is a confirmed structural fact, not a hypothetical, and it leaves
   errors uncorrected once they happen.
3. **Unfair fraud detection** ranks high despite uncertain likelihood, because the harm is severe
   and falls on the most vulnerable people in the picture.
4. **Explainability** and **privacy misuse** form the next tier.

## Human-in-the-loop is not human-in-control

Being *in the loop* means being positioned where you could step in. Being *in control* means
exercising judgement strong enough to catch and correct the system's mistakes. The workflow
guarantees the first by design. It cannot guarantee the second, because that depends on use.

The adjuster sees a drafted summary, the fraud flags and a recommendation before forming a view,
which anchors their judgement. Override logs, escalation and the audit trail only detect
automation bias after the fact, and **a low override rate looks identical whether the AI is
accurate or nobody is checking any more**.

The same problem appears in explainability as the **citation-versus-causation gap**: a rationale
can correctly cite a real clause without that clause being why the model recommended what it
did. An adjuster who is free to override, but cannot see why the model reached its conclusion,
is not meaningfully different from one with no override right.

**Analysis: what monitoring can show.** I simulated 2,000 possible "true worlds" across wide
ranges: AI error rate 1–15%, the share of drafts genuinely reviewed 5–100%, and the chance a real
review catches an error 60–95%. For each, I simulated a month of 2,000 claims.

![Override rate vs harm, and re-review vs harm](figures/automation_bias.png)

- The **override rate has no relationship** with how many wrong drafts become decisions
  (Spearman ρ = −0.02). At a 3% override rate, anywhere from 0.05% to 13% of decisions rested
  on a wrong draft.
- **Unannounced re-review of 100 accepted decisions tracks the harm** (ρ = 0.84). That is why the
  governance design monitors accepted recommendations, not just overridden ones.

This shows what each signal *can* reveal. How carefully real adjusters review has to be measured
in a pilot.

## Fairness: averages hide who gets flagged

Overall accuracy is not enough for a fraud model. It can look well calibrated on average while
flagging one group of honest claimants far more often. The relevant metric is the
**false-positive rate by subgroup**, because a false flag causes harm (delay, scrutiny,
suspicion) even when the claim eventually clears. There is also a **feedback-loop risk**: if a
future model is retrained on outcomes of AI-influenced investigations, today's flagging pattern
becomes tomorrow's training label.

**Analysis: a fairness audit on synthetic claims.** True fraud is generated independently of
where people live. But past investigators looked at area B more often, so more of its fraud was
recorded, and area-B cars are older and cheaper.

![False-positive rate by area for four model variants](figures/fairness_fpr.png)

- Trained on those historical records, the model flags honest area-B claimants **7.6×** as often
  as area A.
- **Removing area and postcode is not enough.** Vehicle age and value predict area (AUC 0.76) and
  carry the bias: a **1.36×** gap remains (95% CI 1.21–1.52).
- **Equalising decision thresholds on an audited sample** of 2,000 randomly investigated claims
  closes the gap (1.00×).
- **Retraining on that small sample is not reliable.** It overshot to 0.77×, unfair in the
  opposite direction, and varied between 0.76× and 1.07× across draws.
- **Controls:**
  - The audit flagged 1 of 10 models trained on unbiased labels: the expected false-alarm rate.
  - The audit flagged 4 of 10 models that see area directly even with *unbiased* labels: one more
    reason to keep the feature out.
  - Sex, which carries no built-in bias, was not flagged in any model.

![Feedback loop: FPR ratio vs historical scrutiny gap](figures/feedback_loop.png)

The more uneven the past scrutiny, the more unequal the model becomes. The lesson for the
assessment: fairness has to be **measured per subgroup on outcomes that are not themselves
biased**, which requires an audited sample, not historical investigation results.

## Privacy, security and sustainability

- **Hallucination** (for example, an invented coverage term) is why generation is grounded in
  the claimant's actual policy. But grounding only fixes hallucination; it does nothing for
  automation bias or fairness.
- **Prompt injection** is a concrete risk: a submitted document could hide text designed to make
  the system reveal another claimant's information.
- **Access should match sensitivity.** A fraud investigator does not automatically need the same
  medical detail as a claims handler, and an AI-generated summary needs the same access controls
  as the medical record it was built from.
- **Sustainability.** Under stated assumptions, I estimated roughly 10.6 kg CO₂e per model
  update. That is an illustrative figure, not a measurement, since no real infrastructure data
  exists for this system. The main Green AI lever is a smaller, task-specific model: the task
  needs grounded factual precision, not broad generative ability.

## Governance

No existing function owns GenAI-specific risk for this system: not Legal and Compliance, not the
DPO, not model risk. Closing that gap takes four mechanisms, detailed in
[`docs/governance.md`](docs/governance.md):

1. **Ownership:** responsibility distributed across existing functions, plus a new coordinating
   AI Governance function, with a RACI across nine activities.
2. **Joint sign-off:** Legal & Compliance, the DPO, model risk and the AI Governance function.
3. **One monitoring programme:** override and acceptance rates, subgroup fairness metrics,
   access-log audits, and unannounced review of *accepted* recommendations.
4. **Incident response:** defined triggers (fairness disparity, privacy incident, misleading
   rationale), each with someone authorised to pause that part of the system.

## Path to deployment

1. **Pre-deployment validation:** subgroup fairness testing with pass/fail criteria set in
   advance, a scoped DPIA, testing whether cited rationales match the model's actual reasoning,
   and prompt-injection security testing.
2. **Restricted pilot:** a limited group of adjusters, special-category and fraud-flagged claims
   excluded at first, and a temporarily lower escalation threshold, to generate evidence that
   review is meaningful.
3. **Limited rollout → full deployment → ongoing monitoring**, each stage earned by evidence.

The business case is reducing adjuster workload, but genuine oversight needs review time, which
puts a floor under how much of that reduction can be realised. **Review time is a governance
control to protect**, not a cost to flex against throughput targets.

## Verdict

The design is a plausible and defensible Responsible AI design:
- Human decision authority is architecturally real.
- The fraud model is kept separate from the generative component.
- Recommendations are grounded in real policy data.
- Every action is logged immutably and attributably.

But responsible deployment cannot be confirmed yet. Fairness validation, privacy validation, real
governance ownership and evidence that human oversight is meaningful all still have to be shown
in practice.

The legal analysis, the five ethical lenses and the technical risk analysis each reach this
conditional answer independently. None of the conditions works alone: validation without
governance ownership leaves no one to act on what it finds, and governance without validation
has nothing concrete to act on.

## About the analyses

The two analyses use **synthetic claims** (`analysis/synthetic.py`) so that the true answer is
known. They show the *mechanisms* the assessment describes, not rates for any real insurer;
validating them needs an insurer's audited claims.

```bash
pip install -r requirements.txt
python -m analysis.run      # both analyses, figures and results/metrics.json (~1 min)
python -m pytest            # 5 tests
```

```text
analysis/   synthetic claims, illustrative fraud model, fairness audit, automation-bias simulation, figures
docs/       governance and RACI, DPIA outline, model card, presentation script
figures/    charts used above
results/    metrics.json from the last run
```

## Author

**Chandana Gurusiddappa** · M.Sc. Applied Data Science & Artificial Intelligence, SRH University · Regensburg, Germany

- Portfolio: [chandana18g.github.io](https://chandana18g.github.io) · [this project on the portfolio](https://chandana18g.github.io/projects/claims-copilot/)
- LinkedIn: [chandana-gurusiddappa](https://www.linkedin.com/in/chandana-gurusiddappa-785563223/)
- GitHub: [@Chandana18G](https://github.com/Chandana18G)

## Copyright

© 2026 Chandana Gurusiddappa. All rights reserved. You may view this repository, but you may not copy, reuse, modify or publish any part of it (text, code, figures or documents) without written permission. See [LICENSE](LICENSE).
