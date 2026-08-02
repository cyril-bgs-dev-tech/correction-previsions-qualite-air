#!/usr/bin/env python3
"""Propriétés de sol SoilGrids autour des stations — un bloc par variable, zéro octet stocké.

Pourquoi ces variables-là, et pas d'autres
------------------------------------------
Le projet a déjà mesuré qu'un bloc statique de vingt-huit variables corrélées (le paysage)
**coûte** 1,9 %. Une seconde famille statique n'est donc admissible que si chaque variable
porte un **mécanisme nommé que CAMS ne représente pas à huit kilomètres**. Six retenues,
deux mécanismes :

* **érodabilité éolienne** — ``sand`` (fraction érodable), ``clay`` (cohésion), ``cfvo``
  (fragments grossiers, qui pavent la surface et la protègent), ``bdod`` (densité
  apparente). Mécanisme : la fraction crustale des PM10 et PM2,5.
* **volatilisation ammoniacale** — ``phh2o`` (un sol basique libère le NH₃ des engrais),
  ``soc`` (matière organique). Mécanisme : le nitrate d'ammonium, PM secondaires, dont
  l'inventaire CAMS-REG répartit spatialement par proxy agricole grossier.

Deux mesures ont dicté la forme finale
--------------------------------------
**1. La valeur au point n'existe pas, et c'est une propriété du jeu, pas un défaut.**
SoilGrids masque le bâti, la roche et l'eau. Sous les stations de qualité de l'air —
urbaines par construction — le pixel est vide **78 % du temps**, alors que l'emprise France
est renseignée à 70 %. Vérifié en confrontant l'indexation d'un bloc à ``src.sample`` :
9 valeurs sur 9 identiques, donc l'absence est dans la donnée. La valeur au point est donc
abandonnée. Ce n'est pas une perte : l'érosion éolienne dépend du sol **autour** du
récepteur, pas de celui qui est sous le capteur — la moyenne de voisinage était déjà la
grandeur juste.

**2. On lit un bloc, jamais 813 points.** Première version : une fenêtre de 5 km par
station, descripteur ouvert une fois. Mesuré 0,16 s/station, soit 8 min pour le lot —
acceptable en apparence. En réalité la couverture s'effondrait à **23 %** en fin de lot
alors qu'elle valait 95 % en lecture fraîche : la source distante se dégradait sous le
nombre d'accès, en rendant du *nodata* sans lever la moindre erreur. L'emprise France
entière fait 3970 × 4049 pixels à 250 m, soit **32 Mo lus en 7 s**. Un bloc par variable,
puis indexation en mémoire — la règle 2 du projet, que la première version avait re-violée.

Usage : python3 scripts/extraire_sol.py
Sortie : data/processed/sol_features_metropole.parquet
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif,.vrt")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyproj  # noqa: E402
import rasterio  # noqa: E402
from rasterio.windows import from_bounds  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.ingest.controle import (  # noqa: E402
    ControleEchec,
    exiger_colonnes,
    exiger_lignes,
    exiger_variation,
    resume_chargement,
)

# SoilGrids est diffusé en Goode homolosine interrompue — on projette les stations vers
# cette grille plutôt que de reprojeter les rasters. La France tient dans un seul lobe.
IGH = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"
BASE = "https://files.isric.org/soilgrids/latest/data"
RESOLUTION_M = 250

# nom → (unité, facteur de conversion depuis l'entier stocké)
VARIABLES = {
    "sand": ("g/kg", 1.0),
    "clay": ("g/kg", 1.0),
    "cfvo": ("cm3/dm3", 10.0),
    "bdod": ("kg/dm3", 100.0),
    "phh2o": ("pH", 10.0),
    "soc": ("g/kg", 10.0),
}
# Deux échelles seulement. 5 km est l'emprise d'une émission surfacique locale, 20 km le
# fetch d'un épisode d'érosion. Pas de troisième : c'est la multiplication des rayons
# corrélés qui a coulé le bloc paysage.
RAYONS_M = [5000, 20000]
MARGE_M = max(RAYONS_M) + 2000


def stations() -> pd.DataFrame:
    """Les stations de métropole, avec leurs coordonnées en Goode homolosine."""
    t = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    exiger_colonnes(t, ["station_id", "lat_wgs84", "lon_wgs84", "metropole"], "stations")
    t = t[t["metropole"].fillna(False)].drop_duplicates("station_id").copy()
    exiger_lignes(t, 400, "stations de métropole")
    if t[["lat_wgs84", "lon_wgs84"]].isna().any().any():
        raise ControleEchec("des stations n'ont pas de coordonnées — la projection serait "
                            "silencieusement fausse pour elles")
    vers = pyproj.Transformer.from_crs("EPSG:4326", IGH, always_xy=True)
    t["igh_x"], t["igh_y"] = vers.transform(t["lon_wgs84"].to_numpy(),
                                            t["lat_wgs84"].to_numpy())
    return t[["station_id", "igh_x", "igh_y"]].reset_index(drop=True)


def bloc(var: str, st: pd.DataFrame) -> tuple[np.ndarray, object]:
    """Charge l'emprise France entière d'une variable — un seul accès distant."""
    url = f"/vsicurl/{BASE}/{var}/{var}_0-5cm_mean.vrt"
    with rasterio.open(url) as src:
        fen = from_bounds(st["igh_x"].min() - MARGE_M, st["igh_y"].min() - MARGE_M,
                          st["igh_x"].max() + MARGE_M, st["igh_y"].max() + MARGE_M,
                          src.transform).round_offsets().round_lengths()
        brut = src.read(1, window=fen)
        transformation = src.window_transform(fen)
        sansval = src.nodata
    a = brut.astype("float32")
    a[a == sansval] = np.nan
    valides = float(np.isfinite(a).mean())
    if valides < 0.4:
        raise ControleEchec(
            f"{var} : {valides:.1%} de l'emprise renseignée — un bloc majoritairement vide "
            "signale une lecture qui a échoué en silence, pas un masque de sol")
    return a, transformation


def moyennes(a: np.ndarray, transformation, st: pd.DataFrame,
             rayon_m: int) -> tuple[np.ndarray, np.ndarray]:
    """Moyenne du disque de rayon donné autour de chaque station, et sa couverture.

    Le disque, pas le carré : un carré de 20 km privilégie les diagonales de 41 % en
    distance, ce qui n'a aucun sens pour une émission qui se dilue radialement.
    """
    inv = ~transformation
    demi = int(round(rayon_m / RESOLUTION_M))
    dy, dx = np.ogrid[-demi:demi + 1, -demi:demi + 1]
    masque = (dx**2 + dy**2) <= demi**2
    hauteur, largeur = a.shape
    val = np.full(len(st), np.nan, dtype="float64")
    couv = np.zeros(len(st), dtype="float64")
    for i, (x, y) in enumerate(zip(st["igh_x"], st["igh_y"])):
        c, r = inv * (x, y)
        c, r = int(c), int(r)
        r0, r1 = max(r - demi, 0), min(r + demi + 1, hauteur)
        c0, c1 = max(c - demi, 0), min(c + demi + 1, largeur)
        if r1 <= r0 or c1 <= c0:
            continue
        vue = a[r0:r1, c0:c1]
        m = masque[r0 - (r - demi):r1 - (r - demi), c0 - (c - demi):c1 - (c - demi)]
        pris = vue[m]
        fini = np.isfinite(pris)
        couv[i] = float(fini.mean()) if pris.size else 0.0
        if fini.any():
            val[i] = float(pris[fini].mean())
    return val, couv


def main() -> int:
    depart = time.time()
    st = stations()
    print(f"{len(st)} stations · rayons {RAYONS_M} m · {len(VARIABLES) + 1} variables lues",
          flush=True)

    out = pd.DataFrame({"station_id": st["station_id"]})
    blocs = {}
    for var, (unite, facteur) in VARIABLES.items():
        t0 = time.time()
        a, tr = bloc(var, st)
        blocs[var] = (a, tr)
        for rayon in RAYONS_M:
            val, couv = moyennes(a, tr, st, rayon)
            nom = f"sol_{var}_{rayon // 1000}km"
            out[nom] = val / facteur
            renseignees = float(np.isfinite(val).mean())
            if renseignees < 0.95:
                raise ControleEchec(
                    f"{nom} : {renseignees:.1%} des stations renseignées, 95 % attendus — "
                    "à cette échelle le masque du bâti ne peut pas tout expliquer")
        print(f"  {var:6} {unite:8} bloc {a.shape} en {time.time() - t0:4.0f} s · "
              f"médiane 5 km {np.nanmedian(out[f'sol_{var}_5km']):8.2f} · "
              f"stations renseignées {np.isfinite(out[f'sol_{var}_5km']).mean():5.1%}",
              flush=True)

    # CONTRÔLE DE CONFORMITÉ. Les trois fractions texturales somment à 1000 g/kg par
    # construction. Si l'échelle lue n'était pas celle supposée, la somme le dirait.
    a_silt, tr_silt = bloc("silt", st)
    silt_5, _ = moyennes(a_silt, tr_silt, st, 5000)
    somme = out["sol_sand_5km"] + out["sol_clay_5km"] + silt_5
    ecart = float(np.nanmax(np.abs(somme - 1000)))
    if ecart > 5:
        raise ControleEchec(
            f"sable + limon + argile s'écarte de 1000 g/kg de {ecart:.0f} au pire — "
            "le facteur d'échelle SoilGrids n'est pas celui supposé")
    print(f"  conformité texturale : écart max à 1000 g/kg = {ecart:.1f}", flush=True)

    exiger_variation(out, [c for c in out.columns if c != "station_id"], "sol")
    exiger_lignes(out, 400, "sol")

    # Règle 4 : nom provisoire, vérification, puis renommage.
    final = RACINE / "data/processed/sol_features_metropole.parquet"
    provisoire = final.with_suffix(".parquet.partiel")
    out.to_parquet(provisoire, index=False)
    relu = pd.read_parquet(provisoire)
    exiger_colonnes(relu, list(out.columns), "sol relu")
    exiger_lignes(relu, 400, "sol relu")
    provisoire.replace(final)

    print(resume_chargement(out, "sol"))
    print(f"Écrit : {final.relative_to(RACINE)} · {time.time() - depart:.0f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
