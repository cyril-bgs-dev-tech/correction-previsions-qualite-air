#!/usr/bin/env python3
"""Le gain plus faible de v2 vient-il du **produit** ou de la **famine de données** ?

Le fait à expliquer
---------------------
Mesuré le 05/08, l'apport de GEOS-CF vaut sur les deux flux :

| polluant | v1 — 29 mois | v2 — 8 mois | rapport |
|---|---|---|---|
| O₃   | +2,69 % | +1,68 % | 0,62 |
| NO₂  | +2,93 % | +1,37 % | 0,47 |
| PM2,5| +1,14 % | +0,59 % | 0,52 |

Le signe tient 7 fois sur 7 — mais **v2 rend systématiquement la moitié de v1**, et le rapport
est trop régulier pour être du bruit. Deux lectures s'opposent, et elles n'ont pas les mêmes
conséquences :

* **le produit** — v2 apporterait réellement moins d'information que v1 ; alors le chiffre à
  publier pour l'avenir est celui de v2, puisque v1 est retiré depuis le 2 janvier 2026 ;
* **la famine** — v2 a **quatre fois moins de lignes**, et une famille de colonnes ajoutée
  aide d'autant moins que le modèle a peu d'exemples pour l'exploiter ; alors le gain de v2
  remontera de lui-même à mesure que son corpus s'allonge, et c'est v1 qui donne la valeur
  asymptotique.

Conclure sans trancher reviendrait à publier une baisse dont on ignore si elle est une
propriété du produit ou un artefact du protocole.

Le contrôle
-------------
Restreindre **v1** aux mêmes mois calendaires que v2 — janvier à juillet plus octobre — sur
une année où v1 existe. Le corpus a alors la même taille et la même saisonnalité que v2 ; il
ne reste qu'une différence, le flux. Si le gain de v1 ainsi amputé tombe au niveau de v2,
c'est la famine ; s'il reste haut, c'est le produit.

⚠️ Choisir les mois **au calendrier** et non au hasard. Huit mois tirés uniformément dans
29 mélangeraient l'effet de taille à un effet de saison — et l'ozone, dont l'apport est le
plus fort, est précisément la grandeur la plus saisonnière du jeu.

Usage  : python3 scripts/controle_taille_geoscf.py --polluant O3
Sortie : reports/controle_taille_geoscf_<polluant>.csv
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

from apport_geoscf import preparer  # noqa: E402
from double_aveugle_journalier import GRAINE  # noqa: E402
from stabilite_apport_geoscf import un_tirage  # noqa: E402


def mois_de(version: str, polluant: str, horizon: int) -> tuple[pd.DataFrame, dict, list[str]]:
    d, colonnes, _ = preparer(polluant, horizon, version)
    return d, colonnes, sorted(d["mois"].unique())


def main(polluant: str, horizon: int, n_spa: int, n_tirages: int) -> int:
    depart = time.time()

    # 1. Ce que v2 couvre réellement — lu dans les données, jamais déduit des noms de
    #    fichiers (règle 4 bis). C'est ce calendrier-là que v1 devra imiter.
    d2, col2, mois_v2 = mois_de("v2", polluant, horizon)
    cal_v2 = sorted({m[5:] for m in mois_v2})
    print(f"\n  v2 couvre {len(mois_v2)} mois : {', '.join(mois_v2)}")
    print(f"  mois calendaires à imiter : {', '.join(cal_v2)}")

    d1, col1, mois_v1 = mois_de("v1", polluant, horizon)
    print(f"  v1 couvre {len(mois_v1)} mois : {mois_v1[0]} → {mois_v1[-1]}")

    sans1 = col1["base"] + col1["familles"]
    sans2 = col2["base"] + col2["familles"]

    # 2. Les années de v1 où le calendrier de v2 est **complet**. Une année amputée
    #    donnerait un corpus plus petit que v2 et fausserait la comparaison dans l'autre
    #    sens : on nomme les mois attendus un par un et on exige leur présence (règle 4).
    annees = []
    for an in sorted({m[:4] for m in mois_v1}):
        vises = [f"{an}-{c}" for c in cal_v2]
        manquants = [m for m in vises if m not in mois_v1]
        if manquants:
            print(f"  {an} : écarté — mois absents de v1 {manquants}")
        else:
            annees.append((an, vises))
    if not annees:
        raise SystemExit("aucune année de v1 ne reproduit le calendrier de v2")

    lignes = []
    print(f"\n{'═' * 88}")
    print(f"CONTRÔLE DE TAILLE — {polluant} · même graine, même protocole, corpus variables")
    print(f"{'═' * 88}")
    print(f"  {'corpus':34s} {'mois':>5s} {'lignes':>9s} {'gain':>8s}")

    essais = [("v1 entier (référence)", d1, sans1, col1["geo"], mois_v1),
              ("v2 entier", d2, sans2, col2["geo"], mois_v2)]
    for an, vises in annees:
        essais.append((f"v1 réduit au calendrier de v2 · {an}", d1, sans1, col1["geo"], vises))

    # ⚠️ Deux années calendaires ne font pas une distribution. Mesuré le 05/08 sur l'ozone,
    # elles ont rendu **−0,02 %** et **+3,76 %** — un écart de 3,8 points là où le balayage
    # de partitions annonçait σ = 0,20 pt sur le corpus entier.
    #
    # Le balayage de partitions ne pouvait PAS voir cet écart : il fait varier *quelles
    # stations* tombent dans quel pli, en gardant *quels mois* fixes. La composition en mois
    # est une seconde source de variance, et sur un corpus court elle domine d'un ordre de
    # grandeur. Conclure « stable » depuis le seul balayage de partitions, c'est mesurer la
    # dispersion d'un axe et l'attribuer aux deux.
    #
    # D'où ces tirages : mêmes 9 mois en nombre, choisis au hasard dans v1, pour obtenir la
    # **distribution d'échantillonnage du gain à cette taille de corpus**. C'est elle qui dit
    # si le chiffre de v2 est mesurable ou seulement affichable.
    rng = np.random.default_rng(GRAINE)
    k = len(mois_v2)
    for i in range(n_tirages):
        pris = sorted(rng.choice(mois_v1, size=min(k, len(mois_v1)), replace=False))
        essais.append((f"v1 · {k} mois au hasard #{i + 1}", d1, sans1, col1["geo"], pris))

    for nom, d, sans, geo, mois in essais:
        sub = d[d["mois"].isin(mois)].reset_index(drop=True)
        if len(sub) < 5_000:
            print(f"  {nom:34s} {len(mois):>5d} {len(sub):>9,}   écarté, trop peu de lignes")
            continue
        r = un_tirage(sub, sans, sans + geo, GRAINE, n_spa)
        print(f"  {nom:34s} {len(mois):>5d} {len(sub):>9,} {r['gain_pct']:+7.2f}%", flush=True)
        lignes.append({"polluant": polluant, "horizon": horizon, "corpus": nom,
                       "n_mois": len(mois), "n_lignes_corpus": len(sub),
                       "n_predictions": r["n"], "plancher_sans": r["plancher_sans"],
                       "plancher_avec": r["plancher_avec"], "gain_pct": r["gain_pct"]})

    # La table se construit après le dernier tirage (règle 2 ter).
    t = pd.DataFrame(lignes)
    for c in ("corpus", "gain_pct", "n_mois"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")

    ref = t[t["corpus"].str.startswith("v1 entier")]["gain_pct"]
    v2 = t[t["corpus"].str.startswith("v2 entier")]["gain_pct"]
    court = t[t["corpus"].str.contains("réduit|au hasard")]["gain_pct"]
    if len(ref) and len(v2) and len(court) >= 3:
        g1, g2 = float(ref.iloc[0]), float(v2.iloc[0])
        c = court.to_numpy()
        print(f"\n  v1 entier ({len(d1):,} lignes) : {g1:+.2f} %")
        print(f"  v1 réduit à {len(mois_v2)} mois, {len(c)} corpus : médiane {np.median(c):+.2f} % · "
              f"étendue {c.min():+.2f} → {c.max():+.2f} · σ {c.std(ddof=1):.2f} pt")
        print(f"  v2 entier ({len(d2):,} lignes) : {g2:+.2f} %")
        # ⚠️ Le verdict ne se lit PAS sur la seule médiane : c'est l'étendue qui dit si le
        # chiffre de v2 est mesurable. Un corpus court dont le gain balaie plusieurs points
        # ne mesure rien, quelle que soit la valeur qu'il affiche une fois.
        if c.min() <= 0 <= c.max():
            print(f"\n  → NON MESURABLE À CETTE TAILLE. Sur {len(mois_v2)} mois, le même flux v1")
            print(f"    rend de {c.min():+.2f} % à {c.max():+.2f} % selon les mois retenus — il")
            print(f"    change de signe. Le chiffre de v2 ({g2:+.2f} %) est compatible avec cette")
            print(f"    dispersion : il ne se publie pas comme une valeur, seulement comme un")
            print(f"    signe cohérent. La valeur qui se publie est celle de v1 entier.")
        elif abs(np.median(c) - g2) < abs(np.median(c) - g1):
            print(f"\n  → FAMINE : v1 amputé tombe près de v2, sans changer de signe. La baisse")
            print(f"    est un effet de taille de corpus, pas une propriété du flux v2.")
        else:
            print(f"\n  → PRODUIT : v1 amputé reste près de v1 entier. v2 apporte réellement")
            print(f"    moins, et c'est son chiffre qui vaut pour l'avenir.")

    f = RACINE / f"reports/controle_taille_geoscf_{polluant}.csv"
    t.to_csv(f, index=False)
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--tirages", type=int, default=6,
                   help="corpus courts tirés au hasard dans v1, pour la distribution")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux, n.tirages))
