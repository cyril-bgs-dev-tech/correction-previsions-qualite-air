"""Construit un panneau horaire de mesures, par périmètre et par jeu de données.

Usage :
  python scripts/build_panel.py --scope occitanie --dataset 2
  python scripts/build_panel.py --scope metropole --dataset 2
  python scripts/build_panel.py --scope occitanie --dataset 3   # Airbase 2001-2012

Jeux de données (voir DATA_CATALOG.md §2.0 bis) :
  3 — Airbase historique, 2001 → 2012, validé
  2 — E1a validé, 2013 → 2025 : le corpus d'entraînement
  1 — temps réel, 2025 → aujourd'hui · ⚠️ O₃ rompu au 01/07/2025
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


def selectionner_stations(scope: str) -> tuple[set[str], pd.DataFrame]:
    referentiel = pd.read_parquet(RACINE / "data/processed/stations.parquet")

    if scope == "occitanie":
        sel = referentiel[
            (referentiel["reseau"] == st.RESEAU_OCCITANIE) & referentiel["active"]
        ]
    elif scope == "metropole":
        # Outre-mer exclu : régime tropical, sources et chimie différentes — l'y
        # inclure dégraderait l'apprentissage spatial métropolitain.
        sel = referentiel[referentiel["metropole"] & referentiel["active"]]
    elif scope == "metropole_all":
        # Stations fermées incluses : elles portent de l'historique, et les
        # exclure biaiserait le corpus vers les seules stations pérennes.
        sel = referentiel[referentiel["metropole"]]
    else:
        raise ValueError(f"Périmètre inconnu : {scope}")

    return set(sel["station_id"]), sel


def main(scope: str, dataset: int) -> int:
    codes, sel = selectionner_stations(scope)
    print(f"Périmètre '{scope}' : {len(codes)} stations | dataset={dataset}", flush=True)

    urls: list[str] = []
    for polluant in POLLUANTS:
        trouves = eea.lister_fichiers([polluant], pays="FR", dataset=dataset)
        retenus = [u for u in trouves if eea.code_station(u) in codes]
        print(f"  {polluant:5s} : {len(retenus):4d} séries", flush=True)
        urls += retenus

    debut = time.time()
    brut, echecs = panel.telecharger_series(urls, max_parallele=8)
    print(f"\nTéléchargé {len(urls) - len(echecs)}/{len(urls)} séries en "
          f"{time.time() - debut:.0f}s — {len(brut):,} lignes brutes", flush=True)
    for url, erreur in echecs[:10]:
        print(f"  ÉCHEC {url.rsplit('/', 1)[-1]} : {erreur}", flush=True)

    if brut.empty:
        print("Aucune donnée récupérée.", flush=True)
        return 1

    p = panel.reindexer_grille(panel.construire_panneau(brut))
    print(f"Panneau : {len(p):,} lignes · {p['station_id'].nunique()} stations · "
          f"{p['timestamp_utc'].min()} → {p['timestamp_utc'].max()}", flush=True)

    qualite = panel.rapport_qualite(p)

    suffixe = f"{scope}_ds{dataset}"
    p.to_parquet(RACINE / f"data/processed/panel_{suffixe}.parquet", index=False)
    qualite.to_csv(RACINE / f"reports/qualite_{suffixe}.csv", index=False)

    print(f"\nCouverture active médiane : {qualite['couverture_active'].median():.1%}")
    print(f"Séries réellement sous 75 % : "
          f"{int((qualite['couverture_active'] < 0.75).sum())}/{len(qualite)}")
    print(f"Écrit : data/processed/panel_{suffixe}.parquet", flush=True)
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--scope", default="occitanie",
                         choices=["occitanie", "metropole", "metropole_all"])
    parseur.add_argument("--dataset", type=int, default=2, choices=[1, 2, 3])
    args = parseur.parse_args()
    raise SystemExit(main(args.scope, args.dataset))
