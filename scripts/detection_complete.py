#!/usr/bin/env python3
"""La meilleure détection atteignable, tous leviers mesurés réunis.

Ce que le projet a établi séparément
-------------------------------------
| levier | apport en RMSE | testé en détection ? |
|---|---|---|
| observations à J−2 | +8,9 % (O₃) · +21,9 % (NO₂) · +8,5 % (PM2,5) | ✅ oui — 3,6× à budget égal |
| six membres d'ensemble bruts | nul sur O₃, **+1,9 %** (NO₂), **+2,9 %** (PM2,5) | ❌ **jamais** |
| exposition aux feux | +3,0 % sur PM2,5 seulement | ❌ jamais |

Le résultat qui porte le dossier est la **détection à budget de fausses alertes égal**, et deux
des trois leviers n'y ont jamais été éprouvés. Or améliorer le RMSE et améliorer le rang des
jours à risque sont deux choses différentes : le projet a mesuré qu'une technique peut gagner
l'un en perdant l'autre.

Ce que ce script mesure
-----------------------
Le rappel à budget de fausses alertes imposé, pour des jeux de variables emboîtés. Le point de
fonctionnement est choisi **hors échantillon** — sur d'autres stations que celles évaluées —
sans quoi le seuil devient un paramètre appris sur son propre test.

**L'ordre des blocs suit la valeur décroissante mesurée en RMSE**, et chaque bloc est comparé
au précédent : c'est la seule façon de distinguer un apport propre d'une redondance.

Usage : python3 scripts/detection_complete.py [--polluant PM25]
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

from aq.ingest import controle as ctl  # noqa: E402
from apport_observation_veille import variables_passees  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from detection_maximale import ajuster, rappel_hors_echantillon  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0}
BUDGETS = (0.10, 0.20, 0.30, 0.40)
MEMBRES = ["chimere", "emep", "mocage", "silam", "lotos", "match"]
COURT = {"O3": "o3", "NO2": "no2", "PM25": "pm25"}


def joindre(j: pd.DataFrame, motif: str, colonnes: list[str],
            cle: list[str], quoi: str) -> tuple[pd.DataFrame, list[str]]:
    """Jointure contrôlée : on vérifie ce qu'on a demandé, pas ce qui paraît normal."""
    fichiers = sorted(glob.glob(str(RACINE / f"data/processed/meteo/{motif}")))
    if not fichiers:
        print(f"  ⚠️ {quoi} absent — bloc ignoré", flush=True)
        return j, []
    d = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    ctl.exiger_colonnes(d, colonnes, quoi)
    ctl.exiger_variation(d, colonnes, quoi)
    if "jour" in d.columns:
        d["jour"] = pd.to_datetime(d["jour"])
    avant = len(j)
    j = j.merge(d, on=cle, how="inner")
    ctl.exiger_lignes(j, max(1000, avant // 4), f"{quoi} après jointure")
    print(f"  {quoi} · {len(fichiers)} fichiers · {avant:,} → {len(j):,} lignes", flush=True)
    return j, colonnes


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    seuil = SEUILS[polluant]
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    # Les membres sont horaires : ils se joignent avant l'agrégation journalière.
    jeu, membres = joindre(jeu, f"membres_metropole_{COURT[polluant]}_*.parquet",
                           MEMBRES, ["station_id", "timestamp_utc"], "membres d'ensemble")

    j = agreger_journalier(jeu, colonnes + membres, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    j["jour"] = pd.to_datetime(j["jour"])

    passees, obs = variables_passees(j)
    j = j.merge(passees, on=["station_id", "jour"], how="left").dropna(subset=obs)

    feux_cols = ["feu_iso_proche", "feu_iso_moyen", "feu_iso_loin",
                 "feu_vent_proche", "feu_vent_moyen", "feu_vent_loin"]
    j, feux = joindre(j, "feux_metropole_*.parquet", feux_cols,
                      ["station_id", "jour"], "exposition aux feux")

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    vrai = (j["obs_jour"] >= seuil).to_numpy()
    groupe = j["groupe"].to_numpy()
    print(f"\n{polluant} · {len(j):,} jours-station · {len(stations)} stations · "
          f"{int(vrai.sum())} dépassements ({100 * vrai.mean():.2f} %)\n", flush=True)

    residu = (j["obs_jour"] - j["cams_jour"]).to_numpy()
    plan = [("CAMS brut", None), ("correction", base),
            ("+ observations J−2", base + obs)]
    if membres:
        plan.append(("+ membres d'ensemble", base + obs + membres))
    if feux:
        plan.append(("+ feux", base + obs + membres + feux))

    produits = {}
    for nom, predicteurs in plan:
        if predicteurs is None:
            produits[nom] = j["cams_jour"].to_numpy()
            continue
        produits[nom] = ajuster(j, predicteurs, residu, n_plis, "regression")
        print(f"  {nom} ajusté ({len(predicteurs)} var) · {time.time() - depart:.0f}s",
              flush=True)

    lignes = []
    for budget in BUDGETS:
        print(f"\n── budget de fausses alertes ≤ {budget:.0%} ──")
        print(f"{'produit':24s} {'rappel':>8s} {'FAR':>7s} {'CSI':>7s}")
        for nom, score in produits.items():
            r = rappel_hors_echantillon(vrai, score, groupe, budget, n_plis)
            if not r:
                print(f"{nom:24s} {'—':>8s}   budget inatteignable")
                continue
            print(f"{nom:24s} {r['POD']:8.3f} {r['FAR']:7.3f} {r['CSI']:7.3f}", flush=True)
            lignes.append({"budget": budget, "produit": nom, **r})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/detection_complete_{polluant}.csv", index=False)

    print(f"\n{'═' * 74}")
    for budget in BUDGETS:
        s = table[table["budget"] == budget]
        if len(s) < 2:
            continue
        g = s.loc[s["POD"].idxmax()]
        brut = s[s["produit"] == "CAMS brut"]["POD"]
        f = g["POD"] / brut.iloc[0] if len(brut) and brut.iloc[0] > 0 else np.nan
        print(f"à {budget:.0%} : **{g['produit']}** rappelle {g['POD']:.3f}"
              + (f" — {f:.1f}× le brut" if not np.isnan(f) else ""))
    print(f"\nÉcrit : reports/detection_complete_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="PM25")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
