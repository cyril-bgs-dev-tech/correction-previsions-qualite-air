"""Le trafic hiérarchisé et la population apportent-ils quelque chose ?

Usage : python scripts/apport_trafic_population.py [--polluant NO2]
Sortie : reports/apport_trafic_population_{polluant}.csv

**La question.** Les variables routières initiales pondéraient les tronçons par leur
**longueur seule** — une rue de village comptait autant qu'une autoroute au mètre. Les
nouvelles distinguent quatre classes issues de `importance` (BD TOPO), pondèrent par le
nombre de voies, écartent les sentiers, et ajoutent l'exposition à la population
communale.

Reste à savoir si cette finesse **se paie en prédiction**, ou si le modèle savait déjà
tout ce qu'elle contient. Quatre jeux comparés, toujours sur stations entièrement
cachées :

| Jeu | Contenu |
|---|---|
| référence | paysage + relief + routes **par longueur** |
| sans routes du tout | témoin bas — ce que valent les autres variables seules |
| + trafic hiérarchisé | les quatre classes remplacent la longueur agrégée |
| + trafic **et** population | tout |

Le témoin bas est indispensable : sans lui, un gain pourrait venir de la simple
multiplication des variables plutôt que de leur contenu.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from aq.models import mos  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402


def _routes_longueur(c: str) -> bool:
    """Anciennes variables routières — pondérées par la seule longueur."""
    return c.startswith("route_") and not any(
        c.startswith(f"route_{k}_") for k in
        ("autoroute", "principale", "secondaire", "locale")
    )


def _trafic_hierarchise(c: str) -> bool:
    return any(c.startswith(f"route_{k}_") for k in
               ("autoroute", "principale", "secondaire", "locale"))


def _population(c: str) -> bool:
    return c.startswith("population_") or c == "distance_pole_dominant_m"


def main(polluant: str, horizon: int, n_plis: int) -> int:
    jeu = charger(polluant, horizon)
    nouvelles = pd.read_parquet(
        RACINE / "data/processed/trafic_population_metropole.parquet")
    jeu = jeu.merge(nouvelles, on="station_id", how="left")

    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"]).reset_index(drop=True)

    base = [c for c in colonnes if not _trafic_hierarchise(c) and not _population(c)]
    sans_routes = [c for c in base if not _routes_longueur(c)]
    avec_trafic = [c for c in colonnes if not _population(c)
                   and not _routes_longueur(c)]
    tout = [c for c in colonnes if not _routes_longueur(c)]

    variantes = {
        "sans aucune route (témoin bas)": sans_routes,
        "routes par longueur (référence)": base,
        "trafic hiérarchisé": avec_trafic,
        "trafic hiérarchisé + population": tout,
    }

    print(f"{polluant} J+{horizon} · {len(jeu):,} paires · "
          f"{jeu['station_id'].nunique()} stations", flush=True)
    for nom, cols in variantes.items():
        print(f"  {nom:34s} {len(cols):3d} variables", flush=True)
    print()

    m_cams = cmp.metriques(jeu["valeur"], jeu["cams"])
    resultats = {}
    print(f"{'jeu de variables':34s} {'RMSE':>7s} {'R²':>8s} {'gain/CAMS':>10s}")
    print(f"{'CAMS brut':34s} {m_cams['rmse']:7.2f} {m_cams['r2']:+8.3f}")

    lignes = []
    for nom, cols in variantes.items():
        r = mos.ajuster_par_stations_exclues(jeu, cols, colonne_cams="cams",
                                             n_plis=n_plis)
        p = r.predictions.dropna(subset=["observe"])
        resultats[nom] = p
        m = cmp.metriques(p["observe"], p["corrige"])
        lignes.append({"jeu": nom, "n_vars": len(cols), **m,
                       "gain_pct": 100 * (1 - m["rmse"] / m_cams["rmse"])})
        print(f"{nom:34s} {m['rmse']:7.2f} {m['r2']:+8.3f} "
              f"{100 * (1 - m['rmse'] / m_cams['rmse']):+9.1f} %", flush=True)

    # L'apport marginal, avec son intervalle : c'est le chiffre qui décide.
    reference = resultats["routes par longueur (référence)"]
    for nom in ("trafic hiérarchisé", "trafic hiérarchisé + population"):
        candidat = resultats[nom]
        commun = reference.merge(
            candidat[["station_id", "timestamp_utc", "corrige"]],
            on=["station_id", "timestamp_utc"], suffixes=("_ref", "_cand"))
        ic = cmp.intervalle_bootstrap(
            commun["observe"], commun["corrige_ref"], commun["corrige_cand"],
            groupes=commun["station_id"], n_tirages=300)
        print(f"\n→ {nom} contre routes par longueur : {ic['gain_pct']:+.1f} % "
              f"IC95 [{ic['borne_basse']:+.1f} ; {ic['borne_haute']:+.1f}] · "
              f"{100 * ic['part_tirages_positifs']:.0f} % de tirages positifs",
              flush=True)

    pd.DataFrame(lignes).to_csv(
        RACINE / f"reports/apport_trafic_population_{polluant}.csv", index=False)
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="NO2", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    parseur.add_argument("--plis", type=int, default=4)
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
