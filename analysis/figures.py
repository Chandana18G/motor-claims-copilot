"""Figures for the README and the portfolio (1920x1080 PNG)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from analysis import style
from analysis.style import AMBER, BG, MAGENTA, MINT, MUTED, TEXT, VIOLET

SIZE = (12, 6.75)
DPI = 160


def _save(fig, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=DPI)
    plt.close(fig)


def fairness(results: dict, out: Path) -> None:
    v = results["fairness"]["variants"]
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
        ax.text(i, 25.2, f"B÷A {d['ratio']:.2f}\n({d['ci'][0]:.2f}–{d['ci'][1]:.2f})", ha="center",
                va="bottom", color=MAGENTA if d["flagged"] else MINT, fontsize=11.5, weight="bold")
    ax.set_xticks(x, [n.replace(", ", ",\n").replace(" on ", "\non ").replace(" removed", "\nremoved") for n in names])
    ax.set_ylim(0, 28)
    ax.set_ylabel("False-positive rate (honest claims flagged)")
    ax.set_title("Who gets wrongly flagged by the fraud indicator?", pad=34)
    style.subtitle(ax, "Synthetic test set (12,000 claims) · 95% bootstrap intervals · flagged: ratio outside 0.8–1.25 and interval excludes 1")
    ax.legend(loc="upper right", bbox_to_anchor=(1, 0.86))
    fig.tight_layout()
    _save(fig, out, "fairness_fpr")


def feedback(results: dict, out: Path) -> None:
    sweep = results["fairness"]["feedback_sweep"]
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


def automation_bias(sim: dict, summary: dict, out: Path) -> None:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=SIZE)
    a1.scatter(sim["override_rate"] * 100, sim["pass_through"] * 100, s=7, color=MAGENTA, alpha=0.35, lw=0)
    a1.set_xlabel("Override rate in the audit log (%)")
    a1.set_ylabel("Wrong AI drafts that became decisions (%)")
    a1.set_title("Override rate: no signal", pad=34)
    style.subtitle(a1, f"Spearman ρ = {summary['spearman_override_vs_harm']:+.2f} over {summary['runs']:,} simulated worlds")
    a2.scatter(sim["pass_through"] * 100, sim["resample_est"] * 100, s=7, color=MINT, alpha=0.35, lw=0)
    top = float(max(sim["pass_through"].max(), sim["resample_est"].max()) * 100)
    a2.plot([0, top], [0, top], color=MUTED, ls="--", lw=1)
    a2.set_xlabel("Wrong AI drafts that became decisions (%)")
    a2.set_ylabel("Estimate from re-reviewing 100 accepted decisions (%)")
    a2.set_title("Re-review of accepted decisions: signal", pad=34)
    style.subtitle(a2, f"Spearman ρ = {summary['spearman_resample_vs_harm']:+.2f} · unannounced, random sample")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.86, bottom=0.11, wspace=0.25)
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
    """The assessed system design: one claim's journey."""
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
    ax.text(0.2, 8.15, "The AI prepares; only people decide", color=MUTED, fontsize=11.5)

    box(0.2, 5.0, 3.0, 2.6, "Claim intake", "portal, email or phone\npolice report, repair\nestimate, medical\ndocuments", VIOLET)
    box(3.7, 5.0, 3.0, 2.6, "Document\nprocessing", "\ncompleteness check:\nwhat is missing?", VIOLET)
    box(7.2, 5.6, 3.8, 2.0, "Generative AI draft", "grounded in policy wording\nand guidelines (RAG):\nsummary + cited rationale", VIOLET)
    box(7.2, 2.9, 3.8, 2.0, "Fraud indicator", "a separate statistical model,\nnot the generative AI", AMBER)
    box(11.6, 4.5, 4.2, 3.1, "Adjuster reviews", "accept, edit or override\n(override reason logged)\nhigh-value or fraud-flagged\n→ supervisor", MINT)
    box(11.6, 1.2, 4.2, 2.6, "Human decision", "approve, deny, request\ninformation or refer to SIU\nonly this reaches the\nclaimant", MINT)
    box(3.7, 0.9, 7.3, 1.4, "Immutable audit log", "every step and decision, attributable", MUTED)

    arrow(3.2, 6.3, 3.7, 6.3)
    arrow(6.7, 6.6, 7.2, 6.6)
    arrow(6.7, 5.7, 7.2, 4.2)
    arrow(11.0, 6.6, 11.6, 6.3)
    arrow(11.0, 3.9, 11.6, 5.0, AMBER)
    arrow(13.7, 4.5, 13.7, 3.8, MINT)
    arrow(11.6, 1.7, 11.0, 1.4, MUTED, "--")
    ax.text(15.8, 0.55, "the AI cannot approve, pay or contact the claimant", color=MINT, fontsize=11, ha="right")
    _save(fig, out, "architecture")


def render_all(results: dict, sim: dict, out: Path) -> None:
    style.apply()
    fairness(results, out)
    feedback(results, out)
    automation_bias(sim, results["automation_bias"], out)
    risk_matrix(out)
    architecture(out)
