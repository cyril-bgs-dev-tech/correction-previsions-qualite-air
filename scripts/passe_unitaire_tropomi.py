#!/usr/bin/env python3
"""Passe unitaire TROPOMI — une journée aux 476 stations, sur les deux axes.

Pourquoi cette source
---------------------
Le levier le plus fort du projet est **l'observation de la veille : +8,9 %**, plus que toute
la météo. Sa limite est énoncée dans le dossier : elle n'existe **qu'aux stations
instrumentées**, et c'est ce qui sépare le chiffre « aux stations » du chiffre « partout ».

TROPOMI observe la colonne troposphérique de NO₂ **partout**, tous les jours, à 0,035° —
soit environ 3,9 km, deux fois plus fin que la maille CAMS. C'est la même information que
l'observation de la veille, sur le domaine exact où nous en sommes privés.

Ce que cette passe doit trancher — les deux axes de la règle 1
--------------------------------------------------------------
**Axe résultat.** Une colonne n'est pas une concentration de surface, et un pixel nuageux ne
vaut rien. Trois contrôles :

* le granule qui couvre la France existe-t-il, et à quelle heure passe-t-il ?
* combien de stations reçoivent un pixel **valide** — `qa_value > 0.75`, seuil recommandé
  par l'ESA pour le NO₂ troposphérique ?
* la colonne extraite **varie-t-elle** d'une station à l'autre ? Une colonne plate serait le
  signe qu'on a lu autre chose que ce qu'on croit (règle 2 bis).

**Axe coût.** Le corpus vise ~950 jours (2024-01 → 2026-07). Le granule pèse 35,5 Mo et le
serveur accepte les requêtes par plage (HTTP 206 vérifié) : on ne lit que la fenêtre France.
Il faut donc chronométrer **la journée entière**, granules non couvrants compris, et
extrapoler — pas mesurer une lecture isolée puis multiplier.

Le piège que cette passe existe pour attraper
----------------------------------------------
Le taux de pixels valides est **le** chiffre qui décide. Sous couverture nuageuse le NO₂
troposphérique n'est pas mesurable, et l'hiver français est nuageux. Si la couverture tombe
à 30 %, TROPOMI est un prédicteur **intermittent** — utilisable, mais qui demande un modèle
tolérant au manquant et une mesure séparée sur les jours couverts. Le savoir maintenant coûte
trois minutes ; le découvrir après le lot coûte la nuit.

Usage : python3 scripts/passe_unitaire_tropomi.py [--jour 2024-07-15]
Sortie : compte rendu sur la sortie standard + reports/passe_unitaire_tropomi_{jour}.csv
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

# /vsicurl : ne jamais lister le répertoire distant, ne jamais lire le fichier entier.
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")

SEAU = "https://meeo-s5p.s3.amazonaws.com"
PRODUIT = "COGT/OFFL/L2__NO2___"
# ⚠️ **`qa_value` est stocké en entier 0-100 dans ces COG, pas en fraction 0-1.** Écrire le
# seuil recommandé par l'ESA tel qu'il est publié — « qa > 0.75 » — laisse alors passer
# **tout**, minimum compris : la couverture mesurée valait 99 % en plein janvier, chiffre
# parfaitement plausible et parfaitement faux.
#
# Et la conversion naïve `0.75 → 75` est fausse elle aussi. La valeur est **quantifiée** et
# la masse des pixels de ciel clair tombe sur **74**, pas 75 :
#
#     2024-01-08 · {33: 145, 73: 14, 74: 235, 100: 78, 255: 4}
#     2024-07-15 · {33:   4, 74: 319, 88: 2, 90: 1, 100: 149, 255: 1}
#
# Un `>= 75` appliqué à la lettre jetterait 235 pixels valides sur 476 en janvier. Le seuil
# qui sépare réellement les régimes est **50** : il rejette le 33 — « couvert par un nuage »
# au sens de l'ESA — et retient tout le reste. C'est un seuil lu **dans les données**, pas
# recopié d'une note.
QA_MIN = 50
# 255 est le remplissage du raster d'octets : absence de pixel, pas mauvaise qualité.
QA_ABSENT = 255
# Emprise France métropolitaine, marge comprise.
FRANCE = (-5.5, 41.0, 10.0, 51.5)  # ouest, sud, est, nord


def granules(jour: str) -> list[str]:
    """Les clés des colonnes troposphériques du jour, et elles seules."""
    a, m, j = jour.split("-")
    prefixe = f"{PRODUIT}/{a}/{m}/{j}/"
    url = f"{SEAU}/?list-type=2&prefix={prefixe}&max-keys=1000"
    with urllib.request.urlopen(url, timeout=60) as r:
        arbre = ET.fromstring(r.read())
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    cles = [e.text for e in arbre.findall(".//s3:Contents/s3:Key", ns)]
    if not cles:
        raise SystemExit(f"aucun objet sous {prefixe} — jour absent de l'archive")
    # Nommer ce qu'on lit (règle 2 bis) : le motif ne doit sélectionner QUE la colonne
    # troposphérique. `.aux.xml` et les autres couches sont exclus explicitement.
    suffixe = "_PRODUCT_nitrogendioxide_tropospheric_column_4326.tif"
    retenus = [k for k in cles if k.endswith(suffixe)]
    if not retenus:
        raise SystemExit(f"aucune colonne troposphérique sous {prefixe} — "
                         f"{len(cles)} objets pourtant présents")
    return sorted(retenus)


def fenetre_france(src, marge: float = 0.0):
    """Fenêtre raster couvrant la France, bornée à l'emprise du fichier."""
    from rasterio.windows import from_bounds

    o, s, e, n = FRANCE
    return from_bounds(o - marge, s - marge, e + marge, n + marge,
                       transform=src.transform).round_offsets().round_lengths()


def lire_bloc(cle: str) -> tuple[np.ndarray, object] | None:
    """Charge la fenêtre France **en entier**, puis on indexera en mémoire (règle 2)."""
    import rasterio

    with rasterio.open(f"/vsicurl/{SEAU}/{cle}") as src:
        f = fenetre_france(src)
        bloc = src.read(1, window=f)
        transform = src.window_transform(f)
    if np.all(bloc == -9999.0) or np.all(np.isnan(bloc)):
        return None
    return bloc, transform


def main(jour: str) -> int:
    import rasterio

    depart = time.time()
    cles = granules(jour)
    print(f"{jour} · {len(cles)} granules de colonne troposphérique publiés\n")

    stations = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                               columns=["station_id", "lat_wgs84", "lon_wgs84",
                                        "metropole", "active"])
    stations = stations[stations["metropole"] & stations["active"]].dropna(
        subset=["lat_wgs84", "lon_wgs84"])
    print(f"{len(stations)} stations de métropole actives\n")

    print("── AXE RÉSULTAT ──────────────────────────────────────────────────────────")
    couvrants, valeurs, qualites, heures = [], None, None, None
    for cle in cles:
        t0 = time.time()
        r = lire_bloc(cle)
        nom = cle.rsplit("/", 1)[-1]
        debut = nom.split("_")[6] if len(nom.split("_")) > 6 else "?"
        if r is None:
            print(f"  {debut} · hors fauchée France · {time.time() - t0:.1f}s")
            continue
        bloc, transform = r
        utiles = int((bloc != -9999.0).sum())
        print(f"  {debut} · COUVRE · {utiles:,} pixels renseignés · "
              f"{time.time() - t0:.1f}s")
        couvrants.append((cle, bloc, transform))

    if not couvrants:
        raise SystemExit("aucun granule ne couvre la France ce jour — "
                         "vérifier l'emprise ou la date avant de conclure")

    # Le granule le mieux renseigné sur la France est celui du passage de mi-journée.
    cle, bloc, transform = max(couvrants, key=lambda c: int((c[1] != -9999.0).sum()))
    print(f"\n  granule retenu : {cle.rsplit('/', 1)[-1][:70]}…")

    # ── qa_value et utctime, mêmes fenêtre et transformation ──────────────────────
    cle_qa = cle.replace("_PRODUCT_nitrogendioxide_tropospheric_column_4326.tif",
                         "_PRODUCT_qa_value_4326.tif")
    cle_t = cle.replace("_PRODUCT_nitrogendioxide_tropospheric_column_4326.tif",
                        "_utctime_4326.tif")
    with rasterio.open(f"/vsicurl/{SEAU}/{cle_qa}") as src:
        qa = src.read(1, window=fenetre_france(src))
    try:
        with rasterio.open(f"/vsicurl/{SEAU}/{cle_t}") as src:
            tt = src.read(1, window=fenetre_france(src))
    except Exception as e:  # noqa: BLE001 — on veut la cause, pas un silence
        print(f"  ⚠️ utctime illisible : {type(e).__name__}: {e}")
        tt = None

    if qa.shape != bloc.shape:
        raise SystemExit(f"qa_value {qa.shape} et colonne {bloc.shape} ne s'alignent pas — "
                         f"ne PAS masquer avec un tableau de forme différente")

    # ── Extraction aux stations : indexer en mémoire, pas un appel par station ────
    from rasterio.transform import rowcol

    lignes, colonnes = rowcol(transform, stations["lon_wgs84"].to_numpy(),
                              stations["lat_wgs84"].to_numpy())
    lignes, colonnes = np.asarray(lignes), np.asarray(colonnes)
    dedans = ((lignes >= 0) & (lignes < bloc.shape[0])
              & (colonnes >= 0) & (colonnes < bloc.shape[1]))
    if not dedans.all():
        print(f"  ⚠️ {int((~dedans).sum())} stations hors fenêtre — élargir FRANCE")

    s = stations[dedans].copy()
    li, co = lignes[dedans], colonnes[dedans]
    s["no2_colonne"] = bloc[li, co]
    s["qa"] = qa[li, co]
    if tt is not None:
        s["utctime"] = tt[li, co]
    s.loc[s["no2_colonne"] == -9999.0, "no2_colonne"] = np.nan
    s.loc[(s["qa"] < QA_MIN) | (s["qa"] == QA_ABSENT), "no2_colonne"] = np.nan

    n_tot = len(s)
    n_present = int((s["qa"] != QA_ABSENT).sum())
    n_val = int(s["no2_colonne"].notna().sum())
    print(f"\n  stations dans la fenêtre : {n_tot}")
    print(f"  pixel présent (qa ≠ 255) : {n_present}")
    print(f"  **qa ≥ {QA_MIN} retenu**        : {n_val} soit {n_val / n_present:.0%} "
          f"des pixels présents")
    print(f"  répartition du qa        : "
          f"{dict(sorted(s['qa'].value_counts().items()))}")

    if n_val == 0:
        raise SystemExit("aucune station avec un pixel valide — journée inexploitable, "
                         "ce n'est pas une erreur de code mais un fait à mesurer sur N jours")

    v = s["no2_colonne"].dropna()
    print(f"\n  colonne NO₂ (mol/m²) · min {v.min():.3e} · médiane {v.median():.3e} · "
          f"max {v.max():.3e}")
    # Règle 2 bis : rejeter une colonne constante — c'est le signe qu'on a lu autre chose.
    if v.nunique() < max(10, len(v) // 20):
        raise SystemExit(f"colonne quasi constante ({v.nunique()} valeurs distinctes sur "
                         f"{len(v)}) — on ne lit pas ce qu'on croit")
    print(f"  {v.nunique()} valeurs distinctes sur {len(v)} — la colonne varie ✓")
    if tt is not None and s["utctime"].notna().any():
        h = pd.to_numeric(s["utctime"], errors="coerce").dropna()
        if len(h):
            print(f"  heure de passage (brut utctime) · min {h.min():.0f} · "
                  f"max {h.max():.0f}")

    sortie = RACINE / f"reports/passe_unitaire_tropomi_{jour}.csv"
    s.to_csv(sortie, index=False)

    # ── AXE COÛT ──────────────────────────────────────────────────────────────────
    duree = time.time() - depart
    print("\n── AXE COÛT ──────────────────────────────────────────────────────────────")
    print(f"  journée complète ({len(cles)} granules sondés) : {duree:.1f} s")
    for n, libelle in ((950, "2024-01 → 2026-07, le corpus visé"),
                       (366, "2024 seule")):
        print(f"  {n} jours × {duree:.1f} s = **{n * duree / 3600:.1f} h** · {libelle}")
    print(f"\n  Une seule fauchée couvre la France : ne sonder que les granules dont "
          f"l'heure\n  de début est compatible, au lieu des {len(cles)}, diviserait ce "
          f"temps par ~{len(cles) // max(len(couvrants), 1)}.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {duree:.0f}s")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jour", default="2024-07-15")
    raise SystemExit(main(p.parse_args().jour))
