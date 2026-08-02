"""Calibration binaire Venn–Abers rapide, sans dépendance supplémentaire.

L'algorithme géométrique est adapté de ``venn-abers`` 1.5.1 (Ivan Petej,
licence MIT) et des algorithmes de Vovk, Petej et Fedorova (2015) :
https://arxiv.org/abs/1511.00213.

Le module ne construit pas les plis. Cette responsabilité reste au script appelant afin
que les ensembles d'apprentissage et de calibration soient bloqués par station et par
temps, ce que les séparations aléatoires proposées par les interfaces génériques ne
garantissent pas.
"""

from __future__ import annotations

import numpy as np


def _vecteurs_isotones(scores: np.ndarray, etiquettes: np.ndarray,
                       precision: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pré-calcule les deux isotones correspondant aux labels hypothétiques 0 et 1."""
    s = np.asarray(scores, dtype="float64").reshape(-1)
    y = np.asarray(etiquettes, dtype="float64").reshape(-1)
    if len(s) != len(y) or len(s) == 0:
        raise ValueError("scores et étiquettes doivent avoir la même longueur non nulle")
    if not np.isfinite(s).all() or not np.isfinite(y).all():
        raise ValueError("scores et étiquettes doivent être finis")
    if not np.isin(y, [0.0, 1.0]).all():
        raise ValueError("Venn–Abers exige une cible binaire 0/1")
    if precision is not None:
        s = np.round(s, precision)

    ordre = np.argsort(s, kind="mergesort")
    s_tries = s[ordre]
    y_tries = y[ordre]
    uniques = np.unique(s_tries)
    debut = np.searchsorted(s_tries, uniques)

    poids = np.empty(len(uniques), dtype="float64")
    poids[:-1] = np.diff(debut)
    poids[-1] = len(s_tries) - debut[-1]

    # Diagramme des sommes cumulées utilisé par l'algorithme rapide de Venn–Abers.
    P = np.zeros((len(uniques) + 2, 2), dtype="float64")
    P[0, 0] = -1.0
    P[2:, 0] = np.cumsum(poids)
    if len(uniques) > 1:
        P[2:-1, 1] = np.cumsum(y_tries)[(debut - 1)[1:]]
    P[-1, 1] = np.cumsum(y_tries)[-1]

    p1 = np.zeros((len(uniques) + 1, 2), dtype="float64")
    p1[1:, 0] = uniques
    P1 = P[1:].copy() + 1.0
    point = 0
    pente = 0.0
    for i in range(len(p1)):
        P1[i] -= 1.0
        if i == 0:
            with np.errstate(divide="ignore", invalid="ignore"):
                pentes = P1[:, 1] / P1[:, 0]
            pente = float(np.nanmin(pentes))
            point = 0
        else:
            niveau = P1[point, 1] + (P1[i, 0] - P1[point, 0]) * pente
            if P1[i, 1] < niveau:
                with np.errstate(divide="ignore", invalid="ignore"):
                    pentes = ((P1[i:, 1] - P1[i, 1]) /
                              (P1[i:, 0] - P1[i, 0]))
                finies = pentes[np.isfinite(pentes)]
                if len(finies):
                    pente = float(finies.min())
                point = i
        p1[i, 1] = pente

    p0 = np.zeros((len(uniques) + 1, 2), dtype="float64")
    p0[1:, 0] = uniques
    P0 = P[1:].copy()
    point = len(p0) - 1
    pente = 0.0
    for i in range(len(p0) - 1, -1, -1):
        P0[i, 0] += 1.0
        if i == len(p0) - 1:
            with np.errstate(divide="ignore", invalid="ignore"):
                pentes = ((P0[:, 1] - P0[i, 1]) /
                           (P0[:, 0] - P0[i, 0]))
            pente = float(np.nanmax(pentes))
            point = i
        else:
            niveau = P0[point, 1] + (P0[i, 0] - P0[point, 0]) * pente
            if P0[i, 1] < niveau:
                with np.errstate(divide="ignore", invalid="ignore"):
                    pentes = ((P0[:, 1] - P0[i, 1]) /
                               (P0[:, 0] - P0[i, 0]))
                pentes[i:] = 0.0
                pente = float(np.nanmax(pentes))
                point = i
        p0[i, 1] = pente

    p0[:, 1] = np.clip(p0[:, 1], 0.0, 1.0)
    p1[:, 1] = np.clip(p1[:, 1], 0.0, 1.0)
    return p0, p1, uniques


def calibrer_venn_abers(scores_calibration: np.ndarray,
                        etiquettes_calibration: np.ndarray,
                        scores_test: np.ndarray,
                        precision: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rend la probabilité ponctuelle et les bornes ``p0``/``p1`` d'un IVAP.

    La probabilité ponctuelle minimise le pire regret en log-loss :
    ``p = p1 / (1 - p0 + p1)``. La garantie Venn porte sur la paire
    multiprobabiliste, pas isolément sur ce résumé ponctuel.
    """
    test = np.asarray(scores_test, dtype="float64").reshape(-1)
    if not np.isfinite(test).all():
        raise ValueError("les scores de test doivent être finis")
    if precision is not None:
        test = np.round(test, precision)
    p0_tab, p1_tab, uniques = _vecteurs_isotones(
        scores_calibration, etiquettes_calibration, precision=precision)
    p0 = p0_tab[np.searchsorted(uniques, test, side="right"), 1]
    p1 = p1_tab[np.searchsorted(uniques, test, side="left"), 1]
    # Les erreurs numériques ne doivent jamais produire un intervalle inversé.
    bas = np.minimum(p0, p1)
    haut = np.maximum(p0, p1)
    denominateur = 1.0 - bas + haut
    point = np.divide(haut, denominateur, out=np.full_like(haut, 0.5),
                      where=denominateur > 0)
    return np.clip(point, 0.0, 1.0), bas, haut


def fusionner_cvap(bornes_basses: np.ndarray,
                   bornes_hautes: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fusion log-loss des IVAP d'un CVAP, un pli par colonne.

    La paire fusionnée est ``(1-GM(1-p0), GM(p1))`` et la probabilité ponctuelle
    normalise ``GM(1-p0)`` et ``GM(p1)``.
    """
    p0 = np.asarray(bornes_basses, dtype="float64")
    p1 = np.asarray(bornes_hautes, dtype="float64")
    if p0.shape != p1.shape or p0.ndim != 2 or p0.shape[1] < 2:
        raise ValueError("les bornes CVAP doivent être deux matrices n×k, k>=2")
    eps = np.finfo("float64").tiny
    gm_zero = np.exp(np.mean(np.log(np.clip(1.0 - p0, eps, 1.0)), axis=1))
    gm_un = np.exp(np.mean(np.log(np.clip(p1, eps, 1.0)), axis=1))
    bas = np.clip(1.0 - gm_zero, 0.0, 1.0)
    haut = np.clip(gm_un, 0.0, 1.0)
    point = gm_un / (gm_zero + gm_un)
    return np.clip(point, 0.0, 1.0), np.minimum(bas, haut), np.maximum(bas, haut)
