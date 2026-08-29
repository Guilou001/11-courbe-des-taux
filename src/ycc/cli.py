"""Ligne de commande : télécharger, factoriser la courbe, prévoir, prédire les récessions, choquer le bilan."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="La courbe des taux canadienne : facteurs Nelson-Siegel, prévision Diebold-Li "
                       "contre marche aléatoire, probit de récession, ALM sous chocs IRRBB.")


@app.callback()
def main() -> None:
    """Sous-commandes nommées."""


@app.command()
def fetch() -> None:
    """Courbe zéro-coupon BdC, primes de terme Valet, chronologie C.D. Howe."""
    from ycc import data

    data.fetch()
    curve = data.load_curve()
    tp = data.load_term_premium()
    eps = data.load_recessions()
    typer.echo(f"courbe : {len(curve)} jours, {curve.index[0].date()} -> {curve.index[-1].date()}, "
               f"{curve.shape[1]} maturités ; prime de terme : {tp.index[0]} -> {tp.index[-1]} ; "
               f"récessions C.D. Howe : {len(eps)}")


@app.command()
def factors(out: Path = Path("results")) -> None:
    """Les betas Nelson-Siegel mois par mois, la figure des facteurs et les instantanés."""
    from ycc import data, figures, ns

    monthly = data.monthly_curve(data.load_curve())
    betas = ns.fit_history(monthly)
    eps = data.load_recessions()
    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)
    betas.round(4).to_csv(tables / "facteurs_ns.csv")
    figures.fig_factors(betas, eps, figs / "facteurs_ns.png")
    figures.fig_snapshots(monthly, ["1990-04", "2007-06", "2020-07", "2022-12", str(monthly.index[-1])],
                          figs / "courbes_instantanees.png")
    typer.echo(f"betas : {len(betas)} mois ; RMSE d'ajustement moyen "
               f"{betas['rmse_ajustement'].mean() * 100:.1f} pb ; "
               f"corr(niveau, 10 ans) = {betas['niveau'].corr(monthly[10.0]):.3f}")


@app.command()
def forecast(out: Path = Path("results")) -> None:
    """Le duel Diebold-Li contre la marche aléatoire, 1996-2026, h = 1, 6 et 12 mois."""
    import pandas as pd

    from ycc import data, figures, ns

    monthly = data.monthly_curve(data.load_curve())
    betas = ns.fit_history(monthly)
    errors = ns.dns_backtest(monthly, betas)
    rmse = ns.rmse_table(errors)
    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)
    errors.to_csv(tables / "erreurs_prevision.csv", index=False)
    rmse.round(4).to_csv(tables / "rmse_prevision.csv", index=False)
    dm_rows = []
    for h in sorted(errors["horizon"].unique()):
        for tau in sorted(errors["maturite"].unique()):
            sub = errors[(errors["horizon"] == h) & (errors["maturite"] == tau)]
            piv = sub.pivot(index="origine", columns="modele", values="erreur")
            stat, p = ns.dm_test(piv["dns"].to_numpy(), piv["rw"].to_numpy(), h)
            dm_rows.append({"horizon": h, "maturite": tau, "dm_dns_vs_rw": stat, "p": p})
    pd.DataFrame(dm_rows).round(4).to_csv(tables / "diebold_mariano.csv", index=False)
    figures.fig_forecast(rmse, figs / "prevision_rmse.png")
    moy = rmse.groupby("horizon")["ratio_dns_rw"].mean()
    typer.echo("ratio RMSE DNS/RW moyen par horizon : "
               + ", ".join(f"h={h} : {v:.3f}" for h, v in moy.items()))


@app.command()
def recession(out: Path = Path("results"), horizon: int = 12) -> None:
    """Le probit : pente brute contre pente nette contre écart forward, et le test de 2022-23."""
    import pandas as pd

    from ycc import data, figures
    from ycc import recession as rec

    monthly = data.monthly_curve(data.load_curve())
    tp = data.load_term_premium()
    eps = data.load_recessions()
    feats = rec.features(monthly, tp)
    indic = data.recession_indicator(feats.index, eps)
    target = data.recession_within(indic, horizon=horizon)

    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    commun = feats.dropna().index                            # 1995+ : la prime ACM borne l'échantillon commun
    rows, probs = [], {}
    for col in feats.columns:
        fit, sample = rec.probit_fit(feats[col], target)
        score = -feats[col].loc[sample].to_numpy()           # pente basse = risque haut
        y = target.loc[sample].to_numpy().astype(int)
        a = rec.auroc(y, score)
        lo, hi = rec.auroc_block_bootstrap(y, score)
        cc = sample.intersection(commun)
        a_commun = rec.auroc(target.loc[cc].to_numpy().astype(int), -feats[col].loc[cc].to_numpy())
        oos = rec.oos_probabilities(feats[col], target, start="1996-01")
        probs[col] = oos
        oos_common = oos.index.intersection(target.dropna().index)
        a_oos = rec.auroc(target.loc[oos_common].to_numpy().astype(int),
                          oos.loc[oos_common].to_numpy())
        # la récession de 2020 est une pandémie : la fenêtre dont la cible la contient est retirée
        hors_covid = oos_common[(oos_common < pd.Period("2019-03", "M"))
                                | (oos_common > pd.Period("2020-04", "M"))]
        y_hc = target.loc[hors_covid].to_numpy().astype(int)
        a_oos_hc = rec.auroc(y_hc, oos.loc[hors_covid].to_numpy()) if 0 < y_hc.sum() < len(y_hc) \
            else float("nan")
        p2223 = oos.loc[pd.Period("2022-01", "M"):pd.Period("2023-12", "M")]
        p2008 = oos.loc[pd.Period("2007-01", "M"):pd.Period("2008-10", "M")]
        rows.append({"variable": col,
                     "debut": str(feats[col].dropna().index[0]), "debut_oos": str(oos.index[0]),
                     "coef": float(fit.params.iloc[1]),
                     "pseudo_r2": float(fit.prsquared), "auroc_in": a,
                     "auroc_ic90_bas": lo, "auroc_ic90_haut": hi,
                     "auroc_in_commun_1995": a_commun, "auroc_oos": a_oos,
                     "auroc_oos_hors_covid": a_oos_hc,
                     "prob_max_2022_23": float(p2223.max()) if len(p2223) else float("nan"),
                     "prob_max_avant_2008": float(p2008.max()) if len(p2008) else float("nan")})
    suffix = "" if horizon == 12 else f"_h{horizon}"
    table = pd.DataFrame(rows)
    table.round(4).to_csv(tables / f"probit_recession{suffix}.csv", index=False)
    feats.round(4).to_csv(tables / "pentes_mensuelles.csv")
    pd.DataFrame(probs).round(4).to_csv(tables / f"probabilites_oos{suffix}.csv")
    labels = {"pente_brute": "pente brute", "pente_nette": "pente nette de prime",
              "ecart_forward": "écart forward"}
    figures.fig_recession(feats, {labels[k]: v for k, v in probs.items()}, eps,
                          figs / f"probit_recession{suffix}.png")
    typer.echo(table.round(3).to_string(index=False))


@app.command()
def alm(out: Path = Path("results")) -> None:
    """Le bilan stylisé sous les six chocs IRRBB et sous le choc mesuré de 2022 ; le classeur Excel."""
    import pandas as pd

    from ycc import alm as mod
    from ycc import data, excel, figures

    curve = data.load_curve()
    last = curve.iloc[-1]
    bilan = mod.bilan_stylise()
    move_2022 = curve.loc[:"2022-12-31"].iloc[-1] - curve.loc[:"2021-12-31"].iloc[-1]
    extra = {"2022 mesuré (déc. 2021 -> déc. 2022)": last + move_2022}
    delta = mod.delta_eve_scenarios(last, bilan, extra=extra)
    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)
    delta.round(3).to_csv(tables / "delta_eve.csv", index=False)
    krd = mod.key_rate_durations(last, coupon_pct=4.0, maturity=10.0)
    krd.round(4).to_csv(tables / "krd_obligation_10ans.csv")
    nii = pd.DataFrame([{"choc_pp": s, "delta_nii_12m": mod.delta_nii_12m(bilan, s)}
                        for s in (+2.0, -2.0)])
    nii.round(3).to_csv(tables / "delta_nii.csv", index=False)
    figures.fig_alm(delta, figs / "delta_eve.png")
    excel.build_workbook(last, str(curve.index[-1].date()), Path("reports/calculs_obligataires.xlsx"))
    regl = delta[~delta["scenario"].str.startswith("2022")]
    pire = regl.loc[regl["delta_eve"].idxmin(), "scenario"]      # la perte la plus profonde, pas |max|
    typer.echo(f"choc court 2022 mesuré : 3 mois {move_2022[0.25]:+.2f} pp, 10 ans {move_2022[10.0]:+.2f} pp ; "
               f"pire scénario réglementaire : {pire} ; "
               f"classeur -> reports/calculs_obligataires.xlsx")


if __name__ == "__main__":
    app()
