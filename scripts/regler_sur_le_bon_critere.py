#!/usr/bin/env python3
"""Régler sur la RMSE a désigné le pire système opérationnel — de combien, et où.

Le contre-exemple qui a produit ce script
-------------------------------------------
`decomposition_information.py`, 03/08, sur l'ozone :

| krigeage | RMSE | épisodes attrapés (2 201 alertes) |
|---|---|---|
| réglages **usuels** (7 j · 50 km · p=2) | 14,64 | **1 259** |
| réglages **« optimisés »** ici (30 j · 200 km · p=1 · typo) | **14,10** | 1 175 |

La RMSE désigne le second, l'astreinte a besoin du premier. Nous avons réglé la méthode
concurrente contre la mauvaise cible et produit un système **mesurablement pire pour
l'usage**, en croyant l'améliorer.

Tout ce projet sélectionne par la RMSE — variables, configurations, réglages du krigeage.
Ce script mesure ce que cette habitude coûte, sur la seule grille où l'on peut le faire
sans réajuster quoi que ce soit.

Les trois critères mis en concurrence
---------------------------------------
1. **RMSE** — l'habitude. Confond information et calage.
2. **Plancher** `σy·√(1−r²)` — la RMSE débarrassée de ses deux paramètres libres. Compare
   les variantes sur ce qu'elles **savent**, pas sur ce qu'elles ont **réglé**.
3. **Épisodes attrapés à volume d'alertes constant** — le critère opérationnel. Invariant
   par toute transformation monotone, donc insensible au calage par construction.

Ce que ce script établit, et ce qu'il n'établit pas
-----------------------------------------------------
Il établit un **désaccord de classement** et son coût en épisodes. Il n'établit pas qu'un
critère est « le bon » : cela dépend de l'usage, et c'est justement la décision qu'il faut
prendre explicitement au lieu de la laisser à un défaut d'implémentation.

⚠️ Aucun apprentissage ici : uniquement du krigeage (numpy). Le script est donc léger et
peut tourner à côté d'un lot LightGBM sans le concurrencer.

Usage  : python3 scripts/regler_sur_le_bon_critere.py --polluant O3 --horizon 2
Sortie : reports/regler_sur_le_bon_critere_<polluant>_h<n>.csv
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

from double_aveugle_journalier import (  # noqa: E402
    GRANDEUR_PAR_POLLUANT, agreger_journalier, charger, colonnes_admises,
)
from krigeage_du_biais import biais_interpole, matrice_distances  # noqa: E402
from tableau_comparatif import NOM_POLLUANT, classe  # noqa: E402

DECALAGE = 2
FENETRES = (3, 7, 14, 30, 60)
RAYONS = (25.0, 50.0, 100.0, 200.0, 400.0)
PUISSANCES = (1.0, 2.0)


def main(polluant: str, horizon: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, cols, GRANDEUR_PAR_POLLUANT[polluant])
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    ids = np.sort(d["station_id"].unique())

    dist, st = matrice_distances(ids)
    t = st["type_station"].fillna("?").to_numpy()
    memes = (t[:, None] == t[None, :]).astype(float)
    ancre = d["cams_jour"].to_numpy()
    d["_b"] = d["valeur"].to_numpy() - ancre
    piv = d.pivot_table(index="jour", columns="station_id", values="_b",
                        aggfunc="mean").reindex(columns=ids)
    piv = piv.reindex(pd.date_range(piv.index.min(), piv.index.max(), freq="D"))
    lig = pd.Index(piv.index).get_indexer(pd.DatetimeIndex(d["jour"]))
    col = d["station_id"].map({s: i for i, s in enumerate(ids)}).to_numpy()

    y = d["valeur"].to_numpy()
    crit = classe(y, polluant) >= 3
    n_crit = int(crit.sum())
    sy = float(y.std())
    ech = "J0" if horizon == 1 else f"J+{horizon - 1}"
    print(f"{NOM_POLLUANT[polluant]} · {ech} · {len(d):,} jours-station · "
          f"{n_crit:,} situations critiques · "
          f"{len(FENETRES) * len(RAYONS) * len(PUISSANCES) * 2} variantes de krigeage",
          flush=True)

    # Le budget d'alertes de référence : celui qu'émet le réglage usuel, mesuré.
    roul_u = piv.shift(DECALAGE).rolling(7, min_periods=2).mean()
    c_u = biais_interpole(roul_u, dist, 0, 50.0, 2.0, None)[lig, col]
    x_u = np.where(np.isfinite(c_u), ancre + c_u, ancre)
    budget = int((classe(x_u, polluant) >= 3).sum())
    print(f"  budget d'alertes de référence : {budget:,} "
          f"(ce qu'émet le réglage usuel 7 j · 50 km · p=2)\n", flush=True)

    lignes = []
    roulantes = {f: piv.shift(DECALAGE).rolling(f, min_periods=max(2, f // 3)).mean()
                 for f in FENETRES}
    for f in FENETRES:
        for rayon in RAYONS:
            for p in PUISSANCES:
                for ty, nom_ty in ((None, "tous"), (memes, "même typo")):
                    c = biais_interpole(roulantes[f], dist, 0, rayon, p, ty)[lig, col]
                    x = np.where(np.isfinite(c), ancre + c, ancre)
                    r = float(np.corrcoef(y, x)[0, 1])
                    rm = float(np.sqrt(np.mean((x - y) ** 2)))
                    vues = int(crit[np.argsort(-x, kind="stable")[:budget]].sum())
                    lignes.append({
                        "polluant": polluant, "horizon": horizon, "fenetre_j": f,
                        "rayon_km": rayon, "puissance": p, "donneurs": nom_ty,
                        "rmse": rm, "r": r,
                        "plancher": sy * np.sqrt(max(1 - r ** 2, 0.0)),
                        "episodes_budget_constant": vues,
                        "couverture_pct": 100 * float(np.isfinite(c).mean())})
        print(f"  fenêtre {f:2d} j · {(time.time() - depart) / 60:4.1f} min", flush=True)

    m = pd.DataFrame(lignes)
    m["nom"] = (m["fenetre_j"].astype(str) + " j · " + m["rayon_km"].astype(int).astype(str)
                + " km · p=" + m["puissance"].astype(int).astype(str) + " · " + m["donneurs"])

    def montre(titre: str, cle: str, croissant: bool) -> pd.Series:
        best = m.sort_values(cle, ascending=croissant).iloc[0]
        print(f"\n  ── choisi par {titre} : {best['nom']}")
        print(f"     RMSE {best['rmse']:7.3f} · plancher {best['plancher']:7.3f} · "
              f"épisodes {int(best['episodes_budget_constant']):5d} / {n_crit}")
        return best

    print(f"{'═' * 92}\nLE CLASSEMENT DÉPEND DU CRITÈRE\n{'═' * 92}")
    b_rmse = montre("la RMSE (l'habitude)", "rmse", True)
    b_plan = montre("le plancher d'information", "plancher", True)
    b_ope = montre("les épisodes à budget constant", "episodes_budget_constant", False)

    perte = int(b_ope["episodes_budget_constant"] - b_rmse["episodes_budget_constant"])
    ecart_rmse = 100 * (b_ope["rmse"] / b_rmse["rmse"] - 1)
    print(f"\n{'═' * 92}\nCE QUE COÛTE LE RÉGLAGE PAR LA RMSE\n{'═' * 92}")
    if perte > 0:
        print(f"  Le réglage choisi par la RMSE attrape **{perte} épisodes de moins** que")
        print(f"  celui choisi par le critère opérationnel — à volume d'alertes identique,")
        print(f"  soit {100 * perte / max(int(b_rmse['episodes_budget_constant']), 1):.1f} % "
              f"de manqués en plus.")
        print(f"  Le prix à payer dans l'autre sens : {ecart_rmse:+.2f} % de RMSE.")
    elif perte == 0:
        print(f"  Les deux critères désignent le même nombre d'épisodes. Pas d'arbitrage")
        print(f"  ici — mais ce n'est pas une garantie générale, cf. l'ozone.")
    else:
        print(f"  Le réglage RMSE attrape {-perte} épisodes de PLUS. Les deux critères")
        print(f"  s'accordent sur ce polluant.")
    accord = (b_rmse["nom"] == b_ope["nom"])
    print(f"\n  Les deux critères désignent {'LE MÊME' if accord else 'DES'} réglage"
          f"{'' if accord else 's DIFFÉRENTS'}.")
    print(f"  Le plancher désigne « {b_plan['nom']} » — c'est le classement par")
    print(f"  l'information seule, indépendant de tout calage.")

    sortie = RACINE / f"reports/regler_sur_le_bon_critere_{polluant}_h{horizon}.csv"
    m.drop(columns=["nom"]).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=2)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon))
