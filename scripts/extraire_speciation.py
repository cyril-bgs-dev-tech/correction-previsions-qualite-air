#!/usr/bin/env python3
"""La spéciation CAMS aux stations — six variables que le modèle n'avait jamais vues.

Pourquoi un script séparé de `extract_copernicus_stations.py`
--------------------------------------------------------------
Celui-ci attend des **dossiers** de fichiers journaliers nommés `..._<espece>_<AAAAMM>` :
c'est la forme du téléchargement par espèce. La spéciation arrive autrement — **un seul
`.nc` mensuel** portant les six variables et 744 pas de temps, parce qu'on a rempli 89 % du
plafond ADS au lieu de 45 %. Deux formes, deux lecteurs ; forcer la première à lire la
seconde aurait demandé plus de conditions que de code neuf.

Le 16/08, ne pas l'avoir vu a coûté une passe : la veille a lancé l'extracteur générique
sur `--service cams_prevision`, qui a rendu **« 0 lignes écrites »** et un code de sortie
**0**. Seul le contrôle sur l'artefact réécrit l'a attrapé (§ 0, règle C).

Ce que ce script applique, et qui vient de règles payées cher
--------------------------------------------------------------
* **charger avant d'indexer** (§ 2) — `extraire_aux_stations` fait le `.load()` ; une
  lecture paresseuse avec des indices désordonnés dégénère en lecture point par point,
  mesurée à **400×** plus lente sur ce dépôt ;
* **longitudes normalisées** — CAMS Europe livre [0, 360] et un axe **non monotone** à
  cheval sur Greenwich ; sans quoi toute station à l'ouest du méridien reçoit la valeur
  d'une maille prise à des centaines de kilomètres. L'Occitanie descend à −0,33° ;
* **écrire sous un nom provisoire, vérifier, renommer** (§ 4) ;
* **compter le reçu contre le demandé** (§ 2 bis) — les six variables sont exigées
  nommément, un service qui en ignore une servirait le reste sans lever.

Usage : python3 scripts/extraire_speciation.py [--scope metropole]
Sortie : data/processed/meteo/speciation_<scope>_AAAAMM.parquet
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.features import meteo  # noqa: E402
from aq.ingest import stations as st  # noqa: E402

SOURCE = RACINE / "data/raw/cams_speciation"
# ⚠️ Le complément (sel marin, carbone élémentaire total) vit dans un répertoire DISTINCT,
# et une revue externe a montré que le laisser de côté rendait son téléchargement inutile :
# l'extracteur ne l'aurait jamais lu, et 32 fichiers seraient restés sur le disque sans
# jamais entrer dans une mesure. Le contrôle de reprise compare en outre le parquet au
# `mtime` du SEUL fichier historique — donc un complément plus récent ne déclenchait rien.
SOURCE_COMPLEMENT = RACINE / "data/raw/cams_speciation_complement"
COMPLEMENT = ["ectot_conc", "pm10_ss_conc"]
SORTIE = RACINE / "data/processed/meteo"

# Les noms tels que CAMS les livre — vérifiés sur fichier réel, jamais déduits du nom
# demandé à l'API (`residential_elementary_carbon` arrive en `ecres_conc`).
ATTENDUES = ["dust", "ecres_conc", "pm2p5_total_om_conc", "pmwf_conc", "sia_conc"]

# ⚠️ **Le nitrate n'existe que depuis décembre 2024**, et CAMS l'omet SANS LEVER pour les
# mois antérieurs : le téléchargement a demandé six variables et reçu cinq, en silence —
# vérifié sur fichier (202401/06/11 : 5 variables ; 202412 : 6). C'est le § 2 bis,
# *« compter le reçu contre le demandé »*, et c'est un relecteur externe qui l'a signalé
# avant que le contrôle de schéma ne soit en place.
#
# Il n'est donc pas « attendu » mais **tardif** : présent quand il l'est, compté quand il
# ne l'est pas. Le déclarer obligatoire aurait rejeté onze mois valides ; le passer sous
# silence aurait produit une colonne à moitié vide dont personne n'aurait su la cause.
# Sa redondance avec `sia_conc` — dont il est une composante — rend la perte faible.
TARDIVES = ["pm2p5_no3_conc"]


def main(scope: str) -> int:
    SORTIE.mkdir(parents=True, exist_ok=True)
    fichiers = sorted(SOURCE.glob("speciation_*.nc"))
    if not fichiers:
        raise SystemExit(f"aucun fichier dans {SOURCE} — lancer "
                         f"scripts/telecharger_speciation_cams.py")

    # ⚠️ **Le périmètre de stations est celui de l'emprise téléchargée, pas le répertoire
    # national.** Prendre les 868 stations du référentiel fait entrer les DROM : le
    # contrôle de couverture a levé sur **55 points hors du domaine** [-4,95 · 9,95] ×
    # [41,05 · 51,95], et il a bien fait — `nearest` les aurait rabattues sur le bord de
    # grille, c'est-à-dire à des centaines de kilomètres, sans rien dire. On réutilise donc
    # la sélection de l'extracteur générique plutôt que d'en réécrire une plus faible.
    from extract_copernicus_stations import selectionner_stations  # noqa: PLC0415

    stations = selectionner_stations(scope).reset_index(drop=True)

    print(f"{len(fichiers)} mois sur disque · {len(stations)} stations", flush=True)
    t0, faits, sautes, avec_tardives = time.time(), 0, 0, []
    for n, f in enumerate(fichiers, start=1):
        mois = f.stem.split("_")[1]
        cible = SORTIE / f"speciation_{scope}_{mois}.parquet"
        # ⚠️ **La reprise doit regarder TOUTES les sources, pas la première.** Elle ne
        # comparait qu'au fichier historique : le complément arrivé après produisait un
        # parquet « déjà à jour » et 32 fichiers téléchargés n'entraient jamais dans une
        # mesure. Signalé par une revue externe, vérifié : « 0 écrits, 32 déjà à jour ».
        # Un test de reprise qui ignore une source est un test qui ment (§ 4).
        fc = SOURCE_COMPLEMENT / f"speciation_complement_{mois}.nc"
        sources = [f] + ([fc] if fc.exists() else [])
        if cible.exists() and cible.stat().st_mtime > max(x.stat().st_mtime for x in sources):
            sautes += 1
            continue

        t = meteo.extraire_aux_stations(str(f), stations)

        # ── Le complément, joint sur (station, horodatage) — jamais sur le jour civil ────
        if fc.exists():
            c = meteo.extraire_aux_stations(str(fc), stations)
            absentes = [v for v in COMPLEMENT if v not in c.columns]
            if absentes:
                raise SystemExit(f"{fc.name} : variables absentes : {absentes} — "
                                 f"reçu {sorted(x for x in c.columns if x.endswith('_conc'))}")
            avant_j = len(t)
            t = t.merge(c[["station_id", "timestamp_utc"] + COMPLEMENT],
                        on=["station_id", "timestamp_utc"], how="left", validate="1:1")
            if len(t) != avant_j:
                raise SystemExit(f"{mois} : jointure du complément a changé le compte "
                                 f"({avant_j} → {len(t)})")
            perdu = t[COMPLEMENT].isna().any(axis=1).mean()
            if perdu > 0.001:
                raise SystemExit(f"{mois} : {100*perdu:.2f} % de lignes sans complément "
                                 f"— au-delà du seuil de 0,1 %")

        manque = [c for c in ATTENDUES if c not in t.columns]
        if manque:
            raise SystemExit(f"{f.name} : variables absentes du fichier reçu : {manque} "
                             f"— reçu {sorted(c for c in t.columns if c not in ('station_id', 'timestamp_utc'))}")
        # Une colonne plate est presque toujours le signe qu'on a lu autre chose que ce
        # qu'on croyait (§ 2 bis). `pmwf_conc` peut légitimement être nulle hors feux :
        # on exige donc la variation sur l'ENSEMBLE, pas colonne par colonne.
        # Périmètre EFFECTIF, pas demandé (§ 2 quater) : on DIT quels mois portent les
        # variables tardives, au lieu de laisser une colonne à moitié vide s'expliquer
        # toute seule dans les métriques finales.
        presentes = [c for c in TARDIVES if c in t.columns]
        if presentes:
            avec_tardives.append(mois)

        if not (t[ATTENDUES].std() > 0).any():
            raise SystemExit(f"{f.name} : les six variables sont constantes")

        prov = cible.with_suffix(".parquet.partiel")
        t.to_parquet(prov, index=False)
        prov.rename(cible)
        faits += 1
        print(f"  [{n}/{len(fichiers)}] {int(time.time()-t0):4d}s  {mois}  "
              f"{len(t):,} lignes · {len(ATTENDUES)} variables", flush=True)

    ecrits = sorted(SORTIE.glob(f"speciation_{scope}_*.parquet"))
    print(f"\n{len(ecrits)} mois sur disque ({faits} écrits, {sautes} déjà à jour) · "
          f"{(time.time()-t0)/60:.1f} min", flush=True)
    print(f"  socle : {len(ATTENDUES)} variables sur les {len(ecrits)} mois", flush=True)
    if avec_tardives:
        print(f"  tardives {TARDIVES} : {len(avec_tardives)} mois sur {faits} traités "
              f"— de {min(avec_tardives)} à {max(avec_tardives)}", flush=True)
    elif faits:
        print(f"  tardives {TARDIVES} : AUCUN mois — à ne pas utiliser", flush=True)
    if not ecrits:
        raise SystemExit("AUCUN fichier écrit")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--scope", default="metropole", choices=("metropole", "occitanie"))
    n = a.parse_args()
    raise SystemExit(main(n.scope))
