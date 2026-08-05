#!/usr/bin/env python3
"""Les deux flux GEOS-CF sont-ils le même prédicteur ? — mesuré sur le mois de recouvrement.

Pourquoi ce script existe
---------------------------
GEOS-CF a changé de flux : **v1** (`aqc_tavg_1hr_g1440x721_v1`, sortie 12z) a été retiré le
2 janvier 2026 ; **v2** (`aqc_tavg_1hr_glo_L1440x721_slv`, sortie 09z) a démarré le 5 août
2025. Le corpus du projet est donc coupé en deux — v1 jusqu'à décembre 2025, v2 à partir de
janvier 2026 — et **la coupure est imposée par le fournisseur**, pas choisie.

Un corpus qui empile les deux donne au modèle une colonne qui **change de définition** en
janvier 2026. Tout apport mesuré dessus peut venir du modèle apprenant à distinguer les deux
régimes : ce n'est pas de l'information sur la qualité de l'air. C'est la règle 4 ter du
projet — une convention non vérifiée est une hypothèse — appliquée à l'identité d'une
variable plutôt qu'à l'unité d'un axe.

Octobre 2025 est le seul mois extrait **dans les deux flux**, aux mêmes stations et aux
mêmes heures. Il tranche la question sans rien supposer.

Deux mesures, dans cet ordre
------------------------------
1. **v1 contre v2**, l'un contre l'autre : si l'écart est de l'ordre de l'erreur des modèles
   contre les observations, ce ne sont pas deux versions d'un même prédicteur.
2. **v1 et v2 chacun contre les observations** : l'écart seul ne dit pas *laquelle* a raison.
   Le biais départage la calibration, le **r** départage le pouvoir prédictif — et c'est lui
   qui compte, un arbre étant invariant par changement d'échelle linéaire.

Usage  : python3 scripts/comparer_geoscf_versions.py
Sortie : reports/geoscf_versions_recouvrement.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
MOIS = "2025-10"
V1 = RACINE / f"data/processed/meteo/geoscf_metropole_{MOIS.replace('-', '')}.parquet"
V2 = RACINE / f"data/processed/meteo/geoscf_metropole_{MOIS.replace('-', '')}_v2.parquet"
PANEL = RACINE / "data/processed/panel_unifie_lcsqa.parquet"
# ⚠️ `pm10` n'existe **que** dans v2 : v1 ne le publiait pas. La paire n'est donc pas
# comparable, et le nommer ici plutôt que de l'omettre en silence évite qu'on croie un jour
# que la comparaison l'a couvert.
PAIRES = {"O3": "geoscf_o3", "NO2": "geoscf_no2", "PM25": "geoscf_pm25"}
SANS_JUMEAU_V1 = ("geoscf_pm10",)


def rmse(a, b) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def main() -> int:
    for f in (V1, V2, PANEL):
        if not f.exists():
            raise SystemExit(f"absent : {f.relative_to(RACINE)}")

    a, b = pd.read_parquet(V1), pd.read_parquet(V2)
    for t in (a, b):
        t["timestamp_utc"] = pd.to_datetime(t["timestamp_utc"])
    # Compter le reçu contre le demandé (règle 2 bis) : les colonnes attendues, nommément.
    for nom, t in (("v1", a), ("v2", b)):
        manque = [c for c in PAIRES.values() if c not in t.columns]
        if manque:
            raise SystemExit(f"{nom} : colonnes absentes {manque}")
    absentes_v1 = [c for c in SANS_JUMEAU_V1 if c in b.columns and c not in a.columns]

    o = pd.read_parquet(PANEL, filters=[("polluant", "in", list(PAIRES))])
    o = o[o["flag_qualite"].eq("valide")].copy()
    o["timestamp_utc"] = pd.to_datetime(o["timestamp_utc"]).dt.tz_localize(None)
    deb = pd.Timestamp(f"{MOIS}-01")
    o = o[(o["timestamp_utc"] >= deb) & (o["timestamp_utc"] < deb + pd.offsets.MonthBegin(1))]
    if o.empty:
        raise SystemExit(f"aucune observation valide sur {MOIS}")

    print(f"Mois de recouvrement {MOIS} — le seul extrait dans les DEUX flux")
    print(f"  v1 : {len(a):,} lignes · {a['timestamp_utc'].min()} → {a['timestamp_utc'].max()}")
    print(f"  v2 : {len(b):,} lignes · {b['timestamp_utc'].min()} → {b['timestamp_utc'].max()}")
    print(f"  observations valides : {len(o):,} lignes · {o['station_id'].nunique()} stations")
    if absentes_v1:
        print(f"  ⚠️ publié par v2 seul, donc hors comparaison : {', '.join(absentes_v1)}")

    print(f"\n{'═' * 92}\n① LES DEUX FLUX L'UN CONTRE L'AUTRE — mêmes stations, mêmes heures\n{'═' * 92}")
    print(f"  {'variable':10s} {'n':>9s} {'moy v1':>9s} {'moy v2':>9s} {'écart moy':>10s} "
          f"{'RMSE écart':>11s} {'corr':>8s}")
    lignes = []
    apparies = {}
    for pol, col in PAIRES.items():
        m = a[["station_id", "timestamp_utc", col]].merge(
            b[["station_id", "timestamp_utc", col]],
            on=["station_id", "timestamp_utc"], suffixes=("_v1", "_v2")).dropna()
        apparies[pol] = m
        x, y = m[f"{col}_v1"].to_numpy(float), m[f"{col}_v2"].to_numpy(float)
        print(f"  {col[7:]:10s} {len(m):>9,} {x.mean():9.2f} {y.mean():9.2f} "
              f"{y.mean() - x.mean():+10.2f} {rmse(x, y):11.2f} "
              f"{np.corrcoef(x, y)[0, 1]:8.4f}")
        lignes.append({"mesure": "v1_contre_v2", "polluant": pol, "n": len(m),
                       "moy_v1": x.mean(), "moy_v2": y.mean(),
                       "ecart_moyen": y.mean() - x.mean(), "rmse_ecart": rmse(x, y),
                       "corr_v1_v2": float(np.corrcoef(x, y)[0, 1])})

    print(f"\n{'═' * 92}\n② CHACUN CONTRE LES OBSERVATIONS — l'écart ne dit pas laquelle a raison\n{'═' * 92}")
    print(f"  {'polluant':9s} {'n':>8s} {'moy obs':>8s} {'biais v1':>9s} {'biais v2':>9s} "
          f"{'RMSE v1':>8s} {'RMSE v2':>8s} {'r v1':>7s} {'r v2':>7s}   verdict sur r")
    for pol, col in PAIRES.items():
        op = o[o["polluant"] == pol][["station_id", "timestamp_utc", "valeur"]]
        m = op.merge(apparies[pol], on=["station_id", "timestamp_utc"]).dropna()
        if len(m) < 1000:
            print(f"  {pol:9s} {len(m):>8,} — trop peu d'appariements, non conclu")
            continue
        y = m["valeur"].to_numpy(float)
        x1, x2 = m[f"{col}_v1"].to_numpy(float), m[f"{col}_v2"].to_numpy(float)
        r1, r2 = np.corrcoef(y, x1)[0, 1], np.corrcoef(y, x2)[0, 1]
        # ⚠️ C'est **r** qui décide, pas le biais ni la RMSE : la variable sert de
        # prédicteur à un arbre, invariant par changement d'échelle linéaire.
        verdict = "v2" if r2 > r1 + 0.01 else ("v1" if r1 > r2 + 0.01 else "égalité")
        print(f"  {pol:9s} {len(m):>8,} {y.mean():8.2f} {x1.mean() - y.mean():+9.2f} "
              f"{x2.mean() - y.mean():+9.2f} {rmse(x1, y):8.2f} {rmse(x2, y):8.2f} "
              f"{r1:7.4f} {r2:7.4f}   {verdict}")
        lignes.append({"mesure": "contre_observations", "polluant": pol, "n": len(m),
                       "moy_obs": y.mean(), "biais_v1": x1.mean() - y.mean(),
                       "biais_v2": x2.mean() - y.mean(), "rmse_v1": rmse(x1, y),
                       "rmse_v2": rmse(x2, y), "r_v1": float(r1), "r_v2": float(r2),
                       "meilleur_sur_r": verdict})

    t = pd.DataFrame(lignes)
    for c in ("mesure", "polluant", "n"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")
    t["mois_recouvrement"] = MOIS
    f = RACINE / "reports/geoscf_versions_recouvrement.csv"
    t.to_csv(f, index=False)
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {len(t)} lignes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
