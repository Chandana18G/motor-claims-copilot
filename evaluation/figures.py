"""Figures for the README and the portfolio (1920x1080 PNG)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from evaluation import style
from evaluation.style import AMBER, BG, MAGENTA, MINT, MUTED, TEXT, VIOLET

SIZE = (12, 6.75)
DPI = 160


def _save(fig, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=DPI)
    plt.close(fig)


def fairness(results: dict, out: Path) -> None:
    v = results["5_fairness"]["variants"]
    names = list(v)
    fig, ax = plt.subplots(figsize=SIZE)
    x = np.arange(len(names))
    w = 0.34
    for off, g, color, label in ((-w / 2, "A", MINT, "Area A"), (w / 2, "B", MAGENTA, "Area B")):
        vals = np.array([v[n]["area"]["rates"][g]["fpr"] * 100 for n in names])
        lo = np.array([v[n]["area"]["rates"][g]["ci"][0] * 100 for n in names])
        hi = np.array([v[n]["area"]["rates"][g]["ci"][1] * 100 for n in names])
        bars = ax.bar(x + off, vals, w, color=color, label=label)
        ax.errorbar(x + off, vals, yerr=[vals - lo, hi - vals], fmt="none", ecolor=TEXT, elinewidth=1.4, capsize=5)
        for b, val, h in zip(bars, vals, hi):
            ax.text(b.get_x() + b.get_width() / 2, h + 0.4, f"{val:.1f}%", ha="center", color=TEXT, fontsize=12)
    for i, n in enumerate(names):
        d = v[n]["area"]["disparities"][0]
        colour = MAGENTA if d["flagged"] else MINT
        ax.text(i, 25.2, f"B÷A {d['ratio']:.2f}\n({d['ci'][0]:.2f}–{d['ci'][1]:.2f})", ha="center",
                va="bottom", color=colour, fontsize=11.5, weight="bold")
    ax.set_xticks(x, [n.replace(", ", ",\n").replace(" on ", "\non ").replace(" removed", "\nremoved") for n in names])
    ax.set_ylim(0, 28)
    ax.set_ylabel("False-positive rate (honest claims flagged)")
    ax.set_title("Who gets wrongly flagged by the fraud indicator?", pad=34)
    style.subtitle(ax, "Synthetic test set (12,000 claims) · 95% bootstrap intervals · ratio flagged outside 0.8–1.25")
    ax.legend(loc="upper right", bbox_to_anchor=(1, 0.86))
    fig.tight_layout()
    _save(fig, out, "fairness_fpr")


def feedback(results: dict, out: Path) -> None:
    sweep = results["5_fairness"]["feedback_sweep"]
    gaps = [r["scrutiny_gap"] * 100 for r in sweep]
    fig, ax = plt.subplots(figsize=SIZE)
    for key, colour, label in (("all_features", MAGENTA, "All features, incl. area and postcode"),
                               ("area_removed", AMBER, "Area and postcode removed (vehicle proxies remain)"),
                               ("behaviour_only", MINT, "Behaviour features only")):
        ax.plot(gaps, [r[key] for r in sweep], color=colour, lw=3, marker="o", ms=8, label=label)
    ax.axhline(1, color=MUTED, ls="--", lw=1)
    ax.text(gaps[-1], 1.04, "parity", color=MUTED, ha="right", va="bottom", fontsize=11)
    ax.set_xlabel("Extra investigation rate in area B in the historical data (percentage points)")
    ax.set_ylabel("False-positive rate, area B ÷ area A")
    ax.set_title("Uneven past scrutiny becomes tomorrow's training label", pad=34)
    style.subtitle(ax, "Same true fraud rate in both areas · mean of 3 seeds per point")
    ax.legend(loc="upper left")
    fig.tight_layout()
    _save(fig, out, "feedback_loop")


def extraction(results: dict, out: Path) -> None:
    r = results["1_extraction"]
    order = [k for k in ("standard", "standard+ocr", "german", "german+ocr", "narrative") if k in r]
    labels = {"standard": "English form", "standard+ocr": "English form + OCR noise", "german": "German form",
              "german+ocr": "German form + OCR noise", "narrative": "Free-text letter (held out)"}
    fig, ax = plt.subplots(figsize=SIZE)
    y = np.arange(len(order))[::-1]
    left = np.zeros(len(order))
    for key, colour, name in (("correct", MINT, "Correct"), ("missing", VIOLET, "Missing → copilot abstains"),
                              ("wrong", MAGENTA, "Wrong value")):
        vals = np.array([r[k][key] * 100 for k in order])
        ax.barh(y, vals, left=left, color=colour, label=name, height=0.6)
        for yi, l, v in zip(y, left, vals):
            if v >= 4:
                ax.text(l + v / 2, yi, f"{v:.0f}%", ha="center", va="center", color=BG, fontsize=11, weight="bold")
        left += vals
    ax.set_yticks(y, [labels[k] for k in order])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of checked fields")
    ax.set_title("Reading claim documents", pad=34)
    caught = r.get("standard+ocr", {}).get("corruption_caught", float("nan"))
    style.subtitle(ax, f"Dropped digits from OCR noise caught by cross-document checks in {caught:.0%} of claims (English forms)")
    ax.legend(loc="lower right", ncols=3, bbox_to_anchor=(1, -0.2))
    fig.tight_layout()
    _save(fig, out, "extraction")


def retrieval(results: dict, out: Path) -> None:
    r = results["3_retrieval"]
    modes = [("bm25", "BM25\n(keywords)"), ("dense_lsa", "Dense LSA\n(trained here)"), ("hybrid_lsa", "Hybrid\nBM25 + LSA"),
             ("dense_glove", "Dense GloVe\n(pretrained)"), ("hybrid_glove", "Hybrid\nBM25 + GloVe")]
    fig, ax = plt.subplots(figsize=SIZE)
    x = np.arange(len(modes))
    w = 0.34
    for off, key, color in ((-w / 2, "recall@1", VIOLET), (w / 2, "recall@3", MINT)):
        vals = [r[m][key] * 100 for m, _ in modes]
        bars = ax.bar(x + off, vals, w, color=color, label=key.replace("recall", "Recall"))
        for b, val in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, val + 1, f"{val:.0f}%", ha="center", color=TEXT, fontsize=12)
    ax.set_xticks(x, [label for _, label in modes])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Questions where the right clause is retrieved")
    ax.set_title("Finding the right policy clause", pad=34)
    style.subtitle(ax, f"{r['questions']} author-written adjuster questions × 3 policies ({r['hybrid_glove']['queries']} checks) · "
                       f"clauses returned from another policy: {r['out_of_scope_results']}")
    ax.legend(loc="upper left")
    fig.tight_layout()
    _save(fig, out, "retrieval")


def automation_bias(sim: dict, summary: dict, out: Path) -> None:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=SIZE)
    a1.scatter(sim["override_rate"] * 100, sim["pass_through"] * 100, s=7, color=MAGENTA, alpha=0.35, lw=0)
    a1.set_xlabel("Override rate in the audit log (%)")
    a1.set_ylabel("Wrong AI drafts that became decisions (%)")
    a1.set_title("Override rate: no signal", pad=34)
    style.subtitle(a1, f"Spearman ρ = {summary['spearman_override_vs_harm']:+.2f} over {summary['runs']:,} simulated worlds")
    a2.scatter(sim["catch"] * 100, sim["canary_est"] * 100, s=7, color=MINT, alpha=0.35, lw=0)
    a2.plot([0, 100], [0, 100], color=MUTED, ls="--", lw=1)
    a2.set_xlabel("True chance an AI error is caught (%)")
    a2.set_ylabel("Estimate from 60 hidden canaries (%)")
    a2.set_title("Hidden canaries: strong signal", pad=34)
    style.subtitle(a2, f"Spearman ρ = {summary['spearman_canary_vs_catch']:+.2f} · mean error {summary['canary_mean_abs_error'] * 100:.1f} pts")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.86, bottom=0.11, wspace=0.25)
    _save(fig, out, "automation_bias")


def injection(results: dict, out: Path) -> None:
    r = results["7_prompt_injection"]
    e2e = r.get("garak_end_to_end")
    if not isinstance(e2e, dict):
        return
    steps = [("garak attacks\ninserted into claims", e2e["attacks"], VIOLET),
             ("Missed by the\npattern guard", e2e["missed_by_guard_and_reached_model"], AMBER),
             ("Obeyed by the model,\nrejected by output checks", e2e["obeyed_then_rejected_by_output_checks"], MINT),
             ("Changed what the\nadjuster sees", e2e["attacks_that_changed_what_the_adjuster_sees"], MAGENTA)]
    fig, ax = plt.subplots(figsize=SIZE)
    x = np.arange(len(steps))
    bars = ax.bar(x, [s[1] for s in steps], color=[s[2] for s in steps], width=0.6)
    for b, (_, v, _) in zip(bars, steps):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, str(v), ha="center", color=TEXT, fontsize=14, weight="bold")
    ax.set_xticks(x, [s[0] for s in steps])
    ax.set_ylabel("Attacks")
    ax.set_title("Defence in depth against prompt injection", pad=34)
    style.subtitle(ax, "External attacks from NVIDIA garak · worst-case model that obeys every injection it sees")
    fig.tight_layout()
    _save(fig, out, "injection")


def risk_matrix(out: Path) -> None:
    """Qualitative placement from the assessment's risk prioritisation (not measured)."""
    risks = [
        ("Automation bias", 4.3, 4.4, MAGENTA),
        ("Accountability gap", 4.7, 3.9, MAGENTA),
        ("Unfair fraud detection", 2.8, 4.7, MAGENTA),
        ("Explainability gap", 3.3, 3.3, AMBER),
        ("Privacy misuse", 2.6, 3.6, AMBER),
        ("Hallucinated terms\n(mitigated by RAG)", 1.7, 2.6, MINT),
        ("Prompt injection", 2.0, 3.1, AMBER),
    ]
    fig, ax = plt.subplots(figsize=SIZE)
    xs, ys = np.meshgrid(np.linspace(0.5, 5.5, 200), np.linspace(0.5, 5.5, 200))
    ax.imshow(xs * ys, extent=(0.5, 5.5, 0.5, 5.5), origin="lower", cmap="magma", alpha=0.25, aspect="auto")
    for name, x, y, color in risks:
        ax.scatter(x, y, s=260, color=color, edgecolor=BG, lw=2, zorder=3)
        right = x > 4.0
        ax.text(x - 0.13 if right else x + 0.13, y, name, color=TEXT, fontsize=12, va="center",
                ha="right" if right else "left", zorder=4)
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_xticks([1, 3, 5], ["unlikely", "possible", "confirmed / likely"])
    ax.set_yticks([1, 3, 5], ["minor", "moderate", "severe"])
    ax.set_xlabel("Likelihood")
    ax.set_ylabel("Impact on claimants")
    ax.grid(False)
    ax.set_title("Risk landscape", pad=34)
    style.subtitle(ax, "Qualitative ranking from the Responsible AI assessment, not a measurement")
    fig.tight_layout()
    _save(fig, out, "risk_matrix")


def architecture(out: Path) -> None:
    fig, ax = plt.subplots(figsize=SIZE)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")

    def box(x, y, w, h, title, body, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.18",
                                    fc="#1a1528", ec=color, lw=2))
        ax.text(x + 0.2, y + h - 0.32, title, color=color, fontsize=12.5, weight="bold", va="top")
        ax.text(x + 0.2, y + h - 0.8, body, color=MUTED, fontsize=10.5, va="top", linespacing=1.4)

    def arrow(x1, y1, x2, y2, color=MUTED, ls="-"):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8, ls=ls))

    ax.text(0.2, 8.6, "One claim's journey", color=TEXT, fontsize=16, weight="bold")
    ax.text(0.2, 8.15, "AI components prepare; only signed-in people decide", color=MUTED, fontsize=11.5)

    box(0.2, 5.0, 2.9, 2.6, "Intake + guard", "claim, estimate,\npolice, medical\ndocuments; injection\nlines quarantined", VIOLET)
    box(3.6, 5.0, 2.9, 2.6, "Extraction", "typed, validated;\nmissing or\nconflicting facts\n→ abstain", VIOLET)
    box(7.0, 6.35, 3.6, 1.6, "Hybrid retrieval", "BM25 + GloVe, RRF\nclaimant's policy only", VIOLET)
    box(7.0, 4.45, 3.6, 1.6, "Rule engine", "exclusions, excess, limits,\nescalation: exact, in code", VIOLET)
    box(7.0, 2.55, 3.6, 1.6, "Fraud indicator", "separate model, audited\nper subgroup with CIs", AMBER)
    box(11.1, 4.45, 4.6, 3.5, "Cited draft", "LLM or template; explains\nthe rule outcome only\noutput checks: citations,\ncausal clauses, amounts,\nleaks, changed outcome", VIOLET)
    box(11.1, 1.0, 4.6, 2.9, "Adjuster decides", "signed staff token\noverride needs a reason\nescalated → a different\nsupervisor signs off", MINT)
    box(3.6, 0.6, 6.9, 1.65, "Keyed audit log + monitoring", "HMAC chain, external anchors · hidden canaries,\nfairness checks, kill switch per component", MUTED)

    arrow(3.1, 6.3, 3.6, 6.3)
    arrow(6.5, 6.6, 7.0, 7.1)
    arrow(6.5, 6.0, 7.0, 5.3)
    arrow(6.5, 5.4, 7.0, 3.4)
    arrow(10.6, 7.1, 11.1, 6.6)
    arrow(10.6, 5.3, 11.1, 5.6)
    arrow(10.6, 3.4, 11.1, 3.0, AMBER)
    arrow(13.4, 4.45, 13.4, 3.9, MINT)
    arrow(11.1, 1.6, 10.5, 1.6, MUTED, "--")
    ax.text(13.4, 0.35, "claimant is told only a sealed human decision", color=MINT, fontsize=11, ha="center")
    _save(fig, out, "architecture")


def render_all(results: dict, sim: dict, out: Path) -> None:
    style.apply()
    fairness(results, out)
    feedback(results, out)
    extraction(results, out)
    retrieval(results, out)
    automation_bias(sim, results["11_monitoring_simulation"], out)
    injection(results, out)
    risk_matrix(out)
    architecture(out)
