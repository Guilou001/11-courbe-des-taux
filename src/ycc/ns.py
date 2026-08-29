"""Nelson-Siegel à la Diebold-Li : ajustement par moindres carrés, prévision AR(1) par facteur.

Diebold et Li (2006) fixent lambda à 0,0609 par mois, ce qui place le maximum de la charge de
courbure à 30 mois ; en années, lambda vaut 0,0609 x 12 = 0,7308 et le maximum tombe à 2,5 ans.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LAMBDA_DL = 0.7308      # par année ; Diebold-Li (2006), déclaré et non réoptimisé


def loadings(taus: np.ndarray, lam: float = LAMBDA_DL) -> np.ndarray:
    """La matrice (n, 3) des charges : niveau, pente, courbure."""
    lt = lam * np.asarray(taus, dtype=float)
    slope = (1.0 - np.exp(-lt)) / lt
    return np.column_stack([np.ones_like(lt), slope, slope - np.exp(-lt)])


def fit_curve(yields_pct: np.ndarray, taus: np.ndarray, lam: float = LAMBDA_DL) -> np.ndarray:
    """Les trois betas d'une courbe, par moindres carrés ordinaires."""
    x = loadings(taus, lam)
    beta, *_ = np.linalg.lstsq(x, np.asarray(yields_pct, dtype=float), rcond=None)
    return beta


def fit_history(monthly: pd.DataFrame, lam: float = LAMBDA_DL) -> pd.DataFrame:
    """Les betas mois par mois (chaque mois n'utilise que sa propre coupe : aucune fuite temporelle)."""
    taus = np.array(monthly.columns, dtype=float)
    x = loadings(taus, lam)
    betas, rmses = [], []
    for _, row in monthly.iterrows():
        y = row.to_numpy(dtype=float)
        ok = np.isfinite(y)
        b, *_ = np.linalg.lstsq(x[ok], y[ok], rcond=None)
        betas.append(b)
        rmses.append(float(np.sqrt(np.mean((x[ok] @ b - y[ok]) ** 2))))
    out = pd.DataFrame(betas, index=monthly.index, columns=["niveau", "pente", "courbure"])
    out["rmse_ajustement"] = rmses
    return out


def ar1_forecast(series: np.ndarray, horizon: int) -> float:
    """AR(1) avec constante estimé par MCO, itéré `horizon` pas."""
    y, x = series[1:], series[:-1]
    x1 = np.column_stack([np.ones_like(x), x])
    (c, phi), *_ = np.linalg.lstsq(x1, y, rcond=None)
    f = series[-1]
    for _ in range(horizon):
        f = c + phi * f
    return float(f)


def dns_backtest(monthly: pd.DataFrame, betas: pd.DataFrame,
                 horizons: tuple[int, ...] = (1, 6, 12),
                 eval_taus: tuple[float, ...] = (0.25, 1, 2, 3, 5, 7, 10, 20, 30),
                 start: str = "1996-01", min_obs: int = 60) -> pd.DataFrame:
    """Prévisions hors échantillon : DNS (AR(1) par facteur), AR(1) direct par rendement, marche aléatoire.

    À chaque origine t, l'AR(1) n'est estimé que sur les betas (ou rendements) jusqu'à t, en fenêtre
    expansive ; la marche aléatoire prédit la courbe de t ; la cible est la courbe de t + h.
    Retourne une ligne par (origine, horizon, maturité, modèle) avec l'erreur de prévision.
    """
    idx = monthly.index
    first = max(idx.get_loc(pd.Period(start, "M")), min_obs)
    x_eval = loadings(np.array(eval_taus))
    rows = []
    for h in horizons:
        for t in range(first, len(idx) - h):
            target = monthly.iloc[t + h][list(eval_taus)].to_numpy(dtype=float)
            spot = monthly.iloc[t][list(eval_taus)].to_numpy(dtype=float)
            b_hist = betas.iloc[: t + 1][["niveau", "pente", "courbure"]].to_numpy()
            b_hat = np.array([ar1_forecast(b_hist[:, k], h) for k in range(3)])
            dns = x_eval @ b_hat
            ar_direct = np.array([ar1_forecast(monthly[tau].iloc[: t + 1].dropna().to_numpy(dtype=float), h)
                                  for tau in eval_taus])
            for j, tau in enumerate(eval_taus):
                if not (np.isfinite(spot[j]) and np.isfinite(target[j])):
                    continue                     # le 30 ans manque avant 1991 : la paire est écartée
                for model, pred in [("dns", dns[j]), ("ar1", ar_direct[j]), ("rw", spot[j])]:
                    rows.append({"origine": str(idx[t]), "horizon": h, "maturite": tau,
                                 "modele": model, "erreur": float(pred - target[j])})
    return pd.DataFrame(rows)


def rmse_table(errors: pd.DataFrame) -> pd.DataFrame:
    """RMSE par modèle, horizon et maturité, et ratio contre la marche aléatoire."""
    rmse = (errors.assign(e2=lambda d: d["erreur"] ** 2)
            .groupby(["horizon", "maturite", "modele"])["e2"].mean() ** 0.5).unstack("modele")
    for m in ("dns", "ar1"):
        rmse[f"ratio_{m}_rw"] = rmse[m] / rmse["rw"]
    return rmse.reset_index()


def dm_test(e1: np.ndarray, e2: np.ndarray, horizon: int) -> tuple[float, float]:
    """Diebold-Mariano sur les erreurs quadratiques, variance HAC (Bartlett, h-1 retards), correction Harvey."""
    from scipy import stats

    d = e1**2 - e2**2
    n = len(d)
    dbar = d.mean()
    gamma0 = np.mean((d - dbar) ** 2)
    var = gamma0
    for lag in range(1, horizon):
        w = 1.0 - lag / horizon
        cov = np.mean((d[lag:] - dbar) * (d[:-lag] - dbar))
        var += 2.0 * w * cov
    var = max(var, 1e-12) / n
    stat = dbar / np.sqrt(var)
    k = np.sqrt((n + 1 - 2 * horizon + horizon * (horizon - 1) / n) / n)   # Harvey et al. (1997)
    stat *= k
    p = 2.0 * (1.0 - stats.t.cdf(abs(stat), df=n - 1))
    return float(stat), float(p)
