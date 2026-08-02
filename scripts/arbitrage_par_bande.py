#!/usr/bin/env python3
"""La correction dégrade les classes basses de l'indice — arbitrer plutôt que corriger partout.

Le fait qui déclenche ce script
--------------------------------
`reports/INDICE_BOUT_EN_BOUT.md` contient un résultat que personne n'a exploité :

============  ==============  ========  ==================
classe        modèle          rappel    épisodes manqués
============  ==============  ========  ==================
**≥ 2**       CAMS brut       **0,992**  **462**
**≥ 2**       notre correction **0,971**  **1 697**
≥ 4           CAMS brut       0,259      1 334
≥ 4           notre correction **0,328**  **1 210**
============  ==============  ========  ==================

**Sur les classes basses, la correction est PIRE que CAMS brut** — 1 697 épisodes manqués
contre 462, un facteur 3,7. Sur les classes hautes elle est meilleure.

Le mécanisme est mécanique : la correction retire un biais **positif** de CAMS, donc elle
pousse les valeurs vers le bas, et près de la frontière de classe 2 elle fait basculer dans
le mauvais sens. Là où CAMS sur-annonce, sur-annoncer était protecteur.

Ce que ce script teste, et pourquoi ce n'est PAS un nouveau modèle
-------------------------------------------------------------------
Le projet a déjà réfuté trois fois l'idée d'un prédicteur spécialisé par classe : tête de
classification, perte pondérée, quantile 0,90, et calibration isotone ordinale n'apportent
**rien** dès que le seuil est libre — au budget de fausses annonces égal, l'isotone à coût
asymétrique achète **+1,2 point de rappel**, sous la barre de bruit de ±2 points.

Ce qui n'a jamais été testé est bien plus simple : **choisir, selon le niveau prévu, laquelle
des deux sorties on publie**. CAMS brut en dessous d'une bascule, la correction au-dessus.
Aucun apprentissage supplémentaire, aucune calibration — juste un aiguillage.

⚠️ Le point de bascule ne doit PAS être lu sur le jeu qui sert à annoncer le résultat
---------------------------------------------------------------------------------------
C'est la faute commise cette nuit sur le test de 90 stations. Ici la bascule est choisie sur
une moitié des **stations**, et le résultat annoncé sur l'autre moitié, jamais consultée pour
choisir. Le script imprime les deux.

Ce qu'il ne résout pas
----------------------
Le **rapport de coût** entre un épisode manqué et une fausse alerte n'existe nulle part dans
ce projet. Sans lui, « meilleur » n'a pas de définition unique : ce script rapporte donc le
front rappel/précision complet et **le F₂** (le rappel pondéré quatre fois plus que la
précision, convention déjà retenue dans `INDICE_BOUT_EN_BOUT`), en laissant le choix ouvert.
Aller chercher ce rapport auprès d'un opérationnel vaut plus que n'importe quel modèle.

Usage : python3 scripts/arbitrage_par_bande.py
Sortie : reports/arbitrage_par_bande.csv
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.models import indice_atmo as idx  # noqa: E402
from eval_indice_bout_en_bout import (charger_predictions,  # noqa: E402
                                      indices_journaliers)

GRAINE = 20260802
# Les classes de l'indice ATMO où l'on peut basculer. 1 = bon … 6 = extrêmement mauvais.
BASCULES = (1, 2, 3, 4, 5)


def scores_par_seuil(ref: pd.Series, cand: pd.Series, seuil: int) -> dict:
    """Détection de « classe ≥ seuil », du point de vue du métier."""
    vrai = (ref >= seuil).to_numpy()
    annonce = (cand >= seuil).to_numpy()
    a = int((vrai & annonce).sum())
    b = int((~vrai & annonce).sum())
    c = int((vrai & ~annonce).sum())
    rappel = a / (a + c) if a + c else np.nan
    precision = a / (a + b) if a + b else np.nan
    # F₂ : le rappel compte quatre fois la précision. L'arrêté du 07/04/2016 consacre cette
    # asymétrie en autorisant le déclenchement **sur prévision** — manquer engage la
    # responsabilité, sur-annoncer coûte de la crédibilité.
    f2 = (5 * precision * rappel / (4 * precision + rappel)
          if precision and rappel and (4 * precision + rappel) else np.nan)
    return {"seuil": seuil, "n_vrais": int(vrai.sum()), "detectes": a,
            "fausses": b, "manques": c, "rappel": rappel, "precision": precision,
            "f2": f2}


def main() -> int:
    depart = time.time()
    horaire = charger_predictions()
    print(f"{len(horaire):,} prévisions horaires · "
          f"{horaire['station_id'].nunique()} stations", flush=True)

    ind = {nom: indices_journaliers(horaire, col)
           for nom, col in (("observe", "observe"), ("cams", "cams"), ("mos", "corrige"))}
    for nom, t in ind.items():
        print(f"  {nom:8s} {len(t):,} couples station×jour", flush=True)

    # Un seul tableau aligné sur les couples communs — jamais trois alignements séparés,
    # qui laisseraient les modèles évalués sur des échantillons différents.
    d = (ind["observe"].rename(columns={"indice": "obs"})
         .merge(ind["cams"].rename(columns={"indice": "cams"}),
                on=["station_id", "jour_local"])
         .merge(ind["mos"].rename(columns={"indice": "mos"}),
                on=["station_id", "jour_local"]))
    print(f"\n{len(d):,} couples communs aux trois indices\n", flush=True)

    # ── Partition par stations : la bascule se choisit d'un côté, se lit de l'autre ──
    stations = np.sort(d["station_id"].unique())
    rng = np.random.default_rng(GRAINE)
    melange = rng.permutation(stations)
    choix = set(melange[: len(melange) // 2])
    d["part"] = np.where(d["station_id"].isin(choix), "choix", "lecture")
    print(f"choix de la bascule : {len(choix)} stations · "
          f"lecture : {len(stations) - len(choix)} stations\n")

    lignes = []
    for part in ("choix", "lecture"):
        sous = d[d["part"] == part]
        # Les deux références, puis chaque bascule possible.
        candidats = {"CAMS brut": sous["cams"], "correction (partout)": sous["mos"]}
        for b in BASCULES:
            # Aiguillage : sous la bascule on publie CAMS, au-dessus la correction.
            # Le niveau qui décide est celui **prévu par la correction** — seul disponible
            # à l'heure d'émission ; utiliser l'observé serait une fuite.
            candidats[f"arbitrage à ≥{b}"] = np.where(sous["mos"] >= b,
                                                      sous["mos"], sous["cams"])
        for nom, cand in candidats.items():
            cand = pd.Series(np.asarray(cand), index=sous.index)
            exact = float((cand == sous["obs"]).mean())
            for seuil in (2, 3, 4):
                lignes.append({"part": part, "modele": nom, "accord_exact": exact,
                               **scores_par_seuil(sous["obs"], cand, seuil)})

    t = pd.DataFrame(lignes)
    sortie = RACINE / "reports/arbitrage_par_bande.csv"
    t.to_csv(sortie, index=False)

    for part in ("choix", "lecture"):
        titre = ("CHOIX de la bascule" if part == "choix"
                 else "LECTURE — stations jamais utilisées pour choisir")
        print(f"{'═' * 82}\n{titre}\n{'═' * 82}")
        for seuil in (2, 3, 4):
            sous = t[(t["part"] == part) & (t["seuil"] == seuil)]
            print(f"\n  classe ≥ {seuil} · {int(sous['n_vrais'].iloc[0]):,} cas réels")
            print(f"    {'modèle':22s} {'rappel':>7s} {'précis.':>8s} {'F₂':>7s} "
                  f"{'manqués':>8s} {'accord':>7s}")
            for _, r in sous.iterrows():
                marque = ""
                if r["f2"] == sous["f2"].max():
                    marque = "  ← meilleur F₂"
                print(f"    {r['modele']:22s} {r['rappel']:7.3f} {r['precision']:8.3f} "
                      f"{r['f2']:7.3f} {int(r['manques']):8,d} "
                      f"{r['accord_exact']:7.3f}{marque}")

    print(f"\n{'─' * 82}")
    print("⚠️ Le rapport de coût épisode manqué / fausse alerte n'existe nulle part dans ce")
    print("   projet. Le F₂ en pose un implicite (rappel = 4× précision) ; il vient de")
    print("   l'asymétrie de l'arrêté du 07/04/2016, pas d'un opérationnel interrogé.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
