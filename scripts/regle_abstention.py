#!/usr/bin/env python3
"""La règle d'abstention : rendre le forçage brut plutôt qu'une correction douteuse.

D'où vient la règle
-------------------
Le 26/07/2026, jour d'alerte PM en Occitanie, CAMS prévoyait **49,6 µg/m³** pour **46,8**
observés — une excellente prévision. La correction l'a abaissée à **36,6**, soit une
dégradation de 12,9 µg/m³ un jour où il fallait alerter. Le même phénomène se lit en
statistique : le gain vaut +14,0 % quand CAMS est bon contre +23,6 % quand il dérive.

D'où la règle candidate, formulée par le cas et non après coup :

> **Ne pas corriger à la baisse quand le forçage annonce déjà un dépassement.**

Ce script la **teste** au lieu de l'affirmer. Une règle d'abstention se juge sur ce qu'elle
coûte autant que sur ce qu'elle sauve : renoncer à corriger, c'est renoncer aussi aux
corrections **utiles** que la règle intercepte.

Quatre variantes, de la plus étroite à la plus large :

| Variante | Renonce à corriger quand |
|---|---|
| `depassement` | CAMS ≥ seuil **et** la correction abaisse |
| `depassement_marge` | CAMS ≥ 80 % du seuil **et** la correction abaisse |
| `baisse_forte` | la correction abaisse de plus de 20 % la valeur de CAMS |
| `cams_haut` | CAMS est dans son décile supérieur **et** la correction abaisse |

Chaque variante est mesurée sur : RMSE global, RMSE du décile supérieur, POD, FAR, CSI, et
la **part des jours où l'on s'abstient** — car une règle qui s'abstient partout ne fait que
rendre le forçage brut.

Aucun ajustement : le script relit les prédictions existantes.

Usage : python3 scripts/regle_abstention.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from scores_episodes import scores  # noqa: E402

SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0}


def variantes(d: pd.DataFrame, seuil: float) -> dict[str, np.ndarray]:
    """Masques d'abstention. `True` = on rend le brut, on ne corrige pas."""
    abaisse = d["corrige"] < d["cams"]
    haut = d["cams"] >= d["cams"].quantile(0.90)
    return {
        "depassement": (d["cams"] >= seuil) & abaisse,
        "depassement_marge": (d["cams"] >= 0.8 * seuil) & abaisse,
        "baisse_forte": (d["corrige"] < 0.8 * d["cams"]) & abaisse,
        "cams_haut": haut & abaisse,
    }


def evaluer(observe, predit, seuil, seuil_haut) -> dict:
    m = cmp.metriques(observe, predit)
    haut = observe >= seuil_haut
    m_haut = cmp.metriques(observe[haut], predit[haut])
    depasse = (observe >= seuil).to_numpy()
    s = scores(depasse, (predit >= seuil).to_numpy()) if depasse.sum() >= 30 else {}
    return {"rmse": m["rmse"], "rmse_haut": m_haut["rmse"],
            "POD": s.get("POD", np.nan), "FAR": s.get("FAR", np.nan),
            "CSI": s.get("CSI", np.nan)}


def main(polluant: str, horizon: int) -> int:
    chemin = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    d = pd.read_csv(chemin, parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])
    seuil = SEUILS[polluant]
    seuil_haut = d["observe"].quantile(0.90)

    print(f"{polluant} J+{horizon} · {len(d):,} couples · seuil {seuil:.0f} µg/m³ · "
          f"décile supérieur au-delà de {seuil_haut:.1f}\n", flush=True)

    reference = {
        "CAMS brut (abstention totale)": evaluer(d["observe"], d["cams"], seuil, seuil_haut),
        "corrigé (jamais d'abstention)": evaluer(d["observe"], d["corrige"], seuil, seuil_haut),
    }

    print(f"{'règle':32s} {'abst.':>6s} {'RMSE':>7s} {'queue':>7s} {'POD':>6s} "
          f"{'FAR':>6s} {'CSI':>6s}")
    lignes = []
    for nom, m in reference.items():
        print(f"{nom:32s} {'—':>6s} {m['rmse']:7.2f} {m['rmse_haut']:7.2f} "
              f"{m['POD']:6.3f} {m['FAR']:6.3f} {m['CSI']:6.3f}")
        lignes.append({"regle": nom, "part_abstention_pct": np.nan, **m})

    for nom, masque in variantes(d, seuil).items():
        # On rend le brut là où la règle s'applique, la correction ailleurs.
        predit = d["corrige"].where(~masque, d["cams"])
        m = evaluer(d["observe"], predit, seuil, seuil_haut)
        part = 100 * float(masque.mean())
        print(f"{'abstention · ' + nom:32s} {part:5.2f}% {m['rmse']:7.2f} "
              f"{m['rmse_haut']:7.2f} {m['POD']:6.3f} {m['FAR']:6.3f} {m['CSI']:6.3f}",
              flush=True)
        lignes.append({"regle": nom, "part_abstention_pct": part, **m})

    table = pd.DataFrame(lignes)
    sortie = RACINE / f"reports/regle_abstention_{polluant}.csv"
    table.to_csv(sortie, index=False)

    # ── Ce que la règle coûte : les corrections utiles qu'elle intercepte ──────
    print("\nCe que l'abstention intercepte — utile de savoir ce qu'on perd :")
    for nom, masque in variantes(d, seuil).items():
        if masque.sum() == 0:
            print(f"  {nom:24s} ne s'applique jamais")
            continue
        sous = d[masque]
        err_cams = (sous["cams"] - sous["observe"]).abs()
        err_mos = (sous["corrige"] - sous["observe"]).abs()
        utiles = 100 * float((err_mos < err_cams).mean())
        print(f"  {nom:24s} {int(masque.sum()):>7,} cas · la correction y était "
              f"**meilleure** dans {utiles:.1f} % d'entre eux", flush=True)

    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    print("Une règle utile abaisse le RMSE de queue et relève le POD **sans** dégrader le "
          "RMSE global\nde plus de 0,3 µg/m³ — le critère d'arrêt du projet.", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
