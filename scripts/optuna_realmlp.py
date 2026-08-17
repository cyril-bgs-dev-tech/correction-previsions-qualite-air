#!/usr/bin/env python3
"""Réglage Optuna de RealMLP — sur l'axe TEMPOREL, et sur lui seul.

Pourquoi ce script existe, et pourquoi il ne ressemble pas à `optuna_mos.py`
-----------------------------------------------------------------------------
`optuna_mos.py` règle LightGBM par validation imbriquée sur des **groupes de stations**
(axe SPATIAL). Ce dépôt a mesuré, sur deux protocoles indépendants, que le gain qu'on y
trouve **ne transfère pas** : +4 à +7 % en spatial, ~0 en temporel (§ 10 septies de
`VERITE_DOSSIER`), et `défaut` bat `optuna` 3/3 en temporel dans la table à quatre
configurations de `double_aveugle_journalier`.

Régler RealMLP sur le même axe reproduirait le même mirage. L'objectif ici est donc la
RMSE sur un **hors-échantillon temporel** — ajustement sur la 1ʳᵉ moitié du calendrier,
notation sur un groupe de jours réservé **antérieur** à la coupure, jamais postérieur.

⚠️ **Et le réglage n'est lancé qu'après avoir constaté que les défauts déçoivent.**
RealMLP-TD vient d'un article intitulé *Better by Default* ; balayer 200 essais d'emblée
serait réintroduire le défaut qu'on vient de corriger. La mesure qui justifie ce script :
aux hyperparamètres du notebook (`lr=0.01`), RealMLP rend 12,5520 contre 12,3882 pour
LightGBM sur NO₂ ; à `lr=0.001` il passe à 12,3295. Le pas d'apprentissage du notebook,
calibré sur un jeu Kaggle bien plus petit, est donc **hors régime** ici — c'est cela qu'on
règle, pas la capacité.

L'étude vit dans `reports/optuna/realmlp_<P>.db` : un segfaut ne perd que l'essai en
cours, la machine ayant dix-sept paniques noyau au compteur.

Usage : python3 scripts/optuna_realmlp.py --polluant NO2 --essais 60
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

from aq.models.realmlp_regression import RealMLPRegressor  # noqa: E402
from optuna_mos import GRAINE, jeu_journalier, rmse  # noqa: E402

DOSSIER = RACINE / "reports/optuna"

# ⚠️ **Borné explicitement.** La contention mesurée sur ce dépôt portait sur des
# ajustements en `n_jobs=-1` : trois lots demandaient 96 fils sur 32 cœurs et deux
# ont été tués à 90 min. À 4 fils déclarés, six lots concurrents tiennent dans la
# machine — la ressource à partager est le **cœur**, pas le processus.
N_FILS = 4


def decouper(d: pd.DataFrame):
    """Trois blocs TEMPORELS emboîtés — et le test n'est jamais consulté ici.

    `fit` < `arret` < coupure < `test`. L'objectif Optuna est mesuré sur `arret`, qui est
    **antérieur** à la coupure : régler sur `test` serait choisir et noter sur les mêmes
    lignes, c'est-à-dire le biais de criblage que ce dépôt mesure à ×2 à ×4.
    """
    jours = np.sort(d["jour"].unique())
    coupe = jours[len(jours) // 2]
    entr = d["jour"] < coupe
    j_entr = np.sort(d.loc[entr, "jour"].unique())
    c_arret = j_entr[int(len(j_entr) * 0.8)]
    return ((entr & (d["jour"] < c_arret)).to_numpy(),
            (entr & (d["jour"] >= c_arret)).to_numpy(),
            (~entr).to_numpy())


def main(polluant: str, n_essais: int, modele: str = "realmlp") -> int:
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    DOSSIER.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    j, predicteurs = jeu_journalier(polluant)
    j["jour"] = pd.to_datetime(j["jour"]).dt.tz_localize(None)
    fit, arret, test = decouper(j)
    X = j[predicteurs].to_numpy(dtype=np.float32)
    y = (j["obs_jour"] - j["cams_jour"]).to_numpy(dtype=np.float32)
    print(f"{polluant} · {len(predicteurs)} prédicteurs · ajustement {fit.sum():,} · "
          f"objectif {arret.sum():,} · test {test.sum():,} (jamais consulté ici)",
          flush=True)

    def espace_lgbm(essai) -> dict:
        """Le MÊME budget d'essais que RealMLP, sur le MÊME objectif temporel.

        ⚠️ Sans cela la comparaison est faussée en faveur du réseau : le 16/08, RealMLP
        réglé sur 60 essais battait LightGBM **non réglé** de 9 % sur PM10, et ce chiffre
        n'était pas citable — « RealMLP réglé bat LightGBM par défaut » n'est pas
        « RealMLP bat LightGBM ». Deux systèmes se comparent à armes égales (§ 4 ter).
        """
        return {
            "num_leaves": essai.suggest_int("num_leaves", 16, 512, log=True),
            "learning_rate": essai.suggest_float("learning_rate", 5e-3, 0.2, log=True),
            "n_estimators": essai.suggest_int("n_estimators", 200, 3000, log=True),
            "min_child_samples": essai.suggest_int("min_child_samples", 5, 300, log=True),
            "reg_lambda": essai.suggest_float("reg_lambda", 1e-3, 30.0, log=True),
            "reg_alpha": essai.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "subsample": essai.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": essai.suggest_float("colsample_bytree", 0.5, 1.0),
        }

    def objectif_lgbm(essai) -> float:
        from lightgbm import LGBMRegressor  # noqa: PLC0415
        m = LGBMRegressor(random_state=GRAINE, verbose=-1, n_jobs=N_FILS,
                          **espace_lgbm(essai))
        m.fit(X[fit], y[fit])
        return float(rmse(y[arret], m.predict(X[arret])))

    def objectif(essai) -> float:
        if modele == "lgbm":
            return objectif_lgbm(essai)
        cfg = {
            # Le pas d'apprentissage est le paramètre qui a fait échouer les défauts :
            # on lui donne la plage la plus large, en log.
            "lr": essai.suggest_float("lr", 3e-4, 3e-2, log=True),
            "train_bs": essai.suggest_categorical("train_bs", [256, 512, 1024, 2048]),
            "epochs": essai.suggest_int("epochs", 8, 40),
            "dropout": essai.suggest_float("dropout", 0.0, 0.25),
            "hidden_dims": essai.suggest_categorical(
                "hidden_dims", [[256] * 3, [512] * 3, [512] * 4, [1024] * 2]),
            "n_ens": essai.suggest_categorical("n_ens", [4, 8, 16]),
            "pbld_freq_scale": essai.suggest_float("pbld_freq_scale", 1.0, 20.0, log=True),
        }
        m = RealMLPRegressor(cfg=cfg, graine=GRAINE, patience=4)
        m.fit(X[fit], y[fit], X[arret], y[arret])
        return float(m.rmse_val_)

    etude = optuna.create_study(
        study_name=f"{modele}_{polluant}_temporel", direction="minimize",
        storage=f"sqlite:///{DOSSIER / f'{modele}_{polluant}_temporel.db'}",
        load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=GRAINE, multivariate=True))
    faits = len([t for t in etude.trials
                 if t.state == optuna.trial.TrialState.COMPLETE])
    print(f"  {faits} essai(s) déjà dans l'étude · cible {n_essais}", flush=True)
    if faits < n_essais:
        etude.optimize(objectif, n_trials=n_essais - faits, show_progress_bar=False,
                       callbacks=[lambda e, t: print(
                           f"  essai {t.number} · {t.state.name} · "
                           f"{t.value if t.value else float('nan'):.4f} · "
                           f"meilleur {e.best_value:.4f} · "
                           f"{(time.time()-t0)/60:.0f} min", flush=True)])

    # ── La mesure finale, sur le test JAMAIS consulté ────────────────────────────────
    obs, cams = j.loc[test, "obs_jour"].to_numpy(), j.loc[test, "cams_jour"].to_numpy()
    from lightgbm import LGBMRegressor  # noqa: PLC0415
    from optuna_mos import params_reference  # noqa: PLC0415
    g = LGBMRegressor(n_estimators=400, random_state=GRAINE, verbose=-1, n_jobs=4,
                      **params_reference("lgbm")).fit(X[fit], y[fit])
    p_lgb = np.clip(cams + g.predict(X[test]), 0, None)

    if modele == "lgbm":
        mm = LGBMRegressor(random_state=GRAINE, verbose=-1, n_jobs=N_FILS,
                           **etude.best_params).fit(X[fit], y[fit])
        p_mlp = np.clip(cams + mm.predict(X[test]), 0, None)
    else:
        m = RealMLPRegressor(cfg=dict(etude.best_params), graine=GRAINE, patience=4)
        m.fit(X[fit], y[fit], X[arret], y[arret])
        p_mlp = np.clip(cams + m.predict(X[test]), 0, None)

    r_cams, r_lgb, r_mlp = rmse(obs, cams), rmse(obs, p_lgb), rmse(obs, p_mlp)
    rho = float(np.corrcoef(p_lgb - obs, p_mlp - obs)[0, 1])
    r_moy = rmse(obs, (p_lgb + p_mlp) / 2)
    print(f"\n  CAMS brut {r_cams:7.4f} · lgbm {r_lgb:7.4f} · realmlp réglé {r_mlp:7.4f}\n"
          f"  corrélation des erreurs {rho:+.3f} · moyenne 50/50 {r_moy:7.4f}\n"
          f"  → le mélange rend {100*(1-r_moy/min(r_lgb, r_mlp)):+.2f} % contre le "
          f"meilleur seul", flush=True)

    # ⚠️ **Étiquettes par RÔLE, jamais par identité.** La version précédente écrivait
    # `rmse_realmlp` quel que soit `--modele` : en mode lgbm, cette colonne contenait le
    # LightGBM réglé. J'en ai tiré « RealMLP bat LightGBM de 9 % sur PM10 », envoyé à un
    # relecteur externe, qui a relu le fichier correctement pour trouver **2,65 %**.
    # `rmse_candidat` + la colonne `modele` ne peuvent pas mentir : le jour où le candidat
    # change, l'identité change avec lui, parce qu'elle EST la donnée.
    from aq.rapport import ecrire_rapport  # noqa: PLC0415

    t = pd.DataFrame([{"essais": len(etude.trials),
                       "rmse_cams": r_cams, "rmse_reference": r_lgb,
                       "rmse_candidat": r_mlp, "rmse_moyenne": r_moy,
                       "correlation_erreurs": rho,
                       **{f"p_{k}": v for k, v in etude.best_params.items()}}])
    ecrire_rapport(t, RACINE / f"reports/optuna_{modele}_{polluant}_temporel.csv",
                   contexte={"polluant": polluant, "axe": "temporel",
                             "modele_candidat": modele, "modele_reference": "lgbm_defaut"},
                   attendues=["rmse_cams", "rmse_reference", "rmse_candidat"])
    print(f"Écrit : reports/optuna_{modele}_{polluant}_temporel.csv · "
          f"{(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2", choices=("O3", "NO2", "PM10", "PM25"))
    a.add_argument("--essais", type=int, default=60)
    a.add_argument("--modele", default="realmlp", choices=("realmlp", "lgbm"))
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.essais, n.modele))
