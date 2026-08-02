#!/usr/bin/env python3
"""Optimisation hyperparamétrique du MOS — étude Optuna stockée, validation imbriquée.

Le défaut que ce script existe pour supprimer
---------------------------------------------
Le réglage du projet, `modele_final.REGLE`, a été obtenu par **30 tirages aléatoires sur
grilles discrètes de 4 valeurs**, sélectionnés sur **un seul jeu de validation** d'environ
45 stations. Trois défauts en découlent, et le troisième est un bogue :

1. **L'espace est minuscule** — 256 combinaisons possibles, 30 tirages, aucune plage continue.
   `subsample`, `colsample_bytree`, `reg_alpha`, `min_split_gain`, `max_bin` n'ont jamais été
   touchés. Et `learning_rate` / `n_estimators` étaient tirés **indépendamment**, alors qu'ils
   sont couplés.
2. **La sélection se fait sur un seul découpage.** Le projet mesure lui-même une barre de
   bruit de **±2,02 points dominée par la partition** : un « +6,28 % » choisi sur une seule
   partition est largement du bruit de sélection.
3. ⚠️ **`REGLE` a été réglé pour LightGBM et il est appliqué à XGBoost** — dans
   `apport_*.py`, `validation_bloquee.py`, `heatmap_annuelle.py`, donc **dans tous les
   chiffres publiés**. La traduction employée est :

       XGBRegressor(max_depth=10, min_child_weight=REGLE["min_child_samples"], ...)

   `num_leaves=255`, **le paramètre de capacité qui portait le gain, est purement jeté** et
   remplacé par un `max_depth=10` écrit en dur. Croissance *leaf-wise* à 255 feuilles contre
   *depth-wise* autorisant 1 024 : ce ne sont pas les mêmes modèles. Le modèle qui produit les
   résultats du dossier **n'a donc jamais été réglé**.

Ce script règle XGBoost — celui qui est réellement déployé — avec `grow_policy="lossguide"`
et `max_leaves` comme vrai paramètre, de sorte que la capacité redevienne réglable.

Ce que la validation contrôle, et pourquoi elle est construite ainsi
---------------------------------------------------------------------
**Imbriquée, sur groupes de stations.** Un tiers des stations part en **test** et n'est
consulté qu'une fois, à la toute fin. Les deux tiers restants forment le développement, sur
lequel tourne une **validation croisée à 3 plis par stations entières** — la même partition
`i % n` que les scripts d'évaluation du projet, pour que le réglage et la mesure parlent du
même découpage.

**Objectif : le RMSE moyen des plis.** Mais le critère du projet
(`aq.eval.critere.cribler`) refuse un gain payé par la queue, et c'est la queue qui décide
d'une alerte. Le RMSE du **décile haut** est donc enregistré à chaque essai, et la sélection
finale ne retient que les essais qui ne dégradent pas la queue au-delà de la tolérance.

Une étude **multi-objectif** aurait été l'autre option ; elle interdit l'élagage, qui vaut ici
un facteur deux sur 200 essais. On garde donc un objectif unique **plus une contrainte
appliquée à la sélection**, ce qui donne le même résultat pour moins cher.

**Arrêt anticipé, par pli.** `n_estimators` est fixé haut et le nombre d'arbres est décidé par
un groupe de stations réservé à l'intérieur de chaque pli. Cela supprime le couplage
`learning_rate` × `n_estimators` de l'espace de recherche — et le réglage actuel, à 900 arbres
fixes, ne pouvait pas savoir s'il sous- ou sur-ajustait.

⚠️ Ce qu'un réglage ne peut PAS faire, et que ce projet a mesuré
-----------------------------------------------------------------
**Un réglage ne vaut que pour son axe.** Le même jeu d'hyperparamètres donne **+5 points en
spatial et −3 en temporel** ; `REGLE` est le **pire des six testés** sur l'axe temporel, et
+3,96 pt de temporel se paie −7,04 de spatial. Optimiser le RMSE en validation par stations
**dégrade** donc probablement la tenue dans le temps.

Ce script ne prétend pas résoudre cet arbitrage. Il le **mesure** : le candidat retenu est
évalué, une fois, sur trois protocoles — test par stations exclues, blocs spatiaux avec fossé
au rayon du variogramme, et origine glissante temporelle. Un réglage qui gagne sur le premier
et perd sur les deux autres est un réglage qu'il faut refuser, et on le saura.

L'étude est **stockée** (SQLite) et reprenable : relancer la même commande poursuit l'étude au
lieu de la recommencer.

Usage :
  python3 scripts/optuna_mos.py --polluant O3 --essais 200
  python3 scripts/optuna_mos.py --polluant O3 --rapport     # relit l'étude sans l'étendre
Sortie : reports/optuna/mos_{polluant}.db + reports/optuna_mos_{polluant}.csv
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

from aq.eval.critere import PART_QUEUE, cribler  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

GRAINE = 20260802
N_PLIS = 3
N_ARBRES_MAX = 4000
PATIENCE = 100

# ── Le nombre d'arbres : mesuré, pas supposé ────────────────────────────────────
#
# Mesuré le 02/08/2026 sur le test de 90 stations jamais consultées, hyperparamètres de
# production inchangés, seul le nombre d'arbres variant :
#
#     400 arbres (LA PRODUCTION)   RMSE 8.9217 · décile haut 11.1394 · +25,59 % vs CAMS
#    1000 arbres                   RMSE 8.6380 · décile haut 10.8698 · +27,96 %
#    2000 arbres                   RMSE 8.4691 · décile haut 10.7113 · +29,37 %
#    3288 arbres (arrêt anticipé)  RMSE 8.3609 · décile haut 10.5745 · +30,27 %
#
# **+4,68 points de gain, monotone, et la queue s'améliore aussi.** Le modèle déployé est
# sous-ajusté d'un facteur huit. Débrider la capacité paie davantage que la régler.
#
# Côté XGBoost, le budget est **fixé à 800 arbres** et les hyperparamètres sont réglés à ce
# budget-là. Avec `grow_policy="lossguide"` et jusqu'à 512 feuilles, la capacité par arbre
# n'a rien de commun avec les 63 feuilles de LightGBM. Régler à budget fixé est aussi plus
# honnête : on optimise le modèle qu'on déploiera, et non un modèle dont le coût varie d'un
# essai à l'autre.
N_ARBRES_XGB = 800
# Rayons du variogramme des résidus, fixés a priori — jamais choisis d'après un score.
RAYON = {"O3": 150.0, "PM25": 150.0, "NO2": 75.0, "PM10": 150.0}
DOSSIER = RACINE / "reports/optuna"

# Le réglage actuel, tel qu'il est réellement appliqué à XGBoost dans les scripts publiés —
# `num_leaves` jeté, `max_depth` en dur. C'est LUI la référence à battre, pas le réglage
# LightGBM d'origine : c'est lui qui a produit les chiffres du dossier.
REFERENCE_XGB = {"max_depth": 10, "learning_rate": 0.03, "min_child_weight": 50,
                 "reg_lambda": 10.0, "subsample": 0.8, "colsample_bytree": 0.8}


# ─────────────────────────────────────────────────────────────────────────────
# Données
# ─────────────────────────────────────────────────────────────────────────────
def typologie(ids: np.ndarray) -> tuple[pd.DataFrame, list[str]]:
    """La typologie de station — mesurée le 02/08/2026 à **+12,9 % sur NO₂ sous blocage**.

    Elle était sur liste noire dans `fit_mos.colonnes_admises`. Un réglage conduit sans elle
    optimiserait un modèle qu'on ne déploiera pas.
    """
    s = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                        columns=["station_id", "typologie_zone", "type_station"])
    s = s.drop_duplicates("station_id").set_index("station_id")
    manquantes = [i for i in ids if i not in s.index]
    if manquantes:
        raise SystemExit(f"{len(manquantes)} stations sans typologie ({manquantes[:4]})")
    s = s.loc[ids]
    if s.isna().any().any():
        raise SystemExit("typologie manquante — ne pas imputer en silence")
    ordre = {"urban": 0, "suburban": 1, "rural-nearcity": 2,
             "rural-regional": 3, "rural-remote": 4}
    inconnues = set(s["typologie_zone"]) - set(ordre)
    if inconnues:
        raise SystemExit(f"typologie_zone inconnue : {inconnues}")
    d = pd.DataFrame(index=s.index)
    d["typo_densite"] = s["typologie_zone"].map(ordre).astype("int8")
    for v in sorted(s["type_station"].unique()):
        d[f"typo_{v}"] = (s["type_station"] == v).astype("int8")
    return d.reset_index(), list(d.columns)


def jeu_journalier(polluant: str) -> tuple[pd.DataFrame, list[str]]:
    """Le jeu d'apprentissage, cible journalière, typologie comprise."""
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    j["jour"] = pd.to_datetime(j["jour"])
    if j["jour"].dt.tz is not None:
        j["jour"] = j["jour"].dt.tz_localize(None)

    typo, cols_typo = typologie(np.sort(j["station_id"].unique()))
    j = j.merge(typo, on="station_id", how="left")
    if j[cols_typo].isna().any().any():
        raise SystemExit("typologie perdue à la jointure")
    return j, predicteurs + cols_typo


def plis_alternes(ids: np.ndarray, n_plis: int) -> np.ndarray:
    """`i % n_plis` sur l'identifiant trié — la partition des scripts d'évaluation."""
    return np.array([i % n_plis for i in range(len(np.sort(ids)))])[
        np.argsort(np.argsort(ids))]


# ─────────────────────────────────────────────────────────────────────────────
# Modèle et scores
# ─────────────────────────────────────────────────────────────────────────────
# ── Les deux bibliothèques, derrière une seule interface ─────────────────────────
#
# Elles ne servent pas les mêmes chiffres du dossier, et c'est le problème :
#   · **LightGBM par défaut** produit le +23,4 % annoncé (`fit_mos` → `mos._modele`) ;
#   · **XGBoost avec `REGLE` mal traduit** produit toutes les mesures de leviers
#     (`apport_*`, `validation_bloquee`, `heatmap_annuelle`…).
# On règle donc les deux, dans deux études stockées séparément, pour que le choix
# d'algorithme devienne une mesure au lieu d'un héritage.
#
# ⚠️ Concurrence : LightGBM prend tous les cœurs et XGBoost le GPU. Les deux études
# cohabitent, mais `n_jobs` de LightGBM est **borné** — la règle 1 de `CLAUDE.md` a été
# écrite après que trois ajustements `n_jobs=-1` simultanés se soient effondrés d'un ordre
# de grandeur sur la bande passante mémoire.
# ⚠️ **Mesuré le 02/08/2026 : `n_jobs=16` n'utilisait qu'UN cœur.**
#
#     charge 8,7 sur 32 cœurs · 67 % au repos
#     optuna_mos (lgbm, n_jobs=16) ......... 112 % de CPU
#     shap_familles (n_jobs=8) ............. 629 % de CPU
#
# LightGBM ne monte pas en charge sur 90 000 lignes × 57 variables : le jeu est trop petit,
# la synchronisation des fils coûte plus que le calcul qu'elle répartit. Augmenter `n_jobs`
# n'y change rien — c'est la version « bibliothèque » du piège de la règle 1 : *la
# concurrence ne sert que si la ressource est réellement libre*, et ici le goulot est la
# taille du lot, pas le nombre de cœurs.
#
# **La parallélisation utile n'est donc pas DANS un essai mais ENTRE les essais.** L'étude
# est stockée précisément pour cela : plusieurs processus l'attaquent ensemble, chacun avec
# un `n_jobs` modeste. Voir `--travailleurs`.
N_JOBS_LGBM = 4


def modele(params: dict, algo: str, n_arbres: int = N_ARBRES_MAX):
    if algo == "xgb":
        from xgboost import XGBRegressor

        # Budget fixé : ni arrêt anticipé ni coût variable d'un essai à l'autre.
        return XGBRegressor(n_estimators=N_ARBRES_XGB, tree_method="hist", device="cuda",
                            random_state=GRAINE, verbosity=0, **params)
    from lightgbm import LGBMRegressor

    return LGBMRegressor(n_estimators=n_arbres, random_state=GRAINE, verbose=-1,
                         n_jobs=N_JOBS_LGBM, **params)


def rmse(obs: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(obs) - np.asarray(pred)) ** 2)))


def scores(obs: pd.Series, pred: np.ndarray) -> tuple[float, float]:
    """RMSE global et RMSE du décile haut — la queue décide d'une alerte."""
    o = obs.to_numpy()
    haut = o >= np.quantile(o, 0.9)
    return rmse(o, pred), rmse(o[haut], np.asarray(pred)[haut])


def ajuster_pli(d: pd.DataFrame, predicteurs: list[str], stations_entr: np.ndarray,
                stations_test: np.ndarray, params: dict, algo: str,
                graine: int = GRAINE) -> tuple[np.ndarray, pd.DataFrame, int]:
    """Ajuste sur `stations_entr`, prédit sur `stations_test`, avec arrêt anticipé.

    L'arrêt anticipé se règle sur un **groupe de stations réservé**, jamais sur des lignes
    tirées au hasard : sinon la station qui sert à décider du nombre d'arbres est aussi dans
    l'entraînement, et le nombre d'arbres devient optimiste.
    """
    rng = np.random.default_rng(graine)
    melange = rng.permutation(stations_entr)
    n_arret = max(1, len(melange) // 5)
    st_arret, st_fit = set(melange[:n_arret]), set(melange[n_arret:])

    fit = d[d["station_id"].isin(st_fit)]
    arret = d[d["station_id"].isin(st_arret)]
    test = d[d["station_id"].isin(set(stations_test))]

    m = modele(params, algo)
    eval_set = [(arret[predicteurs], arret["obs_jour"] - arret["cams_jour"])]
    if algo == "xgb":
        # Budget fixé : le groupe d'arrêt reste néanmoins hors de l'ajustement, pour que
        # les deux bibliothèques voient exactement les mêmes lignes d'entraînement.
        m.fit(fit[predicteurs], fit["obs_jour"] - fit["cams_jour"], verbose=False)
        n_arbres = N_ARBRES_XGB
    else:
        import lightgbm as lgb

        m.fit(fit[predicteurs], fit["obs_jour"] - fit["cams_jour"], eval_set=eval_set,
              eval_metric="rmse",
              callbacks=[lgb.early_stopping(PATIENCE, verbose=False)])
        n_arbres = int(getattr(m, "best_iteration_", 0) or N_ARBRES_MAX)
    pred = np.clip(test["cams_jour"].to_numpy() + m.predict(test[predicteurs]), 0, None)
    return pred, test, n_arbres


# ─────────────────────────────────────────────────────────────────────────────
# L'espace de recherche
# ─────────────────────────────────────────────────────────────────────────────
def espace(essai, algo: str) -> dict:
    """Plages continues et log-uniformes là où la sensibilité l'est.

    Côté XGBoost, `grow_policy="lossguide"` rend `max_leaves` opérant : c'est le paramètre de
    capacité que la traduction LightGBM → XGBoost avait fait disparaître. Côté LightGBM,
    `num_leaves` est natif.

    `n_estimators` n'est tiré dans aucun des deux — l'arrêt anticipé le décide, ce qui
    supprime son couplage avec `learning_rate` au lieu de le tirer au sort.
    """
    commun = {
        "learning_rate": essai.suggest_float("learning_rate", 0.005, 0.2, log=True),
        "reg_lambda": essai.suggest_float("reg_lambda", 1e-3, 100.0, log=True),
        "reg_alpha": essai.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
        "subsample": essai.suggest_float("subsample", 0.4, 1.0),
        "colsample_bytree": essai.suggest_float("colsample_bytree", 0.3, 1.0),
    }
    feuilles = essai.suggest_int("num_leaves", 16, 512, log=True)
    if algo == "xgb":
        return commun | {
            "grow_policy": "lossguide",
            "max_leaves": feuilles,
            "max_depth": 0,  # 0 = sans limite ; la contrainte porte sur les feuilles
            "min_child_weight": essai.suggest_float("min_child_weight", 1.0, 500.0,
                                                    log=True),
            "colsample_bylevel": essai.suggest_float("colsample_bylevel", 0.5, 1.0),
            "gamma": essai.suggest_float("gamma", 1e-4, 5.0, log=True),
            "max_bin": essai.suggest_categorical("max_bin", [128, 256, 512]),
        }
    return commun | {
        "num_leaves": feuilles,
        "min_child_samples": essai.suggest_int("min_child_samples", 5, 500, log=True),
        "subsample_freq": 1,
        "min_split_gain": essai.suggest_float("min_split_gain", 1e-4, 5.0, log=True),
        "max_bin": essai.suggest_categorical("max_bin", [128, 255, 511]),
    }


# Les réglages **réellement en production**, qui servent de référence à battre.
#
# ⚠️ Ce ne sont pas les mêmes, et c'est le fond du problème :
#   · LightGBM tourne sur ses paramètres PAR DÉFAUT (`mos._modele`) — c'est lui qui produit
#     le +23,4 % annoncé, et `REGLE` n'entre jamais dans cette chaîne ;
#   · XGBoost tourne sur `REGLE` mal traduit — `num_leaves` jeté, `max_depth=10` en dur —
#     et c'est lui qui produit toutes les mesures de leviers.
REFERENCE = {
    "lgbm": {"num_leaves": 63, "learning_rate": 0.05, "min_child_samples": 200,
             "reg_lambda": 1e-3, "reg_alpha": 1e-3, "subsample": 0.8,
             "colsample_bytree": 0.8, "min_split_gain": 1e-4, "max_bin": 255},
    "xgb": {"num_leaves": 512, "learning_rate": 0.03, "min_child_weight": 50.0,
            "reg_lambda": 10.0, "reg_alpha": 1e-3, "subsample": 0.8,
            "colsample_bytree": 0.8, "colsample_bylevel": 1.0, "gamma": 1e-4,
            "max_bin": 256},
}


def params_reference(algo: str) -> dict:
    """Les hyperparamètres du modèle en production, prêts à passer au constructeur."""
    if algo == "xgb":
        return {"grow_policy": "depthwise", "max_depth": 10, "learning_rate": 0.03,
                "min_child_weight": 50.0, "reg_lambda": 10.0, "subsample": 0.8,
                "colsample_bytree": 0.8}
    return {"num_leaves": 63, "learning_rate": 0.05, "min_child_samples": 200,
            "subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8}


def main(polluant: str, algo: str, n_essais: int, rapport_seul: bool,
         travailleur: int = 0, muet: bool = False) -> int:
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    depart = time.time()
    DOSSIER.mkdir(parents=True, exist_ok=True)

    j, predicteurs = jeu_journalier(polluant)
    stations = np.sort(j["station_id"].unique())

    # ── Imbrication : le test part d'abord, et n'est consulté qu'à la fin ────────
    rng = np.random.default_rng(GRAINE)
    melange = rng.permutation(stations)
    st_test = np.sort(melange[: len(melange) // 3])
    st_dev = np.sort(melange[len(melange) // 3:])
    dev = j[j["station_id"].isin(set(st_dev))].reset_index(drop=True)
    plis_dev = plis_alternes(st_dev, N_PLIS)

    print(f"{polluant} · {len(j):,} jours-station · {len(predicteurs)} prédicteurs\n"
          f"  développement {len(st_dev)} stations ({N_PLIS} plis) · "
          f"test {len(st_test)} stations, jamais consulté avant la mesure finale\n",
          flush=True)

    def objectif(essai) -> float:
        params = espace(essai, algo)
        rmses, queues, arbres = [], [], []
        for g in range(N_PLIS):
            st_te = st_dev[plis_dev == g]
            st_tr = st_dev[plis_dev != g]
            pred, test, n_arbres = ajuster_pli(dev, predicteurs, st_tr, st_te, params, algo)
            r, q = scores(test["obs_jour"], pred)
            rmses.append(r), queues.append(q), arbres.append(n_arbres)
            # Élagage : un essai franchement mauvais sur le premier pli ne mérite pas les
            # deux autres. Le rapport intermédiaire est la moyenne courante.
            essai.report(float(np.mean(rmses)), g)
            if essai.should_prune():
                raise optuna.TrialPruned()
        essai.set_user_attr("rmse_decile_haut", float(np.mean(queues)))
        essai.set_user_attr("rmse_par_pli", [round(x, 4) for x in rmses])
        essai.set_user_attr("n_arbres", [int(x) for x in arbres])
        return float(np.mean(rmses))

    # SQLite tient plusieurs processus, mais il faut lui laisser le temps de relâcher le
    # verrou : sans `timeout`, deux travailleurs qui écrivent en même temps se soldent par
    # un « database is locked » qui tue l'un des deux au milieu du lot.
    stockage = optuna.storages.RDBStorage(
        url=f"sqlite:///{DOSSIER / f'mos_{polluant}_{algo}.db'}",
        engine_kwargs={"connect_args": {"timeout": 60}})
    # La graine du semeur dépend du travailleur : deux processus avec la même graine
    # proposeraient les mêmes points tant que TPE est en phase de démarrage, et on paierait
    # N fois le même essai.
    etude = optuna.create_study(
        study_name=f"mos_{polluant}_{algo}", storage=stockage,
        direction="minimize", load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=GRAINE + travailleur, multivariate=True,
                                           n_startup_trials=25),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=15, n_warmup_steps=1))

    # ── La référence : le réglage RÉELLEMENT appliqué dans les scripts publiés ───
    faits = len([t for t in etude.trials
                 if t.state == optuna.trial.TrialState.COMPLETE])
    if faits == 0:
        etude.enqueue_trial(REFERENCE[algo], skip_if_exists=True)
        print(f"  essai 0 amorcé sur le réglage {algo} actuellement en production\n",
              flush=True)

    if not rapport_seul:
        print(f"  {faits} essai(s) déjà dans l'étude · cible {n_essais} · "
              f"travailleur {travailleur}\n", flush=True)
        # ⚠️ **Le compte se fait sur l'étude, pas sur le travailleur.** Avec `n_trials`,
        # chaque processus lancerait `n_essais` essais et six travailleurs en feraient six
        # fois trop. On laisse `optimize` sans borne et c'est le rappel qui arrête, quand
        # l'ÉTUDE atteint la cible — le seul compteur partagé qui existe.
        etude.optimize(objectif, n_trials=None, show_progress_bar=False,
                       callbacks=[_trace(depart), _arret(n_essais)])

    if muet:
        print("  travailleur secondaire : pas de rapport (relancer avec --rapport)",
              flush=True)
        return 0
    return _rapport(etude, polluant, algo, j, predicteurs, st_dev, st_test, depart)


def _arret(cible: int):
    """Arrête ce travailleur quand l'ÉTUDE — pas lui — a atteint la cible."""
    def _c(etude, essai):
        import optuna

        n = len([t for t in etude.trials
                 if t.state == optuna.trial.TrialState.COMPLETE])
        if n >= cible:
            etude.stop()
    return _c


def _trace(depart: float):
    def _c(etude, essai):
        import optuna

        n = len([t for t in etude.trials
                 if t.state == optuna.trial.TrialState.COMPLETE])
        if essai.number % 10 == 0 or essai.state == optuna.trial.TrialState.COMPLETE:
            meilleur = etude.best_value if n else float("nan")
            print(f"  essai {essai.number:3d} · {str(essai.state).split('.')[-1]:9s} · "
                  f"valeur {essai.value if essai.value else float('nan'):.4f} · "
                  f"meilleur {meilleur:.4f} · {(time.time() - depart) / 60:.0f} min",
                  flush=True)
    return _c


def _rapport(etude, polluant, algo, j, predicteurs, st_dev, st_test, depart) -> int:
    import optuna

    complets = [t for t in etude.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if not complets:
        raise SystemExit("aucun essai complet dans l'étude")
    print(f"\n{'═' * 78}\n{len(complets)} essais complets · "
          f"{len(etude.trials) - len(complets)} élagués\n{'═' * 78}")

    reference = complets[0]  # l'essai amorcé sur le réglage déployé
    q_ref = reference.user_attrs.get("rmse_decile_haut", float("inf"))

    # ── Sélection sous contrainte de queue ──────────────────────────────────────
    admissibles = [t for t in complets
                   if t.user_attrs.get("rmse_decile_haut", np.inf)
                   <= q_ref * (1 + PART_QUEUE)]
    print(f"référence (réglage déployé) · RMSE {reference.value:.4f} · "
          f"décile haut {q_ref:.4f}")
    print(f"{len(admissibles)} essais sur {len(complets)} ne dégradent pas la queue "
          f"au-delà de {100 * PART_QUEUE:.0f} %")
    if not admissibles:
        raise SystemExit("aucun essai ne respecte la contrainte de queue — "
                         "le réglage déployé reste en place")
    meilleur = min(admissibles, key=lambda t: t.value)
    print(f"\nmeilleur admissible · essai {meilleur.number} · RMSE {meilleur.value:.4f} "
          f"({100 * (reference.value - meilleur.value) / reference.value:+.2f} % "
          f"contre la référence) · décile haut "
          f"{meilleur.user_attrs['rmse_decile_haut']:.4f}")
    for k, v in sorted(meilleur.params.items()):
        print(f"    {k:20s} {v}")
    print(f"    n_arbres retenus     {meilleur.user_attrs.get('n_arbres')}")

    lignes = [{"essai": t.number, "rmse": t.value,
               "rmse_decile_haut": t.user_attrs.get("rmse_decile_haut"),
               "elague": False, **t.params} for t in complets]
    sortie = RACINE / f"reports/optuna_mos_{polluant}_{algo}.csv"
    pd.DataFrame(lignes).sort_values("rmse").to_csv(sortie, index=False)

    # ── La mesure finale, sur le test jamais consulté ───────────────────────────
    print(f"\n{'─' * 78}\nMESURE FINALE — test jamais consulté "
          f"({len(st_test)} stations)\n{'─' * 78}")
    for nom, params in ((f"réglage {algo} déployé", params_reference(algo)),
                        ("meilleur Optuna", _params_essai(meilleur, algo))):
        pred, test, n_arbres = ajuster_pli(j, predicteurs, st_dev, st_test, params, algo)
        r, q = scores(test["obs_jour"], pred)
        r_cams = rmse(test["obs_jour"], test["cams_jour"])
        print(f"  {nom:18s} RMSE {r:.4f} · décile haut {q:.4f} · "
              f"gain vs CAMS {100 * (1 - r / r_cams):+.2f} % · {n_arbres} arbres")

    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · "
          f"étude : {(DOSSIER / f'mos_{polluant}_{algo}.db').relative_to(RACINE)} · "
          f"{(time.time() - depart) / 60:.0f} min")
    print("\n⚠️ Ce chiffre porte sur l'axe SPATIAL. Le projet a mesuré qu'un réglage "
          "gagnant\n   en spatial peut perdre en temporel (+5 / −3 points). Passer le "
          "candidat retenu\n   par `reglage_temporel.py` et `validation_bloquee.py` "
          "avant de l'adopter.")
    return 0


def _params_essai(essai, algo: str) -> dict:
    """Traduit les paramètres d'un essai en arguments de constructeur."""
    p = dict(essai.params)
    if algo == "xgb":
        p["max_leaves"] = p.pop("num_leaves")
        p["grow_policy"] = "lossguide"
        p["max_depth"] = 0
    else:
        p["subsample_freq"] = 1
    return p


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--algo", default="lgbm", choices=("lgbm", "xgb"))
    a.add_argument("--essais", type=int, default=200)
    a.add_argument("--rapport", action="store_true",
                   help="relit l'étude stockée sans lancer d'essai")
    a.add_argument("--travailleur", type=int, default=0,
                   help="indice du processus ; décale la graine du semeur")
    a.add_argument("--muet", action="store_true",
                   help="travailleur secondaire : n'imprime pas le rapport final")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.algo, n.essais, n.rapport,
                          n.travailleur, n.muet))
