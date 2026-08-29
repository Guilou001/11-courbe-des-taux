"""Calculs obligataires sur la courbe zéro-coupon et bilan bancaire sous les six chocs IRRBB.

Toute l'actualisation suit la convention de la courbe BdC, la composition continue : le facteur
d'actualisation d'un flux à t années vaut exp(-z(t) * t), z en décimales.

Les chocs viennent du gabarit du Comité de Bâle pour le CAD, recalibré en juillet 2024 (d578,
table de SRP31.90) et en vigueur depuis le 1er janvier 2026 (rapporté) : parallèle 200 pb, taux
court 275 pb, taux long 175 pb, avec les formes fonctionnelles de la norme IRRBB (décroissance
exp(-t/4) pour le choc court, 1 - exp(-t/4) pour le choc long, coefficients 0,65/0,90 et
0,80/0,60 des chocs de pente).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

R_PARALLELE = 2.00      # points de pourcentage, CAD, BCBS d578 (2024, SRP31.90), rapporté
R_COURT = 2.75
R_LONG = 1.75


def interp_zero(curve_row: pd.Series, t: np.ndarray) -> np.ndarray:
    """Le taux zéro (en %) interpolé linéairement aux échéances t (années)."""
    taus = np.array(curve_row.index, dtype=float)
    return np.interp(np.asarray(t, dtype=float), taus, curve_row.to_numpy(dtype=float))


def bond_price(curve_row: pd.Series, coupon_pct: float, maturity: float,
               freq: int = 2, notional: float = 100.0) -> float:
    """Le prix d'une obligation à coupons, actualisée flux par flux sur la courbe zéro."""
    times = np.arange(1, int(round(maturity * freq)) + 1) / freq
    if times.size == 0:      # échéance plus courte que le pas de coupon : un flux unique
        times = np.array([maturity])
        cfs = np.array([notional * (1.0 + coupon_pct / 100.0 * maturity)])
    else:
        cfs = np.full(times.shape, notional * coupon_pct / 100.0 / freq)
        cfs[-1] += notional
    z = interp_zero(curve_row, times) / 100.0
    return float(np.sum(cfs * np.exp(-z * times)))


def modified_duration(curve_row: pd.Series, coupon_pct: float, maturity: float,
                      freq: int = 2, bump_bp: float = 1.0) -> float:
    """La sensibilité au déplacement parallèle, par revalorisation à +/- bump_bp."""
    up = curve_row + bump_bp / 100.0
    dn = curve_row - bump_bp / 100.0
    p0 = bond_price(curve_row, coupon_pct, maturity, freq)
    return float((bond_price(dn, coupon_pct, maturity, freq)
                  - bond_price(up, coupon_pct, maturity, freq)) / (2 * p0 * bump_bp / 10000.0))


def key_rate_durations(curve_row: pd.Series, coupon_pct: float, maturity: float,
                       keys: tuple[float, ...] = (0.25, 2.0, 5.0, 10.0, 30.0),
                       freq: int = 2, bump_bp: float = 1.0) -> pd.Series:
    """Les durations par taux clés : bosses triangulaires entre les clés voisines, somme ~ duration totale."""
    taus = np.array(curve_row.index, dtype=float)
    p0 = bond_price(curve_row, coupon_pct, maturity, freq)
    out = {}
    for i, k in enumerate(keys):
        lo = keys[i - 1] if i > 0 else -np.inf
        hi = keys[i + 1] if i < len(keys) - 1 else np.inf
        w = np.ones_like(taus)
        left = (taus < k) & (taus > lo)
        right = (taus > k) & (taus < hi)
        w[left] = (taus[left] - lo) / (k - lo)
        w[right] = (hi - taus[right]) / (hi - k)
        w[(taus <= lo) | (taus >= hi)] = 0.0
        bumped_up = curve_row + w * bump_bp / 100.0
        bumped_dn = curve_row - w * bump_bp / 100.0
        out[k] = float((bond_price(bumped_dn, coupon_pct, maturity, freq)
                        - bond_price(bumped_up, coupon_pct, maturity, freq))
                       / (2 * p0 * bump_bp / 10000.0))
    return pd.Series(out, name="krd")


def irrbb_shocks(taus: np.ndarray) -> dict[str, np.ndarray]:
    """Les six scénarios de la norme IRRBB, en points de pourcentage par échéance."""
    t = np.asarray(taus, dtype=float)
    court = np.exp(-t / 4.0)
    long_ = 1.0 - court
    return {
        "parallele_hausse": np.full_like(t, R_PARALLELE),
        "parallele_baisse": np.full_like(t, -R_PARALLELE),
        "pentification": -0.65 * R_COURT * court + 0.90 * R_LONG * long_,
        "aplatissement": 0.80 * R_COURT * court - 0.60 * R_LONG * long_,
        "court_hausse": R_COURT * court,
        "court_baisse": -R_COURT * court,
    }


@dataclass(frozen=True)
class Poste:
    """Un poste du bilan, approximé par une obligation à coupons (précepte déclaré)."""

    nom: str
    montant: float          # milliards de dollars, positif à l'actif, négatif au passif
    coupon_pct: float
    maturite: float         # années ; les dépôts à vue portent leur duration COMPORTEMENTALE
    refixation_mois: float  # premier mois où le poste se refixe (pour le revenu net d'intérêts)


def bilan_stylise() -> list[Poste]:
    """Un bilan de banque de détail stylisé, 100 G$ d'actifs, précepte déclaré dans le README."""
    return [
        Poste("hypothèques 5 ans", 45.0, 4.0, 5.0, 30.0),
        Poste("portefeuille obligataire", 20.0, 3.5, 10.0, 60.0),
        Poste("prêts entreprises variables", 25.0, 5.0, 0.25, 3.0),
        Poste("encaisse et court terme", 10.0, 2.5, 0.25, 1.0),
        Poste("dépôts à vue (duration comportementale)", -40.0, 1.0, 2.5, 30.0),
        Poste("CPG", -30.0, 3.0, 1.5, 18.0),
        Poste("financement de gros", -22.0, 3.5, 2.0, 24.0),
    ]


def eve(curve_row: pd.Series, bilan: list[Poste]) -> float:
    """La valeur économique des fonds propres : la somme des postes revalorisés (G$)."""
    return float(sum(p.montant * bond_price(curve_row, p.coupon_pct, p.maturite) / 100.0
                     for p in bilan))


def delta_eve_scenarios(curve_row: pd.Series, bilan: list[Poste],
                        extra: dict[str, pd.Series] | None = None) -> pd.DataFrame:
    """Le Delta-EVE des six chocs réglementaires, plus des scénarios mesurés optionnels (G$)."""
    base = eve(curve_row, bilan)
    taus = np.array(curve_row.index, dtype=float)
    rows = []
    for name, shock in irrbb_shocks(taus).items():
        shocked = curve_row + shock
        rows.append({"scenario": name, "delta_eve": eve(shocked, bilan) - base})
    for name, shocked_row in (extra or {}).items():
        rows.append({"scenario": name, "delta_eve": eve(shocked_row, bilan) - base})
    return pd.DataFrame(rows)


def delta_nii_12m(bilan: list[Poste], shock_pp: float, beta_depot: float = 0.5) -> float:
    """Le revenu net d'intérêts à 12 mois sous un choc parallèle : gap de refixation (G$).

    Chaque poste qui se refixe au mois m subit le choc pendant (12 - m)/12 de l'année ;
    un passif qui se refixe coûte plus cher, d'où le signe du montant.

    ``beta_depot`` est la part du choc de taux répercutée sur le coût des dépôts à vue, un précepte
    déclaré (Bâle emploie 0,5 comme ordre de grandeur usuel pour un dépôt de détail). Le paramètre
    est décisif : le bilan précepte donne aux dépôts à vue une duration COMPORTEMENTALE de 2,5 ans
    pour l'actualisation, mais leur taux, lui, se révise en continu. Les confondre revient à poser
    un bêta nul, c'est-à-dire à supposer qu'une hausse de 200 pb ne coûte rien au passif pendant un
    an, et le gap est alors positif par construction. Mesuré sur le bilan du dépôt sous +200 pb
    (results/tables/delta_nii.csv) : +0,558 G$ à bêta nul, +0,158 G$ à bêta 0,5, -0,242 G$ à bêta 1.
    Convention : le dépôt à vue, dont le taux se révise en continu, porte le choc sur les douze mois.
    """
    total = 0.0
    for p in bilan:
        depot_a_vue = p.montant < 0 and "vue" in p.nom
        if depot_a_vue:
            total += p.montant * (shock_pp / 100.0) * beta_depot
        elif p.refixation_mois <= 12:
            total += p.montant * (shock_pp / 100.0) * (12.0 - p.refixation_mois) / 12.0
    return float(total)
