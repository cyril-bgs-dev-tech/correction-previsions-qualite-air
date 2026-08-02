"""Quand la correction échoue-t-elle ? Erreur ventilée par régime météorologique.

Usage : python scripts/erreur_par_regime_meteo.py [--polluant O3]
Sortie : reports/REGIMES_METEO.md et reports/regimes_meteo_{polluant}.csv

**Un usage de la réanalyse qui est légitime, et il faut dire pourquoi.** ERA5 est une
réanalyse : l'employer comme *entrée* d'un modèle de prévision serait une fuite — elle
décrit un passé que la prévision n'avait pas. L'employer ici en **diagnostic
a posteriori** ne pose aucun problème : on ne prédit rien, on caractérise les conditions
dans lesquelles la correction s'est trouvée bonne ou mauvaise. La distinction tient à
l'usage, pas à la donnée.

**Pourquoi cette ventilation compte plus qu'un RMSE global.** Un modèle qui échoue de
façon diffuse et un modèle qui échoue systématiquement sous inversion hivernale ont le
même RMSE et n'ont pas du tout la même valeur opérationnelle : le second est prévisible,
donc corrigeable — et surtout, on sait quand ne pas lui faire confiance.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval import comparaison as cmp  # noqa: E402

# Régimes définis par la physique de la dispersion, pas par des quantiles arbitraires.
# Une couche limite basse et un vent faible signent la stagnation ; un fort rayonnement
# et une température élevée signent la photochimie.
SEUIL_COUCHE_BASSE = 300.0     # m — sous cette hauteur, la dilution est très réduite
SEUIL_VENT_FAIBLE = 2.0        # m/s — en deçà, le transport horizontal est négligeable
SEUIL_RAYONNEMENT_FORT = 150.0  # W/m² en moyenne journalière


def charger_meteo(mois: list[str]) -> pd.DataFrame:
    blocs = []
    for m in mois:
        chemin = RACINE / f"data/processed/meteo/era5_metropole_{m}.parquet"
        if chemin.exists():
            blocs.append(pd.read_parquet(chemin))
    if not blocs:
        raise SystemExit("Aucun mois ERA5 extrait ne recouvre la période évaluée.")
    return pd.concat(blocs, ignore_index=True)


def qualifier(meteo: pd.DataFrame) -> pd.DataFrame:
    """Attribue un régime à chaque heure-station.

    Les régimes sont **exclusifs et ordonnés** : la stagnation prime, parce que c'est la
    condition qui produit les épisodes. Un jour peut être à la fois peu venté et
    ensoleillé ; le classer en « stagnation » est le choix qui a un sens métier.
    """
    couche_basse = meteo["couche_limite_m"] < SEUIL_COUCHE_BASSE
    vent_faible = meteo["vent_vitesse_m_s"] < SEUIL_VENT_FAIBLE
    ensoleille = meteo["rayonnement_w_m2"] > SEUIL_RAYONNEMENT_FORT
    pluie = meteo["precipitation_mm"] > 0.2

    regime = np.select(
        [couche_basse & vent_faible, pluie, ensoleille, ~vent_faible],
        ["stagnation (couche basse + vent faible)", "précipitations",
         "photochimique (fort rayonnement)", "ventilé"],
        default="intermédiaire",
    )
    return meteo.assign(regime=regime)


def main(polluant: str, horizon: int) -> int:
    predictions = pd.read_csv(RACINE / f"reports/mos_{polluant}_J{horizon}.csv",
                              parse_dates=["timestamp_utc"]).dropna(subset=["observe"])
    mois = sorted(predictions["timestamp_utc"].dt.strftime("%Y%m").unique())
    print(f"{polluant} J+{horizon} · {len(predictions):,} paires · mois {mois}",
          flush=True)

    meteo = charger_meteo(mois)
    colonnes = ["station_id", "timestamp_utc", "couche_limite_m", "vent_vitesse_m_s",
                "rayonnement_w_m2", "precipitation_mm", "temperature_c"]
    jeu = predictions.merge(qualifier(meteo)[colonnes + ["regime"]],
                            on=["station_id", "timestamp_utc"], how="inner")
    print(f"{len(jeu):,} paires appariées à la météo "
          f"({100 * len(jeu) / len(predictions):.0f} %)\n", flush=True)

    lignes = []
    print(f"{'régime':42s} {'n':>9s} {'obs':>6s} {'CAMS':>7s} {'MOS':>7s} {'gain':>8s}")
    for regime, groupe in jeu.groupby("regime"):
        a = cmp.metriques(groupe["observe"], groupe["cams"])
        b = cmp.metriques(groupe["observe"], groupe["corrige"])
        gain = 100 * (1 - b["rmse"] / a["rmse"])
        lignes.append({"regime": regime, "n": len(groupe),
                       "obs_moy": groupe["observe"].mean(),
                       "rmse_cams": a["rmse"], "rmse_mos": b["rmse"],
                       "biais_cams": a["biais"], "biais_mos": b["biais"],
                       "gain_pct": gain})
        print(f"{regime:42s} {len(groupe):>9,} {groupe['observe'].mean():6.1f} "
              f"{a['rmse']:7.2f} {b['rmse']:7.2f} {gain:+7.1f} %", flush=True)

    # La question opérationnelle : le gain tient-il quand la concentration est forte ?
    print("\nCroisement régime × niveau observé :", flush=True)
    haut = jeu["observe"] >= jeu["observe"].quantile(0.90)
    for regime, groupe in jeu[haut].groupby("regime"):
        if len(groupe) < 200:
            continue
        a = cmp.metriques(groupe["observe"], groupe["cams"])
        b = cmp.metriques(groupe["observe"], groupe["corrige"])
        print(f"  décile supérieur · {regime:38s} {len(groupe):>7,} "
              f"gain {100 * (1 - b['rmse'] / a['rmse']):+6.1f} %", flush=True)

    pd.DataFrame(lignes).to_csv(
        RACINE / f"reports/regimes_meteo_{polluant}.csv", index=False)
    print(f"\nÉcrit : regimes_meteo_{polluant}.csv")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
