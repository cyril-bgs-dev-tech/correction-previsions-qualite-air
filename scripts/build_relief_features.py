"""Calcule les indices topographiques de chaque station depuis le MNT Copernicus GLO-30.

Usage : python scripts/build_relief_features.py [--scope metropole]
Sortie : data/processed/relief_features_{scope}.parquet

Aucune donnée n'est stockée : le MNT est lu **par fenêtre** directement sur le stockage
objet public, grâce au format COG. Mesuré à ~2,6 s par station pour un rayon de 30 km.

Le point délicat est le **raccord entre dalles**. Les dalles GLO-30 couvrent 1° × 1° ;
une station proche d'un bord a son voisinage à cheval sur deux, voire quatre d'entre
elles. Lire la seule dalle du point tronquerait le voisinage du côté de la coupure —
et le TPI serait calculé sur un demi-disque, biaisé vers le relief du côté conservé.
Rien ne le signalerait : la valeur resterait plausible.
"""

from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.features import relief  # noqa: E402
from aq.ingest import stations as st  # noqa: E402

PAS_SAUVEGARDE = 25


def fenetre_altitudes(lon: float, lat: float, rayon_m: float) -> np.ndarray:
    """Altitudes dans un carré de `rayon_m` autour d'un point, raccords compris.

    Les dalles nécessaires sont déterminées à partir de l'emprise, puis mosaïquées.
    Une dalle absente — mer, hors couverture — laisse des NaN plutôt que des zéros :
    un zéro se lirait comme « niveau de la mer », valeur parfaitement plausible qui
    fausserait le TPI sans alerter.
    """
    import rasterio
    from rasterio.windows import from_bounds

    d_lon, d_lat = relief.degres_par_metre(lat)
    ouest, est = lon - rayon_m * d_lon, lon + rayon_m * d_lon
    sud, nord = lat - rayon_m * d_lat, lat + rayon_m * d_lat

    morceaux = []
    for lat_dalle in range(int(np.floor(sud)), int(np.floor(nord)) + 1):
        ligne = []
        for lon_dalle in range(int(np.floor(ouest)), int(np.floor(est)) + 1):
            url = relief.url_dalle(lon_dalle + 0.5, lat_dalle + 0.5)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    with rasterio.open(url) as source:
                        fenetre = from_bounds(
                            max(ouest, lon_dalle), max(sud, lat_dalle),
                            min(est, lon_dalle + 1), min(nord, lat_dalle + 1),
                            source.transform,
                        )
                        bloc = source.read(1, window=fenetre, boundless=True,
                                           fill_value=np.nan).astype("float32")
            except Exception:  # noqa: BLE001
                bloc = None
            ligne.append(bloc)

        presents = [b for b in ligne if b is not None]
        if not presents:
            continue
        hauteur = max(b.shape[0] for b in presents)
        ligne = [
            b if b is not None else np.full((hauteur, 1), np.nan, dtype="float32")
            for b in ligne
        ]
        # Harmonise les hauteurs avant l'empilement horizontal : deux dalles voisines
        # peuvent différer d'un pixel après découpe, et `hstack` refuserait.
        ligne = [b[:hauteur] if b.shape[0] >= hauteur
                 else np.pad(b, ((0, hauteur - b.shape[0]), (0, 0)),
                             constant_values=np.nan)
                 for b in ligne]
        morceaux.append(np.hstack(ligne))

    if not morceaux:
        return np.array([[np.nan]], dtype="float32")

    largeur = max(m.shape[1] for m in morceaux)
    morceaux = [m if m.shape[1] == largeur
                else np.pad(m, ((0, 0), (0, largeur - m.shape[1])),
                            constant_values=np.nan)
                for m in morceaux]
    # Le MNT code la mer et les trous par des valeurs très négatives : les garder
    # ferait plonger toutes les moyennes de voisinage côtier.
    mosaique = np.vstack(morceaux)
    return np.where(mosaique < -1000, np.nan, mosaique)


def indices_station(lon: float, lat: float) -> dict[str, float]:
    """Tous les indices topographiques d'une station.

    L'altitude du point est lue dans le MNT plutôt que reprise du référentiel : c'est
    la seule façon d'assurer que le point et son voisinage viennent de la **même**
    source. Mélanger une altitude déclarée avec un voisinage GLO-30 ferait apparaître
    dans le TPI l'écart entre les deux sources, et non le relief.
    """
    rayon_max = max(max(relief.RAYONS_TPI), relief.RAYON_VALLEE)
    grand = fenetre_altitudes(lon, lat, rayon_max)

    # Taille d'un pixel déduite de la fenêtre elle-même, et non supposée : la grande
    # fenêtre couvre exactement 2 × rayon_max de côté. Coder « 30 m » en dur casserait
    # dès qu'on change de rayon ou de MNT, sans le dire.
    metres_par_pixel_y = 2 * rayon_max / grand.shape[0]
    metres_par_pixel_x = 2 * rayon_max / grand.shape[1]

    cy, cx = grand.shape[0] // 2, grand.shape[1] // 2
    centre = grand[cy, cx]
    altitude = float(centre) if np.isfinite(centre) else float("nan")

    def sous_fenetre(rayon_m: float) -> np.ndarray:
        demi_y = max(1, int(rayon_m / metres_par_pixel_y))
        demi_x = max(1, int(rayon_m / metres_par_pixel_x))
        return grand[max(0, cy - demi_y):cy + demi_y + 1,
                     max(0, cx - demi_x):cx + demi_x + 1]

    valeurs: dict[str, float] = {"altitude_mnt_m": altitude}
    for rayon in relief.RAYONS_TPI:
        sous = sous_fenetre(rayon)
        valeurs[f"tpi_{int(rayon)}m"] = relief.indice_position_topographique(
            sous, altitude
        )
        valeurs[f"rugosite_{int(rayon)}m"] = relief.rugosite(sous)

    vallee = sous_fenetre(relief.RAYON_VALLEE)
    valeurs["profondeur_vallee_m"] = relief.profondeur_vallee(vallee, altitude)
    valeurs["pente_deg"] = relief.pente_moyenne(vallee, metres_par_pixel_y)
    return valeurs


def main(scope: str) -> int:
    referentiel = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    if scope == "occitanie":
        sel = referentiel[
            (referentiel["reseau"] == st.RESEAU_OCCITANIE) & referentiel["active"]
        ]
    else:
        sel = referentiel[referentiel["metropole"] & referentiel["active"]]

    chemin = RACINE / f"data/processed/relief_features_{scope}.parquet"
    deja = pd.DataFrame()
    if chemin.exists():
        deja = pd.read_parquet(chemin)
        sel = sel[~sel["station_id"].isin(set(deja["station_id"]))]
        print(f"Reprise : {len(deja)} stations déjà traitées", flush=True)

    sel = sel.reset_index(drop=True)
    print(f"Relief GLO-30 · {len(sel)} stations à traiter", flush=True)

    lignes = []
    debut = time.time()
    for n, station in sel.iterrows():
        try:
            valeurs = indices_station(station["lon_wgs84"], station["lat_wgs84"])
        except Exception as exc:  # noqa: BLE001
            print(f"  [{n+1}/{len(sel)}] ECHEC {station['station_id']} : "
                  f"{type(exc).__name__}: {str(exc)[:120]}", flush=True)
            continue
        lignes.append({"station_id": station["station_id"], **valeurs})

        if len(lignes) % PAS_SAUVEGARDE == 0:
            pd.concat([deja, pd.DataFrame(lignes)], ignore_index=True).to_parquet(
                chemin, index=False
            )
            print(f"  [{n+1}/{len(sel)}] {time.time()-debut:5.0f}s · "
                  f"{len(deja)+len(lignes)} stations", flush=True)

    features = pd.concat([deja, pd.DataFrame(lignes)], ignore_index=True)
    features.to_parquet(chemin, index=False)
    print(f"\n{len(features)} stations · {features.shape[1]-1} indices · {chemin.name}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--scope", default="metropole",
                         choices=["metropole", "occitanie"])
    args = parseur.parse_args()
    raise SystemExit(main(args.scope))
