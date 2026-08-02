#!/usr/bin/env python3
"""Archive le flux officiel de l'indice ATMO Occitanie, **avec son horodatage de collecte**.

Pourquoi ce script existe
-------------------------
Le flux ouvert d'Atmo Occitanie est **glissant et destructif** :

- il ne sert que du 1er janvier de l'année N−1 jusqu'à J+1 — l'indice de 2024 n'est
  déjà plus récupérable ;
- pour une même échéance `date_ech`, la valeur **J+1** est remplacée par **J0**, puis par
  **J−1**. `date_dif` datant la diffusion *présente*, rien ne conserve les millésimes
  écrasés.

Conséquence : une comparaison prévision-à-prévision ne peut **pas** se reconstituer après
coup. Seul un archivage quotidien la rend possible un jour. Chaque jour sans collecte perd
un millésime définitivement.

Deux modes
----------
- `--mode jour` (défaut) : les échéances J−1 à J+1, **une seule requête**, ~1 s. C'est le
  mode du cron quotidien — la fenêtre utile, pas l'archive entière (règle 3).
- `--mode complet` : tout le flux, 95 requêtes de 1000 lignes, ~110 s. Pour une référence
  de fond ou pour mesurer le taux d'écrasement entre deux millésimes.

Le plafond mesuré vaut **1000 lignes par requête**, malgré un `standardMaxRecordCount` de
16000 annoncé par le service : une requête à 14000 renvoie 1000 lignes et
`exceededTransferLimit: true`. Ne pas se fier au métadonnée, la pagination est obligatoire.

Écriture : fichier `.part`, vérifié, puis renommé (règle 4). Un artefact au nom définitif
est donc toujours complet.

Usage :
    python3 scripts/archiver_indice_officiel.py                 # J−1..J+1
    python3 scripts/archiver_indice_officiel.py --mode complet
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "data/raw/indice_officiel"

SERVICE = (
    "https://services9.arcgis.com/7Sr9Ek9c1QTKmbwr/arcgis/rest/services/"
    "Indice_quotidien_de_qualit%C3%A9_de_l%E2%80%99air_pour_les_collectivit%C3%A9s_"
    "territoriales_en_Occitanie/FeatureServer/0"
)

# Mesuré, pas déduit du service : une requête à 14000 rend 1000 lignes.
PLAFOND = 1000

# Colonnes sans lesquelles l'archive ne sert à rien : l'échéance, la classe, et surtout
# la date de diffusion — c'est elle qui distingue un millésime J+1 d'un constat J−1.
COLONNES_REQUISES = ("date_ech", "date_dif", "code_qual", "code_zone", "type_zone")


def _interroger(params: dict) -> dict:
    url = f"{SERVICE}/query?" + urllib.parse.urlencode({"f": "json", **params})
    with urllib.request.urlopen(url, timeout=120) as reponse:
        import json

        return json.loads(reponse.read())


def _compter(clause: str) -> int:
    return int(_interroger({"where": clause, "returnCountOnly": "true"})["count"])


def recuperer(clause: str) -> pd.DataFrame:
    """Pagine jusqu'à épuisement, en séquentiel.

    Pas de concurrence : le gain serait nul sur 95 requêtes d'une seconde, et un service
    public n'a pas à absorber notre parallélisme.
    """
    total = _compter(clause)
    attendu = (total + PLAFOND - 1) // PLAFOND
    print(f"  {total} lignes annoncées · {attendu} requête(s) de {PLAFOND}", flush=True)

    lignes, decalage, depart = [], 0, time.time()
    while True:
        page = _interroger({
            "where": clause,
            "outFields": "*",
            "returnGeometry": "false",
            "orderByFields": "ObjectId",
            "resultOffset": decalage,
            "resultRecordCount": PLAFOND,
        })
        recues = page.get("features", [])
        lignes.extend(f["attributes"] for f in recues)
        if not recues or len(lignes) >= total:
            break
        decalage += len(recues)
        if decalage % (PLAFOND * 20) == 0:
            ecoule = time.time() - depart
            reste = ecoule / decalage * (total - decalage)
            print(f"    {decalage}/{total} · {ecoule:.0f}s · reste ~{reste:.0f}s", flush=True)

    if len(lignes) != total:
        # Un écart signale une pagination interrompue : le refuser plutôt que l'écrire.
        raise RuntimeError(f"{len(lignes)} lignes reçues pour {total} annoncées")
    return pd.DataFrame(lignes)


def verifier(table: pd.DataFrame) -> tuple[str, str]:
    """Contrôle la structure et **retourne les bornes lues dans les données**.

    Les bornes ne sont jamais déduites d'un nom de fichier (règle 4 bis) : elles sortent
    de `min()` et `max()` de la colonne d'échéance.
    """
    if table.empty:
        raise RuntimeError("table vide")

    manquantes = [c for c in COLONNES_REQUISES if c not in table.columns]
    if manquantes:
        raise RuntimeError(f"colonnes absentes : {', '.join(manquantes)}")

    ech = pd.to_datetime(table["date_ech"], unit="ms", utc=True)
    if ech.isna().any():
        raise RuntimeError(f"{int(ech.isna().sum())} échéances illisibles")

    return ech.min().strftime("%Y-%m-%d"), ech.max().strftime("%Y-%m-%d")


def main(mode: str) -> int:
    DOSSIER.mkdir(parents=True, exist_ok=True)
    collecte = dt.datetime.now(dt.timezone.utc)

    if mode == "jour":
        # Fenêtre utile : les seules échéances encore susceptibles d'être réécrites.
        veille = (collecte - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        clause = f"date_ech >= DATE '{veille}'"
    else:
        clause = "1=1"

    print(f"collecte {collecte:%Y-%m-%d %H:%M} UTC · mode {mode}", flush=True)
    table = recuperer(clause)

    debut, fin = verifier(table)
    # L'horodatage de collecte est la raison d'être de l'archive : sans lui, impossible de
    # savoir si une ligne était une prévision ou un constat au moment où on l'a lue.
    table["collecte_utc"] = collecte

    nom = f"indice_officiel_{collecte:%Y%m%d_%H%M}_{mode}"
    provisoire = DOSSIER / f"{nom}.parquet.part"
    table.to_parquet(provisoire, index=False)
    provisoire.rename(DOSSIER / f"{nom}.parquet")

    millesimes = pd.to_datetime(table["date_dif"], unit="ms", utc=True).nunique()
    print(
        f"écrit : {nom}.parquet · {len(table)} lignes · échéances {debut} → {fin} · "
        f"{millesimes} date(s) de diffusion distincte(s)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("jour", "complet"), default="jour")
    args = p.parse_args()
    try:
        sys.exit(main(args.mode))
    except Exception as erreur:  # noqa: BLE001 — un cron doit voir la cause en clair
        print(f"ÉCHEC : {erreur}", file=sys.stderr)
        sys.exit(1)
