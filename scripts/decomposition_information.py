#!/usr/bin/env python3
"""Pourquoi le meilleur système en RMSE voit le moins de situations critiques.

La question qui a produit ce script
-------------------------------------
Le tableau comparatif donne, sur NO₂ : notre modèle **premier en RMSE** et **avant-dernier
en détections** — 24 situations critiques vues sur 886, contre 137 pour le krigeage. Deux
lectures possibles :

* soit notre modèle est moins **informatif** que le krigeage sur les pics ;
* soit il est aussi informatif mais **moins ample**, et rate le seuil par construction.

Ce sont deux affirmations très différentes. La première condamnerait l'approche. La seconde
désigne un **paramètre libre mal réglé**. Ce script tranche, et la démonstration tient en
une décomposition connue.

La décomposition, et ce qu'elle sépare
----------------------------------------
Pour tout prédicteur `x` d'une observation `y` :

    MSE = (μx − μy)²  +  (σx − r·σy)²  +  σy²(1 − r²)
          ╰─ biais ─╯    ╰─ amplitude ─╯   ╰─ information ─╯

Les deux premiers termes sont des **paramètres libres** : toute recalibration affine
`x' = a + b·x` les fixe à volonté **sans toucher `r`**. Le troisième ne dépend que de `r`,
et `r` ne s'achète pas — c'est la seule quantité rare.

Conséquence directe, et c'est tout le sujet : minimiser la MSE **impose** `σx = r·σy`.
Comme `r < 1`, l'optimum RMSE est **sous-dispersé par construction**. Un prédicteur
sous-dispersé franchit rarement un seuil haut. Le déficit de détection n'est donc pas un
défaut du modèle : c'est la signature de son point de fonctionnement.

Les trois mesures, et pourquoi ces trois-là
---------------------------------------------
1. **Le plancher d'information** `σy·√(1−r²)` — la RMSE que chaque système atteindrait
   après recalibration affine parfaite. Il classe les systèmes sur leur information seule,
   biais et amplitude neutralisés. C'est le classement qui ne dépend d'aucun réglage.

2. **La détection à budget d'alerte égal** — on prend les `N` prédictions les plus fortes
   de chaque système, `N` = nombre de situations critiques réellement observées, et on
   compte les bonnes. **Invariant par toute transformation monotone** : ni l'amplitude ni
   le biais n'y entrent. C'est la mesure honnête du pouvoir de détection.

3. **La détection après recalage d'amplitude** — ce que chaque système voit une fois son
   paramètre libre réglé pour la détection (`σx = σy`) plutôt que pour la RMSE.

⚠️ Le recalage est **sans fuite, et strictement** : pour le mois `m` à la station `s`, les
moments viennent des mois **antérieurs à m** et des stations **autres que s**. Pas de
l'échantillon de test, pas du mois courant, pas de la station évaluée. L'exclusion de la
station se fait par soustraction de sa contribution aux sommes — exact, pas approché.

Ce que ce script ne fait pas
------------------------------
Il ne réajuste aucun modèle. Il lit les prédictions déjà écrites par `tableau_comparatif.py`
et n'opère que des transformations monotones. Aucun chiffre ici ne peut être meilleur que
ce que le modèle sait déjà : on ne fait que **choisir où le poser**.

Usage  : python3 scripts/decomposition_information.py --polluant NO2 --horizon 2
Entrée : data/processed/predictions/comparatif_<polluant>_h<n>.parquet
Sortie : reports/decomposition_information_<polluant>_h<n>.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from tableau_comparatif import BANDES, NOM_BANDE, NOM_POLLUANT, classe  # noqa: E402

MIN_HISTORIQUE = 3_000   # en deçà, les moments antérieurs sont trop bruités pour recaler


def moments_anterieurs(d: pd.DataFrame, colonnes: list[str],
                       saison: int | None = None) -> dict[str, np.ndarray]:
    """Moyenne et écart-type des mois **antérieurs**, station de test **exclue**.

    L'exclusion est exacte : on retranche la contribution de la station aux sommes
    cumulées, on ne l'approche pas. Sans elle, la station évaluée participerait à son
    propre étalon — une fuite ténue mais réelle, et invérifiable une fois publiée.

    Renvoie, pour chaque colonne, deux vecteurs alignés sur les lignes de `d`
    (`NaN` là où l'historique est insuffisant).
    """
    t = d[["mois", "station_id"] + colonnes].copy()
    for c in colonnes:
        t[f"__{c}2"] = t[c].to_numpy() ** 2
    agg = {"n": ("station_id", "size")}
    for c in colonnes:
        agg[f"s_{c}"] = (c, "sum")
        agg[f"q_{c}"] = (f"__{c}2", "sum")
    g = t.groupby(["mois", "station_id"], observed=True).agg(**agg).reset_index()

    sortie = {c: (np.full(len(d), np.nan), np.full(len(d), np.nan)) for c in colonnes}
    mois = np.sort(d["mois"].unique())
    lignes_mois = {m: np.flatnonzero((d["mois"] == m).to_numpy()) for m in mois}
    if saison is not None:
        g["_mc"] = g["mois"].str.slice(5, 7).astype(int)
    for m in mois:
        avant = g[g["mois"] < m]
        # ⚠️ Restreindre l'historique au **même régime saisonnier** quand on le demande.
        # Sans cela, l'étalon d'un mois de juillet est dilué par les hivers : mesuré le
        # 04/08 sur l'ozone, le rapport σ prédite/σ observée tombait à 0,903 en juillet
        # 2026 — une sous-dispersion qui fait manquer le seuil par construction, et que le
        # recalage était précisément censé corriger.
        if saison is not None:
            mc = int(m[5:7])
            proches = {((mc - 1 + k) % 12) + 1 for k in range(-saison, saison + 1)}
            avant = avant[avant["_mc"].isin(proches)]
        if avant["n"].sum() < MIN_HISTORIQUE:
            continue
        total = avant.drop(columns=["mois", "station_id"],
                           errors="ignore").select_dtypes("number").sum()
        total = total.drop(labels=["_mc"], errors="ignore")
        par_st = avant.drop(columns=["_mc"], errors="ignore").groupby(
            "station_id").sum(numeric_only=True)
        idx = lignes_mois[m]
        st = d["station_id"].to_numpy()[idx]
        # contribution propre de chaque station — 0 si elle n'apparaît pas avant `m`
        contrib = par_st.reindex(pd.Index(st)).fillna(0.0)
        n = total["n"] - contrib["n"].to_numpy()
        valide = n >= 200
        for c in colonnes:
            s = total[f"s_{c}"] - contrib[f"s_{c}"].to_numpy()
            q = total[f"q_{c}"] - contrib[f"q_{c}"].to_numpy()
            mu = np.where(valide, s / np.where(n > 0, n, 1), np.nan)
            var = np.where(valide, q / np.where(n > 0, n, 1) - mu ** 2, np.nan)
            sortie[c][0][idx] = mu
            sortie[c][1][idx] = np.sqrt(np.maximum(var, 0.0))
    return sortie


def detection(obs_crit: np.ndarray, x: np.ndarray, polluant: str) -> tuple[int, int]:
    """Situations critiques vues et fausses alertes, au seuil de bande ATMO."""
    p = classe(x, polluant) >= 3
    return int((p & obs_crit).sum()), int((p & ~obs_crit).sum())


def main(polluant: str, horizon: int) -> int:
    src = RACINE / f"data/processed/predictions/comparatif_{polluant}_h{horizon}.parquet"
    ref = RACINE / f"data/processed/predictions/systemes_{polluant}_h{horizon}.csv"
    if not src.exists():
        raise SystemExit(f"absent : {src.relative_to(RACINE)} — lancer d'abord "
                         f"tableau_comparatif.py --polluant {polluant}")
    d = pd.read_parquet(src)
    noms = dict(pd.read_csv(ref)[["code", "systeme"]].to_numpy())
    syst = [c for c in d.columns if c.startswith("sys")]
    if not syst:
        raise SystemExit("aucune colonne de système dans le parquet")
    if len(noms) != len(syst):
        raise SystemExit(f"{len(syst)} systèmes dans le parquet, {len(noms)} nommés")

    y = d["valeur"].to_numpy()
    sy, my = float(y.std()), float(y.mean())
    crit = classe(y, polluant) >= 3
    n_crit = int(crit.sum())
    ech = "J0" if horizon == 1 else f"J+{horizon - 1}"
    print(f"{NOM_POLLUANT[polluant]} · {ech} · {len(d):,} prédictions · "
          f"{len(syst)} systèmes · σ(obs) = {sy:.2f} µg/m³")
    print(f"  {n_crit:,} situations critiques observées "
          f"({100 * n_crit / len(d):.2f} %) — classes « {NOM_BANDE[3]} » et pire, "
          f"seuil {int(BANDES[polluant][3][0])} µg/m³\n")
    if n_crit < 30:
        raise SystemExit(f"{n_crit} situations critiques — trop peu pour conclure")

    # ── 1. La décomposition — ce qui est rare, ce qui est libre ──────────────
    print(f"{'═' * 104}")
    print(f"DÉCOMPOSITION · MSE = biais² + (σx − r·σy)² + σy²(1 − r²)")
    print(f"{'═' * 104}")
    print(f"  {'système':42s} {'r':>6s} {'σx/σy':>7s} {'biais':>7s} {'RMSE':>7s} "
          f"{'plancher':>9s} {'perdu':>7s}")
    lignes = []
    for c in syst:
        x = d[c].to_numpy()
        r = float(np.corrcoef(y, x)[0, 1])
        sx, mx = float(x.std()), float(x.mean())
        rm = float(np.sqrt(np.mean((x - y) ** 2)))
        plancher = sy * np.sqrt(max(1 - r ** 2, 0.0))
        print(f"  {noms[c][:42]:42s} {r:6.3f} {sx / sy:7.3f} {mx - my:+7.2f} "
              f"{rm:7.2f} {plancher:9.2f} {100 * (1 - plancher / rm):6.1f}%")
        lignes.append({"polluant": polluant, "horizon": horizon, "systeme": noms[c],
                       "r": r, "rho_spearman": float(pd.Series(y).corr(
                           pd.Series(x), method="spearman")),
                       "sigma_ratio": sx / sy, "biais": mx - my, "rmse": rm,
                       "plancher_information": plancher})
    print(f"\n  `plancher` = σy·√(1−r²) : la RMSE atteignable après recalibration affine")
    print(f"  parfaite — biais et amplitude annulés. Il ne dépend QUE de l'information.")
    print(f"  `perdu` = la part de RMSE imputable aux deux paramètres libres, donc")
    print(f"  récupérable sans rien apprendre de plus.")

    # ── 2. Détection à budget d'alerte égal — invariante par monotonie ───────
    print(f"\n{'═' * 104}")
    print(f"DÉTECTION À BUDGET ÉGAL · les {n_crit:,} plus fortes prédictions de chaque "
          f"système")
    print(f"{'═' * 104}")
    print(f"  Invariant par toute transformation monotone : ni l'amplitude ni le biais")
    print(f"  n'y entrent. C'est le pouvoir de détection **nu**.\n")
    print(f"  {'système':42s} {'vues':>7s} {'/':1s}{'total':>6s} {'taux':>8s} "
          f"{'× hasard':>9s}")
    hasard = n_crit * n_crit / len(d)
    for c, ln in zip(syst, lignes):
        x = d[c].to_numpy()
        haut = np.argsort(-x, kind="stable")[:n_crit]
        vues = int(crit[haut].sum())
        print(f"  {noms[c][:42]:42s} {vues:7d} /{n_crit:6d} "
              f"{100 * vues / n_crit:7.1f}% {vues / hasard:8.1f}×")
        ln.update(budget_egal_vues=vues, budget_egal_taux_pct=100 * vues / n_crit,
                  budget_egal_vs_hasard=vues / hasard)

    # ── 3. Détection au seuil, avant et après recalage d'amplitude ───────────
    mom = moments_anterieurs(d, ["valeur"] + syst)
    mu_y, sd_y = mom["valeur"]
    couvert = np.isfinite(mu_y)
    print(f"\n{'═' * 104}")
    print(f"DÉTECTION AU SEUIL ATMO · avant / après recalage d'amplitude "
          f"({100 * couvert.mean():.0f} % des lignes recalables)")
    print(f"{'═' * 104}")
    print(f"  Recalage : x' = μy + (σy/σx)·(x − μx), moments des mois ANTÉRIEURS et des")
    print(f"  stations AUTRES que celle évaluée. Transformation monotone : `r` inchangé.\n")
    print(f"  {'système':42s} {'brut':>13s} {'recalé':>13s} {'fausses':>9s} "
          f"{'précision':>10s} {'RMSE':>7s}")
    sous = crit[couvert]
    for c, ln in zip(syst, lignes):
        x = d[c].to_numpy()
        mu_x, sd_x = mom[c]
        v0, f0 = detection(sous, x[couvert], polluant)
        ech_x = np.where(sd_x > 1e-9, sd_y / np.maximum(sd_x, 1e-9), 1.0)
        xr = mu_y + ech_x * (x - mu_x)
        xr = np.clip(xr, 0.0, None)[couvert]
        v1, f1 = detection(sous, xr, polluant)
        rmse_r = float(np.sqrt(np.mean((xr - y[couvert]) ** 2)))
        prec = v1 / max(v1 + f1, 1)
        fleche = "→" if v1 != v0 else "="
        print(f"  {noms[c][:42]:42s} {v0:6d} ({100 * v0 / sous.sum():4.1f}%) {fleche} "
              f"{v1:6d} ({100 * v1 / sous.sum():4.1f}%) {f1:9d} {100 * prec:9.1f}% "
              f"{rmse_r:7.2f}")
        ln.update(n_recalable=int(couvert.sum()), critiques_recalables=int(sous.sum()),
                  vues_brut=v0, fausses_brut=f0, vues_recale=v1, fausses_recale=f1,
                  precision_recale_pct=100 * prec, rmse_recale=rmse_r)

    # ── 4. Le budget réellement émis par la chaîne en service ────────────────
    # « Budget égal » au nombre de situations critiques est une convention commode. La
    # question opérationnelle est autre : **à volume d'alertes constant pour l'astreinte**,
    # combien d'épisodes de plus attrape-t-on ? Le volume de référence est celui que la
    # chaîne AASQA émet déjà — mesuré, pas choisi.
    i_aasqa = next((k for k, c in enumerate(syst)
                    if "krigeage" in noms[c] and "usuel" in noms[c]), None)
    if i_aasqa is not None:
        xa = d[syst[i_aasqa]].to_numpy()
        budget = int((classe(xa, polluant) >= 3).sum())
        if budget >= 30:
            print(f"\n{'═' * 104}")
            print(f"À VOLUME D'ALERTES CONSTANT · {budget:,} alertes — exactement ce que "
                  f"la chaîne\nen service émet déjà sur cette période\n{'═' * 104}")
            print(f"  {'système':42s} {'attrapés':>9s} {'/':1s}{'total':>6s} "
                  f"{'taux':>8s} {'vs chaîne':>10s}")
            base_v = None
            for c, ln in zip(syst, lignes):
                x = d[c].to_numpy()
                v = int(crit[np.argsort(-x, kind="stable")[:budget]].sum())
                if c == syst[i_aasqa]:
                    base_v = v
                ln["budget_service_vues"] = v
            for c, ln in zip(syst, lignes):
                v = ln["budget_service_vues"]
                delta = (f"{100 * (v / base_v - 1):+9.1f}%" if base_v else " " * 10)
                print(f"  {noms[c][:42]:42s} {v:9d} /{n_crit:6d} "
                      f"{100 * v / n_crit:7.1f}% {delta}")
                ln["budget_service_n"] = budget
            print(f"\n  Lecture : l'astreinte traite le même nombre d'alertes qu'aujourd'hui.")
            print(f"  Seule change la liste. La colonne de droite est le gain net d'épisodes")
            print(f"  attrapés, à charge de travail rigoureusement identique.")

    # ── 5. La courbe : l'avantage dépend-il du budget choisi ? ───────────────
    # Un seul budget peut flatter n'importe qui. Sur PM10, notre modèle passe de −2 % à
    # +10 % selon qu'on lui donne 154 ou 451 alertes. Publier l'un des deux serait
    # choisir son résultat ; on publie donc la courbe, et l'on dit où l'on perd.
    budgets = sorted({max(int(f * n_crit), 20) for f in (0.25, 0.5, 1, 2, 4)}
                     | ({budget} if i_aasqa is not None and budget >= 30 else set()))
    budgets = [b for b in budgets if b < len(d)]
    print(f"\n{'═' * 104}")
    print(f"L'AVANTAGE DÉPEND-IL DU BUDGET ? · épisodes attrapés selon le nombre "
          f"d'alertes émises\n{'═' * 104}")
    print(f"  {'système':42s}" + "".join(f"{b:>10,d}" for b in budgets))
    tri = {c: np.argsort(-d[c].to_numpy(), kind="stable") for c in syst}
    courbe = {}
    for c, ln in zip(syst, lignes):
        v = [int(crit[tri[c][:b]].sum()) for b in budgets]
        courbe[c] = v
        print(f"  {noms[c][:42]:42s}" + "".join(f"{k:>10,d}" for k in v))
        ln.update({f"budget_{b}": k for b, k in zip(budgets, v)})
    i_nous = next((k for k, c in enumerate(syst) if "notre modèle" in noms[c]), None)
    if i_aasqa is not None and i_nous is not None:
        ca = courbe[syst[i_aasqa]]
        cn = courbe[syst[i_nous]]
        print(f"\n  {'notre modèle vs chaîne en service':42s}"
              + "".join(f"{100 * (n / a - 1):>9.1f}%" if a else " " * 10
                        for n, a in zip(cn, ca)))
        perd = [b for b, n, a in zip(budgets, cn, ca) if n < a]
        if perd:
            print(f"\n  ⚠️ Nous perdons aux budgets : "
                  + ", ".join(f"{b:,}" for b in perd) + " alertes. Le krigeage est")
            print(f"     compétitif dans le régime très sélectif ; notre avantage se")
            print(f"     construit dès que le budget s'élargit. C'est dit, pas contourné.")
        else:
            print(f"\n  → Nous dominons à **tous** les budgets testés.")

    m = pd.DataFrame(lignes)
    meilleur_info = m.loc[m["plancher_information"].idxmin(), "systeme"]
    meilleur_det = m.loc[m["budget_egal_vues"].idxmax(), "systeme"]
    print(f"\n  Plancher d'information le plus bas : {meilleur_info}")
    print(f"  Meilleure détection à budget égal   : {meilleur_det}")
    if meilleur_info == meilleur_det:
        print(f"\n  → Le même système domine sur l'information ET sur la détection nue.")
        print(f"    L'arbitrage RMSE / détections n'existe pas : c'est un réglage.")
    else:
        print(f"\n  → Deux systèmes différents dominent. L'arbitrage est réel, et il")
        print(f"    faut le documenter plutôt que le régler.")

    sortie = RACINE / f"reports/decomposition_information_{polluant}_h{horizon}.csv"
    m.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon))
