#!/usr/bin/env python3
"""La plus petite différence que ce protocole sait RÉSOUDRE — action A04.

Pourquoi ce script existe
--------------------------
Le dépôt publie des gains à trois décimales. Rien ne dit à partir de quelle amplitude un
gain cesse d'être discernable du bruit du protocole, et c'est la question qui décide
**avant** de lire un chiffre : un « +0,3 % » n'est pas un petit résultat, c'est un
non-résultat si la résolution vaut ±0,5 %.

Ce que le script mesure — et ce qu'il ne mesure pas
----------------------------------------------------
La demi-largeur de l'IC95 bootstrap sur l'écart apparié **est** la résolution : deux
configurations dont les moyennes diffèrent de moins que cela ne sont pas séparées par ce
plan d'expérience. Le script l'agrège par polluant sur toutes les configurations déjà
mesurées, et rend la **médiane** — pas le minimum, qui serait la configuration la plus
chanceuse, ni la moyenne, qu'une queue tirerait.

⚠️ Ce n'est PAS un seuil de pertinence opérationnelle. Un gain résolu peut rester sans
valeur métier, et un gain non résolu peut être réel — il est seulement invisible ici.
La résolution borne ce que le protocole PEUT dire, pas ce qui MÉRITE d'être dit.

⚠️ Et elle dépend du nombre de blocs, donc de la fenêtre du polluant : PM10 n'a que
32 mois de spéciation contre 36 aux autres, et sa résolution s'en ressent. Le script
imprime `n_blocs` à côté de chaque chiffre pour que la comparaison entre polluants ne se
fasse jamais à l'aveugle.
"""

import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "reports" / "plus_petite_difference.csv"


def main(axe: str = "double") -> int:
    fichiers = sorted((RACINE / "reports").glob(f"verdict_*_{axe}.csv"))
    if not fichiers:
        print(f"❌ aucun verdict_*_{axe}.csv — lancer verdict_apports.py d'abord")
        return 1
    t = pd.concat([pd.read_csv(f) for f in fichiers], ignore_index=True)
    # Une configuration mesurée deux fois (deux préfixes) ne compte qu'une : sinon la
    # médiane suivrait le nombre de fichiers plutôt que le nombre de mesures.
    t = t.drop_duplicates(subset=["configuration", "polluant"])
    t["demi_ic95"] = (t["ic95_haut"] - t["ic95_bas"]) / 2.0

    manque = [c for c in ("demi_ic95", "n_blocs_3mois", "polluant") if c not in t]
    if manque:
        raise SystemExit(f"colonnes absentes des verdicts : {manque}")

    print(f"RÉSOLUTION DU PROTOCOLE · axe {axe} · {len(fichiers)} fichier(s) de verdict · "
          f"{t['configuration'].nunique()} configurations")
    print("═" * 88)
    print(f"{'polluant':8s} {'n_blocs':>8s} {'n_conf':>7s} "
          f"{'résolution':>12s} {'min':>8s} {'max':>8s}   plus petit gain mesuré")
    lignes = []
    for p, g in t.groupby("polluant"):
        res = float(g["demi_ic95"].median())
        # Le plus petit écart POSITIF déjà mesuré : s'il est sous la résolution, il a été
        # lu comme un résultat alors que le protocole ne le distingue pas de zéro.
        positifs = g.loc[g["ecart_apparie_moyen_pct"] > 0, "ecart_apparie_moyen_pct"]
        petit = float(positifs.min()) if len(positifs) else float("nan")
        drapeau = "  🔴 sous la résolution" if petit == petit and petit < res else ""
        print(f"{p:8s} {int(g['n_blocs_3mois'].median()):8d} {len(g):7d} "
              f"±{res:11.3f} % ±{g['demi_ic95'].min():6.3f} ±{g['demi_ic95'].max():6.3f}"
              f"   {petit:+.3f} %{drapeau}")
        lignes.append({"axe": axe, "polluant": p, "n_blocs_3mois_median":
                       int(g["n_blocs_3mois"].median()), "n_configurations": len(g),
                       "resolution_demi_ic95_pct": res,
                       "demi_ic95_min": float(g["demi_ic95"].min()),
                       "demi_ic95_max": float(g["demi_ic95"].max()),
                       "plus_petit_gain_positif_mesure_pct": petit})
    print("═" * 88)
    r = pd.DataFrame(lignes)
    pire = r.loc[r["resolution_demi_ic95_pct"].idxmax()]
    print(f"Lecture : sur cet axe, un gain apparié inférieur à ±{r['resolution_demi_ic95_pct'].median():.2f} % "
          f"n'est pas séparé de zéro.")
    print(f"          Le polluant le moins résolu est {pire['polluant']} "
          f"(±{pire['resolution_demi_ic95_pct']:.2f} %, {int(pire['n_blocs_3mois_median'])} blocs).")
    if manquants := [c for c in ("resolution_demi_ic95_pct", "polluant") if c not in r]:
        raise SystemExit(f"colonnes absentes du rapport : {manquants}")
    r.to_csv(SORTIE, index=False)
    print(f"Écrit : {SORTIE.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--axe", default="double")
    sys.exit(main(**vars(a.parse_args())))
