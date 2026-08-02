"""Fusionne les panneaux des trois jeux EEA en une série continue.

Usage : python scripts/merge_panels.py --scope occitanie

Les trois jeux couvrent des périodes qui se raccordent :
  dataset 3 (Airbase)  1999 → 2012   validé
  dataset 2 (E1a)      2013 → 2025   validé  ← corpus d'entraînement
  dataset 1 (UTD)      2025 → auj.   provisoire · ⚠️ O₃ rompu au 01/07/2025

La colonne `source_dataset` est conservée : sans elle, on perdrait la trace du
passage validé → provisoire, qui est précisément le décalage de distribution que le
projet doit mesurer plutôt que subir.

En cas de recouvrement, la donnée VALIDÉE prime sur la provisoire : une valeur
corrigée lors de la validation réglementaire remplace la valeur brute transmise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.ingest import panel  # noqa: E402

# Ordre de PRIORITÉ décroissante : le premier gagne en cas de doublon.
# Airbase et E1a sont validés, l'UTD est provisoire et donc le moins fiable.
PRIORITE = [2, 3, 1]


def main(scope: str) -> int:
    morceaux = []
    for dataset in PRIORITE:
        chemin = RACINE / f"data/processed/panel_{scope}_ds{dataset}.parquet"
        if not chemin.exists():
            print(f"  absent : {chemin.name} — ignoré")
            continue
        p = pd.read_parquet(chemin)
        p["source_dataset"] = dataset
        # Les lignes vides du réindexage ne portent aucune information : les
        # conserver ferait exploser le volume et masquerait les vrais recouvrements.
        p = p[p["valeur"].notna()]
        morceaux.append(p)
        print(f"  ds{dataset} : {len(p):>10,} mesures  "
              f"{p['timestamp_utc'].min()} → {p['timestamp_utc'].max()}")

    if not morceaux:
        print("Aucun panneau à fusionner.")
        return 1

    fusion = pd.concat(morceaux, ignore_index=True)
    avant = len(fusion)

    cles = ["station_id", "polluant", "timestamp_utc"]
    fusion["_rang"] = fusion["source_dataset"].map(
        {ds: rang for rang, ds in enumerate(PRIORITE)}
    )
    fusion = (
        fusion.sort_values(cles + ["_rang"])
        .drop_duplicates(cles, keep="first")
        .drop(columns="_rang")
    )
    recouvrements = avant - len(fusion)

    print(f"\nFusion : {len(fusion):,} mesures "
          f"({recouvrements:,} doublons arbitrés au profit du validé)")
    print(f"Période : {fusion['timestamp_utc'].min()} → {fusion['timestamp_utc'].max()}")

    # Contrôle des raccords : un trou d'une heure à la jonction de deux jeux
    # passerait inaperçu et créerait une discontinuité systématique.
    print("\nRaccords entre jeux :")
    for dataset in sorted(fusion["source_dataset"].unique()):
        bloc = fusion[fusion["source_dataset"] == dataset]
        print(f"  ds{dataset} : {bloc['timestamp_utc'].min()} → "
              f"{bloc['timestamp_utc'].max()}  ({len(bloc):,} mesures)")

    complet = panel.reindexer_grille(fusion)
    qualite = panel.rapport_qualite(complet)

    complet.to_parquet(RACINE / f"data/processed/panel_{scope}_complet.parquet",
                       index=False)
    qualite.to_csv(RACINE / f"reports/qualite_{scope}_complet.csv", index=False)

    annees = (fusion["timestamp_utc"].max() - fusion["timestamp_utc"].min()).days / 365.25
    print(f"\nPanneau complet : {len(complet):,} lignes · "
          f"{complet['station_id'].nunique()} stations · {annees:.1f} ans")
    print(f"Couverture active médiane : {qualite['couverture_active'].median():.1%}")
    print(f"Écrit : data/processed/panel_{scope}_complet.parquet")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--scope", default="occitanie")
    raise SystemExit(main(parseur.parse_args().scope))
