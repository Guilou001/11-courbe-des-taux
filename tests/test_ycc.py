"""Chaque brique contre une vérité connue : Nelson-Siegel exact, forwards plats, prix fermés, chocs."""

import numpy as np
import pandas as pd
import pytest

from ycc.alm import (
    Poste,
    bond_price,
    delta_nii_12m,
    interp_zero,
    irrbb_shocks,
    key_rate_durations,
    modified_duration,
)
from ycc.data import recession_indicator, recession_within
from ycc.ns import LAMBDA_DL, ar1_forecast, dm_test, fit_curve, fit_history, loadings

TAUS = np.arange(0.25, 30.25, 0.25)


def test_ns_fit_recovers_known_betas_exactly():
    beta_true = np.array([4.0, -2.0, 1.5])
    y = loadings(TAUS) @ beta_true
    assert fit_curve(y, TAUS) == pytest.approx(beta_true, abs=1e-10)


def test_ns_loading_limits():
    x = loadings(np.array([1e-6, 1e6]))
    assert x[0, 1] == pytest.approx(1.0, abs=1e-4)     # la charge de pente vaut 1 en tau = 0
    assert x[0, 2] == pytest.approx(0.0, abs=1e-4)     # la courbure part de 0
    assert x[1, 1] == pytest.approx(0.0, abs=1e-4)     # et tout s'éteint à l'infini sauf le niveau
    curv = loadings(TAUS)[:, 2]
    assert TAUS[np.argmax(curv)] == pytest.approx(2.5, abs=0.25)   # Diebold-Li : maximum à 30 mois
    assert LAMBDA_DL == pytest.approx(0.0609 * 12)


def test_fit_history_one_month_per_row():
    idx = pd.period_range("2000-01", periods=3, freq="M")
    curves = pd.DataFrame([loadings(TAUS) @ [4, -2, 1]] * 3, index=idx, columns=TAUS)
    betas = fit_history(curves)
    assert betas.shape[0] == 3
    assert betas["rmse_ajustement"].max() < 1e-10


def test_ar1_forecast_recovers_persistence():
    rng = np.random.default_rng(0)
    phi, c = 0.9, 0.5
    y = [0.0]
    for _ in range(2000):
        y.append(c + phi * y[-1] + 0.1 * rng.standard_normal())
    series = np.array(y)
    f1 = ar1_forecast(series, 1)
    assert f1 == pytest.approx(c + phi * series[-1], abs=0.05)
    f_inf = ar1_forecast(series, 600)
    assert f_inf == pytest.approx(c / (1 - phi), abs=0.3)  # convergence vers la moyenne


def test_dm_test_detects_a_dominated_model():
    rng = np.random.default_rng(1)
    e2 = rng.standard_normal(300)
    e1 = e2 + 1.0                                # erreurs systématiquement plus grandes
    stat, p = dm_test(e1, e2, horizon=1)
    assert stat > 3 and p < 0.01
    e3 = rng.standard_normal(300)                # même loi, indépendant : aucun modèle ne domine
    stat0, _ = dm_test(e2, e3, horizon=1)
    assert abs(stat0) < 3


def test_recession_indicator_convention():
    idx = pd.period_range("1990-01", "1990-12", freq="M")
    eps = [(pd.Period("1990-03", "M"), pd.Period("1990-06", "M"))]
    flag = recession_indicator(idx, eps)
    assert flag[pd.Period("1990-03", "M")] == 0          # le pic est le dernier mois d'expansion
    assert flag[pd.Period("1990-04", "M")] == 1
    assert flag[pd.Period("1990-06", "M")] == 1
    assert flag[pd.Period("1990-07", "M")] == 0


def test_recession_within_hand_case():
    idx = pd.period_range("2000-01", periods=30, freq="M")
    indic = pd.Series(0, index=idx)
    indic[pd.Period("2001-06", "M")] = 1                 # un seul mois de récession
    target = recession_within(indic, horizon=12)
    assert target[pd.Period("2000-06", "M")] == 1.0      # 12 mois avant : visible
    assert target[pd.Period("2000-05", "M")] == 0.0      # 13 mois avant : hors fenêtre
    assert target[pd.Period("2001-05", "M")] == 1.0
    assert target[pd.Period("2001-06", "M")] == 0.0      # le mois même ne compte plus


def test_forward_on_flat_curve_is_flat():
    # composition continue : f = (z2*t2 - z1*t1)/(t2 - t1) = z sur une courbe plate
    z = 3.0
    f = (z * 1.75 - z * 1.5) / 0.25
    assert f == pytest.approx(z)


def test_bond_price_flat_curve_closed_form():
    flat = pd.Series(5.0, index=TAUS)
    # obligation 2 ans, coupon 5 % semestriel : prix = somme fermée en composition continue
    times = np.array([0.5, 1.0, 1.5, 2.0])
    cfs = np.array([2.5, 2.5, 2.5, 102.5])
    expected = float(np.sum(cfs * np.exp(-0.05 * times)))
    assert bond_price(flat, 5.0, 2.0) == pytest.approx(expected, abs=1e-10)


def test_zero_coupon_duration_equals_maturity():
    flat = pd.Series(4.0, index=TAUS)
    d = modified_duration(flat, coupon_pct=0.0, maturity=7.0)
    assert d == pytest.approx(7.0, rel=1e-3)             # en composition continue, D = tau exactement


def test_key_rate_durations_sum_to_total():
    flat = pd.Series(4.0, index=TAUS)
    krd = key_rate_durations(flat, coupon_pct=4.0, maturity=10.0)
    total = modified_duration(flat, coupon_pct=4.0, maturity=10.0)
    assert float(krd.sum()) == pytest.approx(total, rel=1e-2)


def test_interp_zero_linear():
    row = pd.Series([2.0, 4.0], index=[1.0, 2.0])
    assert interp_zero(row, np.array([1.5]))[0] == pytest.approx(3.0)


def test_irrbb_shock_shapes():
    taus = np.array([0.25, 30.0])
    s = irrbb_shocks(taus)
    assert s["parallele_hausse"][0] == pytest.approx(2.0)
    assert s["court_hausse"][0] > s["court_hausse"][1]           # le choc court s'éteint avec l'échéance
    assert s["pentification"][0] < 0 < s["pentification"][1]     # pentification : court baisse, long monte
    assert s["aplatissement"][0] > 0 > s["aplatissement"][1]


def test_delta_eve_sign_for_asset_long_book():
    from ycc.alm import bilan_stylise, delta_eve_scenarios

    flat = pd.Series(4.0, index=TAUS)
    delta = delta_eve_scenarios(flat, bilan_stylise())
    par_up = delta.set_index("scenario").loc["parallele_hausse", "delta_eve"]
    assert par_up < 0        # duration d'actif > duration de passif : la hausse des taux coûte


def test_delta_nii_hand_case():
    bilan = [Poste("actif variable", 100.0, 0.0, 0.25, 3.0),
             Poste("passif fixe", -100.0, 0.0, 5.0, 60.0)]
    # +200 pb : l'actif se refixe au mois 3, 9 mois de portage : 100 * 2 % * 9/12 = 1,5 G$
    assert delta_nii_12m(bilan, 2.0) == pytest.approx(1.5)


def test_delta_nii_depend_du_beta_de_depot():
    # le poste de dépôts à vue porte une duration COMPORTEMENTALE de 2,5 ans pour l'actualisation ;
    # son taux, lui, se révise en continu. Le confondre avec une refixation à 30 mois revient à
    # poser un bêta nul, et le gap devient positif par construction.
    bilan = [Poste("actif variable", 100.0, 0.0, 0.25, 3.0),
             Poste("dépôts à vue (duration comportementale)", -100.0, 0.0, 2.5, 30.0)]
    assert delta_nii_12m(bilan, 2.0, beta_depot=0.0) == pytest.approx(1.5)
    assert delta_nii_12m(bilan, 2.0, beta_depot=0.5) == pytest.approx(1.5 - 1.0)
    assert delta_nii_12m(bilan, 2.0, beta_depot=1.0) == pytest.approx(1.5 - 2.0)


def test_delta_nii_du_bilan_precepte_change_de_signe_avec_le_beta():
    from ycc.alm import bilan_stylise

    b = bilan_stylise()
    assert delta_nii_12m(b, 2.0, beta_depot=0.0) > 0.0
    assert delta_nii_12m(b, 2.0, beta_depot=1.0) < 0.0
