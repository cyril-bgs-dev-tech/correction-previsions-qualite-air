#!/usr/bin/env python3
"""L'intervalle du plan sur les quatre chiffres du socle — chantier ②.

Pourquoi un point nu ne suffit pas
-----------------------------------
Le contrat de produit publie « ≈ 41 % ». L'arrondi vient d'une mesure : 0,14 % de données
déplacent un pli de 2,56 pt. Mais l'arrondi ne DIT pas l'incertitude — il la cache.

Trois sources se distinguent, et elles n'ont ni la même taille ni le même remède :

1. **bruit d'exécution** à données identiques — mesuré ≤ 0,039 pt par pli. Le plus petit.
   Se réduit en moyennant des graines ; ce n'est pas la priorité.
2. **échantillonnage des mois et des stations** — c'est CET intervalle. Il répond à
   « et si le corpus avait couvert d'autres mois ? ».
3. **version du corpus** — l'enveloppe de stabilité, chantier ① : « et si les données
   avaient été corrigées autrement ? ». Non couverte ici.

Ce script calcule la deuxième, par bootstrap sur blocs de trois mois consécutifs — l'unité
de réplication du plan, puisque la rotation `groupes[i % 3]` fait qu'un bloc de trois mois
voit les trois groupes de stations.

⚠️ Ce n'est PAS un intervalle sur l'effet d'une famille : c'est l'incertitude du SCORE du
produit. Les décisions de famille restent portées par des écarts appariés, qui soustraient
le déplacement commun et sont bien plus serrés.

Usage  : python3 scripts/intervalle_socle.py [--variante _sans-feux-geoscf_fenetre-complete]
Sortie : reports/intervalle_socle.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
from verdict_apports import blocs_de  # noqa: E402

P4 = ("NO2", "O3", "PM10", "PM25")
MAX = "★ MAXIMALE — PARTOUT"
BLOC = 3


def main(variante: str, horizon: int, tirages: int, graine: int) -> int:
    rng = np.random.default_rng(graine)
    lignes = []
    print(f"INTERVALLE DU PLAN · variante « {variante or 'référence'} » · "
          f"blocs de {BLOC} mois · {tirages:,} tirages")
    print("═" * 96)
    print(f"{'polluant':9s} {'mois':>5s} {'blocs':>6s} {'score':>8s} "
          f"{'IC95 du plan':>20s} {'demi-largeur':>13s}   à dire")
    for p in P4:
        f = RACINE / f"reports/methode_maximale_{p}_h{horizon}{variante}_par_pli.csv"
        if not f.exists():
            print(f"{p:9s} ✘ absent : {f.name}")
            continue
        t = pd.read_csv(f)
        s = t[t["configuration"] == MAX]
        if s.empty:
            print(f"{p:9s} ✘ configuration MAXIMALE absente")
            continue
        # 🔴 Le gain POOLÉ, jamais une moyenne de gains — corrigé le 24/08.
        #
        # La première version moyennait les `gain_pct` des plis, pondérés par leur
        # effectif. Elle donnait 16,68 % sur l'ozone là où la pile en publie 19,44 : la
        # RMSE n'est pas linéaire, donc la moyenne des ratios n'est pas le ratio des
        # moyennes. L'intervalle était centré sur une autre grandeur que le chiffre publié.
        #
        # Le gain poolé se reconstruit exactement depuis les colonnes du fichier :
        #     1 − √( Σ nᵢ·rmse_corrigéᵢ² / Σ nᵢ·rmse_camsᵢ² )
        # Chaque bloc porte donc ses deux sommes de carrés pondérées, et le rééchantillonnage
        # recompose le ratio — pas la moyenne.
        n = s["n_test"].to_numpy(dtype=float)
        sc = n * s["rmse_corrige"].to_numpy() ** 2
        sa = n * s["rmse_cams"].to_numpy() ** 2
        k = len(n) - len(n) % BLOC
        b_c = np.array([sc[i:i + BLOC].sum() for i in range(0, k, BLOC)])
        b_a = np.array([sa[i:i + BLOC].sum() for i in range(0, k, BLOC)])
        v = list(s["gain_pct"].to_numpy())
        if len(b_c) < 6:
            print(f"{p:9s} ✘ {len(b_c)} blocs — trop peu pour un intervalle")
            continue
        idx = rng.integers(0, len(b_c), size=(tirages, len(b_c)))
        ech = 100 * (1 - np.sqrt(b_c[idx].sum(axis=1) / b_a[idx].sum(axis=1)))
        centre = float(100 * (1 - np.sqrt(b_c.sum() / b_a.sum())))
        b_v = b_c
        bas, haut = (float(x) for x in np.percentile(ech, [2.5, 97.5]))
        demi = (haut - bas) / 2
        dire = f"≈ {round(centre):.0f} %"
        print(f"{p:9s} {len(v):5d} {len(b_v):6d} {centre:7.2f}% "
              f"[{bas:7.2f} ; {haut:7.2f}] {demi:12.2f} pt   {dire}")
        lignes.append({"variante": variante or "reference", "polluant": p,
                       "n_mois": len(v), "n_blocs": len(b_v), "score_pct": centre,
                       "ic95_bas": bas, "ic95_haut": haut, "demi_largeur_pt": demi,
                       "a_dire": dire})
    if not lignes:
        return 1
    print("═" * 96)
    t = pd.DataFrame(lignes)
    print(f"demi-largeur médiane : ±{t['demi_largeur_pt'].median():.2f} pt — c'est "
          f"l'incertitude d'ÉCHANTILLONNAGE seule.")
    print("Elle ne couvre ni le bruit d'exécution (≤0,04 pt/pli) ni la version du corpus")
    print("(chantier ①, non calculée). Le chiffre à dire reste l'arrondi à l'entier.")
    sortie = RACINE / f"reports/intervalle_socle{variante}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--variante", default="_sans-feux-geoscf_fenetre-complete")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--tirages", type=int, default=10000)
    a.add_argument("--graine", type=int, default=20260824)
    sys.exit(main(**vars(a.parse_args())))
