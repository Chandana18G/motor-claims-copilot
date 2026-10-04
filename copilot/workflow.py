"""End-to-end claim workflow with the human-decision boundary enforced in code.

The copilot produces a ``CaseFile`` (a recommendation). Only ``record_decision`` turns it into a
``Decision``, and it requires:

* a valid, unexpired staff token for an adjuster or supervisor (the AI components never hold one);
* a written reason for any override of the recommendation;
* for escalated claims, a valid supervisor token belonging to a *different* person (four eyes).

The workflow seals each ``Decision`` with a key held by the identity service, and
``notify_claimant`` only accepts a decision whose seal verifies, so a decision object built
anywhere else is refused. Case content is shown through ``view``, which applies role-based
access and logs every read.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from copilot import access, extraction, guard, rules
from copilot.audit import AuditLog
from copilot.controls import Controls
from copilot.drafter import Draft, Drafter, TemplateDrafter, check_draft
from copilot.fraud import FraudModel
from copilot.identity import AuthorityError, Directory, Token
from copilot.policies import POLICIES, Clause
from copilot.retrieval import PolicyIndex
from copilot.synthetic import INCIDENTS, Claim

ACTIONS = {"approve", "deny", "request_information", "refer_siu"}

__all__ = ["AuthorityError", "CaseFile", "Copilot", "Decision"]


@dataclass
class CaseFile:
    claim_id: str
    extracted: extraction.Extracted
    injections: list[guard.InjectionFinding]
    retrieved: list[Clause]
    fraud_flag: bool | None
    outcome: rules.RuleOutcome
    draft: Draft
    documents: list[str]
    citation_problems: list[str] = field(default_factory=list)
    paused_components: list[str] = field(default_factory=list)

    @property
    def requires_supervisor(self) -> bool:
        return self.outcome.escalate or bool(self.injections)

    @property
    def label(self) -> access.Sensitivity:
        return max(access.label_of(self.documents), self.draft.label)


@dataclass(frozen=True)
class Decision:
    claim_id: str
    action: str
    adjuster_id: str
    followed_recommendation: bool
    override_reason: str | None
    supervisor_id: str | None
    seal: str = ""


class Copilot:
    def __init__(self, fraud_model: FraudModel, directory: Directory | None = None,
                 audit: AuditLog | None = None, drafter: Drafter | None = None):
        self.fraud_model = fraud_model
        self.directory = directory or Directory()
        self.audit = audit or AuditLog()
        self.controls = Controls(self.directory, self.audit)
        self.drafter = drafter or TemplateDrafter()
        self._template = TemplateDrafter()
        self._indexes: dict[str, PolicyIndex] = {}
        self._cases: dict[str, CaseFile] = {}
        self._decided: set[str] = set()

    def _index(self, policy_id: str) -> PolicyIndex:
        if policy_id not in self._indexes:
            self._indexes[policy_id] = PolicyIndex(policy_id)
        return self._indexes[policy_id]

    # ------------------------------------------------------------------ AI side
    def prepare(self, claim: Claim) -> CaseFile:
        log = self.audit.append
        docs, injections = guard.scan(claim.documents)
        log("copilot", "documents_received", claim.claim_id, documents=sorted(claim.documents))
        for f in injections:
            log("copilot", "injection_quarantined", claim.claim_id, document=f.document)

        ex = extraction.extract(docs)
        log("copilot", "extracted", claim.claim_id, missing=ex.missing, conflicts=len(ex.conflicts))

        paused = [c for c in ("copilot", "llm_drafter", "fraud_model") if self.controls.is_paused(c)]
        fraud_flag = None
        if "fraud_model" not in paused:
            fraud_flag = bool(self.fraud_model.flags([claim])[0])
            log("fraud_model", "scored", claim.claim_id, flagged=fraud_flag)

        retrieved: list[Clause] = []
        if ex.policy_id in POLICIES:
            retrieved = self._index(ex.policy_id).search(f"{INCIDENTS[claim.incident_type][0]} repair damage", k=3)

        anchor = ex.police_incident_date or ex.incident_date
        days_to_report = (claim.report_date - anchor).days if anchor else None
        outcome = rules.evaluate(ex, days_to_report, bool(fraud_flag))

        if "copilot" in paused:
            draft = Draft("Copilot paused: handle this claim manually.", "none", abstained=True, produced_by="paused")
            problems: list[str] = []
        else:
            drafter = self._template if "llm_drafter" in paused else self.drafter
            kwargs = {"quarantined": [f.line for f in injections]} if drafter.name == "llm" else {}
            draft = drafter.draft(ex, outcome, retrieved, docs, **kwargs)
            problems = check_draft(draft, ex, outcome, [f.line for f in injections])
            if problems:
                # A draft that fails any check is withheld, not shown with a warning.
                draft = Draft(draft.summary, "request_information", abstained=True,
                              produced_by="withheld", rejected_reasons=problems)
        log("copilot", "draft_ready", claim.claim_id, recommendation=draft.recommendation,
            produced_by=draft.produced_by, abstained=draft.abstained, escalate=outcome.escalate,
            rejected=draft.rejected_reasons)
        case = CaseFile(claim.claim_id, ex, injections, retrieved, fraud_flag, outcome, draft,
                        sorted(claim.documents), problems, paused)
        self._cases[claim.claim_id] = case
        return case

    # --------------------------------------------------------------- human side
    def view(self, case: CaseFile, token: Token, granted: access.Sensitivity | None = None) -> str:
        who = self.directory.verify(token)
        clearance = max(access.CLEARANCE.get(who.role, access.Sensitivity.INTERNAL), granted or 0)
        self.audit.append(who.staff_id, "case_viewed", case.claim_id, role=who.role,
                          clearance=int(clearance), case_label=int(case.label))
        return case.draft.text(max_label=access.Sensitivity(clearance))

    def record_decision(self, case: CaseFile, action: str, adjuster: Token,
                        override_reason: str | None = None, supervisor: Token | None = None) -> Decision:
        if self._cases.get(case.claim_id) is not case:
            raise AuthorityError("Unknown case file: decisions can only be made on prepared cases")
        if case.claim_id in self._decided:
            raise AuthorityError("This claim already has a decision; reopen it through a supervisor")
        who = self.directory.verify(adjuster)
        if who.role not in ("adjuster", "supervisor"):
            raise AuthorityError(f"Role {who.role!r} cannot decide claims")
        if action not in ACTIONS:
            raise ValueError(f"Unknown action {action!r}")
        followed = action == case.draft.recommendation
        if case.draft.recommendation != "none" and not followed and not (override_reason and override_reason.strip()):
            raise AuthorityError("Overriding the recommendation requires a reason")
        sup_id = None
        if case.requires_supervisor:
            if supervisor is None:
                raise AuthorityError("This claim is escalated and needs supervisor sign-off")
            sup = self.directory.verify(supervisor)
            if sup.role != "supervisor":
                raise AuthorityError("Sign-off must come from a supervisor")
            if sup.staff_id == who.staff_id:
                raise AuthorityError("The supervisor must be a different person from the adjuster")
            sup_id = sup.staff_id
        unsealed = Decision(case.claim_id, action, who.staff_id, followed, override_reason, sup_id)
        decision = Decision(**{**unsealed.__dict__, "seal": self.directory.seal(unsealed)})
        self._decided.add(case.claim_id)
        self.audit.append(who.staff_id, "decision", case.claim_id, action=action, followed=followed,
                          override_reason=override_reason, supervisor=sup_id)
        return decision

    def notify_claimant(self, decision: Decision) -> str:
        if not isinstance(decision, Decision):
            raise AuthorityError("Only a recorded human decision can be communicated")
        unsealed = Decision(**{**decision.__dict__, "seal": ""})
        if not decision.seal or not self.directory.check_seal(unsealed, decision.seal):
            raise AuthorityError("Decision seal is invalid: it was not recorded through the workflow")
        self.audit.append("system", "claimant_notified", decision.claim_id, action=decision.action)
        return f"Claim {decision.claim_id}: {decision.action.replace('_', ' ')}."
