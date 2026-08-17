#!/usr/bin/env python3
"""Le poids optimal du mélange LightGBM / RealMLP — balayé, et honnêtement daté.

Pourquoi un balayage plutôt qu'un ridge
----------------------------------------
Le ridge de `stacking_ridge.py` a rendu, sur NO₂, un poids **négatif** pour RealMLP et une
RMSE **pire que ses deux entrées**. Un combineur à deux entrées n'a qu'un degré de liberté
utile : autant le regarder en face. Un balayage montre la **forme** de la courbe — plate,
piquée, ou monotone —, ce qu'un coefficient unique ne dit pas.

🔴 **Deux chiffres, et ne jamais citer le premier seul**
--------------------------------------------------------
* `w*` **choisi sur le test** — c'est un **majorant**, pas un score. Choisir et noter sur
  les mêmes lignes est le biais de criblage que ce dépôt mesure à ×2 à ×4.
* `w` **choisi sur le bloc de validation**, appliqué au test — la seule valeur citable.

L'écart entre les deux **est** la mesure du biais de criblage sur ce combineur.

Usage : python3 scripts/poids_melange.py [--polluant NO2]
Sortie : reports/poids_melange_<polluant>.csv
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


def main(polluant: str) -> int:
    from stacking_ridge import meilleurs_params

    t0 = time.time()
    p_lgb = meilleurs_params("lgbm", polluant) or params_reference("lgbm")
    p_mlp = meilleurs_params("realmlp", polluant) or {}

    j, predicteurs = jeu_journalier(polluant)
    j["jour"] = pd.to_datetime(j["jour"]).dt.tz_localize(None)
    jours = np.sort(j["jour"].unique())
    coupe = jours[len(jours) // 2]
    entr = (j["jour"] < coupe).to_numpy()
    test = ~entr
    j_e = np.sort(j.loc[entr, "jour"].unique())
    c_val = j_e[int(len(j_e) * 0.8)]
    fit = entr & (j["jour"] < c_val).to_numpy()
    val = entr & (j["jour"] >= c_val).to_numpy()

    X = j[predicteurs].to_numpy(dtype=np.float32)
    y = (j["obs_jour"] - j["cams_jour"]).to_numpy(dtype=np.float32)

    from lightgbm import LGBMRegressor

    g = LGBMRegressor(random_state=GRAINE, verbose=-1, n_jobs=4, **p_lgb).fit(X[fit], y[fit])
    m = RealMLPRegressor(cfg=p_mlp, graine=GRAINE, patience=4)
    m.fit(X[fit], y[fit], X[val], y[val])

    grille = np.linspace(0.0, 1.0, 41)

    def courbe(masque):
        obs = j.loc[masque, "obs_jour"].to_numpy()
        cams = j.loc[masque, "cams_jour"].to_numpy()
        pl, pm = g.predict(X[masque]), m.predict(X[masque])
        return obs, cams, np.array(
            [rmse(obs, np.clip(cams + w * pl + (1 - w) * pm, 0, None)) for w in grille])

    _, _, r_val = courbe(val)
    obs_t, cams_t, r_te = courbe(test)

    w_val = float(grille[int(np.argmin(r_val))])      # choisi HORS test — citable
    w_te = float(grille[int(np.argmin(r_te))])        # choisi SUR test — majorant
    r_cams = rmse(obs_t, cams_t)
    i_val = int(np.argmin(r_val))

    print(f"\n{polluant} · lgbm {'réglé' if meilleurs_params('lgbm', polluant) else 'défaut'}"
          f" · realmlp {'réglé' if p_mlp else 'défaut'}")
    print(f"  {'w':>5s} {'RMSE test':>10s}   (w=1 : lgbm seul · w=0 : realmlp seul)")
    for k in (0, 10, 20, 30, 40):
        marque = "  ← w retenu" if k == i_val else ""
        print(f"  {grille[k]:5.2f} {r_te[k]:10.4f}{marque}")
    print(f"\n  w choisi sur VALIDATION : {w_val:.2f} → RMSE test {r_te[i_val]:.4f} "
          f"(gain vs CAMS {100*(1-r_te[i_val]/r_cams):+.2f} %)   ← citable")
    print(f"  w choisi sur TEST        : {w_te:.2f} → RMSE test {r_te.min():.4f}   "
          f"← MAJORANT, jamais un score")
    print(f"  biais de criblage du combineur : {100*(1-r_te.min()/r_te[i_val]):+.2f} %")
    seuls = min(r_te[-1], r_te[0])
    print(f"  apport contre le meilleur seul : {100*(1-r_te[i_val]/seuls):+.2f} % "
          f"(moyenne 50/50 : {100*(1-r_te[20]/seuls):+.2f} %)")

    t = pd.DataFrame({"w": grille, "rmse_test": r_te, "rmse_validation": r_val})
    t["polluant"], t["w_validation"], t["w_test"] = polluant, w_val, w_te
    t.to_csv(RACINE / f"reports/poids_melange_{polluant}.csv", index=False)
    print(f"  Écrit · {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2", choices=("O3", "NO2", "PM10", "PM25"))
    n = a.parse_args()
    raise SystemExit(main(n.polluant))
