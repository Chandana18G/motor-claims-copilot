"""Shared chart style (dark theme matching the portfolio)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BG = "#110e1a"
GRID = "#2a2240"
TEXT = "#ece8f5"
MUTED = "#a59dbb"
MINT = "#5eead4"
MAGENTA = "#e879f9"
VIOLET = "#b794ff"
AMBER = "#fbbf24"


def apply() -> None:
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "axes.titlecolor": TEXT,
        "axes.titlesize": 15, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 12, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 11, "ytick.labelsize": 11,
        "text.color": TEXT, "legend.frameon": False, "legend.fontsize": 11,
        "font.family": "DejaVu Sans", "figure.dpi": 100,
    })


def subtitle(ax, text: str) -> None:
    ax.text(0, 1.02, text, transform=ax.transAxes, color=MUTED, fontsize=11, va="bottom")
