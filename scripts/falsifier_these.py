#!/usr/bin/env python3
"""La corrélation +0,913 est-elle réelle, ou un artefact de la métrique choisie ?

L'objection à trancher
----------------------
Le gain s'écrit `G = 1 − RMSE_corr / RMSE_CAMS`. Le dénominateur **est** la quantité dont on
mesure la dégradation : corréler l'un à l'autre expose à un **couplage mathématique**. Même
avec `RMSE_corr` rigoureusement constant, une hausse de `RMSE_CAMS` fait monter `G`
mécaniquement. Le piège est classique (Tu 2016, doi:10.1038/srep23247 ; Moreno et al. 1986,
doi:10.1152/jappl.1986.60.1.335 ; Wheatcroft 2019 sur la dépendance d'un skill score à sa
référence).

Trois tests, du plus simple au plus décisif :

1. **Métrique découplée.** Refaire la corrélation sur la **différence absolue** de perte
   `ΔMSE = MSE_CAMS − MSE_corr`, qui ne divise par rien. Si la corrélation s'évanouit, le
   +0,913 était l'artefact.
2. **Le correcteur nul.** Simuler un correcteur **fixe** — un simple débiaisage constant,
   qui n'a par construction *rien appris* des défaillances de CAMS. S'il produit lui aussi
   une corrélation élevée, alors le phénomène ne dit rien de l'apprentissage.
3. **Le test de Grok.** Restreindre aux mois où **CAMS est bon** et regarder si la correction
   y apporte encore quelque chose. C'est la formulation directe de la thèse, sans ratio.

Aucun ajustement : le script relit `reports/mos_{polluant}_J{horizon}.csv`.

Usage : python3 scripts/falsifier_these.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
GRAINE = 20260730


def par_mois(d: pd.DataFrame) -> pd.DataFrame:
    """RMSE, MSE et différence absolue de perte, par mois calendaire et par année."""
    lignes = []
    for (annee, mois), g in d.groupby([d["timestamp_utc"].dt.year,
                                       d["timestamp_utc"].dt.month]):
        e_cams = (g["cams"] - g["observe"]) ** 2
        e_mos = (g["corrige"] - g["observe"]) ** 2
        lignes.append({
            "annee": annee, "mois": mois, "n": len(g),
            "rmse_cams": float(np.sqrt(e_cams.mean())),
            "rmse_mos": float(np.sqrt(e_mos.mean())),
            "delta_mse": float(e_cams.mean() - e_mos.mean()),
            "gain_pct": 100 * (1 - float(np.sqrt(e_mos.mean() / e_cams.mean()))),
        })
    return pd.DataFrame(lignes)


def apparier_saisons(t: pd.DataFrame) -> pd.DataFrame:
    """Apparie chaque mois calendaire entre deux années — le protocole d'origine."""
    paires = []
    for mois, g in t.groupby("mois"):
        if g["annee"].nunique() < 2:
            continue
        a, b = sorted(g["annee"])[0], sorted(g["annee"])[-1]
        ga = g[g["annee"] == a].iloc[0]
        gb = g[g["annee"] == b].iloc[0]
        paires.append({
            "mois": mois,
            "d_rmse_cams": gb["rmse_cams"] - ga["rmse_cams"],
            "d_gain_pct": gb["gain_pct"] - ga["gain_pct"],
            "d_delta_mse": gb["delta_mse"] - ga["delta_mse"],
            "rmse_mos_a": ga["rmse_mos"], "rmse_mos_b": gb["rmse_mos"],
        })
    return pd.DataFrame(paires)


def correlation(x: pd.Series, y: pd.Series) -> tuple[float, float, float]:
    """Corrélation, et son étendue en retirant un point à la fois (leave-one-out).

    Avec cinq paires, une corrélation ne vaut que si elle survit au retrait de n'importe
    lequel de ses points.
    """
    r = float(np.corrcoef(x, y)[0, 1])
    loo = [float(np.corrcoef(x.drop(i), y.drop(i))[0, 1]) for i in x.index]
    return r, min(loo), max(loo)


def main(polluant: str, horizon: int, n_simulations: int) -> int:
    chemin = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    d = pd.read_csv(chemin, parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])
    t = par_mois(d)
    paires = apparier_saisons(t)

    print(f"{polluant} J+{horizon} · {len(d):,} couples · {len(paires)} paires "
          f"de mois appariées entre années\n", flush=True)

    # ── Test 1 : la métrique change-t-elle la conclusion ? ─────────────────────
    r_gain, lo_g, hi_g = correlation(paires["d_rmse_cams"], paires["d_gain_pct"])
    r_delta, lo_d, hi_d = correlation(paires["d_rmse_cams"], paires["d_delta_mse"])

    print("TEST 1 — la corrélation survit-elle au découplage de la métrique ?")
    print(f"  gain relatif (métrique d'origine, contient RMSE_CAMS au dénominateur)")
    print(f"    r = {r_gain:+.3f} · leave-one-out {lo_g:+.3f} à {hi_g:+.3f}")
    print(f"  différence absolue ΔMSE (ne divise par rien)")
    print(f"    r = {r_delta:+.3f} · leave-one-out {lo_d:+.3f} à {hi_d:+.3f}", flush=True)

    # ── Test 2 : un correcteur qui n'a rien appris fait-il aussi bien ? ────────
    # Débiaisage constant : on retranche à CAMS son biais **global**, identique tous les
    # mois. Il ne peut donc rien savoir des défaillances mensuelles du forçage.
    biais_global = float((d["cams"] - d["observe"]).mean())
    nul = d.assign(corrige=d["cams"] - biais_global)
    t_nul = par_mois(nul)
    paires_nul = apparier_saisons(t_nul)
    r_nul, lo_n, hi_n = correlation(paires_nul["d_rmse_cams"], paires_nul["d_gain_pct"])

    print("\nTEST 2 — un correcteur FIXE (débiaisage constant) produit-il la même "
          "corrélation ?")
    print(f"  biais global retranché : {biais_global:+.2f} µg/m³ · identique tous les mois")
    print(f"    r = {r_nul:+.3f} · leave-one-out {lo_n:+.3f} à {hi_n:+.3f}")
    verdict2 = ("⚠️ ARTEFACT — un correcteur qui n'a rien appris reproduit le phénomène"
                if abs(r_nul) > 0.7 else
                "✅ le correcteur fixe ne reproduit pas le phénomène")
    print(f"  {verdict2}", flush=True)

    # ── Test 3 : la thèse énoncée sans ratio ───────────────────────────────────
    median = t["rmse_cams"].median()
    bons = t[t["rmse_cams"] <= median]
    mauvais = t[t["rmse_cams"] > median]
    print("\nTEST 3 — la correction apporte-t-elle encore quelque chose quand CAMS est bon ?")
    print(f"  (partage à la médiane du RMSE CAMS mensuel : {median:.2f})")
    # Une RMSE de strate s'agrège **quadratiquement** sur ses mois. Le ΔMSE et le gain en
    # pourcentage, eux, se moyennent linéairement : ce ne sont pas des racines.
    def _agregee(sous, colonne):
        return float(np.sqrt(np.mean(sous[colonne].to_numpy() ** 2)))

    for nom, sous in (("mois où CAMS est BON  ", bons), ("mois où CAMS est MAUVAIS", mauvais)):
        print(f"  {nom} · n={len(sous):2d} · RMSE CAMS {_agregee(sous, 'rmse_cams'):5.2f} → "
              f"MOS {_agregee(sous, 'rmse_mos'):5.2f} · ΔMSE moyen {sous['delta_mse'].mean():+7.2f}"
              f" · gain {sous['gain_pct'].mean():+5.1f} %", flush=True)

    # ── Verdict ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    if abs(r_nul) > 0.7 and abs(r_delta) < 0.5:
        print("VERDICT : la thèse ne survit pas. Le +0,913 est un artefact de métrique —")
        print("  il disparaît en différence absolue et se reproduit avec un correcteur nul.")
    elif abs(r_delta) >= 0.5 and abs(r_nul) <= 0.7:
        print("VERDICT : la thèse survit aux deux tests. La corrélation tient en métrique")
        print("  découplée et un correcteur fixe ne la reproduit pas.")
    else:
        print("VERDICT : résultat mixte — voir le détail des trois tests ci-dessus.")
    print("Réserve constante : 5 paires de mois. Aucun de ces tests ne compense l'effectif.")

    sortie = RACINE / f"reports/falsification_{polluant}.csv"
    paires.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--simulations", type=int, default=500)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.simulations))
