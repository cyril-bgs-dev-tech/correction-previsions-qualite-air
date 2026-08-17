#!/usr/bin/env python3
"""RealMLP contre LightGBM sur le MOS — et ce que leur mélange ajoute.

Ce que ce script cherche, et ce qu'il ne cherche PAS
-----------------------------------------------------
Il ne cherche **pas** un meilleur modèle : ce dépôt a mesuré deux fois qu'ajouter de la
capacité à LightGBM gagne +4 à +7 % sur l'axe SPATIAL et **~0 sur l'axe TEMPOREL**
(§ 10 septies de `VERITE_DOSSIER`, et la table à quatre configurations de
`double_aveugle_journalier`). Un troisième réglage du même arbre ne donnerait rien de
plus.

Il cherche de la **diversité d'erreur**. Un MLP n'est pas plus de capacité, c'est un biais
inductif différent — et la diversité, elle, a déjà payé ici : moyenner sept pertes rend
+1,8 % de plancher, 4/4. La quantité qui décide n'est donc pas la RMSE de RealMLP seul,
c'est la **corrélation entre ses erreurs et celles de LightGBM** : à corrélation 1, il
n'apporte rien quel que soit son score ; à corrélation basse, il apporte même en étant
moins bon.

⚠️ **L'axe est TEMPOREL, et ce n'est pas négociable.** Ajuster sur la 1ʳᵉ moitié du
calendrier, noter sur la 2ᵈᵉ. Mesurer sur l'axe spatial reproduirait exactement le mirage
que ce dépôt vient de documenter, et le chantier entier serait à refaire.

Usage : python3 scripts/realmlp_mos.py --polluant NO2 [--epoques 30]
Sortie : reports/realmlp_mos_<polluant>.csv
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
from optuna_mos import (  # noqa: E402
    GRAINE, jeu_journalier, params_reference, rmse,
)


def partage_temporel(d: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """1ʳᵉ moitié du calendrier pour ajuster, dernier cinquième d'icelle pour l'arrêt.

    Le groupe d'arrêt est **temporel lui aussi** et pris AVANT la coupure : le régler sur
    des jours postérieurs ferait fuir le futur dans le choix du nombre d'époques, ce qui
    est la version « réseau » de la fuite que ce dépôt traque partout ailleurs.
    """
    jours = np.sort(d["jour"].unique())
    coupe = jours[len(jours) // 2]
    entr = d["jour"] < coupe
    j_entr = np.sort(d.loc[entr, "jour"].unique())
    coupe_arret = j_entr[int(len(j_entr) * 0.8)]
    return (entr & (d["jour"] < coupe_arret)).to_numpy(), \
           (entr & (d["jour"] >= coupe_arret)).to_numpy(), \
           (~entr).to_numpy()


def main(polluant: str, epoques: int) -> int:
    t0 = time.time()
    j, predicteurs = jeu_journalier(polluant)
    j["jour"] = pd.to_datetime(j["jour"]).dt.tz_localize(None)
    fit, arret, test = partage_temporel(j)
    print(f"{polluant} · {len(j):,} jours-station · {len(predicteurs)} prédicteurs\n"
          f"  ajustement {fit.sum():,} · arrêt {arret.sum():,} · test {test.sum():,} "
          f"(2ᵈᵉ moitié du calendrier)", flush=True)

    # La cible est le RÉSIDU, comme pour le MOS : obs − CAMS. Prédire la concentration
    # directement ferait réapprendre au réseau ce que CAMS sait déjà.
    X = j[predicteurs].to_numpy(dtype=np.float32)
    y = (j["obs_jour"] - j["cams_jour"]).to_numpy(dtype=np.float32)
    obs_te, cams_te = j.loc[test, "obs_jour"].to_numpy(), j.loc[test, "cams_jour"].to_numpy()

    lignes, preds = [], {}

    r_cams = rmse(obs_te, cams_te)
    lignes.append({"systeme": "CAMS brut", "rmse": r_cams, "gain_cams_pct": 0.0})
    print(f"  CAMS brut              RMSE {r_cams:7.4f}", flush=True)

    from lightgbm import LGBMRegressor  # noqa: PLC0415
    p = params_reference("lgbm")
    g = LGBMRegressor(n_estimators=400, random_state=GRAINE, verbose=-1, n_jobs=4, **p)
    g.fit(X[fit], y[fit])
    preds["lgbm"] = np.clip(cams_te + g.predict(X[test]), 0, None)

    m = RealMLPRegressor(cfg={"epochs": epoques}, graine=GRAINE, bavard=True)
    m.fit(X[fit], y[fit], X[arret], y[arret])
    preds["realmlp"] = np.clip(cams_te + m.predict(X[test]), 0, None)

    for nom, pr in preds.items():
        r = rmse(obs_te, pr)
        lignes.append({"systeme": nom, "rmse": r, "gain_cams_pct": 100 * (1 - r / r_cams)})
        print(f"  {nom:22s} RMSE {r:7.4f} · gain vs CAMS {100*(1-r/r_cams):+6.2f} %",
              flush=True)

    # ── La quantité qui décide : les erreurs sont-elles décorrélées ? ────────────────────
    e1, e2 = preds["lgbm"] - obs_te, preds["realmlp"] - obs_te
    rho = float(np.corrcoef(e1, e2)[0, 1])
    moy = (preds["lgbm"] + preds["realmlp"]) / 2
    r_moy = rmse(obs_te, moy)
    lignes.append({"systeme": "moyenne 50/50", "rmse": r_moy,
                   "gain_cams_pct": 100 * (1 - r_moy / r_cams)})
    print(f"\n  corrélation des erreurs : {rho:+.3f}", flush=True)
    print(f"  moyenne 50/50          RMSE {r_moy:7.4f} · gain vs CAMS "
          f"{100*(1-r_moy/r_cams):+6.2f} %", flush=True)

    meilleur_seul = min(rmse(obs_te, preds["lgbm"]), rmse(obs_te, preds["realmlp"]))
    apport = 100 * (1 - r_moy / meilleur_seul)
    print(f"  → le mélange rend {apport:+.2f} % contre le meilleur des deux seuls",
          flush=True)
    lignes.append({"systeme": "apport du mélange", "rmse": np.nan,
                   "gain_cams_pct": apport, "correlation_erreurs": rho})

    t = pd.DataFrame(lignes)
    for c in ("systeme", "rmse", "gain_cams_pct"):
        if c not in t.columns:
            raise SystemExit(f"colonne absente du rapport : {c}")
    t["polluant"], t["axe"], t["epoques"] = polluant, "temporel", epoques
    t.to_csv(RACINE / f"reports/realmlp_mos_{polluant}.csv", index=False)
    print(f"\nÉcrit : reports/realmlp_mos_{polluant}.csv · {(time.time()-t0)/60:.1f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2", choices=("O3", "NO2", "PM10", "PM25"))
    a.add_argument("--epoques", type=int, default=30,
                   help="le défaut du notebook est 6, calibré sur un jeu Kaggle bien plus "
                        "petit ; la passe unitaire montrait la validation encore en baisse")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.epoques))
