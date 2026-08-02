#!/usr/bin/env python3
"""Cinq diagnostics sur des données déjà écrites — aucun ajustement, donc parallélisable.

Tout ce qui suit était **disponible depuis le début** et n'avait jamais été regardé. C'est
la différence entre voir et observer : les fichiers existaient, les colonnes aussi.

| | Diagnostic | Ce qu'il répond |
|---|---|---|
| **L1** | importances de variables | les 38 descripteurs de paysage servent-ils tous ? |
| **L2** | le 26/07 station par station | reconstruire le récit exact, après une erreur d'agrégation |
| **L3** | cycle diurne résiduel | un résidu structuré par heure trahit une variable manquante |
| **L4** | stations irrécupérables | lesquelles résistent à toute correction, et qu'ont-elles en commun ? |
| **L5** | dispersion inter-stations par EPCI | borne l'écart de spatialisation sans reproduire la chaîne |

**L2 corrige une erreur réelle.** Le récit « CAMS 49,6 · observation 46,8 · correction 36,6 »
croisait **trois maxima de stations différentes**. Un maximum journalier agrège des lieux :
le comparer à un autre maximum, c'est comparer deux endroits. Toute figure « un jour, trois
barres » doit être **par station**.

Usage : python3 scripts/diagnostics_legers.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))


def l1_importances(polluant: str) -> None:
    """Importances déjà collectées à chaque ajustement — jamais lues jusqu'ici."""
    print("\n=== L1 · Importances de variables ===")
    chemin = RACINE / f"reports/importances_{polluant}.csv"
    if not chemin.exists():
        # Le module les rend dans `ResultatMos.importances` mais rien ne les écrivait.
        print("  aucun fichier d'importances écrit — elles étaient calculées et jetées.")
        print("  → `mos.ajuster_par_stations_exclues` les expose ; il suffit de les sauver.")
        return
    t = pd.read_csv(chemin).sort_values("importance", ascending=False)
    print(t.head(15).to_string(index=False))
    cumul = t["importance"].cumsum()
    n80 = int((cumul <= 0.80).sum()) + 1
    print(f"\n  {n80} variables sur {len(t)} portent 80 % de l'importance.")


def l2_jour_par_station(polluant: str, jour: str) -> None:
    """Le récit d'un jour, station par station — jamais par maxima croisés."""
    print(f"\n=== L2 · {jour}, station par station ===")
    chemin = RACINE / f"reports/rejeu_stations_{polluant}.csv"
    if not chemin.exists():
        print(f"  {chemin.name} absent — produit par rejeu_episode.py (à étendre)")
        return
    d = pd.read_csv(chemin)
    d = d[d["jour"] == jour].sort_values("obs_jour", ascending=False)
    d["err_cams"] = (d["cams_jour"] - d["obs_jour"]).abs()
    d["err_mos"] = (d["corrige"] - d["obs_jour"]).abs()
    d["correction_utile"] = d["err_mos"] < d["err_cams"]
    print(d.to_string(index=False, float_format=lambda x: f"{x:6.1f}"))
    print(f"\n  correction utile sur {int(d['correction_utile'].sum())}/{len(d)} stations")


def l3_cycle_diurne(polluant: str, horizon: int) -> None:
    """Résidu moyen par heure locale — un cycle résiduel trahit une variable manquante."""
    print("\n=== L3 · Cycle diurne du résidu ===")
    d = pd.read_csv(RACINE / f"reports/mos_{polluant}_J{horizon}.csv",
                    parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])
    d["heure"] = d["timestamp_utc"].dt.hour
    t = d.groupby("heure").apply(
        lambda g: pd.Series({
            "biais_cams": (g["cams"] - g["observe"]).mean(),
            "biais_mos": (g["corrige"] - g["observe"]).mean(),
            "obs_moyenne": g["observe"].mean(),
        }), include_groups=False)
    print(t.round(2).to_string())
    amplitude = t["biais_mos"].max() - t["biais_mos"].min()
    print(f"\n  amplitude du biais résiduel sur le cycle : {amplitude:.2f} µg/m³")
    print("  (une amplitude notable signale une variable horaire manquante)")


def l4_stations_irrecuperables(polluant: str, horizon: int) -> None:
    """Stations où la correction n'apporte rien, ou nuit."""
    print("\n=== L4 · Stations irrécupérables ===")
    d = pd.read_csv(RACINE / f"reports/mos_{polluant}_J{horizon}.csv").dropna(
        subset=["observe", "cams", "corrige"])
    t = d.groupby("station_id").apply(
        lambda g: pd.Series({
            "n": len(g),
            "rmse_cams": float(np.sqrt(((g["cams"] - g["observe"]) ** 2).mean())),
            "rmse_mos": float(np.sqrt(((g["corrige"] - g["observe"]) ** 2).mean())),
        }), include_groups=False)
    t = t[t["n"] >= 1000]
    t["gain_pct"] = 100 * (1 - t["rmse_mos"] / t["rmse_cams"])

    pires = t.nsmallest(10, "gain_pct")
    print(f"  {len(t)} stations · gain médian {t['gain_pct'].median():+.1f} % · "
          f"{int((t['gain_pct'] < 0).sum())} station(s) où la correction NUIT")
    print("\n  Les dix pires :")
    print(pires.round(2).to_string())

    stations = pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "type_station", "altitude", "typologie_zone", "commune"])
    fusion = pires.merge(stations, on="station_id", how="left")
    if not fusion.empty:
        print(f"\n  Leur profil : altitude médiane {fusion['altitude'].median():.0f} m "
              f"(contre {stations['altitude'].median():.0f} m sur l'ensemble)")
        print(f"  types : {fusion['type_station'].value_counts().to_dict()}")
        print(f"  zones : {fusion['typologie_zone'].value_counts().to_dict()}")


def l5_dispersion_epci(polluant: str, horizon: int) -> None:
    """Écart entre stations d'un même EPCI — borne l'erreur de spatialisation."""
    print("\n=== L5 · Dispersion inter-stations, même commune ===")
    d = pd.read_csv(RACINE / f"reports/mos_{polluant}_J{horizon}.csv",
                    parse_dates=["timestamp_utc"]).dropna(subset=["observe"])
    stations = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                               columns=["station_id", "commune"])
    d = d.merge(stations, on="station_id")
    d["jour"] = d["timestamp_utc"].dt.floor("D")

    # Communes portant au moins deux stations : leur écart mesure ce qu'une valeur
    # unique par zone ne peut pas représenter.
    par_jour = d.groupby(["commune", "jour"])["observe"].agg(["mean", "std", "count"])
    multi = par_jour[par_jour["count"] >= 2].dropna()
    if multi.empty:
        print("  aucune commune avec deux stations simultanées")
        return
    print(f"  {multi.index.get_level_values(0).nunique()} communes à ≥2 stations · "
          f"{len(multi):,} jours-commune")
    print(f"  écart-type intra-commune : médiane {multi['std'].median():.2f} µg/m³ · "
          f"90e centile {multi['std'].quantile(0.9):.2f}")
    print("  → c'est le plancher d'erreur qu'une valeur unique par zone ne peut pas battre.")


def main(polluant: str, horizon: int, jour: str) -> int:
    print(f"Diagnostics légers · {polluant} J+{horizon}")
    for fonction, args in (
        (l1_importances, (polluant,)),
        (l2_jour_par_station, (polluant, jour)),
        (l3_cycle_diurne, (polluant, horizon)),
        (l4_stations_irrecuperables, (polluant, horizon)),
        (l5_dispersion_epci, (polluant, horizon)),
    ):
        try:
            fonction(*args)
        except Exception as erreur:  # noqa: BLE001 — un diagnostic raté n'arrête pas les autres
            print(f"\n  ⚠️ {fonction.__name__} : {type(erreur).__name__}: {erreur}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--jour", default="2026-07-26")
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.jour))
