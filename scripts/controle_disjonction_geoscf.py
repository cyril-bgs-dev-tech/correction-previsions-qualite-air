#!/usr/bin/env python3
"""Le gain de v2 tient-il **sans le mois que v1 partage avec lui** ?

Le défaut que ce script ferme
-------------------------------
L'argument tiré de la mesure par flux est une **réplication** : le même apport se retrouve
sur deux corpus construits à partir de deux produits différents. Cet argument suppose que
les deux corpus sont disjoints — et ils ne le sont pas tout à fait.

**Octobre 2025 a été extrait dans les deux flux**, exprès, pour mesurer leur écart. Il pèse
un huitième du corpus v2 et un vingt-neuvième de v1. Tant qu'il y figure, « réplication sur
un corpus disjoint » est une phrase légèrement fausse — le genre de réserve qu'on écrit en
note de bas de page au lieu de la lever, et que la règle 4 ter du projet interdit :

> Avant d'écrire « attention, cette comparaison est imparfaite », se demander : **est-ce que
> je peux la rendre équitable ?** Si oui, la réserve est une paresse déguisée en rigueur.

Ici, la rendre équitable coûte un filtre sur une colonne et deux minutes de calcul.

Ce qui est mesuré
-------------------
Le même protocole double aveugle, à graine identique, sur v2 **privé d'octobre 2025**. Si le
gain tient, la réplication porte sur des corpus strictement disjoints et la phrase se dit
sans réserve. S'il s'effondre, c'est que le mois de recouvrement portait le résultat — et il
fallait le savoir avant de l'écrire, pas après.

Usage  : python3 scripts/controle_disjonction_geoscf.py --polluant O3
Sortie : reports/controle_disjonction_geoscf.csv  (une ligne par polluant, en ajout)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from apport_geoscf import preparer  # noqa: E402
from double_aveugle_journalier import GRAINE  # noqa: E402
from stabilite_apport_geoscf import un_tirage  # noqa: E402

PARTAGE = "2025-10"          # le seul mois extrait dans les deux flux


def main(polluants: list[str], horizon: int, n_spa: int) -> int:
    depart, lignes = time.time(), []
    print(f"\n{'═' * 86}")
    print(f"CORPUS STRICTEMENT DISJOINTS — v2 privé de {PARTAGE}, le mois partagé avec v1")
    print(f"{'═' * 86}")
    print(f"  {'polluant':9s} {'mois':>5s} {'n avec':>9s} {'n sans':>9s} "
          f"{'gain avec':>10s} {'gain sans':>10s} {'écart':>8s}")

    for pol in polluants:
        d, colonnes, _ = preparer(pol, horizon, "v2")
        sans_cols = colonnes["base"] + colonnes["familles"]
        avec_cols = sans_cols + colonnes["geo"]
        mois = sorted(d["mois"].unique())
        if PARTAGE not in mois:
            # Nommer l'absence plutôt que de la traiter comme un succès (règle 2 bis) :
            # un filtre qui ne retire rien produirait deux fois le même chiffre et
            # « l'écart est nul » passerait pour une confirmation.
            print(f"  {pol:9s} — {PARTAGE} absent du corpus v2 préparé, rien à retirer")
            continue
        d_sans = d[d["mois"] != PARTAGE].reset_index(drop=True)
        r_avec = un_tirage(d, sans_cols, avec_cols, GRAINE, n_spa)
        r_sans = un_tirage(d_sans, sans_cols, avec_cols, GRAINE, n_spa)
        ecart = r_sans["gain_pct"] - r_avec["gain_pct"]
        print(f"  {pol:9s} {len(mois):>5d} {r_avec['n']:>9,} {r_sans['n']:>9,} "
              f"{r_avec['gain_pct']:+9.2f}% {r_sans['gain_pct']:+9.2f}% "
              f"{ecart:+7.2f}", flush=True)
        lignes.append({"polluant": pol, "horizon": horizon, "n_mois_v2": len(mois),
                       "mois_retire": PARTAGE, "n_avec": r_avec["n"],
                       "n_sans": r_sans["n"], "gain_avec_pct": r_avec["gain_pct"],
                       "gain_sans_pct": r_sans["gain_pct"], "ecart_pt": ecart})

    if not lignes:
        raise SystemExit("aucun polluant mesuré — rien écrit")
    t = pd.DataFrame(lignes)
    for c in ("gain_avec_pct", "gain_sans_pct", "ecart_pt"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")
    tous_positifs = bool((t["gain_sans_pct"] > 0).all())
    print(f"\n  gain sans le mois partagé : positif sur "
          f"{int((t['gain_sans_pct'] > 0).sum())}/{len(t)} polluants · "
          f"écart médian {t['ecart_pt'].median():+.2f} pt")
    if tous_positifs:
        print(f"  → La réplication porte sur des corpus **strictement disjoints**.")
    else:
        print(f"  → Le mois partagé portait le résultat : ne pas parler de réplication.")

    f = RACINE / "reports/controle_disjonction_geoscf.csv"
    t.to_csv(f, index=False)
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3,NO2,PM25,PM10")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main([p.strip() for p in n.polluant.split(",") if p.strip()],
                          n.horizon, n.plis_spatiaux))
