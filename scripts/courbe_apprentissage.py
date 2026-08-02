"""Combien d'historique faut-il ? Courbe d'apprentissage et validation inter-annuelle.

Usage : python scripts/courbe_apprentissage.py [--polluant O3]
Sorties : reports/COURBE_APPRENTISSAGE.md et le CSV associé

**Deux questions distinctes, et la seconde est la plus dure.**

**1. La courbe d'apprentissage.** Le gain en fonction du nombre de mois d'entraînement.
Elle répond à *combien d'historique faut-il* et montre où le rendement sature. Le premier
constat du projet — la correction s'effondrait à −19 % quand l'été était caché sur trois
mois — suggère qu'un **cycle annuel complet** est un seuil, pas une préférence : sans lui,
le modèle n'a jamais vu certains régimes.

**2. La validation inter-annuelle.** Entraîner sur une année, tester sur la suivante.
C'est bien plus exigeant qu'un mois exclu à l'intérieur d'une année : là, le modèle avait
toujours vu la saison voisine. Ici, il doit affronter une année entière qu'il n'a pas vue,
avec sa météo propre, ses épisodes propres, et d'éventuels changements de version du
modèle amont. **C'est le scénario opérationnel réel** — on entraîne sur le passé et on
prédit l'avenir.

L'archive couvre 2023-07 à 2025-06, soit deux années glissantes non chevauchantes.
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
from aq.models import mos  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402


def evaluer(entrainement, test, colonnes) -> dict:
    modele = mos._modele(0)
    modele.fit(entrainement[colonnes],
               entrainement["valeur"] - entrainement["cams"])
    predit = np.clip(
        test["cams"].to_numpy() + modele.predict(test[colonnes]), 0, None)
    a = cmp.metriques(test["valeur"], test["cams"])
    b = cmp.metriques(test["valeur"], predit)
    return {"rmse_cams": a["rmse"], "rmse_mos": b["rmse"], "r2_mos": b["r2"],
            "biais_mos": b["biais"], "gain_pct": 100 * (1 - b["rmse"] / a["rmse"]),
            "n_test": len(test)}


def main(polluant: str, horizon: int) -> int:
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"]).reset_index(drop=True)
    jeu["mois"] = pd.to_datetime(jeu["timestamp_utc"]).dt.to_period("M")

    mois = sorted(jeu["mois"].unique())
    print(f"{polluant} J+{horizon} · {len(jeu):,} paires · "
          f"{len(mois)} mois · {mois[0]} → {mois[-1]}\n", flush=True)
    if len(mois) < 6:
        raise SystemExit("Trop peu de mois pour une courbe d'apprentissage.")

    lignes = []

    # ── 1. Courbe d'apprentissage ────────────────────────────────────────────
    # Le test est **fixé** aux six derniers mois : sans cela, chaque point de la courbe
    # serait évalué sur une période différente et l'on ne saurait pas si la variation
    # vient de l'entraînement ou du test.
    test_fixe = jeu[jeu["mois"].isin(mois[-6:])]
    disponibles = mois[:-6]
    print(f"Test fixé sur les 6 derniers mois ({mois[-6]} → {mois[-1]}) · "
          f"{len(test_fixe):,} paires", flush=True)
    print(f"{'mois appris':>12s} {'n train':>11s} {'RMSE CAMS':>10s} "
          f"{'RMSE MOS':>9s} {'gain':>8s}")

    # Le dernier point est **tout l'historique disponible**, quel qu'il soit : sans lui
    # la courbe s'arrêterait avant son terme dès que le total n'est pas rond, et c'est
    # précisément ce point qui répond à « faut-il plus d'historique ? ».
    paliers = sorted({n for n in (1, 2, 3, 6, 9, 12) if n <= len(disponibles)}
                     | {len(disponibles)})
    for n_mois in paliers:
        if n_mois > len(disponibles):
            continue
        # On prend les mois **les plus récents** avant le test : c'est ce qu'on ferait
        # en exploitation, et cela évite de créer un trou temporel artificiel.
        appris = disponibles[-n_mois:]
        entrainement = jeu[jeu["mois"].isin(appris)]
        r = evaluer(entrainement, test_fixe, colonnes)
        lignes.append({"experience": "courbe", "n_mois": n_mois,
                       "n_train": len(entrainement), **r})
        print(f"{n_mois:>12d} {len(entrainement):>11,} {r['rmse_cams']:10.2f} "
              f"{r['rmse_mos']:9.2f} {r['gain_pct']:+7.1f} %", flush=True)

    # ── 2. Validation inter-annuelle ─────────────────────────────────────────
    # Douze mois d'entraînement — un cycle saisonnier complet — et **tout le reste** en
    # test. Exiger deux années pleines rendrait l'expérience impossible : l'archive
    # exploitable s'arrête au 1er janvier 2025, faute d'observations au-delà.
    if len(mois) >= 15:
        premiere = mois[:12]
        seconde = mois[12:]
        entrainement = jeu[jeu["mois"].isin(premiere)]
        test = jeu[jeu["mois"].isin(seconde)]
        r = evaluer(entrainement, test, colonnes)
        lignes.append({"experience": "inter-annuelle", "n_mois": 12,
                       "n_train": len(entrainement), **r})
        print(f"\n── Validation inter-annuelle ──", flush=True)
        print(f"  appris  {premiere[0]} → {premiere[-1]} ({len(entrainement):,} paires)",
              flush=True)
        print(f"  testé   {seconde[0]} → {seconde[-1]} ({len(test):,} paires)",
              flush=True)
        print(f"  RMSE {r['rmse_cams']:.2f} → {r['rmse_mos']:.2f} · "
              f"gain {r['gain_pct']:+.1f} % · R² {r['r2_mos']:+.3f} · "
              f"biais {r['biais_mos']:+.2f}", flush=True)
    else:
        print(f"\n(validation inter-annuelle impossible : {len(mois)} mois, 15 requis)",
              flush=True)

    pd.DataFrame(lignes).to_csv(
        RACINE / f"reports/courbe_apprentissage_{polluant}.csv", index=False)
    print(f"\nÉcrit : courbe_apprentissage_{polluant}.csv")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
