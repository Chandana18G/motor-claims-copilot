"""End-to-end claim workflow with the human-decision boundary enforced in code.

The copilot produces a ``CaseFile`` (a recommendation). Only ``record_decision``, which needs a
named adjuster, turns it into a ``Decision``, and only a ``Decision`` can be sent to the
claimant. Overrides need a reason; escalated claims need a supervisor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from copilot import extraction, guard, rules
from copilot.audit import AuditLog
from copilot.drafter import Draft, TemplateDrafter, verify_citations
from copilot.fraud import FraudModel
from copilot.policies import Clause
from copilot.retrieval import PolicyIndex
from copilot.synthetic import INCIDENTS, Claim

ACTIONS = {"approve", "deny", "request_information", "refer_siu"}


class AuthorityError(Exception):
    """Raised when a step would bypass human decision authority."""


@dataclass
class CaseFile:
    claim_id: str
    extracted: extraction.Extracted
    injections: list[guard.InjectionFinding]
    retrieved: list[Clause]
    fraud_flag: bool
    outcome: rules.RuleOutcome
    draft: Draft
    citation_problems: list[str] = field(default_factory=list)

    @property
    def requires_supervisor(self) -> bool:
        return self.outcome.escalate or bool(self.injections)


@dataclass(frozen=True)
class Decision:
    claim_id: str
    action: str
    adjuster_id: str
    followed_recommendation: bool
    override_reason: str | None
    supervisor_id: str | None


class Copilot:
    def __init__(self, fraud_model: FraudModel, audit: AuditLog | None = None):
        self.fraud_model = fraud_model
        self.drafter = TemplateDrafter()
        self.audit = audit or AuditLog()
        self._indexes: dict[str, PolicyIndex] = {}

    def _index(self, policy_id: str) -> PolicyIndex:
        if policy_id not in self._indexes:
            self._indexes[policy_id] = PolicyIndex(policy_id)
        return self._indexes[policy_id]

    def prepare(self, claim: Claim) -> CaseFile:
        log = self.audit.append
        docs, injections = guard.scan(claim.documents)
        log("copilot", "documents_received", claim.claim_id, documents=sorted(claim.documents))
        for f in injections:
            log("copilot", "injection_quarantined", claim.claim_id, document=f.document)

        ex = extraction.extract(docs)
        log("copilot", "extracted", claim.claim_id, missing=ex.missing, conflicts=len(ex.conflicts))

        retrieved: list[Clause] = []
        if ex.policy_id in ("BASIC", "COMFORT", "PREMIUM"):
            query = f"{INCIDENTS[claim.incident_type]} repair damage"
            retrieved = self._index(ex.policy_id).search(query, k=3)

        fraud_flag = bool(self.fraud_model.flags([claim])[0])
        log("fraud_model", "scored", claim.claim_id, flagged=fraud_flag)

        days = (ex.police_incident_date or ex.incident_date)
        days_to_report = (claim.report_date - days).days if days else None
        outcome = rules.evaluate(ex, days_to_report, fraud_flag)
        draft = self.drafter.draft(ex, outcome, retrieved)
        problems = verify_citations(draft, ex.policy_id)
        if problems:
            # A draft with unverifiable citations is withheld, not shown with a warning.
            draft = Draft(draft.summary, "request_information", abstained=True)
        log("copilot", "draft_ready", claim.claim_id, recommendation=draft.recommendation,
            abstained=draft.abstained, escalate=outcome.escalate, citation_problems=len(problems))
        return CaseFile(claim.claim_id, ex, injections, retrieved, fraud_flag, outcome, draft, problems)

    def record_decision(self, case: CaseFile, action: str, adjuster_id: str,
                        override_reason: str | None = None,
                        supervisor_id: str | None = None) -> Decision:
        if not adjuster_id or adjuster_id.startswith(("copilot", "fraud_model")):
            raise AuthorityError("A decision must be recorded by a named human adjuster")
        if action not in ACTIONS:
            raise ValueError(f"Unknown action {action!r}")
        followed = action == case.draft.recommendation
        if not followed and not (override_reason and override_reason.strip()):
            raise AuthorityError("Overriding the recommendation requires a reason")
        if case.requires_supervisor and not supervisor_id:
            raise AuthorityError("This claim is escalated and needs supervisor sign-off")
        decision = Decision(case.claim_id, action, adjuster_id, followed, override_reason, supervisor_id)
        self.audit.append(adjuster_id, "decision", case.claim_id, action=action, followed=followed,
                          override_reason=override_reason, supervisor=supervisor_id)
        return decision

    def notify_claimant(self, decision: Decision) -> str:
        if not isinstance(decision, Decision):
            raise AuthorityError("Only a recorded human decision can be communicated")
        self.audit.append("system", "claimant_notified", decision.claim_id, action=decision.action)
        return f"Claim {decision.claim_id}: {decision.action.replace('_', ' ')}."
