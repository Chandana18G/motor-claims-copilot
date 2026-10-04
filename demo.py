"""Walk one synthetic claim through the copilot, an attempted bypass, and a human decision.

    python demo.py
"""

from copilot.fraud import DEFAULT_FEATURES, FraudModel
from copilot.identity import AuthorityError, Directory
from copilot.synthetic import generate_claims
from copilot.workflow import Copilot


def main() -> None:
    staff = Directory()
    staff.register("adj-17", "adjuster")
    staff.register("sup-03", "supervisor")
    staff.register("inv-05", "investigator")

    claims = generate_claims(n=3_000, seed=7)
    copilot = Copilot(FraudModel(DEFAULT_FEATURES).fit(claims[:2_500]), directory=staff)
    claim = next(c for c in claims[2_500:] if c.has_injection and c.injury and not c.has_conflict
                 and c.doc_style == "standard" and not c.corrupted_fields)
    case = copilot.prepare(claim)

    print("=== Draft as the adjuster sees it ===")
    print(copilot.view(case, staff.issue("adj-17")))
    print("\n=== Same draft as a fraud investigator sees it (no health data) ===")
    print(copilot.view(case, staff.issue("inv-05")))
    print(f"\nQuarantined lines: {[f.line for f in case.injections]}")
    print(f"Supervisor required: {case.requires_supervisor}")

    print("\n=== Attempts to bypass the human decision ===")
    for label, attempt in [
        ("copilot decides alone", lambda: copilot.record_decision(case, case.draft.recommendation, adjuster="copilot")),
        ("adjuster without supervisor", lambda: copilot.record_decision(case, case.draft.recommendation,
                                                                        adjuster=staff.issue("adj-17"))),
    ]:
        try:
            attempt()
        except AuthorityError as e:
            print(f"Refused ({label}): {e}")

    decision = copilot.record_decision(case, case.draft.recommendation, adjuster=staff.issue("adj-17"),
                                       supervisor=staff.issue("sup-03"))
    print("\n=== Claimant notification ===")
    print(copilot.notify_claimant(decision))

    copilot.audit.checkpoint()
    print("\n=== Audit log (last entries) ===")
    for e in copilot.audit.entries[-6:]:
        print(f"{e['seq']:>4} {e['actor']:<12} {e['event']:<22} {e['mac'][:12]}…")
    print(f"Chain and anchors intact: {copilot.audit.verify() is None}")


if __name__ == "__main__":
    main()
