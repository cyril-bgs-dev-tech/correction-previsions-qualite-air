#!/usr/bin/env python3
"""Cinq largeurs d'étalon saisonnier, mesurées mois par mois — l'arbitrage caché du recalage.

Le concept
------------
Le recalage d'amplitude remplace `ŷ` par `μ_y + (σ_y/σ_x)·(ŷ − μ_x)`, où les quatre moments
viennent des **mois antérieurs**, station évaluée exclue. Il ne crée aucune information — le
rang est préservé, donc à budget d'alertes constant les comptes ne bougent pas. Il déplace le
**point de fonctionnement** : une régression au moindre carré vise l'espérance
conditionnelle, donc elle est sous-dispersée par construction (`σ_x ≈ r·σ_y`), et rien ne
franchit un seuil haut parce que rien ne s'en approche.

Le paramètre `saison` décide **quels** mois antérieurs entrent dans l'étalon :

    saison=None  tous les mois antérieurs          étalon le plus fourni, mais un juillet
                                                    y est dilué par les hivers
    saison=0     le seul mois calendaire            le plus spécifique, le plus mince
    saison=1     mois calendaire ± 1  (défaut)      juin·juillet·août pour juillet
    saison=2     mois calendaire ± 2
    saison=3     mois calendaire ± 3

C'est un arbitrage **spécificité du régime ↔ taille de l'échantillon**, et rien ne dit que
son optimum soit fixe : il dépend de la profondeur d'historique déjà accumulée. C'est
précisément ce que ce banc mesure, mois par mois plutôt qu'en moyenne — une moyenne annuelle
annulerait le renversement qu'on cherche.

Ce que le banc affiche, et pourquoi
-------------------------------------
* **σ prédite / σ observée** — le diagnostic, pas le score. Un rapport sous 1 signale la
  sous-dispersion que le recalage doit corriger ; c'est lui qui explique les seuils manqués.
* **RMSE** — le recalage la **dégrade** presque toujours, et c'est attendu : il s'éloigne de
  l'optimum quadratique. L'afficher évite de vendre un gain là où il y a un échange.
* **détections / fausses alertes** à seuil physique fixe — le critère opérationnel.
* **part des lignes réellement recalées** — un mois sans historique suffisant se replie sur
  la valeur brute (`MIN_HISTORIQUE`, `n ≥ 200`). Ce repli est **compté et affiché** : sans
  cela, un réglage trop étroit paraîtrait neutre alors qu'il n'aurait simplement rien fait.

Usage : python3 scripts/banc_recalage_saisonnier.py [--polluants O3 NO2 ...]
Sortie : reports/banc_recalage_saisonnier.csv  ·  synthèse à l'écran
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

from decomposition_information import moments_anterieurs  # noqa: E402
from tableau_comparatif import SEUIL  # noqa: E402

POLLUANTS = ("O3", "NO2", "PM10", "PM25")
COURT = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}
REGLAGES = [("aucun", "sentinelle"), ("tous mois", None), ("±0 mois", 0),
            ("±1 mois", 1), ("±2 mois", 2), ("±3 mois", 3)]


def charger(polluant: str, horizon: int = 1) -> pd.DataFrame:
    f = RACINE / f"data/processed/predictions/production_{polluant}_h{horizon}.parquet"
    if not f.exists():
        raise SystemExit(f"absent : {f}")
    d = pd.read_parquet(f)
    for c in ("valeur", "nous", "mois", "station_id"):
        if c not in d:
            raise SystemExit(f"colonne absente de {f.name} : {c}")
    return d.sort_values(["mois", "station_id"]).reset_index(drop=True)


def recaler(d: pd.DataFrame, colonne: str, saison: int | None) -> tuple[np.ndarray, np.ndarray]:
    """Renvoie (valeurs recalées, masque des lignes réellement recalées).

    Le masque est la moitié qui compte : une ligne sans étalon garde sa valeur brute, et
    confondre « recalé sans effet » avec « pas recalé » ferait passer un réglage inerte
    pour un réglage neutre.
    """
    mom = moments_anterieurs(d, ["valeur", colonne], saison=saison)
    mu_y, sd_y = mom["valeur"]
    mu_x, sd_x = mom[colonne]
    brut = d[colonne].to_numpy()
    ech = np.where(sd_x > 1e-9, sd_y / np.maximum(sd_x, 1e-9), 1.0)
    r = mu_y + ech * (brut - mu_x)
    fait = np.isfinite(r)
    return np.clip(np.where(fait, r, brut), 0, None), fait


def mesurer(obs: np.ndarray, pred: np.ndarray, seuil: float) -> dict:
    depasse_obs, depasse_pred = obs >= seuil, pred >= seuil
    return {
        "n": len(obs),
        "rmse": float(np.sqrt(np.mean((pred - obs) ** 2))),
        "sigma_ratio": float(pred.std() / obs.std()) if obs.std() > 1e-9 else np.nan,
        "biais": float((pred - obs).mean()),
        "episodes": int(depasse_obs.sum()),
        "attrapes": int((depasse_obs & depasse_pred).sum()),
        "fausses": int((~depasse_obs & depasse_pred).sum()),
    }


def main(polluants: list[str]) -> int:
    lignes = []
    for pol in polluants:
        d = charger(pol)
        seuil = SEUIL[pol]
        print(f"\n═══ {COURT[pol]} · seuil {seuil:g} µg/m³ · {len(d):,} lignes · "
              f"{d['mois'].nunique()} mois ═══", flush=True)
        for nom, saison in REGLAGES:
            t0 = time.time()
            if saison == "sentinelle":
                pred, fait = d["nous"].to_numpy(), np.ones(len(d), bool)
            else:
                pred, fait = recaler(d, "nous", saison)
            dt = time.time() - t0
            part = float(fait.mean())
            for mois, idx in d.groupby("mois", observed=True).indices.items():
                m = mesurer(d["valeur"].to_numpy()[idx], pred[idx], seuil)
                lignes.append({"polluant": pol, "reglage": nom, "saison": str(saison),
                               "mois": mois, "part_recalee": float(fait[idx].mean()), **m})
            glob = mesurer(d["valeur"].to_numpy(), pred, seuil)
            print(f"  {nom:<10} recalé {part:5.1%} · RMSE {glob['rmse']:6.3f} · "
                  f"σ/σ {glob['sigma_ratio']:5.3f} · {glob['attrapes']:>5}/{glob['episodes']} "
                  f"attrapés · {glob['fausses']:>6} fausses · {dt:4.1f} s", flush=True)

    t = pd.DataFrame(lignes)
    manque = [c for c in ("polluant", "reglage", "mois", "rmse", "sigma_ratio",
                          "attrapes", "fausses", "part_recalee") if c not in t]
    if manque:
        raise SystemExit(f"colonnes absentes du rapport : {manque}")
    cible = RACINE / "reports/banc_recalage_saisonnier.csv"
    t.to_csv(cible, index=False)
    print(f"\nÉcrit : {cible.relative_to(RACINE)} · {len(t)} lignes")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--polluants", nargs="+", default=list(POLLUANTS))
    raise SystemExit(main(ap.parse_args().polluants))
