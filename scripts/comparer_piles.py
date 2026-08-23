#!/usr/bin/env python3
"""Deux piles, mêmes plis : l'écart apparié et ce qu'on a le droit d'en dire.

Pourquoi cet outil plutôt qu'une soustraction de gains
-------------------------------------------------------
Le dossier compare des variantes de pile — spéciation `core7`, précurseurs réduits aux
moyennes, fenêtre complète — à la pile de référence. La tentation est de soustraire les
deux `gain_pct` publiés. C'est faux pour une raison mesurée le 23/08/2026 :

    à données identiques, un pli bouge d'au plus 0,039 pt
    avec 0,14 % de données en plus, jusqu'à 2,56 pt par pli et +0,23 en agrégé

Le gradient boosting n'est pas stable au sens de Lipschitz. **Une différence de gains
publiés mélange donc l'effet de la variante et l'instabilité du modèle**, et rien ne les
sépare. L'écart APPARIÉ pli à pli, lui, soustrait le déplacement commun : les deux piles
partagent leurs plis, leur graine et leur découpage.

Ce que le script refuse de faire
---------------------------------
* conclure si les deux fenêtres diffèrent — un écart entre deux fenêtres n'est pas un
  écart, c'est deux mesures ;
* conclure si l'IC95 contient zéro — il dit alors « non résolu », qui est une information
  et non un échec ;
* nommer une structure sous la résolution.

Usage  : python3 scripts/comparer_piles.py --variante _spe-core7 [--polluants NO2,O3]
Sortie : reports/comparaison_piles<variante>.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))
from verdict_apports import bootstrap_blocs, permutation_blocs  # noqa: E402

MAX = "★ MAXIMALE — PARTOUT"
STATIONS = "★ MAXIMALE — AUX STATIONS (+ veille)"
BLOC = 3


def serie(chemin: Path, config: str) -> pd.DataFrame:
    t = pd.read_csv(chemin)
    s = t[t["configuration"] == config]
    if s.empty:
        raise SystemExit(f"{chemin.name} : configuration « {config} » absente")
    return s.set_index("mois")[["gain_pct", "n_test"]]


def main(variante: str, horizon: int, polluants: str) -> int:
    lignes = []
    print(f"COMPARAISON APPARIÉE · variante « {variante} » · blocs de {BLOC} mois")
    print("═" * 96)
    for p in [x.strip() for x in polluants.split(",") if x.strip()]:
        ref = RACINE / f"reports/methode_maximale_{p}_h{horizon}.csv"
        var = RACINE / f"reports/methode_maximale_{p}_h{horizon}{variante}.csv"
        if not var.exists():
            print(f"  {p:5s} ✘ absent : {var.name}")
            continue
        ta, tb = pd.read_csv(ref), pd.read_csv(var)
        fa = str(ta["fenetre"].iloc[0]), int(ta["n_mois"].iloc[0])
        fb = str(tb["fenetre"].iloc[0]), int(tb["n_mois"].iloc[0])
        # L'empreinte des entrées prime sur toute autre vérification : elle voit un
        # remplissage que ni la fenêtre, ni le nombre de colonnes, ni `n_test` ne montrent.
        ea = str(ta["empreinte_entrees"].iloc[0]) if "empreinte_entrees" in ta else ""
        eb = str(tb["empreinte_entrees"].iloc[0]) if "empreinte_entrees" in tb else ""
        if ea and eb and ea != eb:
            print(f"  {p:5s} 🔴 ENTRÉES DIFFÉRENTES — empreintes {ea} ≠ {eb}. Les deux "
                  f"piles ne reposent pas sur les mêmes données. Régénérer la variante.")
            lignes.append({"variante": variante, "polluant": p,
                           "verdict": "entrées différentes",
                           "empreinte_reference": ea, "empreinte_variante": eb})
            continue
        if not (ea and eb):
            print(f"  {p:5s} ⚠️ empreinte absente d'un côté ({ea or '—'} / {eb or '—'}) : "
                  f"fichier antérieur au 24/08. L'identité des entrées n'est PAS vérifiée.")
        if fa != fb:
            print(f"  {p:5s} 🔴 FENÊTRES DIFFÉRENTES — référence {fa[0]} ({fa[1]} mois) "
                  f"contre variante {fb[0]} ({fb[1]}). Deux mesures, pas un écart.")
            lignes.append({"variante": variante, "polluant": p, "verdict": "fenêtres différentes",
                           "fenetre_reference": fa[0], "fenetre_variante": fb[0]})
            continue
        for nom, config in (("PARTOUT", MAX), ("AUX STATIONS", STATIONS)):
            pa = Path(str(ref).replace(".csv", "_par_pli.csv"))
            pb = Path(str(var).replace(".csv", "_par_pli.csv"))
            if not (pa.exists() and pb.exists()):
                continue
            try:
                sa, sb = serie(pa, config), serie(pb, config)
            except SystemExit:
                continue
            paire = sa.join(sb, lsuffix="_ref", rsuffix="_var").dropna()
            # 🔴 Le garde de DENSITÉ, et le trou qu'il ferme — 24/08/2026.
            #
            # Le contrôle de fenêtre compare deux chaînes. Il ne voit donc RIEN quand les
            # deux piles couvrent les mêmes mois mais pas les mêmes jours : c'est ce qui
            # s'est produit ce soir, la spéciation complétée ayant ajouté 2024-01-01 à une
            # fenêtre par ailleurs inchangée. La première comparaison lancée avec cet outil
            # opposait une référence de 21 h 59 à une variante de 16 h 23 — deux corpus,
            # et le verdict tombait sans un mot.
            #
            # `n_test` par pli est le signal qui manquait : deux piles construites sur le
            # même corpus ont exactement les mêmes lignes de test à chaque pli.
            diff = paire[paire["n_test_ref"] != paire["n_test_var"]]
            if not diff.empty:
                print(f"  {p:5s} {nom:13s} 🔴 CORPUS DIFFÉRENTS — {len(diff)} pli(s) "
                      f"n'ont pas le même nombre de lignes de test "
                      f"({', '.join(f'{m} {int(r.n_test_ref)}≠{int(r.n_test_var)}' for m, r in diff.head(3).iterrows())}"
                      f"{' …' if len(diff) > 3 else ''}). Régénérer la variante.")
                lignes.append({"variante": variante, "polluant": p, "perimetre": nom,
                               "verdict": "corpus différents", "n_plis_divergents": len(diff)})
                continue
            # Le signe est celui de la VARIANTE : positif, elle fait mieux.
            ecart = list((paire["gain_pct_var"] - paire["gain_pct_ref"]).to_numpy())
            if len(ecart) < 6:
                continue
            moy, bas, haut, _, _ = bootstrap_blocs(ecart, BLOC)
            p_plus, p_moins = permutation_blocs(ecart, BLOC)
            resolu = not (bas <= 0.0 <= haut)
            verdict = ("✅ la variante fait MIEUX" if resolu and moy > 0 else
                       "🔴 la variante fait MOINS BIEN" if resolu else
                       "⬜ non résolu — l'IC contient zéro")
            print(f"  {p:5s} {nom:13s} {moy:+7.3f} pt · IC95 [{bas:+6.3f} ; {haut:+6.3f}] · "
                  f"p⁺={p_plus:.4f} · {len(ecart)} plis · {verdict}")
            lignes.append({"variante": variante, "polluant": p, "perimetre": nom,
                           "fenetre": fa[0], "n_mois": fa[1], "n_plis": len(ecart),
                           "ecart_apparie_pt": moy, "ic95_bas": bas, "ic95_haut": haut,
                           "p_permutation_positif": p_plus,
                           "p_permutation_negatif": p_moins,
                           "resolu": bool(resolu), "verdict": verdict})
    if not lignes:
        print("  aucune comparaison possible — variantes absentes ?")
        return 1
    t = pd.DataFrame(lignes)
    for c in ("variante", "polluant", "verdict"):
        if c not in t:
            raise SystemExit(f"colonne absente du rapport : {c}")
    sortie = RACINE / f"reports/comparaison_piles{variante}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--variante", required=True,
                   help="suffixe du fichier de variante, ex. _spe-core7 ou _pre-moyennes")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--polluants", default="NO2,O3,PM10,PM25")
    sys.exit(main(**vars(a.parse_args())))
