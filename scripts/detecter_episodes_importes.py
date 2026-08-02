"""Détecte les épisodes de particules d'origine **importée**, non locale.

Usage : python scripts/detecter_episodes_importes.py [--polluant PM10]
Sortie : reports/EPISODES_IMPORTES.md et reports/episodes_importes.csv

**Pourquoi cette détection a une valeur réglementaire directe.** L'article 20 de la
directive 2008/50/CE autorise un État membre à **soustraire la contribution des sources
naturelles** — poussières sahariennes, embruns marins, feux de végétation — du décompte
des dépassements servant à établir la conformité. Encore faut-il la démontrer. Pour une
AASQA méditerranéenne, c'est une question opérationnelle annuelle, pas un cas d'école.

**Le critère, et pourquoi le niveau seul ne suffit pas.** Un épisode importé arrive par
la circulation d'altitude et touche tout un territoire à la fois : il est **synchrone et
homogène**. Une pollution locale — trafic, chauffage, industrie — reste contrastée d'une
station à l'autre, quelle que soit son intensité. C'est donc le **coefficient de
variation entre stations**, et non la concentration, qui porte l'information d'origine.

Retenir le seul niveau confondrait les inversions hivernales, souvent plus intenses
encore, mais spatialement très hétérogènes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval import phenomenes  # noqa: E402

# Valeur limite journalière PM10 : 50 µg/m³, à ne pas dépasser plus de 35 jours par an
# (directive 2008/50/CE, annexe XI). C'est ce décompte que l'article 20 permet de
# corriger des sources naturelles.
VALEUR_LIMITE_PM10 = 50.0


def main(polluant: str, panneau: str) -> int:
    chemin = RACINE / f"data/processed/{panneau}"
    p = pd.read_parquet(chemin, columns=["station_id", "polluant", "timestamp_utc",
                                         "valeur"])
    p = p[(p["polluant"] == polluant) & p["valeur"].notna()]

    stations = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                               columns=["station_id", "nom", "commune", "type_station"])
    p = p.merge(stations, on="station_id")
    p = p[p["type_station"] == "background"]

    print(f"{polluant} · {len(p):,} mesures de fond · "
          f"{p['station_id'].nunique()} stations", flush=True)

    jours = phenomenes.episodes_importes(p)
    importes = jours[jours["importe"]]

    print(f"\n{len(jours):,} jours évaluables · {len(importes)} épisodes importés",
          flush=True)
    print(f"  concentration pendant ces jours : {importes['moyenne'].mean():.1f} µg/m³ "
          f"contre {jours['moyenne'].median():.1f} en médiane", flush=True)
    print(f"  homogénéité (CV) : {importes['coef_variation'].mean():.2f} contre "
          f"{jours['coef_variation'].median():.2f}", flush=True)

    # Ce que la déduction changerait au décompte réglementaire.
    if polluant == "PM10":
        depassements = jours[jours["moyenne"] >= VALEUR_LIMITE_PM10]
        deductibles = depassements[depassements["importe"]]
        print(f"\nDécompte réglementaire (valeur limite {VALEUR_LIMITE_PM10:.0f} µg/m³ "
              "en moyenne journalière) :", flush=True)
        print(f"  {len(depassements)} jour(s) de dépassement moyen sur le territoire",
              flush=True)
        print(f"  dont {len(deductibles)} attribuable(s) à un apport importé "
              f"({100 * len(deductibles) / max(1, len(depassements)):.0f} %)", flush=True)

    par_annee = (importes.assign(annee=pd.to_datetime(importes["jour"]).dt.year)
                 .groupby("annee").size())
    print("\nRépartition par année :", flush=True)
    for annee, n in par_annee.items():
        print(f"  {annee} : {'▪' * int(n)} {n}", flush=True)

    print("\nLes dix épisodes les plus marqués :", flush=True)
    top = importes.nlargest(10, "moyenne")
    for _, ligne in top.iterrows():
        print(f"  {ligne['jour']} · {ligne['moyenne']:5.1f} µg/m³ · "
              f"CV {ligne['coef_variation']:.2f} · {int(ligne['n_stations'])} stations",
              flush=True)

    sortie = RACINE / "reports/episodes_importes.csv"
    importes.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.name}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="PM10", choices=["PM10", "PM25"])
    parseur.add_argument("--panneau", default="panel_occitanie_ds2.parquet")
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.panneau))
