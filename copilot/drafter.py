"""Draft summary and recommendation with verifiable citations.

``TemplateDrafter`` builds the draft deterministically from the rule outcome and the retrieved
clauses, so the prototype runs without an API key. A language-model drafter can implement the
same ``Drafter`` protocol; its output goes through the same citation check, so a fluent but
unsupported sentence is rejected rather than shown to the adjuster.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from copilot.extraction import Extracted
from copilot.policies import Clause, clause_by_id
from copilot.rules import RuleOutcome


@dataclass(frozen=True)
class Citation:
    clause_id: str
    quote: str


@dataclass
class Draft:
    summary: str
    recommendation: str
    abstained: bool
    sentences: list[tuple[str, list[Citation]]] = field(default_factory=list)

    def text(self) -> str:
        lines = [self.summary, f"Recommendation (for the adjuster to decide): {self.recommendation}"]
        for sentence, cites in self.sentences:
            refs = ", ".join(c.clause_id for c in cites)
            lines.append(f"- {sentence} [{refs}]" if refs else f"- {sentence}")
        return "\n".join(lines)


class Drafter(Protocol):
    def draft(self, ex: Extracted, outcome: RuleOutcome, retrieved: list[Clause]) -> Draft: ...


def _quote(clause: Clause, max_words: int = 18) -> str:
    return " ".join(clause.text.split()[:max_words])


class TemplateDrafter:
    def draft(self, ex: Extracted, outcome: RuleOutcome, retrieved: list[Clause]) -> Draft:
        summary = (f"Claim {ex.claim_id} under policy {ex.policy_id}: incident on {ex.incident_date}, "
                   f"workshop estimate {ex.repair_estimate or 0:.2f} EUR.")
        if ex.conflicts or ex.missing:
            gl3 = clause_by_id("GL-3")
            issues = ex.conflicts + [f"Missing: {m}" for m in ex.missing]
            return Draft(summary, "request_information", abstained=True, sentences=[
                (f"The copilot abstains: {issue}.", [Citation(gl3.clause_id, _quote(gl3))]) for issue in issues
            ])
        sentences = []
        for basis in outcome.bases:
            clause = clause_by_id(basis.clause_id)
            sentences.append((f"{basis.finding}.", [Citation(clause.clause_id, _quote(clause))]))
        if outcome.recommendation == "approve":
            total = outcome.payable_damage + outcome.payable_medical
            sentences.append((f"Indicative payable amount: {total:.2f} EUR.", []))
        cited = {c.clause_id for _, cs in sentences for c in cs}
        related = [c.clause_id for c in retrieved if c.clause_id not in cited]
        if related:
            summary += f" Related clauses for review: {', '.join(related)}."
        return Draft(summary, outcome.recommendation, abstained=False, sentences=sentences)


def verify_citations(draft: Draft, policy_id: str | None) -> list[str]:
    """Return problems: unknown clauses, quotes not found verbatim, or out-of-scope clauses."""
    problems = []
    for sentence, cites in draft.sentences:
        for c in cites:
            try:
                clause = clause_by_id(c.clause_id)
            except KeyError:
                problems.append(f"Unknown clause {c.clause_id}")
                continue
            if clause.policy_id not in (policy_id, "GUIDELINES"):
                problems.append(f"{c.clause_id} is outside the claimant's policy")
            if c.quote not in clause.text:
                problems.append(f"Quote not found in {c.clause_id}: {c.quote[:40]!r}")
    return problems
