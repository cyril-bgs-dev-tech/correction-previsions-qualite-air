#!/usr/bin/env python3
"""Passe unitaire GFAS — les feux comme sources ponctuelles, avant tout lot.

Pourquoi ce jeu
---------------
Un feu est une **source ponctuelle avec des coordonnées, une puissance et une date**. C'est
exactement ce qui manquait à `exposure.exposition_au_vent` — fonction écrite, testée, jamais
utilisée faute de géométries : les stations trafic prises comme mandataires donnaient **86 % de
valeurs nulles à 1 km**.

GFAS couvre **2003 → 03/12/2025**, donc toute la fenêtre d'entraînement du projet. Il est
accessible avec les identifiants ADS déjà en place.

Ce que le mécanisme prédit
--------------------------
Le mode d'échec exhibé par les trois matinées rejouées est la **sous-estimation brutale** :
le 25/07, CAMS annonçait 7,7 µg/m³ là où l'air en portait 51,2, sans qu'aucun produit ne voie
rien. Si une part de ces épisodes vient de panaches de combustion, une exposition anisotrope
aux feux amont devrait s'y voir — et **seulement là**. Un gain réparti uniformément serait
suspect.

Les deux axes, et l'oubli du second a déjà coûté treize heures à ce projet
--------------------------------------------------------------------------
**Résultat** : le format est-il celui annoncé (le `.nc` peut être un ZIP), le mois est-il
complet en jours, les valeurs sont-elles plausibles — une puissance radiative nulle partout
signifierait une variable mal nommée plutôt qu'une absence de feux.

**Coût** : chronométrer, puis extrapoler `t × N` avant de lancer quoi que ce soit.

Usage : python3 scripts/passe_unitaire_gfas.py [--annee 2024] [--mois 7]
"""

from __future__ import annotations

import argparse
import calendar
import sys
import time
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import copernicus as cop  # noqa: E402
from download_copernicus import SERVICES, lire_cle  # noqa: E402

JEU = "cams-global-fire-emissions-gfas"
DOSSIER = RACINE / "data/raw/gfas"
# Emprise large : un panache de combustion voyage sur des centaines de kilomètres, et les feux
# ibériques comme nord-africains concernent l'Occitanie. Restreindre à la France perdrait la
# source la plus probable des épisodes du sud-ouest.
EMPRISE = [55, -15, 30, 15]  # N, O, S, E
N_MOIS_LOT = 17


def main(annee: int, mois: int) -> int:
    DOSSIER.mkdir(parents=True, exist_ok=True)
    jours = calendar.monthrange(annee, mois)[1]
    requete = {
        # La puissance radiative est le diagnostic **direct** de l'intensité d'un feu ; les flux
        # de matière particulaire en sont dérivés et dépendent d'un facteur d'émission par type
        # de végétation, donc d'une hypothèse supplémentaire.
        #
        # Une première version demandait aussi `wildfire_flux_of_particulate_matter_pm2point5`.
        # Le service a rendu **une seule variable sans lever d'erreur** : le nom était invalide.
        # Le contrôle de complétude l'a vu et a rejeté les seize mois du lot — c'est le
        # comportement voulu. On corrige la requête, jamais le garde-fou.
        "variable": ["wildfire_radiative_power"],
        "date": [f"{annee}-{mois:02d}-01/{annee}-{mois:02d}-{jours:02d}"],
        "area": EMPRISE,
        "data_format": "netcdf",
    }
    url, _ = SERVICES["cams_prevision"]
    identifiants = cop.Identifiants(url=url, cle=lire_cle())

    cible = DOSSIER / f"gfas_{annee}{mois:02d}.nc"
    partiel = cible.with_suffix(".nc.partiel")
    print(f"GFAS · {annee}-{mois:02d} · {jours} jours · emprise {EMPRISE}")
    print(f"variables : {', '.join(requete['variable'])}\n", flush=True)

    debut = time.time()
    try:
        cop.executer(identifiants, JEU, requete, str(partiel))
    except Exception as exc:  # noqa: BLE001
        print(f"ÉCHEC {type(exc).__name__}: {str(exc)[:400]}")
        partiel.unlink(missing_ok=True)
        return 1
    duree = time.time() - debut

    # ── Axe résultat ──────────────────────────────────────────────────────────
    import xarray as xr

    est_zip = zipfile.is_zipfile(partiel)
    ouvrir = partiel
    if est_zip:
        with zipfile.ZipFile(partiel) as z:
            noms = z.namelist()
            cible_zip = DOSSIER / "_unitaire"
            cible_zip.mkdir(exist_ok=True)
            z.extractall(cible_zip)
            ouvrir = cible_zip / noms[0]
    d = xr.open_dataset(ouvrir)
    taille = partiel.stat().st_size / 1e6

    print("AXE RÉSULTAT")
    print(f"  {taille:.1f} Mo · archive ZIP : {est_zip}")
    print(f"  variables : {list(d.data_vars)}")
    print(f"  dimensions : {dict(d.sizes)}")

    manques = []
    axe_temps = next((k for k in d.sizes if "time" in k.lower() or k == "valid_time"), None)
    if axe_temps is None or d.sizes[axe_temps] != jours:
        manques.append(f"axe temporel {d.sizes.get(axe_temps)} au lieu de {jours} jours")

    # **Compter les variables reçues contre celles demandées.** Une première version ne
    # vérifiait que l'absence de variable nulle : la requête portait sur deux variables, le
    # service n'en a rendu qu'une, et le contrôle est passé au vert. Vérifier le contenu ne
    # suffit pas — il faut vérifier qu'il est **complet**.
    if len(d.data_vars) != len(requete["variable"]):
        manques.append(f"{len(d.data_vars)} variable(s) reçue(s) pour "
                       f"{len(requete['variable'])} demandée(s) : "
                       f"{list(d.data_vars)} — un nom est probablement invalide")

    # **Une variable entièrement nulle n'est pas une absence de feux** : c'est le signe d'un
    # nom de variable mal choisi ou d'une unité inattendue. On le distingue en regardant le
    # maximum, pas la moyenne — les feux sont rares et intenses.
    for v in d.data_vars:
        m = float(d[v].max())
        n_non_nuls = int((d[v] > 0).sum())
        print(f"  {v}: max {m:.4g} {d[v].attrs.get('units','?')} · "
              f"{n_non_nuls:,} points non nuls")
        if m <= 0:
            manques.append(f"{v} entièrement nulle")
    print(f"  → {'⚠️ ' + ' · '.join(manques) if manques else '✅ structure conforme'}\n",
          flush=True)

    # ── Axe coût ──────────────────────────────────────────────────────────────
    print("AXE COÛT")
    print(f"  durée {duree:.0f}s · {taille:.1f} Mo")
    print(f"  extrapolation lot : {duree:.0f}s × {N_MOIS_LOT} = "
          f"**{duree * N_MOIS_LOT / 60:.0f} min** · {taille * N_MOIS_LOT / 1000:.1f} Go",
          flush=True)

    if manques:
        print("\nLot NON lancé : corriger la requête d'abord.")
        partiel.unlink(missing_ok=True)
        return 1
    partiel.rename(cible)
    print(f"\nÉcrit : {cible.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--annee", type=int, default=2024)
    p.add_argument("--mois", type=int, default=7)
    args = p.parse_args()
    raise SystemExit(main(args.annee, args.mois))
