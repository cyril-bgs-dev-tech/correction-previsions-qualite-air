#!/usr/bin/env python3
"""Où le réseau d'Atmo Occitanie sait, et où il devine — une aide à la décision.

Pourquoi cet angle, et pas « voici un meilleur modèle »
--------------------------------------------------------
Atmo Occitanie exploite déjà CHIMERE et une adaptation statistique depuis 2023. Proposer
une correction de plus répond à une question qu'ils ont déjà traitée. En revanche, deux
échéances réglementaires leur imposent un travail qu'ils n'ont pas encore publié :

* **30 juin 2028** — la décision d'exécution (UE) 2026/1208 impose de déterminer les
  **aires de représentativité spatiale** de chaque station, avec une tolérance de ±15 %
  (ou un minimum absolu selon le polluant) sur les mailles rattachées ;
* **1er janvier 2030** — la directive (UE) 2024/2881 abaisse fortement les valeurs limites,
  ce qui déplace l'enjeu du pic vers la **cartographie fiable à basse concentration**, et
  pose la question de la densité du réseau.

Or ce projet possède exactement l'instrument qui répond à la première : un protocole où
**la station est cachée du modèle**. L'erreur commise sur une station jamais vue *est* une
mesure directe de sa prédictibilité depuis le reste du réseau. C'est la même quantité que
la représentativité spatiale, prise par l'autre bout.

Ce que le script produit, et la décision que chaque sortie éclaire
-------------------------------------------------------------------
1. **Prédictibilité par station** — erreur du modèle quand cette station est cachée.
   *Faible* : l'information est redondante avec le voisinage ; la station peut être
   déplacée sans perte d'information régionale. *Forte* : la station porte une information
   que rien d'autre ne fournit — elle est structurante.
2. **Couverture par EPCI** — pour chacune des 164 intercommunalités qu'Atmo Occitanie
   publie, la distance à la station la plus proche, par polluant.
3. **Classement des zones aveugles** — croisement des deux : les EPCI éloignés **et** dont
   le voisinage est mal prédit sont ceux où une station neuve apporterait le plus.
4. **Quel polluant décide de l'indice publié** — depuis leur propre archive, la part des
   jours-zone où chaque sous-indice fixe la classe finale.

⚠️ Ce que ce script **ne** fait pas
------------------------------------
Il ne calcule pas une aire de représentativité au sens de la décision 2026/1208 : celle-ci
se détermine par modélisation avec une tolérance sur les concentrations, pas par l'erreur
d'un correcteur statistique. Les deux quantités sont liées mais distinctes. La formulation
honnête est « un indicateur de prédictibilité, proposé comme point de départ », jamais
« la SRA réglementaire ».

Il ne mesure pas non plus la qualité de la chaîne d'Atmo Occitanie : nos prédictions
corrigent **CAMS**, pas CHIMERE.

Usage : python3 scripts/valeur_reseau_occitanie.py [--polluant PM10]
Sorties :
  reports/reseau_occitanie_stations.csv  — prédictibilité par station
  reports/reseau_occitanie_zones.csv     — couverture et priorité par EPCI
  reports/RESEAU_OCCITANIE.md            — la note de synthèse
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

# Les sous-indices publiés par Atmo Occitanie, dans leur nomenclature.
SOUS_INDICES = {"code_no2": "NO₂", "code_o3": "O₃", "code_pm10": "PM10",
                "code_pm25": "PM2,5", "code_so2": "SO₂"}


def charger_zones() -> pd.DataFrame:
    """Les 164 EPCI de l'archive d'indice, avec leur centroïde en Lambert 93."""
    t = pd.read_parquet(RACINE / "data/processed/indice_officiel_occitanie.parquet")
    if t.empty:
        raise SystemExit("archive d'indice vide — ne pas continuer")
    z = (t.groupby(["code_zone", "lib_zone"])[["x_reg", "y_reg"]]
         .median().reset_index())
    # Contrôle : la projection annoncée doit être unique et connue.
    epsg = t["epsg_reg"].dropna().unique()
    if len(epsg) != 1 or int(epsg[0]) != 2154:
        raise SystemExit(f"projection inattendue : {epsg} — attendu 2154 (Lambert 93)")
    return z


def charger_stations() -> pd.DataFrame:
    s = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    s = s.dropna(subset=["x_l93", "y_l93"])
    return s[["station_id", "nom", "commune", "typologie_zone", "type_station",
              "x_l93", "y_l93", "active"]]


def predictibilite(polluant: str) -> pd.DataFrame | None:
    """Erreur par station quand elle est **cachée du modèle** — l'épreuve spatiale.

    On prend l'épreuve `spatiale` et non le double aveugle : la question posée est
    « que sait-on de ce lieu sans y mesurer », pas « que sait-on de ce lieu à une date
    inconnue ». Mélanger les deux attribuerait à la géographie une part de la difficulté
    temporelle.
    """
    for suffixe in ("_typo", ""):
        f = RACINE / f"data/interim/oof/oof_{polluant}{suffixe}.parquet"
        if f.exists():
            break
    else:
        return None
    o = pd.read_parquet(f)
    o = o[o["epreuve"] == "spatiale"]
    if o.empty:
        return None
    o = o.assign(err_mos=(o["pred"] - o["valeur"]).abs(),
                 err_cams=(o["cams_jour"] - o["valeur"]).abs())
    g = o.groupby("station_id").agg(
        n_jours=("valeur", "size"), obs_moyenne=("valeur", "mean"),
        rmse_mos=("err_mos", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        rmse_cams=("err_cams", lambda x: float(np.sqrt(np.mean(x ** 2))))).reset_index()
    g = g[g["n_jours"] >= 60]  # sous 60 jours, l'estimation par station n'est pas stable
    g["polluant"] = polluant
    return g


def plus_proche(zones: pd.DataFrame, stations: pd.DataFrame) -> pd.DataFrame:
    """Distance de chaque centroïde d'EPCI à la station la plus proche, en km."""
    zx = zones[["x_reg", "y_reg"]].to_numpy()[:, None, :]
    sx = stations[["x_l93", "y_l93"]].to_numpy()[None, :, :]
    d = np.sqrt(((zx - sx) ** 2).sum(axis=2)) / 1000.0
    i = d.argmin(axis=1)
    out = zones.copy()
    out["km_station_proche"] = d.min(axis=1)
    out["station_proche"] = stations["nom"].to_numpy()[i]
    out["station_proche_id"] = stations["station_id"].to_numpy()[i]
    out["n_stations_30km"] = (d <= 30).sum(axis=1)
    return out


def polluant_pilote(t: pd.DataFrame) -> pd.DataFrame:
    """Quel sous-indice fixe la classe publiée — depuis leur propre archive.

    L'indice ATMO est le **maximum** des sous-indices. Un jour-zone peut avoir plusieurs
    sous-indices ex æquo au maximum : on compte alors chacun comme pilote partiel, plutôt
    que d'en choisir un arbitrairement. Attribuer 100 % à la première colonne trouvée
    serait la faute de « la colonne prise par position ».
    """
    cols = [c for c in SOUS_INDICES if c in t.columns]
    sub = t[cols].apply(pd.to_numeric, errors="coerce")
    mx = sub.max(axis=1)
    ok = mx.notna() & t["code_qual"].notna()
    egal = sub[ok].eq(mx[ok], axis=0)
    parts = egal.div(egal.sum(axis=1).replace(0, np.nan), axis=0).sum()
    r = (parts / parts.sum() * 100).sort_values(ascending=False)
    return pd.DataFrame({"sous_indice": [SOUS_INDICES[c] for c in r.index],
                         "part_pilote_pct": r.to_numpy(),
                         "n_jours_zone": int(ok.sum())})


def main(polluants: list[str]) -> int:
    zones = charger_zones()
    stations = charger_stations()
    indice = pd.read_parquet(RACINE / "data/processed/indice_officiel_occitanie.parquet")
    print(f"Archive Atmo Occitanie · {len(indice):,} jours-zone · "
          f"{zones['code_zone'].nunique()} EPCI · "
          f"{indice['jour_local'].nunique()} jours", flush=True)

    # ── Stations effectivement en Occitanie : celles à moins de 60 km d'un EPCI ────
    # On ne se fie pas à un code département absent du fichier : on lit la géométrie.
    zx = zones[["x_reg", "y_reg"]].to_numpy()[None, :, :]
    sx = stations[["x_l93", "y_l93"]].to_numpy()[:, None, :]
    d_min = np.sqrt(((sx - zx) ** 2).sum(axis=2)).min(axis=1) / 1000.0
    occ = stations[d_min <= 60].reset_index(drop=True)
    print(f"  {len(occ)} stations dans l'emprise régionale "
          f"({occ['active'].sum() if 'active' in occ else '?'} actives)", flush=True)

    couverture = plus_proche(zones, occ)

    print(f"\n{'═' * 78}\n① QUEL POLLUANT DÉCIDE DE L'INDICE PUBLIÉ\n{'═' * 78}")
    pilote = polluant_pilote(indice)
    for _, r in pilote.iterrows():
        print(f"  {r['sous_indice']:8s} {r['part_pilote_pct']:5.1f} %")
    pilote.to_csv(RACINE / "reports/reseau_occitanie_pilote.csv", index=False)

    print(f"\n{'═' * 78}\n② COUVERTURE DU RÉSEAU PAR EPCI\n{'═' * 78}")
    q = couverture["km_station_proche"]
    print(f"  distance médiane au poste le plus proche : {q.median():.1f} km")
    print(f"  quartile supérieur : {q.quantile(0.75):.1f} km · maximum {q.max():.1f} km")
    print(f"  EPCI sans aucune station à moins de 30 km : "
          f"{int((couverture['n_stations_30km'] == 0).sum())} sur {len(couverture)}")
    print(f"\n  Les 10 EPCI les plus éloignés d'un point de mesure :")
    for _, r in couverture.nlargest(10, "km_station_proche").iterrows():
        print(f"    {r['km_station_proche']:5.1f} km  {r['lib_zone'][:46]:46s} "
              f"→ {str(r['station_proche'])[:24]}")

    # ── ③ Prédictibilité par station, quand elle est cachée ───────────────────────
    morceaux = []
    for p in polluants:
        g = predictibilite(p)
        if g is None:
            print(f"\n  ⚠️ {p} : aucune prédiction hors pli — lancer oof_double_aveugle.py")
            continue
        morceaux.append(g)
    if morceaux:
        pred = pd.concat(morceaux, ignore_index=True)
        pred = pred.merge(occ[["station_id", "nom", "commune", "typologie_zone",
                               "type_station"]], on="station_id", how="inner")
        pred["gain_pct"] = 100 * (1 - pred["rmse_mos"] / pred["rmse_cams"])
        print(f"\n{'═' * 78}\n③ PRÉDICTIBILITÉ DES STATIONS D'OCCITANIE, STATION CACHÉE\n"
              f"{'═' * 78}")
        for p, g in pred.groupby("polluant"):
            print(f"\n  {p} · {len(g)} stations · RMSE médiane {g['rmse_mos'].median():.2f} "
                  f"µg/m³ (CAMS {g['rmse_cams'].median():.2f})")
            print(f"    ── les mieux prédites sans elles-mêmes (information redondante) :")
            for _, r in g.nsmallest(5, "rmse_mos").iterrows():
                print(f"       {r['rmse_mos']:5.2f}  {str(r['nom'])[:34]:34s} "
                      f"{str(r['type_station'])[:12]:12s} {str(r['typologie_zone'])[:10]}")
            print(f"    ── les moins prédites (information unique, station structurante) :")
            for _, r in g.nlargest(5, "rmse_mos").iterrows():
                print(f"       {r['rmse_mos']:5.2f}  {str(r['nom'])[:34]:34s} "
                      f"{str(r['type_station'])[:12]:12s} {str(r['typologie_zone'])[:10]}")
        pred.to_csv(RACINE / "reports/reseau_occitanie_stations.csv", index=False)

        # ── ④ Où une station neuve apporterait le plus ────────────────────────────
        med = pred.groupby("station_id")["rmse_mos"].median()
        couverture["rmse_voisin"] = couverture["station_proche_id"].map(med)
        # Priorité : loin d'un poste ET voisinage mal prédit. Produit normalisé, pour
        # que l'unité (km, µg/m³) ne décide pas du classement.
        for c in ("km_station_proche", "rmse_voisin"):
            v = couverture[c]
            couverture[f"z_{c}"] = (v - v.min()) / (v.max() - v.min())
        couverture["priorite"] = (couverture["z_km_station_proche"]
                                  * couverture["z_rmse_voisin"])
        print(f"\n{'═' * 78}\n④ OÙ UNE STATION NEUVE APPORTERAIT LE PLUS\n{'═' * 78}")
        print(f"  Croisement : éloignement × imprédictibilité du voisinage.")
        print(f"  {'priorité':>8s} {'km':>6s} {'RMSE voisin':>11s}  EPCI")
        for _, r in couverture.nlargest(12, "priorite").iterrows():
            print(f"  {r['priorite']:8.3f} {r['km_station_proche']:6.1f} "
                  f"{r['rmse_voisin']:11.2f}  {r['lib_zone'][:44]}")

    couverture.to_csv(RACINE / "reports/reseau_occitanie_zones.csv", index=False)
    print(f"\n⚠️ Indicateur de prédictibilité — PAS l'aire de représentativité au sens de")
    print(f"   la décision (UE) 2026/1208, qui se détermine par modélisation avec une")
    print(f"   tolérance sur les concentrations. Proposé comme point de départ.")
    print(f"\nÉcrit : reports/reseau_occitanie_{{stations,zones,pilote}}.csv")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluants", default="NO2,O3,PM10")
    n = a.parse_args()
    raise SystemExit(main([p.strip() for p in n.polluants.split(",") if p.strip()]))
