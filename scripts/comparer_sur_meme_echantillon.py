"""Compare tous les modèles sur **exactement** le même échantillon.

Usage : python scripts/comparer_sur_meme_echantillon.py [--polluant O3] [--horizon 1]
Sortie : reports/COMPARAISON_COMMUNE.md et reports/comparaison_commune.csv

**Pourquoi ce script existe.** Les baselines observationnelles avaient été mesurées sur
l'Occitanie 2023-2024, le benchmark CAMS et le MOS sur trois mois de 2024 en métropole.
Les présenter comme une progression — persistance, puis climatologie, puis CAMS, puis
correction — laissait croire à une comparaison qui n'en était pas une : ni les mêmes
stations, ni la même période, ni la même région.

Une relecture adverse l'a relevé. Ici, tous les modèles sont évalués sur l'**intersection
exacte** des couples (station, heure) où la prévision corrigée existe : mêmes stations,
mêmes heures, même polluant, même horizon.

Les baselines retenues sont celles qu'une AASQA considérerait effectivement :

- **persistance** — la valeur observée 24 h plus tôt. C'est le réflexe naturel, et le
  premier concurrent honnête d'un modèle de prévision ;
- **climatologie horaire** — moyenne par (station, mois, heure) apprise sur les années
  antérieures. Elle capte le cycle diurne et la saison sans rien prévoir du tout ;
- **CAMS brut**, puis **CAMS corrigé**.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval import comparaison as cmp  # noqa: E402


def climatologie(historique: pd.DataFrame, cible: pd.DataFrame) -> np.ndarray:
    """Moyenne par (station, mois, heure), apprise **strictement avant** la cible.

    Le repli par (mois, heure) toutes stations confondues sert aux stations absentes de
    l'historique : sans lui, elles seraient écartées de la comparaison, ce qui
    avantagerait la climatologie en lui retirant les cas difficiles.
    """
    h = historique.assign(
        mois=historique["timestamp_utc"].dt.month,
        heure=historique["timestamp_utc"].dt.hour,
    )
    par_station = h.groupby(["station_id", "mois", "heure"])["valeur"].mean()
    par_defaut = h.groupby(["mois", "heure"])["valeur"].mean()

    c = cible.assign(mois=cible["timestamp_utc"].dt.month,
                     heure=cible["timestamp_utc"].dt.hour)
    cles = list(zip(c["station_id"], c["mois"], c["heure"]))
    valeurs = par_station.reindex(cles).to_numpy()
    replis = par_defaut.reindex(list(zip(c["mois"], c["heure"]))).to_numpy()
    return np.where(np.isnan(valeurs), replis, valeurs)


def main(polluant: str, horizon: int) -> int:
    chemin = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    if not chemin.exists():
        raise SystemExit(f"{chemin.name} absent — lancer fit_mos.py d'abord.")

    mos = pd.read_csv(chemin, parse_dates=["timestamp_utc"])
    mos = mos.dropna(subset=["observe"])
    debut, fin = mos["timestamp_utc"].min(), mos["timestamp_utc"].max()
    stations = set(mos["station_id"])

    print(f"{polluant} J+{horizon} · {len(mos):,} couples · {len(stations)} stations · "
          f"{debut.date()} → {fin.date()}", flush=True)

    # Observations nécessaires aux baselines : la fenêtre évaluée, plus l'historique
    # antérieur pour la climatologie.
    panneau = RACINE / "data/processed/panel_metropole_ds2.parquet"
    obs = pd.read_parquet(
        panneau,
        filters=[("polluant", "==", polluant),
                 ("timestamp_utc", "<=", fin)],
        columns=["station_id", "timestamp_utc", "valeur"],
    )
    obs = obs[obs["station_id"].isin(stations)].dropna(subset=["valeur"])

    # Persistance : la valeur observée 24 h avant l'échéance.
    decale = obs.assign(timestamp_utc=obs["timestamp_utc"] + pd.Timedelta(hours=24))
    decale = decale.rename(columns={"valeur": "persistance"})
    jeu = mos.merge(decale, on=["station_id", "timestamp_utc"], how="left")

    # Climatologie : apprise strictement avant le début de la fenêtre évaluée.
    historique = obs[obs["timestamp_utc"] < debut]
    print(f"historique de climatologie : {len(historique):,} observations "
          f"antérieures au {debut.date()}", flush=True)
    jeu["climatologie"] = climatologie(historique, jeu)

    modeles = {
        "Persistance (J−1, même heure)": "persistance",
        "Climatologie horaire": "climatologie",
        "CAMS brut": "cams",
        "CAMS corrigé (MOS)": "corrige",
    }

    # **L'intersection est la clé.** On ne garde que les lignes où TOUS les modèles ont
    # une valeur : sinon chacun serait jugé sur un échantillon différent, et la
    # comparaison ne voudrait rien dire.
    complet = jeu.dropna(subset=list(modeles.values()) + ["observe"])
    print(f"intersection commune à tous les modèles : {len(complet):,} couples "
          f"({100 * len(complet) / len(jeu):.0f} % de l'échantillon)\n", flush=True)

    lignes = []
    print(f"{'modèle':32s} {'RMSE':>7s} {'MAE':>7s} {'biais':>8s} {'R²':>8s}")
    for nom, colonne in modeles.items():
        m = cmp.metriques(complet["observe"], complet[colonne])
        lignes.append({"modele": nom, **m})
        print(f"{nom:32s} {m['rmse']:7.2f} {m['mae']:7.2f} {m['biais']:+8.2f} "
              f"{m['r2']:+8.3f}")

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / "reports/comparaison_commune.csv", index=False)

    meilleure_baseline = table.iloc[:2]["rmse"].min()
    mos_rmse = table.iloc[3]["rmse"]
    print(f"\n→ la correction retire {100 * (1 - mos_rmse / meilleure_baseline):+.1f} % "
          f"de RMSE à la meilleure baseline observationnelle", flush=True)
    print(f"→ et {100 * (1 - mos_rmse / table.iloc[2]['rmse']):+.1f} % à CAMS brut",
          flush=True)
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
