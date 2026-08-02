"""Spatialisation : des stations vers un champ, puis vers l'indice par EPCI.

C'est l'étape qui manque pour reproduire l'indice officiel. La mesure de l'écart
(`reports/INDICE_ATMO.md`) l'a chiffrée : un indice ponctuel accuse **−0,72 classe**
de biais systématique contre l'officiel, parce que celui-ci est un **maximum sur une
surface** et non une valeur en un point.

La chaîne comporte quatre étapes, et chacune peut être remplacée indépendamment :

    stations → champ interpolé → maximum par EPCI → classe d'indice

L'interpolation par distance inverse (IDW) sert de **référence**, pas d'objectif : elle
ne connaît que la distance et ignore le paysage. Le gain attendu du projet vient de son
remplacement par un champ prédit à partir des variables géospatiales — c'est
précisément là que la LUR devient utile.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from shapely.geometry import shape
from shapely.prepared import prep

RESOLUTION_M = 1_000.0


def grille_reguliere(
    x_min: float, y_min: float, x_max: float, y_max: float,
    resolution_m: float = RESOLUTION_M,
) -> pd.DataFrame:
    """Grille régulière en Lambert-93, alignée sur des multiples de la résolution.

    L'alignement garantit qu'une même maille porte les mêmes coordonnées d'un calcul
    à l'autre — sans quoi deux exécutions ne seraient pas superposables.
    """
    debut_x = np.floor(x_min / resolution_m) * resolution_m
    debut_y = np.floor(y_min / resolution_m) * resolution_m
    xs = np.arange(debut_x, x_max + resolution_m, resolution_m)
    ys = np.arange(debut_y, y_max + resolution_m, resolution_m)
    gx, gy = np.meshgrid(xs, ys)
    return pd.DataFrame({"x": gx.ravel(), "y": gy.ravel()})


def interpoler_idw(
    x_cible, y_cible,
    x_source, y_source, valeurs,
    puissance: float = 2.0,
    n_voisins: int = 8,
    distance_min_m: float = 1.0,
) -> np.ndarray:
    """Interpolation par distance inverse — la référence à battre.

    `n_voisins` limite l'influence aux stations les plus proches : sans cette
    restriction, une station lointaine de l'autre bout de la région contribuerait
    encore, et le champ serait lissé jusqu'à perdre tout contraste local.

    **Limite structurelle, à énoncer :** l'IDW ne peut pas produire de valeur hors
    de l'intervalle des observations. Elle ne prédira donc jamais un maximum
    supérieur au maximum mesuré — alors que l'officiel, lui, modélise et peut
    dépasser. C'est une cause identifiée du biais résiduel.
    """
    xc = np.asarray(x_cible, dtype="float64")
    yc = np.asarray(y_cible, dtype="float64")
    xs = np.asarray(x_source, dtype="float64")
    ys = np.asarray(y_source, dtype="float64")
    v = np.asarray(valeurs, dtype="float64")

    fini = np.isfinite(v)
    xs, ys, v = xs[fini], ys[fini], v[fini]
    if len(v) == 0:
        return np.full(len(xc), np.nan)

    distances = np.maximum(
        np.hypot(xc[:, None] - xs[None, :], yc[:, None] - ys[None, :]), distance_min_m
    )

    k = min(n_voisins, len(v))
    proches = np.argpartition(distances, k - 1, axis=1)[:, :k]
    d_proches = np.take_along_axis(distances, proches, axis=1)
    v_proches = v[proches]

    poids = 1.0 / d_proches**puissance
    return (poids * v_proches).sum(axis=1) / poids.sum(axis=1)


def indexer_grille_par_zone(
    grille: pd.DataFrame, zones: list[dict], champ_code: str = "code_siren"
) -> pd.DataFrame:
    """Rattache chaque maille à la zone qui la contient.

    Les géométries sont « préparées » (index spatial interne) : sans cela, le test
    d'appartenance pour des dizaines de milliers de mailles contre des centaines de
    polygones est inutilisable.
    """
    from shapely.geometry import Point

    points = [Point(x, y) for x, y in zip(grille["x"], grille["y"])]
    affectation = np.full(len(grille), None, dtype=object)

    for zone in zones:
        geometrie = shape(zone["geometry"])
        prepare = prep(geometrie)
        x_min, y_min, x_max, y_max = geometrie.bounds
        # Pré-filtre par boîte englobante : le test exact ne s'applique qu'aux
        # mailles plausibles, ce qui change l'ordre de grandeur du temps de calcul.
        candidates = np.where(
            (grille["x"] >= x_min) & (grille["x"] <= x_max)
            & (grille["y"] >= y_min) & (grille["y"] <= y_max)
            & (affectation == None)  # noqa: E711 — comparaison à None sur objet
        )[0]
        for i in candidates:
            if prepare.contains(points[i]):
                affectation[i] = zone["properties"][champ_code]

    out = grille.copy()
    out["code_zone"] = affectation
    return out.dropna(subset=["code_zone"])


def agreger_par_zone(
    grille_valorisee: pd.DataFrame, colonne: str = "valeur"
) -> pd.DataFrame:
    """Statistiques par zone, dont le **maximum** — la grandeur officielle.

    La moyenne est conservée pour comparaison : l'écart entre maximum et moyenne
    mesure directement l'hétérogénéité interne de la zone, et donc la part du biais
    ponctuel imputable à la taille de l'EPCI.
    """
    return (
        grille_valorisee.groupby("code_zone", observed=True)[colonne]
        .agg(maximum="max", moyenne="mean", minimum="min", n_mailles="size")
        .reset_index()
    )
