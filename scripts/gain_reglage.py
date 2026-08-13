#!/usr/bin/env python3
"""Ce que le réglage par polluant rapporte à NOTRE méthode — en CSV, plus seulement en journal.

Pourquoi ce script, alors que `optuna_mos.py` imprime déjà ces deux chiffres
------------------------------------------------------------------------------
`optuna_mos.py` termine par une « mesure finale » sur les stations jamais consultées :

    réglage lgbm déployé RMSE 8.5254 · gain vs CAMS +28.90 %
    meilleur Optuna      RMSE 8.1027 · gain vs CAMS +32.42 %

Ces deux lignes sont **imprimées, jamais enregistrées** : le CSV de l'étude ne porte que
l'objectif de validation croisée, pas la mesure finale. Pour faire entrer ce gain dans la
présentation, il faudrait le recopier à la main — et un chiffre recopié se périme en
silence (§ 2 ter : le chiffre affiché n'est pas le chiffre enregistré).

Ce script rejoue la mesure finale depuis l'étude stockée et l'**écrit**. Il ne relance aucun
essai : il relit le `.db`, retient le meilleur essai admissible, et ajuste deux fois.

Il est délibérément SÉPARÉ de `optuna_mos.py` : ce dernier est exécuté en boucle par
`lot_optuna_reglage.sh`, et modifier un script pendant qu'un lot l'appelle est le geste qui
a déjà tué un lot sur ce dépôt (§ 1 bis).

⚠️ Le gain rendu ici porte sur l'axe SPATIAL — réglage choisi par validation imbriquée sur
des groupes de stations, mesuré sur des stations jamais consultées. Le projet a mesuré
qu'un réglage gagnant en spatial peut PERDRE en temporel (+5 / −3 points). L'axe se cite
avec le chiffre.

Usage  : python3 scripts/gain_reglage.py --polluant O3
         python3 scripts/gain_reglage.py --tous
Sortie : reports/gain_reglage_<polluant>.csv
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

from optuna_mos import (  # noqa: E402
    DOSSIER, GRAINE, PART_QUEUE, _params_essai, ajuster_pli, jeu_journalier,
    params_reference, rmse, scores,
)

NOM = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}


def mesurer(polluant: str, algo: str = "lgbm") -> dict:
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    t0 = time.time()
    base = DOSSIER / f"mos_{polluant}_{algo}.db"
    if not base.exists():
        raise SystemExit(f"aucune étude pour {polluant} : {base} — lancer d'abord "
                         f"`bash scripts/lot_optuna_reglage.sh {polluant}`")
    etude = optuna.load_study(study_name=f"mos_{polluant}_{algo}",
                              storage=f"sqlite:///{base}")
    complets = [t for t in etude.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if not complets:
        raise SystemExit(f"{polluant} : aucun essai complet dans l'étude")

    # ── La MÊME partition que l'étude : même graine, même tiers de test. Reconstruire
    # une partition différente comparerait deux mesures sur deux jeux, et l'écart
    # passerait pour un effet du réglage (§ 2 quater).
    j, predicteurs = jeu_journalier(polluant)
    stations = np.sort(j["station_id"].unique())
    melange = np.random.default_rng(GRAINE).permutation(stations)
    st_test = np.sort(melange[: len(melange) // 3])
    st_dev = np.sort(melange[len(melange) // 3:])

    # ── La sélection est celle de `optuna_mos._rapport`, à la lettre : le meilleur essai
    # SOUS CONTRAINTE DE QUEUE. Retenir le minimum global donnerait un gain plus flatteur
    # et un modèle que le dossier ne déploierait pas.
    reference = complets[0]          # l'essai amorcé sur le réglage déployé
    q_ref = reference.user_attrs.get("rmse_decile_haut", float("inf"))
    admissibles = [t for t in complets
                   if t.user_attrs.get("rmse_decile_haut", np.inf) <= q_ref * (1 + PART_QUEUE)]
    if not admissibles:
        raise SystemExit(f"{polluant} : aucun essai ne respecte la contrainte de queue")
    meilleur = min(admissibles, key=lambda t: t.value)

    print(f"{NOM[polluant]} · {len(complets)} essais complets · "
          f"{len(admissibles)} admissibles · test {len(st_test)} stations jamais vues",
          flush=True)

    ligne = {"polluant": polluant, "algo": algo, "essais_complets": len(complets),
             "essais_admissibles": len(admissibles), "essai_retenu": meilleur.number,
             "stations_test": len(st_test), "n": len(j)}
    for cle, nom, params in (("deploye", "réglage déployé", params_reference(algo)),
                             ("regle", "réglé par polluant", _params_essai(meilleur, algo))):
        pred, test, n_arbres = ajuster_pli(j, predicteurs, st_dev, st_test, params, algo)
        r, q = scores(test["obs_jour"], pred)
        r_cams = rmse(test["obs_jour"], test["cams_jour"])
        ligne |= {f"rmse_{cle}": r, f"decile_haut_{cle}": q,
                  f"gain_cams_{cle}_pct": 100 * (1 - r / r_cams)}
        print(f"  {nom:22s} RMSE {r:7.4f} · décile haut {q:7.4f} · "
              f"gain vs CAMS {100 * (1 - r / r_cams):+6.2f} %", flush=True)

    ligne["gain_reglage_pct"] = 100 * (1 - ligne["rmse_regle"] / ligne["rmse_deploye"])
    ligne["gain_reglage_pt"] = ligne["gain_cams_regle_pct"] - ligne["gain_cams_deploye_pct"]
    print(f"  → le réglage par polluant vaut {ligne['gain_reglage_pct']:+.2f} % de RMSE "
          f"({ligne['gain_reglage_pt']:+.2f} pt de gain vs CAMS) · "
          f"{(time.time() - t0) / 60:.1f} min\n", flush=True)
    return ligne


def main(polluants: list[str], algo: str) -> int:
    lignes = []
    for p in polluants:
        lignes.append(mesurer(p, algo))
        # La table s'écrit APRÈS chaque polluant, jamais à la fin : sur cette machine, un
        # lot qui garde tout en mémoire jusqu'au bout perd tout à la première coupure.
        t = pd.DataFrame(lignes)
        attendues = ["polluant", "rmse_deploye", "rmse_regle", "gain_reglage_pct"]
        if manque := [c for c in attendues if c not in t.columns]:
            raise SystemExit(f"colonnes absentes du rapport : {manque}")
        for _, l in t.iterrows():
            (pd.DataFrame([l]).to_csv(
                RACINE / f"reports/gain_reglage_{l['polluant']}.csv", index=False))
    print(f"Écrit : {len(lignes)} fichier(s) reports/gain_reglage_<polluant>.csv")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3", choices=tuple(NOM))
    a.add_argument("--algo", default="lgbm", choices=("lgbm", "xgb"))
    a.add_argument("--tous", action="store_true", help="les quatre polluants à la suite")
    n = a.parse_args()
    raise SystemExit(main(list(NOM) if n.tous else [n.polluant], n.algo))
