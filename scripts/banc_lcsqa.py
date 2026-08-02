#!/usr/bin/env python3
"""Banc d'évaluation conforme au référentiel LCSQA — et aux trois modes de dégradation.

Pourquoi ce script existe
--------------------------
Nos chiffres étaient calculés selon **notre** convention : une RMSE sur toutes les lignes
empilées. Le référentiel technique national du LCSQA, applicable depuis le 1er janvier
2022, procède autrement pour les scores continus :

    score_zone = moyenne arithmétique des scores par STATION

Ce n'est pas un détail de présentation. Empiler les lignes **surpondère les stations les
plus complètes** — celles qui n'ont pas de panne, souvent les mieux instrumentées et les
plus urbaines. Les deux quantités ne répondent pas à la même question, et seule la seconde
est comparable au rapport annuel qu'une AASQA transmet à la DREAL.

À l'inverse, pour les **dépassements**, le référentiel cumule bien les occurrences
station-jour dans une table unique et ne moyenne pas un CSI par station. Notre
`detection_appariee.py` était donc déjà conforme sur ce point ; c'est l'agrégation continue
qui ne l'était pas.

Les trois modes, et pourquoi les séparer
------------------------------------------
Le levier le plus fort du projet — la mémoire locale du site — n'est disponible **qu'aux
stations instrumentées**. Publier un seul chiffre laisserait croire à une capacité spatiale
que le produit n'a pas.

| mode | entrées | population d'usage |
|---|---|---|
| `FULL` | CAMS + terrain + typologie + mémoire locale | station instrumentée, flux frais |
| `NO_LOCAL_OBS` | CAMS + terrain + typologie | station neuve, ou panne du capteur |
| `RAW` | CAMS seul | rupture du pipeline — le repli |

Le mode `NO_LOCAL_OBS` est le seul qui décrive une prédiction en un lieu sans capteur.
Le mode `FULL` est le seul qui décrive le produit réellement servi aux stations.

Ce que le script calcule
-------------------------
1. **Scores continus par station**, puis moyenne — biais, RMSE, corrélation de Pearson,
   avec les repères de qualité du référentiel.
2. **La règle des 75 %** : une station n'est retenue que si ses couples valides atteignent
   75 % du **calendrier attendu** — pas 75 % des lignes restantes après suppression des
   manquants. Le dénominateur est le calendrier de la période évaluée.
3. **`MQI_f` de FAIRMODE** — rapport de la RMSE du modèle à celle de la persistance, où la
   persistance de l'échéance J+1 utilise `O[i−2]`. Objectif satisfait si `MQI_f ≤ 1` ; une
   application passe le seuil si **au moins 90 % des stations** le satisfont.
4. **Table de contingence cumulée** sur les occurrences station-jour, aux seuils du
   référentiel.

⚠️ Ce que ce banc ne peut pas faire
------------------------------------
Le référentiel évalue l'ozone en **maximum horaire journalier**, d'avril à septembre, au
seuil de 180 µg/m³. Notre cible d'ozone est le **maximum 8 h glissant**, qui sert la valeur
cible européenne de 120 µg/m³. Ce n'est pas la même grandeur : un résultat calculé sur le
max 8 h ne doit **jamais** être présenté comme conforme au référentiel pour l'ozone.
Relancer avec `--grandeur max_horaire` produit la grandeur conforme.

Usage : python3 scripts/banc_lcsqa.py --polluant PM10
Sortie : reports/banc_lcsqa_<polluant>.csv et reports/BANC_LCSQA_<polluant>.md
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

from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster,
    charger, colonnes_admises,
)

# Repères du référentiel — ce sont des objectifs graphiques, pas des preuves de
# supériorité entre deux modèles.
REFERENTIEL = {
    "O3": {"grandeur_attendue": "max_horaire", "mois": (4, 9), "seuil": 180.0,
           "biais_max": 10.0, "rmse_max": 25.0, "r_min": 0.70},
    "PM10": {"grandeur_attendue": "moyenne_jour", "mois": (1, 12), "seuil": 50.0,
             "biais_max": 7.5, "rmse_max": 15.0, "r_min": 0.60},
}
# Le référentiel ne couvre ni NO₂ ni PM2,5 en continu ou en épisode. Les évaluer est utile,
# les dire « conformes » serait faux.
HORS_REFERENTIEL = {
    "NO2": {"grandeur_attendue": "max_horaire", "mois": (1, 12), "seuil": 200.0},
    "PM25": {"grandeur_attendue": "moyenne_jour", "mois": (1, 12), "seuil": 50.0},
}
COUVERTURE_MIN = 0.75
DECALAGE_PERSISTANCE = 2  # échéance J+1 : FAIRMODE utilise O[i−2]


def scores_station(g: pd.DataFrame, colonne: str) -> dict:
    o, x = g["valeur"].to_numpy(), g[colonne].to_numpy()
    r = np.corrcoef(o, x)[0, 1] if len(g) > 2 and o.std() > 0 and x.std() > 0 else np.nan
    return {"biais": float(np.mean(x - o)),
            "rmse": float(np.sqrt(np.mean((x - o) ** 2))),
            "correlation": float(r), "n": len(g)}


def contingence(v: np.ndarray, a: np.ndarray) -> dict:
    tp, fp = int((v & a).sum()), int((~v & a).sum())
    fn, tn = int((v & ~a).sum()), int((~v & ~a).sum())
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "POD": tp / (tp + fn) if tp + fn else np.nan,
            "SR": tp / (tp + fp) if tp + fp else np.nan,
            "FAR": fp / (tp + fp) if tp + fp else np.nan,
            "biais_frequence": (tp + fp) / (tp + fn) if tp + fn else np.nan,
            "CSI": tp / (tp + fp + fn) if tp + fp + fn else np.nan}


def main(polluant: str, horizon: int, n_spa: int, grandeur: str | None,
         epreuve: str = "double") -> int:
    depart = time.time()
    regle = REFERENTIEL.get(polluant) or HORS_REFERENTIEL[polluant]
    conforme = polluant in REFERENTIEL
    grandeur = grandeur or GRANDEUR_PAR_POLLUANT[polluant]

    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, cols, grandeur)
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    from apport_observation_veille import variables_passees  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    p, noms_mem = variables_passees(d.rename(columns={"valeur": "obs_jour"}))
    p["jour"] = pd.to_datetime(p["jour"]).dt.tz_localize(None)
    avant = len(d)
    d = d.merge(p, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure mémoire : {avant:,} → {len(d):,}")

    # ── Période d'évaluation du référentiel ───────────────────────────────────────
    m1, m2 = regle["mois"]
    dans_saison = d["jour"].dt.month.between(m1, m2)
    d = d[dans_saison].reset_index(drop=True)
    print(f"{polluant} · échéances {1 if horizon == 1 else 25}-{24 * horizon} h "
      f"(**{'J0' if horizon == 1 else f'J+{horizon - 1}'}**) · épreuve {epreuve} · "
      f"grandeur **{grandeur}** · mois {m1}–{m2} · {len(d):,} "
          f"jours-station · {'CONFORME' if conforme else 'HORS'} référentiel", flush=True)
    if conforme and grandeur != regle["grandeur_attendue"]:
        print(f"  ⚠️ le référentiel attend « {regle['grandeur_attendue']} » — les scores "
              f"ci-dessous ne sont PAS conformes pour {polluant}.", flush=True)
        conforme = False

    # ── Persistance FAIRMODE, par station, sur calendrier réindexé ────────────────
    morceaux = []
    for st, g in d.groupby("station_id", sort=False):
        g = g.set_index("jour").sort_index()
        plein = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="D"))
        s = pd.DataFrame(index=plein.index)
        s["persistance"] = plein["valeur"].shift(DECALAGE_PERSISTANCE)
        s["station_id"] = st
        morceaux.append(s.reset_index(names="jour"))
    d = d.merge(pd.concat(morceaux, ignore_index=True), on=["station_id", "jour"],
                how="left")

    # ── Les trois modes, sur les mêmes plis double aveugle ────────────────────────
    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), n_spa)
    mois = np.sort(d["mois"].unique())
    modes = {"FULL": base + cols_typo + noms_mem, "NO_LOCAL_OBS": base + cols_typo}
    pred = {k: np.full(len(d), np.nan) for k in modes}
    for i, m in enumerate(mois):
        # ⚠️ Deux estimands distincts, et il faut publier les DEUX.
        #
        # `double` cache la station **et** le mois : c'est la condition de déploiement en
        # un lieu neuf. `temporelle` ne cache que le mois — c'est le protocole des
        # évaluations publiées (PREV'AIR, Bertrand et al.), où les stations de test sont
        # connues du modèle. Comparer notre chiffre en double aveugle à leur chiffre sur
        # stations connues nous impose un handicap qu'eux n'ont pas ; c'est fausser la
        # comparaison contre nous, ce qui n'est pas plus honnête que l'inverse.
        dans = (d["station_id"].isin(groupes[i % n_spa]) if epreuve == "double"
                else pd.Series(True, index=d.index))
        m_test = (d["mois"] == m) & dans
        m_train = (d["mois"] != m) & (~dans if epreuve == "double" else True)
        te, tr = d[m_test], d[m_train]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(m_test.to_numpy())
        for nom, colonnes in modes.items():
            pred[nom][idx] = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
    for nom, v in pred.items():
        d[nom] = v
    d["RAW"] = d["cams_jour"]

    # ── ① La règle des 75 %, appliquée à la MESURE et non à notre validation ─────
    #
    # ⚠️ Deux pièges superposés, tous deux rencontrés :
    #
    # 1. Le dénominateur est le calendrier **de la période évaluée**. Compter les jours
    #    entre le premier et le dernier relevé rejetterait toute station d'ozone : la
    #    saison ne fait que six mois sur douze, une station parfaite afficherait 50 %.
    #
    # 2. La règle porte sur la **complétude de la mesure**, pas sur la couverture de nos
    #    plis. Le double aveugle ne teste chaque station que dans **un tiers des mois** —
    #    trois groupes qui tournent avec le mois. L'appliquer aux prédictions hors pli
    #    rejetterait 270 stations sur 271, ce qui est arrivé. Le référentiel suppose une
    #    année opérationnelle complète ; un plan en k plis ne s'y superpose pas.
    #
    # On qualifie donc les stations **avant** de restreindre aux lignes prédites.
    calendrier = d.groupby("station_id")["jour"].agg(["min", "max"])
    attendu = calendrier.apply(
        lambda r: int(pd.date_range(r["min"], r["max"], freq="D")
                      .month.isin(range(m1, m2 + 1)).sum()), axis=1)
    obtenu = d.groupby("station_id")["jour"].nunique()
    couverture = (obtenu / attendu.replace(0, np.nan)).rename("couverture")
    retenues = couverture[couverture >= COUVERTURE_MIN].index
    print(f"  règle des 75 % (sur la MESURE) : {len(retenues)} stations retenues sur "
          f"{d['station_id'].nunique()} · couverture médiane "
          f"{couverture.median():.1%}", flush=True)

    besoin = ["valeur", "RAW", "FULL", "NO_LOCAL_OBS", "persistance"]
    d = d[d[besoin].notna().all(axis=1)].reset_index(drop=True)
    print(f"  {len(d):,} occurrences avec les trois modes et la persistance", flush=True)
    if len(retenues) == 0:
        raise SystemExit("aucune station ne satisfait la règle des 75 % — ne pas conclure")
    e = d[d["station_id"].isin(retenues)]

    lignes = []
    print(f"\n{'═' * 76}\n① SCORES CONTINUS — moyenne des scores PAR STATION "
          f"(convention LCSQA)\n{'═' * 76}")
    print(f"  {'mode':14s} {'biais':>8s} {'RMSE':>8s} {'r':>7s} {'MQI_f':>7s} "
          f"{'% stations MQI≤1':>17s}")
    for mode in ("RAW", "NO_LOCAL_OBS", "FULL"):
        par = e.groupby("station_id").apply(lambda g: pd.Series(scores_station(g, mode)),
                                            include_groups=False)
        pers = e.groupby("station_id").apply(
            lambda g: pd.Series(scores_station(g, "persistance")), include_groups=False)
        mqi = par["rmse"] / pers["rmse"].replace(0, np.nan)
        part = float((mqi <= 1).mean() * 100)
        r = {"mode": mode, "biais": par["biais"].mean(), "rmse": par["rmse"].mean(),
             "correlation": par["correlation"].mean(), "mqi_f_median": float(mqi.median()),
             "part_stations_mqi_ok_pct": part, "n_stations": len(par)}
        print(f"  {mode:14s} {r['biais']:+8.2f} {r['rmse']:8.2f} {r['correlation']:7.3f} "
              f"{r['mqi_f_median']:7.3f} {part:16.1f} %")
        lignes.append(r)

    if conforme:
        print(f"\n  Repères du référentiel — biais ∈ [−{regle['biais_max']:.1f} ; "
              f"+{regle['biais_max']:.1f}] · RMSE ≤ {regle['rmse_max']:.0f} · "
              f"r ≥ {regle['r_min']:.2f}")
        for r in lignes:
            ok = (abs(r["biais"]) <= regle["biais_max"] and r["rmse"] <= regle["rmse_max"]
                  and r["correlation"] >= regle["r_min"])
            print(f"    {r['mode']:14s} {'✓ dans les repères' if ok else '✗ hors repères'}")
        print(f"\n  FAIRMODE : une application satisfait le critère si ≥ 90 % des stations "
              f"ont MQI_f ≤ 1")
        for r in lignes:
            print(f"    {r['mode']:14s} {r['part_stations_mqi_ok_pct']:5.1f} % "
                  f"{'✓' if r['part_stations_mqi_ok_pct'] >= 90 else '✗'}")

    # ── ② Dépassements : table CUMULÉE, convention du référentiel ────────────────
    seuil = regle["seuil"]
    v = e["valeur"].to_numpy() > seuil
    print(f"\n{'═' * 76}\n② DÉPASSEMENTS > {seuil:.0f} µg/m³ — occurrences station-jour "
          f"CUMULÉES\n{'═' * 76}")
    print(f"  {int(v.sum()):,} dépassements observés sur {len(e):,} occurrences "
          f"({100 * v.mean():.2f} %)")
    if v.sum() < 10:
        print(f"  ⚠️ moins de 10 dépassements — mesuré, pas conclu.")
    print(f"\n  {'mode':14s} {'TP':>5s} {'FP':>5s} {'FN':>5s} {'POD':>7s} {'SR':>7s} "
          f"{'CSI':>7s} {'biais fq':>9s}")
    for mode in ("RAW", "NO_LOCAL_OBS", "FULL", "persistance"):
        c = contingence(v, e[mode].to_numpy() > seuil)
        print(f"  {mode:14s} {c['TP']:5d} {c['FP']:5d} {c['FN']:5d} {c['POD']:7.3f} "
              f"{c['SR']:7.3f} {c['CSI']:7.3f} {c['biais_frequence']:9.3f}")
        lignes.append({"mode": f"{mode}_dépassements", "seuil": seuil, **c})

    sortie = RACINE / f"reports/banc_lcsqa_{polluant}_{epreuve}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\n⚠️ `FULL` n'est disponible qu'aux stations instrumentées. `NO_LOCAL_OBS` est")
    print(f"   le seul mode qui décrive une prédiction en un lieu sans capteur.")
    if not conforme:
        print(f"⚠️ {polluant} : résultat NON conforme au référentiel LCSQA — "
              f"grandeur ou polluant hors périmètre.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--horizon", type=int, default=1)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--epreuve", default="double", choices=["double", "temporelle"],
                   help="'double' cache station ET mois ; 'temporelle' ne cache que le "
                        "mois — le protocole des évaluations publiées")
    a.add_argument("--grandeur", default=None,
                   help="force la grandeur journalière — ex. max_horaire pour l'ozone "
                        "conforme au référentiel")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux, n.grandeur,
                      n.epreuve))
