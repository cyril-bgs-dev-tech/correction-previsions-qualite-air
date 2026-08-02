"""Calcule les variables d'exposition géospatiale pour chaque station.

Usage : python scripts/build_geo_features.py --scope occitanie [--rayon 30000]
Sortie : data/processed/geo_features_{scope}.parquet

Une ligne par station, une colonne par couple (couche, λ). Les distances se
calculent en Lambert-93, jamais en degrés.

Les essences forestières sont séparées : les **chênes** sont les grands émetteurs
d'isoprène, précurseur d'ozone dont l'émission croît exponentiellement avec la
température. Les conifères émettent surtout des monoterpènes, au potentiel de
formation d'ozone bien moindre. Agréger les deux sous « forêt » dilue le signal.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.features import exposure  # noqa: E402
from aq.features import extraction_groupee as eg  # noqa: E402
from aq.ingest import geopf, stations as st  # noqa: E402

# Regroupements d'essences par potentiel d'émission de COV biogéniques.
# Les libellés proviennent de l'attribut `essence` de la BD Forêt V2.
# Fréquence d'écriture du point de reprise, en nombre de stations.
PAS_SAUVEGARDE = 10

# Rayon d'interrogation du reseau routier : le NO2 retombe au fond vers 150-300 m,
# au-dela de quelques kilometres une route ne contribue plus.
RAYON_ROUTE = 5_000.0

GROUPES_ESSENCE = {
    "chene": ["Chênes décidus", "Chênes sempervirents", "Chêne liège"],
    "feuillu_autre": ["Feuillus", "Peuplier", "Robinier", "Hêtre", "Châtaignier",
                      "Mixte"],
    "conifere": ["Conifères", "Pin laricio, pin noir", "Pin maritime",
                 "Pin sylvestre", "Sapin, épicéa", "Douglas", "Mélèze",
                 "Pin d'Alep", "Pin à crochets, pin cembro"],
}


def features_station(
    x: float, y: float, rayon_m: float,
    forets_groupe=None, routes_groupe=None,
) -> dict[str, float]:
    """Toutes les variables d'exposition pour une station.

    Les entités peuvent venir du groupe : elles sont alors filtrées sur le disque de
    la station, ce qui supprime une requête réseau redondante.
    """
    valeurs: dict[str, float] = {}

    forets = (
        eg.filtrer_autour(forets_groupe, x, y, rayon_m)
        if forets_groupe is not None
        else geopf.interroger("foret", x, y, rayon_m)
    )
    par_essence = geopf.separer_par_essence(forets)

    # Un groupe par potentiel d'émission, plus l'agrégat toutes forêts confondues
    # pour permettre la comparaison avec la littérature LUR classique.
    groupes = {
        nom: [e for libelle in libelles for e in par_essence.get(libelle, [])]
        for nom, libelles in GROUPES_ESSENCE.items()
    }
    groupes["foret_tot"] = forets

    for nom, entites in groupes.items():
        xs = [e.x for e in entites]
        ys = [e.y for e in entites]
        masses = [e.masse for e in entites]

        valeurs[f"{nom}_surface_m2"] = float(sum(masses))
        valeurs[f"{nom}_dist_min_m"] = float(
            exposure.distance_plus_proche([x], [y], xs, ys)[0]
        )
        colonnes = exposure.balayer_lambdas(
            [x], [y], xs, ys, masses, prefixe=nom
        )
        valeurs.update(colonnes.iloc[0].to_dict())

    # Routes : la masse est une longueur, pas une surface. Le NO₂ décroît très vite
    # (fond atteint vers 150-300 m), d'où l'intérêt des λ courts.
    rayon_route = min(rayon_m, RAYON_ROUTE)
    routes = (
        eg.filtrer_autour(routes_groupe, x, y, rayon_route)
        if routes_groupe is not None
        else geopf.interroger("route", x, y, rayon_route)
    )
    xs = [e.x for e in routes]
    ys = [e.y for e in routes]
    masses = [e.masse for e in routes]
    valeurs["route_longueur_m"] = float(sum(masses))
    valeurs["route_dist_min_m"] = float(
        exposure.distance_plus_proche([x], [y], xs, ys)[0]
    )
    valeurs.update(
        exposure.balayer_lambdas(
            [x], [y], xs, ys, masses,
            lambdas=(100.0, 300.0, 1_000.0, 3_000.0), prefixe="route",
        ).iloc[0].to_dict()
    )

    return valeurs


def main(scope: str, rayon_m: float) -> int:
    referentiel = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    if scope == "occitanie":
        sel = referentiel[
            (referentiel["reseau"] == st.RESEAU_OCCITANIE) & referentiel["active"]
        ]
    else:
        sel = referentiel[referentiel["metropole"] & referentiel["active"]]

    chemin = RACINE / f"data/processed/geo_features_{scope}.parquet"

    # Reprise sur interruption. Une extraction de plusieurs heures DOIT être
    # reprenable : sans cela, une coupure au bout de 400 stations perd tout le
    # travail, et rien n'est lisible avant la toute fin.
    deja = pd.DataFrame()
    if chemin.exists():
        deja = pd.read_parquet(chemin)
        sel = sel[~sel["station_id"].isin(set(deja["station_id"]))]
        print(f"Reprise : {len(deja)} stations déjà extraites", flush=True)

    print(f"Périmètre '{scope}' : {len(sel)} à traiter · rayon {rayon_m/1000:.0f} km",
          flush=True)

    sel = sel.reset_index(drop=True)
    x = sel["x_l93"].to_numpy()
    y = sel["y_l93"].to_numpy()
    groupes = eg.grouper_stations(x, y, seuil_m=rayon_m, cote_max_m=80_000)
    resume = eg.resume_groupes(x, y, groupes, rayon_m)
    print(f"Regroupement : {len(groupes)} requetes au lieu de {len(sel)} "
          f"({resume['surface_km2'].sum() / 1e3:.0f} x10^3 km2 a interroger)", flush=True)

    # Le reseau routier est deux ordres de grandeur plus dense que la foret : une
    # emprise de 137 km contient ~40 000 polygones forestiers mais 1,2 MILLION de
    # troncons. Les routes n'ayant besoin que de 5 km de rayon, elles sont regroupees
    # separement, sur des emprises bien plus petites.
    groupes_routes = eg.grouper_stations(x, y, seuil_m=RAYON_ROUTE, cote_max_m=30_000)
    print(f"Routes : {len(groupes_routes)} requetes (rayon {RAYON_ROUTE/1000:.0f} km)",
          flush=True)

    lignes = []
    debut = time.time()
    n = 0
    routes_par_station: dict[int, list] = {}

    for groupe in groupes_routes:
        cx, cy, demi = eg.emprise_groupe(x, y, groupe, RAYON_ROUTE)
        try:
            routes = geopf.interroger("route", cx, cy, demi)
            for i in groupe:
                routes_par_station[i] = routes
        except ValueError:
            # Emprise trop dense pour une requete groupee (coeur urbain : plus de
            # 280 000 troncons sur 30 km). Repli sur des requetes par station, peu
            # couteuses a 5 km de rayon, plutot que de tronquer ou d'abandonner.
            print(f"  Groupe routier trop dense ({len(groupe)} stations) : "
                  "repli sur requetes individuelles", flush=True)
            for i in groupe:
                try:
                    routes_par_station[i] = geopf.interroger(
                        "route", x[i], y[i], RAYON_ROUTE
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"    ECHEC station {i} : {type(exc).__name__}: {exc}",
                          flush=True)
                    routes_par_station[i] = []
        except Exception as exc:  # noqa: BLE001
            print(f"  ECHEC routes ({len(groupe)} stations) : "
                  f"{type(exc).__name__}: {exc}", flush=True)
            for i in groupe:
                routes_par_station[i] = []

    print(f"Routes recuperees en {time.time() - debut:.0f}s", flush=True)

    for groupe in groupes:
        cx, cy, demi = eg.emprise_groupe(x, y, groupe, rayon_m)
        try:
            forets = geopf.interroger("foret", cx, cy, demi)
        except Exception as exc:  # noqa: BLE001
            print(f"  ECHEC forets ({len(groupe)} stations) : "
                  f"{type(exc).__name__}: {exc}", flush=True)
            n += len(groupe)
            continue

        for i in groupe:
            n += 1
            station = sel.iloc[i]
            try:
                valeurs = features_station(
                    station["x_l93"], station["y_l93"], rayon_m,
                    forets_groupe=forets,
                    routes_groupe=routes_par_station.get(i, []),
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  [{n}/{len(sel)}] ECHEC {station['station_id']} : "
                      f"{type(exc).__name__}: {exc}", flush=True)
                continue
            lignes.append({"station_id": station["station_id"], **valeurs})

        # Ecriture apres chaque groupe : les resultats partiels restent lisibles.
        if True:
            pd.concat([deja, pd.DataFrame(lignes)], ignore_index=True).to_parquet(
                chemin, index=False
            )
            print(f"  [{n}/{len(sel)}] {time.time() - debut:.0f}s · "
                  f"{len(deja) + len(lignes)} stations enregistrées", flush=True)

    features = pd.concat([deja, pd.DataFrame(lignes)], ignore_index=True)
    features.to_parquet(chemin, index=False)

    print(f"\n{len(features)} stations · {features.shape[1] - 1} variables")
    print(f"Écrit : {chemin.name}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--scope", default="occitanie",
                         choices=["occitanie", "metropole"])
    parseur.add_argument("--rayon", type=float, default=30_000.0)
    args = parseur.parse_args()
    raise SystemExit(main(args.scope, args.rayon))
