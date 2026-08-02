#!/usr/bin/env python3
"""Nos intervalles de confiance sont-ils trop étroits ? Quatre schémas de rééchantillonnage.

Le reproche
-----------
Le projet bootstrape **par station**, ce qui corrige la pseudo-réplication spatiale : sans
cela, 3,2 M de lignes issues de 270 stations feraient croire à 3,2 M d'observations
indépendantes. C'était déjà un progrès — mesuré sur ce projet, l'écart de largeur atteignait
un facteur 23 par rapport au tirage par ligne.

Mais une relecture du 30/07 (`docs/GROK_R5.md` Q19) pointe ce qui reste : **les erreurs sont
aussi corrélées dans le temps**. Deux jours consécutifs partagent le même régime météo, la
même masse d'air, le même état du modèle amont. Tirer des stations entières n'y change rien,
puisque chaque station tirée apporte toute sa série temporelle. Nos IC restent donc trop
étroits, et de combien n'est pas connu.

Quatre schémas, du plus naïf au plus honnête :

1. **par ligne** — ignore tout, sert de témoin pour mesurer l'ampleur du problème ;
2. **par station** — ce que le projet fait aujourd'hui ;
3. **par bloc temporel** (mois calendaires entiers) — traite le temps, ignore l'espace ;
4. **par station et par bloc** — tire les deux, le seul défendable ici.

Le quatrième est un bootstrap sur les **cellules** station × mois : on tire des stations avec
remise *et* des mois avec remise, puis on garde l'intersection. C'est approximatif — un vrai
bootstrap doublement indexé n'existe pas sans hypothèses — mais il majore honnêtement
l'incertitude au lieu de la sous-estimer.

Aucun ajustement : le script lit `reports/mos_{polluant}_J{horizon}.csv`.

Usage : python3 scripts/intervalles_bloques.py [--polluant O3] [--tirages 400]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

GRAINE = 20260730


def _gain(observe: np.ndarray, cams: np.ndarray, corrige: np.ndarray) -> float:
    """Gain relatif de RMSE, en pourcentage."""
    rc = np.sqrt(np.mean((cams - observe) ** 2))
    rm = np.sqrt(np.mean((corrige - observe) ** 2))
    return 100.0 * (1.0 - rm / rc) if rc > 0 else np.nan


def bootstrap(d: pd.DataFrame, schema: str, n_tirages: int) -> dict:
    """Distribution du gain sous un schéma de rééchantillonnage donné."""
    rng = np.random.default_rng(GRAINE)
    obs = d["observe"].to_numpy()
    cams = d["cams"].to_numpy()
    corr = d["corrige"].to_numpy()

    # Index par unité, calculé une fois : refaire un `groupby` à chaque tirage dominerait
    # le coût total (400 tirages × un balayage de 3 M de lignes).
    if schema != "ligne":
        par_station = {s: i for s, i in d.groupby("station_id").indices.items()}
        par_mois = {m: i for m, i in d.groupby("mois").indices.items()}
        stations = np.array(list(par_station))
        mois = np.array(list(par_mois))

    tirages = []
    for _ in range(n_tirages):
        if schema == "ligne":
            idx = rng.integers(0, len(d), len(d))
        elif schema == "station":
            choisies = rng.choice(stations, size=stations.size, replace=True)
            idx = np.concatenate([par_station[s] for s in choisies])
        elif schema == "bloc_temporel":
            choisis = rng.choice(mois, size=mois.size, replace=True)
            idx = np.concatenate([par_mois[m] for m in choisis])
        else:  # station et bloc
            choisies = set(rng.choice(stations, size=stations.size, replace=True))
            choisis = set(rng.choice(mois, size=mois.size, replace=True))
            masque = d["station_id"].isin(choisies) & d["mois"].isin(choisis)
            idx = np.flatnonzero(masque.to_numpy())
            if idx.size == 0:
                continue
        tirages.append(_gain(obs[idx], cams[idx], corr[idx]))

    t = np.array(tirages)
    basse, haute = np.quantile(t, [0.025, 0.975])
    return {"schema": schema, "gain": _gain(obs, cams, corr),
            "borne_basse": basse, "borne_haute": haute,
            "largeur": haute - basse, "part_positifs": float((t > 0).mean()),
            "n_tirages": len(t)}


def main(polluant: str, horizon: int, n_tirages: int) -> int:
    chemin = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    if not chemin.exists():
        print(f"ÉCHEC : {chemin.name} absent", file=sys.stderr)
        return 1

    d = pd.read_csv(chemin, parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])
    d["mois"] = d["timestamp_utc"].dt.strftime("%Y-%m")
    print(f"{polluant} J+{horizon} · {len(d):,} couples · "
          f"{d['station_id'].nunique()} stations · {d['mois'].nunique()} mois · "
          f"{n_tirages} tirages\n", flush=True)

    lignes = []
    print(f"{'schéma de tirage':24s} {'gain':>7s} {'IC 95 %':>20s} {'largeur':>9s} "
          f"{'× vs ligne':>11s}")
    reference = None
    for schema in ("ligne", "station", "bloc_temporel", "station_et_bloc"):
        r = bootstrap(d, schema, n_tirages)
        reference = reference or r["largeur"]
        facteur = r["largeur"] / reference if reference else np.nan
        print(f"{schema:24s} {r['gain']:+6.2f} % "
              f"[{r['borne_basse']:+6.2f} ; {r['borne_haute']:+6.2f}] "
              f"{r['largeur']:8.2f} {facteur:10.1f}×", flush=True)
        lignes.append(r)

    table = pd.DataFrame(lignes)
    sortie = RACINE / f"reports/intervalles_bloques_{polluant}_J{horizon}.csv"
    table.to_csv(sortie, index=False)

    naif = table.loc[table["schema"] == "ligne", "largeur"].iloc[0]
    actuel = table.loc[table["schema"] == "station", "largeur"].iloc[0]
    honnete = table.loc[table["schema"] == "station_et_bloc", "largeur"].iloc[0]
    print(f"\nLe tirage par station élargit déjà l'IC de **{actuel / naif:.1f}×** face au "
          f"tirage par ligne.")
    print(f"Ajouter le blocage temporel l'élargit encore de **{honnete / actuel:.1f}×** : "
          f"c'est la part\nd'incertitude que le projet sous-estimait.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--tirages", type=int, default=400)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.tirages))
