#!/usr/bin/env python3
"""Les quatre cases du contrat gelé — un ajustement, quatre lectures, une consultation comptée.

À quoi ça répond
----------------
Le projet publie depuis le début une seule case : **stations exclues × dates passées**. Sa
revendication propre — *prédire demain, là où rien ne mesure* — en est une autre, qu'il n'a
jamais mesurée. Ce script mesure les quatre, sur la partition scellée par
`contrat_evaluation.py`, et **enregistre la consultation** dans le journal du contrat.

=============================  ==========================  ==========================
                               **dates passées**            **dates futures**
=============================  ==========================  ==========================
**stations d'entraînement**    ① ajustement (en échantillon) ③ tenue dans le temps
**stations exclues + fossé**   ② transfert spatial          ④ **LA REVENDICATION**
=============================  ==========================  ==========================

⚠️ La case ① est **en échantillon** : même stations, mêmes dates que l'ajustement. Ce n'est
pas un score, c'est un repère de capacité. Elle est affichée pour que l'écart ①→④ se lise,
jamais pour être citée.

Deux fits pour quatre cases, et c'est ce qui les rend comparables
------------------------------------------------------------------
Les cases ① et ③ partagent le même entraînement (dev × passé) ; les cases ② et ④ partagent le
leur (dev moins fossé × passé). **Deux ajustements suffisent donc**, et les quatre lectures
portent sur les mêmes modèles — un écart entre cases mesure la géométrie du test, jamais une
différence d'apprentissage.

Deux périmètres, jamais mélangés
---------------------------------
* ``PARTOUT`` — aucune variable dérivée d'une observation au sol. C'est le seul périmètre où
  la case ④ a un sens : à un endroit non instrumenté, il n'y a pas d'observation de la veille.
* ``AUX_STATIONS`` — retards autorisés (observation J−2, erreurs récentes, fraîcheur). Répond
  à *« corriger là où l'on mesure déjà »*, ce qui est une **autre question**, légitime et
  souvent la plus utile en pratique — mais qu'il ne faut pas présenter comme la première.

L'audit externe R9 désigne la confusion de ces deux périmètres comme la contradiction centrale
du dossier : le levier le plus fort (+8,9 %) appartient au second, et il était cité à côté de
chiffres qui prétendent répondre au premier.

Usage :
  python3 scripts/evaluer_contrat.py --polluant O3 --perimetre PARTOUT --motif "..."
Sortie : reports/contrat_{polluant}_{perimetre}.csv + une ligne dans le journal
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

import contrat_evaluation as ce  # noqa: E402
from aq.eval import comparaison as cmp  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from optuna_mos import typologie  # noqa: E402

GRAINE = 20260802

# Le réglage retenu par l'étude Optuna du 02/08/2026, mesuré contre le réglage réellement
# déployé (LightGBM par défaut) sur la validation interne du développement.
# ⚠️ À mettre à jour depuis `reports/optuna_mos_O3_lgbm.csv` — et à ne PAS choisir d'après
# les scores du contrat, sous peine de transformer le test en jeu de validation.
REGLAGE = {
    "production": {"n_estimators": 400, "learning_rate": 0.05, "num_leaves": 63,
                   "min_child_samples": 200, "subsample": 0.8, "subsample_freq": 1,
                   "colsample_bytree": 0.8},
}


def modele(params: dict):
    from lightgbm import LGBMRegressor

    return LGBMRegressor(random_state=GRAINE, verbose=-1, n_jobs=8, **params)


def jeu(polluant: str, perimetre: str) -> tuple[pd.DataFrame, list[str]]:
    """Le jeu de la case, avec le jeu de variables **du périmètre demandé**."""
    if perimetre not in ce.PERIMETRES:
        raise SystemExit(f"périmètre inconnu « {perimetre} » — attendu "
                         f"{sorted(ce.PERIMETRES)}")
    j0 = charger(polluant, 1)
    colonnes = colonnes_admises(j0)
    j0[colonnes] = j0[colonnes].replace([np.inf, -np.inf], 30_000.0)
    j = agreger_journalier(j0.dropna(subset=["valeur"]), colonnes,
                           GRANDEUR_PAR_POLLUANT[polluant])
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    j["jour"] = pd.to_datetime(j["jour"])
    if j["jour"].dt.tz is not None:
        j["jour"] = j["jour"].dt.tz_localize(None)

    typo, cols_typo = typologie(np.sort(j["station_id"].unique()))
    j = j.merge(typo, on="station_id", how="left")
    predicteurs += cols_typo

    if perimetre == "AUX_STATIONS":
        from apport_observation_veille import variables_passees  # noqa: PLC0415

        passees, noms = variables_passees(j)
        passees["jour"] = pd.to_datetime(passees["jour"])
        j = j.merge(passees, on=["station_id", "jour"], how="left").dropna(subset=noms)
        predicteurs += noms

    manquants = [c for c in predicteurs if c not in j.columns]
    if manquants:
        raise SystemExit(f"prédicteurs absents : {manquants[:6]}")
    return j, predicteurs


def scores(obs: pd.Series, pred: np.ndarray, cams: pd.Series) -> dict:
    o, p, c = obs.to_numpy(), np.asarray(pred), cams.to_numpy()
    haut = o >= np.quantile(o, 0.9)
    r = float(np.sqrt(np.mean((o - p) ** 2)))
    rc = float(np.sqrt(np.mean((o - c) ** 2)))
    return {
        "n": int(len(o)), "rmse_cams": rc, "rmse": r,
        "gain_pct": 100 * (1 - r / rc) if rc > 0 else float("nan"),
        "rmse_decile_haut": float(np.sqrt(np.mean((o[haut] - p[haut]) ** 2))),
        "biais": float(np.mean(p - o)),
        "r2": float(cmp.metriques(obs, p)["r2"]),
    }


def main(polluant: str, perimetre: str, reglage: str, motif: str) -> int:
    depart = time.time()
    contrat = ce.charger_contrat()
    if reglage not in REGLAGE:
        raise SystemExit(f"réglage inconnu « {reglage} » — attendu {sorted(REGLAGE)}")
    params = REGLAGE[reglage]

    j, predicteurs = jeu(polluant, perimetre)
    print(f"\n{polluant} · {perimetre} · réglage « {reglage} » · {len(j):,} jours-station "
          f"· {len(predicteurs)} prédicteurs")
    print(f"contrat scellé {contrat['sceau'][:16]}… · "
          f"coupure {contrat['bornes_temporelles'][polluant]['coupure']}\n")

    # ── Deux ajustements seulement : la géométrie du TEST change, pas l'apprentissage ──
    modeles, entraines = {}, {}
    for geometrie, case_source in (("sans_fosse", "1_ajustement"),
                                   ("avec_fosse", "2_transfert_spatial")):
        tr, _ = ce.decouper(j, contrat, polluant, case_source)
        m = modele(params)
        m.fit(tr[predicteurs], tr["obs_jour"] - tr["cams_jour"])
        modeles[geometrie] = m
        entraines[geometrie] = tr
        print(f"  ajusté « {geometrie} » · {len(tr):,} lignes · "
              f"{tr['station_id'].nunique()} stations · {time.time() - depart:.0f}s",
              flush=True)

    lignes = []
    for case in ce.CASES:
        geometrie = ("avec_fosse" if case in ("2_transfert_spatial", "4_revendication")
                     else "sans_fosse")
        _, te = ce.decouper(j, contrat, polluant, case)
        if te.empty:
            print(f"  ⚠️ {case} · test vide — cas à comprendre, pas à ignorer")
            continue
        pred = np.clip(te["cams_jour"].to_numpy()
                       + modeles[geometrie].predict(te[predicteurs]), 0, None)
        r = scores(te["obs_jour"], pred, te["cams_jour"])
        lignes.append({"case": case, "geometrie": geometrie,
                       "n_stations": int(te["station_id"].nunique()),
                       "n_entrainement": int(len(entraines[geometrie])), **r})

    t = pd.DataFrame(lignes)
    print(f"\n{'─' * 86}")
    print(f"{'case':24s} {'n':>8s} {'st':>4s} {'CAMS':>7s} {'nous':>7s} {'gain':>8s} "
          f"{'déc.haut':>9s} {'biais':>7s}")
    print(f"{'─' * 86}")
    for _, r in t.iterrows():
        etoile = " ⭐" if r["case"] == "4_revendication" else ""
        note = "  (en échantillon)" if r["case"] == "1_ajustement" else etoile
        print(f"{r['case']:24s} {r['n']:8,d} {r['n_stations']:4d} {r['rmse_cams']:7.3f} "
              f"{r['rmse']:7.3f} {r['gain_pct']:+7.2f} % {r['rmse_decile_haut']:9.3f} "
              f"{r['biais']:+7.3f}{note}")

    if {"2_transfert_spatial", "4_revendication"} <= set(t["case"]):
        g2 = float(t.loc[t["case"] == "2_transfert_spatial", "gain_pct"].iloc[0])
        g4 = float(t.loc[t["case"] == "4_revendication", "gain_pct"].iloc[0])
        print(f"\n  Coût du passage au futur, à géométrie spatiale identique : "
              f"{g4 - g2:+.2f} points ({g2:+.2f} % → {g4:+.2f} %)")
    if {"3_tenue_temporelle", "4_revendication"} <= set(t["case"]):
        g3 = float(t.loc[t["case"] == "3_tenue_temporelle", "gain_pct"].iloc[0])
        g4 = float(t.loc[t["case"] == "4_revendication", "gain_pct"].iloc[0])
        print(f"  Coût du fossé spatial, à date identique : {g4 - g3:+.2f} points "
              f"({g3:+.2f} % → {g4:+.2f} %)")

    sortie = RACINE / f"reports/contrat_{polluant}_{perimetre}.csv"
    t.to_csv(sortie, index=False)

    resultat = {r["case"]: round(float(r["gain_pct"]), 3) for _, r in t.iterrows()}
    n = ce.journaliser(motif=motif, perimetre=perimetre, case="les_quatre",
                       polluant=polluant, modele=f"lightgbm/{reglage}", resultat=resultat)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    print(f"⚠️ CONSULTATION #{n} du test gelé — enregistrée au journal du contrat.")
    print(f"   Motif : {motif}")
    if n > 1:
        print(f"   {n} lectures = {n} degrés de liberté. Le dire en présentant le chiffre.")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--perimetre", default="PARTOUT", choices=sorted(ce.PERIMETRES))
    a.add_argument("--reglage", default="production", choices=sorted(REGLAGE))
    a.add_argument("--motif", required=True,
                   help="pourquoi on consulte le test — sera inscrit au journal")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.perimetre, n.reglage, n.motif))
