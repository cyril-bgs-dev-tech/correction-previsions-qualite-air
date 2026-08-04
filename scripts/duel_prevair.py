#!/usr/bin/env python3
"""PREV'AIR contre notre correction, sur les mêmes stations et les mêmes jours.

⚠️ CE QUE CE SCRIPT NE PEUT PAS FAIRE
=======================================
**Quatre jours ne concluent rien.** La fenêtre publique de PREV'AIR ne conserve qu'une
semaine ; l'intersection avec nos observations et nos prévisions CAMS tombe à quelques
journées. Un écart mesuré là-dessus n'a aucune valeur statistique, et le script le répète
à chaque sortie.

Ce qu'il fait, c'est **poser la comparaison** et la faire tourner. Le jour où l'archive
historique arrive — demandée à l'INERIS puis à Atmo Occitanie le 03/08 — il suffit de la
relancer.

La comparaison est-elle seulement équitable ?
-----------------------------------------------
Non, et dans les deux sens. Il faut le dire avant les chiffres.

**En notre défaveur :**
* PREV'AIR tourne à **≈ 1,7 km** ; nous corrigeons un ensemble européen à **10 km** ;
* PREV'AIR **assimile** les observations et applique déjà un **krigeage** ;
* PREV'AIR fait tourner CHIMERE **et** MOCAGE en configuration **nationale**, avec
  l'inventaire d'émissions français.

**En notre faveur :**
* notre modèle a **appris sur ces stations** (il est entraîné sur 2023-2024, testé ici en
  2026 — extrapolation temporelle, mais stations connues) ;
* PREV'AIR est jugé sur un produit livré au public, nous sur un calcul de laboratoire.

Autrement dit : c'est une comparaison de **chaînes d'ampleur différente**, pas de méthodes.
Le seul énoncé défendable est un ordre de grandeur.

Le grain, vérifié et non déduit
---------------------------------
PREV'AIR publie **deux** familles : `MAXJ*` (maximum journalier) et `MOYJ*` (moyenne
journalière). Le 03/08, le test des quatre appariements possibles a donné :

    MAXJ1 contre maximum     RMSE 35,95   corr 0,117
    MAXJ1 contre moyenne     RMSE 17,57   corr 0,192
    MOYJ1 contre moyenne     RMSE  7,51   corr 0,405   ← sans comparaison

Chaque polluant est donc comparé au produit de **son grain réglementaire** : `MOYJ` pour les
particules — seuil de 50 µg/m³ en moyenne journalière — et `MAXJ` pour O₃ et NO₂.

Usage : python3 scripts/duel_prevair.py --polluant PM10
Sortie : reports/duel_prevair_<polluant>.csv
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

from comparer_prevair import AGREGAT, PRODUIT, extraire  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)

# L'apprentissage s'arrête bien avant les jours testés : aucune fuite possible.
FIN_APPRENTISSAGE = "2024-12"


def scores(o, x) -> dict:
    e = x - o
    return {"n": len(o), "biais": float(e.mean()),
            "rmse": float(np.sqrt((e ** 2).mean())),
            "mae": float(np.abs(e).mean()),
            "correlation": float(np.corrcoef(o, x)[0, 1]) if o.std() and x.std() else np.nan}


def main(polluant: str, horizon: int) -> int:
    depart = time.time()
    agr, prod = AGREGAT[polluant], PRODUIT[polluant]
    ech = f"{prod}{horizon - 1}"

    # ── ① PREV'AIR aux stations ──────────────────────────────────────────────
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "lat_wgs84", "lon_wgs84"]
                         ).dropna().drop_duplicates("station_id").reset_index(drop=True)
    fichiers = [Path(f) for f in glob.glob(str(RACINE / "data/raw/prevair/*.nc"))
                if f".{ech}.{polluant}." in f.upper() and "PREVISION" in f.upper()]
    if not fichiers:
        raise SystemExit(f"aucun fichier {ech}.{polluant} — lancer archiver_prevair.py")
    pv = pd.concat([extraire(f, st) for f in fichiers], ignore_index=True)
    print(f"{polluant} · {ech} · {len(fichiers)} jours PREV'AIR · "
          f"{len(pv):,} valeurs extraites", flush=True)

    # ── ② Notre correction, entraînée AVANT les jours testés ─────────────────
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, cols, GRANDEUR_PAR_POLLUANT[polluant])
    pred_cols = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    pred_cols += cols_typo

    jours_pv = set(pv["jour"].unique())
    appr = d[d["mois"] <= FIN_APPRENTISSAGE]
    test = d[d["jour"].isin(jours_pv)]
    if test.empty:
        raise SystemExit(f"aucun jour commun entre PREV'AIR ({sorted(jours_pv)[:3]}…) "
                         f"et nos prévisions CAMS — étendre l'extraction CAMS")
    print(f"  apprentissage : {len(appr):,} jours-station jusqu'à {FIN_APPRENTISSAGE}\n"
          f"  test          : {len(test):,} jours-station sur "
          f"{test['jour'].nunique()} jour(s) communs", flush=True)
    p = ajuster(DEFAUT, appr, test, pred_cols, "cams_jour")
    nous = test[["station_id", "jour", "valeur", "cams_jour"]].copy()
    nous["nous"] = p

    # ── ③ Les trois systèmes sur EXACTEMENT les mêmes lignes ─────────────────
    m = nous.merge(pv[["station_id", "jour", "prevair"]], on=["station_id", "jour"],
                   how="inner").dropna()
    if len(m) < 100:
        print(f"  ⚠️ {len(m)} lignes communes — trop peu même pour un ordre de grandeur.")
        return 1
    o = m["valeur"].to_numpy()
    print(f"\n{'═' * 76}\n{polluant} · {len(m):,} lignes communes · "
          f"{m['jour'].nunique()} jour(s) · {m['station_id'].nunique()} stations\n"
          f"⚠️ {m['jour'].nunique()} jour(s) NE CONCLUENT RIEN — ordre de grandeur seul\n"
          f"{'═' * 76}")
    print(f"  {'système':34s} {'biais':>8s} {'RMSE':>8s} {'MAE':>8s} {'corr':>7s}")
    lignes = []
    for nom, col in (("CAMS Europe brut (10 km)", "cams_jour"),
                     ("notre correction de CAMS", "nous"),
                     ("PREV'AIR (1,7 km, assimilé, krigé)", "prevair")):
        s = scores(o, m[col].to_numpy())
        print(f"  {nom:34s} {s['biais']:+8.2f} {s['rmse']:8.2f} {s['mae']:8.2f} "
              f"{s['correlation']:7.3f}")
        lignes.append({"polluant": polluant, "echeance": ech, "systeme": nom, **s})

    r_nous = scores(o, m["nous"].to_numpy())["rmse"]
    r_pv = scores(o, m["prevair"].to_numpy())["rmse"]
    ecart = 100 * (r_pv / r_nous - 1)
    print(f"\n  Écart PREV'AIR contre nous : {ecart:+.1f} % de RMSE "
          f"({'à notre avantage' if ecart > 0 else 'à leur avantage'})")
    print(f"\n  ⚠️ Rappel : ils tournent à 1,7 km avec assimilation et krigeage ; nous")
    print(f"     corrigeons un ensemble européen à 10 km. Nos stations sont connues de")
    print(f"     notre modèle, les leurs le sont aussi de leur krigeage. Ordre de")
    print(f"     grandeur, sur {m['jour'].nunique()} jour(s).")

    sortie = RACINE / f"reports/duel_prevair_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--horizon", type=int, default=2, help="2 = J+1")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon))
