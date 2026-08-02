#!/usr/bin/env python3
"""Le run final : une seule mesure, un seul découpage, tous les chiffres citables.

Pourquoi ce script existe
-------------------------
Les mesures de la nuit du 30/07 sont justes mais **dispersées** : la cible journalière a été
évaluée sur trois plis de stations, le tuning sur un découpage à trois groupes, les scores
d'épisode sur l'année entière alors que le référentiel LCSQA évalue l'ozone d'avril à
septembre. Chacune répondait à sa question, aucune ne permet d'annoncer un cumul.

Ce script produit **un tableau unique**, sur un découpage unique, avec :

- la **cible réglementaire** de chaque polluant — max 8 h (O₃), max horaire (NO₂), moyenne
  journalière (PM2.5) ;
- les **trois échéances** J+1 à J+3, pour étayer « tout l'horizon réglementaire » ;
- les hyperparamètres **par défaut et réglés**, pour répondre à une question ouverte : le
  réglage trouvé sur l'ozone **transfère-t-il** aux autres polluants ? Rien ne le garantit —
  les trois distributions n'ont ni la même asymétrie ni la même variance ;
- les scores d'épisode **sur la fenêtre du référentiel** : avril-septembre pour l'ozone, année
  entière pour les autres.

Ce que ce script ne fait pas : il ne rejoue pas la voie horaire agrégée, déjà mesurée
(`reports/cible_journaliere_*.csv`). Le point de comparaison y est repris tel quel, et l'écart
n'est annoncé que pour les polluants où les deux voies partagent le même échantillon de
jours-station — ce qui est le cas par construction.

Usage : python3 scripts/modele_final.py [--polluants O3,NO2,PM25] [--horizons 1,2,3]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from aq.models import mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from scores_episodes import scores  # noqa: E402

# Réglage retenu par `tuning_borne.py` sur la cible journalière d'O₃, en validation
# imbriquée : +6,28 % sur un test jamais consulté. Son transfert aux autres polluants est
# une hypothèse que ce script teste, pas un acquis.
REGLE = {"num_leaves": 255, "learning_rate": 0.03, "n_estimators": 900,
         "min_child_samples": 50, "reg_lambda": 10.0}
DEFAUT = {"num_leaves": 63, "learning_rate": 0.05, "n_estimators": 400,
          "min_child_samples": 200, "reg_lambda": 0.0}

# ⚠️ Ces trois premiers seuils ne sont **pas** des déclencheurs de procédure : 120 en
# max 8 h est la valeur cible européenne de l'ozone, 120 et 25 sont des bornes de
# l'indice ATMO. Le PM10 fait exception : **50 µg/m³ en moyenne journalière est le
# seuil d'information français**, celui qui déclenche réellement une procédure — et
# c'est le polluant qui porte 40 des 52 vigilances déclarées en Occitanie.
SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0, "PM10": 50.0}
# Fenêtre d'évaluation imposée par le référentiel LCSQA : l'ozone d'avril à septembre.
FENETRE = {"O3": (4, 9), "NO2": (1, 12), "PM25": (1, 12)}


def fabrique(params: dict):
    def _f(graine: int):
        from lightgbm import LGBMRegressor

        return LGBMRegressor(subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                             random_state=graine, n_jobs=-1, verbose=-1, **params)
    return _f


def main(polluants: list[str], horizons: list[int], n_plis: int) -> int:
    depart = time.time()
    lignes = []

    for polluant in polluants:
        grandeur = GRANDEUR_PAR_POLLUANT[polluant]
        seuil = SEUILS[polluant]
        mois_min, mois_max = FENETRE[polluant]

        for horizon in horizons:
            jeu = charger(polluant, horizon)
            colonnes = colonnes_admises(jeu)
            jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
            jeu = jeu.dropna(subset=["valeur"])

            journalier = agreger_journalier(jeu, colonnes, grandeur)
            predicteurs = ([c for c in colonnes if c != "cams"]
                           + ["cams_moy_jour", "cams_jour"])
            entree = journalier.rename(columns={"obs_jour": "valeur",
                                                "jour": "timestamp_utc"})

            base = cmp.metriques(entree["valeur"], entree["cams_jour"])
            print(f"\n=== {polluant} J+{horizon} · {grandeur} · "
                  f"{len(entree):,} jours-station · CAMS {base['rmse']:.2f} ===", flush=True)

            for nom, params in (("défaut", DEFAUT), ("réglé", REGLE)):
                resultat = mos.ajuster_par_stations_exclues(
                    entree, predicteurs, colonne_cams="cams_jour", n_plis=n_plis,
                    verbeux=False, fabrique_modele=fabrique(params),
                )
                p = resultat.predictions.dropna(subset=["observe"])
                m = cmp.metriques(p["observe"], p["corrige"])
                gain = 100 * (1 - m["rmse"] / base["rmse"])

                # Scores d'épisode sur la fenêtre du référentiel, pas sur l'année entière.
                mois = p["timestamp_utc"].dt.month
                dans = (mois >= mois_min) & (mois <= mois_max)
                q = p[dans]
                depasse = (q["observe"] >= seuil).to_numpy()
                s = (scores(depasse, (q["corrige"] >= seuil).to_numpy())
                     if depasse.sum() >= 100 else {})
                s_cams = (scores(depasse, (q["cams"] >= seuil).to_numpy())
                          if depasse.sum() >= 100 else {})

                détail = ""
                if s:
                    détail = (f" · POD {s_cams['POD']:.3f}→{s['POD']:.3f}"
                              f" · CSI {s_cams['CSI']:.3f}→{s['CSI']:.3f}"
                              f" (n={s['n_observes']:,})")
                print(f"  {nom:7s} RMSE {m['rmse']:6.2f} · R² {m['r2']:+.3f} · "
                      f"gain {gain:+5.1f} %{détail}", flush=True)

                lignes.append({
                    "polluant": polluant, "horizon": horizon, "grandeur": grandeur,
                    "reglage": nom, "n_jours": len(p), "rmse_cams": base["rmse"],
                    "rmse": m["rmse"], "r2": m["r2"], "gain_pct": gain,
                    "fenetre_scores": f"{mois_min}-{mois_max}",
                    **{f"cams_{k}": v for k, v in s_cams.items()},
                    **{f"mos_{k}": v for k, v in s.items()},
                })

    table = pd.DataFrame(lignes)
    sortie = RACINE / "reports/modele_final.csv"
    table.to_csv(sortie, index=False)

    print(f"\n{'=' * 72}\nSynthèse — gain par polluant et échéance, sur découpage unique\n")
    pivot = table.pivot_table(index=["polluant", "grandeur"],
                              columns=["reglage", "horizon"], values="gain_pct")
    print(pivot.round(1).to_string())

    print("\nApport du réglage (points de gain), par polluant :")
    for polluant in polluants:
        sous = table[table["polluant"] == polluant]
        d = sous[sous["reglage"] == "défaut"]["gain_pct"].mean()
        r = sous[sous["reglage"] == "réglé"]["gain_pct"].mean()
        verdict = "transfère" if r - d >= 1.0 else "ne transfère pas"
        print(f"  {polluant:5s} défaut {d:+5.1f} % → réglé {r:+5.1f} % "
              f"· écart {r - d:+4.1f} pt → **{verdict}**")

    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluants", default="O3,NO2,PM25")
    p.add_argument("--horizons", default="1,2,3")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluants.split(","),
                          [int(h) for h in args.horizons.split(",")], args.plis))
