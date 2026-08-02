#!/usr/bin/env python3
"""La dispersion entre modèles vaut-elle quelque chose ?

Trois questions ouvertes, une seule mesure
-------------------------------------------
Le projet n'utilisait que la **médiane** de l'ensemble CAMS. Le désaccord entre les modèles —
mesuré ici à **11 µg/m³ d'écart-type médian** entre six d'entre eux — était jeté. Il devrait
répondre à trois questions que le projet a laissées ouvertes :

1. **Prédicteur** : la dispersion améliore-t-elle la correction ? Là où les modèles divergent,
   l'erreur est probablement plus grande, et le correcteur pourrait en tenir compte.
2. **Signal *ex ante* de dérive** : le projet a montré que stratifier le gain par l'erreur
   **réalisée** de CAMS est mathématiquement couplé (`ΔMSE = 2em − m²`). La dispersion est
   disponible **avant** l'observation : elle permet une stratification honnête.
3. **Coupure** : ni le détecteur d'anomalies sur les entrées, ni le moniteur de résidu n'ont
   fourni de signal exploitable pour suspendre la correction. La dispersion est le dernier
   candidat.

Ce que le script mesure, dans cet ordre
----------------------------------------
- l'apport de la dispersion **comme prédicteur**, au protocole habituel ;
- la **relation dispersion / erreur** : la dispersion prédit-elle l'erreur, et de combien ?
- le gain de la correction **stratifié par dispersion**, qui est la version non couplée de la
  question « le modèle rattrape-t-il surtout quand le forçage est mauvais ? ».

**Six membres sur onze** : le plafond ADS l'impose, la dispersion est donc sous-estimée. Et il
manque **novembre 2023** (HTTP 400), donc un mois d'automne.

Usage : python3 scripts/apport_dispersion.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from apport_meteo import evaluer, ic_difference, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

RESUMES = ["membres_ecart", "membres_etendue", "membres_asymetrie",
           "membres_min", "membres_max", "membres_median"]
MEMBRES = ["chimere", "emep", "mocage", "silam", "lotos", "match"]
# Le critère de rétention vit dans `aq.eval.critere` : **relatif au RMSE de base**,
# donc comparable entre polluants. L'ancien 0,3 µg/m³ absolu valait 2 % sur le NO₂
# et 11 % sur les PM2,5 — il écartait ces dernières par artefact d'unité.


def charger_dispersion(court: str) -> pd.DataFrame:
    fichiers = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/membres_metropole_{court}_*.parquet")))
    if not fichiers:
        raise SystemExit("aucun mois de membres extrait")
    d = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    print(f"  {len(fichiers)} mois de membres · {len(d):,} lignes horaires", flush=True)
    return d


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    court = {"O3": "o3", "NO2": "no2", "PM25": "pm25"}[polluant]
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    disp = charger_dispersion(court)
    avant = len(jeu)
    jeu = jeu.merge(disp, on=["station_id", "timestamp_utc"], how="inner")
    print(f"{polluant} · {avant:,} → {len(jeu):,} lignes après jointure "
          f"({100 * len(jeu) / avant:.0f} %)", flush=True)

    presents = [c for c in RESUMES + MEMBRES if c in jeu.columns]
    j = agreger_journalier(jeu, colonnes + presents, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    resumes = [c for c in RESUMES if c in j.columns]
    membres = [c for c in MEMBRES if c in j.columns]

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    print(f"  {len(j):,} jours-station · dispersion médiane "
          f"{j['membres_ecart'].median():.2f} µg/m³\n", flush=True)

    # ── 1. La dispersion comme prédicteur ─────────────────────────────────────
    jeux = {"base": base,
            "+ résumés de dispersion": base + resumes,
            "+ les 6 membres bruts": base + membres}
    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:26s} {len(predicteurs):3d} var · RMSE {resultats[nom]['rmse']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    print(f"\n{'jeu':26s} {'RMSE':>7s} {'décile haut':>12s} {'POD':>7s} {'CSI':>7s}")
    for nom, r in resultats.items():
        print(f"{nom:26s} {r['rmse']:7.3f} {r['rmse_decile_haut']:12.3f} "
              f"{r.get('POD', np.nan):7.3f} {r.get('CSI', np.nan):7.3f}", flush=True)

    print(f"\n{'─' * 74}")
    for nom in ("+ résumés de dispersion", "+ les 6 membres bruts"):
        gain = resultats["base"]["rmse"] - resultats[nom]["rmse"]
        bas, haut = ic_difference(predictions["base"], predictions[nom])
        print(f"{nom:26s} gain {gain:+.3f} µg/m³ ({100 * gain / resultats['base']['rmse']:+.1f} %)"
              f"  IC95 [{bas:+.3f} ; {haut:+.3f}]  "
              f"{'✅ établi' if bas > 0 else '— IC contenant zéro'}")

    # ── 2. La dispersion prédit-elle l'erreur ? ───────────────────────────────
    p = predictions["base"]
    p = p.assign(dispersion=j["membres_ecart"].to_numpy(),
                 err_cams=np.abs(j["obs_jour"] - j["cams_jour"]).to_numpy(),
                 err_mos=np.abs(j["obs_jour"] - p["pred"]).to_numpy())
    r_cams = float(p[["dispersion", "err_cams"]].corr().iloc[0, 1])
    r_mos = float(p[["dispersion", "err_mos"]].corr().iloc[0, 1])
    print(f"\nRELATION dispersion / erreur absolue")
    print(f"  contre l'erreur de CAMS  : r = {r_cams:+.3f}")
    print(f"  contre l'erreur corrigée : r = {r_mos:+.3f}")
    print(f"  → {'la dispersion informe sur l’erreur' if r_cams >= 0.2 else 'relation faible — la dispersion ne prédit guère l’erreur'}",
          flush=True)

    # ── 3. Stratification **ex ante**, non couplée ────────────────────────────
    # C'est l'objet principal : stratifier par l'erreur *réalisée* est arithmétiquement
    # couplé au gain. La dispersion, elle, est connue avant l'observation.
    p["decile"] = pd.qcut(p["dispersion"], 10, labels=False, duplicates="drop")
    strat = (p.assign(gain=p["err_cams"] ** 2 - p["err_mos"] ** 2)
              .groupby("decile")
              .agg(n=("gain", "size"), dispersion=("dispersion", "mean"),
                   gain_mse=("gain", "mean"), err_cams=("err_cams", "mean")).reset_index())
    print(f"\nGAIN PAR DÉCILE DE DISPERSION (stratification *ex ante*, non couplée)")
    print(f"{'décile':>7s} {'dispersion':>11s} {'err CAMS':>9s} {'gain MSE':>10s}")
    for _, r in strat.iterrows():
        print(f"{int(r['decile']):7d} {r['dispersion']:11.2f} {r['err_cams']:9.2f} "
              f"{r['gain_mse']:10.1f}", flush=True)
    bas_, haut_ = strat["gain_mse"].iloc[0], strat["gain_mse"].iloc[-1]
    print(f"\n  du décile le plus concordant au plus divergent : {bas_:.1f} → {haut_:.1f}")
    print(f"  → {'le gain croît avec le désaccord entre modèles — signal ex ante confirmé' if haut_ > bas_ * 1.5 else 'pas de tendance nette'}")

    pd.DataFrame(resultats).T.to_csv(RACINE / f"reports/apport_dispersion_{polluant}.csv")
    strat.to_csv(RACINE / f"reports/dispersion_strates_{polluant}.csv", index=False)
    print(f"\nÉcrit : reports/apport_dispersion_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
