#!/usr/bin/env python3
"""Prépare un contour de France **léger** et projeté, pour les pages autonomes.

Pourquoi une étape séparée
----------------------------
Le fichier source pèse 3,4 Mo en WGS84 non simplifié. L'embarquer tel quel dans chaque
page produirait des documents de plusieurs mégaoctets pour un tracé affiché à 800 px de
large, où 99 % des sommets tombent sous le pixel.

Cette étape fait donc trois choses, une seule fois :

1. **filtre la métropole** — les départements d'outre-mer étireraient l'emprise sur un
   demi-globe et rendraient la France illisible ;
2. **projette en Lambert-93**, le système des coordonnées de stations déjà présentes dans
   `stations.parquet` — sans quoi points et contours ne se superposeraient pas ;
3. **simplifie par Douglas-Peucker** à une tolérance exprimée en **mètres**, donc lisible :
   1 200 m ≈ 1,5 px à l'échelle d'affichage.

Source et licence
-------------------
`france-geojson` (Grégoire David), dérivé d'**IGN Admin Express** — licence **ODbL**.
L'attribution est reportée dans le pied de chaque page produite.

Usage  : python3 scripts/contour_france.py [--tolerance 1200]
Sortie : data/processed/contour_france.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[1]
SOURCE = RACINE / "data/raw/geo/departements.geojson"
SORTIE = RACINE / "data/processed/contour_france.json"
# Emprise métropolitaine, en degrés — large, mais suffisante pour écarter l'outre-mer.
METROPOLE = (-5.5, 41.0, 10.0, 51.5)


def douglas_peucker(pts: np.ndarray, tol: float) -> np.ndarray:
    """Simplifie une ligne en gardant les sommets qui portent la forme.

    Implémentation itérative : la version récursive dépasse la pile sur les côtes
    bretonnes, qui comptent plusieurs dizaines de milliers de sommets d'un seul tenant.
    """
    n = len(pts)
    if n < 3:
        return pts
    garde = np.zeros(n, dtype=bool)
    garde[0] = garde[-1] = True
    pile = [(0, n - 1)]
    while pile:
        i, j = pile.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        seg = b - a
        long2 = float(seg @ seg)
        rel = pts[i + 1:j] - a
        if long2 == 0.0:
            dist = np.hypot(rel[:, 0], rel[:, 1])
        else:
            t = np.clip((rel @ seg) / long2, 0.0, 1.0)
            proj = t[:, None] * seg
            dist = np.hypot(*(rel - proj).T)
        k = int(np.argmax(dist))
        if dist[k] > tol:
            garde[i + 1 + k] = True
            pile.append((i, i + 1 + k))
            pile.append((i + 1 + k, j))
    return pts[garde]


def anneaux(geom: dict):
    if geom["type"] == "Polygon":
        yield from geom["coordinates"]
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            yield from poly


def main(tolerance: float, aire_min: float) -> int:
    if not SOURCE.exists():
        raise SystemExit(f"absent : {SOURCE.relative_to(RACINE)} — récupérer d'abord "
                         f"departements.geojson (france-geojson, ODbL)")
    from pyproj import Transformer

    vers93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    brut = json.loads(SOURCE.read_text(encoding="utf-8"))
    chemins, n_sommets_avant, n_sommets_apres = [], 0, 0
    gardes = 0
    for f in brut["features"]:
        for anneau in anneaux(f["geometry"]):
            a = np.asarray(anneau, dtype="float64")
            if a.ndim != 2 or len(a) < 4:
                continue
            lon, lat = a[:, 0], a[:, 1]
            if not (METROPOLE[0] <= lon.mean() <= METROPOLE[2]
                    and METROPOLE[1] <= lat.mean() <= METROPOLE[3]):
                continue
            x, y = vers93.transform(lon, lat)
            p = np.column_stack([x, y])
            n_sommets_avant += len(p)
            # Aire du polygone (formule du lacet) — écarte les îlots sous le pixel.
            aire = 0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], -1))
                             - np.dot(p[:, 1], np.roll(p[:, 0], -1)))
            if aire < aire_min:
                continue
            s = douglas_peucker(p, tolerance)
            if len(s) < 4:
                continue
            n_sommets_apres += len(s)
            gardes += 1
            chemins.append(np.round(s, 0).astype("int64").tolist())

    if not chemins:
        raise SystemExit("aucun anneau retenu — vérifier l'emprise ou la tolérance")
    tous = np.vstack([np.asarray(c) for c in chemins])
    emprise = [int(tous[:, 0].min()), int(tous[:, 1].min()),
               int(tous[:, 0].max()), int(tous[:, 1].max())]
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(json.dumps({
        "crs": "EPSG:2154", "tolerance_m": tolerance, "emprise": emprise,
        "source": "france-geojson (G. David) d'après IGN Admin Express — ODbL",
        "chemins": chemins}, separators=(",", ":")), encoding="utf-8")
    print(f"{gardes} anneaux retenus · {n_sommets_avant:,} sommets → "
          f"{n_sommets_apres:,} ({100 * n_sommets_apres / n_sommets_avant:.1f} %)")
    print(f"emprise L93 : x {emprise[0]:,} → {emprise[2]:,} · "
          f"y {emprise[1]:,} → {emprise[3]:,}")
    print(f"Écrit : {SORTIE.relative_to(RACINE)} · "
          f"{SORTIE.stat().st_size / 1024:.0f} ko")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--tolerance", type=float, default=1200.0, help="mètres")
    a.add_argument("--aire-min", type=float, default=8e6, help="m² — écarte les îlots")
    n = a.parse_args()
    raise SystemExit(main(n.tolerance, n.aire_min))
