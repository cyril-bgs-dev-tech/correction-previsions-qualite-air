"""Construit le panneau horaire des mesures d'Occitanie.

Usage : python scripts/build_panel_occitanie.py [--dataset 1|2|3]
  2 (défaut) — E1a validé, 2013 → 2025 : le corpus d'entraînement
  1          — temps réel, 2025 → aujourd'hui (⚠️ O₃ rompu au 01/07/2025)
  3          — Airbase historique, 2001 → 2012

Sortie : data/processed/panel_occitanie_ds{N}.parquet + reports/qualite_occitanie_ds{N}.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.ingest import eea, panel, stations as st  # noqa: E402

# PM10 ajouté le 29/07 : c'est le polluant des **épisodes importés** (poussières
# sahariennes), dont l'article 20 de la directive 2008/50/CE permet de déduire la
# contribution du décompte de conformité — encore faut-il pouvoir la démontrer.
POLLUANTS = ["NO2", "O3", "PM25", "PM10"]


def main(dataset: int = eea.DATASET_VERIFIED) -> int:
    referentiel = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    occitanie = referentiel[
        (referentiel["reseau"] == st.RESEAU_OCCITANIE) & referentiel["active"]
    ]
    codes = set(occitanie["station_id"])
    print(f"Stations occitanes actives : {len(codes)} | dataset={dataset}")

    urls: list[str] = []
    for polluant in POLLUANTS:
        trouves = eea.lister_fichiers([polluant], pays="FR", dataset=dataset)
        retenus = [u for u in trouves if eea.code_station(u) in codes]
        print(f"  {polluant:5s} : {len(retenus):3d} séries")
        urls += retenus

    debut = time.time()
    brut, echecs = panel.telecharger_series(urls)
    print(f"\nTéléchargé {len(urls) - len(echecs)}/{len(urls)} séries "
          f"en {time.time() - debut:.0f}s — {len(brut):,} lignes brutes")
    for url, erreur in echecs:
        print(f"  ÉCHEC {url.rsplit('/', 1)[-1]} : {erreur}")

    p = panel.reindexer_grille(panel.construire_panneau(brut))
    print(f"Panneau réindexé : {len(p):,} lignes, "
          f"{p['station_id'].nunique()} stations, "
          f"{p['timestamp_utc'].min()} → {p['timestamp_utc'].max()}")

    qualite = panel.rapport_qualite(p)

    (RACINE / "reports").mkdir(exist_ok=True)
    p.to_parquet(RACINE / f"data/processed/panel_occitanie_ds{dataset}.parquet", index=False)
    qualite.to_csv(RACINE / f"reports/qualite_occitanie_ds{dataset}.csv", index=False)

    print("\n--- Séries les plus dégradées ---")
    print(qualite.head(8).to_string(index=False))
    print(f"\nCouverture médiane : {qualite['couverture_active'].median():.1%}")
    print(f"Séries sous 75 % de couverture : "
          f"{int((qualite['couverture_active'] < 0.75).sum())}/{len(qualite)}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--dataset", type=int, default=eea.DATASET_VERIFIED,
                         choices=[1, 2, 3])
    raise SystemExit(main(parseur.parse_args().dataset))
