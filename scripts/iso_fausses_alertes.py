#!/usr/bin/env python3
"""À budget de fausses alertes égal, qui détecte le plus ?

Pourquoi cette comparaison-ci
-----------------------------
Le dossier compare les produits **chacun à son seuil optimal**. Ce n'est pas la question d'un
service : celui-ci ne choisit pas un seuil pour maximiser un score, il subit un **budget de
fausses alertes** — au-delà d'une certaine fréquence, une alerte cesse d'être écoutée, et la
décision devient politique avant d'être technique.

La comparaison utile est donc *à taux de fausse alerte fixé, quel produit rappelle le plus ?*

Une remarque de méthode qui rend ce script court
-------------------------------------------------
Maximiser le **F1** ne changerait rien à ce que le projet fait déjà : avec `b = FP + FN`,

    CSI = TP/(TP+b)    et    F1 = 2·TP/(2·TP+b)    donc    F1 = 2·CSI/(1+CSI),

strictement croissante. Le seuil qui maximise le CSI maximise le F1. Inutile de refaire les
mesures sous l'autre nom — et la **précision seule** est un objectif dégénéré, qu'on approche
de 1 en n'annonçant presque rien.

Ce que ce script produit
------------------------
Pour chaque produit, le **rappel atteint** à des taux de fausse alerte imposés (10 %, 20 %,
30 %, 40 %), le seuil correspondant, et le nombre d'alertes émises. C'est la courbe qu'un
service lit pour choisir son point de fonctionnement, et elle rend l'arbitrage explicite au
lieu de le laisser dans le choix d'une métrique.

Usage : python3 scripts/iso_fausses_alertes.py [--source 2025|appris]
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

from scores_episodes import scores  # noqa: E402

SEUIL_O3 = 120.0
BUDGETS = (0.10, 0.20, 0.30, 0.40)


def charger(source: str) -> tuple[pd.DataFrame, list[tuple[str, str]], str]:
    if source == "2025":
        d = pd.read_csv(RACINE / "reports/test_hors_echantillon_2025_detail_O3.csv").rename(
            columns={"obs_jour": "observe", "cams_jour": "cams"})
        produits = [("CAMS brut", "cams"), ("MOS officiel", "officiel_mos"),
                    ("notre correction", "corrige")]
        produits = [(n, c) for n, c in produits if c in d]
        return d.dropna(subset=["observe"] + [c for _, c in produits]), produits, \
            "1ᵉʳ semestre 2025, hors fenêtre d'apprentissage"

    d = pd.read_csv(RACINE / "reports/mos_O3_J1.csv",
                    parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])
    d = d.sort_values(["station_id", "timestamp_utc"])
    d["jour"] = d["timestamp_utc"].dt.floor("D")
    for c in ("observe", "cams", "corrige"):
        d[c + "_8h"] = (d.groupby("station_id")[c]
                          .transform(lambda s: s.rolling(8, min_periods=6).mean()))
    j = (d.groupby(["station_id", "jour"])
           .agg(observe=("observe_8h", "max"), cams=("cams_8h", "max"),
                corrige=("corrige_8h", "max"), n=("timestamp_utc", "size")).reset_index())
    j = j[j["n"] >= 18].dropna(subset=["observe", "cams", "corrige"])
    return j, [("CAMS brut", "cams"), ("notre correction", "corrige")], \
        "17 mois appris, validation par stations exclues"


def rappel_a_budget(vrai: np.ndarray, score: np.ndarray, budget: float) -> dict:
    """Rappel obtenu au seuil le plus bas dont le taux de fausse alerte reste sous le budget.

    On balaie les valeurs prédites elles-mêmes plutôt qu'une grille : la plage utile dépend du
    produit — un modèle qui écrase les extrêmes n'atteint jamais 120 — et une grille fixe
    explorerait surtout des seuils sans aucune annonce.
    """
    candidats = np.unique(np.quantile(score, np.linspace(0.50, 0.9999, 400)))
    meilleur = None
    for s in candidats:
        m = scores(vrai, score >= s)
        far = m.get("FAR")
        if far is None or np.isnan(far) or far > budget:
            continue
        # À budget respecté, on garde le seuil qui rappelle le plus.
        if meilleur is None or (m.get("POD") or 0) > (meilleur[1].get("POD") or 0):
            meilleur = (float(s), m)
    if meilleur is None:
        return {}
    seuil, m = meilleur
    return {"seuil": seuil, "POD": m["POD"], "FAR": m["FAR"], "CSI": m["CSI"],
            "n_alertes": int((score >= seuil).sum())}


def main(source: str) -> int:
    d, produits, description = charger(source)
    vrai = (d["observe"] >= SEUIL_O3).to_numpy()
    print(f"O₃ · {description}\n  {len(d):,} jours-station · "
          f"{int(vrai.sum())} dépassements ({100 * vrai.mean():.2f} %)\n", flush=True)

    lignes = []
    for budget in BUDGETS:
        print(f"── budget de fausses alertes ≤ {budget:.0%} ──")
        print(f"{'produit':20s} {'seuil':>8s} {'rappel':>8s} {'FAR':>7s} "
              f"{'CSI':>7s} {'alertes':>8s}")
        for nom, col in produits:
            r = rappel_a_budget(vrai, d[col].to_numpy(), budget)
            if not r:
                print(f"{nom:20s} {'—':>8s}   budget inatteignable")
                lignes.append({"budget": budget, "produit": nom})
                continue
            print(f"{nom:20s} {r['seuil']:8.1f} {r['POD']:8.3f} {r['FAR']:7.3f} "
                  f"{r['CSI']:7.3f} {r['n_alertes']:8,}", flush=True)
            lignes.append({"budget": budget, "produit": nom, **r})
        print()

    table = pd.DataFrame(lignes)
    suffixe = "" if source == "appris" else f"_{source}"
    table.to_csv(RACINE / f"reports/iso_fausses_alertes_O3{suffixe}.csv", index=False)

    print("=" * 74)
    # **Ce que la comparaison décide** : à budget imposé, l'ordre des produits peut différer
    # de celui obtenu à seuils optimaux respectifs. Si l'ordre change, c'est que le classement
    # publié dépendait du choix de la métrique, pas de la capacité des produits.
    for budget in BUDGETS:
        s = table[(table["budget"] == budget) & table["POD"].notna()]
        if len(s) < 2:
            continue
        gagnant = s.loc[s["POD"].idxmax()]
        ecart = gagnant["POD"] - s["POD"].drop(gagnant.name).max()
        print(f"à {budget:.0%} de fausses alertes : **{gagnant['produit']}** rappelle "
              f"{gagnant['POD']:.3f} ({ecart:+.3f} sur le suivant)")
    print(f"\nÉcrit : reports/iso_fausses_alertes_O3{suffixe}.csv", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", default="appris", choices=("appris", "2025"))
    args = p.parse_args()
    raise SystemExit(main(args.source))
