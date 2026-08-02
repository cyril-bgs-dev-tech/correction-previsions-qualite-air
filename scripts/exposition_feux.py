#!/usr/bin/env python3
"""Exposition des stations aux feux, conditionnée au vent.

Le premier vrai cas d'usage d'un code écrit il y a des semaines
---------------------------------------------------------------
`exposure.exposition_au_vent` — décroissance exponentielle, secteur au vent en cosinus tronqué,
vent nul traité — est écrite et vérifiée depuis longtemps et n'a **jamais servi**. Le criblage
tenté avec les stations trafic comme mandataires a été écarté à la passe unitaire : **86 % de
valeurs nulles à 1 km**, la densité du réseau interdisant d'atteindre l'échelle visée.

Un feu n'a pas ce défaut. GFAS en donne la **position** (maille 0,1°), la **puissance
radiative** et la **date**. Ce sont de vraies sources ponctuelles, et la géométrie
station→source devient calculable.

Ce que le mécanisme prédit, et donc ce qui le réfuterait
--------------------------------------------------------
Le mode d'échec exhibé par les trois matinées rejouées est la **sous-estimation brutale** :
le 25/07, CAMS annonçait 7,7 µg/m³ là où l'air en portait 51,2. Si une part de ces épisodes
vient de panaches de combustion, l'exposition aux feux amont doit s'y voir — et **seulement
là**. Un gain réparti uniformément sur l'année serait suspect : il signalerait une corrélation
avec la saison, les feux et l'ozone culminant tous deux en été.

D'où le contrôle : on mesure l'exposition **anisotrope** (secteur au vent) *et* son pendant
**isotrope** (tous azimuts). Si seule la seconde compte, ce n'est pas le transport qui parle,
c'est le calendrier.

Trois échelles — 50, 200 et 500 km — parce qu'un panache de combustion voyage loin, et que le
feu ibérique compte autant que le feu local pour l'Occitanie.

Usage : python3 scripts/exposition_feux.py [--scope metropole]
Sortie : data/processed/meteo/feux_{scope}_AAAAMM.parquet
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.harmonize import wind  # noqa: E402
from aq.ingest import stations as st  # noqa: E402

SOURCE = RACINE / "data/raw/gfas"
SORTIE = RACINE / "data/processed/meteo"
LAMBDAS = {"proche": 50_000.0, "moyen": 200_000.0, "loin": 500_000.0}
OUVERTURE = 60.0  # demi-ouverture du secteur au vent : plus large qu'en local, car un panache
                  # à 300 km a divergé et la direction de surface n'est qu'un mandataire.
SEUIL_FRP = 1e-3  # W/m² — en deçà, la maille ne porte pas de feu identifiable


def _rayon_terre_km(lat: np.ndarray) -> tuple[np.ndarray, float]:
    """Facteurs de conversion degré → mètre, à la latitude considérée.

    Un degré de longitude ne vaut pas un degré de latitude, et l'écart atteint 26 % à 45° N.
    Travailler en degrés fabriquerait une anisotropie artificielle **orientée est-ouest** —
    exactement l'axe que ces variables cherchent à mesurer.
    """
    return 111_320.0 * np.cos(np.deg2rad(lat)), 110_540.0


def exposition_un_mois(chemin: Path, stations: pd.DataFrame,
                       meteo: pd.DataFrame) -> pd.DataFrame:
    """Exposition journalière de chaque station aux feux, avec et sans conditionnement au vent."""
    import xarray as xr

    d = xr.open_dataset(chemin)
    frp = d["frpfire"]
    axe_t = "valid_time" if "valid_time" in frp.dims else "time"
    lat_g = frp["latitude"].values
    lon_g = frp["longitude"].values
    # GFAS livre les longitudes en [0, 360] comme CAMS : les ramener sous peine de placer
    # l'Ibérie à 350° et de la déclarer à 30 000 km de Toulouse.
    lon_g = np.where(lon_g > 180, lon_g - 360, lon_g)

    xs = stations["lon_wgs84"].to_numpy()
    ys = stations["lat_wgs84"].to_numpy()
    m_par_deg_lon, m_par_deg_lat = _rayon_terre_km(ys)

    lignes = []
    for i in range(frp.sizes[axe_t]):
        champ = frp.isel({axe_t: i}).values.squeeze()
        jour = pd.Timestamp(frp[axe_t].values[i]).tz_localize("UTC").normalize()
        actifs = np.argwhere(champ > SEUIL_FRP)
        if actifs.size == 0:
            continue
        f_lat = lat_g[actifs[:, 0]]
        f_lon = lon_g[actifs[:, 1]]
        poids = champ[actifs[:, 0], actifs[:, 1]]

        dx = (f_lon[None, :] - xs[:, None]) * m_par_deg_lon[:, None]
        dy = (f_lat[None, :] - ys[:, None]) * m_par_deg_lat
        dist = np.maximum(np.hypot(dx, dy), 1.0)
        # Azimut géographique de la source vue de la station : 0° au nord, sens horaire.
        azimut = (np.degrees(np.arctan2(dx, dy)) + 360.0) % 360.0

        vent = meteo[meteo["jour"] == jour].set_index("station_id")["vent_direction_deg"]
        direction = stations["station_id"].map(vent).to_numpy(dtype="float64")
        angulaire = wind.poids_secteur_au_vent(azimut, direction[:, None],
                                               demi_ouverture_deg=OUVERTURE)
        angulaire = np.where(np.isnan(direction)[:, None], 0.0, angulaire)

        ligne = {"station_id": stations["station_id"].to_numpy(), "jour": jour}
        for nom, lam in LAMBDAS.items():
            decroissance = poids[None, :] * np.exp(-dist / lam)
            ligne[f"feu_vent_{nom}"] = (decroissance * angulaire).sum(axis=1)
            # Le pendant isotrope : sans lui, impossible de distinguer un effet de transport
            # d'une simple corrélation saisonnière entre feux et pollution.
            ligne[f"feu_iso_{nom}"] = decroissance.sum(axis=1)
        lignes.append(pd.DataFrame(ligne))

    if not lignes:
        return pd.DataFrame()
    return pd.concat(lignes, ignore_index=True)


def main(scope: str) -> int:
    ref = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    stations = (ref[(ref["reseau"] == st.RESEAU_OCCITANIE) & ref["active"]] if scope == "occitanie"
                else ref[ref["metropole"] & ref["active"]])
    stations = stations.dropna(subset=["lat_wgs84", "lon_wgs84"]).reset_index(drop=True)
    SORTIE.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(SOURCE.glob("gfas_*.nc"))
    if not fichiers:
        raise SystemExit(f"aucun fichier GFAS dans {SOURCE}")
    print(f"{len(fichiers)} mois GFAS · {len(stations)} stations", flush=True)

    debut = time.time()
    # ⚠️ **Capture TOUS les jetons du nom, jamais le dernier.**
    #
    # Une expression qui ne capture qu'un seul groupe de six chiffres avant l'extension,
    # ancrée sur la fin du nom, perdrait le premier mois d'un fichier regroupé. C'est le
    # défaut qui a coûté **35 % du jeu d'entraînement** au projet dans `fit_mos.py`, et le
    # test `test_aucune_fenetre_deduite_du_nom_de_fichier` le signalait ici sans être
    # corrigé.
    #
    # Le risque n'est pas théorique : le projet a **déjà adopté le regroupement** pour CAMS,
    # afin de tenir sous le plafond de coût par requête. GFAS peut suivre.
    motif = re.compile(r"^gfas_(\d{6}(?:_\d{6})*)\.nc$")
    for n, chemin in enumerate(fichiers, start=1):
        trouve = motif.match(chemin.name)
        if not trouve:
            # **Lever, et non avertir puis sauter.** Un `continue` écarterait silencieusement
            # un fichier, et le journal ne serait relu par personne.
            raise SystemExit(
                f"nom de fichier non conforme : {chemin.name}\n"
                f"Attendu `gfas_AAAAMM.nc`, éventuellement groupé `gfas_AAAAMM_AAAAMM.nc`.")
        jetons = trouve.group(1).split("_")
        if len(jetons) > 1:
            raise SystemExit(
                f"{chemin.name} porte {len(jetons)} mois : {', '.join(jetons)}.\n"
                f"Ce script ne sait traiter qu'un mois par fichier. Il le DIT plutôt que "
                f"d'en garder un seul\nen silence — corriger la boucle avant de poursuivre.")
        mois = jetons[0]
        cible = SORTIE / f"feux_{scope}_{mois}.parquet"
        if cible.exists():
            continue

        era5 = sorted(glob.glob(str(RACINE / f"data/processed/meteo/era5_metropole_{mois}*.parquet")))
        if not era5:
            print(f"  [{n}] {mois} — ERA5 absent, mois sauté", flush=True)
            continue
        m = pd.concat([pd.read_parquet(f, columns=["station_id", "timestamp_utc",
                                                   "vent_direction_deg"]) for f in era5])
        m["jour"] = m["timestamp_utc"].dt.floor("D")
        # Direction **moyenne circulaire** du jour : moyenner des degrés ferait de 359° et 1°
        # une direction sud.
        m = (m.groupby(["station_id", "jour"])["vent_direction_deg"]
              .apply(lambda s: wind.moyenne_directionnelle(s.to_numpy()))
              .reset_index())

        t = exposition_un_mois(chemin, stations, m)
        if t.empty:
            print(f"  [{n}] {mois} — aucun feu au-dessus du seuil", flush=True)
            continue
        provisoire = cible.with_suffix(".parquet.partiel")
        t.to_parquet(provisoire, index=False)
        provisoire.rename(cible)
        part = 100 * (t["feu_vent_moyen"] > 0).mean()
        print(f"  [{n}/{len(fichiers)}] {cible.name} · {len(t):,} lignes · "
              f"exposition non nulle sur {part:.0f} % · {time.time() - debut:.0f}s", flush=True)

    produits = sorted(SORTIE.glob(f"feux_{scope}_*.parquet"))
    print(f"\n{len(produits)} mois écrits · {time.time() - debut:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scope", default="metropole", choices=["metropole", "occitanie"])
    args = p.parse_args()
    raise SystemExit(main(args.scope))
