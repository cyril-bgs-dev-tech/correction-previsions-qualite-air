#!/usr/bin/env python3
"""A09 — quelle taille d'effet ce protocole peut-il DÉTECTER, et à quel nombre de blocs ?

Le défaut que ce script existe pour supprimer — mesuré le 23/08/2026
---------------------------------------------------------------------
J'ai déclaré une famille « instable » parce que son verdict changeait avec la longueur de
bloc. C'était faux, et la raison est arithmétique : **à neuf blocs, le p le plus petit
qu'un test de signe puisse rendre vaut 0,0039** — 0,0117 après conjonction partielle sur
quatre polluants. Aucun effet modeste ne peut y être déclaré significatif, quel qu'il soit.
Exiger la significativité à cette longueur revient donc à exiger qu'un effet survive à un
handicap que l'analyse de sensibilité fabrique elle-même.

> **Un seuil de décision qui ignore la puissance de son propre test rejette des effets
> réels et appelle cela de la rigueur.**

Ce que ce script rend
-----------------------
Pour chaque nombre de blocs réellement disponible, deux chiffres qu'aucune décision ne
devrait ignorer :

* le **plancher de p** — la plus petite valeur atteignable, obtenue quand *tous* les blocs
  vont dans le même sens. Si ce plancher dépasse 0,05, la longueur de bloc ne peut rien
  conclure et il faut le dire avant de mesurer, pas après ;
* la **puissance** — la probabilité de détecter un effet dont une part `q` des blocs est
  positive. `q` se lit sur les familles déjà mesurées : la forme du profil donne 0,83 à
  0,92 selon le polluant, les précurseurs 0,70 à 1,00.

La puissance est calculée exactement, sans simulation : sous l'hypothèse que chaque bloc
est positif avec probabilité `q` indépendamment, le compte suit une binomiale, et le test
de signe rejette au-delà d'un seuil qui se calcule.

Usage : python3 scripts/puissance_blocs.py [--polluants 4] [--alpha 0.05]
Sortie : reports/puissance_blocs.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))


def plancher_p(n: int) -> float:
    """Le plus petit `p` qu'un test de signe bilatéral puisse rendre à `n` blocs."""
    return float(stats.binomtest(n, n, 0.5).pvalue)


def seuil_rejet(n: int, alpha: float) -> int | None:
    """Nombre minimal de blocs positifs pour rejeter au seuil `alpha`. None si inatteignable."""
    for k in range(n // 2 + 1, n + 1):
        if stats.binomtest(k, n, 0.5).pvalue <= alpha:
            return k
    return None


def puissance(n: int, q: float, alpha: float) -> float:
    """Probabilité de rejeter quand chaque bloc est positif avec probabilité `q`."""
    k = seuil_rejet(n, alpha)
    if k is None:
        return 0.0
    return float(1.0 - stats.binom.cdf(k - 1, n, q))


def main(n_polluants: int, alpha: float) -> int:
    # Le seuil effectif par polluant, une fois la conjonction partielle appliquée : la
    # forme de Bonferroni multiplie le p du r-ième groupe par (n − r + 1). Exiger p_PC < α
    # revient donc à exiger, du groupe le moins bon des r porteurs, un p sous α/(n−r+1).
    r = 2
    facteur = n_polluants - r + 1
    alpha_eff = alpha / facteur
    print(f"Conjonction partielle r={r} sur {n_polluants} polluants : "
          f"p_PC = {facteur} × p_({r})")
    print(f"→ chaque porteur doit atteindre p ≤ {alpha:.3f}/{facteur} = {alpha_eff:.4f}\n")

    lignes = []
    print(f"{'blocs':>6s} {'plancher p':>11s} {'p_PC plancher':>14s} {'k requis':>9s} "
          f"{'puissance q=0,75':>17s} {'q=0,85':>8s} {'q=0,95':>8s}")
    for n in range(6, 21):
        pl = plancher_p(n)
        k = seuil_rejet(n, alpha_eff)
        p75, p85, p95 = (puissance(n, q, alpha_eff) for q in (0.75, 0.85, 0.95))
        marque = "" if k is not None else "   ← AUCUN verdict possible"
        print(f"{n:6d} {pl:11.4f} {min(1.0, facteur*pl):14.4f} "
              f"{'—' if k is None else k:>9} {p75:16.0%} {p85:7.0%} {p95:7.0%}{marque}")
        lignes.append({"n_blocs": n, "plancher_p": pl,
                       "plancher_p_conjonction": min(1.0, facteur * pl),
                       "k_requis": k, "alpha_effectif": alpha_eff,
                       "puissance_q075": p75, "puissance_q085": p85,
                       "puissance_q095": p95, "n_polluants": n_polluants})

    t = pd.DataFrame(lignes)
    # Les deux nombres qui décident, imprimés en clair plutôt que laissés à lire dans la table.
    utilisables = t[t["k_requis"].notna()]
    n_min = int(utilisables["n_blocs"].min()) if len(utilisables) else None
    n_80 = t[t["puissance_q085"] >= 0.80]
    print(f"\n  ⚠️  Sous {n_min} blocs, AUCUNE configuration ne peut être déclarée porteuse : "
          f"le plancher de p dépasse déjà le seuil effectif.")
    if len(n_80):
        print(f"  → il faut au moins {int(n_80['n_blocs'].min())} blocs pour avoir 80 % de "
              f"chances de détecter un effet dont 85 % des blocs sont positifs.")
    else:
        print(f"  → 80 % de puissance n'est atteinte à aucun nombre de blocs testé.")

    print(f"\n  Ce que le corpus offre aujourd'hui, en blocs de 3 mois :")
    for p_, n_plis in (("NO2", 37), ("O3", 37), ("PM10", 32), ("PM25", 37)):
        nb = n_plis // 3
        k = seuil_rejet(nb, alpha_eff)
        print(f"    {p_:5s} {n_plis} plis → {nb} blocs · k requis "
              f"{'—' if k is None else k}/{nb} · puissance à q=0,85 : "
              f"{puissance(nb, 0.85, alpha_eff):.0%}")

    from aq.rapport import ecrire_rapport  # noqa: PLC0415
    ecrire_rapport(t, RACINE / "reports/puissance_blocs.csv",
                   contexte={"axe": "double"},
                   attendues=["n_blocs", "plancher_p", "puissance_q085"])
    print(f"\nÉcrit : reports/puissance_blocs.csv")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluants", type=int, default=4)
    a.add_argument("--alpha", type=float, default=0.05)
    n = a.parse_args()
    raise SystemExit(main(n.polluants, n.alpha))
