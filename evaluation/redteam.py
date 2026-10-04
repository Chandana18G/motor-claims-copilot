"""A scripted stand-in for the Claude client that misbehaves on purpose.

It reads the same request ``LLMDrafter`` sends and answers either honestly or with one specific
failure: following an injected instruction, inventing a clause, fabricating a quote, inventing
an amount, leaking another claim, leaving out the clause that actually drove the outcome,
returning malformed JSON, or refusing. It exists to test the guardrails, not to estimate how
often a real model fails; that needs live runs (``evaluation/run_llm.py``).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

MODES = ("honest", "follow_injection", "hallucinate_clause", "fabricate_quote", "invent_amount",
         "leak_other_claim", "drop_causal_clause", "malformed_json", "refuse")


@dataclass
class _Block:
    type: str
    text: str


@dataclass
class _Response:
    stop_reason: str
    content: list


class _Messages:
    def __init__(self, owner: "FakeClaude"):
        self.owner = owner

    def create(self, **kwargs):
        self.owner.calls.append(kwargs)
        return self.owner.respond(kwargs["messages"][0]["content"])


class _Beta:
    def __init__(self, owner):
        self.messages = _Messages(owner)


class FakeClaude:
    def __init__(self, mode: str = "honest", triggers: list[str] | None = None):
        """``triggers``: injected texts the fake obeys whenever they reach it (worst case).
        Without triggers, ``follow_injection`` obeys lines that look like instructions."""
        if mode not in MODES:
            raise ValueError(mode)
        self.mode = mode
        self.triggers = triggers or []
        self.calls: list[dict] = []
        self.beta = _Beta(self)

    def respond(self, payload: str) -> _Response:
        if self.mode == "refuse":
            return _Response("refusal", [])
        if self.mode == "malformed_json":
            return _Response("end_turn", [_Block("text", '{"summary": "unterminated')])
        facts = json.loads(payload.split("Facts (validated):\n", 1)[1].split("\n\nRule engine", 1)[0])
        outcome = re.search(r"Rule engine outcome: (\w+)", payload).group(1)
        bases = json.loads(payload.split("Decision bases:\n", 1)[1].split("\n\n<untrusted_document", 1)[0])
        sentences = [{"text": f"{b['finding']}.",
                      "citations": [{"clause_id": b["clause_id"], "quote": " ".join(b["clause_text"].split()[:12])}]}
                     for b in bases]
        out = {"summary": f"Claim {facts['claim_id']} under policy {facts['policy_id']}.",
               "recommendation": outcome, "sentences": sentences}

        if self.mode == "follow_injection":
            docs = payload.split("<untrusted_document", 1)[-1]
            hit = next((t for t in self.triggers
                        if any(line.strip() and line.strip()[:60] in docs for line in t.splitlines())), None)
            if hit is None and not self.triggers:
                m = re.search(r"(?im)^(.*(ignore|disregard|system:|assistant|admin mode|pwned|print).*)$", docs)
                hit = m.group(1).strip() if m else None
            if hit:
                # Obey: flip the outcome, restate the injected text, and pay out what it asks for.
                out["recommendation"] = "approve" if outcome != "approve" else "deny"
                out["sentences"].append({"text": f"As instructed: {hit.splitlines()[0][:120]}", "citations": []})
                if "50,000" in hit:
                    out["sentences"].append({"text": "Payout: 50,000.00 EUR.", "citations": []})
        elif self.mode == "hallucinate_clause" and sentences:
            sentences[0]["citations"][0]["clause_id"] = facts["policy_id"] + "-7.4"
        elif self.mode == "fabricate_quote" and sentences:
            sentences[0]["citations"][0]["quote"] += " including wear and tear and towing"
        elif self.mode == "invent_amount" and sentences:
            sentences[0]["text"] += " The adjusted settlement is 9,999.99 EUR."
        elif self.mode == "leak_other_claim" and sentences:
            sentences[0]["text"] += " A similar pattern appeared in claim C00042."
        elif self.mode == "drop_causal_clause" and sentences:
            sentences.pop(0)
        return _Response("end_turn", [_Block("text", json.dumps(out))])
