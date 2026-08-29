"""Cinq figures : les facteurs, les instantanés de courbe, la prévision, la récession, l'ALM."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]


def use_style():
    import matplotlib as mpl
    from cycler import cycler
    from matplotlib.ticker import FuncFormatter

    mpl.rcParams.update({
        "figure.dpi": 200, "savefig.dpi": 200, "figure.constrained_layout.use": True,
        "font.size": 11, "axes.titlesize": 12, "axes.prop_cycle": cycler(color=OKABE_ITO),
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.5,
        "legend.frameon": False, "lines.linewidth": 1.6,
    })
    return FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def _shade(ax, episodes, index) -> None:
    lo, hi = index[0].to_timestamp(), index[-1].to_timestamp()
    for peak, trough in episodes:
        a, b = peak.to_timestamp(), trough.to_timestamp(how="end")
        if b >= lo and a <= hi:
            ax.axvspan(max(a, lo), min(b, hi), color="0.88", zorder=0)


def fig_factors(betas: pd.DataFrame, episodes, dest: Path) -> None:
    """Niveau, pente et courbure Nelson-Siegel sur quarante ans, récessions ombrées."""
    fr = use_style()
    fig, axes = plt.subplots(3, 1, figsize=(9, 7.5), sharex=True)
    ts = betas.index.to_timestamp()
    labels = [("niveau", "Niveau (beta 1, %)"), ("pente", "Pente (beta 2, %)"),
              ("courbure", "Courbure (beta 3, %)")]
    for ax, (col, lab), color in zip(axes, labels, OKABE_ITO, strict=False):
        ax.plot(ts, betas[col], color=color)
        ax.set_ylabel(lab, fontsize=9.5)
        ax.yaxis.set_major_formatter(fr)
        _shade(ax, episodes, betas.index)
    axes[1].axhline(0, color="0.5", linewidth=0.8)
    axes[0].set_title("Trois nombres résument la courbe canadienne : le niveau tombe de 10 % à 3 % en quarante ans")
    fig.savefig(dest)
    plt.close(fig)


def fig_snapshots(monthly: pd.DataFrame, dates: list[str], dest: Path) -> None:
    """Des instantanés de courbe : la désinflation, l'inversion de 2022-23, la normalisation."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    taus = np.array(monthly.columns, dtype=float)
    for d, color in zip(dates, OKABE_ITO, strict=False):
        row = monthly.loc[pd.Period(d, "M")]
        ax.plot(taus, row.to_numpy(dtype=float), color=color,
                label=f"{d} ({row[10.0]:.1f} % à 10 ans)".replace(".", ","))
    ax.set_xlabel("Échéance (années)")
    ax.set_ylabel("Taux zéro-coupon (%)")
    ax.yaxis.set_major_formatter(fr)
    ax.xaxis.set_major_formatter(fr)
    ax.set_title("La même économie, cinq courbes : de la désinflation de 1990 à l'inversion de 2022")
    ax.legend(fontsize=9)
    fig.savefig(dest)
    plt.close(fig)


def fig_forecast(rmse: pd.DataFrame, dest: Path) -> None:
    """Le ratio de RMSE contre la marche aléatoire : sous 1, le modèle bat la naïveté."""
    fr = use_style()
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.8), sharey=True)
    for ax, h in zip(axes, sorted(rmse["horizon"].unique()), strict=False):
        sub = rmse[rmse["horizon"] == h].sort_values("maturite")
        ax.plot(sub["maturite"], sub["ratio_dns_rw"], marker="o", ms=4,
                color=OKABE_ITO[0], label="DNS / marche aléatoire")
        ax.plot(sub["maturite"], sub["ratio_ar1_rw"], marker="s", ms=4, linestyle="--",
                color=OKABE_ITO[1], label="AR(1) direct / marche aléatoire")
        ax.axhline(1.0, color="0.4", linewidth=0.9)
        ax.set_xscale("log")
        ax.set_xticks([0.25, 1, 2, 5, 10, 30])
        ax.xaxis.set_major_formatter(fr)
        ax.set_title(f"h = {h} mois", fontsize=10.5)
        ax.set_xlabel("Échéance (années)")
        ax.yaxis.set_major_formatter(fr)
    axes[0].set_ylabel("Ratio de RMSE")
    axes[0].legend(fontsize=8.5, loc="upper center")
    fig.suptitle("La marche aléatoire reste dure à battre : ratios de RMSE hors échantillon, 1996-2026", y=1.04)
    fig.savefig(dest, bbox_inches="tight")
    plt.close(fig)


def fig_recession(feats: pd.DataFrame, probs: dict[str, pd.Series], episodes, dest: Path) -> None:
    """En haut les pentes, en bas les probabilités hors échantillon ; 2022-23 est le test décisif."""
    fr = use_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 6.6), sharex=True,
                                   height_ratios=[1.0, 1.0])
    ts = feats.index.to_timestamp()
    ax1.plot(ts, feats["pente_brute"], color=OKABE_ITO[0], label="Pente brute (10 ans - 3 mois)")
    ax1.plot(ts, feats["pente_nette"], color=OKABE_ITO[3], label="Pente nette de prime de terme")
    ax1.axhline(0, color="0.4", linewidth=0.9)
    ax1.set_ylabel("Points de %")
    ax1.yaxis.set_major_formatter(fr)
    _shade(ax1, episodes, feats.index)
    ax1.legend(fontsize=9, loc="upper right")
    ax1.set_title("La pente brute s'inverse en 2022-23 sans récession ; la pente nette s'inverse moins")

    for (name, p), color in zip(probs.items(), OKABE_ITO, strict=False):
        ax2.plot(p.index.to_timestamp(), p.to_numpy(), color=color, label=name)
    ax2.set_ylabel("Prob. de récession à 12 mois")
    ax2.set_ylim(0, 1)
    ax2.yaxis.set_major_formatter(fr)
    _shade(ax2, episodes, feats.index)
    ax2.legend(fontsize=9, loc="upper right")
    ax2.set_title("Probit estimé en fenêtre expansive, cible jamais observée avant t + 12", fontsize=10.5)
    fig.savefig(dest)
    plt.close(fig)


def fig_alm(delta: pd.DataFrame, dest: Path) -> None:
    """Le Delta-EVE du bilan stylisé : le choc mesuré de 2022 contre les gabarits réglementaires."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(9, 4.4))
    colors = [OKABE_ITO[3] if v < 0 else OKABE_ITO[2] for v in delta["delta_eve"]]
    mesure = delta["scenario"].str.startswith("2022")
    for i, m in enumerate(mesure):
        if m:
            colors[i] = OKABE_ITO[0]
    noms = delta["scenario"].str.replace("_", " ")
    ax.barh(noms, delta["delta_eve"], color=colors, height=0.62)
    for nom, v in zip(noms, delta["delta_eve"], strict=True):
        ax.text(v + (0.1 if v >= 0 else -0.1), nom,
                f"{v:+.1f}".replace(".", ","), va="center",
                ha="left" if v >= 0 else "right", fontsize=9)
    lim = float(delta["delta_eve"].abs().max()) * 1.22
    ax.set_xlim(-lim, lim)
    ax.axvline(0, color="0.3", linewidth=0.9)
    ax.set_xlabel("Delta-EVE (milliards de dollars, bilan stylisé de 100)")
    ax.xaxis.set_major_formatter(fr)
    ax.set_title("2022 dépasse le gabarit court en ampleur, mais sa forme d'aplatissement amortit la perte")
    fig.savefig(dest, bbox_inches="tight")
    plt.close(fig)
