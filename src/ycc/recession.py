"""Le probit de récession : pente brute, pente nette de prime de terme, écart forward de court terme.

Estrella et Mishkin (1998) montrent que la pente 10 ans moins 3 mois domine les autres variables
financières pour prédire les récessions américaines ; Engstrom et Sharpe (2019) répondent que
l'écart forward de court terme, le taux à 3 mois attendu dans 6 trimestres moins le taux à 3 mois
courant, capte la même information sans le bruit de la prime de terme.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def features(monthly: pd.DataFrame, tp_10y: pd.Series) -> pd.DataFrame:
    """Les trois pentes mensuelles, en points de pourcentage, chacune sur son échantillon maximal.

    La pente brute et l'écart forward ne demandent que la courbe (1986-) ; la pente nette retire
    la prime de terme ACM à 10 ans (disponible depuis 1995 seulement, mesuré) de la pente brute :
    il reste l'écart des anticipations de taux courts, la composante que la théorie relie au
    cycle. La prime du taux à 3 mois est traitée comme nulle, approximation déclarée.
    """
    z3m, z10 = monthly[0.25], monthly[10.0]
    # forward 3 mois dans 6 trimestres, composition continue : f = (z2*t2 - z1*t1)/(t2 - t1)
    t1, t2 = 1.5, 1.75
    fwd = (monthly[t2] * t2 - monthly[t1] * t1) / (t2 - t1)
    return pd.DataFrame({
        "pente_brute": z10 - z3m,
        "pente_nette": (z10 - z3m) - tp_10y.reindex(monthly.index),
        "ecart_forward": fwd - z3m,
    })


def probit_fit(x: pd.Series, y: pd.Series):
    """Probit à une variable, constante incluse (statsmodels)."""
    import statsmodels.api as sm

    common = x.dropna().index.intersection(y.dropna().index)
    model = sm.Probit(y.loc[common].astype(float), sm.add_constant(x.loc[common].astype(float)))
    return model.fit(disp=0), common


def auroc(y: np.ndarray, score: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    return float(roc_auc_score(y, score))


def auroc_block_bootstrap(y: np.ndarray, score: np.ndarray, block: int = 24,
                          n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """L'intervalle à 90 % de l'AUROC par bootstrap de blocs mobiles (les mois sont autocorrélés).

    Les tirages sans les deux classes sont rejetés ; avec trois récessions par échantillon,
    l'intervalle est large, et c'est le message.
    """
    rng = np.random.default_rng(seed)
    n = len(y)
    stats = []
    while len(stats) < n_boot:
        starts = rng.integers(0, n - block + 1, size=int(np.ceil(n / block)))
        take = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        yb, sb = y[take], score[take]
        if yb.min() == yb.max():
            continue
        stats.append(auroc(yb, sb))
    return float(np.percentile(stats, 5)), float(np.percentile(stats, 95))


def oos_probabilities(x: pd.Series, y: pd.Series, start: str = "2000-01",
                      horizon: int = 12) -> pd.Series:
    """Les probabilités hors échantillon : à chaque mois, le probit n'est estimé que sur le passé.

    La cible du mois t (récession dans les `horizon` mois) n'est observable qu'en t + horizon :
    l'estimation à l'origine t n'utilise que les cibles des mois <= t - horizon, sinon
    l'information fuit.
    """
    import statsmodels.api as sm

    x = x.dropna()
    origins = x.loc[pd.Period(start, "M"):].index
    probs = {}
    for t in origins:
        past = y.loc[: t - horizon].dropna()
        xt = x.reindex(past.index).dropna()
        past = past.loc[xt.index]
        if len(past) < 60 or past.min() == past.max():
            continue
        fit = sm.Probit(past.astype(float), sm.add_constant(xt.astype(float))).fit(disp=0)
        probs[t] = float(fit.predict([1.0, x.loc[t]])[0])
    return pd.Series(probs).sort_index()
