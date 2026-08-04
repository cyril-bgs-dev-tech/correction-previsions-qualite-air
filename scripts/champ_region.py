#!/usr/bin/env python3
"""Le champ spatialisé sur une région — propagation, incertitude, correction.

Pourquoi ce script, et pourquoi il n'interpole rien
-----------------------------------------------------
Les pages du projet montrent des **points de station**. On voit *où* la correction gagne,
jamais *comment un panache traverse la région*. La demande — voir la diffusion en intensité
spatiale, pas seulement aux stations — a une réponse honnête et une réponse fragile.

La fragile serait d'interpoler les valeurs des 60 stations d'Occitanie : une régression
spatiale calée sur 60 points ne tient pas à l'échelle de la rue, et le projet a **décidé de
ne pas spatialiser** pour cette raison, décision confirmée par deux relectures externes.

La réponse honnête : **le champ existe déjà**. `data/raw/cams_prevision/` conserve
**9 035 grilles** au pas de 0,1° sur la France, dont on n'extrayait que 476 points. Afficher
ce champ n'est pas une interpolation — c'est cesser de jeter 99,7 % de ce qu'on a téléchargé.

Trois couches, trois natures
------------------------------
| couche | ce qu'elle montre | provenance |
|---|---|---|
| `cams` | la **propagation** — advection, accumulation, panaches | grille brute, telle quelle |
| `biais` | la **correction spatiale**, positive là où le modèle sous-estime | krigeage du biais récent, évalué **aux mailles** |
| `corrige` | `cams + biais` | la chaîne de correction, appliquée partout |

⚠️ **Ce que ce champ N'EST PAS.** Ce n'est pas notre modèle appris : celui-ci exige des
descripteurs de terrain, de paysage et de typologie **à chaque maille**, qui ne sont
calculés qu'aux stations. C'est la chaîne de krigeage — celle de la famille PREV'AIR —
appliquée au champ. La distinction doit rester lisible sur la page.

⚠️ **La résolution est celle du modèle : 0,1°, soit ~8 × 11 km.** On voit un panache
traverser l'Occitanie, jamais une rue. Les cartes fines d'Atmo viennent d'un modèle de
dispersion nourri d'un inventaire d'émissions routières — autre objet, autre métier.

Les longitudes se replient
----------------------------
La grille CAMS porte les longitudes en **0-360°** : la partie ouest de l'Occitanie apparaît
vers 359,7°. Sans repli, la région sort coupée en deux et la carte est fausse sans lever.

Usage  : python3 scripts/champ_region.py --polluant O3 --region 76
Régions : 76 Occitanie · 75 Nouvelle-Aquitaine · 84 Auvergne-Rhône-Alpes · etc.
Sortie : data/processed/champs/champ_<region>_<polluant>.npz
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from cible_journaliere import GRANDEUR_PAR_POLLUANT  # noqa: E402

SORTIE = RACINE / "data/processed/champs"
COURT = {"O3": "o3", "NO2": "no2", "PM10": "pm10", "PM25": "pm25"}
VARIABLE = {"O3": "o3_conc", "NO2": "no2_conc", "PM10": "pm10_conc",
            "PM25": "pm2p5_conc"}
MARGE = 0.30           # degrés — pour que le contour régional ne soit pas rasant
DECALAGE = 2                 # jours — rien de plus récent que la fin de J−2
KRIG = dict(fenetre=30, rayon=200.0, p=1.0)


def emprise_region(code: str) -> tuple[dict, str]:
    """Boîte englobante et nom d'une région, **lus dans le référentiel**.

    Coder une emprise en dur pour chaque région ferait diverger le tracé du rattachement
    dès la première correction. Elle se déduit du même contour que celui affiché.
    """
    from pages_regions import SOURCE_REGIONS, ardoise  # noqa: PLC0415

    # « france » : l'emprise du domaine CAMS lui-même, sans découpe régionale.
    if str(code).lower() in ("france", "fr", "0"):
        return dict(lon=(-5.05, 10.05), lat=(41.00, 52.00)), "france"

    brut = json.loads(SOURCE_REGIONS.read_text(encoding="utf-8"))
    f = next((x for x in brut["features"] if x["properties"]["code"] == code), None)
    if f is None:
        dispo = ", ".join(f'{x["properties"]["code"]} {x["properties"]["nom"]}'
                          for x in brut["features"])
        raise SystemExit(f"région « {code} » inconnue. Disponibles : {dispo}")
    g = f["geometry"]
    anneaux = (g["coordinates"] if g["type"] == "Polygon"
               else [a for poly in g["coordinates"] for a in poly])
    pts = np.vstack([np.asarray(a, dtype="float64") for a in anneaux if len(a) >= 4])
    # Écarter l'outre-mer d'une région qui en porterait : on garde la métropole.
    pts = pts[(pts[:, 0] > -6) & (pts[:, 0] < 10) & (pts[:, 1] > 41) & (pts[:, 1] < 52)]
    boite = dict(lon=(float(pts[:, 0].min()) - MARGE, float(pts[:, 0].max()) + MARGE),
                 lat=(float(pts[:, 1].min()) - MARGE, float(pts[:, 1].max()) + MARGE))
    return boite, ardoise(f["properties"]["nom"])


def _replier(lon: np.ndarray) -> np.ndarray:
    """0-360° → −180-180°. Sans cela l'ouest de la région part à 359,7°."""
    return np.where(lon > 180.0, lon - 360.0, lon)


def agreger_jour(cube: np.ndarray, grandeur: str) -> np.ndarray:
    """Des 24 heures d'une journée à la grandeur journalière, maille par maille."""
    if grandeur == "max_8h":
        # Moyenne glissante 8 h puis maximum — la grandeur réglementaire de l'ozone.
        n = cube.shape[0]
        if n < 8:
            return np.nanmax(cube, axis=0)
        vues = np.lib.stride_tricks.sliding_window_view(cube, 8, axis=0)
        return np.nanmax(np.nanmean(vues, axis=-1), axis=0)
    if grandeur == "max_horaire":
        return np.nanmax(cube, axis=0)
    return np.nanmean(cube, axis=0)


def lire_champs(polluant: str, debut: str, fin: str, boite: dict,
                pas: int = 1) -> tuple:
    """Lit les grilles jour par jour, restreintes à l'Occitanie et à l'échéance J0."""
    import xarray as xr

    court, var = COURT[polluant], VARIABLE[polluant]
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    fichiers = sorted(glob.glob(str(
        RACINE / f"data/raw/cams_prevision/cams_prevision_{court}_*/*.nc")))
    motif = re.compile(r"(\d{4}-\d{2}-\d{2})\.nc$")
    par_jour = {}
    for f in fichiers:
        m = motif.search(f)
        if m and debut <= m.group(1) <= fin:
            par_jour.setdefault(m.group(1), f)     # un fichier par jour, le premier vu
    if not par_jour:
        raise SystemExit(f"aucune grille {polluant} entre {debut} et {fin}")

    jours = sorted(par_jour)
    lat = lon = None
    ilat = ilon = ordre = None
    cubes = []
    t0 = time.time()
    for k, j in enumerate(jours):
        d = xr.open_dataset(par_jour[j])
        if lat is None:
            la = d["latitude"].values
            lo = _replier(d["longitude"].values)
            ilat = np.flatnonzero((la >= boite["lat"][0]) & (la <= boite["lat"][1]))
            ilon = np.flatnonzero((lo >= boite["lon"][0]) & (lo <= boite["lon"][1]))
            if len(ilat) < 5 or len(ilon) < 5:
                raise SystemExit(f"emprise vide : {len(ilat)} × {len(ilon)} mailles")
            ordre = np.argsort(lo[ilon])           # remettre l'ouest à gauche
            # ⚠️ Sous-échantillonnage pour la vue nationale : 16 500 mailles pèsent
            # **92 Mo** par polluant, soit 45 à 80 Mo d'atlas pour quatre — impubliable.
            # À l'échelle du pays on lit des motifs synoptiques, pas des mailles : un pas
            # de 2 (0,2° ≈ 16 × 22 km) divise le poids par quatre sans rien perdre du
            # phénomène montré. Une région garde le pas natif.
            if pas > 1:
                ilat, ordre = ilat[::pas], ordre[::pas]
            lat, lon = la[ilat], lo[ilon][ordre]
        t = d["time"].values
        garde = np.flatnonzero((t >= 1) & (t <= 24))
        # **Compter le reçu contre le demandé** : une journée fait 24 échéances.
        if len(garde) != 24:
            print(f"  ⚠️ {j} : {len(garde)} échéances sur 24 — jour ignoré", flush=True)
            d.close()
            continue
        a = d[var].values[garde][:, 0][:, ilat][:, :, ilon][:, :, ordre]
        cubes.append((j, agreger_jour(a, grandeur).astype("float32")))
        d.close()
        if (k + 1) % 120 == 0:
            print(f"  {k + 1}/{len(jours)} jours · {time.time() - t0:.0f}s", flush=True)
    if not cubes:
        raise SystemExit("aucun jour exploitable")
    return ([c[0] for c in cubes], lat, lon,
            np.stack([c[1] for c in cubes]))


def champ_biais(jours: list[str], lat: np.ndarray, lon: np.ndarray,
                polluant: str) -> np.ndarray:
    """Krigeage du biais récent des stations, évalué **à chaque maille**.

    C'est la famille PREV'AIR étendue au champ : le biais observé aux stations sur les
    30 derniers jours (décalé de 2, donc sans fuite) est interpolé par l'inverse de la
    distance vers chaque point de grille.
    """
    from pages_soutenance import charger  # noqa: PLC0415

    d = charger(polluant, 1)
    if d is None:
        raise SystemExit(f"pas de prédictions {polluant} — lancer production_reelle.py")
    d = d.copy()
    d["jour"] = pd.to_datetime(d["jour"])
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "lat_wgs84", "lon_wgs84", "type_station"]
                         ).drop_duplicates("station_id")
    d = d.merge(st, on="station_id", how="inner").dropna(subset=["lat_wgs84"])
    # ⚠️ **Kriger le biais des seules stations de FOND**, et c'est une nécessité, pas un
    # raffinement. Mesuré le 04/08 : la typologie explique **57 % de la variance du biais
    # entre stations sur NO₂** — +10,24 µg/m³ en fond contre **+27,58 en trafic**. Le biais
    # est une propriété du **type de site**, pas du lieu ; l'interpoler géographiquement
    # étalerait une correction de station trafic sur la campagne, où le modèle n'a pas ce
    # défaut. Sur O₃ la typologie n'explique que 1 % : le champ y est légitimement lisse.
    #
    # C'est aussi ce que le droit demande : l'arrêté du 10 juillet 2020 exclut les mailles
    # de **proximité routière** de l'indice, la représentativité exigée étant celle du fond.
    avant = d["station_id"].nunique()
    d = d[d["type_station"].astype(str).str.lower() == "background"]
    if d["station_id"].nunique() < 10:
        raise SystemExit(f"{d['station_id'].nunique()} stations de fond seulement — "
                         f"krigeage non fiable")
    print(f"  krigeage sur {d['station_id'].nunique()} stations de FOND "
          f"(sur {avant}) — trafic et industriel écartés", flush=True)
    d["_b"] = d["valeur"].to_numpy() - d["cams"].to_numpy()

    ids = np.sort(d["station_id"].unique())
    piv = d.pivot_table(index="jour", columns="station_id", values="_b",
                        aggfunc="mean").reindex(columns=ids)
    piv = piv.reindex(pd.date_range(piv.index.min(), piv.index.max(), freq="D"))
    roul = piv.shift(DECALAGE).rolling(
        KRIG["fenetre"], min_periods=KRIG["fenetre"] // 3).mean()

    pos = st.set_index("station_id").reindex(ids)
    # distances maille → station, en km (approximation locale suffisante à 0,1°)
    la = np.repeat(lat, len(lon))
    lo = np.tile(lon, len(lat))
    dy = (la[:, None] - pos["lat_wgs84"].to_numpy()[None, :]) * 111.0
    dx = ((lo[:, None] - pos["lon_wgs84"].to_numpy()[None, :]) * 111.0
          * np.cos(np.radians(la[:, None])))
    dist = np.hypot(dx, dy)
    with np.errstate(divide="ignore"):
        poids = np.where(dist <= KRIG["rayon"],
                         1.0 / np.maximum(dist, 0.5) ** KRIG["p"], 0.0)

    B = roul.reindex(pd.DatetimeIndex(jours)).to_numpy(dtype="float64")
    valide = np.isfinite(B)
    num = np.nan_to_num(B) @ poids.T
    den = valide.astype(float) @ poids.T
    with np.errstate(invalid="ignore", divide="ignore"):
        champ = np.where(den > 0, num / den, np.nan)
    return champ.reshape(len(jours), len(lat), len(lon)).astype("float32")


def main(polluant: str, debut: str, fin: str, region: str) -> int:
    depart = time.time()
    boite, ardoise_reg = emprise_region(region)
    print(f"région {region} · emprise lon {boite['lon'][0]:.2f}→{boite['lon'][1]:.2f} "
          f"· lat {boite['lat'][0]:.2f}→{boite['lat'][1]:.2f}", flush=True)
    pas = 2 if ardoise_reg == "france" else 1
    jours, lat, lon, cams = lire_champs(polluant, debut, fin, boite, pas)
    print(f"{polluant} · {len(jours)} jours · grille {len(lat)} × {len(lon)} "
          f"= {len(lat) * len(lon):,} mailles", flush=True)
    biais = champ_biais(jours, lat, lon, polluant)
    corrige = np.clip(cams + np.nan_to_num(biais), 0, None).astype("float32")

    SORTIE.mkdir(parents=True, exist_ok=True)
    f = SORTIE / f"champ_{ardoise_reg}_{polluant}.npz"
    # ⚠️ `np.savez_compressed` **ajoute** « .npz » si le nom n'y finit pas : un provisoire
    # nommé « .npz.partiel » part sur le disque sous « .npz.partiel.npz », et le renommage
    # échoue sur un fichier absent. Le provisoire doit donc lui aussi finir par « .npz ».
    prov = SORTIE / f"champ_{ardoise_reg}_{polluant}_partiel.npz"
    np.savez_compressed(prov, jours=np.array(jours), lat=lat, lon=lon,
                        cams=cams, biais=biais, corrige=corrige)
    prov.replace(f)

    for nom, a in (("CAMS brut", cams), ("biais krigé", biais), ("corrigé", corrige)):
        v = a[np.isfinite(a)]
        print(f"  {nom:14s} médiane {np.median(v):7.2f} · p95 {np.percentile(v, 95):7.2f} "
              f"· min {v.min():8.2f} · max {v.max():7.2f} · couverture "
              f"{100 * np.isfinite(a).mean():5.1f} %")
    print(f"\n  ⚠️ Résolution 0,1° ≈ 8 × 11 km : un panache régional, jamais une rue.")
    print(f"  ⚠️ Le champ corrigé est le **krigeage** appliqué à la grille, PAS notre")
    print(f"     modèle appris — celui-ci exige des descripteurs de site à chaque maille.")
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {f.stat().st_size / 1e6:.1f} Mo · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--debut", default="2025-01-01")
    a.add_argument("--fin", default="2026-07-31")
    a.add_argument("--region", default="76", help="76 Occitanie · 75 Nouvelle-Aquitaine")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.debut, n.fin, n.region))
