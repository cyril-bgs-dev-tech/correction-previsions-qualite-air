"""Mesure la performance des prévisions CAMS contre les observations en station.

Usage : python scripts/benchmark_cams.py [--scope metropole] [--horizons 1,2,3]
Sorties : reports/CAMS_BENCHMARK.md et reports/cams_benchmark.csv

C'est la **barre à battre** du projet : toute amélioration proposée se mesure contre
ces chiffres, jamais contre une moyenne ou une persistance.

Trois précautions de méthode, chacune capable de fausser la conclusion :

- **Prévisions, pas réanalyse.** La réanalyse CAMS assimile les observations EEA, donc
  la cible même qu'on prédit. La comparer à ces observations lui prêterait un avantage
  qu'elle n'a pas en exploitation.
- **Ventilation par typologie.** La maille CAMS fait 0,1° (~8 km en longitude × 11 en latitude) ; une station trafic
  mesure un micro-environnement de quelques mètres. Lui imputer cet écart confond la
  qualité du modèle avec la définition de la mesure.
- **Correspondance exacte des instants.** La jointure porte sur (station, instant UTC).
  Un décalage d'une heure passerait inaperçu et améliorerait ou dégraderait les scores
  sans qu'aucun contrôle ne le signale.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval import comparaison as cmp  # noqa: E402

METEO = RACINE / "data/processed/meteo"

# Correspondance entre l'espèce CAMS et le polluant du panneau. La colonne de
# concentration porte le nom de l'espèce tel que le service l'écrit — `pm2p5_conc`,
# pas `pm25_conc` : le point est transcrit en `p`.
ESPECES = {
    "no2": ("NO2", "no2_conc"),
    "o3": ("O3", "o3_conc"),
    "pm25": ("PM25", "pm2p5_conc"),
}

# Un horizon réglementaire couvre 24 heures d'échéance. L'échéance 0 est l'analyse,
# pas une prévision : l'inclure flatterait le modèle.
# ⚠️ La clé est l'index de tranche, le libellé est J+(clé−1) : la tranche 1
# couvre les heures 1-24 d'une sortie 00 UTC, donc le JOUR MÊME. Voir
# `aq.rapport.libelle_echeance`, qui le dérive au lieu de le laisser écrire.
# La tranche 4 (73-96 h) est le dernier étage que CAMS Europe produise.
TRANCHES = {1: (1, 24), 2: (25, 48), 3: (49, 72), 4: (73, 96)}


def mois_disponibles(scope: str, court: str) -> list[Path]:
    return sorted(METEO.glob(f"cams_prevision_{scope}_{court}_*.parquet"))


def charger_observations(scope: str, debut: pd.Timestamp,
                         fin: pd.Timestamp) -> pd.DataFrame:
    """Observations horaires sur la fenêtre demandée, avec la typologie de station.

    **Les bornes viennent des prévisions elles-mêmes, jamais du nom des fichiers.**
    Un nom groupé `..._o3_202308_202309.parquet` porte deux mois ; une expression
    ancrée à droite n'en capture que le second, et la fenêtre ainsi construite
    ampute silencieusement le premier mois de l'archive.
    """
    panneau = RACINE / f"data/processed/panel_{scope}_ds2.parquet"

    obs = pd.read_parquet(
        panneau,
        filters=[("timestamp_utc", ">=", debut), ("timestamp_utc", "<", fin)],
        columns=["station_id", "polluant", "timestamp_utc", "valeur"],
    )
    stations = pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "type_station", "typologie_zone"],
    )
    return obs.merge(stations, on="station_id")


def evaluer(scope: str, horizons: list[int]) -> pd.DataFrame:
    lignes = []
    for court, (polluant, colonne) in ESPECES.items():
        fichiers = mois_disponibles(scope, court)
        if not fichiers:
            print(f"  {polluant} : aucun mois extrait, ignoré", flush=True)
            continue

        prev = pd.concat(
            [pd.read_parquet(f, columns=["station_id", "timestamp_utc",
                                         "echeance_h", colonne])
             for f in fichiers],
            ignore_index=True,
        )
        obs = charger_observations(
            scope, prev["timestamp_utc"].min(),
            prev["timestamp_utc"].max() + pd.Timedelta(hours=1))
        reel = obs[obs["polluant"] == polluant]

        for horizon in horizons:
            bas, haut = TRANCHES[horizon]
            joint = prev[prev["echeance_h"].between(bas, haut)].merge(
                reel, on=["station_id", "timestamp_utc"]
            )
            if joint.empty:
                print(f"  {polluant} J+{horizon} : aucune correspondance", flush=True)
                continue

            table = cmp.comparer(joint, colonne_predit=colonne, polluant=polluant,
                                 par=["type_station"])
            globale = cmp.comparer(joint, colonne_predit=colonne, polluant=polluant)
            globale["type_station"] = "toutes"

            for _, ligne in pd.concat([globale, table], ignore_index=True).iterrows():
                lignes.append({"polluant": polluant, "horizon": f"J+{horizon}",
                               "n_mois": len(fichiers), **ligne.to_dict()})
            print(f"  {polluant} J+{horizon} : {len(joint):,} paires · "
                  f"RMSE {globale['rmse'].iloc[0]:.2f} µg/m³", flush=True)

    return pd.DataFrame(lignes)


def rediger(resultats: pd.DataFrame, scope: str) -> str:
    """Rapport lisible — les chiffres seuls ne disent pas ce qu'ils impliquent."""
    lignes = [
        "# Performance des prévisions CAMS — la barre à battre",
        "",
        f"Périmètre **{scope}** · source `cams-europe-air-quality-forecasts` "
        "(ensemble de 9 à 11 modèles, maille 0,1°).",
        "",
        "Ce sont des **prévisions**, pas la réanalyse : la réanalyse assimile les "
        "observations EEA, donc la cible même qu'on cherche à prédire, et la comparer "
        "à ces observations lui prêterait un avantage qu'elle n'a pas en exploitation.",
        "",
        "> ⚠️ Les paramètres d'incertitude FAIRMODE utilisés pour le MQI sont repris de "
        "mémoire et **doivent être vérifiés contre le Guidance Document en vigueur** "
        "avant toute publication. Le seuil de conformité MQI ≤ 1 en dépend directement.",
        "",
        "| Polluant | Horizon | Typologie | n | RMSE | Biais | R² | MQI |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, r in resultats.iterrows():
        mqi = f"{r['mqi']:.2f}" if pd.notna(r.get("mqi")) else "—"
        lignes.append(
            f"| {r['polluant']} | {r['horizon']} | {r['type_station']} | "
            f"{int(r['n']):,} | {r['rmse']:.2f} | {r['biais']:+.2f} | "
            f"{r['r2']:+.3f} | {mqi} |"
        )
    return "\n".join(lignes) + "\n"


def main(scope: str, horizons: list[int]) -> int:
    print(f"Évaluation CAMS · périmètre {scope} · horizons {horizons}", flush=True)
    resultats = evaluer(scope, horizons)
    if resultats.empty:
        print("Aucun résultat — extraire d'abord les prévisions aux stations.")
        return 1

    (RACINE / "reports").mkdir(exist_ok=True)
    resultats.to_csv(RACINE / "reports/cams_benchmark.csv", index=False)
    (RACINE / "reports/CAMS_BENCHMARK.md").write_text(rediger(resultats, scope))
    print(f"\nÉcrit : reports/CAMS_BENCHMARK.md et cams_benchmark.csv "
          f"({len(resultats)} lignes)")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--scope", default="metropole",
                         choices=["metropole", "occitanie"])
    parseur.add_argument("--horizons", default="1,2,3")
    args = parseur.parse_args()
    raise SystemExit(
        main(args.scope, [int(h) for h in args.horizons.split(",")])
    )
