#!/usr/bin/env python3
"""Jusqu'où peut-on pousser la détection des vrais dépassements ?

La question, posée correctement
-------------------------------
Détecter plus n'a de sens qu'à **budget de fausses alertes fixé** : n'importe quel modèle
atteint 100 % de rappel en annonçant tous les jours. La question utile est donc *combien de
dépassements réels attrape-t-on sans dépasser un taux de fausse alerte donné ?*

Le dossier établit déjà qu'à 30 % de fausses alertes, la correction attrape **47,6 %** des
dépassements contre **21,2 %** pour CAMS brut. C'est 2,2 fois mieux — et c'est encore moins
d'un sur deux.

Les deux leviers jamais combinés
--------------------------------
Deux mesures séparées améliorent nettement la détection, et aucune n'a été testée avec l'autre :

1. **Classer plutôt que régresser.** Prédire la probabilité de dépassement au lieu de seuiller
   une concentration prédite porte le POD de 0,483 à 0,641 à protocole égal. La raison est
   mécanique : une régression au moindre carré écrase les extrêmes, et le seuil tombe alors du
   mauvais côté.
2. **L'observation récente.** Elle rend +8,9 % sur O₃ et +21,9 % sur NO₂, et sur le rejeu du
   26/07 elle **récupère une alerte** que la correction actuelle avait détruite.

Ce script les combine et mesure les quatre produits **au même budget de fausses alertes** — la
seule comparaison qu'un service puisse utiliser.

**Le point de fonctionnement est choisi hors échantillon** : le seuil est fixé sur d'autres
stations que celles où il est appliqué. Le mesurer sur les données qui l'évaluent fabriquerait
un score, défaut déjà corrigé ailleurs dans ce projet.

Usage : python3 scripts/detection_maximale.py [--polluant O3]
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

from apport_observation_veille import variables_passees  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402
from scores_episodes import scores  # noqa: E402

# Seuils de détection, choisis pour que le problème **existe**.
#
# Le seuil d'information horaire du NO₂ (200 µg/m³) donne **2 dépassements sur 161 637
# jours-station** : le test y est dégénéré, aucun budget de fausse alerte n'est atteignable, et
# le résultat ne dit rien de la méthode. On retient le seuil du sous-indice ATMO « mauvais »,
# **120 µg/m³**, qui est celui sur lequel un service communique.
#
# La leçon vaut au-delà du NO₂ : un seuil sans événements ne mesure pas une incapacité à
# détecter, il mesure l'absence de ce qu'on cherche à détecter. Vérifier le nombre de positifs
# **avant** de conclure d'une détection.
SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0}
BUDGETS = (0.10, 0.20, 0.30, 0.40)


def ajuster(j: pd.DataFrame, predicteurs: list[str], cible: np.ndarray,
            n_plis: int, mode: str = "regression", quantile: float = 0.90) -> np.ndarray:
    """Prédiction hors échantillon par groupes de stations exclues.

    Quatre modes, et le troisième corrige une erreur de catégorie du projet. Le **quantile
    0,90** avait été écarté parce que son RMSE valait 20,90, pire que CAMS brut — mais c'est
    juger un **détecteur** sur un critère de **prédiction ponctuelle**. Une prédiction au
    quantile 0,90 est construite pour se placer haut : mauvaise à l'unité près, potentiellement
    excellente pour ordonner les jours à risque. C'est la même faute que d'avoir seuillé la
    régression à 120 µg/m³ alors qu'un moindre carré n'y monte presque jamais.
    """
    from xgboost import XGBClassifier, XGBRegressor

    sortie = np.full(len(j), np.nan)
    commun = dict(n_estimators=REGLE["n_estimators"], learning_rate=REGLE["learning_rate"],
                  max_depth=10, min_child_weight=REGLE["min_child_samples"],
                  reg_lambda=REGLE["reg_lambda"], subsample=0.8, colsample_bytree=0.8,
                  tree_method="hist", device="cuda", random_state=0, verbosity=0)
    for g in range(n_plis):
        test = (j["groupe"] == g).to_numpy()
        x_train, x_test = j.loc[~test, predicteurs], j.loc[test, predicteurs]
        if mode == "classification":
            m = XGBClassifier(**commun)
            m.fit(x_train, cible[~test])
            sortie[test] = m.predict_proba(x_test)[:, 1]
            continue

        poids = None
        parametres = dict(commun)
        if mode == "ponderee":
            # Poids croissants avec la concentration observée. La forme `1 + obs/moyenne`
            # plutôt que `obs/moyenne` : le maximum journalier 8 h **peut valoir zéro**, et
            # XGBoost refuse un poids nul — « Weights must be positive values ». Le `+1`
            # garantit la stricte positivité sans changer l'ordre ni écraser le contraste
            # entre journées calmes et journées chargées.
            obs = j.loc[~test, "obs_jour"].to_numpy()
            poids = 1.0 + obs / max(obs.mean(), 1e-6)
        elif mode == "quantile":
            parametres |= {"objective": "reg:quantileerror", "quantile_alpha": quantile}
        m = XGBRegressor(**parametres)
        m.fit(x_train, cible[~test], sample_weight=poids)
        sortie[test] = np.clip(
            j.loc[test, "cams_jour"] + m.predict(x_test), 0, None)
    return sortie


def rappel_hors_echantillon(vrai: np.ndarray, score: np.ndarray, groupe: np.ndarray,
                            budget: float, n_plis: int) -> dict:
    """Rappel à budget imposé, seuil choisi sur d'**autres stations** que celles évaluées."""
    grille = np.unique(np.quantile(score, np.linspace(0.50, 0.9995, 300)))
    annonce = np.zeros(len(score), dtype=bool)
    seuils = []
    for g in range(n_plis):
        test = groupe == g
        if test.sum() == 0 or (~test).sum() == 0:
            continue
        meilleur, pod = None, -1.0
        for s in grille:
            m = scores(vrai[~test], score[~test] >= s)
            far = m.get("FAR")
            if far is None or np.isnan(far) or far > budget:
                continue
            if (m.get("POD") or 0) > pod:
                meilleur, pod = float(s), m["POD"]
        if meilleur is None:
            continue
        seuils.append(meilleur)
        annonce[test] = score[test] >= meilleur
    if not seuils:
        return {}
    m = scores(vrai, annonce)
    return {"POD": m["POD"], "FAR": m["FAR"], "CSI": m["CSI"],
            "n_alertes": int(annonce.sum()), "n_seuils": len(seuils)}


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    seuil = SEUILS[polluant]
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    passees, noms = variables_passees(j)
    j["jour"] = pd.to_datetime(j["jour"])
    j = j.merge(passees, on=["station_id", "jour"], how="left").dropna(subset=noms)

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    vrai = (j["obs_jour"] >= seuil).to_numpy()
    groupe = j["groupe"].to_numpy()
    print(f"{polluant} · {len(j):,} jours-station · {len(stations)} stations · "
          f"{int(vrai.sum())} dépassements ({100 * vrai.mean():.2f} %)\n", flush=True)

    residu = (j["obs_jour"] - j["cams_jour"]).to_numpy()
    plan = [
        ("régression", base, residu, "regression"),
        ("régression + obs", base + noms, residu, "regression"),
        ("classification + obs", base + noms, vrai.astype(int), "classification"),
        ("pondérée + obs", base + noms, residu, "ponderee"),
        ("quantile 0,90 + obs", base + noms, residu, "quantile"),
    ]
    produits = {"CAMS brut": j["cams_jour"].to_numpy()}
    for nom, predicteurs, cible, mode in plan:
        produits[nom] = ajuster(j, predicteurs, cible, n_plis, mode)
        print(f"  {nom} ajusté · {time.time() - depart:.0f}s", flush=True)
    print(flush=True)

    lignes = []
    for budget in BUDGETS:
        print(f"── budget de fausses alertes ≤ {budget:.0%} ──")
        print(f"{'produit':24s} {'rappel':>8s} {'FAR':>7s} {'CSI':>7s} {'alertes':>9s}")
        for nom, score in produits.items():
            r = rappel_hors_echantillon(vrai, score, groupe, budget, n_plis)
            if not r:
                print(f"{nom:24s} {'—':>8s}   budget inatteignable")
                lignes.append({"budget": budget, "produit": nom})
                continue
            print(f"{nom:24s} {r['POD']:8.3f} {r['FAR']:7.3f} {r['CSI']:7.3f} "
                  f"{r['n_alertes']:9,}", flush=True)
            lignes.append({"budget": budget, "produit": nom, **r})
        print()

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/detection_maximale_{polluant}.csv", index=False)

    print("=" * 74)
    reference = table[table["produit"] == "CAMS brut"].set_index("budget")["POD"]
    for budget in BUDGETS:
        s = table[(table["budget"] == budget) & table["POD"].notna()]
        if s.empty:
            continue
        g = s.loc[s["POD"].idxmax()]
        base_pod = reference.get(budget, np.nan)
        facteur = g["POD"] / base_pod if base_pod and base_pod > 0 else np.nan
        print(f"à {budget:.0%} : **{g['produit']}** rappelle {g['POD']:.3f}"
              + (f" — {facteur:.1f}× le CAMS brut" if not np.isnan(facteur) else ""))
    print(f"\nÉcrit : reports/detection_maximale_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
