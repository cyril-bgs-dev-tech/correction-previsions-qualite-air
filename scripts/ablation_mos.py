"""Chiffre l'apport de chaque famille de variables, et évalue sur l'Occitanie seule.

Usage : python scripts/ablation_mos.py [--polluant O3] [--horizon 1]
Sortie : reports/ABLATION.md et reports/ablation_{polluant}.csv

**Deux questions distinctes, souvent confondues.**

1. *Quelle famille de variables porte le gain ?* On retire une famille à la fois et on
   mesure ce qu'on perd. Retirer plutôt qu'ajouter, parce que les variables sont
   corrélées entre elles : ajoutées seules, deux familles redondantes paraissent toutes
   deux décisives ; retirées seules, aucune ne manque — et c'est cette seconde lecture
   qui dit ce qu'on peut se permettre d'abandonner.

2. *Le modèle national tient-il en Occitanie ?* On entraîne en excluant **toute**
   l'Occitanie, et on évalue dessus. C'est la question de l'employeur, et elle est plus
   dure qu'une validation par stations exclues au hasard : les stations occitanes
   partagent un climat, un relief et des essences forestières que le modèle n'aura vus
   nulle part ailleurs de façon aussi concentrée.
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

# Familles de variables, définies par ce qu'elles décrivent — pas par leur préfixe
# technique. Une famille doit correspondre à une décision qu'on pourrait prendre :
# « faut-il extraire le relief ? », « faut-il séparer les essences ? ».
FAMILLES = {
    "relief": lambda c: c.startswith(("tpi_", "rugosite_"))
                        or c in ("profondeur_vallee_m", "pente_deg", "altitude_mnt_m"),
    "forêt": lambda c: c.startswith(("chene_", "conifere_", "feuillu_", "foret_")),
    "routes": lambda c: c.startswith("route_"),
    "calendrier": lambda c: c in ("heure_cos", "heure_sin", "jour_annee_cos",
                                  "jour_annee_sin", "jour_semaine", "weekend"),
    "coordonnées": lambda c: c in ("lat_wgs84", "lon_wgs84"),
    "échéance": lambda c: c == "echeance_h",
}

DEPARTEMENTS_OCCITANIE = {
    "09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82",
}


def evaluer(jeu: pd.DataFrame, colonnes: list[str], n_plis: int = 5) -> dict:
    """Performance en validation par stations exclues, sur un jeu de colonnes donné."""
    resultat = mos.ajuster_par_stations_exclues(
        jeu, colonnes, colonne_cams="cams", n_plis=n_plis
    )
    p = resultat.predictions.dropna(subset=["observe"])
    return cmp.metriques(p["observe"], p["corrige"])


def main(polluant: str, horizon: int, n_plis: int) -> int:
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    print(f"{polluant} J+{horizon} · {len(jeu):,} paires · "
          f"{jeu['station_id'].nunique()} stations · {len(colonnes)} variables\n",
          flush=True)

    base_cams = cmp.metriques(jeu["valeur"], jeu["cams"])
    complet = evaluer(jeu, colonnes, n_plis)
    print(f"{'jeu de variables':22s} {'RMSE':>7s} {'R²':>8s} {'perte':>8s}")
    print(f"{'CAMS brut':22s} {base_cams['rmse']:7.2f} {base_cams['r2']:+8.3f}")
    print(f"{'toutes':22s} {complet['rmse']:7.2f} {complet['r2']:+8.3f}", flush=True)

    lignes = [{"jeu": "CAMS brut", "n_vars": 0, **base_cams},
              {"jeu": "toutes", "n_vars": len(colonnes), **complet}]

    for nom, appartient in FAMILLES.items():
        restantes = [c for c in colonnes if not appartient(c)]
        retirees = len(colonnes) - len(restantes)
        if retirees == 0:
            continue
        m = evaluer(jeu, restantes, n_plis)
        perte = 100 * (m["rmse"] / complet["rmse"] - 1)
        print(f"{'sans ' + nom:22s} {m['rmse']:7.2f} {m['r2']:+8.3f} "
              f"{perte:+7.1f} %", flush=True)
        lignes.append({"jeu": f"sans {nom}", "n_vars": len(restantes),
                       "perte_pct": perte, **m})

    # ── Évaluation Occitanie : entraîner en excluant toute la région ──
    stations = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                               columns=["station_id", "commune", "code_national"])
    fusion = jeu.merge(stations, on="station_id", how="left")
    # Le préfixe du code station n'est PAS le département (FR34051 est dans l'Indre) :
    # on passe donc par les coordonnées, seule source fiable ici.
    occitanie = ((fusion["lat_wgs84"].between(42.3, 45.1))
                 & (fusion["lon_wgs84"].between(-0.4, 4.9)))
    st_occ = set(fusion.loc[occitanie, "station_id"].unique())

    print(f"\n--- Généralisation à l'Occitanie · {len(st_occ)} stations ---", flush=True)
    if len(st_occ) < 5:
        print("Trop peu de stations occitanes pour conclure.")
    else:
        entrainement = jeu[~jeu["station_id"].isin(st_occ)]
        test = jeu[jeu["station_id"].isin(st_occ)]
        modele = mos._modele(0)
        modele.fit(entrainement[colonnes],
                   entrainement["valeur"] - entrainement["cams"])
        predit = np.clip(
            test["cams"].to_numpy() + modele.predict(test[colonnes]), 0, None)
        m_occ = cmp.metriques(test["valeur"], predit)
        m_cams = cmp.metriques(test["valeur"], test["cams"])
        print(f"  {'CAMS brut':16s} RMSE {m_cams['rmse']:6.2f} · R² {m_cams['r2']:+.3f}")
        print(f"  {'MOS (hors Occ.)':16s} RMSE {m_occ['rmse']:6.2f} · R² {m_occ['r2']:+.3f}"
              f" · gain {100 * (1 - m_occ['rmse'] / m_cams['rmse']):+.1f} %", flush=True)
        lignes += [{"jeu": "Occitanie — CAMS brut", "n_vars": 0, **m_cams},
                   {"jeu": "Occitanie — MOS entraîné hors Occitanie",
                    "n_vars": len(colonnes), **m_occ}]

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/ablation_{polluant}.csv", index=False)
    print(f"\nÉcrit : reports/ablation_{polluant}.csv")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    parseur.add_argument("--plis", type=int, default=4)
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
