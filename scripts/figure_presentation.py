"""Draw the README figure from published results, without rerunning the study.

Run from the repository with ``uv run python scripts/figure_presentation.py``.
The input tables remain the numerical source of truth.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
BLUE, ORANGE, GREEN, GREY = "#176B96", "#C56628", "#14816D", "#718096"
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 15,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#CBD5E0",
        "text.color": "#172B3A",
        "axes.labelcolor": "#172B3A",
        "xtick.color": "#425466",
        "ytick.color": "#425466",
        "axes.axisbelow": True,
    }
)


def number(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def finish(fig, axes, title, note, path="results/figures/presentation.png"):
    for ax in np.asarray(axes, dtype=object).ravel():
        ax.grid(axis="x", color="#EDF0F3", linewidth=0.8)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))
    fig.suptitle(title, x=0.02, ha="left", fontweight="bold", fontsize=16)
    fig.text(0.02, 0.015, note, ha="left", va="bottom", fontsize=9, color="#526575")
    fig.tight_layout(rect=(0, 0.075, 1, 0.91))
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    d = pd.read_csv(ROOT / "results/tables/rmse_prevision.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11, 6), sharex=True, sharey=True)
    for horizon, ax in zip([1, 6, 12], axes, strict=True):
        row = d[d.horizon == horizon].sort_values("maturite")
        values = row.ratio_dns_rw.to_numpy()
        ax.scatter(values, np.arange(len(row)), s=60, color=BLUE, zorder=3)
        ax.axvline(1, color=ORANGE, linestyle="--")
        ax.set_yticks(
            np.arange(len(row)),
            ["3 mois" if v == 0.25 else number(v, 0) + (" an" if v == 1 else " ans") for v in row.maturite],
        )
        ax.set_xlim(0.9, 1.6)
        ax.set_xlabel("Erreur relative au taux inchangé")
        ax.set_title(f"Prévoir à {horizon} mois", fontsize=12)
    axes[0].invert_yaxis()
    axes[0].set_ylabel("Durée du prêt")
    count = int((d.ratio_dns_rw > 1).sum())
    finish(
        fig,
        axes,
        f"Garder le taux actuel fait mieux dans {count} cas sur {len(d)}",
        "Courbes canadiennes · prévisions depuis 1996, données jusqu'en août 2026\n"
        "À droite de 1, le modèle de Diebold et Li commet plus d'erreur que la prévision d'un taux inchangé.",
    )


if __name__ == "__main__":
    main()
