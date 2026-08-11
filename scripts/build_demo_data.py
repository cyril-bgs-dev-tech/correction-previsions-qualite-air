"""Prépare les données compactes de la démo Streamlit.

Usage : python scripts/build_demo_data.py
Sortie : data/demo/*.parquet

**Pourquoi une étape de préparation plutôt qu'une lecture directe.** Streamlit relit ses
données à chaque interaction : sur une carte où l'on change de polluant, la différence
sépare une démo fluide d'une démo poussive.

Chiffres **re-mesurés le 11/08/2026**, les précédents (« 127 Mo → 36 Mo, 2,0 s → 0,1 s »)
datant d'un corpus trois fois plus petit et de trois polluants :

- entrée : quatre CSV MOS, **1,8 Go** au total ;
- sortie : `predictions.parquet`, **295 Mo** pour **28,9 M de lignes**, chargé en **1,70 s**
  et **634 Mo** en mémoire.

Le volume a grossi avec le corpus (flux LCSQA) et l'arrivée de PM10 ; il n'est pas réduit
par un échantillonnage. **C'est un arbitrage, pas un oubli** : raccourcir la fenêtre
allégerait la démo mais la ferait diverger du corpus annoncé dans le dossier, ce qui coûte
plus cher qu'une seconde et demie de chargement — d'autant que `@st.cache_data` ne la paie
qu'une fois par session.

On en profite pour ne garder que ce que l'interface affiche réellement.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

SORTIE = RACINE / "data/demo"
# PM10 entre le 11/08 : le dossier le couvre depuis le 01/08 mais la démo n'en montrait que
# trois sur quatre, parce que `fit_mos.py` le refusait dans son `choices` d'argparse — et
# nulle part ailleurs. Un polluant absent d'une démo ne lève rien : il est simplement absent.
POLLUANTS = ["O3", "NO2", "PM25", "PM10"]


def preparer_predictions() -> pd.DataFrame:
    """Rassemble les sorties MOS des trois polluants en une table unique."""
    blocs = []
    for polluant in POLLUANTS:
        chemin = RACINE / f"reports/mos_{polluant}_J1.csv"
        if not chemin.exists():
            print(f"  {polluant} : absent, ignoré", flush=True)
            continue
        bloc = pd.read_csv(chemin, parse_dates=["timestamp_utc"])
        bloc["polluant"] = polluant
        # Les concentrations tiennent largement dans un flottant simple précision :
        # la mesure elle-même n'a pas trois décimales significatives.
        for c in ("observe", "cams", "corrige"):
            bloc[c] = bloc[c].astype("float32")
        blocs.append(bloc)
        print(f"  {polluant} : {len(bloc):,} lignes", flush=True)
    table = pd.concat(blocs, ignore_index=True)
    table["polluant"] = table["polluant"].astype("category")
    table["station_id"] = table["station_id"].astype("category")
    return table


def resumer_par_station(predictions: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par (station, polluant) : de quoi dessiner la carte sans tout relire."""
    def stats(g: pd.DataFrame) -> pd.Series:
        err_c, err_m = g["cams"] - g["observe"], g["corrige"] - g["observe"]
        return pd.Series({
            "n": len(g),
            "obs_moy": g["observe"].mean(),
            "rmse_cams": np.sqrt((err_c ** 2).mean()),
            "rmse_mos": np.sqrt((err_m ** 2).mean()),
            "biais_cams": err_c.mean(),
            "biais_mos": err_m.mean(),
        })

    resume = (predictions.groupby(["station_id", "polluant"], observed=True)
              .apply(stats, include_groups=False).reset_index())
    resume["gain_pct"] = 100 * (1 - resume["rmse_mos"] / resume["rmse_cams"])

    # **Écarter les couples sans aucune mesure valide.** Le panneau conserve des lignes
    # horaires sans observation : 49 couples (station, polluant) n'en ont pas une seule.
    # Leurs métriques sont toutes NaN — il n'y a rien à évaluer, et les laisser passer
    # fait remonter des « nan » jusqu'à l'écran, sur une carte comme dans un tableau.
    vides = resume["rmse_cams"].isna()
    if vides.any():
        print(f"  {int(vides.sum())} couple(s) (station, polluant) sans mesure valide, "
              "écartés", flush=True)
    return resume[~vides].reset_index(drop=True)


def main() -> int:
    SORTIE.mkdir(parents=True, exist_ok=True)
    print("Préparation des prévisions…", flush=True)
    predictions = preparer_predictions()
    predictions.to_parquet(SORTIE / "predictions.parquet", index=False)

    resume = resumer_par_station(predictions)

    stations = pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "nom", "commune", "lat_wgs84", "lon_wgs84",
                 "altitude", "type_station", "typologie_zone"],
    )
    geo = pd.read_parquet(RACINE / "data/processed/geo_features_metropole.parquet")
    relief = pd.read_parquet(RACINE / "data/processed/relief_features_metropole.parquet")

    contexte = (stations.merge(relief, on="station_id", how="inner")
                .merge(geo, on="station_id", how="inner"))
    contexte.to_parquet(SORTIE / "stations.parquet", index=False)
    resume.to_parquet(SORTIE / "resume_stations.parquet", index=False)

    for nom, chemin in [("cams_benchmark.csv", "reports/cams_benchmark.csv"),
                        ("indice_detection.csv", "reports/indice_detection.csv")]:
        source = RACINE / chemin
        if source.exists():
            pd.read_csv(source).to_parquet(SORTIE / nom.replace(".csv", ".parquet"),
                                           index=False)

    volume = sum(f.stat().st_size for f in SORTIE.glob("*.parquet")) / 1e6
    print(f"\n{len(predictions):,} prévisions · {len(contexte)} stations · "
          f"{volume:.0f} Mo dans {SORTIE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
