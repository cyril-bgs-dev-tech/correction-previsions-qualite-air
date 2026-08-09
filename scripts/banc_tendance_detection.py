#!/usr/bin/env python3
"""`tendance_cams` apporte-t-il quelque chose **en détection** — et sur quels polluants ?

Pourquoi ce banc existe
-------------------------
`tendance_cams` a été retenu sur le **plancher d'information** : +2,08 pt sur l'ozone dans
la pile, +0,13 à +0,45 ailleurs. Or le dossier porte sa propre règle, écrite avant :

> *« Une variable peut n'apporter rien à la précision ponctuelle et beaucoup au classement
> des jours à risque. D'où la règle : tester en détection ce qui a été écarté sur le RMSE,
> et réciproquement. »*

La réciproque n'avait jamais été honorée pour ce levier : aucun script de détection ne
connaît `tendance`. Ce banc la mesure, et il le fait **avant** de porter la famille en
production — un lot de 55 minutes pour un gain qu'on n'aurait pas vérifié serait exactement
la faute que `CLAUDE.md` § 1 reproche.

Le protocole, identique à celui qui a retenu la famille
---------------------------------------------------------
Mêmes plis de **double aveugle** (station ET mois cachés ensemble), même graine, même
ajusteur, même corpus en cache que `banc_preprocessing`. Seules les colonnes changent. Un
banc qui redéfinirait ses plis mesurerait la partition autant que la famille — σ 0,20 point
par partition contre 1,31 par composition en mois, mesuré le 04/08.

Les deux lectures, et pourquoi il en faut deux
------------------------------------------------
* **à seuil physique fixe** — la vue opérationnelle. Elle mélange deux choses : le pouvoir
  de classement, et la position de l'échelle. Une variable qui ne fait que dilater la
  prédiction y gagne sans rien apprendre.
* **à budget d'alertes constant** — le même nombre d'alertes émises pour les deux variantes,
  donc **invariant par toute transformation monotone**. C'est le seul des deux qui mesure
  de l'*information*. S'ils divergent, c'est le second qui tranche.

Reprise : le `.partiel` est relu par nom de polluant. Un chargement de corpus sur deux à
cinq finit en `code=139` sur cette machine — un lot qui repart de zéro n'aboutirait jamais.

Usage : python3 scripts/banc_tendance_detection.py [--polluants O3 NO2 PM10 PM25]
Sortie : reports/banc_tendance_detection.csv
"""
from __future__ import annotations

import argparse
import gc
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from banc_preprocessing import FAMILLES, plis_double_aveugle, preparer  # noqa: E402
from double_aveugle_journalier import ajuster  # noqa: E402
from modele_final import DEFAUT  # noqa: E402
from tableau_comparatif import SEUIL  # noqa: E402

COURT = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}
CIBLE = RACINE / "reports/banc_tendance_detection.csv"


def scores(obs_h: np.ndarray, pred_h: np.ndarray) -> dict:
    tp = int((obs_h & pred_h).sum())
    fn = int((obs_h & ~pred_h).sum())
    fp = int((~obs_h & pred_h).sum())
    return {"attrapes": tp, "manques": fn, "fausses": fp,
            "rappel": tp / (tp + fn) if tp + fn else np.nan,
            "csi": tp / (tp + fn + fp) if tp + fn + fp else np.nan}


def a_budget(obs_h: np.ndarray, pred: np.ndarray, n_alertes: int) -> dict:
    """Attrapés quand on émet EXACTEMENT `n_alertes` — invariant par transformation monotone.

    C'est la seule lecture qui mesure de l'information : dilater ou décaler une prédiction
    n'y change rien, seul son **ordre** compte.
    """
    if n_alertes <= 0 or n_alertes >= len(pred):
        return {"attrapes_budget": np.nan}
    seuil = np.partition(pred, -n_alertes)[-n_alertes]
    return {"attrapes_budget": int((obs_h & (pred >= seuil)).sum())}


def variante(d: pd.DataFrame, colonnes: list[str], plis, seuil: float) -> dict:
    """Prédictions hors pli concaténées, puis les deux lectures de détection."""
    gardees = list(dict.fromkeys(["valeur", "cams_jour", *colonnes]))
    t = d[gardees].astype({c: "float64" for c in gardees}).copy()
    obs, pred, ecartes = [], [], 0
    for _etiq, mt, mtr in plis:
        te, tr = t[mt.to_numpy()], t[mtr.to_numpy()]
        if len(te) < 200 or tr.empty:
            ecartes += 1                      # § 2 quater : un pli écarté se compte
            continue
        obs.append(te["valeur"].to_numpy())
        pred.append(ajuster(DEFAUT, tr, te, colonnes, "cams_jour"))
    o, p = np.concatenate(obs), np.concatenate(pred)
    haut = o >= seuil
    r = scores(haut, p >= seuil)
    r["plis_ecartes"] = ecartes
    r["n"] = len(o)
    r["episodes"] = int(haut.sum())
    return r, o, p, haut


def main(polluants: list[str], horizon: int) -> int:
    faits = {}
    if CIBLE.with_suffix(".csv.partiel").exists():
        deja = pd.read_csv(CIBLE.with_suffix(".csv.partiel"))
        faits = {p: g for p, g in deja.groupby("polluant")}
        print(f"reprise : {sorted(faits)} déjà mesurés", flush=True)

    lignes = [r for g in faits.values() for r in g.to_dict("records")]
    for pol in polluants:
        if pol in faits:
            continue
        t0 = time.time()
        seuil = SEUIL[pol]
        d, base = preparer(pol, horizon)
        plis = plis_double_aveugle(d)
        neuves = FAMILLES["tendance_cams"](d)
        avec_cols = base + [c for c in neuves.columns if c not in base]
        d_avec = pd.concat([d, neuves[[c for c in neuves.columns if c not in d]]], axis=1)
        print(f"\n═══ {COURT[pol]} · {len(d):,} lignes · {len(plis)} plis · "
              f"seuil {seuil:g} µg/m³ · +{len(avec_cols)-len(base)} colonnes ═══", flush=True)

        r_sans, o, p_sans, haut = variante(d, base, plis, seuil)
        r_avec, _, p_avec, _ = variante(d_avec, avec_cols, plis, seuil)
        # budget = le volume d'alertes de la variante SANS ; l'autre doit faire mieux
        # avec le même volume, sinon elle n'a rien appris qu'un seuil ne ferait.
        budget = r_sans["attrapes"] + r_sans["fausses"]
        r_sans.update(a_budget(haut, p_sans, budget))
        r_avec.update(a_budget(haut, p_avec, budget))
        for nom, r in (("sans tendance", r_sans), ("avec tendance", r_avec)):
            lignes.append({"polluant": pol, "variante": nom, "budget_alertes": budget,
                           "secondes": round(time.time() - t0, 1), **r})
        # ⚠️ ÉCRIRE AVANT D'AFFICHER. La version précédente imprimait puis enregistrait, et
        # un `{:+d}` sur un NaN — budget nul, cas réel du NO₂ dont le seuil de 200 µg/m³ ne
        # retient qu'un dépassement — levait AVANT le `to_csv`. La reprise ne progressait
        # donc jamais sur ce polluant : cinq relances, cinq fois le même travail perdu.
        # `CLAUDE.md` § 2 ter, en pire : ici l'affichage empêchait l'enregistrement.
        pd.DataFrame(lignes).to_csv(CIBLE.with_suffix(".csv.partiel"), index=False)

        def q(v, entier=False):
            """Format tolérant au NaN — un polluant sans épisode n'est pas une panne."""
            if v is None or (isinstance(v, float) and not np.isfinite(v)):
                return "n/a"
            return f"{int(v):+d}" if entier else f"{v:.4f}"

        print(f"  {'seuil physique':<18} CSI {q(r_sans['csi'])} → {q(r_avec['csi'])}"
              f"  ({q(r_avec['csi'] - r_sans['csi'])})   "
              f"rappel {r_sans['rappel']:.1%} → {r_avec['rappel']:.1%}")
        if np.isfinite(r_sans.get("attrapes_budget", np.nan)):
            d_b = r_avec["attrapes_budget"] - r_sans["attrapes_budget"]
            print(f"  {'budget constant':<18} {int(r_sans['attrapes_budget'])} → "
                  f"{int(r_avec['attrapes_budget'])} épisodes  ({q(d_b, True)}) sur "
                  f"{budget:,} alertes   · {time.time()-t0:.0f} s", flush=True)
        else:
            print(f"  {'budget constant':<18} non évaluable — {r_sans['episodes']} "
                  f"dépassement(s) dans le corpus, budget {budget} alerte(s)."
                  f"   · {time.time()-t0:.0f} s", flush=True)
        del d, d_avec, neuves
        gc.collect()

    t = pd.DataFrame(lignes)
    for c in ("polluant", "variante", "csi", "attrapes_budget", "plis_ecartes"):
        if c not in t:
            raise SystemExit(f"colonne absente du rapport : {c}")
    t.to_csv(CIBLE, index=False)
    CIBLE.with_suffix(".csv.partiel").unlink(missing_ok=True)
    print(f"\nÉcrit : {CIBLE.relative_to(RACINE)} · {len(t)} lignes")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--polluants", nargs="+", default=["O3", "NO2", "PM10", "PM25"])
    ap.add_argument("--horizon", type=int, default=2)
    a = ap.parse_args()
    raise SystemExit(main(a.polluants, a.horizon))
