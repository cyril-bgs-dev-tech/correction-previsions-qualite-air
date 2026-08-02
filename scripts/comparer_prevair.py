#!/usr/bin/env python3
"""Extraire PREV'AIR aux stations et le comparer — le démonstrateur, pas la conclusion.

Ce que ce script est, et ce qu'il n'est pas
--------------------------------------------
Il **n'établit rien**. Neuf dates ne concluent sur rien, et le script le dit à chaque
sortie. Ce qu'il fait, c'est **poser la chaîne de comparaison** au produit opérationnel
français, et la faire tourner sur ce qui est publiquement disponible.

C'est la différence entre « nous ne pouvons pas nous comparer » et :

> « Voici la chaîne, elle tourne, voici le résultat sur les jours accessibles.
>   Donnez-nous l'archive et nous la faisons sur trois ans. »

Pourquoi seulement neuf dates
-------------------------------
PREV'AIR publie ses prévisions en NetCDF sur data.gouv.fr, mais **la fenêtre n'est que
d'environ six jours**. L'archive complète existe à l'INERIS depuis 2003 ; elle n'est pas
téléchargeable en masse et se demande à `prevair@ineris.fr`.
`scripts/archiver_prevair.py` archive quotidiennement — chaque jour non archivé est perdu.

Ce que le produit contient, mesuré et non supposé
--------------------------------------------------
* variable **`PM10_kriging`** — la sortie **déjà corrigée par krigeage**, adaptation
  statistique comprise. Ce n'est **pas** du CHIMERE brut ;
* grille **755 × 534** sur la France, soit **≈ 1,7 km** — six fois plus fine que les 0,1°
  de CAMS ;
* échéances `MAXJ0` à `MAXJ3`, quatre polluants, **maximum journalier**.

⚠️ La comparaison n'est donc pas « deux méthodes » mais **deux chaînes d'ampleur
différente** : un ensemble européen à 10 km sans assimilation, contre un produit national
assimilé, krigé et déjà adapté. Toute lecture qui l'oublie est fausse.

Usage : python3 scripts/comparer_prevair.py --polluant PM10 --echeance MAXJ1
Sortie : reports/comparaison_prevair_<polluant>_<echeance>.csv
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
ARCHIVE = RACINE / "data/raw/prevair"
# Nom de la variable dans le NetCDF, par polluant — lu, jamais deviné.
# ⚠️ Le nom de fichier dit « MAXJ » pour tous les polluants, mais la grandeur réellement
# publiée n'est PAS la même. Vérifié le 03/08 en comparant les trois agrégats possibles de
# l'observation horaire :
#
#     agrégat observé        biais    RMSE    corr
#     maximum horaire        -7,55   35,95   0,117
#     moyenne journalière    +7,19   17,57   0,192   ← deux fois meilleur
#
# Sur les particules, « MAXJ » désigne donc la **moyenne journalière** — le grain du seuil
# de 50 µg/m³. Croire le nom de fichier aurait doublé la RMSE (règle 4 bis).
AGREGAT = {"PM10": "mean", "PM25": "mean", "O3": "max", "NO2": "max"}


def extraire(fichier: Path, stations: pd.DataFrame) -> pd.DataFrame | None:
    """Valeur au plus proche voisin de chaque station, dans la grille régulière."""
    import xarray as xr

    d = xr.open_dataset(fichier)
    noms = list(d.data_vars)
    if not noms:
        raise SystemExit(f"{fichier.name} : aucune variable — fichier corrompu ?")
    if len(noms) > 1:
        # ⚠️ Deux variables = ambiguïté. On lève plutôt que de prendre la première : c'est
        # exactement la faute « colonne prise par position » que la règle 2 bis interdit.
        raise SystemExit(f"{fichier.name} : {len(noms)} variables {noms} — nommer laquelle")
    v = noms[0]
    lat, lon = d["lat"].values, d["lon"].values
    a = np.squeeze(d[v].values)
    if a.ndim != 2:
        raise SystemExit(f"{fichier.name} : forme {a.shape} inattendue")
    i = np.abs(lat[:, None] - stations["lat_wgs84"].to_numpy()[None, :]).argmin(0)
    j = np.abs(lon[:, None] - stations["lon_wgs84"].to_numpy()[None, :]).argmin(0)
    # Hors emprise : la station la plus proche du bord serait prise à tort.
    dans = ((stations["lat_wgs84"].to_numpy() >= lat.min())
            & (stations["lat_wgs84"].to_numpy() <= lat.max())
            & (stations["lon_wgs84"].to_numpy() >= lon.min())
            & (stations["lon_wgs84"].to_numpy() <= lon.max()))
    # `np.squeeze` sur un axe de taille 1 rend un tableau 0-d, pas un scalaire.
    jour = pd.Timestamp(np.asarray(d["time"].values).ravel()[0]).normalize()
    out = pd.DataFrame({"station_id": stations["station_id"].to_numpy(),
                        "jour": jour, "prevair": a[i, j], "variable": v})
    out.loc[~dans, "prevair"] = np.nan
    return out.dropna(subset=["prevair"])


def main(polluant: str, echeance: str) -> int:
    # ⚠️ Les noms sont en MAJUSCULES : `PREVAIR.prevision.20260802.MAXJ1.PM10.public.nc`.
    # Un motif en minuscules ne trouvait rien et sortait sur « lancer archiver_prevair.py »,
    # message trompeur puisque l'archive existait. On compare sans tenir compte de la casse.
    cle = f".{echeance}.{polluant}.".upper()
    fichiers = sorted(f for f in ARCHIVE.glob("*.nc")
                      if cle in f.name.upper() and "PREVISION" in f.name.upper())
    if not fichiers:
        raise SystemExit(f"aucun fichier {cle} dans {ARCHIVE} — lancer archiver_prevair.py")
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "nom", "lat_wgs84", "lon_wgs84",
                                  "type_station"]).dropna(subset=["lat_wgs84"])
    st = st.drop_duplicates("station_id").reset_index(drop=True)

    dates = sorted({m for f in fichiers for m in re.findall(r"\.(\d{8})\.", f.name)})
    print(f"{polluant} · échéance {echeance} · {len(fichiers)} fichiers · "
          f"{len(dates)} dates : {dates[0]} → {dates[-1]}", flush=True)
    print(f"  ⚠️ {len(dates)} dates ne concluent RIEN. Ce script pose la chaîne, "
          f"il ne mesure pas une performance.", flush=True)

    morceaux = [extraire(f, st) for f in fichiers]
    p = pd.concat([m for m in morceaux if m is not None], ignore_index=True)
    print(f"  {len(p):,} valeurs extraites · {p['station_id'].nunique()} stations · "
          f"variable **{p['variable'].iloc[0]}**", flush=True)

    # ── Observations correspondantes, depuis le flux LCSQA ────────────────────
    obs = []
    for f in sorted((RACINE / "data/interim/lcsqa").glob("lcsqa_*.parquet")):
        mois = re.findall(r"(\d{6})", f.name)
        if not any(d[:6] in mois for d in dates):
            continue
        t = pd.read_parquet(f, columns=["station_id", "polluant", "timestamp_utc",
                                        "valeur"])
        obs.append(t[t["polluant"] == polluant])
    if not obs:
        raise SystemExit(f"aucune observation LCSQA sur {dates[0][:6]}–{dates[-1][:6]}")
    o = pd.concat(obs, ignore_index=True)
    o["jour"] = pd.to_datetime(o["timestamp_utc"]).dt.tz_localize(None).dt.normalize()
    agr = AGREGAT[polluant]
    oj = o.groupby(["station_id", "jour"])["valeur"].agg(agr).reset_index()
    print(f"  agrégat de l'observation : **{agr}** (vérifié, pas déduit du nom de fichier)",
          flush=True)

    d = p.merge(oj, on=["station_id", "jour"], how="inner")
    print(f"\n  {len(d):,} couples appariés · {d['jour'].nunique()} jours · "
          f"{d['station_id'].nunique()} stations", flush=True)
    if len(d) < 200:
        print(f"  ⚠️ {len(d)} couples — trop peu même pour un démonstrateur.")
        return 1

    err = d["prevair"] - d["valeur"]
    print(f"\n{'═' * 70}\nPREV'AIR aux stations — DÉMONSTRATEUR, {len(d):,} couples\n"
          f"{'═' * 70}")
    print(f"  biais       {err.mean():+7.2f} µg/m³")
    print(f"  RMSE        {np.sqrt((err ** 2).mean()):7.2f} µg/m³")
    print(f"  corrélation {np.corrcoef(d['prevair'], d['valeur'])[0, 1]:7.3f}")
    print(f"\n  Rappel : ce produit est **déjà corrigé** (krigeage + adaptation")
    print(f"  statistique) et tourne à ~1,7 km. Ce n'est pas une référence brute.")

    sortie = RACINE / f"reports/comparaison_prevair_{polluant}_{echeance}.csv"
    d.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    print(f"\n→ Pour conclure il faut l'archive historique : prevair@ineris.fr")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--echeance", default="MAXJ1", choices=["MAXJ0", "MAXJ1", "MAXJ2",
                                                          "MAXJ3"])
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.echeance))
