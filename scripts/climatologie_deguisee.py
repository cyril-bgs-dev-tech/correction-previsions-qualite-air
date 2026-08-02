#!/usr/bin/env python3
"""Le modèle corrige-t-il CAMS, ou apprend-il une climatologie locale ?

Le soupçon
----------
Les importances de variables, lues pour la première fois le 30/07, donnent :

| famille | part |
|---|---|
| calendrier (jour de l'année, jour de semaine) | **37 %** |
| CAMS (max 8 h + moyenne journalière) | **18 %** |
| coordonnées | 8 % |

Un correcteur où le champ à corriger ne pèse que 18 % pose une question simple : le modèle
s'appuie-t-il sur *ce que CAMS annonce*, ou surtout sur *quand* et *où* — c'est-à-dire une
**climatologie locale apprise** ?

L'enjeu n'est pas cosmétique. Si une climatologie suffit, alors le projet ne démontre pas
qu'une correction de chaîne opérationnelle est utile : il démontre qu'on peut prédire l'ozone
sans modèle de chimie-transport, ce qui est un tout autre propos — et un propos plus faible,
puisque la climatologie ne peut par construction pas anticiper un épisode atypique.

Le test
-------
Trois modèles, **mêmes plis de stations exclues**, même grandeur réglementaire :

| Modèle | Cible | Prédicteurs | Ce qu'il représente |
|---|---|---|---|
| **CAMS brut** | — | — | la chaîne opérationnelle seule |
| **Climatologie apprise** | l'observation | **tout sauf CAMS** | ce qu'on prédit sans modèle physique |
| **MOS** | le résidu | tout | le dispositif du projet |

La lecture est directe : si la climatologie apprise approche le MOS, CAMS n'apporte presque
rien et le récit doit changer. Si elle en reste loin, le modèle corrige bien une prévision
physique et ne la remplace pas.

Le test est **décisif dans les deux sens**, ce qui est la condition pour qu'il vaille d'être
fait.

Usage : python3 scripts/climatologie_deguisee.py [--polluant O3]
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

from aq.eval import comparaison as cmp  # noqa: E402
from aq.models import mos  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from scores_episodes import scores  # noqa: E402

SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0}


def _xgb(graine: int):
    return modele_mos(graine=graine)


def main(polluant: str, horizon: int, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, colonnes, grandeur)
    d = j.rename(columns={"obs_jour": "valeur", "jour": "timestamp_utc"})

    tous = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    # « Tout sauf CAMS » : ni la prévision du jour, ni sa moyenne, ni rien qui en dérive.
    sans_cams = [c for c in tous if not c.startswith("cams")]

    seuil = SEUILS[polluant]
    base = cmp.metriques(d["valeur"], d["cams_jour"])
    depasse = (d["valeur"] >= seuil).to_numpy()
    s_base = scores(depasse, (d["cams_jour"] >= seuil).to_numpy())

    print(f"{polluant} · {grandeur} · {len(d):,} jours-station · "
          f"{d['station_id'].nunique()} stations")
    print(f"  prédicteurs : {len(tous)} au total, {len(sans_cams)} sans CAMS\n", flush=True)

    print(f"{'modèle':26s} {'RMSE':>7s} {'R²':>8s} {'vs CAMS':>9s} {'POD':>6s} {'CSI':>6s}")
    print(f"{'CAMS brut':26s} {base['rmse']:7.2f} {base['r2']:+8.3f} {'—':>9s} "
          f"{s_base['POD']:6.3f} {s_base['CSI']:6.3f}", flush=True)

    lignes = [{"modele": "CAMS brut", **base, **{f"s_{k}": v for k, v in s_base.items()}}]
    for nom, cols, residu in (("climatologie apprise", sans_cams, False),
                              ("MOS (référence)", tous, True)):
        r = mos.ajuster_par_stations_exclues(
            d, cols, colonne_cams="cams_jour", n_plis=n_plis, cible_residu=residu,
            verbeux=False, fabrique_modele=_xgb,
        )
        p = r.predictions.dropna(subset=["observe"])
        m = cmp.metriques(p["observe"], p["corrige"])
        dep = (p["observe"] >= seuil).to_numpy()
        s = scores(dep, (p["corrige"] >= seuil).to_numpy())
        print(f"{nom:26s} {m['rmse']:7.2f} {m['r2']:+8.3f} "
              f"{100 * (1 - m['rmse'] / base['rmse']):+8.1f} % {s['POD']:6.3f} "
              f"{s['CSI']:6.3f}", flush=True)
        lignes.append({"modele": nom, **m, **{f"s_{k}": v for k, v in s.items()}})

    table = pd.DataFrame(lignes)
    clim = float(table.loc[table["modele"] == "climatologie apprise", "rmse"].iloc[0])
    mos_ = float(table.loc[table["modele"] == "MOS (référence)", "rmse"].iloc[0])
    part = 100 * (base["rmse"] - clim) / (base["rmse"] - mos_) if base["rmse"] > mos_ else np.nan

    print("\n" + "=" * 72)
    print(f"La climatologie apprise capture **{part:.0f} %** de l'écart entre CAMS brut et le "
          f"MOS.")
    if part >= 80:
        print("→ ⚠️ Le dispositif est largement une climatologie : CAMS n'apporte que le reste.")
    elif part >= 50:
        print("→ Une part importante du gain ne doit rien à CAMS. À dire explicitement.")
    else:
        print("→ Le modèle corrige bien une prévision physique : la climatologie seule reste "
              "loin.")
    print("\nÀ lire aussi sur la détection : une climatologie ne peut pas anticiper un "
          "épisode\natypique. Comparer les POD est plus révélateur que comparer les RMSE.")

    table.to_csv(RACINE / f"reports/climatologie_deguisee_{polluant}.csv", index=False)
    print(f"\nÉcrit : reports/climatologie_deguisee_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
