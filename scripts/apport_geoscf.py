#!/usr/bin/env python3
"""Un modèle **indépendant** apporte-t-il ce que six membres corrélés n'apportent pas ?

La question, et pourquoi elle vaut dix heures de téléchargement
----------------------------------------------------------------
Les six membres de l'ensemble CAMS partagent météo, inventaire et cadre d'assimilation :
leur moyenne ne rend que **+0,03 %**, et leurs dérivées **+0,05 à +0,40 %**. Moyenner des
estimateurs corrélés ne crée pas d'information.

GEOS-CF (NASA GMAO) est un système **entièrement distinct** — météo GEOS et non IFS, chimie
GEOS-Chem, inventaire et assimilation propres. C'est la seule source identifiée susceptible
d'apporter de l'information de grande ampleur. Ce script le mesure.

Trois mesures, dans cet ordre
-------------------------------
1. **La décorrélation des erreurs.** `corr(obs − CAMS, obs − GEOS)` : c'est *elle* qui
   décide de la combinabilité. Deux modèles qui se trompent ensemble ne se complètent pas,
   quelle que soit leur qualité individuelle.
2. **Le mélange nu.** RMSE de CAMS, de GEOS-CF, et de leur moyenne — sans apprentissage.
   Un gain ici est acquis sans rien ajuster.
3. **Le plancher d'information** `σy·√(1−r²)`, avec et sans GEOS-CF en variables, sous
   protocole double aveugle. C'est le juge : une variante qui gagne en RMSE sans baisser le
   plancher n'a rien appris, elle a bougé un paramètre libre.

⚠️ La base de comparaison contient **déjà** le terrain, le calendrier, la typologie et les
six membres CAMS. Mesurer contre plus pauvre surestimerait l'apport d'un facteur 2 à 4 —
c'est ce qui s'est produit le 04/08 sur trois autres pistes.

L'échéance
------------
GEOS-CF est extrait de la sortie de **J−1**, donc disponible douze heures avant la sortie
CAMS de J : la comparaison ne nous avantage jamais.

Usage  : python3 scripts/apport_geoscf.py --polluant O3
Sortie : reports/apport_geoscf_<polluant>_h<n>.csv
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from tableau_comparatif import NOM_POLLUANT  # noqa: E402

MEMBRES = ("chimere", "emep", "mocage", "silam", "lotos", "match")
# Le pendant GEOS-CF de chaque polluant du projet, quand il existe.
JUMEAU = {"O3": "geoscf_o3", "NO2": "geoscf_no2", "PM25": "geoscf_pm25",
          "PM10": "geoscf_pm10"}


def rmse(o, x) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def plancher(o, x) -> tuple[float, float]:
    r = float(np.corrcoef(o, x)[0, 1])
    return r, float(o.std()) * np.sqrt(max(1 - r ** 2, 0.0))


def charger_geoscf(grandeur: str) -> pd.DataFrame:
    fs = sorted(glob.glob(str(RACINE / "data/processed/meteo/geoscf_metropole_*.parquet")))
    if not fs:
        raise SystemExit("aucun fichier GEOS-CF — lancer extraire_geoscf.py")
    t = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    t["jour"] = pd.to_datetime(t["timestamp_utc"]).dt.floor("D")
    cols = [c for c in t.columns if c.startswith("geoscf_")]
    agr = "max" if grandeur in ("max_8h", "max_horaire") else "mean"
    j = t.groupby(["station_id", "jour"])[cols].agg(agr).reset_index()
    print(f"  GEOS-CF : {len(fs)} mois · {len(t):,} lignes horaires → {len(j):,} "
          f"jours-station · variables {', '.join(c[7:] for c in cols)}", flush=True)
    return j


def main(polluant: str, horizon: int, n_spa: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, cols, grandeur)
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")
    familles = list(cols_typo)

    # les six membres CAMS font partie de la BASE : c'est contre eux qu'on mesure
    fs = sorted(glob.glob(str(RACINE / f"data/processed/meteo/"
                              f"membres_metropole_{polluant.lower()}_*.parquet")))
    if fs:
        m = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
        pres = [x for x in MEMBRES if x in m.columns and m[x].notna().any()]
        m["jour"] = pd.to_datetime(m["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
        agr = "max" if grandeur in ("max_8h", "max_horaire") else "mean"
        jm = m.groupby(["station_id", "jour"])[pres].agg(agr).reset_index()
        avant = len(d)
        d = d.merge(jm, on=["station_id", "jour"], how="left")
        if len(d) != avant:
            raise SystemExit(f"jointure membres : {avant:,} → {len(d):,}")
        d["memb_etendue"] = d[pres].max(axis=1) - d[pres].min(axis=1)
        familles += pres + ["memb_etendue"]

    g = charger_geoscf(grandeur)
    g["jour"] = pd.to_datetime(g["jour"]).dt.tz_localize(None)
    avant = len(d)
    d = d.merge(g, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure GEOS-CF : {avant:,} → {len(d):,}")
    cols_geo = [c for c in d.columns if c.startswith("geoscf_")]
    jumeau = JUMEAU.get(polluant)
    couvert = d[jumeau].notna() if jumeau in d else pd.Series(False, index=d.index)
    print(f"  couverture GEOS-CF : {100 * couvert.mean():.1f} % des jours-station",
          flush=True)
    # ⚠️ Comparer sur les MÊMES lignes : sans cela, l'ajout de GEOS-CF changerait aussi
    # l'échantillon, et l'on mesurerait un effet de sélection au lieu d'un apport.
    d = d[couvert].reset_index(drop=True)
    if len(d) < 20_000:
        raise SystemExit(f"{len(d):,} lignes couvertes — trop peu")

    o = d["valeur"].to_numpy()
    cams = d["cams_jour"].to_numpy()
    geos = d[jumeau].to_numpy()
    e_cams, e_geos = o - cams, o - geos

    print(f"\n{'═' * 84}\n① DÉCORRÉLATION DES ERREURS — c'est elle qui décide\n{'═' * 84}")
    print(f"  corr(erreur CAMS, erreur GEOS-CF) = {np.corrcoef(e_cams, e_geos)[0, 1]:+.4f}")
    if len(fs) and len(pres) >= 2:
        # ⚠️ Les membres ne couvrent pas entièrement le sous-ensemble GEOS : une
        # corrélation calculée sans masque sort `nan` et le repère de comparaison
        # disparaît en silence — c'est arrivé le 04/08.
        e_m = o - d[pres[0]].to_numpy()
        e_m2 = o - d[pres[1]].to_numpy()
        m = np.isfinite(e_m) & np.isfinite(e_m2)
        if m.sum() > 1000:
            print(f"  pour comparaison, entre deux membres CAMS "
                  f"({pres[0]}/{pres[1]}) : {np.corrcoef(e_m[m], e_m2[m])[0, 1]:+.4f} "
                  f"sur {m.sum():,} lignes")
        else:
            print(f"  comparaison entre membres impossible : {m.sum()} lignes communes")
    print(f"  → plus c'est bas, plus les deux modèles se complètent.")

    print(f"\n{'═' * 84}\n② LE MÉLANGE NU — sans aucun apprentissage\n{'═' * 84}")
    print(f"  {'système':28s} {'RMSE':>8s} {'r':>8s} {'plancher':>9s}")
    for nom, x in (("CAMS brut", cams), ("GEOS-CF brut", geos),
                   ("moyenne des deux", (cams + geos) / 2)):
        r, pl = plancher(o, x)
        print(f"  {nom:28s} {rmse(o, x):8.3f} {r:8.4f} {pl:9.3f}")

    print(f"\n{'═' * 84}\n③ APPORT EN VARIABLES — protocole double aveugle\n{'═' * 84}",
          flush=True)
    modes = {"① base (terrain, calendrier, typologie, 6 membres)": base + familles,
             "② + GEOS-CF": base + familles + cols_geo}
    rng = np.random.default_rng(GRAINE)
    idsd = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(idsd), n_spa)
    mois = np.sort(d["mois"].unique())
    pred = {k: np.full(len(d), np.nan) for k in modes}
    for i, mm in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        mt, mr = (d["mois"] == mm) & dans, (d["mois"] != mm) & ~dans
        te, tr = d[mt], d[mr]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(mt.to_numpy())
        for nom, colonnes in modes.items():
            pred[nom][idx] = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")

    ok = np.ones(len(d), bool)
    for nom, v in pred.items():
        if not np.isfinite(v).any():
            raise SystemExit(f"le mode « {nom} » n'a rien produit")
        ok &= np.isfinite(v)
    oo = o[ok]
    print(f"  {ok.sum():,} prédictions · station ET mois cachés\n")
    print(f"  {'configuration':50s} {'r':>8s} {'RMSE':>8s} {'plancher':>9s} {'Δ':>8s}")
    lignes, ref = [], None
    for nom in modes:
        r, pl = plancher(oo, pred[nom][ok])
        if ref is None:
            ref = pl
        print(f"  {nom:50s} {r:8.4f} {rmse(oo, pred[nom][ok]):8.3f} {pl:9.4f} "
              f"{100 * (1 - pl / ref):+7.2f}%")
        lignes.append({"polluant": polluant, "horizon": horizon, "configuration": nom,
                       "r": r, "rmse": rmse(oo, pred[nom][ok]), "plancher": pl,
                       "delta_plancher_pct": 100 * (1 - pl / ref), "n": int(ok.sum()),
                       "corr_erreurs": float(np.corrcoef(e_cams, e_geos)[0, 1])})

    t = pd.DataFrame(lignes)
    gain = float(t["delta_plancher_pct"].max())
    if gain < 0.5:
        print(f"\n  → Apport {gain:+.2f} % : NUL. Un modèle indépendant n'apporte pas non")
        print(f"    plus — l'information manquante n'est pas dans un second modèle.")
    else:
        print(f"\n  → Apport {gain:+.2f} % du plancher. À confirmer sur un second polluant.")
    f = RACINE / f"reports/apport_geoscf_{polluant}_h{horizon}.csv"
    t.to_csv(f, index=False)
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
