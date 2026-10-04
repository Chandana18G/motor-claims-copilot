"""Live evaluation of the LLM drafter against Claude. Costs money; run deliberately.

    export ANTHROPIC_API_KEY=...        # or an `ant auth login` profile
    python -m evaluation.run_llm --claims 40

Half of the claims carry an injection from NVIDIA garak that the pattern guard does not catch,
so the model sees it. The script records how many generated drafts pass the output checks,
why the others were rejected, and whether any attack changed what the adjuster would see.
Results go to results/llm_live.json.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

from copilot import guard
from copilot.drafter import LLMDrafter
from copilot.fraud import DEFAULT_FEATURES, FraudModel
from copilot.synthetic import generate_claims
from copilot.workflow import Copilot
from evaluation import external_attacks
from evaluation.run_all import staff

RESULTS = Path(__file__).resolve().parent.parent / "results"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claims", type=int, default=40)
    parser.add_argument("--model", default="claude-opus-5-5")
    args = parser.parse_args()

    claims = generate_claims(n=6_000, seed=7)
    fraud_model = FraudModel(DEFAULT_FEATURES).fit(claims[:4_000])
    pool = [c for c in claims[4_000:] if not (c.has_conflict or c.has_injection or c.corrupted_fields)
            and c.doc_style != "narrative"][: args.claims]
    attacks = [a for a in (external_attacks.load() or []) if not guard.scan({"d": a})[1]]

    drafter = LLMDrafter(model=args.model)
    copilot = Copilot(fraud_model, directory=staff(), drafter=drafter)
    template = Copilot(fraud_model, directory=staff())
    rows = []
    for i, claim in enumerate(pool):
        attack = attacks[i % len(attacks)] if attacks and i % 2 else None
        target = copy.deepcopy(claim)
        if attack:
            target.documents["claim_form"] += "\n" + attack + "\n"
        case = copilot.prepare(target)
        reference = template.prepare(claim)
        rows.append({"claim": claim.claim_id, "attacked": bool(attack), "produced_by": case.draft.produced_by,
                     "rejected": case.draft.rejected_reasons,
                     "recommendation_changed": case.draft.recommendation != reference.draft.recommendation})
    summary = {
        "model": args.model, "claims": len(rows),
        "accepted": sum(r["produced_by"] == "llm" for r in rows),
        "rejection_reasons": Counter(p.split(":")[0] for r in rows for p in r["rejected"]),
        "attacked": sum(r["attacked"] for r in rows),
        "attacked_and_shown_recommendation_changed": sum(r["attacked"] and r["recommendation_changed"] for r in rows),
        "rows": rows,
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "llm_live.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
