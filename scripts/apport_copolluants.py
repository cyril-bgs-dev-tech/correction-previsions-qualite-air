#!/usr/bin/env python3
"""Croiser les polluants : ce qui dormait sur le disque depuis le début.

Le constat
----------
Le modèle reçoit **une seule** concentration CAMS — celle du polluant qu'il corrige — alors que
les prévisions des trois espèces sont dans les mêmes fichiers, aux mêmes stations, aux mêmes
instants, aux mêmes échéances. Trois modèles ont donc été entraînés côte à côte en s'ignorant.

C'est un défaut de conception, pas de données : le pipeline mental « un modèle = une cible = un
CAMS de la cible » a fait traiter un fichier multi-espèces comme l'archive de trois projets
parallèles.

Pourquoi la chimie dit que ça devrait servir
--------------------------------------------
NO₂ et O₃ sont couplés par la **titration** : NO + O₃ → NO₂ + O₂. Là où le NO₂ est élevé —
stations trafic, nuit, cœur urbain — l'ozone est mécaniquement détruit. Un modèle qui corrige
l'ozone sans voir le NO₂ prévu ignore le principal mécanisme de sa destruction locale, celui
que la maille de 8 × 11 km résout mal précisément parce qu'il est de proximité.

Les particules secondaires, elles, se forment à partir de précurseurs dont le NO₂ est un
traceur. La prédiction est donc **asymétrique** : le NO₂ devrait aider l'ozone et les
particules plus que l'inverse.

Ce que le script ne fait pas
----------------------------
Il ne fabrique **pas** un modèle multi-sorties. Les prédicteurs sont croisés, les têtes restent
séparées et déployables indépendamment — un service doit pouvoir corriger le NO₂ sans toucher à
la chaîne ozone la veille d'un pic estival, et une espèce CAMS manquante ne doit pas contaminer
les deux autres.

Usage : python3 scripts/apport_copolluants.py [--polluant O3]
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

from aq.eval import comparaison as cmp  # noqa: E402
from aq.eval.critere import cribler, seuil  # noqa: E402
from apport_meteo import evaluer, ic_difference, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import ESPECES, TRANCHES, charger, colonnes_admises  # noqa: E402

# Le critère de rétention vit dans `aq.eval.critere` : **relatif au RMSE de base**,
# donc comparable entre polluants. L'ancien 0,3 µg/m³ absolu valait 2 % sur le NO₂
# et 11 % sur les PM2,5.


def copolluants(cible: str, horizon: int,
                bornes: tuple[pd.Timestamp, pd.Timestamp]) -> tuple[pd.DataFrame, list[str]]:
    """Charge les prévisions CAMS des **autres** espèces, aux mêmes clés."""
    court_cible = next(c for c, (p, _) in ESPECES.items() if p == cible)
    bas, haut = TRANCHES[horizon]
    debut, fin = bornes

    tables, noms = [], []
    for court, (polluant, colonne) in ESPECES.items():
        if court == court_cible:
            continue
        fichiers = sorted(glob.glob(str(
            RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_*.parquet")))
        if not fichiers:
            continue
        blocs = []
        for f in fichiers:
            d = pd.read_parquet(
                f, columns=["station_id", "timestamp_utc", "echeance_h", colonne])
            d = d[d["echeance_h"].between(bas, haut)]
            d = d[(d["timestamp_utc"] >= debut) & (d["timestamp_utc"] <= fin)]
            if not d.empty:
                blocs.append(d)
        if not blocs:
            continue
        t = pd.concat(blocs, ignore_index=True).rename(
            columns={colonne: f"cams_{court}"})
        # Une même clé peut porter plusieurs échéances dans la tranche : on moyenne, comme le
        # fait déjà l'agrégation journalière pour la cible.
        t = t.groupby(["station_id", "timestamp_utc"], as_index=False)[
            f"cams_{court}"].mean()
        tables.append(t)
        noms.append(f"cams_{court}")

    if not tables:
        raise SystemExit("aucune autre espèce CAMS disponible")
    fusion = tables[0]
    for t in tables[1:]:
        fusion = fusion.merge(t, on=["station_id", "timestamp_utc"], how="outer")
    return fusion, noms


def main(polluant: str, horizon: int, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    co, noms = copolluants(polluant, horizon,
                           (jeu["timestamp_utc"].min(), jeu["timestamp_utc"].max()))
    avant = len(jeu)
    jeu = jeu.merge(co, on=["station_id", "timestamp_utc"], how="left")
    couverture = float(jeu[noms].notna().all(axis=1).mean())
    print(f"{polluant} · {avant:,} lignes horaires · copolluants {', '.join(noms)} "
          f"renseignés sur {100 * couverture:.1f} %", flush=True)
    jeu = jeu.dropna(subset=noms)

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    # Les copolluants entrent dans l'agrégation comme les autres prédicteurs : moyenne du jour.
    j = agreger_journalier(jeu, colonnes + noms, grandeur)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    print(f"  {len(j):,} jours-station · {len(stations)} stations", flush=True)

    jeux = {"base (actuel)": base, "+ copolluants CAMS": base + noms}
    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:22s} {len(predicteurs):3d} variables · "
              f"RMSE {resultats[nom]['rmse']:6.3f} · {time.time() - depart:5.0f}s", flush=True)

    print(f"\n{'jeu':22s} {'RMSE':>7s} {'décile haut':>12s} {'POD':>7s} {'FAR':>7s} {'CSI':>7s}")
    for nom, r in resultats.items():
        print(f"{nom:22s} {r['rmse']:7.3f} {r['rmse_decile_haut']:12.3f} "
              f"{r.get('POD', np.nan):7.3f} {r.get('FAR', np.nan):7.3f} "
              f"{r.get('CSI', np.nan):7.3f}", flush=True)

    ref, ajout = resultats["base (actuel)"], resultats["+ copolluants CAMS"]
    gain = ref["rmse"] - ajout["rmse"]
    bas, haut = ic_difference(predictions["base (actuel)"], predictions["+ copolluants CAMS"])
    queue = ajout["rmse_decile_haut"] - ref["rmse_decile_haut"]
    d_csi = ajout.get("CSI", np.nan) - ref.get("CSI", np.nan)
    retenu = cribler(ref["rmse"], gain, bas, gain_queue=-queue,
                     rmse_queue_base=ref["rmse_decile_haut"]).retenu

    print(f"\n{'─' * 74}")
    print(f"gain {gain:+.3f} µg/m³ ({100 * gain / ref['rmse']:+.1f} % relatif) · "
          f"IC95 [{bas:+.3f} ; {haut:+.3f}]")
    print(f"décile haut {queue:+.3f} · ΔCSI {d_csi:+.3f}")
    print(f"→ {'RETENU' if retenu else 'sous le critère d’arrêt absolu de 0,3'}")
    # Le critère absolu est connu pour être **défectueux** entre polluants d'échelles
    # différentes : on affiche aussi le relatif, seul comparable d'un polluant à l'autre.
    print(f"   (critère relatif : {seuil(ref['rmse']):.3f} µg/m³, soit 2 % du "
          f"RMSE de ce polluant — il n'est pas comparable d'une espèce à l'autre)")

    pd.DataFrame(resultats).T.to_csv(RACINE / f"reports/apport_copolluants_{polluant}.csv")
    pd.DataFrame([{"polluant": polluant, "gain": gain, "relatif_pct": 100 * gain / ref["rmse"],
                   "ic_bas": bas, "ic_haut": haut, "cout_queue": queue, "delta_csi": d_csi,
                   "retenu": retenu, "couverture": couverture}]).to_csv(
        RACINE / f"reports/apport_copolluants_{polluant}_ic.csv", index=False)
    print(f"\nÉcrit : reports/apport_copolluants_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
