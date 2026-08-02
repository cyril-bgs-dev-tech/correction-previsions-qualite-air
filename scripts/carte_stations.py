#!/usr/bin/env python3
"""L'amélioration station par station, et sa carte — le livrable qu'une AASQA lit d'abord.

Pourquoi cette vue
------------------
Le dossier publie des moyennes : +23,4 % sur l'ozone, +34,7 % sur le NO₂. Une moyenne ne dit
pas *où* la correction travaille, ni surtout **où elle ne travaille pas**. Or c'est la
première question d'un service régional : *chez moi, ça change quoi ?*

La carte répond en un coup d'œil, et elle rend le résultat **réfutable** : une station où la
correction dégrade se voit, alors qu'elle disparaît dans une moyenne.

Ce que le script produit
------------------------
Pour chaque station et chaque polluant, au grain réglementaire, en **validation par stations
entièrement exclues** — la station évaluée n'a jamais servi à ajuster le modèle qui la
prédit :

* RMSE de CAMS brut, RMSE de la correction, gain en pourcentage ;
* biais des deux, corrélation, effectif ;
* coordonnées Lambert-93 pour la carte, typologie et zone.

Sortie : ``reports/carte_stations.csv`` et ``reports/carte_stations_contours.json``
(contours France simplifiés, projetés en Lambert-93, intégrés dans la page — la politique de
sécurité des pages publiées interdit toute requête externe à l'affichage).

Usage : python3 scripts/carte_stations.py
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

from aq.ingest.controle import ControleEchec, exiger_colonnes, exiger_lignes  # noqa: E402

GRAINE = 20260731
CONTOURS = ("https://raw.githubusercontent.com/gregoiredavid/france-geojson/"
            "master/metropole.geojson")
# En dessous de cet effectif, une RMSE de station n'a pas de sens : on l'écarte en le disant.
MIN_JOURS = 60


def modele():
    return modele_mos(graine=GRAINE)


def wgs84_vers_l93(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Projette en Lambert-93 — la projection légale française, celle des stations."""
    import pyproj

    t = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    return t.transform(lon, lat)


def contours_l93() -> list[list[list[float]]]:
    """Contours de la France métropolitaine, simplifiés et projetés en Lambert-93.

    Téléchargés au moment de la construction et **intégrés** au fichier de sortie : la
    politique de sécurité des pages publiées interdit toute requête externe à l'affichage,
    donc un contour chargé depuis un CDN ne s'afficherait jamais.
    """
    with urllib.request.urlopen(CONTOURS, timeout=60) as r:
        g = json.loads(r.read())
    # La source peut être une collection, une entité seule ou une géométrie nue — vérifié
    # plutôt que supposé : `metropole.geojson` est un **Feature** unique portant un
    # MultiPolygon de 167 anneaux, et supposer une FeatureCollection lève un KeyError.
    if g.get("type") == "FeatureCollection":
        geometries = [e["geometry"] for e in g["features"]]
    elif g.get("type") == "Feature":
        geometries = [g["geometry"]]
    else:
        geometries = [g]
    anneaux: list[list[list[float]]] = []
    for geo in geometries:
        polys = ([geo["coordinates"]] if geo["type"] == "Polygon"
                 else geo["coordinates"])
        for poly in polys:
            ext = np.asarray(poly[0], dtype="float64")
            if len(ext) < 40:  # îlots minuscules : ils encombrent sans rien apporter
                continue
            x, y = wgs84_vers_l93(ext[:, 0], ext[:, 1])
            # Simplification par pas fixe : le contour n'est pas une donnée, seulement un
            # repère. Un fichier de 600 Ko rendrait la page inutilisable sur mobile.
            pas = max(1, len(x) // 400)
            anneaux.append([[round(float(a) / 1000, 1), round(float(b) / 1000, 1)]
                            for a, b in zip(x[::pas], y[::pas])])
    if not anneaux:
        raise ControleEchec("aucun contour exploitable — la source a changé de structure")
    return anneaux


def par_station(polluant: str, n_plis: int = 3) -> pd.DataFrame:
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    d = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    d = d.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    stations = np.sort(d["station_id"].unique())
    groupe = d["station_id"].map({s: i % n_plis for i, s in enumerate(stations)}).to_numpy()
    d["nous"] = np.nan
    for p in sorted(set(groupe)):
        test = groupe == p
        m = modele()
        m.fit(d.loc[~test, predicteurs], d.loc[~test, "valeur"] - d.loc[~test, "cams_jour"])
        d.loc[test, "nous"] = np.clip(
            d.loc[test, "cams_jour"].to_numpy() + m.predict(d.loc[test, predicteurs]),
            0, None)

    lignes = []
    for s, g in d.groupby("station_id"):
        if len(g) < MIN_JOURS:
            continue
        o = g["valeur"].to_numpy()
        rc = float(np.sqrt(np.mean((g["cams_jour"] - o) ** 2)))
        rn = float(np.sqrt(np.mean((g["nous"] - o) ** 2)))
        lignes.append({
            "polluant": polluant, "station_id": s, "n_jours": len(g),
            "rmse_cams": rc, "rmse_nous": rn,
            "gain_pct": 100 * (1 - rn / rc) if rc > 0 else np.nan,
            "biais_cams": float(np.mean(g["cams_jour"] - o)),
            "biais_nous": float(np.mean(g["nous"] - o)),
            "obs_median": float(np.median(o))})
    t = pd.DataFrame(lignes)
    exiger_lignes(t, 100, f"stations {polluant}")
    return t


def main() -> int:
    depart = time.time()
    meta = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    exiger_colonnes(meta, ["station_id", "x_l93", "y_l93", "type_station",
                           "typologie_zone", "nom"], "stations")
    meta = meta.drop_duplicates("station_id")[
        ["station_id", "x_l93", "y_l93", "type_station", "typologie_zone", "nom"]]

    morceaux = []
    for polluant in ("O3", "NO2", "PM25", "PM10"):
        t = par_station(polluant)
        avant = len(t)
        t = t.merge(meta, on="station_id", how="inner")
        if len(t) != avant:
            raise ControleEchec(
                f"{polluant} : {avant - len(t)} stations sans métadonnées — une station "
                "sans coordonnées disparaîtrait de la carte sans que rien ne le signale")
        morceaux.append(t)
        print(f"  {polluant:5} {len(t):4d} stations · gain médian "
              f"{t['gain_pct'].median():+5.1f} % · dégradées "
              f"{(t['gain_pct'] < 0).sum():3d} · {time.time() - depart:4.0f}s", flush=True)

    t = pd.concat(morceaux, ignore_index=True)
    t["x_km"] = (t["x_l93"] / 1000).round(1)
    t["y_km"] = (t["y_l93"] / 1000).round(1)
    sortie = RACINE / "reports/carte_stations.csv"
    t.to_csv(sortie, index=False)

    contours = contours_l93()
    chemin = RACINE / "reports/carte_stations_contours.json"
    chemin.write_text(json.dumps(contours, separators=(",", ":")), encoding="utf-8")
    print(f"\n{len(t)} lignes · {t['station_id'].nunique()} stations distinctes")
    print(f"contours : {len(contours)} anneaux · "
          f"{chemin.stat().st_size / 1024:.0f} Ko")
    print(f"Écrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
