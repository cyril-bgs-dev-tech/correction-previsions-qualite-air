#!/usr/bin/env python3
"""L'exposition aux feux améliore-t-elle la correction — et où ?

Le contrôle qui décide
----------------------
Les feux et les fortes concentrations culminent tous deux en été. Une variable d'exposition
aux feux pourrait donc « marcher » sans rien dire du transport : il lui suffirait de corréler
avec la saison, que le calendrier porte déjà.

Deux garde-fous, et le second est le vrai :

1. l'exposition **isotrope** (tous azimuts) entre en même temps que l'**anisotrope** (secteur
   au vent). Si seule l'isotrope compte, c'est le calendrier qui parle ;
2. le gain est ventilé par **régime d'erreur** de CAMS. Le mécanisme prédit un effet sur les
   **sous-estimations** — un panache que le modèle amont n'a pas vu ajoute de la matière, il
   n'en retire pas. Un gain réparti uniformément, ou concentré sur les sur-estimations,
   réfuterait le mécanisme même s'il améliorait le RMSE.

**Ce qu'on ne peut pas conclure.** GFAS alimente déjà CAMS en conditions aux limites. Un gain
ici ne dirait donc pas « les feux étaient ignorés » mais « l'information arrive trop tard ou au
mauvais endroit » — latence d'assimilation, résolution, hauteur d'injection.

Usage : python3 scripts/apport_feux.py [--polluant PM25]
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

# Le critère de rétention vit dans `aq.eval.critere` : **relatif au RMSE de base**,
# donc comparable entre polluants. L'ancien 0,3 µg/m³ absolu valait 2 % sur le NO₂
# et 11 % sur les PM2,5 — il écartait ces dernières par artefact d'unité.


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    fichiers = sorted(glob.glob(str(RACINE / "data/processed/meteo/feux_metropole_*.parquet")))
    if not fichiers:
        raise SystemExit("aucun mois d'exposition aux feux")
    feux = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    feux["jour"] = pd.to_datetime(feux["jour"])
    j["jour"] = pd.to_datetime(j["jour"])
    avant = len(j)
    j = j.merge(feux, on=["station_id", "jour"], how="inner")
    iso = [c for c in j.columns if c.startswith("feu_iso_")]
    vent = [c for c in j.columns if c.startswith("feu_vent_")]
    print(f"{polluant} · {avant:,} → {len(j):,} jours-station · "
          f"{len(iso)} isotropes + {len(vent)} anisotropes · "
          f"exposition non nulle sur {100 * (j[vent[0]] > 0).mean():.0f} %\n", flush=True)

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})

    jeux = {"base": base, "+ feux isotropes": base + iso,
            "+ feux au vent": base + iso + vent}
    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:20s} {len(predicteurs):3d} var · RMSE {resultats[nom]['rmse']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    print(f"\n{'jeu':20s} {'RMSE':>7s} {'décile haut':>12s} {'POD':>7s} {'CSI':>7s}")
    for nom, r in resultats.items():
        print(f"{nom:20s} {r['rmse']:7.3f} {r['rmse_decile_haut']:12.3f} "
              f"{r.get('POD', np.nan):7.3f} {r.get('CSI', np.nan):7.3f}", flush=True)

    print(f"\n{'─' * 74}")
    for depuis, vers in (("base", "+ feux isotropes"),
                         ("+ feux isotropes", "+ feux au vent")):
        gain = resultats[depuis]["rmse"] - resultats[vers]["rmse"]
        bas, haut = ic_difference(predictions[depuis], predictions[vers])
        print(f"{vers:20s} contre {depuis:20s} : {gain:+.3f} µg/m³ "
              f"IC95 [{bas:+.3f} ; {haut:+.3f}] "
              f"{'✅' if bas > 0 else '—'}")

    # ── Le contrôle de mécanisme ──────────────────────────────────────────────
    ref, avec = predictions["base"], predictions["+ feux au vent"]
    d = ref[["obs_jour", "cams_jour"]].copy()
    d["err_base"] = ref["pred"] - ref["obs_jour"]
    d["err_feux"] = avec["pred"] - avec["obs_jour"]
    d["gain"] = d["err_base"] ** 2 - d["err_feux"] ** 2
    d["regime"] = np.where(d["cams_jour"] < d["obs_jour"], "CAMS sous-estime",
                           "CAMS sur-estime")
    print(f"\nOÙ LE GAIN TOMBE — le mécanisme prédit les sous-estimations")
    for regime, g in d.groupby("regime"):
        print(f"  {regime:20s} n={len(g):7,}  gain MSE moyen {g['gain'].mean():+8.2f}")
    part = d.groupby("regime")["gain"].mean()
    if "CAMS sous-estime" in part and "CAMS sur-estime" in part:
        verdict = ("conforme au mécanisme" if part["CAMS sous-estime"] > part["CAMS sur-estime"]
                   else "**contraire au mécanisme** — le gain ne vient pas des panaches manqués")
        print(f"  → {verdict}")

    pd.DataFrame(resultats).T.to_csv(RACINE / f"reports/apport_feux_{polluant}.csv")
    print(f"\nÉcrit : reports/apport_feux_{polluant}.csv · {time.time() - depart:.0f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="PM25")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
