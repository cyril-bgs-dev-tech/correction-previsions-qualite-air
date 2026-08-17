#!/usr/bin/env python3
"""Ridge de stacking sur LightGBM + RealMLP — pondéré hors-pli, jamais moyenné.

Pourquoi pas une moyenne 50/50
-------------------------------
Mesuré le 16/08 sur l'axe temporel : la moyenne aide sur NO₂ (+1,03 %) et PM2,5 (+1,09 %)
mais **nuit** sur O₃ (−0,39 %) et PM10 (−2,35 %) — parce qu'elle tire le meilleur modèle
vers le moins bon. Sur PM10, RealMLP est 9 % devant LightGBM : lui donner le même poids
qu'à son concurrent jette la moitié de l'écart. Un ridge apprend les poids ; une moyenne
les postule.

🔴 Le piège que ce script existe pour éviter
---------------------------------------------
La tentation est d'ajuster le ridge sur le bloc `arret` — il est hors de l'ajustement des
deux modèles, donc « propre ». **Il ne l'est pas** : RealMLP y règle son arrêt anticipé,
donc ses prédictions y sont optimistes, et LightGBM non. Le ridge apprendrait cet écart de
protocole et surpondérerait le réseau. C'est le biais de criblage, déplacé dans le
combineur.

On construit donc de vraies prédictions **hors-pli** par découpage TEMPOREL du bloc
d'ajustement : pour chaque pli, les deux modèles apprennent sur les plis antérieurs et
prédisent sur celui-ci — jamais l'inverse, car un combineur entraîné sur des prédictions
issues du futur n'a aucun sens opérationnel. Les poids sont ensuite figés et appliqués au
test, jamais consulté.

Usage : python3 scripts/stacking_ridge.py --polluant PM10 [--plis 4]
Sortie : reports/stacking_ridge_<polluant>.csv
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
from optuna_mos import GRAINE, jeu_journalier, params_reference, rmse  # noqa: E402

DOSSIER = RACINE / "reports/optuna"
N_FILS = 4


def meilleurs_params(modele: str, polluant: str) -> dict | None:
    """Le meilleur essai de l'étude TEMPORELLE, ou None si elle n'existe pas encore."""
    import optuna

    # ⚠️ **Deux conventions de nom coexistent, et l'ignorer coûte le réglage entier.**
    # Les études RealMLP du 16/08 ont été écrites en `realmlp_<P>.db` ; le suffixe
    # `_temporel` est venu après, quand le script a été généralisé à LightGBM. Chercher la
    # seule forme récente faisait retomber sur les hyperparamètres PAR DÉFAUT **en
    # silence** — le ridge aurait pondéré un RealMLP non réglé contre un LightGBM réglé,
    # et sous-estimé le réseau sans qu'aucune erreur ne soit levée. On essaie donc les
    # deux, et on DIT laquelle a servi.
    for nom in (f"{modele}_{polluant}_temporel", f"{modele}_{polluant}"):
        base = DOSSIER / f"{nom}.db"
        if not base.exists():
            continue
        try:
            e = optuna.load_study(study_name=nom, storage=f"sqlite:///{base}")
            if e.best_trials:
                print(f"    {modele} : étude « {nom} » · {len(e.trials)} essais",
                      flush=True)
                return dict(e.best_params)
        except Exception:  # noqa: BLE001
            continue
    return None


def ajuster_paire(Xa, ya, Xb, p_lgb: dict, p_mlp: dict) -> tuple[np.ndarray, np.ndarray]:
    """Ajuste les deux modèles sur (Xa, ya) et prédit le RÉSIDU sur Xb."""
    from lightgbm import LGBMRegressor  # noqa: PLC0415

    g = LGBMRegressor(random_state=GRAINE, verbose=-1, n_jobs=N_FILS, **p_lgb)
    g.fit(Xa, ya)
    # Arrêt anticipé du réseau sur le dernier cinquième de SON bloc d'ajustement : jamais
    # sur le bloc qu'il s'apprête à prédire, sinon le hors-pli n'en est plus un.
    n = len(ya)
    coupe = int(n * 0.8)
    m = RealMLPRegressor(cfg=p_mlp, graine=GRAINE, patience=4)
    m.fit(Xa[:coupe], ya[:coupe], Xa[coupe:], ya[coupe:])
    return g.predict(Xb), m.predict(Xb)


def main(polluant: str, n_plis: int) -> int:
    t0 = time.time()
    p_lgb = meilleurs_params("lgbm", polluant) or params_reference("lgbm")
    p_mlp = meilleurs_params("realmlp", polluant) or {}
    print(f"{polluant} · lgbm {'réglé' if meilleurs_params('lgbm', polluant) else 'DÉFAUT'}"
          f" · realmlp {'réglé' if p_mlp else 'DÉFAUT'}", flush=True)

    j, predicteurs = jeu_journalier(polluant)
    j["jour"] = pd.to_datetime(j["jour"]).dt.tz_localize(None)
    j = j.sort_values("jour").reset_index(drop=True)
    jours = np.sort(j["jour"].unique())
    coupe = jours[len(jours) // 2]
    entr = (j["jour"] < coupe).to_numpy()
    test = ~entr

    X = j[predicteurs].to_numpy(dtype=np.float32)
    y = (j["obs_jour"] - j["cams_jour"]).to_numpy(dtype=np.float32)
    obs, cams = j.loc[test, "obs_jour"].to_numpy(), j.loc[test, "cams_jour"].to_numpy()

    # ── ① Hors-pli TEMPOREL glissant sur le bloc d'ajustement ───────────────────────────
    idx = np.flatnonzero(entr)
    bornes = np.array_split(idx, n_plis + 1)
    oof_l, oof_m, oof_y = [], [], []
    for k in range(1, n_plis + 1):
        passe = np.concatenate(bornes[:k])          # tout ce qui précède
        courant = bornes[k]                         # le pli à prédire
        pl, pm = ajuster_paire(X[passe], y[passe], X[courant], p_lgb, p_mlp)
        oof_l.append(pl); oof_m.append(pm); oof_y.append(y[courant])
        print(f"  pli {k}/{n_plis} · apprentissage {len(passe):,} → hors-pli "
              f"{len(courant):,} · {(time.time()-t0)/60:.1f} min", flush=True)

    A = np.column_stack([np.concatenate(oof_l), np.concatenate(oof_m)])
    b = np.concatenate(oof_y)

    from sklearn.linear_model import RidgeCV  # noqa: PLC0415

    ridge = RidgeCV(alphas=np.logspace(-3, 3, 25)).fit(A, b)
    w = ridge.coef_
    print(f"\n  poids appris hors-pli : lgbm {w[0]:+.3f} · realmlp {w[1]:+.3f} · "
          f"biais {ridge.intercept_:+.4f} · α {ridge.alpha_:.3g}", flush=True)

    # ── ② Les deux modèles réajustés sur TOUT le bloc, puis le ridge figé appliqué ──────
    pl_te, pm_te = ajuster_paire(X[entr], y[entr], X[test], p_lgb, p_mlp)
    pred = {
        "CAMS brut": cams,
        "lgbm": np.clip(cams + pl_te, 0, None),
        "realmlp": np.clip(cams + pm_te, 0, None),
        "moyenne 50/50": np.clip(cams + (pl_te + pm_te) / 2, 0, None),
        "ridge hors-pli": np.clip(
            cams + ridge.predict(np.column_stack([pl_te, pm_te])), 0, None),
    }
    lignes = []
    r_cams = rmse(obs, cams)
    for nom, p in pred.items():
        r = rmse(obs, p)
        lignes.append({"systeme": nom, "rmse": r, "gain_cams_pct": 100 * (1 - r / r_cams)})
        print(f"  {nom:16s} RMSE {r:7.4f} · gain vs CAMS {100*(1-r/r_cams):+6.2f} %",
              flush=True)

    seuls = min(rmse(obs, pred["lgbm"]), rmse(obs, pred["realmlp"]))
    apport = 100 * (1 - rmse(obs, pred["ridge hors-pli"]) / seuls)
    print(f"  → le ridge rend {apport:+.2f} % contre le meilleur des deux seuls "
          f"(la moyenne : {100*(1-rmse(obs, pred['moyenne 50/50'])/seuls):+.2f} %)",
          flush=True)

    t = pd.DataFrame(lignes)
    t["polluant"], t["axe"] = polluant, "temporel"
    t["poids_lgbm"], t["poids_realmlp"] = w[0], w[1]
    t["apport_ridge_pct"] = apport
    t.to_csv(RACINE / f"reports/stacking_ridge_{polluant}.csv", index=False)
    print(f"Écrit : reports/stacking_ridge_{polluant}.csv · {(time.time()-t0)/60:.1f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10", choices=("O3", "NO2", "PM10", "PM25"))
    a.add_argument("--plis", type=int, default=4)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.plis))
