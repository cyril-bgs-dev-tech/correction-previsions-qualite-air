"""Reproduit la chaîne officielle : stations → champ → maximum par EPCI → indice.

Usage : python scripts/spatialiser_indice.py [--polluant O3] [--resolution 2000]

Compare le résultat à l'indice publié par Atmo Occitanie. L'écart mesuré ici est
l'écart de **spatialisation** — la seule étape de la chaîne officielle que le projet
ne peut pas reprendre telle quelle, faute d'accès à leur modèle.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.models import indice_atmo as ia, spatialisation as sp  # noqa: E402

COLONNE_OFFICIELLE = {"O3": "code_o3", "NO2": "code_no2", "PM25": "code_pm25"}


def main(polluant: str, resolution_m: float) -> int:
    officiel = pd.read_parquet(RACINE / "data/processed/indice_officiel_occitanie.parquet")
    officiel["code_zone"] = officiel["code_zone"].astype(str)
    stations = pd.read_parquet(RACINE / "data/processed/stations.parquet")

    zones = json.loads((RACINE / "data/raw/epci_occitanie.geojson").read_text())["features"]
    codes_utiles = set(officiel["code_zone"])
    zones = [z for z in zones if z["properties"]["code_siren"] in codes_utiles]
    print(f"EPCI retenus : {len(zones)}", flush=True)

    # Les stations de FOND seules : l'indice officiel les utilise exclusivement,
    # une station trafic mesurerait un micro-environnement non représentatif.
    fond = stations[
        (stations["type_station"] == "background")
        & (stations["reseau"] == "NET-FR068A")
        & stations["active"]
    ]

    panneaux = [
        pd.read_parquet(RACINE / f"data/processed/panel_occitanie_ds{ds}.parquet")
        for ds in (1, 2)
    ]
    panneau = pd.concat(panneaux, ignore_index=True)
    panneau = panneau[
        (panneau["polluant"] == polluant)
        & panneau["station_id"].isin(set(fond["station_id"]))
    ]

    # Grandeur journalière conforme à l'arrêté pour ce polluant.
    quotidien = ia.sous_indices_journaliers(panneau)
    quotidien = quotidien.dropna(subset=["grandeur_retenue"])
    quotidien = quotidien.merge(
        fond[["station_id", "x_l93", "y_l93"]], on="station_id"
    )

    jours_officiels = set(officiel["jour_local"])
    quotidien = quotidien[quotidien["jour_local"].isin(jours_officiels)]
    jours = sorted(quotidien["jour_local"].unique())
    print(f"Jours comparables : {len(jours)} · "
          f"{quotidien['station_id'].nunique()} stations de fond", flush=True)
    if not jours:
        print("Aucun jour commun entre les mesures et l'indice publié.")
        return 1

    grille = sp.grille_reguliere(430_000, 6_160_000, 850_000, 6_490_000, resolution_m)
    print(f"Grille : {len(grille):,} mailles à {resolution_m:.0f} m", flush=True)

    debut = time.time()
    grille = sp.indexer_grille_par_zone(grille, zones)
    print(f"Mailles rattachées à un EPCI : {len(grille):,} "
          f"({time.time() - debut:.0f}s)", flush=True)

    resultats = []
    for n, jour in enumerate(jours, 1):
        bloc = quotidien[quotidien["jour_local"] == jour]
        if len(bloc) < 5:  # trop peu de stations pour interpoler un champ crédible
            continue
        champ = grille.copy()
        champ["valeur"] = sp.interpoler_idw(
            champ["x"], champ["y"],
            bloc["x_l93"], bloc["y_l93"], bloc["grandeur_retenue"],
        )
        agrege = sp.agreger_par_zone(champ)
        agrege["jour_local"] = jour
        agrege["n_stations"] = len(bloc)
        resultats.append(agrege)
        if n % 50 == 0:
            print(f"  [{n}/{len(jours)}] {time.time() - debut:.0f}s", flush=True)

    predit = pd.concat(resultats, ignore_index=True)
    predit["sous_indice_max"] = ia.sous_indice(predit["maximum"], polluant)
    predit["sous_indice_moy"] = ia.sous_indice(predit["moyenne"], polluant)

    colonne = COLONNE_OFFICIELLE[polluant]
    comparaison = predit.merge(
        officiel[["jour_local", "code_zone", colonne]].dropna(),
        on=["jour_local", "code_zone"],
    ).rename(columns={colonne: "sous_indice_officiel"})

    print(f"\n=== {polluant} · {len(comparaison):,} couples jour × EPCI ===")
    for nom, colonne_predite in [("maximum sur la zone", "sous_indice_max"),
                                 ("moyenne sur la zone", "sous_indice_moy")]:
        ecart = comparaison[colonne_predite] - comparaison["sous_indice_officiel"]
        print(f"\n-- agrégation par {nom} --")
        print(f"  accord exact   {100 * (ecart == 0).mean():5.1f} %")
        print(f"  écart ≤ 1      {100 * (ecart.abs() <= 1).mean():5.1f} %")
        print(f"  biais moyen    {ecart.mean():+.3f} classe")

    croisement = pd.crosstab(
        comparaison["sous_indice_max"], comparaison["sous_indice_officiel"]
    )
    print("\nMatrice (lignes : spatialisé par maximum · colonnes : officiel)")
    print(croisement.to_string())

    sortie = RACINE / f"reports/spatialisation_{polluant}.csv"
    comparaison.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.name}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--resolution", type=float, default=2000.0)
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.resolution))
