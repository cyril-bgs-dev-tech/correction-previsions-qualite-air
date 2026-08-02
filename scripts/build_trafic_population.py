"""Extrait les variables de trafic hiérarchisé et de population pour chaque station.

Usage : python scripts/build_trafic_population.py [--scope metropole]
Sortie : data/processed/trafic_population_{scope}.parquet

Deux couches sont interrogées : le réseau routier de la BD TOPO, dont on exploite cette
fois `nature`, `importance` et `nombre_de_voies` — et non la seule longueur —, et les
communes d'ADMIN EXPRESS, qui portent la population.

**Le regroupement par proximité est repris du chantier géospatial**, pour la même
raison : la distance médiane au plus proche voisin est de 4,1 km, si bien que des
requêtes individuelles retéléchargeraient massivement les mêmes objets.

Rayons distincts, parce que les deux phénomènes n'ont pas la même portée :

- **routes 5 km** — le NO₂ retombe au fond vers 150-300 m ; au-delà de quelques
  kilomètres une route ne contribue plus, et le réseau est deux ordres de grandeur plus
  dense que la forêt ;
- **communes 40 km** — une métropole influence la composition de l'air bien au-delà de
  ses limites, et le pôle dominant d'une station rurale peut être lointain.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.features import extraction_groupee as eg  # noqa: E402
from aq.features import trafic_population as tp  # noqa: E402
from aq.ingest import geopf, stations as st  # noqa: E402

COUCHE_COMMUNE = "ADMINEXPRESS-COG-CARTO-PE.LATEST:commune"
RAYON_ROUTE = 5_000.0
RAYON_COMMUNE = 40_000.0
PAS_SAUVEGARDE = 20


def main(scope: str) -> int:
    referentiel = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    if scope == "occitanie":
        sel = referentiel[
            (referentiel["reseau"] == st.RESEAU_OCCITANIE) & referentiel["active"]
        ]
    else:
        sel = referentiel[referentiel["metropole"] & referentiel["active"]]

    chemin = RACINE / f"data/processed/trafic_population_{scope}.parquet"
    deja = pd.DataFrame()
    if chemin.exists():
        deja = pd.read_parquet(chemin)
        sel = sel[~sel["station_id"].isin(set(deja["station_id"]))]
        print(f"Reprise : {len(deja)} stations déjà traitées", flush=True)

    sel = sel.reset_index(drop=True)
    if sel.empty:
        print("Rien à faire.")
        return 0

    x = sel["x_l93"].to_numpy()
    y = sel["y_l93"].to_numpy()
    groupes_routes = eg.grouper_stations(x, y, seuil_m=RAYON_ROUTE, cote_max_m=30_000)
    groupes_communes = eg.grouper_stations(x, y, seuil_m=RAYON_COMMUNE,
                                           cote_max_m=120_000)
    print(f"{len(sel)} stations · {len(groupes_routes)} requêtes routes · "
          f"{len(groupes_communes)} requêtes communes", flush=True)

    # ── Routes ──
    routes_par_station: dict[int, list] = {}
    debut = time.time()
    for groupe in groupes_routes:
        cx, cy, demi = eg.emprise_groupe(x, y, groupe, RAYON_ROUTE)
        try:
            entites = geopf.interroger("route", cx, cy, demi)
            for i in groupe:
                routes_par_station[i] = entites
        except ValueError:
            # Emprise trop dense (cœur urbain) : repli station par station, peu coûteux
            # à 5 km de rayon, plutôt que de tronquer.
            for i in groupe:
                try:
                    routes_par_station[i] = geopf.interroger(
                        "route", x[i], y[i], RAYON_ROUTE)
                except Exception:  # noqa: BLE001
                    routes_par_station[i] = []
        except Exception as exc:  # noqa: BLE001
            print(f"  ECHEC routes ({len(groupe)} stations) : "
                  f"{type(exc).__name__}", flush=True)
            for i in groupe:
                routes_par_station[i] = []
    print(f"Routes récupérées en {time.time() - debut:.0f}s", flush=True)

    # ── Communes ──
    communes_par_station: dict[int, list] = {}
    for groupe in groupes_communes:
        cx, cy, demi = eg.emprise_groupe(x, y, groupe, RAYON_COMMUNE)
        try:
            entites = geopf.interroger(COUCHE_COMMUNE, cx, cy, demi)
            for i in groupe:
                communes_par_station[i] = entites
        except Exception as exc:  # noqa: BLE001
            print(f"  ECHEC communes ({len(groupe)} stations) : "
                  f"{type(exc).__name__}", flush=True)
            for i in groupe:
                communes_par_station[i] = []
    print(f"Communes récupérées en {time.time() - debut:.0f}s\n", flush=True)

    lignes = []
    for n, station in sel.iterrows():
        xs, ys = station["x_l93"], station["y_l93"]
        routes = eg.filtrer_autour(routes_par_station.get(n, []), xs, ys, RAYON_ROUTE)
        communes = eg.filtrer_autour(communes_par_station.get(n, []), xs, ys,
                                     RAYON_COMMUNE)
        try:
            valeurs = tp.variables_routieres(xs, ys, routes)
            valeurs |= tp.variables_population(xs, ys, communes)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{n+1}/{len(sel)}] ECHEC {station['station_id']} : "
                  f"{type(exc).__name__}: {str(exc)[:100]}", flush=True)
            continue
        lignes.append({"station_id": station["station_id"], **valeurs})

        if len(lignes) % PAS_SAUVEGARDE == 0:
            pd.concat([deja, pd.DataFrame(lignes)], ignore_index=True).to_parquet(
                chemin, index=False)
            print(f"  [{n+1}/{len(sel)}] {time.time() - debut:5.0f}s · "
                  f"{len(deja) + len(lignes)} stations", flush=True)

    table = pd.concat([deja, pd.DataFrame(lignes)], ignore_index=True)
    table.to_parquet(chemin, index=False)
    print(f"\n{len(table)} stations · {table.shape[1] - 1} variables · {chemin.name}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--scope", default="metropole",
                         choices=["metropole", "occitanie"])
    args = parseur.parse_args()
    raise SystemExit(main(args.scope))
