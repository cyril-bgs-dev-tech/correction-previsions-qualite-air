#!/usr/bin/env python3
"""L'écart entre échéances : une mesure d'incertitude déjà dans les données.

L'idée
------
CAMS produit chaque jour des prévisions à 0-72 h. Une même heure cible est donc couverte par
**plusieurs runs** : celui de la veille la voit à ~12 h d'échéance, celui de l'avant-veille à
~36 h, et ainsi de suite. **L'écart entre ces prévisions successives mesure la stabilité du
signal** — et il est disponible sans rien télécharger.

C'est un substitut à la dispersion d'ensemble, que le projet n'a pas et que la littérature
juge utile comme indicateur d'incertitude. Contrairement à l'altitude — qui s'est révélée
déductible des coordonnées et du relief — cette information **n'est pas dans le jeu** : elle
naît de la comparaison entre runs, que rien d'autre ne porte.

Deux usages, testés séparément :

1. **Comme prédicteur** — le modèle peut moduler sa correction selon la stabilité ;
2. **Comme indicateur de confiance** — une prévision instable signale un jour où il vaut
   peut-être mieux s'abstenir. C'est le garde-fou fondé sur l'incertitude plutôt que sur le
   niveau.

Calcul par le moteur unique du projet (`aq.models.moteur`). ⚠️ Ce docstring affirmait que
« les trois bibliothèques de boosting tiennent en 0,3 point » : **aucune mesure de ce type
n'existe dans le dépôt** — le seul banc compare LightGBM, Ridge et forêt aléatoire. Retiré le
02/08/2026. Ancien texte, à ne pas réutiliser :
ce problème, donc le choix est neutre pour la conclusion et libère les 32 cœurs.

Usage : python3 scripts/ecart_echeances.py [--polluant O3]
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

from aq.eval import comparaison as cmp  # noqa: E402
from aq.models import mos  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from fit_mos import ESPECES, charger, colonnes_admises  # noqa: E402


def construire_ecart(polluant: str) -> pd.DataFrame:
    """Pour chaque (station, heure cible) : dispersion des prévisions selon l'échéance.

    On ne garde que les cibles vues par **au moins deux** échéances distinctes — sans quoi
    l'écart n'existe pas et la variable serait un simple indicateur de disponibilité.
    """
    court = next(c for c, (p, _) in ESPECES.items() if p == polluant)
    colonne = ESPECES[court][1]
    fichiers = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_*.parquet")))

    blocs = []
    for fichier in fichiers:
        d = pd.read_parquet(
            fichier, columns=["station_id", "timestamp_utc", "echeance_h", colonne])
        # Tranches d'échéance : chaque run couvre la cible à un délai différent.
        d["tranche"] = pd.cut(d["echeance_h"], bins=[-1, 24, 48, 72],
                              labels=["j1", "j2", "j3"])
        g = d.groupby(["station_id", "timestamp_utc"], observed=True)[colonne]
        agr = g.agg(["std", "min", "max", "count"]).reset_index()
        agr = agr[agr["count"] >= 2]
        blocs.append(agr)

    e = pd.concat(blocs, ignore_index=True)
    e = e.rename(columns={"std": "ech_ecart_type", "min": "ech_min", "max": "ech_max"})
    e["ech_amplitude"] = e["ech_max"] - e["ech_min"]
    # Amplitude **relative** : 5 µg/m³ d'écart n'ont pas le même sens à 20 et à 150.
    e["ech_amplitude_rel"] = e["ech_amplitude"] / e["ech_max"].clip(lower=1.0)
    return e.drop(columns=["count", "ech_min", "ech_max"])


def _xgb(graine: int):
    """XGBoost sur GPU — paramètres miroir du LightGBM réglé du projet."""
    return modele_mos(graine=graine)


def main(polluant: str, horizon: int, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    ecart = construire_ecart(polluant)
    print(f"{polluant} · {len(ecart):,} cibles vues par ≥2 échéances", flush=True)

    avant = len(jeu)
    jeu = jeu.merge(ecart, on=["station_id", "timestamp_utc"], how="inner")
    print(f"  jeu apparié : {avant:,} → {len(jeu):,} lignes "
          f"({100 * len(jeu) / avant:.0f} %)", flush=True)

    nouvelles = ["ech_ecart_type", "ech_amplitude", "ech_amplitude_rel"]
    print(f"  dispersion entre échéances : médiane "
          f"{jeu['ech_ecart_type'].median():.2f} µg/m³ · "
          f"90e centile {jeu['ech_ecart_type'].quantile(0.9):.2f}\n", flush=True)

    base = cmp.metriques(jeu["valeur"], jeu["cams"])
    print(f"{'jeu de variables':28s} {'RMSE':>7s} {'R²':>8s} {'gain':>8s} {'durée':>7s}")
    print(f"{'CAMS brut':28s} {base['rmse']:7.2f} {base['r2']:+8.3f}", flush=True)

    resultats = {}
    for nom, cols in (("sans écart d'échéances", colonnes),
                      ("avec écart d'échéances", colonnes + nouvelles)):
        t0 = time.time()
        r = mos.ajuster_par_stations_exclues(
            jeu, cols, colonne_cams="cams", n_plis=n_plis,
            verbeux=False, fabrique_modele=_xgb,
        )
        p = r.predictions.dropna(subset=["observe"])
        m = cmp.metriques(p["observe"], p["corrige"])
        resultats[nom] = (m, p)
        print(f"{nom:28s} {m['rmse']:7.2f} {m['r2']:+8.3f} "
              f"{100 * (1 - m['rmse'] / base['rmse']):+7.1f} % {time.time() - t0:6.0f}s",
              flush=True)

    ecart_pts = (100 * (1 - resultats["avec écart d'échéances"][0]["rmse"] / base["rmse"])
                 - 100 * (1 - resultats["sans écart d'échéances"][0]["rmse"] / base["rmse"]))
    delta_rmse = (resultats["sans écart d'échéances"][0]["rmse"]
                  - resultats["avec écart d'échéances"][0]["rmse"])
    print(f"\napport comme prédicteur : {ecart_pts:+.2f} point · "
          f"{delta_rmse:+.3f} µg/m³")
    print(f"  critère d'arrêt du projet : ≥ 0,3 µg/m³ → "
          f"{'RETENU' if delta_rmse >= 0.3 else 'SOUS LE SEUIL'}", flush=True)

    # ── Second usage : la dispersion prédit-elle l'échec de la correction ? ────
    p = resultats["avec écart d'échéances"][1].merge(
        jeu[["station_id", "timestamp_utc"] + nouvelles],
        on=["station_id", "timestamp_utc"], how="left")
    p["correction_utile"] = ((p["corrige"] - p["observe"]).abs()
                             < (p["cams"] - p["observe"]).abs())
    print("\nLa dispersion annonce-t-elle une correction inutile ?")
    quartiles = pd.qcut(p["ech_ecart_type"], 4, labels=["Q1 stable", "Q2", "Q3", "Q4 instable"],
                        duplicates="drop")
    for q, g in p.groupby(quartiles, observed=True):
        print(f"  {str(q):12s} n={len(g):>9,} · correction utile "
              f"{100 * g['correction_utile'].mean():5.1f} % · "
              f"gain {100 * (1 - np.sqrt(((g['corrige'] - g['observe'])**2).mean()) / np.sqrt(((g['cams'] - g['observe'])**2).mean())):+5.1f} %",
              flush=True)

    pd.DataFrame([{"variante": k, **v[0]} for k, v in resultats.items()]).to_csv(
        RACINE / f"reports/ecart_echeances_{polluant}.csv", index=False)
    print(f"\nÉcrit : reports/ecart_echeances_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
