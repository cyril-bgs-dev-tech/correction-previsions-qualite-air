#!/usr/bin/env python3
"""Trente essais d'hyperparamètres, en validation imbriquée — puis on s'arrête.

Pourquoi borner
---------------
Aucun hyperparamètre n'a jamais été optimisé sur ce projet. La littérature et les relectures
convergent sur un gain modeste : **2 à 5 % relatif**, pas quinze — et l'espace est plat, trois
bibliothèques de boosting tenant en 0,3 point. Une recherche exhaustive coûterait une nuit
pour un gain que le protocole ne saurait même pas distinguer du bruit.

Trente essais aléatoires sur les **quatre** paramètres qui portent l'essentiel dans ce type
de tâche : capacité (`num_leaves`), pas d'apprentissage couplé au nombre d'arbres,
régularisation par effectif de feuille (`min_child_samples`) et pénalité L2 (`reg_lambda`).

**La précaution qui décide de tout : validation imbriquée.** Choisir les hyperparamètres
d'après le jeu qui sert ensuite à annoncer le résultat est la façon la plus courante de
fabriquer un gain qui n'existe pas. On découpe donc :

1. les stations de **test** sont mises de côté et jamais consultées ;
2. parmi les stations restantes, un sous-ensemble sert de **validation** — c'est lui qui
   choisit les hyperparamètres ;
3. le candidat retenu est réajusté sur tout l'entraînement, puis évalué **une seule fois**
   sur le test, contre le modèle par défaut évalué sur le même test.

Sans l'étape 2, tout écart mesuré serait de l'optimisme de sélection.

Le test porte sur la **cible journalière** d'O₃ (max 8 h), désormais la voie retenue pour ce
polluant : 134 000 jours-station au lieu de 3,2 M de lignes, donc trente essais restent
abordables.

Usage : python3 scripts/tuning_borne.py [--polluant O3] [--essais 30]
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
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

GRAINE = 20260730
SEUIL_ABANDON_PCT = 0.5  # gain externe minimal, sous lequel on ne retient pas le réglage


def tirer(rng: np.random.Generator) -> dict:
    """Un jeu d'hyperparamètres. Les plages encadrent le réglage actuel du projet."""
    n_estimators = int(rng.choice([300, 400, 600, 900]))
    return {
        "num_leaves": int(rng.choice([31, 63, 127, 255])),
        "learning_rate": float(rng.choice([0.02, 0.03, 0.05, 0.08])),
        "n_estimators": n_estimators,
        "min_child_samples": int(rng.choice([50, 100, 200, 400])),
        "reg_lambda": float(rng.choice([0.0, 1.0, 10.0, 50.0])),
    }


def ajuster(params: dict, tr: pd.DataFrame, te: pd.DataFrame,
            colonnes: list[str], ancre: str) -> float:
    """Ajuste sur `tr`, rend le RMSE sur `te`. Cible résiduelle, écrêtage à zéro."""
    from lightgbm import LGBMRegressor

    modele = LGBMRegressor(subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                           random_state=GRAINE, n_jobs=-1, verbose=-1, **params)
    modele.fit(tr[colonnes], tr["valeur"] - tr[ancre])
    predit = np.clip(te[ancre].to_numpy() + modele.predict(te[colonnes]), 0, None)
    return float(cmp.metriques(te["valeur"], predit)["rmse"])


def main(polluant: str, horizon: int, n_essais: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    journalier = agreger_journalier(jeu, colonnes, grandeur)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = journalier.rename(columns={"obs_jour": "valeur"})

    # ── Trois groupes de stations disjoints : test, validation, entraînement ────
    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    melange = rng.permutation(stations)
    n = len(melange)
    st_test = set(melange[: n // 3])
    st_val = set(melange[n // 3 : n // 2])
    st_train = set(melange[n // 2 :])

    test = d[d["station_id"].isin(st_test)]
    val = d[d["station_id"].isin(st_val)]
    train = d[d["station_id"].isin(st_train)]
    train_complet = d[~d["station_id"].isin(st_test)]

    print(f"{polluant} · {grandeur} · {len(d):,} jours-station\n"
          f"  entraînement {len(st_train)} stations · validation {len(st_val)} · "
          f"test {len(st_test)} (jamais consulté avant la mesure finale)\n", flush=True)

    defaut = {"num_leaves": 63, "learning_rate": 0.05, "n_estimators": 400,
              "min_child_samples": 200, "reg_lambda": 0.0}

    # ── Sélection sur la validation seule ──────────────────────────────────────
    rmse_val_defaut = ajuster(defaut, train, val, predicteurs, "cams_jour")
    print(f"  défaut, sur validation : RMSE {rmse_val_defaut:.4f}", flush=True)

    meilleur, rmse_meilleur, essais = defaut, rmse_val_defaut, []
    for i in range(1, n_essais + 1):
        params = tirer(rng)
        r = ajuster(params, train, val, predicteurs, "cams_jour")
        essais.append({"essai": i, "rmse_val": r, **params})
        marque = ""
        if r < rmse_meilleur:
            meilleur, rmse_meilleur, marque = params, r, "  ← meilleur"
        print(f"  essai {i:2d}/{n_essais} · RMSE val {r:.4f}{marque}", flush=True)

    print(f"\nmeilleur sur validation : {rmse_meilleur:.4f} contre "
          f"{rmse_val_defaut:.4f} au défaut")
    print(f"  {meilleur}", flush=True)

    # ── Une seule mesure sur le test, pour les deux candidats ──────────────────
    rmse_test_defaut = ajuster(defaut, train_complet, test, predicteurs, "cams_jour")
    rmse_test_regle = ajuster(meilleur, train_complet, test, predicteurs, "cams_jour")
    base = cmp.metriques(test["valeur"], test["cams_jour"])["rmse"]

    gain_pct = 100 * (1 - rmse_test_regle / rmse_test_defaut)
    print(f"\n{'sur le test (jamais utilisé pour choisir)':44s} {'RMSE':>8s} {'gain/CAMS':>10s}")
    print(f"{'CAMS brut':44s} {base:8.3f}")
    print(f"{'LightGBM par défaut':44s} {rmse_test_defaut:8.3f} "
          f"{100 * (1 - rmse_test_defaut / base):+9.1f} %")
    print(f"{'LightGBM réglé':44s} {rmse_test_regle:8.3f} "
          f"{100 * (1 - rmse_test_regle / base):+9.1f} %", flush=True)

    verdict = ("CONCLUANT — réglage retenu" if gain_pct >= SEUIL_ABANDON_PCT
               else f"NON CONCLUANT (< {SEUIL_ABANDON_PCT} %) — garder le défaut")
    print(f"\napport du réglage sur le test : {gain_pct:+.2f} % → {verdict}")
    if rmse_meilleur < rmse_val_defaut and gain_pct < 0:
        print("⚠️ Le réglage gagnait en validation et perd en test : c'est exactement\n"
              "   l'optimisme de sélection que la validation imbriquée sert à démasquer.",
              flush=True)

    pd.DataFrame(essais).to_csv(
        RACINE / f"reports/tuning_essais_{polluant}.csv", index=False)
    pd.DataFrame([
        {"modele": "défaut", "rmse_test": rmse_test_defaut, **defaut},
        {"modele": "réglé", "rmse_test": rmse_test_regle, **meilleur},
    ]).to_csv(RACINE / f"reports/tuning_borne_{polluant}.csv", index=False)
    print(f"\nÉcrit : reports/tuning_borne_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--essais", type=int, default=30)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.essais))
