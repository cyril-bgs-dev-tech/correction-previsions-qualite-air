#!/usr/bin/env python3
"""La titration, écrite comme la chimie l'écrit — et non comme une jointure de colonnes.

Pourquoi ce second essai
------------------------
`apport_copolluants.py` a ajouté les concentrations CAMS des autres espèces en **µg/m³**,
agrégées en moyenne journalière. Résultat : rien. Sur O₃, +0,069 µg/m³ avec un IC95 contenant
zéro, et un CSI qui baisse.

Une relecture externe a nommé deux fautes de construction, et elles sont physiques :

1. **On n'additionne pas des µg/m³.** O₃ (M = 48) et NO₂ (M = 46) n'ont pas la même masse
   molaire ; la chimie opère sur des **rapports molaires**. La grandeur qui porte le mécanisme
   est l'**oxydant total** `Ox = χ(O₃) + χ(NO₂)`, approximativement **conservé** par la
   titration `NO + O₃ → NO₂ + O₂` : celle-ci redistribue l'ozone vers le dioxyde d'azote sans
   détruire l'oxydant. Un O₃ faux avec un Ox juste désigne une erreur de **partition locale** ;
   un Ox faux désigne une erreur de **production, transport ou dépôt**. Ce sont deux défauts
   différents, et la concentration brute ne les sépare pas.
2. **La titration est nocturne et locale.** Elle s'exerce près des sources, la nuit, quand la
   photolyse ne régénère plus l'ozone. Une moyenne journalière la dilue précisément dans les
   heures où elle n'agit pas.

Ce que le script construit
--------------------------
Six variables, toutes dérivées de champs déjà sur le disque, aucune requête :

| variable | définition | ce qu'elle doit porter |
|---|---|---|
| `ox` | χ(O₃) + χ(NO₂), moyenne du jour | niveau d'oxydant, insensible à la titration |
| `f_no2` | χ(NO₂) / Ox | degré de titration, donc urbanité chimique |
| `ox_nuit`, `f_no2_nuit` | idem, 21 h – 05 h UTC | le mécanisme là où il agit |
| `no2_max_nuit` | maximum nocturne de χ(NO₂) | potentiel de destruction de l'ozone |
| `amplitude_f_no2` | f_no2 nuit − f_no2 jour | bascule diurne du régime |

**Ce que le test ne peut pas montrer.** Sans NO ni COV, on ne diagnostique pas le régime
limité par les NOₓ ou par les COV : `f_no2` est un indicateur de titration et d'urbanité, pas
un diagnostic de sensibilité de production. Le gain attendu porte donc sur les **faibles ozones
nocturnes et les stations urbaines**, pas sur les maxima photochimiques ruraux.

Usage : python3 scripts/apport_chimie.py [--polluant O3]
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

from aq.eval.critere import seuil  # noqa: E402
from apport_meteo import evaluer, ic_difference, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import ESPECES, TRANCHES, charger, colonnes_admises  # noqa: E402

# Masses molaires, g/mol. Le rapport molaire est proportionnel à C/M ; les constantes
# communes (volume molaire, température, pression) se simplifient dans les rapports et ne
# changent rien à un arbre, qui est invariant par transformation monotone d'une variable.
M = {"o3": 48.0, "no2": 46.0}
NUIT = (21, 5)  # heures UTC — approximation raisonnable de la période sans photolyse
# Le critère de rétention vit dans `aq.eval.critere` : **relatif au RMSE de base**,
# donc comparable entre polluants. L'ancien 0,3 µg/m³ absolu valait 2 % sur le NO₂
# et 11 % sur les PM2,5 — il écartait ces dernières par artefact d'unité.


def champs_chimie(horizon: int,
                  bornes: tuple[pd.Timestamp, pd.Timestamp]) -> tuple[pd.DataFrame, list[str]]:
    """Construit les variables d'oxydant et de partition, au jour-station."""
    bas, haut = TRANCHES[horizon]
    debut, fin = bornes
    especes = {}
    for court in ("o3", "no2"):
        colonne = ESPECES[court][1]
        blocs = []
        for f in sorted(glob.glob(str(
                RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_*.parquet"))):
            d = pd.read_parquet(
                f, columns=["station_id", "timestamp_utc", "echeance_h", colonne])
            d = d[d["echeance_h"].between(bas, haut)]
            d = d[(d["timestamp_utc"] >= debut) & (d["timestamp_utc"] <= fin)]
            if not d.empty:
                blocs.append(d)
        t = pd.concat(blocs, ignore_index=True)
        t = t.groupby(["station_id", "timestamp_utc"], as_index=False)[colonne].mean()
        especes[court] = t.rename(columns={colonne: court})

    h = especes["o3"].merge(especes["no2"], on=["station_id", "timestamp_utc"], how="inner")
    # Rapports molaires, à une constante près commune aux deux espèces.
    h["chi_o3"] = h["o3"] / M["o3"]
    h["chi_no2"] = h["no2"] / M["no2"]
    h["ox"] = h["chi_o3"] + h["chi_no2"]
    h["f_no2"] = h["chi_no2"] / h["ox"].replace(0, np.nan)

    h["jour"] = h["timestamp_utc"].dt.floor("D")
    heure = h["timestamp_utc"].dt.hour
    h["est_nuit"] = (heure >= NUIT[0]) | (heure < NUIT[1])

    jour = (h.groupby(["station_id", "jour"])
             .agg(ox=("ox", "mean"), f_no2=("f_no2", "mean")).reset_index())
    nuit = (h[h["est_nuit"]].groupby(["station_id", "jour"])
             .agg(ox_nuit=("ox", "mean"), f_no2_nuit=("f_no2", "mean"),
                  no2_max_nuit=("chi_no2", "max")).reset_index())
    diurne = (h[~h["est_nuit"]].groupby(["station_id", "jour"])
               .agg(f_no2_jour=("f_no2", "mean")).reset_index())

    t = jour.merge(nuit, on=["station_id", "jour"], how="left").merge(
        diurne, on=["station_id", "jour"], how="left")
    t["amplitude_f_no2"] = t["f_no2_nuit"] - t["f_no2_jour"]
    noms = ["ox", "f_no2", "ox_nuit", "f_no2_nuit", "no2_max_nuit", "amplitude_f_no2"]
    return t.drop(columns=["f_no2_jour"]), noms


def main(polluant: str, horizon: int, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, colonnes, grandeur)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    chimie, noms = champs_chimie(
        horizon, (jeu["timestamp_utc"].min(), jeu["timestamp_utc"].max()))
    j["jour"] = pd.to_datetime(j["jour"])
    chimie["jour"] = pd.to_datetime(chimie["jour"])
    avant = len(j)
    j = j.merge(chimie, on=["station_id", "jour"], how="inner").dropna(subset=noms)
    print(f"{polluant} · {avant:,} → {len(j):,} jours-station après jointure chimie "
          f"({100 * len(j) / avant:.0f} %) · {j['station_id'].nunique()} stations", flush=True)
    print(f"  f_no2 médian {j['f_no2'].median():.3f} · nuit {j['f_no2_nuit'].median():.3f} "
          f"· amplitude médiane {j['amplitude_f_no2'].median():+.3f}", flush=True)

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})

    jeux = {"base (actuel)": base, "+ chimie (Ox, partition)": base + noms}
    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:26s} {len(predicteurs):3d} variables · "
              f"RMSE {resultats[nom]['rmse']:6.3f} · {time.time() - depart:5.0f}s", flush=True)

    print(f"\n{'jeu':26s} {'RMSE':>7s} {'décile haut':>12s} {'POD':>7s} {'CSI':>7s}")
    for nom, r in resultats.items():
        print(f"{nom:26s} {r['rmse']:7.3f} {r['rmse_decile_haut']:12.3f} "
              f"{r.get('POD', np.nan):7.3f} {r.get('CSI', np.nan):7.3f}", flush=True)

    ref, ajout = resultats["base (actuel)"], resultats["+ chimie (Ox, partition)"]
    gain = ref["rmse"] - ajout["rmse"]
    bas, haut = ic_difference(predictions["base (actuel)"],
                              predictions["+ chimie (Ox, partition)"])
    queue = ajout["rmse_decile_haut"] - ref["rmse_decile_haut"]

    print(f"\n{'─' * 74}")
    print(f"gain {gain:+.3f} µg/m³ ({100 * gain / ref['rmse']:+.1f} % relatif) · "
          f"IC95 [{bas:+.3f} ; {haut:+.3f}] · décile haut {queue:+.3f}")
    concluant = bas > 0
    print(f"→ {'écart établi' if concluant else 'IC contenant zéro — non concluant'}"
          f" · {'au-dessus' if gain >= seuil(ref['rmse']) else 'sous'} le critère relatif"
          f" de {seuil(ref['rmse']):.3f} µg/m³ (2 % du RMSE de base)")

    # **La comparaison qui décide vraiment** : la formulation chimique fait-elle mieux que la
    # jointure brute de concentrations, qui n'avait rien donné ? Si les deux sont nulles, ce
    # n'est pas la construction des variables qui est en cause — c'est que CAMS modélise déjà
    # ce mécanisme, et qu'une correction n'ajoute rien là où la physique n'est pas aveugle.
    brut = RACINE / f"reports/apport_copolluants_{polluant}_ic.csv"
    if brut.exists():
        g0 = float(pd.read_csv(brut)["gain"].iloc[0])
        print(f"\nconcentrations brutes (essai précédent) : {g0:+.3f} µg/m³")
        print(f"formulation chimique                    : {gain:+.3f} µg/m³  "
              f"({gain - g0:+.3f})")
        if gain - g0 < 0.1:
            print("→ la construction n'était pas le problème : **CAMS modélise déjà cette "
                  "chimie**.\n  Une correction n'ajoute rien là où la physique n'est pas "
                  "aveugle — même conclusion\n  que pour les variables forestières, dont le "
                  "retrait améliorait le modèle.")

    pd.DataFrame([{"polluant": polluant, "gain": gain, "relatif_pct": 100 * gain / ref["rmse"],
                   "ic_bas": bas, "ic_haut": haut, "cout_queue": queue}]).to_csv(
        RACINE / f"reports/apport_chimie_{polluant}_ic.csv", index=False)
    pd.DataFrame(resultats).T.to_csv(RACINE / f"reports/apport_chimie_{polluant}.csv")
    print(f"\nÉcrit : reports/apport_chimie_{polluant}.csv · {time.time() - depart:.0f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
