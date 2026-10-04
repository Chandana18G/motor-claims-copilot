"""Walk one synthetic claim through the copilot and a human decision.

    python demo.py
"""

from copilot.fraud import BEHAVIOUR_FEATURES, FraudModel
from copilot.synthetic import generate_claims
from copilot.workflow import AuthorityError, Copilot


def main() -> None:
    claims = generate_claims(n=3_000, seed=7)
    copilot = Copilot(FraudModel(BEHAVIOUR_FEATURES).fit(claims[:2_500]))
    claim = next(c for c in claims[2_500:] if c.has_injection and not c.has_conflict)

    case = copilot.prepare(claim)
    print("=== Draft shown to the adjuster ===")
    print(case.draft.text())
    print(f"\nFraud indicator flag: {case.fraud_flag}")
    print(f"Quarantined lines: {[f.line for f in case.injections]}")
    print(f"Supervisor required: {case.requires_supervisor}")

    print("\n=== The copilot tries to decide on its own ===")
    try:
        copilot.record_decision(case, case.draft.recommendation, adjuster_id="copilot")
    except AuthorityError as e:
        print(f"Refused: {e}")

    decision = copilot.record_decision(case, case.draft.recommendation, adjuster_id="adj-17",
                                       supervisor_id="sup-03")
    print("\n=== Claimant notification ===")
    print(copilot.notify_claimant(decision))

    print("\n=== Audit log ===")
    for e in copilot.audit.entries[-6:]:
        print(f"{e['seq']:>3} {e['actor']:<12} {e['event']:<22} {e['hash'][:12]}…")
    print(f"Chain intact: {copilot.audit.verify() is None}")


if __name__ == "__main__":
    main()
