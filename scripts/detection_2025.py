#!/usr/bin/env python3
"""La détection tient-elle hors de la fenêtre d'apprentissage ?

Ce qu'il faut vérifier
----------------------
Sur les 17 mois appris, à budget de fausses alertes égal, la correction avec observations
passées attrape **65,6 %** des dépassements d'ozone contre **18,4 %** pour CAMS brut — 3,6 fois
plus. C'est le meilleur résultat du projet.

Mais il est mesuré sur la période d'entraînement, par stations exclues. La question qui décide
de sa valeur est ailleurs : **tient-il sur une période que le modèle n'a jamais vue ?** La
généralisation temporelle est précisément le point faible établi du projet — +1,1 % seulement
en saison ozone, en validation prospective stricte.

Le protocole
------------
Apprentissage strictement jusqu'au **31/12/2024**, application au 1ᵉʳ semestre **2025**
(21 stations occitanes). Le seuil de décision est calibré **sur 2024**, jamais sur 2025 : le
choisir sur les données évaluées fabriquerait le résultat.

Trois produits au même budget de fausses alertes : CAMS brut, la correction, et la correction
avec observations passées.

**Ce que l'échantillon interdit.** 21 stations et ~160 dépassements : un écart faible n'y serait
pas concluant, et les intervalles de confiance mesurés précédemment sur ce jeu montraient que
seule la différence de RMSE face au MOS officiel survivait. Les écarts ci-dessous se lisent
comme descriptifs, sauf s'ils sont massifs.

Usage : python3 scripts/detection_2025.py
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

from apport_observation_veille import variables_passees  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402
from scores_episodes import scores  # noqa: E402
from test_hors_echantillon_2025 import charger_2025  # noqa: E402

SEUIL = 120.0
BUDGETS = (0.10, 0.20, 0.30, 0.40)


def seuil_a_budget(vrai: np.ndarray, score: np.ndarray, budget: float) -> float:
    """Seuil le plus rappelant dont le taux de fausse alerte reste sous le budget — sur 2024."""
    grille = np.unique(np.quantile(score, np.linspace(0.50, 0.9995, 300)))
    meilleur, pod = np.nan, -1.0
    for s in grille:
        m = scores(vrai, score >= s)
        far = m.get("FAR")
        if far is None or np.isnan(far) or far > budget:
            continue
        if (m.get("POD") or 0) > pod:
            meilleur, pod = float(s), m["POD"]
    return meilleur


def main(polluant: str = "O3", horizon: int = 1) -> int:
    depart = time.time()

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    appris = charger(polluant, horizon)
    colonnes = colonnes_admises(appris)
    appris[colonnes] = appris[colonnes].replace([np.inf, -np.inf], 30_000.0)
    appris = appris.dropna(subset=["valeur"])
    ja = agreger_journalier(appris, colonnes, grandeur)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    passees_a, noms = variables_passees(ja)
    ja["jour"] = pd.to_datetime(ja["jour"])
    ja = ja.merge(passees_a, on=["station_id", "jour"], how="left").dropna(subset=noms)
    print(f"appris sur {len(ja):,} jours-station, jusqu'au {ja['jour'].max():%Y-%m-%d}",
          flush=True)

    cible = ja["obs_jour"] - ja["cams_jour"]
    sans = modele_mos().fit(ja[base], cible)
    avec = modele_mos().fit(ja[base + noms], cible)

    # ── 2025 ──────────────────────────────────────────────────────────────────
    d = charger_2025(polluant, horizon)
    d[colonnes] = d[colonnes].replace([np.inf, -np.inf], 30_000.0)
    d = d.dropna(subset=["valeur"])
    j = agreger_journalier(d, colonnes, grandeur)
    j["jour"] = pd.to_datetime(j["jour"])
    passees_r, _ = variables_passees(j)
    j = j.merge(passees_r, on=["station_id", "jour"], how="left").dropna(subset=noms)
    j["sans_obs"] = np.clip(j["cams_jour"] + sans.predict(j[base]), 0, None)
    j["avec_obs"] = np.clip(j["cams_jour"] + avec.predict(j[base + noms]), 0, None)

    vrai = (j["obs_jour"] >= SEUIL).to_numpy()
    print(f"2025 · {len(j):,} jours-station · {j['station_id'].nunique()} stations · "
          f"{int(vrai.sum())} dépassements\n", flush=True)

    # Les prédictions **sur 2024** servent à calibrer les seuils, jamais 2025.
    ja["sans_obs"] = np.clip(ja["cams_jour"] + sans.predict(ja[base]), 0, None)
    ja["avec_obs"] = np.clip(ja["cams_jour"] + avec.predict(ja[base + noms]), 0, None)
    vrai_2024 = (ja["obs_jour"] >= SEUIL).to_numpy()

    produits = [("CAMS brut", "cams_jour"), ("correction", "sans_obs"),
                ("correction + obs", "avec_obs")]
    lignes = []
    for budget in BUDGETS:
        print(f"── budget de fausses alertes ≤ {budget:.0%} (seuil calibré sur 2024) ──")
        print(f"{'produit':20s} {'seuil':>8s} {'rappel':>8s} {'FAR':>7s} {'CSI':>7s}")
        for nom, col in produits:
            s = seuil_a_budget(vrai_2024, ja[col].to_numpy(), budget)
            if np.isnan(s):
                print(f"{nom:20s} {'—':>8s}   budget inatteignable sur 2024")
                continue
            m = scores(vrai, (j[col] >= s).to_numpy())
            print(f"{nom:20s} {s:8.1f} {m['POD']:8.3f} {m['FAR']:7.3f} {m['CSI']:7.3f}",
                  flush=True)
            lignes.append({"budget": budget, "produit": nom, "seuil_2024": s, **m})
        print()

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/detection_2025_{polluant}.csv", index=False)
    print("=" * 74)
    for budget in BUDGETS:
        s = table[table["budget"] == budget]
        if len(s) < 2:
            continue
        g = s.loc[s["POD"].idxmax()]
        brut = s[s["produit"] == "CAMS brut"]["POD"]
        facteur = (g["POD"] / brut.iloc[0]) if len(brut) and brut.iloc[0] > 0 else np.nan
        print(f"à {budget:.0%} : **{g['produit']}** rappelle {g['POD']:.3f}"
              + (f" — {facteur:.1f}× le brut" if not np.isnan(facteur) else ""))
    print(f"\nÉcrit : reports/detection_2025_{polluant}.csv · {time.time() - depart:.0f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
