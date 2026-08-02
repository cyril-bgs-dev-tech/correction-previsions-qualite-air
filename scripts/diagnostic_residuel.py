#!/usr/bin/env python3
"""Trois diagnostics sur les prédictions déjà écrites — sans réajuster quoi que ce soit.

Les trois questions posées par la relecture externe du 30/07, dans l'ordre où elles
menacent le dossier :

**1. Le gain vient-il du modèle ou d'une dégradation de CAMS ?** Deux ruptures
opérationnelles CAMS sont documentées (13/11/2024 et 03/12/2024, `docs/GPT_R3.md`), et
c'est exactement là que le RMSE de CAMS grimpe et que le gain explose : +30 à +34 % en
octobre-décembre 2024 contre +14 à +22 % un an plus tôt à saison égale. Si le surplus vient
d'un forçage devenu plus biaisé, ce qui tombe n'est pas la validation sur stations exclues
mais le récit « gain structurel durable ». La comparaison **à saison égale d'une année sur
l'autre** est la seule qui tranche.

**2. Où le gain se concentre-t-il ?** Décomposition **mois × décile de concentration**. Un
gain moyen élevé porté uniquement par le fond, alors que la queue se dégrade, ne rend aucun
service — c'est déjà établi globalement, il reste à voir si cela varie dans le temps.

**3. L'écrêtage à zéro biaise-t-il les faibles concentrations ?** Le module écrête les
prédictions négatives, sans que le coût n'ait jamais été mesuré. Sur des polluants dont la
distribution frôle zéro, tronquer par le bas déplace la moyenne vers le haut — précisément
dans la gamme qui sépare les classes « Bon » et « Moyen » de l'indice ATMO.

Aucun ajustement : le script lit `reports/mos_{polluant}_J{horizon}.csv`. Il peut donc
tourner pendant qu'un autre modèle s'entraîne.

Usage : python3 scripts/diagnostic_residuel.py [--polluant O3] [--horizon 1]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval import comparaison as cmp  # noqa: E402

# Ruptures opérationnelles CAMS documentées, avec la demi-fenêtre d'observation.
RUPTURES = ("2024-11-13", "2024-12-03")
DEMI_FENETRE_JOURS = 14


def _gain(sous: pd.DataFrame) -> dict:
    """RMSE de CAMS et du modèle sur un sous-ensemble, et le gain relatif."""
    if len(sous) < 500:
        return {"n": len(sous), "cams": np.nan, "mos": np.nan, "gain": np.nan}
    rc = cmp.metriques(sous["observe"], sous["cams"])["rmse"]
    rm = cmp.metriques(sous["observe"], sous["corrige"])["rmse"]
    return {"n": len(sous), "cams": rc, "mos": rm, "gain": 100 * (1 - rm / rc)}


def saison_egale(d: pd.DataFrame) -> pd.DataFrame:
    """Compare chaque mois calendaire d'une année à l'autre — le seul test qui tranche.

    Un gain élevé en novembre ne prouve rien seul : novembre est un mois où CAMS se trompe
    davantage. Comparer novembre 2024 à novembre 2023 neutralise la saison et laisse
    apparaître ce qui a changé **dans le forçage**.
    """
    lignes = []
    for mois_cal, groupe in d.groupby(d["timestamp_utc"].dt.month):
        par_an = {an: _gain(g) for an, g in groupe.groupby(groupe["timestamp_utc"].dt.year)}
        if len(par_an) < 2:
            continue
        annees = sorted(par_an)
        a, b = annees[0], annees[-1]
        lignes.append({
            "mois_calendaire": mois_cal,
            f"cams_{a}": par_an[a]["cams"], f"cams_{b}": par_an[b]["cams"],
            f"gain_{a}": par_an[a]["gain"], f"gain_{b}": par_an[b]["gain"],
            "delta_cams": par_an[b]["cams"] - par_an[a]["cams"],
            "delta_gain": par_an[b]["gain"] - par_an[a]["gain"],
        })
    return pd.DataFrame(lignes)


def autour_des_ruptures(d: pd.DataFrame) -> pd.DataFrame:
    """Avant/après chaque rupture, sur une fenêtre symétrique.

    La fenêtre est **symétrique et fixée d'avance** : la choisir après avoir vu le résultat
    reviendrait à fabriquer l'effet qu'on prétend mesurer.
    """
    lignes = []
    for date in RUPTURES:
        pivot = pd.Timestamp(date, tz="UTC")
        delta = pd.Timedelta(days=DEMI_FENETRE_JOURS)
        avant = d[(d["timestamp_utc"] >= pivot - delta) & (d["timestamp_utc"] < pivot)]
        apres = d[(d["timestamp_utc"] >= pivot) & (d["timestamp_utc"] < pivot + delta)]
        for nom, sous in (("avant", avant), ("après", apres)):
            lignes.append({"rupture": date, "periode": nom, **_gain(sous)})
    return pd.DataFrame(lignes)


def mois_par_decile(d: pd.DataFrame, seuil_haut: float) -> pd.DataFrame:
    """Gain par mois, séparé entre le gros de la distribution et le décile supérieur."""
    lignes = []
    for mois, groupe in d.groupby(d["timestamp_utc"].dt.strftime("%Y-%m")):
        haut = groupe[groupe["observe"] >= seuil_haut]
        bas = groupe[groupe["observe"] < seuil_haut]
        lignes.append({
            "mois": mois,
            "gain_bas": _gain(bas)["gain"], "n_bas": len(bas),
            "gain_haut": _gain(haut)["gain"], "n_haut": len(haut),
        })
    return pd.DataFrame(lignes)


def cout_ecretage(d: pd.DataFrame) -> dict:
    """Ce que l'écrêtage à zéro coûte, et ce qu'il évite.

    On ne peut pas « désécrêter » a posteriori : le fichier ne contient que la prédiction
    finale. On mesure donc ce qui est observable — la fraction écrêtée et le biais
    conditionnel dans le bas de la distribution, là où l'écrêtage opère.
    """
    ecrete = d["corrige"] <= 0.0
    bas = d[d["observe"] < d["observe"].quantile(0.10)]
    return {
        "part_ecretee_pct": 100 * float(ecrete.mean()),
        "n_ecretees": int(ecrete.sum()),
        "obs_moyenne_sur_ecretees": float(d.loc[ecrete, "observe"].mean()) if ecrete.any() else np.nan,
        "biais_decile_bas_cams": float((bas["cams"] - bas["observe"]).mean()),
        "biais_decile_bas_mos": float((bas["corrige"] - bas["observe"]).mean()),
        "seuil_decile_bas": float(d["observe"].quantile(0.10)),
    }


def main(polluant: str, horizon: int) -> int:
    chemin = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    if not chemin.exists():
        print(f"ÉCHEC : {chemin.name} absent", file=sys.stderr)
        return 1

    d = pd.read_csv(chemin, parse_dates=["timestamp_utc"])
    d = d.dropna(subset=["observe", "cams", "corrige"])
    seuil_haut = d["observe"].quantile(0.90)
    print(f"{polluant} J+{horizon} · {len(d):,} couples · "
          f"décile supérieur au-delà de {seuil_haut:.1f} µg/m³\n", flush=True)

    print("=== 1. À saison égale, d'une année sur l'autre ===")
    print("(delta_cams > 0 : CAMS s'est dégradé · delta_gain > 0 : le gain a monté)")
    tableau = saison_egale(d)
    print(tableau.to_string(index=False, float_format=lambda x: f"{x:7.2f}"), flush=True)
    if not tableau.empty and tableau["delta_cams"].notna().any():
        correlation = tableau[["delta_cams", "delta_gain"]].corr().iloc[0, 1]
        print(f"\ncorrélation entre dégradation de CAMS et hausse du gain : {correlation:+.3f}")
        print("→ proche de +1 : le gain suit la dégradation du forçage, non un progrès du "
              "modèle.", flush=True)

    print("\n=== 2. Autour des ruptures CAMS documentées ===")
    print(f"(fenêtre symétrique de ±{DEMI_FENETRE_JOURS} jours, fixée avant de regarder)")
    print(autour_des_ruptures(d).to_string(index=False,
                                          float_format=lambda x: f"{x:8.2f}"), flush=True)

    print("\n=== 3. Gain par mois : fond contre décile supérieur ===")
    print(mois_par_decile(d, seuil_haut).to_string(index=False,
                                                   float_format=lambda x: f"{x:7.1f}"),
          flush=True)

    print("\n=== 4. Coût de l'écrêtage à zéro ===")
    for cle, valeur in cout_ecretage(d).items():
        print(f"  {cle:28s} {valeur:9.3f}")

    sortie = RACINE / f"reports/diagnostic_residuel_{polluant}_J{horizon}.csv"
    saison_egale(d).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
