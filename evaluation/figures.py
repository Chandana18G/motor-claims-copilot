"""Figures for the README and the portfolio (1920x1080 PNG)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from evaluation import style
from evaluation.style import AMBER, BG, GRID, MAGENTA, MINT, MUTED, TEXT, VIOLET

SIZE = (12, 6.75)
DPI = 160


def _save(fig, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=DPI)
    plt.close(fig)


def fairness(results: dict, out: Path) -> None:
    v = results["5_fraud_fairness"]["variants"]
    names = list(v)
    fig, ax = plt.subplots(figsize=SIZE)
    x = np.arange(len(names))
    w = 0.34
    for off, g, color, label in ((-w / 2, "A", MINT, "Area A"), (w / 2, "B", MAGENTA, "Area B")):
        vals = [v[n][g]["fpr"] * 100 for n in names]
        bars = ax.bar(x + off, vals, w, color=color, label=label)
        for b, val in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, val + 0.2, f"{val:.1f}%", ha="center", color=TEXT, fontsize=12)
    ax.set_xticks(x, [n.replace(" on ", "\non ").replace(" proxy", "\nproxy") for n in names])
    ax.set_ylabel("False-positive rate (honest claims flagged)")
    ax.set_title("Who gets wrongly flagged by the fraud indicator?", pad=34)
    style.subtitle(ax, "Synthetic test set; true fraud is independent of area, but past investigations focused on area B")
    ax.legend(loc="upper right")
    fig.tight_layout()
    _save(fig, out, "fairness_fpr")


def feedback(results: dict, out: Path) -> None:
    sweep = results["5_fraud_fairness"]["feedback_sweep"]
    gaps = [r["scrutiny_gap"] * 100 for r in sweep]
    fig, ax = plt.subplots(figsize=SIZE)
    ax.plot(gaps, [r["with_proxies"] for r in sweep], color=MAGENTA, lw=3, marker="o", ms=8, label="Model sees area / postcode")
    ax.plot(gaps, [r["without_proxies"] for r in sweep], color=MINT, lw=3, marker="o", ms=8, label="Proxies removed")
    ax.axhline(1, color=MUTED, ls="--", lw=1)
    ax.text(gaps[-1], 1.04, "parity", color=MUTED, ha="right", va="bottom", fontsize=11)
    ax.set_xlabel("Extra investigation rate in area B in the historical data (percentage points)")
    ax.set_ylabel("False-positive rate, area B ÷ area A")
    ax.set_title("Uneven past scrutiny becomes tomorrow's training label", pad=34)
    style.subtitle(ax, "Same true fraud rate in both areas; only who was investigated differs")
    ax.legend(loc="upper left")
    fig.tight_layout()
    _save(fig, out, "feedback_loop")


def retrieval(results: dict, out: Path) -> None:
    r = results["3_retrieval"]
    modes = [("bm25", "BM25 (keywords)"), ("dense", "Dense (LSA vectors)"), ("hybrid", "Hybrid (RRF)")]
    fig, ax = plt.subplots(figsize=SIZE)
    x = np.arange(len(modes))
    w = 0.34
    for off, key, color in ((-w / 2, "recall@1", VIOLET), (w / 2, "recall@3", MINT)):
        vals = [r[m][key] * 100 for m, _ in modes]
        bars = ax.bar(x + off, vals, w, color=color, label=key.replace("recall", "Recall"))
        for b, val in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, val + 1, f"{val:.0f}%", ha="center", color=TEXT, fontsize=12)
    ax.set_xticks(x, [label for _, label in modes])
    ax.set_ylim(0, 110)
    ax.set_ylabel("Questions where the right clause is retrieved")
    ax.set_title("Finding the right policy clause", pad=34)
    style.subtitle(ax, f"{r['hybrid']['queries']} plain-language adjuster questions across 3 synthetic policies · "
                       f"out-of-scope clauses returned: {r['out_of_scope_results']}")
    ax.legend(loc="upper left")
    fig.tight_layout()
    _save(fig, out, "retrieval")


def automation_bias(out: Path) -> None:
    """Analytic model of review: diligence d, AI error rate e.

    A diligent review catches an AI error with p=0.9 and wrongly overrides a correct draft with
    p=0.02; a non-diligent review accepts the draft as is.
    """
    catch, false_override = 0.9, 0.02
    fig, (a1, a2) = plt.subplots(1, 2, figsize=SIZE, gridspec_kw={"wspace": 0.28})
    for d, color in ((0.95, MINT), (0.6, VIOLET), (0.3, AMBER), (0.1, MAGENTA)):
        e = np.linspace(0.005, 0.15, 60)
        override = d * (e * catch + (1 - e) * false_override)
        passed = e * (1 - d * catch)
        a1.plot(override * 100, passed * 100, color=color, lw=3, label=f"{d:.0%} of drafts really reviewed")
    a1.axvline(3, color=MUTED, ls="--", lw=1)
    a1.text(3.15, -0.45, "same 3% override rate", color=MUTED, fontsize=11)
    a1.set_xlabel("Override rate seen in the audit log (%)")
    a1.set_ylabel("Wrong AI drafts that become decisions (%)")
    a1.set_title("A low override rate proves nothing", pad=34)
    style.subtitle(a1, "Model: diligent review catches 90% of AI errors")
    a1.legend(loc="upper right", fontsize=10)

    n = np.arange(0, 201)
    for p, color in ((0.10, MAGENTA), (0.05, AMBER), (0.02, VIOLET), (0.01, MINT)):
        a2.plot(n, (1 - (1 - p) ** n) * 100, color=color, lw=3, label=f"{p:.0%} of accepted drafts wrong")
    a2.axhline(95, color=MUTED, ls="--", lw=1)
    a2.set_xlabel("Accepted drafts re-reviewed (unannounced sample)")
    a2.set_ylabel("Chance the sample contains an error (%)")
    a2.set_title("Audit what was accepted", pad=34)
    style.subtitle(a2, "Probability of finding at least one bad acceptance")
    a2.legend(loc="lower right", fontsize=10)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.86, bottom=0.11, wspace=0.28)
    _save(fig, out, "automation_bias")


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
    ax.text(0.2, 8.15, "AI components prepare; only people decide", color=MUTED, fontsize=11.5)

    box(0.2, 5.0, 2.9, 2.6, "Intake + guard", "claim form, repair\nestimate, police and\nmedical documents\ninjection lines\nquarantined", VIOLET)
    box(3.6, 5.0, 2.9, 2.6, "Extraction", "typed fields,\nvalidated\nmissing documents\nand conflicts\nflagged", VIOLET)
    box(7.0, 6.35, 3.6, 1.6, "Hybrid retrieval", "BM25 + dense, RRF\nclaimant's policy only", VIOLET)
    box(7.0, 4.45, 3.6, 1.6, "Rule engine", "exclusions, excess, limits,\nescalation: exact, in code", VIOLET)
    box(7.0, 2.55, 3.6, 1.6, "Fraud indicator", "separate statistical model\nstructured features only", AMBER)
    box(11.1, 4.45, 4.6, 3.5, "Cited draft", "summary + recommendation\nevery sentence cites a clause\ncitations checked verbatim\nabstains on conflicting\nevidence", VIOLET)
    box(11.1, 1.0, 4.6, 2.9, "Adjuster decides", "accept / edit / override\noverride needs a reason\nhigh-value or flagged\n→ supervisor sign-off", MINT)
    box(3.6, 0.6, 6.9, 1.65, "Hash-chained audit log", "every step, actor and decision\nediting any entry breaks the chain", MUTED)

    arrow(3.1, 6.3, 3.6, 6.3)
    arrow(6.5, 6.6, 7.0, 7.1)
    arrow(6.5, 6.0, 7.0, 5.3)
    arrow(6.5, 5.4, 7.0, 3.4)
    arrow(10.6, 7.1, 11.1, 6.6)
    arrow(10.6, 5.3, 11.1, 5.6)
    arrow(10.6, 3.4, 11.1, 3.0, AMBER)
    arrow(13.4, 4.45, 13.4, 3.9, MINT)
    arrow(11.1, 1.6, 10.5, 1.6, MUTED, "--")
    ax.text(13.4, 0.45, "claimant is told only the human decision", color=MINT, fontsize=11, ha="center")
    _save(fig, out, "architecture")


def render_all(results: dict, out: Path) -> None:
    style.apply()
    fairness(results, out)
    feedback(results, out)
    retrieval(results, out)
    automation_bias(out)
    risk_matrix(out)
    architecture(out)
