#!/usr/bin/env python3
"""Décodeur GRIB isolé — exécuté dans l'environnement `grib`, jamais dans le principal.

`cfgrib` tire `eccodes` et contraint `numpy`. L'installer dans l'environnement où tournent les
ajustements XGBoost risquerait un conflit de version au milieu d'un lot de plusieurs heures.
Ce script vit donc dans un environnement séparé et communique par l'entrée et la sortie
standard, en JSON.

Entrée  : {"fichiers": [...], "lat": [...], "lon": [...], "ids": [...]}
Sortie  : un tableau JSON, une ligne par station × instant.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import cfgrib


def indices_plus_proches(axe: np.ndarray, valeurs: np.ndarray) -> np.ndarray:
    """Indice de la maille la plus proche, sans supposer l'axe trié.

    Repris de `aq.features.meteo` : `sel(method="nearest")` échoue ou ment sur un axe non
    monotone, et rabat silencieusement sur la cellule de bord pour un point hors domaine.
    """
    axe = np.asarray(axe, dtype="float64")
    valeurs = np.asarray(valeurs, dtype="float64")
    return np.abs(axe[None, :] - valeurs[:, None]).argmin(axis=1)


def main() -> int:
    entree = json.load(sys.stdin)
    lat = np.asarray(entree["lat"], dtype="float64")
    lon = np.asarray(entree["lon"], dtype="float64")
    ids = entree["ids"]

    morceaux = []
    for chemin in entree["fichiers"]:
        trouve = re.search(r"ifs_(\d{8})_(\d{3})h", Path(chemin).name)
        if not trouve:
            continue
        base = pd.Timestamp(trouve.group(1), tz="UTC")
        instant = base + pd.Timedelta(hours=int(trouve.group(2)))

        # Un même fichier porte plusieurs types de niveaux ; `cfgrib` refuse de les fusionner
        # et rend alors une liste de jeux. On les traite tous plutôt que de prendre le premier.
        # `xarray` n'expose **pas** de `open_datasets` : la fonction qui rend une liste de jeux
        # quand les hypercubes ne se fusionnent pas appartient à `cfgrib`. L'appel fautif était
        # avalé par le `except` ci-dessous et rendait zéro ligne sans jamais dire pourquoi —
        # un piège attrapé seulement en décodant un fichier à la main.
        try:
            jeux = cfgrib.open_datasets(chemin, backend_kwargs={"indexpath": ""})
        except Exception as exc:  # noqa: BLE001
            print(f"décodage {Path(chemin).name} : {type(exc).__name__} {exc}",
                  file=sys.stderr)
            continue

        colonnes = {}
        for d in jeux:
            if "latitude" not in d.coords or "longitude" not in d.coords:
                continue
            lo = d["longitude"].values
            lo = np.where(lo > 180, lo - 360, lo)
            i_lon = indices_plus_proches(lo, lon)
            i_lat = indices_plus_proches(d["latitude"].values, lat)
            for nom, champ in d.data_vars.items():
                valeurs = champ.values
                if valeurs.ndim == 2:
                    colonnes[nom] = valeurs[i_lat, i_lon]
                elif valeurs.ndim == 3 and "isobaricInhPa" in champ.dims:
                    # **Les niveaux de pression arrivent gratuitement** : le regroupement des
                    # plages d'octets les embarque avec les champs de surface. Une version
                    # antérieure indexait `[i_lat, i_lon]` sur un tableau à trois axes et
                    # levait `IndexError` — l'axe des niveaux venant en premier. On les
                    # déplie en une colonne par niveau, nommée en hPa.
                    niveaux = d["isobaricInhPa"].values
                    for k, niveau in enumerate(niveaux):
                        colonnes[f"{nom}{int(niveau)}"] = valeurs[k, i_lat, i_lon]
                # Tout autre rang est ignoré **en le disant** : un champ silencieusement sauté
                # est une variable manquante qui ne s'annonce jamais.
                elif valeurs.ndim != 2:
                    print(f"  ignoré {nom} : rang {valeurs.ndim}, dims {champ.dims}",
                          file=sys.stderr)
        if not colonnes:
            continue
        t = pd.DataFrame(colonnes)
        t.insert(0, "timestamp_utc", instant)
        t.insert(0, "station_id", ids)
        morceaux.append(t)

    if not morceaux:
        print("[]")
        return 0
    tout = pd.concat(morceaux, ignore_index=True)
    # Les unités natives ne sont pas celles du métier : kelvins, joules, mètres de pluie.
    if "t2m" in tout:
        tout["temperature_c"] = tout["t2m"] - 273.15
    if "d2m" in tout:
        tout["point_rosee_c"] = tout["d2m"] - 273.15
    if "ssrd" in tout:
        tout["rayonnement_w_m2"] = tout["ssrd"] / 3600.0
    if "tp" in tout:
        tout["precipitation_mm"] = tout["tp"] * 1000.0
    if {"u10", "v10"} <= set(tout.columns):
        tout["vent_vitesse_m_s"] = np.hypot(tout["u10"], tout["v10"])
        tout["vent_direction_deg"] = (np.degrees(
            np.arctan2(-tout["u10"], -tout["v10"])) + 360.0) % 360.0
    print(tout.to_json(orient="records", date_format="iso"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
