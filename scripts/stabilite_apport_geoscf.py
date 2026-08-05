#!/usr/bin/env python3
"""L'apport de GEOS-CF est-il **stable**, ou tient-il à une partition heureuse ?

Pourquoi ce test, et pourquoi la barre connue ne suffit pas
------------------------------------------------------------
`repetabilite.py` a mesuré la dispersion graine-à-graine du projet : **±2,02 points sur
l'ozone**, dominés par la partition (σ 1,368) et non par l'ajustement (σ 0,399). La consigne
qui en découle — *diviser tout écart par 2 points, et ne rien conclure en dessous de 2×* —
condamnerait les apports mesurés ici, qui valent +1,4 à +2,9 %.

Sauf que **cette barre porte sur un score absolu**, et que la mesure d'apport est
**appariée** : les configurations ① et ② partagent la même partition, les mêmes plis, les
mêmes lignes, et ne diffèrent que par cinq colonnes. Le déplacement commun que la partition
inflige aux deux scores **se soustrait** dans leur écart. Appliquer une barre non appariée à
une différence appariée, c'est refuser un résultat sur un bruit qui n'entre pas dedans.

Ce script mesure donc la seule chose qui décide : **la dispersion du gain lui-même**, d'une
partition à l'autre. Ce n'est pas la barre des autres mesures ; c'est celle de celle-ci.

Ce qui varie, et ce qui ne varie pas
--------------------------------------
Seule la **partition spatiale** change d'une graine à l'autre — c'est l'aléa qui domine d'un
facteur 3,4. L'aléa d'ajustement reste figé : le faire varier en même temps mélangerait deux
sources et ne dirait plus laquelle porte l'instabilité.

Le verdict se lit sur trois chiffres, pas un
----------------------------------------------
* la **médiane** du gain — sa valeur centrale ;
* l'**étendue** min–max — ce que la partition peut lui faire de pire ;
* le **nombre de graines de signe positif** — un gain qui change de signe n'est pas un gain,
  quelle que soit sa moyenne.

⚠️ Extrapoler depuis la **pire** graine, jamais la meilleure ni la première : c'est la
règle 1 ter du projet, transposée de la mesure de débit à la mesure de gain.

Usage  : python3 scripts/stabilite_apport_geoscf.py --polluant O3 --version v1 --graines 4
Sortie : reports/stabilite_geoscf_<polluant>_<version>.csv
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

from apport_geoscf import plancher, preparer  # noqa: E402
from double_aveugle_journalier import DEFAUT, GRAINE, ajuster  # noqa: E402


def un_tirage(d: pd.DataFrame, sans: list[str], avec: list[str], graine: int,
              n_spa: int) -> dict:
    """Un protocole double aveugle complet, pour une partition donnée.

    Rend le plancher des deux configurations **et leur écart**, mesurés sur exactement les
    mêmes lignes : c'est l'appariement qui fait tout l'intérêt de la mesure.
    """
    modes = {"sans": sans, "avec": avec}
    rng = np.random.default_rng(graine)
    ids = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(ids), n_spa)
    mois = np.sort(d["mois"].unique())
    pred = {k: np.full(len(d), np.nan) for k in modes}
    for i, mm in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        mt, mr = (d["mois"] == mm) & dans, (d["mois"] != mm) & ~dans
        te, tr = d[mt], d[mr]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(mt.to_numpy())
        for nom, colonnes in modes.items():
            pred[nom][idx] = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")

    ok = np.ones(len(d), bool)
    for nom, v in pred.items():
        if not np.isfinite(v).any():
            raise SystemExit(f"graine {graine} : le mode « {nom} » n'a rien produit")
        ok &= np.isfinite(v)
    o = d["valeur"].to_numpy()[ok]
    _, pl_sans = plancher(o, pred["sans"][ok])
    _, pl_avec = plancher(o, pred["avec"][ok])
    return {"graine": graine, "n": int(ok.sum()), "plancher_sans": pl_sans,
            "plancher_avec": pl_avec, "gain_pct": 100 * (1 - pl_avec / pl_sans)}


def main(polluant: str, horizon: int, version: str, n_graines: int, n_spa: int) -> int:
    depart = time.time()
    d, colonnes, _ = preparer(polluant, horizon, version)
    sans = colonnes["base"] + colonnes["familles"]
    cols_geo = colonnes["geo"]
    avec = sans + cols_geo
    if not cols_geo:
        raise SystemExit("aucune colonne GEOS-CF — rien à mesurer")

    # La première graine est celle du dossier : le balayage doit **contenir** le chiffre
    # publié, sinon on compare deux mesures qui ne se recouvrent pas.
    graines = [GRAINE] + [GRAINE + 1000 * k for k in range(1, n_graines)]
    print(f"\n{'═' * 84}")
    print(f"STABILITÉ DE L'APPORT — {polluant} · {version} · {len(graines)} partitions")
    print(f"{'═' * 84}")
    print(f"  {len(d):,} jours-station · {len(cols_geo)} colonnes GEOS-CF ajoutées "
          f"aux {len(sans)} de la base")
    print(f"\n  {'graine':>10s} {'n':>8s} {'plancher sans':>14s} {'plancher avec':>14s} "
          f"{'gain':>8s}")
    lignes = []
    for g in graines:
        r = un_tirage(d, sans, avec, g, n_spa)
        r.update(polluant=polluant, horizon=horizon, version_geoscf=version)
        lignes.append(r)
        print(f"  {g:>10d} {r['n']:>8,} {r['plancher_sans']:14.4f} "
              f"{r['plancher_avec']:14.4f} {r['gain_pct']:+7.2f}%", flush=True)

    # ⚠️ La table se construit APRÈS le dernier tirage (règle 2 ter) : un `DataFrame` bâti
    # avant fige une copie, et les mesures suivantes n'y entrent jamais.
    t = pd.DataFrame(lignes)
    for c in ("gain_pct", "graine", "n"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")
    gains = t["gain_pct"].to_numpy()
    positifs = int((gains > 0).sum())
    if len(gains) < 2:
        # ⚠️ Une graine ne fait pas une dispersion. `std(ddof=1)` rend `nan` en silence et
        # le verdict s'imprimerait quand même — exactement le « +nan% » de la règle 2 ter.
        print(f"\n  une seule partition : {gains[0]:+.2f} %. Aucune dispersion mesurable,")
        print(f"  aucun verdict — relancer avec --graines ≥ 3.")
        f = RACINE / f"reports/stabilite_geoscf_{polluant}_{version}.csv"
        t.to_csv(f, index=False)
        print(f"\nÉcrit : {f.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
        return 0
    print(f"\n  médiane {np.median(gains):+.2f} %  ·  étendue "
          f"{gains.min():+.2f} → {gains.max():+.2f}  ·  σ {gains.std(ddof=1):.2f} pt")
    print(f"  signe positif sur {positifs}/{len(gains)} partitions")
    # Le verdict se prononce sur la PIRE graine, pas sur la médiane.
    if positifs < len(gains):
        print(f"  → NON STABLE : le gain change de signe. Ne pas publier de valeur centrale.")
    elif gains.min() > 2 * gains.std(ddof=1):
        print(f"  → STABLE : même la pire partition rend {gains.min():+.2f} %, "
              f"soit {gains.min() / max(gains.std(ddof=1), 1e-9):.1f}× la dispersion.")
    else:
        print(f"  → FRAGILE : pire partition {gains.min():+.2f} % contre σ "
              f"{gains.std(ddof=1):.2f} pt. Positif partout, mais l'ampleur ne se publie pas.")

    f = RACINE / f"reports/stabilite_geoscf_{polluant}_{version}.csv"
    t.to_csv(f, index=False)
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--version", default="v1", choices=("mixte", "v1", "v2"))
    a.add_argument("--graines", type=int, default=4)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.version, n.graines, n.plis_spatiaux))
