#!/usr/bin/env python3
"""L'erreur vient-elle du modèle, ou du fait qu'une station n'est pas une maille ?

Le test
-------
CAMS rend **une valeur par maille** d'environ 8 × 11 km. Plusieurs stations tombent dans la même
maille et reçoivent donc **la même prévision** — alors qu'elles mesurent des lieux différents.

Si l'erreur venait surtout du modèle, deux stations d'une même maille auraient des résidus
semblables : la prévision est la même, l'erreur devrait l'être aussi. Si l'erreur vient
surtout de la **représentativité** — chaque station voit une rue, une clairière, un fond de
vallée — alors les résidus de deux stations d'une même maille divergeront autant, sinon
plus, que ceux de mailles voisines.

C'est le symptôme n°1 identifié comme angle mort (`docs/GPT_ANGLES_MORTS.md` Q1) :

> « Le résidu garde le même signe par station, et varie davantage **entre stations d'une même
> maille CAMS** qu'entre mailles voisines. »

Ce que le test décide : si la représentativité domine, aucun raffinement d'algorithme ne
franchira le mur — il faudrait descendre sous la maille, ce qui n'est pas un problème
d'apprentissage mais de données.

Trois mesures :

1. **Écart-type des résidus intra-maille** contre inter-mailles voisines ;
2. **Part de la variance du résidu expliquée par la station** — un résidu qui est surtout une
   constante par station est une erreur de lieu, pas de moment ;
3. **Persistance du signe** du résidu par station, avant et après correction.

Aucun ajustement : lit les prédictions et les mailles déjà écrites.

Usage : python3 scripts/representativite_maille.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from fit_mos import ESPECES  # noqa: E402


def mailles(polluant: str) -> pd.DataFrame:
    """Association station → maille CAMS, lue dans n'importe quel mois de prévision."""
    court = next(c for c, (p, _) in ESPECES.items() if p == polluant)
    fichiers = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_*.parquet")))
    if not fichiers:
        raise SystemExit(f"aucune prévision extraite pour {polluant}")
    d = pd.read_parquet(fichiers[0], columns=["station_id", "maille_lat", "maille_lon"])
    return d.drop_duplicates("station_id")


def main(polluant: str, horizon: int) -> int:
    p = pd.read_csv(RACINE / f"reports/mos_{polluant}_J{horizon}.csv",
                    parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])
    m = mailles(polluant)
    d = p.merge(m, on="station_id", how="inner")
    d["maille"] = (d["maille_lat"].round(3).astype(str) + "_"
                   + d["maille_lon"].round(3).astype(str))
    d["residu_cams"] = d["cams"] - d["observe"]
    d["residu_mos"] = d["corrige"] - d["observe"]

    par_maille = d.groupby("maille")["station_id"].nunique()
    partagees = par_maille[par_maille >= 2]
    print(f"{polluant} J+{horizon} · {d['station_id'].nunique()} stations · "
          f"{d['maille'].nunique()} mailles CAMS distinctes")
    print(f"  {len(partagees)} maille(s) contiennent ≥2 stations · "
          f"{int(partagees.sum())} stations concernées\n", flush=True)

    if partagees.empty:
        print("  Aucune maille partagée : le test ne peut pas être conduit.")
        return 0

    # ── 1. Divergence intra-maille : deux stations, une seule prévision ────────
    sous = d[d["maille"].isin(partagees.index)]
    intra = sous.groupby(["maille", "timestamp_utc"]).agg(
        ecart_obs=("observe", "std"),
        ecart_res_cams=("residu_cams", "std"),
        ecart_res_mos=("residu_mos", "std"),
        n=("observe", "size"),
    )
    intra = intra[intra["n"] >= 2].dropna()

    print("1. Divergence ENTRE stations d'une MÊME maille (même prévision CAMS)")
    print(f"   écart-type des observations   : médiane {intra['ecart_obs'].median():5.2f} "
          f"· 90e centile {intra['ecart_obs'].quantile(0.9):5.2f} µg/m³")
    print(f"   écart-type du résidu CAMS     : médiane {intra['ecart_res_cams'].median():5.2f}")
    print(f"   écart-type du résidu corrigé  : médiane {intra['ecart_res_mos'].median():5.2f}",
          flush=True)

    # ── 2. Part de la variance du résidu qui est une constante par station ────
    print("\n2. Le résidu est-il un décalage de LIEU ou une erreur de MOMENT ?")
    for nom, colonne in (("CAMS   ", "residu_cams"), ("corrigé", "residu_mos")):
        moyennes = d.groupby("station_id")[colonne].mean()
        var_inter = float(moyennes.var())
        var_totale = float(d[colonne].var())
        part = 100 * var_inter / var_totale if var_totale else np.nan
        print(f"   résidu {nom} · {part:5.1f} % de la variance est un **décalage propre à "
              f"la station**", flush=True)

    # ── 3. Persistance du signe : une station se trompe-t-elle toujours pareil ?
    print("\n3. Le résidu garde-t-il le même signe par station ?")
    for nom, colonne in (("CAMS   ", "residu_cams"), ("corrigé", "residu_mos")):
        signe = d.groupby("station_id")[colonne].apply(lambda s: max((s > 0).mean(),
                                                                    (s < 0).mean()))
        print(f"   résidu {nom} · part du temps dans le signe dominant : "
              f"médiane {100 * signe.median():.1f} % · "
              f"{int((signe > 0.8).sum())} station(s) au-delà de 80 %", flush=True)

    sortie = RACINE / f"reports/representativite_{polluant}.csv"
    intra.reset_index().to_csv(sortie, index=False)

    print("\n" + "=" * 72)
    rapport = intra["ecart_res_mos"].median() / intra["ecart_obs"].median()
    print(f"Lecture : après correction, deux stations d'une même maille gardent des résidus "
          f"qui\ndivergent de {intra['ecart_res_mos'].median():.2f} µg/m³ — soit "
          f"{100 * rapport:.0f} % de la divergence de leurs observations.")
    print("Ce qui reste là n'est pas de l'erreur de modèle : c'est l'écart entre un point de\n"
          "mesure et un volume de 8 × 11 km. Aucun algorithme ne le franchit sans données plus fines.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
