#!/usr/bin/env python3
"""Quelle part du gain météo revient au vent ?

Ce que la mesure précédente ne dit pas
--------------------------------------
`apport_meteo.py` établit que les huit variables ERA5 rendent **+7,8 %** sur l'ozone, +6,7 %
sur les PM2,5 et +2,7 % sur le NO₂. Mais elles y entrent **en bloc** : impossible de savoir si
le gain vient du rayonnement, de la température, du vent ou de la couche limite.

C'est une question pratique, pas académique. Le chantier suivant — récupérer une météo
**prévue** plutôt que réanalysée — coûte des heures de téléchargement, et son plan dépend
directement de ce qui porte le signal. Extraire treize niveaux de pression pour le vent n'a de
sens que si le vent compte.

Le découpage, par mécanisme et non par commodité
------------------------------------------------
| famille | variables | mécanisme visé |
|---|---|---|
| **vent** | direction (sin/cos pondérés), vitesse, maxima | transport, dilution, ventilation |
| **thermique** | température, point de rosée, maxima | production photochimique, partition semi-volatile |
| **rayonnement** | rayonnement global et son maximum | photolyse, moteur de la production d'ozone |
| **couche limite** | hauteur, minimum et maximum du jour | volume de dilution, accumulation nocturne |
| **hydrique** | précipitation, cumul, pression | lessivage, régime synoptique |

Chaque famille est mesurée **seule** contre la base, puis **retirée** du bloc complet. Les deux
lectures diffèrent quand les variables sont corrélées : une famille peut être utile isolément
et redondante en présence des autres. C'est précisément le cas qu'il faut distinguer avant de
décider quoi télécharger.

Usage : python3 scripts/informativite_vent.py [--polluant O3]
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

from apport_meteo import evaluer, ic_difference, meteo_journaliere, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

FAMILLES = {
    "vent": ["vent_sin", "vent_cos", "vent_vitesse_m_s", "vent_vitesse_max"],
    "thermique": ["temperature_c", "point_rosee_c", "temperature_max"],
    "rayonnement": ["rayonnement_w_m2", "rayonnement_max"],
    "couche limite": ["couche_limite_m", "couche_limite_min", "couche_limite_max"],
    "hydrique": ["precipitation_mm", "precipitation_totale", "pression_hpa"],
}


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    j["jour"] = pd.to_datetime(j["jour"])
    met, cols_moy, cols_enr = meteo_journaliere((j["jour"].min(), j["jour"].max()))
    met["jour"] = pd.to_datetime(met["jour"])
    j = j.merge(met, on=["station_id", "jour"], how="inner")
    toutes = [c for c in cols_moy + cols_enr if c in j.columns]

    # Une variable oubliée d'une famille fausserait les deux lectures : on le vérifie.
    classees = {v for fam in FAMILLES.values() for v in fam}
    orphelines = [c for c in toutes if c not in classees]
    if orphelines:
        print(f"⚠️ non classées, ajoutées à « hydrique » : {orphelines}")
        FAMILLES["hydrique"] = FAMILLES["hydrique"] + orphelines

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    print(f"{polluant} · {len(j):,} jours-station · {len(toutes)} variables météo\n",
          flush=True)

    reference = resume(evaluer(j, base, n_plis), polluant)
    complet = resume(evaluer(j, base + toutes, n_plis), polluant)
    print(f"base                     RMSE {reference['rmse']:6.3f}")
    print(f"base + toute la météo    RMSE {complet['rmse']:6.3f}  "
          f"(+{100 * (1 - complet['rmse'] / reference['rmse']):.1f} %)\n", flush=True)

    lignes = []
    print(f"{'famille':16s} {'seule':>18s} {'retirée du bloc':>20s}")
    for nom, variables in FAMILLES.items():
        presentes = [v for v in variables if v in j.columns]
        if not presentes:
            continue
        seule = resume(evaluer(j, base + presentes, n_plis), polluant)
        sans = resume(evaluer(j, base + [c for c in toutes if c not in presentes],
                              n_plis), polluant)
        gain_seule = reference["rmse"] - seule["rmse"]
        # Ce que la famille apporte **en plus** de toutes les autres : la vraie mesure de sa
        # non-redondance.
        marginal = sans["rmse"] - complet["rmse"]
        print(f"{nom:16s} {gain_seule:+8.3f} µg/m³   {marginal:+8.3f} µg/m³   "
              f"({len(presentes)} var)", flush=True)
        lignes.append({"famille": nom, "n_variables": len(presentes),
                       "gain_seule": gain_seule, "gain_marginal": marginal,
                       "rmse_seule": seule["rmse"], "rmse_sans": sans["rmse"]})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/informativite_vent_{polluant}.csv", index=False)

    print("\n" + "=" * 74)
    vent = table[table["famille"] == "vent"]
    if not vent.empty:
        v = vent.iloc[0]
        part = 100 * v["gain_seule"] / max(reference["rmse"] - complet["rmse"], 1e-9)
        print(f"Le vent seul rend {v['gain_seule']:+.3f} µg/m³, soit {part:.0f} % du gain "
              f"total de la météo.")
        print(f"Son apport **marginal**, toutes les autres familles présentes, vaut "
              f"{v['gain_marginal']:+.3f} µg/m³.")
        if v["gain_marginal"] < 0.05 <= v["gain_seule"]:
            print("→ le vent est **informatif mais redondant** : les autres familles portent "
                  "déjà son information.\n  Extraire les niveaux de pression pour lui seul ne se "
                  "justifierait pas.")
        elif v["gain_marginal"] >= 0.1:
            print("→ le vent apporte une information que les autres familles ne portent "
                  "pas.\n  Les grandeurs dérivées du profil vertical méritent le "
                  "téléchargement.")
    print(f"\nÉcrit : reports/informativite_vent_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
