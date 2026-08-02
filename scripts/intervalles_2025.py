#!/usr/bin/env python3
"""Ce que 21 stations et 163 dépassements autorisent réellement à dire.

Le problème
-----------
Le test hors échantillon 2025 produit des écarts que le dossier cite comme des résultats :
RMSE 10,33 contre 13,56, CSI 0,495 contre 0,387, AUC-PR 0,786 contre 0,764. Aucun n'a
d'intervalle. Or l'échantillon est petit — 3 353 jours-station, mais **21 stations
seulement**, et les jours d'une même station ne sont pas indépendants : un épisode dure et
touche toutes les stations d'une région à la fois.

Un écart de 0,048 de CSI sur cette base peut très bien être du bruit. Le publier sans le
dire serait la faute que ce projet reproche par ailleurs aux moyennes annuelles.

La méthode
----------
**Bootstrap apparié par blocs sur les deux axes.** On tire avec remise des *stations* et des
*blocs calendaires* de 7 jours, et l'on recalcule la métrique **dans chaque tirage** pour les
trois produits sur les **mêmes lignes**. L'appariement est essentiel : ce qui nous intéresse
n'est pas la variance de chaque score mais celle de leur **différence**, bien plus petite
puisque les produits partagent leurs jours difficiles.

Trois longueurs de bloc — 3, 7 et 14 jours — parce qu'une conclusion qui dépendrait de la
longueur choisie n'en serait pas une.

**Ce que le script ne fait pas** : il ne corrige pas la multiplicité. Les intervalles sont
lus un par un, et un écart dont l'intervalle frôle zéro doit être annoncé comme non concluant,
pas comme « presque significatif ».

Usage : python3 scripts/intervalles_2025.py [--tirages 2000]
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

from scores_episodes import scores  # noqa: E402

SEUIL = 120.0
# Seuils de décision calibrés sur 2024 (cf. scripts/seuil_decision.py). Figés ici pour que
# le bootstrap ne les rechoisisse pas à chaque tirage — les rechoisir mesurerait la variance
# de la calibration, pas celle de la comparaison.
SEUILS_CALIBRES = {"cams": 113.5, "officiel_mos": 105.9, "corrige": 111.7}
PRODUITS = [("CAMS brut", "cams"), ("MOS officiel", "officiel_mos"), ("nous", "corrige")]


def rmse(obs: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((obs - pred) ** 2)))


def metriques_bloc(d: pd.DataFrame) -> dict[str, float]:
    """Les trois scores comparés, pour un échantillon donné."""
    obs = d["observe"].to_numpy()
    depasse = obs >= SEUIL
    sortie = {}
    for _, col in PRODUITS:
        pred = d[col].to_numpy()
        sortie[f"rmse_{col}"] = rmse(obs, pred)
        s = scores(depasse, pred >= SEUILS_CALIBRES[col]) if depasse.sum() >= 5 else {}
        sortie[f"csi_{col}"] = s.get("CSI", np.nan)
        sortie[f"pod_{col}"] = s.get("POD", np.nan)
        sortie[f"far_{col}"] = s.get("FAR", np.nan)
    return sortie


def tirer(d: pd.DataFrame, blocs: int, rng: np.random.Generator) -> pd.DataFrame:
    """Un tirage : stations avec remise × blocs calendaires avec remise.

    Les deux axes sont rééchantillonnés **ensemble**. Ne tirer que les stations ignorerait
    qu'un épisode traverse la région entière ; ne tirer que le temps ignorerait qu'une
    station atypique pèse sur tout le score.
    """
    stations = rng.choice(d["station_id"].unique(), size=d["station_id"].nunique(),
                          replace=True)
    ids_blocs = d["bloc"].unique()
    choisis = rng.choice(ids_blocs, size=len(ids_blocs), replace=True)

    # Produit des deux tirages : on empile les sous-tables correspondantes. Une station ou un
    # bloc tiré deux fois apparaît deux fois — c'est le principe du bootstrap.
    par_station = {s: g for s, g in d.groupby("station_id")}
    morceaux = []
    for s in stations:
        g = par_station[s]
        par_bloc = {b: h for b, h in g.groupby("bloc")}
        for b in choisis:
            if b in par_bloc:
                morceaux.append(par_bloc[b])
    return pd.concat(morceaux, ignore_index=True) if morceaux else d.iloc[:0]


def main(tirages: int, longueurs: tuple[int, ...]) -> int:
    depart = time.time()
    chemin = RACINE / "reports/test_hors_echantillon_2025_detail_O3.csv"
    if not chemin.exists():
        raise SystemExit(f"{chemin.name} absent")
    d = pd.read_csv(chemin, parse_dates=["jour"]).rename(
        columns={"obs_jour": "observe", "cams_jour": "cams"})
    d = d.dropna(subset=["observe"] + [c for _, c in PRODUITS])

    reference = metriques_bloc(d)
    n_dep = int((d["observe"] >= SEUIL).sum())
    print(f"O₃ 2025 · {len(d):,} jours-station · {d['station_id'].nunique()} stations · "
          f"{n_dep} dépassements\n", flush=True)
    print("Estimations ponctuelles (seuils calibrés sur 2024) :")
    print(f"{'produit':14s} {'RMSE':>7s} {'POD':>7s} {'FAR':>7s} {'CSI':>7s}")
    for nom, col in PRODUITS:
        print(f"{nom:14s} {reference[f'rmse_{col}']:7.2f} {reference[f'pod_{col}']:7.3f} "
              f"{reference[f'far_{col}']:7.3f} {reference[f'csi_{col}']:7.3f}", flush=True)

    lignes = []
    jour0 = d["jour"].min()
    for longueur in longueurs:
        d["bloc"] = ((d["jour"] - jour0).dt.days // longueur).astype(int)
        rng = np.random.default_rng(0)
        replications = []
        for _ in range(tirages):
            ech = tirer(d, longueur, rng)
            if len(ech) < 200 or (ech["observe"] >= SEUIL).sum() < 5:
                continue
            replications.append(metriques_bloc(ech))
        rep = pd.DataFrame(replications)

        print(f"\n{'─' * 74}\nBlocs de {longueur} jours · {len(rep)} tirages retenus · "
              f"{d['bloc'].nunique()} blocs")
        print(f"{'comparaison':34s} {'écart':>8s} {'IC95':>20s}  verdict")
        for metrique, sens in (("rmse", -1), ("csi", +1), ("pod", +1)):
            for nom_a, col_a in PRODUITS[:-1]:
                diff = (rep[f"{metrique}_corrige"] - rep[f"{metrique}_{col_a}"]).dropna()
                if diff.empty:
                    continue
                bas, haut = np.percentile(diff, [2.5, 97.5])
                point = (reference[f"{metrique}_corrige"]
                         - reference[f"{metrique}_{col_a}"])
                # « Concluant » = l'intervalle ne contient pas zéro. Rien d'autre.
                concluant = (bas > 0) or (haut < 0)
                favorable = concluant and (np.sign(point) == sens)
                verdict = ("✅ favorable" if favorable else
                           "❌ défavorable" if concluant else "— non concluant")
                print(f"{metrique.upper() + ' : nous − ' + nom_a:34s} {point:+8.3f} "
                      f"[{bas:+8.3f} ; {haut:+8.3f}]  {verdict}", flush=True)
                lignes.append({"bloc_jours": longueur, "metrique": metrique,
                               "contre": nom_a, "ecart": point, "ic_bas": bas,
                               "ic_haut": haut, "concluant": concluant})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / "reports/intervalles_2025_O3.csv", index=False)

    print(f"\n{'═' * 74}")
    # **La stabilité aux trois longueurs est le vrai test.** Une conclusion qui n'apparaît
    # qu'à une longueur de bloc est un artefact du découpage.
    stable = (table.groupby(["metrique", "contre"])["concluant"]
                   .agg(["sum", "count"]).reset_index())
    for _, r in stable.iterrows():
        etat = ("concluant aux 3 longueurs" if r["sum"] == r["count"]
                else f"concluant à {int(r['sum'])}/{int(r['count'])} longueurs — "
                     f"**instable, à présenter comme descriptif**" if r["sum"]
                else "jamais concluant")
        print(f"{r['metrique'].upper():6s} contre {r['contre']:14s} : {etat}")
    print(f"\nÉcrit : reports/intervalles_2025_O3.csv · {time.time() - depart:.0f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tirages", type=int, default=2000)
    args = p.parse_args()
    raise SystemExit(main(args.tirages, (3, 7, 14)))
