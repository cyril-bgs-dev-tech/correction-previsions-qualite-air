"""Ajuste et valide un modèle LUR sur les moyennes annuelles.

Usage : python scripts/fit_lur.py [--scope occitanie] [--polluant NO2] [--annee 2023]

Une LUR est **transversale** : une observation par station. Utiliser plusieurs années
de la même station créerait de la pseudo-réplication — le modèle paraîtrait reposer
sur bien plus de points indépendants qu'il n'en a réellement, et tous les intervalles
de confiance seraient trop étroits.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.models import lur  # noqa: E402

# Colonnes de features géospatiales à exclure : masses brutes non pondérées, qui
# dépendent surtout du rayon d'interrogation et non de la structure du paysage.
EXCLUES = ("_surface_m2", "_longueur_m")


def charger(scope: str, polluant: str, annee: int | None) -> pd.DataFrame:
    annuel = pd.read_parquet(RACINE / f"data/processed/annuel_{scope}.parquet")
    geo = pd.read_parquet(RACINE / f"data/processed/geo_features_{scope}.parquet")
    stations = pd.read_parquet(RACINE / "data/processed/stations.parquet")

    cible = annuel[(annuel["polluant"] == polluant) & annuel["valide"]]
    if annee is not None:
        cible = cible[cible["annee"] == annee]
    else:
        # À défaut d'année imposée, moyenne pluriannuelle par station — plus stable
        # qu'une année isolée, et toujours une seule observation par station.
        cible = (
            cible.groupby("station_id", as_index=False)
            .agg(moyenne_annuelle=("moyenne_annuelle", "mean"),
                 n_annees=("annee", "nunique"))
        )

    return (
        cible.merge(geo, on="station_id")
        .merge(stations[["station_id", "nom", "type_station", "typologie_zone",
                         "altitude"]], on="station_id")
    )


def controler_features(jeu: pd.DataFrame) -> None:
    """Signale les stations dont les variables routières sont nulles.

    Une extraction ayant échoué en réseau produit des variables à zéro, ce qui se lit
    exactement comme « aucune route à proximité ». Le modèle interpréterait alors une
    panne de téléchargement comme une caractéristique du paysage — erreur silencieuse,
    et d'autant plus trompeuse que ces stations sont souvent urbaines.
    """
    if "route_longueur_m" not in jeu.columns:
        return
    suspectes = jeu[jeu["route_longueur_m"] == 0]
    if len(suspectes):
        print(f"\n⚠️  {len(suspectes)} station(s) sans aucune route dans 5 km — "
              "extraction probablement incomplète :")
        for _, ligne in suspectes.head(10).iterrows():
            print(f"     {ligne['station_id']} {ligne.get('nom', '')}")
        print("     → exclues de l'ajustement.\n")


def main(scope: str, polluant: str, annee: int | None, fond_seul: bool) -> int:
    jeu = charger(scope, polluant, annee)
    controler_features(jeu)
    if "route_longueur_m" in jeu.columns:
        jeu = jeu[jeu["route_longueur_m"] > 0]

    if fond_seul:
        # Les stations trafic mesurent un micro-environnement de quelques mètres,
        # que les couches de paysage ne décrivent pas. Les mélanger au fond fait
        # porter au modèle une variance qu'il ne peut pas expliquer.
        jeu = jeu[jeu["type_station"] == "background"]

    colonnes_geo = [
        c for c in jeu.columns
        if ("_lambda" in c or "_dist_min_m" in c) and not c.endswith(EXCLUES)
    ]
    X = jeu[colonnes_geo].astype("float64")
    # Une distance infinie signifie « aucun objet dans le rayon » : on la remplace
    # par le rayon d'interrogation, valeur finie et interprétable.
    X = X.replace([float("inf")], 30_000.0)

    # Transformation logarithmique des expositions — indispensable, pas cosmétique.
    # À λ court, exp(−d/λ) décroît si vite que la variable s'étale sur douze ordres
    # de grandeur (10⁻⁴⁴ à 10³ observé sur `chene_lambda100m`). Une régression
    # linéaire y est dominée par une ou deux stations, et le modèle explose dès
    # qu'on retire l'une d'elles. Le logarithme rend la variable exploitable et
    # correspond à l'usage courant de la littérature LUR.
    expositions = [c for c in X.columns if "_lambda" in c]
    X[expositions] = np.log1p(X[expositions].clip(lower=0))

    # Écarter les variables trop dégénérées pour porter un signal : quelques points
    # extrêmes suffiraient à piloter le coefficient.
    assez_variables = X.columns[X.std() > 1e-6]
    X = X[assez_variables]

    y = jeu["moyenne_annuelle"].to_numpy()

    titre = f"{polluant} · {scope} · {'fond seul' if fond_seul else 'toutes typologies'}"
    print(f"=== LUR {titre} ===")
    print(f"{len(jeu)} stations · {len(colonnes_geo)} variables candidates")
    print(f"Cible : moyenne {'de ' + str(annee) if annee else 'pluriannuelle'} · "
          f"{y.mean():.1f} ± {y.std():.1f} µg/m³ (min {y.min():.1f}, max {y.max():.1f})")

    if len(jeu) < 8:
        print("\nEffectif insuffisant pour un ajustement crédible.")
        return 1

    modele = lur.ajuster(X, y)
    print(f"\n--- Modèle sur l'échantillon complet (R² ajusté {modele.r2_ajuste:.3f}) ---")
    for (variable, score), coefficient in zip(modele.historique, modele.coefficients):
        print(f"  {variable:32s} coef {coefficient:+12.3e}   R²aj cumulé {score:.3f}")
    if not modele.variables:
        print("  aucune variable retenue (contrainte de signe ou gain insuffisant)")

    resultats = lur.valider_station_exclue(X, y, jeu["station_id"])
    m = lur.metriques(resultats["observe"], resultats["predit"])

    print("\n--- Validation leave-one-station-out ---")
    print(f"  RMSE          {m['rmse']:.2f} µg/m³")
    print(f"  MAE           {m['mae']:.2f} µg/m³")
    print(f"  Biais         {m['biais']:+.2f} µg/m³")
    print(f"  R²            {m['r2']:.3f}")
    print(f"  RMSE baseline {m['rmse_baseline_moyenne']:.2f} µg/m³  "
          f"(prédire la moyenne partout)")
    gain = 100 * (1 - m["rmse"] / m["rmse_baseline_moyenne"])
    print(f"  → gain sur la baseline : {gain:+.1f} %")

    resultats = resultats.merge(jeu[["station_id", "nom"]], on="station_id")
    resultats["erreur"] = resultats["predit"] - resultats["observe"]
    print("\n--- Stations les plus mal prédites ---")
    print(resultats.reindex(resultats["erreur"].abs().sort_values(ascending=False).index)
          .head(5)[["nom", "observe", "predit", "erreur"]].round(1).to_string(index=False))

    sortie = RACINE / f"reports/lur_{scope}_{polluant}.csv"
    resultats.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.name}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--scope", default="occitanie")
    parseur.add_argument("--polluant", default="NO2", choices=["NO2", "O3", "PM25"])
    parseur.add_argument("--annee", type=int, default=None)
    parseur.add_argument("--fond-seul", action="store_true")
    args = parseur.parse_args()
    raise SystemExit(main(args.scope, args.polluant, args.annee, args.fond_seul))
