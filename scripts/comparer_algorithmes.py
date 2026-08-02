#!/usr/bin/env python3
"""LightGBM était-il le bon choix ? Comparaison d'algorithmes à protocole identique.

Pourquoi ce script existe
-------------------------
Le projet emploie le gradient boosting sans jamais l'avoir comparé à quoi que ce soit.
On pouvait donc dire « il fonctionne », pas « c'était le bon choix ». La littérature rend
la question sérieuse plutôt qu'académique : Bertrand et al. (2023,
doi:10.5194/acp-23-5317-2023, tableau 2) trouvent la **régression ridge ou LASSO
meilleure** que le boosting pour plusieurs cibles de post-traitement CAMS, et la forêt
aléatoire meilleure sur les cibles horaires. Le boosting n'y est pas vainqueur général,
**même face à des modèles simples**.

Ce que la comparaison isole : la part du gain due à la **non-linéarité**. Si le modèle
linéaire suit de près, le gain vient des variables, non de l'algorithme — et c'est une
information qui vaut mieux qu'un point de RMSE.

**Protocole strictement identique** pour tous les candidats, via
`mos.ajuster_par_stations_exclues` : mêmes plis de stations exclues, même cible résiduelle
`observation − CAMS`, même écrêtage à zéro. Un modèle linéaire exige en plus une imputation
et une mise à l'échelle, que le boosting n'a pas besoin — elles sont dans son pipeline, pas
dans le protocole.

Usage : python3 scripts/comparer_algorithmes.py [--polluant O3] [--plis 3]
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
from fit_mos import charger, colonnes_admises  # noqa: E402


def _lineaire(graine: int):
    """Ridge, avec le prétraitement qu'un modèle linéaire exige.

    **Pourquoi un rang et non un écart-type.** Le pipeline du projet remplace les valeurs
    infinies par la sentinelle `30_000` — un choix taillé pour des arbres, qui ne
    regardent que l'ordre des valeurs. Passé dans un `StandardScaler`, un seul 30 000 au
    milieu de valeurs de l'ordre de la dizaine écrase l'échelle de toute la colonne et
    ruine la régression : mesuré en passe unitaire, le ridge tombait à **−32,6 %** de gain,
    c'est-à-dire pire que de ne rien corriger. Ce n'était pas une propriété du modèle
    linéaire mais un artefact du prétraitement.

    `QuantileTransformer` range les valeurs plutôt qu'il ne les centre : une sentinelle
    devient « la plus grande valeur », sans levier démesuré. La comparaison porte alors sur
    les algorithmes et non sur leur tolérance aux valeurs extrêmes.

    Imputation et transformation sont ajustées **dans le pli d'entraînement**, puisqu'elles
    font partie du pipeline : aucune statistique du test ne fuit vers l'apprentissage.

    **Pourquoi `RidgeCV` et non `Ridge`.** Le gradient boosting du projet a des
    hyperparamètres choisis avec soin ; lui opposer un ridge à `alpha=1.0` par défaut ne
    serait pas une comparaison d'algorithmes mais une comparaison entre un modèle réglé et
    un modèle non réglé. Or la régularisation est précisément ce qui bride l'extrapolation
    — et l'extrapolation est ce qui pénalise le linéaire sur des stations jamais vues
    (mesuré : corrections jusqu'à −45,6 µg/m³ pour un résidu réel d'écart-type 15,3).
    `RidgeCV` choisit `alpha` par validation généralisée **sur le pli d'entraînement seul**.
    """
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import RidgeCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import QuantileTransformer

    return make_pipeline(
        SimpleImputer(strategy="median"),
        QuantileTransformer(
            n_quantiles=1000, output_distribution="normal",
            subsample=200_000, random_state=graine,
        ),
        RidgeCV(alphas=(1.0, 10.0, 100.0, 1_000.0, 10_000.0, 100_000.0)),
    )


def _foret(graine: int):
    """Forêt aléatoire — l'architecture que Bertrand et al. trouvent la meilleure en horaire.

    Bornée à 200 000 lignes par arbre et 300 arbres : sur 3 M de lignes, une forêt sans
    borne demanderait des heures pour un résultat que ce nombre d'échantillons établit
    déjà.
    """
    from sklearn.ensemble import RandomForestRegressor

    return RandomForestRegressor(
        n_estimators=300,
        max_samples=200_000,
        min_samples_leaf=50,
        max_features=0.5,
        random_state=graine,
        n_jobs=-1,
    )


def _xgboost(graine: int):
    """XGBoost sur GPU, **paramètres miroir** de ceux du LightGBM du projet.

    Profondeur 8 pour ~63 feuilles, même pas d'apprentissage, mêmes taux
    d'échantillonnage, même minimum d'observations par feuille : l'écart mesuré est alors
    celui des implémentations, non celui de deux réglages différents.
    """
    from xgboost import XGBRegressor

    return XGBRegressor(
        n_estimators=400, learning_rate=0.05, max_depth=8,
        min_child_weight=200, subsample=0.8, colsample_bytree=0.8,
        tree_method="hist", device="cuda",
        random_state=graine, verbosity=0,
    )


def _catboost(graine: int):
    """CatBoost sur GPU. Réputé robuste sans réglage — on le prend au mot, sans tuning."""
    from catboost import CatBoostRegressor

    return CatBoostRegressor(
        iterations=400, learning_rate=0.05, depth=8,
        task_type="GPU", devices="0",
        random_seed=graine, verbose=0, allow_writing_files=False,
    )


def _realmlp(graine: int):
    """RealMLP en réglages par défaut ajustés (Holzmüller et al.), via pytabkit, sur GPU.

    C'est le réseau de neurones tabulaire qui conteste sérieusement le boosting dans la
    littérature récente. Les variantes `_TD_` portent des hyperparamètres réglés par les
    auteurs sur des dizaines de jeux : les employer tels quels est plus équitable qu'un
    réglage improvisé, et évite de comparer un modèle soigné à un modèle bâclé.

    Un réseau ne tolère ni les valeurs manquantes ni la sentinelle `30_000` du projet —
    d'où l'imputation et le rangement par quantiles, comme pour le ridge.
    """
    from pytabkit import RealMLP_TD_Regressor
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import QuantileTransformer

    return make_pipeline(
        SimpleImputer(strategy="median"),
        QuantileTransformer(
            n_quantiles=1000, output_distribution="normal",
            subsample=200_000, random_state=graine,
        ),
        RealMLP_TD_Regressor(device="cuda", random_state=graine, verbosity=0),
    )


def _tabm(graine: int):
    """TabM — ensemble paramétriquement efficace, l'un des meilleurs réseaux tabulaires 2024."""
    from pytabkit import TabM_D_Regressor
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import QuantileTransformer

    return make_pipeline(
        SimpleImputer(strategy="median"),
        QuantileTransformer(
            n_quantiles=1000, output_distribution="normal",
            subsample=200_000, random_state=graine,
        ),
        TabM_D_Regressor(device="cuda", random_state=graine, verbosity=0),
    )


CANDIDATS = {
    "LightGBM (référence)": None,       # None → la fabrique par défaut du module
    "Ridge (linéaire)": _lineaire,
    "Forêt aléatoire": _foret,
    "XGBoost (GPU)": _xgboost,
    "CatBoost (GPU)": _catboost,
    "RealMLP (GPU)": _realmlp,
    "TabM (GPU)": _tabm,
}


def main(polluant: str, horizon: int, n_plis: int) -> int:
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    base = cmp.metriques(jeu["valeur"], jeu["cams"])
    print(f"{polluant} J+{horizon} · {len(jeu):,} paires · "
          f"{jeu['station_id'].nunique()} stations · {len(colonnes)} variables · "
          f"{n_plis} plis de stations exclues\n", flush=True)
    print(f"{'algorithme':22s} {'RMSE':>7s} {'R²':>8s} {'gain/CAMS':>10s} {'durée':>8s}")
    print(f"{'CAMS brut':22s} {base['rmse']:7.2f} {base['r2']:+8.3f}", flush=True)

    lignes = [{"algorithme": "CAMS brut", **base}]
    for nom, fabrique in CANDIDATS.items():
        depart = time.time()
        try:
            resultat = mos.ajuster_par_stations_exclues(
                jeu, colonnes, colonne_cams="cams", n_plis=n_plis,
                fabrique_modele=fabrique, verbeux=False,
            )
        except Exception as erreur:  # noqa: BLE001 — un candidat qui échoue ne doit pas
            print(f"{nom:22s} ÉCHEC : {erreur}", flush=True)   # emporter les autres
            continue

        p = resultat.predictions.dropna(subset=["observe"])
        m = cmp.metriques(p["observe"], p["corrige"])
        gain = 100 * (1 - m["rmse"] / base["rmse"])
        duree = time.time() - depart
        print(f"{nom:22s} {m['rmse']:7.2f} {m['r2']:+8.3f} {gain:+9.1f} % "
              f"{duree:7.0f}s", flush=True)
        lignes.append({"algorithme": nom, "gain_pct": gain, "duree_s": duree, **m})

    sortie = RACINE / f"reports/comparaison_algorithmes_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
