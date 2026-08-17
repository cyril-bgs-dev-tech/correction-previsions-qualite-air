#!/usr/bin/env python3
"""L'incertitude d'un écart entre deux modèles — APPARIÉE, par blocs de mois et de stations.

Pourquoi ce script, et pourquoi la barre de bruit du dépôt ne convient pas
---------------------------------------------------------------------------
Ce dépôt a mesuré une barre de bruit de **±2,02 pt**, dominée par la composition des plis.
Elle porte sur un **score absolu, non apparié**. Or deux configurations comparées ici sont
ajustées et notées sur **exactement les mêmes lignes** : le déplacement commun causé par
une partition se **soustrait**. Comparer un écart apparié à une barre non appariée
surestime l'incertitude de plusieurs fois, et ferait déclarer « dans le bruit » des effets
qui n'y sont pas.

La quantité à estimer n'est donc pas la dispersion de chaque score, mais celle de la
**différence de pertes sur les mêmes observations** :

    d(s,t) = (obs − pred_candidat)² − (obs − pred_reference)²

Pourquoi des blocs, et pourquoi DEUX familles
-----------------------------------------------
Les résidus de qualité de l'air sont corrélés **dans le temps** (un épisode dure des jours)
et **dans l'espace** (les résidus PM restent corrélés sur des centaines de kilomètres). Un
bootstrap sur les lignes traiterait 200 000 observations comme 200 000 informations
indépendantes et rendrait un intervalle absurdement étroit. On rééchantillonne donc des
**mois entiers** et des **groupes géographiques**, puis on garde leur produit.

⚠️ **Ce que cet intervalle ne restaure pas.** Le bloc de test a déjà été consulté — pour
choisir des hyperparamètres, arrêter un réseau, lire un résultat. L'intervalle est
**conditionnel à ce test** ; il ne rend pas au bloc sa virginité. Une conclusion
confirmatoire demande une origine future.

Usage : python3 scripts/bootstrap_apparie.py --predictions reports/predictions_speciation_PM10.parquet
Sortie : reports/bootstrap_<nom>.csv
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

GRAINE = 20260817


def clusters_stations(d: pd.DataFrame, n: int) -> pd.Series:
    """Groupes géographiques fixes — la corrélation spatiale des résidus l'impose.

    À défaut de coordonnées dans le fichier de prédictions, on les reprend du référentiel.
    Un découpage ALÉATOIRE des stations serait un aveu : il supposerait indépendantes des
    stations voisines dont les résidus sont précisément corrélés.
    """
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "lat_wgs84", "lon_wgs84"]).dropna()
    st = st.drop_duplicates("station_id")
    xy = d[["station_id"]].merge(st, on="station_id", how="left")
    manque = xy["lat_wgs84"].isna().sum()
    if manque:
        raise SystemExit(f"{manque} lignes sans coordonnées — clusters impossibles")
    from sklearn.cluster import KMeans  # noqa: PLC0415

    km = KMeans(n_clusters=n, random_state=GRAINE, n_init=10)
    return pd.Series(km.fit_predict(xy[["lat_wgs84", "lon_wgs84"]].to_numpy()),
                     index=d.index)


def main(chemin: str, tirages: int, n_clusters: int, bloc_mois: int) -> int:
    t0 = time.time()
    f = Path(chemin)
    d = pd.read_parquet(f)
    for c in ("obs", "pred_reference", "pred_candidat", "station_id", "jour"):
        if c not in d.columns:
            raise SystemExit(f"colonne absente : {c}")
    d["mois"] = pd.to_datetime(d["jour"]).dt.strftime("%Y-%m")

    # ── L'écart ponctuel, sur toutes les lignes ────────────────────────────────────────
    def rmse(p):
        return float(np.sqrt(np.mean((d["obs"].to_numpy() - p) ** 2)))

    r_ref, r_cand = rmse(d["pred_reference"].to_numpy()), rmse(d["pred_candidat"].to_numpy())
    gain = 100 * (1 - r_cand / r_ref)
    print(f"{f.name}\n  {len(d):,} lignes · {d['station_id'].nunique()} stations · "
          f"{d['mois'].nunique()} mois", flush=True)
    print(f"  référence {r_ref:7.4f} · candidat {r_cand:7.4f} · "
          f"gain ponctuel {gain:+.2f} %", flush=True)

    d["cl"] = clusters_stations(d, n_clusters)
    mois = np.sort(d["mois"].unique())
    # Blocs de `bloc_mois` mois consécutifs, non chevauchants.
    blocs = [tuple(mois[i:i + bloc_mois]) for i in range(0, len(mois), bloc_mois)]
    cl = np.sort(d["cl"].unique())
    print(f"  {len(blocs)} blocs de {bloc_mois} mois · {len(cl)} groupes géographiques",
          flush=True)

    # Index par (bloc, cluster) — construit UNE fois, réutilisé à chaque tirage.
    par_cellule = {}
    m_bloc = {m: i for i, b in enumerate(blocs) for m in b}
    d["bloc"] = d["mois"].map(m_bloc)
    for (b, c), g in d.groupby(["bloc", "cl"], sort=False):
        par_cellule[(b, c)] = g.index.to_numpy()

    obs = d["obs"].to_numpy()
    pr, pc = d["pred_reference"].to_numpy(), d["pred_candidat"].to_numpy()
    rng = np.random.default_rng(GRAINE)
    gains = np.empty(tirages)
    for k in range(tirages):
        bb = rng.choice(len(blocs), len(blocs), replace=True)
        cc = rng.choice(cl, len(cl), replace=True)
        idx = np.concatenate([par_cellule[(b, c)] for b in bb for c in cc
                              if (b, c) in par_cellule])
        e_ref = np.sqrt(np.mean((obs[idx] - pr[idx]) ** 2))
        e_can = np.sqrt(np.mean((obs[idx] - pc[idx]) ** 2))
        gains[k] = 100 * (1 - e_can / e_ref)
        if (k + 1) % max(1, tirages // 5) == 0:
            print(f"    {k+1}/{tirages} tirages · {(time.time()-t0)/60:.1f} min", flush=True)

    bas, haut = np.percentile(gains, [2.5, 97.5])
    part_pos = float((gains > 0).mean())
    print(f"\n  gain {gain:+.2f} % · IC95 [{bas:+.2f} ; {haut:+.2f}] · "
          f"{100*part_pos:.1f} % des tirages positifs", flush=True)
    verdict = ("DÉMONTRÉ — la borne basse exclut zéro" if bas > 0 else
               "NON DÉMONTRÉ — l'intervalle contient zéro")
    print(f"  → {verdict}", flush=True)

    from aq.rapport import ecrire_rapport  # noqa: PLC0415

    nom = f.stem.replace("predictions_", "")
    ecrire_rapport(
        pd.DataFrame([{"gain_ponctuel_pct": gain, "ic95_bas": bas, "ic95_haut": haut,
                       "part_tirages_positifs": part_pos, "n_lignes": len(d),
                       "n_blocs_mois": len(blocs), "n_clusters": len(cl),
                       "tirages": tirages, "rmse_reference": r_ref,
                       "rmse_candidat": r_cand}]),
        RACINE / f"reports/bootstrap_{nom}.csv",
        contexte={"axe": "temporel"},
        attendues=["gain_ponctuel_pct", "ic95_bas", "ic95_haut"])
    print(f"Écrit : reports/bootstrap_{nom}.csv · {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--predictions", required=True)
    a.add_argument("--tirages", type=int, default=2000)
    a.add_argument("--clusters-stations", type=int, default=20)
    a.add_argument("--bloc-mois", type=int, default=1)
    n = a.parse_args()
    raise SystemExit(main(n.predictions, n.tirages, n.clusters_stations, n.bloc_mois))
