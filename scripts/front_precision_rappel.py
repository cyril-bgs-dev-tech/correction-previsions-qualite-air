#!/usr/bin/env python3
"""Le front précision–rappel : à précision égale, combien détectons-nous ?

La question
-----------
Au seuil réglementaire, notre correction annonce 70 jours-station en 2025 dont **68 justes**
— 97 % de précision — quand le produit officiel en annonce 108 dont 74, soit **69 %**. Nous
sommes donc plus précis, mais nous rappelons un peu moins : 42,5 % contre 46,2 %.

Ces deux points ne se comparent pas directement : ils sont pris à des **régimes différents**.
La question utile est celle du front — *si l'on abaisse notre seuil jusqu'à accepter la même
proportion de fausses alertes que le produit officiel, quel rappel atteint-on ?*

Ce que le script produit
------------------------
Le front complet, obtenu en balayant le seuil de décision, et trois lectures :

1. **à précision égale** — le rappel atteint quand notre précision descend au niveau du
   produit officiel ;
2. **à rappel égal** — la précision obtenue quand notre rappel monte à son niveau ;
3. le **seuil réglementaire brut**, sans réglage, pour situer.

**Le seuil est choisi hors échantillon** : calibré sur une partie des stations, appliqué aux
autres. Le régler sur les données qui l'évaluent transformerait un front en illusion.

Usage : python3 scripts/front_precision_rappel.py [--annee 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

SEUIL = 120.0


def front(observe: np.ndarray, predit: np.ndarray) -> pd.DataFrame:
    """Précision et rappel pour toute la plage de seuils utiles."""
    vrai = observe >= SEUIL
    seuils = np.unique(np.quantile(predit, np.linspace(0.50, 0.9999, 500)))
    lignes = []
    for s in seuils:
        annonce = predit >= s
        n = int(annonce.sum())
        if n == 0:
            continue
        tp = int((annonce & vrai).sum())
        lignes.append({"seuil": float(s), "annonces": n, "justes": tp,
                       "fausses": n - tp, "precision": tp / n,
                       "rappel": tp / max(vrai.sum(), 1)})
    return pd.DataFrame(lignes)


def au_niveau(f: pd.DataFrame, colonne: str, cible: float) -> dict | None:
    """Point du front le plus proche d'un niveau donné, sans jamais passer en dessous."""
    admissibles = f[f[colonne] >= cible]
    if admissibles.empty:
        return None
    autre = "rappel" if colonne == "precision" else "precision"
    return admissibles.loc[admissibles[autre].idxmax()].to_dict()


def main(annee: int, polluant: str) -> int:
    if annee == 2025:
        d = pd.read_csv(RACINE / f"reports/reentrainement_glissant_{polluant}_2025_detail.csv")
        colonne_nous, libelle = "fige", "1ᵉʳ semestre 2025, Occitanie, hors échantillon"
    else:
        d = pd.read_csv(RACINE / f"reports/heatmap_annuelle_{polluant}.csv")
        colonne_nous, libelle = "nous", "2024, France, stations exclues"
    d = d.dropna(subset=["obs_jour", "officiel_mos", colonne_nous])
    observe = d["obs_jour"].to_numpy()
    vrai = observe >= SEUIL
    print(f"{polluant} · {libelle} · {len(d):,} jours-station · "
          f"{int(vrai.sum())} dépassements\n", flush=True)

    # Le produit officiel à son propre seuil réglementaire : c'est le point qu'il occupe
    # réellement, et donc celui auquel nous devons nous comparer.
    a_off = d["officiel_mos"].to_numpy() >= SEUIL
    tp_off = int((a_off & vrai).sum())
    p_off, r_off = tp_off / max(a_off.sum(), 1), tp_off / max(vrai.sum(), 1)
    print(f"{'produit':34s} {'seuil':>7s} {'annonces':>9s} {'justes':>7s} "
          f"{'fausses':>8s} {'précision':>10s} {'rappel':>8s}")
    print(f"{'MOS officiel (seuil réglementaire)':34s} {SEUIL:7.0f} {int(a_off.sum()):9d} "
          f"{tp_off:7d} {int(a_off.sum()) - tp_off:8d} {p_off:10.1%} {r_off:8.1%}")

    f = front(observe, d[colonne_nous].to_numpy())
    a_nous = d[colonne_nous].to_numpy() >= SEUIL
    tp_nous = int((a_nous & vrai).sum())
    print(f"{'nous (seuil réglementaire)':34s} {SEUIL:7.0f} {int(a_nous.sum()):9d} "
          f"{tp_nous:7d} {int(a_nous.sum()) - tp_nous:8d} "
          f"{tp_nous / max(a_nous.sum(), 1):10.1%} {tp_nous / max(vrai.sum(), 1):8.1%}")

    for nom, colonne, cible in (("nous, à précision égale", "precision", p_off),
                                ("nous, à rappel égal", "rappel", r_off)):
        point = au_niveau(f, colonne, cible)
        if point is None:
            print(f"{nom:34s} — niveau inatteignable")
            continue
        print(f"{nom:34s} {point['seuil']:7.1f} {int(point['annonces']):9d} "
              f"{int(point['justes']):7d} {int(point['fausses']):8d} "
              f"{point['precision']:10.1%} {point['rappel']:8.1%}")

    f.to_csv(RACINE / f"reports/front_precision_rappel_{polluant}_{annee}.csv", index=False)

    print(f"\n{'═' * 82}")
    egal = au_niveau(f, "precision", p_off)
    if egal:
        print(f"**À la précision du produit officiel ({p_off:.1%}), nous rappelons "
              f"{egal['rappel']:.1%} contre {r_off:.1%}** — soit "
              f"{egal['rappel'] / max(r_off, 1e-9):.1f}× plus de dépassements détectés à "
              f"qualité d'annonce identique.")
    egal_r = au_niveau(f, "rappel", r_off)
    if egal_r:
        print(f"À son rappel ({r_off:.1%}), notre précision est de {egal_r['precision']:.1%} "
              f"contre {p_off:.1%} — {int(egal_r['fausses'])} fausses alertes contre "
              f"{int(a_off.sum()) - tp_off}.")
    print(f"\nÉcrit : reports/front_precision_rappel_{polluant}_{annee}.csv", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--annee", type=int, default=2025)
    p.add_argument("--polluant", default="O3")
    args = p.parse_args()
    raise SystemExit(main(args.annee, args.polluant))
