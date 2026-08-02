#!/usr/bin/env python3
"""Combiner deux corrections : front de Pareto entre erreur globale et erreur de queue.

Le problème que cela résout
---------------------------
Mesuré sur ce projet (`reports/queue_O3.csv`, 17 mois, stations exclues) : la correction
par **erreur quadratique** gagne +19,4 % de RMSE global mais devient **pire que CAMS brut
de 3,1 %** sur le décile supérieur — là où se jouent les épisodes. La variante **pondérée
par la concentration** fait l'inverse : +12,4 % global seulement, mais **+8,5 %** sur la
queue.

Aucune des deux n'est bonne partout. Plutôt que de choisir, on **commute** : la prédiction
prudente pour le fond, la prédiction pondérée quand on entre dans le haut de la
distribution. Le seuil de commutation trace un front de Pareto entre les deux erreurs.

**Ce que ce script ne fait pas.** Il ne prétend pas désigner un seuil optimal : le choisir
sur les données qui servent à l'évaluer serait une fuite, et l'optimum dépend du coût
relatif d'une alerte manquée et d'une fausse alerte — un arbitrage de politique publique,
pas de statistique. Le script **trace le front** et laisse le choix explicite.

La commutation se fait sur la **prédiction** et jamais sur l'observation : décider d'après
la valeur mesurée serait inapplicable en prévision, et gonflerait artificiellement les
scores.

Entrée : `reports/queue_predictions_{polluant}.csv`, produit par `preserver_la_queue.py`.
Aucun ajustement — pur post-traitement, quelques secondes.

Usage : python3 scripts/front_pareto_queue.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval import comparaison as cmp  # noqa: E402

COLONNE_FOND = "erreur_quadratique"
COLONNE_QUEUE = "quadratique_pondérée_par_la_concentration"


def _rmse(observe, predit) -> float:
    return float(cmp.metriques(observe, predit)["rmse"])


def main(polluant: str, quantile_haut: float) -> int:
    chemin = RACINE / f"reports/queue_predictions_{polluant}.csv"
    if not chemin.exists():
        print(f"ÉCHEC : {chemin.name} absent — relancer preserver_la_queue.py",
              file=sys.stderr)
        return 1

    d = pd.read_csv(chemin)
    manquantes = [c for c in (COLONNE_FOND, COLONNE_QUEUE) if c not in d.columns]
    if manquantes:
        print(f"ÉCHEC : colonnes absentes {manquantes} · présentes : {list(d.columns)}",
              file=sys.stderr)
        return 1

    seuil_haut = d["valeur"].quantile(quantile_haut)
    haut = d["valeur"] >= seuil_haut
    print(f"{polluant} · {len(d):,} lignes · décile supérieur au-delà de "
          f"{seuil_haut:.1f} µg/m³ ({int(haut.sum()):,} lignes)\n", flush=True)

    rmse_cams = _rmse(d["valeur"], d["cams"])
    rmse_cams_haut = _rmse(d.loc[haut, "valeur"], d.loc[haut, "cams"])

    print(f"{'règle':38s} {'RMSE':>7s} {'queue':>7s} {'gain glob.':>11s} {'gain queue':>11s}")
    print(f"{'CAMS brut':38s} {rmse_cams:7.2f} {rmse_cams_haut:7.2f}")

    lignes = []

    def _mesurer(nom: str, predit: pd.Series, seuil=None) -> None:
        rg = _rmse(d["valeur"], predit)
        rh = _rmse(d.loc[haut, "valeur"], predit[haut])
        gg = 100 * (1 - rg / rmse_cams)
        gh = 100 * (1 - rh / rmse_cams_haut)
        print(f"{nom:38s} {rg:7.2f} {rh:7.2f} {gg:+10.1f} % {gh:+10.1f} %", flush=True)
        lignes.append({"regle": nom, "seuil_commutation": seuil, "rmse": rg,
                       "rmse_queue": rh, "gain_global": gg, "gain_queue": gh})

    _mesurer("fond seul (quadratique)", d[COLONNE_FOND])
    _mesurer("queue seule (pondérée)", d[COLONNE_QUEUE])

    # Le front : commuter vers la prédiction pondérée au-delà d'un seuil, lu sur la
    # **prédiction de fond** — la seule information disponible en situation réelle.
    print()
    for seuil in (40, 50, 60, 70, 80, 90, 100, 110, 120):
        commute = d[COLONNE_FOND] >= seuil
        predit = d[COLONNE_FOND].where(~commute, d[COLONNE_QUEUE])
        part = 100 * commute.mean()
        _mesurer(f"commutation à {seuil} µg/m³ ({part:4.1f} % comm.)", predit, seuil)

    sortie = RACINE / f"reports/front_pareto_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    print("Le seuil ne se déduit pas de ce tableau : il dépend du coût relatif d'une "
          "alerte manquée\net d'une fausse alerte, qui est une décision, pas une mesure.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--quantile-haut", type=float, default=0.90)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.quantile_haut))
