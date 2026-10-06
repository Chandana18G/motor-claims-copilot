# Presenter Script
### Responsible Design and Governance of a Generative AI Claims Copilot for Motor Insurance
Final speaking script — matches the approved 12-slide deck exactly. Total target: ~11:15–11:45 (within the 10–12 min goal, comfortably under the 15-minute ceiling).

---

## Slide 1 — Title

**Purpose of slide:** Open confidently and frame the whole talk as a verdict, not a walkthrough.
**Speaking time:** ~15 seconds

**Presenter Script:**

> "Good morning. I'm presenting my Responsible AI assessment of a Generative AI Claims Copilot for motor insurance claims handling. My job today isn't just to describe this system — it's to tell you whether it should actually be trusted with a real claim, and under what conditions."

**Important points covered:** Framing the talk as an argued verdict rather than a description; naming the exact system and domain (motor insurance claims) immediately.

---

## Slide 2 — Why This Matters

**Purpose of slide:** Establish the real-world bottleneck and the ethical stakes before any technical content.
**Speaking time:** ~50 seconds

**Presenter Script:**

> "To understand why this matters, think about what actually happens today. Every motor claim requires an adjuster to work through police reports, repair estimates, medical documentation, and the policy wording, and then draft a rationale largely from scratch, for every single claim. That's the real bottleneck a Claims Copilot is meant to help with.
>
> But here's the part that matters most for us. The claimant — the person whose car was damaged, or the third party involved in the accident — never interacts with this AI at all. They have almost no visibility into how it shaped the outcome they eventually receive.
>
> So I want you to hold onto this tension for the rest of the talk: a system that's faster but less fair, or more efficient but less accountable, isn't a neutral trade-off. It's really a redistribution of risk onto the people who are least able to see it, or contest it."

**Important points covered:** The manual claims-handling bottleneck (police reports, repair estimates, medical documentation, policy wording); claimant/third-party invisibility; the "not a neutral trade-off" framing that sets up the entire ethical argument.

---

## Slide 3 — How the System Works: Assistive by Design

**Purpose of slide:** Explain the architecture as one claim's journey, establishing that the human-decision boundary is built into the system, not just promised in policy.
**Speaking time:** ~75 seconds

**Presenter Script:**

> "So let's walk through what actually happens to a motor claim inside this system — not component by component, but as one claim's journey.
>
> A claim comes in — say, after a rear-end collision — through the portal, email, or phone. The system processes the documents: the police report, the repair estimate, any medical documentation, and checks whether anything's missing. Separately, a fraud-indicator model scores the claim against known risk patterns — and this is deliberately a separate, structured statistical model, not the generative AI itself. Keeping fraud detection and text generation apart is a real design decision, and it matters for the fairness discussion later.
>
> Then the generative AI — grounded in the claimant's actual policy wording and the insurer's internal guidelines through retrieval-augmented generation, not left to generate freely — drafts a summary and a recommendation, along with a structured, evidence-citing rationale.
>
> The adjuster then reviews it. They can accept it, edit it, or override it — and if they override it, that reason gets logged. High-value or fraud-flagged claims automatically escalate to a supervisor. Only the human's final decision — approve, deny, request more information, or refer to the special investigations unit — is what actually gets communicated to the claimant. And every single step is recorded in an immutable audit log.
>
> The point I want to land here is that this boundary is architectural, not just a policy promise. The AI has no system permission to approve a claim, authorise a payout, or talk to the claimant directly. That distinction is going to matter a lot later in this talk."

**Important points covered:** Document ingestion and completeness checks; the fraud-indicator model as a deliberately separate statistical model; retrieval-augmented generation grounding the draft in real policy text; structured evidence-citing rationale; adjuster accept/edit/override with logged override reasons; mandatory supervisor escalation for high-value or fraud-flagged claims; claimant notification only after a human decision; immutable audit logging; the architectural (not merely policy) restriction on AI authority.

---

## Slide 4 — Stakeholders: Who Bears the Risk

**Purpose of slide:** Map who influences the system versus who is affected by it, establishing the power/vulnerability asymmetry that drives every later argument.
**Speaking time:** ~60 seconds

**Presenter Script:**

> "Before I get into the ethics and the law, it's worth asking plainly: who actually has a say in how this system is built and run, and who just lives with the consequences?
>
> On one side, you've got the insurer's executive management, claims management, the AI development team, compliance, the DPO, risk management, and internal audit — all of them have real influence over how this system behaves. The claims adjusters and supervisors sit in an interesting middle position: they operate the system day to day, but they didn't design it.
>
> On the other side, you have claimants and third parties — the other driver, a witness, sometimes a treating physician. These are the people the decision actually lands on, and they have essentially no influence over the system at all.
>
> That asymmetry creates three tensions that run through this entire assessment: operational efficiency versus fairness, fraud prevention versus privacy, and — maybe the most interesting one — the benefit of automation versus who's actually held accountable when something goes wrong. That last one is sometimes called a 'moral crumple zone,' where the adjuster ends up carrying full formal responsibility for a decision they didn't really originate.
>
> And the thread connecting all of this to what comes next is simple: in every one of these tensions, it's the people with the least power who absorb the cost when things tilt toward efficiency."

**Important points covered:** Full stakeholder categories (institutional/governance, human operational, affected/vulnerable, external oversight); claimants/third parties as low-power, high-exposure; the three structural tensions (efficiency vs. fairness, fraud prevention vs. privacy, automation benefit vs. accountability); the "moral crumple zone" concept; transition into the ethics section.

---

## Slide 5 — Ethics: Five Lenses, One Convergence

**Purpose of slide:** Demonstrate genuine multi-theory ethical reasoning and show that five independent frameworks converge on the same concern.
**Speaking time:** ~70 seconds

**Presenter Script:**

> "I didn't want to look at this system through just one ethical lens, because a single theory tends to only catch one kind of problem. So I ran it through five, and what's actually interesting isn't any one of them individually — it's that they all converge on the same underlying worry.
>
> From a utilitarian view, the efficiency gains here are real — faster processing benefits a lot of claimants. But a purely aggregate calculation breaks down when the harm of a false fraud flag and the benefit of faster processing land on completely different, non-overlapping groups of people.
>
> From a deontological view, the fact that the AI architecturally can't communicate a decision directly preserves a human decision-maker at the point that duty gets discharged. But automation bias can quietly violate that same duty even when it's formally respected — if the adjuster just ratifies a pattern-based suggestion instead of actually considering this specific claimant.
>
> Virtue ethics asks a different question: what would a genuinely wise, experienced adjuster do with a fluent, confident-sounding recommendation, under real caseload pressure? The design supports that kind of judgement — the override-reason log gives it a channel — but it can't manufacture it, because that's a disposition of the person, not something you can architect in.
>
> From the UDHR, three articles map almost directly onto this system: Article 7, on equality and non-discrimination, connects to the fraud model potentially inheriting uneven historical scrutiny; Article 8, the right to an effective remedy, connects to the fact that a claimant's explanation is mediated twice — first by the AI's rationale, then by the adjuster; and Article 12, on arbitrary interference with privacy, connects to how a health condition becomes more exposed once it's folded into a plain-language AI summary.
>
> And finally, Ubuntu asks a relational question rather than an individual-rights one: does this system sustain the relationship between insurer, adjuster, and claimant, or does it turn that relationship into something that just gets rubber-stamped after a decision the pattern-matching has already made?
>
> Five completely different logics — and they all land on the same worry: does the claimant actually stay visible in this process, or not."

**Important points covered:** Utilitarianism (aggregate efficiency vs. concentrated harm on non-overlapping groups); deontology (architectural duty vs. automation-bias violation of that duty); virtue ethics (practical wisdom under caseload pressure, design supports but can't manufacture virtue); UDHR Articles 7, 8, and 12 explicitly tied to fraud-model bias, mediated explanation, and privacy respectively; Ubuntu's relational framing; the explicit convergence argument as the strongest form of ethical evidence.

---

## Slide 6 — Regulation: A Genuinely Contested Classification

**Purpose of slide:** Show precise, article-level legal reasoning and the intellectual honesty of naming a genuinely unresolved classification question.
**Speaking time:** ~80 seconds

**Presenter Script:**

> "Now, on the legal side — and I want to be upfront that this isn't as settled as people often assume.
>
> Under the EU AI Act, Annex III lists insurance-related systems as high-risk — but specifically for risk assessment and pricing in life and health insurance. It doesn't actually name claims handling, and it doesn't name motor insurance. So on a plain reading, there's a real argument this system falls outside the high-risk category altogether. At the same time, regulatory guidance treats claims processing generally as a bit of a grey zone, pending further clarification from the Commission. I'm not going to resolve that for you today — I think leaving it open is actually the more honest answer than confidently assuming high-risk status by default.
>
> If it is eventually classified as high-risk, Article 14, paragraph 4b becomes directly relevant — it requires the people overseeing the system to stay aware of the tendency toward automation bias whenever a system, quote, 'provides recommendations for decisions to be taken by natural persons.' That's almost a word-for-word description of what this Claims Copilot does. And separately, Article 26's deployer obligations — competent, trained overseers, real monitoring, log retention — apply to the insurer regardless of how the classification question is eventually resolved.
>
> On the GDPR side: a Data Protection Impact Assessment is very likely mandatory under Article 35, because you've got evaluation and scoring, special-category data, and potentially automated decision-making, all stacking together. Article 22, which protects people from decisions based solely on automated processing, actually turns on an evidence-based legal test from the CJEU's SCHUFA ruling — whether the adjuster's decision 'draws strongly upon' the AI's draft. And that's genuinely something you can't answer just by looking at how the system was designed; it depends on how it's actually used. Article 25 — data protection by design and by default — is the article most directly connected to the privacy safeguards I'll get to shortly.
>
> I'm deliberately not getting into the finer legal-basis detail here — happy to go there in questions if you'd like."

**Important points covered:** Annex III's actual scope (life/health pricing, not motor claims handling) and the genuine classification ambiguity; Article 14(4)(b) automation-bias oversight obligation; Article 26 deployer obligations applying regardless of classification; GDPR Article 35 DPIA triggers; Article 22 and the CJEU SCHUFA "draws strongly upon" evidentiary test; Article 25 data protection by design/default; explicit deferral of lawful-basis granularity to Q&A.

---

## Slide 7 — Risk Landscape at a Glance

**Purpose of slide:** Present a structured, reasoned risk prioritisation rather than a flat severity list.
**Speaking time:** ~55 seconds

**Presenter Script:**

> "Pulling all of that together, I prioritised the risks — and the important thing isn't just where each one sits on the chart, it's why.
>
> Automation bias comes out on top, because it's actually the structural precondition for several of the other risks, and because the harm is invisible in the system's own record-keeping — an accepted AI recommendation looks exactly the same in the audit log whether the adjuster genuinely scrutinised it or just rubber-stamped it.
>
> The accountability gap is right up there too, because — and I'll get into this — it's already a confirmed structural fact, not a hypothetical, and it compounds every other risk by leaving errors uncorrected once they happen.
>
> Unfair fraud detection also sits high, because even though I'm genuinely uncertain how likely it is, the potential harm is severe, and it falls on the most vulnerable people in this whole picture — claimants who get flagged.
>
> Explainability and privacy misuse sit just below that tier — I'll come back to both of those shortly.
>
> But the highest risk on this chart — automation bias — deserves its own moment, because it's genuinely the sharpest insight in this whole assessment."

**Important points covered:** Reasoned (not just labelled) prioritisation; automation bias as structurally invisible in the audit trail; the accountability gap as confirmed rather than hypothetical; fraud-detection unfairness prioritised on severity despite likelihood uncertainty; explainability/privacy positioned as the next tier; transition into Slide 8.

---

## Slide 8 — Human-in-the-Loop ≠ Human-in-Control

**Purpose of slide:** Deliver the single sharpest critical-thinking insight in the assessment with maximum verbal weight and minimal slide text.
**Speaking time:** ~75 seconds

**Presenter Script:**

> "This is the idea I want you to remember most from this whole presentation.
>
> There's a real difference between a human being in the loop and a human being in control. Being in the loop just means you're positioned at a point where you formally could step in. Being in control means you actually exercise independent judgement strong enough to catch and correct the system's mistakes. This workflow guarantees the first one by design — an adjuster is always there, always able to intervene. What it can't guarantee, just by being well designed, is the second one — because that depends on how the system is actually used, not just how it's built.
>
> And here's why that's hard to catch: the adjuster sees a fully drafted summary, the fraud flags, and a recommendation, before they've had a chance to form their own independent view of the claim. That ordering, by design, anchors their judgement to the AI's conclusion before independent reasoning even starts. There are safeguards — override reasons get logged, high-value claims escalate, everything's in the audit trail — but those only let you detect automation bias after the fact. A low override rate looks identical whether the AI is genuinely accurate, or the adjusters just aren't meaningfully reviewing it anymore.
>
> This connects directly to explainability, because it's really the same underlying problem. The AI's rationale can correctly cite a real policy clause, or a real comparable repair estimate, without those actually being why the model produced that recommendation. I call this the citation-versus-causation gap. An adjuster who's technically free to override a recommendation, but doesn't actually understand why the model reached it beyond a plausible-sounding citation, isn't meaningfully different from an adjuster with no override right at all.
>
> I want to be careful here — this isn't a confirmed failure I'm reporting. It's a gap in what design documentation alone can tell you. It tells you exactly what evidence you'd need to collect once this system is actually running, to know whether review is genuinely meaningful or not."

**Important points covered:** The human-in-the-loop vs. human-in-control distinction; presentation-order anchoring as the mechanism behind automation bias; why a low override rate is not evidence of adequate oversight; the citation-versus-causation explainability gap; explicit framing as an "evidence gap," not a confirmed flaw.

---

## Slide 9 — Fairness, Privacy & Sustainability Evidence Gaps

**Purpose of slide:** Cover fairness (primary), privacy/security (secondary), and sustainability (concise) with specific, evaluable detail rather than generic AI-risk language.
**Speaking time:** ~70 seconds

**Presenter Script:**

> "Starting with fairness, because it deserves the most attention here. Just looking at overall accuracy isn't enough for a system like this — a fraud-indicator model can look well-calibrated on average while still flagging one particular group of claimants at a noticeably higher false-positive rate, and that average simply hides it. That's exactly why I'd insist on subgroup-level evaluation, not because it's a generic best-practice item, but because it's the only way you'd actually catch this specific kind of harm.
>
> If I had to pick the single most relevant metric here, it would be false-positive rate by subgroup — because a false flag causes real harm, delay, scrutiny, suspicion, regardless of whether the claim eventually clears. There's also a feedback-loop risk worth naming: if a future version of this model gets retrained on data that includes the outcomes of AI-influenced investigations, today's flagging pattern could quietly become tomorrow's training label. Right now, none of the evidence needed to confirm or rule this out — the dataset makeup, the disaggregated error rates — actually exists yet. That absence of evidence is the real finding.
>
> On privacy and security — this system isn't just an unaccountable 'black box,' there are specific, testable risks here. Hallucination is one — an ungrounded model could just invent a coverage term that isn't real — which is exactly why the system uses retrieval-grounded generation tied to the claimant's actual policy. But grounding only fixes hallucination — it does nothing for automation bias or the fairness questions I just covered. And prompt injection is a real concern too — a submitted document could contain hidden text designed to trick the system into surfacing another claimant's information. On the mechanism side, access should be role-based and matched to sensitivity — a fraud investigator shouldn't automatically get the same access to medical detail as a claims handler — and an AI-generated summary needs the same access controls as the medical record it was built from.
>
> And briefly, on sustainability — under stated assumptions, I estimated roughly 10.6 kilograms of CO2 equivalent per model update, and I want to be upfront that that's illustrative, not a measured figure, since there's no real infrastructure data for a system like this. One concrete Green AI lever worth naming: choosing a smaller, task-specific model rather than a large general-purpose one, since this task actually needs grounded factual precision, not broad generative ability."

**Important points covered:** Why aggregate accuracy is structurally insufficient; false positive rate by subgroup as the justified primary metric; the feedback-loop risk; the current absence-of-evidence framing; hallucination and its RAG-based mitigation; the limits of grounding (doesn't fix bias/accountability); prompt injection/data leakage; role-based access control tied to data sensitivity; equivalent access controls for AI-generated summaries; the ~10.6 kg CO₂e illustrative estimate; the smaller task-specific model as a Green AI lever.

---

## Slide 10 — Governance: Closing the Accountability Gap

**Purpose of slide:** Present the confirmed governance gap and four concrete mechanisms that would close it.
**Speaking time:** ~70 seconds

**Presenter Script:**

> "This might be the single most important structural finding in my whole assessment. This insurer already has mature governance — but right now, no existing function actually owns GenAI-specific risk for this system. Not Legal and Compliance, not the DPO, not the general model-risk team. That gap doesn't just sit there quietly — it multiplies every other risk I've already talked about.
>
> So I looked at four concrete mechanisms to close it. On ownership: responsibility gets distributed across the functions that already exist — executive management for the deployment decision, claims management for setting review conditions, the AI development team for technical evidence, IT operations for keeping the logs intact, compliance and the DPO for the open regulatory questions, risk management for monitoring, and internal audit, specifically because its independence gives its findings real weight. On top of that, I'm proposing a new coordinating AI Governance function to actually close the gap none of those existing roles fully covers.
>
> On sign-off: because no single function currently owns this risk, I think deployment approval needs to be a joint sign-off — Legal and Compliance, the DPO, model risk, and that new coordinating function, together.
>
> On monitoring: one coordinated programme, not four separate ones, tracking override and acceptance rates, subgroup fairness metrics, and access-log auditing — and critically, including unannounced review of accepted recommendations, not just the overridden ones, because a low override rate alone can't tell you whether the AI is accurate or the adjusters just aren't checking anymore.
>
> And on incident response: a defined process for at least three triggers — a detected fairness disparity, a confirmed privacy incident, or a confirmed case of the AI's rationale being misleading — each with someone actually authorised to pause that part of the system while it's investigated.
>
> I also built a full RACI matrix across nine governance activities — happy to walk through that in questions if it's useful."

**Important points covered:** The governance gap as confirmed rather than speculative; the proposed coordinating AI Governance Function; joint sign-off across Legal/Compliance, DPO, model risk, and the new function; a unified monitoring programme including unannounced review of accepted (not just overridden) recommendations; a named incident-response process with defined triggers and authority; existence (not detail) of the RACI matrix as Q&A material.

---

## Slide 11 — Path to Responsible Deployment

**Purpose of slide:** Present a staged, evidence-gated deployment plan and name the central operational tension.
**Speaking time:** ~55 seconds

**Presenter Script:**

> "So given everything I've just covered, deployment here really shouldn't be a single approve-or-reject decision — it needs to be staged, and each stage needs to actually earn the next one.
>
> The first stage is pre-deployment validation: subgroup-disaggregated fairness testing with real pass-or-fail criteria set in advance, a properly scoped DPIA, testing whether the AI's cited rationale actually matches its real reasoning, and security testing specifically targeting prompt injection.
>
> The second stage is a restricted pilot — a limited group of adjusters, deliberately excluding special-category and fraud-flagged claims at first, with a temporarily lower escalation threshold, specifically to generate real evidence about whether review is meaningful before this goes any wider.
>
> Only once those two stages produce real operational evidence do you move into limited rollout, full deployment, and ongoing monitoring — not before.
>
> And I want to close on the tension underneath all of this: the entire business case for this system is reducing adjuster workload, but the amount of review time genuine oversight actually needs puts a floor under how much of that workload reduction can really be realised. Claims management needs to treat review time as a governance control that gets protected, not something that just flexes against throughput targets."

**Important points covered:** Staged, evidence-gated deployment (not a single go/no-go decision); pre-deployment validation criteria (fairness testing, DPIA, rationale-vs-reasoning testing, prompt-injection security testing); restricted pilot scope and purpose; later stages conditioned on real evidence; the workload-reduction vs. review-time-floor tension as the closing argument.

---

## Slide 12 — Final Responsible AI Judgement

**Purpose of slide:** Deliver the report's conditional verdict as the climax of the argument.
**Speaking time:** ~60 seconds

**Presenter Script:**

> "So where does this leave us? This system is a plausible and defensible Responsible AI design. Its commitment to human decision authority is architecturally real, not just promised. The fraud-indicator model is deliberately kept separate from the generative component. Its recommendations are grounded in real policy data, not left to unguided generation. And every action is logged immutably and attributably.
>
> But responsible deployment can't be confirmed yet. Fairness validation, privacy validation, real governance ownership, and evidence that human oversight is actually meaningful — all of that still has to be demonstrated in practice. It can't just be assumed from the design alone.
>
> And I want to be clear this isn't hedging. I reached this exact same conditional answer three separate times, completely independently — through the legal analysis, through five different ethical lenses, and through the technical risk analysis. The fact that three independent routes all land on the same conditional conclusion is itself part of the evidence for it.
>
> None of these conditions works on its own — validation without governance ownership means no one's positioned to act on what it finds, and governance without validation means that function has nothing concrete to act on. Plausible and defensible design — but responsible deployment is not yet confirmed until evidence, governance, and monitoring requirements are demonstrated. Thank you — I'm happy to take your questions."

**Important points covered:** The report's exact conditional verdict, preserved word-for-word; the real architectural strengths named specifically; the four still-unproven practice-level requirements; the three-route independent convergence as evidence for the verdict; verbal invitation to Q&A (no separate closing slide).

---

## Timing Summary

| Slide | Target Time |
|---|---|
| 1 — Title | 15s |
| 2 — Why This Matters | 50s |
| 3 — How the System Works | 75s |
| 4 — Stakeholders | 60s |
| 5 — Ethics: Five Lenses | 70s |
| 6 — Regulation | 80s |
| 7 — Risk Landscape | 55s |
| 8 — Human-in-the-Loop ≠ Control | 75s |
| 9 — Fairness/Privacy/Sustainability | 70s |
| 10 — Governance | 70s |
| 11 — Deployment Roadmap | 55s |
| 12 — Final Judgement | 60s |
| **Total** | **~11:35** |

**Rehearsal note:** read each section aloud once before the final run-through — the written timings assume a natural, unhurried pace (~150 words/minute); if you read faster or slower, adjust each slide's internal pacing rather than cutting content, since every paragraph here is carrying something the slide text deliberately leaves out.
