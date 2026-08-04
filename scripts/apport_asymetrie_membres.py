#!/usr/bin/env python3
"""Les dérivées de l'ensemble sont calculées, stockées — et jamais données au modèle.

Le constat
------------
`extraire_membres.py` écrit sept colonnes dérivées à chaque requête depuis le 30/07 :
`membres_median`, `membres_ecart`, `membres_min`, `membres_max`, `membres_n`,
`membres_etendue`, `membres_asymetrie`.

Le modèle n'en reçoit **aucune**. `production_reelle.py` et `maximum_deployable.py` joignent
les six membres bruts, puis recalculent *leur propre* étendue et moyenne. Les cinq autres
dorment sur le disque depuis le premier téléchargement.

Pourquoi cela pourrait servir malgré la redondance apparente
--------------------------------------------------------------
Un arbre de décision partitionne sur **une variable à la fois**. Donner les six membres ne
lui permet pas de former `max − médiane` ni `(max − médiane) − (médiane − min)` : il faudrait
des dizaines de coupes pour approcher ce que ces expressions disent en un nombre.

`membres_asymetrie` est la plus intéressante : elle distingue un désaccord **orienté** —
tous les modèles serrés sauf un qui prévoit haut, signature d'un épisode incertain — d'un
désaccord **symétrique**, qui n'est que du bruit d'ensemble. La dispersion seule confond les
deux, et le projet a déjà mesuré que la dispersion brute est **nulle comme prédicteur**
tout en stratifiant l'erreur d'un facteur 6,6.

Le juge, et pourquoi pas la RMSE
----------------------------------
Le **plancher d'information** `σy·√(1−r²)`. Une variante qui gagne en RMSE sans baisser le
plancher n'a rien appris : elle a bougé un paramètre libre, et ce paramètre est déjà réglé.

⚠️ Contrôle indispensable : la base de comparaison contient **déjà les six membres bruts**
plus l'étendue et la moyenne. Mesurer contre une base plus pauvre surestimerait l'apport
d'un facteur 2 à 4 — c'est ce qui s'est produit le 04/08 sur trois autres pistes.

Usage  : python3 scripts/apport_asymetrie_membres.py --polluant O3
Sortie : reports/apport_asymetrie_membres_<polluant>_h<n>.csv
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

from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from tableau_comparatif import NOM_POLLUANT  # noqa: E402

MEMBRES = ("chimere", "emep", "mocage", "silam", "lotos", "match")
DERIVEES = ["membres_ecart", "membres_min", "membres_max", "membres_n",
            "membres_asymetrie"]


def rmse(o, x) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def plancher(o, x) -> tuple[float, float]:
    r = float(np.corrcoef(o, x)[0, 1])
    return r, float(o.std()) * np.sqrt(max(1 - r ** 2, 0.0))


def main(polluant: str, horizon: int, n_spa: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, cols, grandeur)
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")

    fs = sorted(glob.glob(str(RACINE / "data/processed/meteo/"
                              f"membres_metropole_{polluant.lower()}_*.parquet")))
    if not fs:
        raise SystemExit(f"aucun membre pour {polluant}")
    m = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    pres = [x for x in MEMBRES if x in m.columns and m[x].notna().any()]
    deriv = [x for x in DERIVEES if x in m.columns]
    if not deriv:
        raise SystemExit(f"aucune dérivée trouvée parmi {DERIVEES}")
    m["jour"] = pd.to_datetime(m["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    agr = "max" if grandeur in ("max_8h", "max_horaire") else "mean"
    jm = m.groupby(["station_id", "jour"])[pres + deriv].agg(agr).reset_index()
    avant = len(d)
    d = d.merge(jm, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure membres : {avant:,} → {len(d):,}")
    d["memb_etendue"] = d[pres].max(axis=1) - d[pres].min(axis=1)
    d["memb_moyenne"] = d[pres].mean(axis=1)

    # ⚠️ La base contient DÉJÀ tout ce que le modèle possède aujourd'hui.
    socle = base + list(cols_typo) + pres + ["memb_etendue", "memb_moyenne"]
    modes = {
        "① base actuelle (6 membres + étendue + moyenne)": socle,
        "② + asymétrie seule": socle + ["membres_asymetrie"],
        "③ + les cinq dérivées stockées": socle + deriv,
    }
    ech = "J0" if horizon == 1 else f"J+{horizon - 1}"
    print(f"{NOM_POLLUANT[polluant]} · {ech} · {len(d):,} jours-station · "
          f"{len(ids)} stations · dérivées disponibles : {', '.join(deriv)}", flush=True)
    print(f"  couverture des dérivées : "
          f"{100 * d['membres_asymetrie'].notna().mean():.0f} % des lignes", flush=True)

    rng = np.random.default_rng(GRAINE)
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
        if (i + 1) % 9 == 0:
            print(f"  {i + 1}/{len(mois)} mois · {(time.time() - depart) / 60:.1f} min",
                  flush=True)

    ok = np.ones(len(d), bool)
    for nom, v in pred.items():
        if not np.isfinite(v).any():
            raise SystemExit(f"le mode « {nom} » n'a rien produit")
        ok &= np.isfinite(v)
    o = d["valeur"].to_numpy()[ok]

    print(f"\n{'═' * 88}\nAPPORT DES DÉRIVÉES D'ENSEMBLE · {ok.sum():,} prédictions · "
          f"station ET mois cachés\n{'═' * 88}")
    print(f"  {'configuration':46s} {'r':>7s} {'RMSE':>8s} {'plancher':>9s} {'Δ':>8s}")
    lignes, ref = [], None
    for nom in modes:
        x = pred[nom][ok]
        r, pl = plancher(o, x)
        if ref is None:
            ref = pl
        print(f"  {nom:46s} {r:7.4f} {rmse(o, x):8.3f} {pl:9.4f} "
              f"{100 * (1 - pl / ref):+7.2f}%")
        lignes.append({"polluant": polluant, "horizon": horizon, "configuration": nom,
                       "r": r, "rmse": rmse(o, x), "plancher": pl,
                       "delta_plancher_pct": 100 * (1 - pl / ref), "n": int(ok.sum())})

    t = pd.DataFrame(lignes)
    best = float(t["delta_plancher_pct"].max())
    print(f"\n  Base de comparaison : les six membres bruts, leur étendue et leur moyenne")
    print(f"  sont DÉJÀ dedans. Ce qui se mesure ici est l'apport **marginal** des")
    print(f"  dérivées que le modèle ne sait pas former lui-même.")
    if best < 0.3:
        print(f"\n  → Apport nul ({best:+.2f} %). Les six membres suffisent : l'arbre")
        print(f"    reconstitue ce dont il a besoin. Ne pas les joindre.")
    else:
        print(f"\n  → Apport de {best:+.2f} %. À confirmer sur un second polluant avant")
        print(f"    d'être retenu — choisi ici, il serait sélectionné sur son test.")

    sortie = RACINE / f"reports/apport_asymetrie_membres_{polluant}_h{horizon}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
