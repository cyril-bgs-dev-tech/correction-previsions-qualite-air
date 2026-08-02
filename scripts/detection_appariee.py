#!/usr/bin/env python3
"""Comparaison **appariée** des détecteurs, sur exactement les mêmes prédictions hors pli.

Ce que ce script tranche
-------------------------
Le dossier annonce « à précision égale, 1,7× à 4,1× plus de dépassements détectés ». Ce
chiffre a été mesuré sur l'axe **spatial seul**. Une tentative sur l'axe double aveugle a
rendu **×0,85** — un renversement complet.

Deux choses avaient changé en même temps : le protocole *et* le détecteur (un classifieur
au lieu du score du régresseur). Tant que les deux bougent ensemble, on ne peut rien
conclure. Ici, **seul le détecteur change** : mêmes lignes, même cible, même horizon,
mêmes plis.

L'hypothèse d'écrasement de queue est déjà réfutée : `oof_double_aveugle.py` mesure un
rapport de dispersion **supérieur** pour la correction (0,754) à celui de CAMS (0,662) sur
NO₂, et 0,890 contre 0,774 sur O₃. La correction restaure de l'amplitude, elle n'en
détruit pas. Il reste donc à savoir si l'avantage de détection survit.

Les trois règles d'évaluation, posées avant de mesurer
-------------------------------------------------------
1. **Agrégation micro.** On empile toutes les prédictions hors pli puis on construit
   **une** table de contingence, plutôt que de moyenner des ratios par pli. C'est la
   pratique du référentiel LCSQA, et c'est la seule qui réponde à « sur une occurrence
   station-jour future, que se passe-t-il ? ». Une moyenne non pondérée donnerait le même
   poids à un mois contenant un dépassement et à un mois en contenant vingt.
2. **Comparaison à budget d'alerte égal.** Comparer deux détecteurs à seuil identique
   confond discrimination et calibration : celui qui alerte plus détecte plus,
   trivialement. On compare donc aussi à **nombre d'alertes égal** — le détecteur classe,
   on prend les N premiers, N étant fixé par le nombre d'alertes de CAMS.
3. **L'incertitude est portée par les épisodes, pas par les lignes.** Un épisode régional
   touche des dizaines de stations le même jour : les compter comme indépendantes
   fabriquerait un intervalle faussement étroit. Le bootstrap resample donc des **jours**.

Les seuils, et ce qu'ils sont exactement
-----------------------------------------
* **PM10 · moyenne journalière · 50 µg/m³** — c'est le seuil d'information français
  (arrêté du 07/04/2016) *et* le grain d'agrégation de notre cible. Comparable aux chiffres
  publiés de PREV'AIR pour 2023 : à J0, CHIMERE `POD=31 %, SR=17 %` ; leur adaptation
  statistique `POD=33 %, SR=50 %`.
* **O₃ · maximum 8 h glissant · 120 µg/m³** — c'est la **valeur cible européenne**, pas le
  seuil d'information français. Celui-ci vaut 180 µg/m³ en **moyenne horaire** et ne peut
  pas se calculer sur notre cible en max 8 h. Ne jamais présenter un résultat à 120 comme
  une performance sur la procédure préfectorale.
* **NO₂ · maximum horaire · 200 µg/m³** — seuil d'information français.

Usage : python3 scripts/detection_appariee.py --polluant PM10 [--typologie]
Sortie : reports/detection_appariee_<polluant>[_typo].csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]

# Seuil, grandeur sur laquelle il porte, et statut réglementaire — jamais un nombre nu.
SEUILS = {
    "PM10": (50.0, "moyenne journalière", "seuil d'information français"),
    "PM25": (50.0, "moyenne journalière", "AUCUN seuil français — repère indicatif"),
    "O3": (120.0, "maximum 8 h glissant", "valeur cible européenne (PAS le seuil 180)"),
    "NO2": (200.0, "maximum horaire", "seuil d'information français"),
}


def wilson(succes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalle de Wilson — préféré à l'approximation normale quand les succès sont rares."""
    if total == 0:
        return (np.nan, np.nan)
    p, n = succes / total, total
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    e = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - e), min(1.0, c + e))


def contingence(verite: np.ndarray, alerte: np.ndarray) -> dict:
    """Table de contingence et les scores du référentiel LCSQA.

    ⚠️ `FAR` est pris au sens des AASQA — `FP/(TP+FP)`, la part de fausses alertes **parmi
    les alertes émises**. Ce n'est PAS le taux de faux positifs `FP/(FP+TN)` de la
    littérature d'apprentissage. Les confondre change le chiffre d'un ordre de grandeur,
    les non-événements étant écrasants.
    """
    tp = int(np.sum(verite & alerte))
    fp = int(np.sum(~verite & alerte))
    fn = int(np.sum(verite & ~alerte))
    tn = int(np.sum(~verite & ~alerte))
    pod = tp / (tp + fn) if tp + fn else np.nan
    sr = tp / (tp + fp) if tp + fp else np.nan
    csi = tp / (tp + fp + fn) if tp + fp + fn else np.nan
    bas, haut = wilson(tp, tp + fn)
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "n_alertes": tp + fp,
            "POD": pod, "POD_ic95_bas": bas, "POD_ic95_haut": haut,
            "SR": sr, "FAR": 1 - sr if np.isfinite(sr) else np.nan, "CSI": csi,
            "biais_frequence": (tp + fp) / (tp + fn) if tp + fn else np.nan}


def au_budget(score: np.ndarray, n_alertes: int) -> np.ndarray:
    """Alerte sur les `n_alertes` scores les plus élevés — comparaison à budget égal."""
    alerte = np.zeros(len(score), dtype=bool)
    if n_alertes > 0:
        alerte[np.argsort(-score, kind="stable")[:n_alertes]] = True
    return alerte


def bootstrap_jours(d: pd.DataFrame, verite: np.ndarray, a_ref: np.ndarray,
                    a_test: np.ndarray, n: int = 400, graine: int = 20260802) -> dict:
    """Intervalle sur l'écart de CSI, en resamplant des **jours** et non des lignes.

    Un épisode touche des dizaines de stations le même jour. Resampler les lignes
    traiterait ces observations comme indépendantes et rendrait un intervalle
    faussement étroit — l'erreur exacte que la règle 5 du projet interdit.
    """
    rng = np.random.default_rng(graine)
    jours = d["jour"].to_numpy()
    uniques = np.unique(jours)
    index_par_jour = {j: np.flatnonzero(jours == j) for j in uniques}
    ecarts = []
    for _ in range(n):
        tirage = rng.choice(uniques, size=len(uniques), replace=True)
        idx = np.concatenate([index_par_jour[j] for j in tirage])
        c_ref = contingence(verite[idx], a_ref[idx])["CSI"]
        c_test = contingence(verite[idx], a_test[idx])["CSI"]
        if np.isfinite(c_ref) and np.isfinite(c_test):
            ecarts.append(c_test - c_ref)
    if not ecarts:
        return {"delta_csi_bas": np.nan, "delta_csi_haut": np.nan}
    return {"delta_csi_bas": float(np.percentile(ecarts, 2.5)),
            "delta_csi_haut": float(np.percentile(ecarts, 97.5))}


def main(polluant: str, typologie: bool, epreuve: str) -> int:
    suffixe = "_typo" if typologie else ""
    source = RACINE / f"data/interim/oof/oof_{polluant}{suffixe}.parquet"
    if not source.exists():
        raise SystemExit(f"absent : {source.relative_to(RACINE)} — lancer d'abord "
                         f"oof_double_aveugle.py --polluant {polluant}"
                         f"{' --typologie' if typologie else ''}")

    oof = pd.read_parquet(source)
    seuil, grandeur, statut = SEUILS[polluant]

    lignes = []
    epreuves = sorted(oof["epreuve"].unique()) if epreuve == "toutes" else [epreuve]
    for ep in epreuves:
        d = oof[oof["epreuve"] == ep].reset_index(drop=True)
        verite = (d["valeur"].to_numpy() >= seuil)
        n_pos = int(verite.sum())
        print(f"\n{'═' * 78}\n{polluant} · {ep} · seuil {seuil:.0f} µg/m³ ({grandeur})\n"
              f"{statut}\n{'═' * 78}")
        print(f"  {len(d):,} occurrences station-jour · {n_pos:,} dépassements observés "
              f"({100 * n_pos / len(d):.2f} %) · {d['jour'].nunique():,} jours distincts")
        if n_pos < 10:
            print(f"  ⚠️ {n_pos} dépassements — trop peu pour conclure. Mesuré, pas conclu.")

        # ── ① Même seuil appliqué aux deux ────────────────────────────────────────
        r_cams = contingence(verite, d["cams_jour"].to_numpy() >= seuil)
        r_mos = contingence(verite, d["pred"].to_numpy() >= seuil)

        # ── ② Budget d'alerte égal — le détecteur CLASSE, on prend les N premiers ──
        n_budget = r_cams["n_alertes"]
        r_mos_budget = contingence(verite, au_budget(d["pred"].to_numpy(), n_budget))
        r_cams_budget = contingence(verite, au_budget(d["cams_jour"].to_numpy(), n_budget))

        ic = bootstrap_jours(d, verite, au_budget(d["cams_jour"].to_numpy(), n_budget),
                             au_budget(d["pred"].to_numpy(), n_budget))

        print(f"\n  {'détecteur':28s} {'alertes':>8s} {'TP':>5s} {'POD':>7s} "
              f"{'IC95 POD':>16s} {'SR':>7s} {'CSI':>7s}")
        for nom, r in (("CAMS brut, seuil", r_cams),
                       ("correction, seuil", r_mos),
                       ("CAMS brut, budget égal", r_cams_budget),
                       ("correction, budget égal", r_mos_budget)):
            print(f"  {nom:28s} {r['n_alertes']:8,d} {r['TP']:5d} {r['POD']:7.3f} "
                  f"[{r['POD_ic95_bas']:.3f} ; {r['POD_ic95_haut']:.3f}] "
                  f"{r['SR']:7.3f} {r['CSI']:7.3f}")

        if np.isfinite(r_cams_budget["CSI"]) and r_cams_budget["CSI"] > 0:
            rapport = r_mos_budget["TP"] / max(r_cams_budget["TP"], 1)
            print(f"\n  À budget d'alerte égal ({n_budget:,} alertes) : "
                  f"**×{rapport:.2f}** de dépassements détectés")
            print(f"  Écart de CSI, IC95 par bootstrap de JOURS : "
                  f"[{ic['delta_csi_bas']:+.4f} ; {ic['delta_csi_haut']:+.4f}]"
                  f"{'  — significatif' if ic['delta_csi_bas'] > 0 else ''}"
                  f"{'  — NON significatif' if ic['delta_csi_bas'] <= 0 <= ic['delta_csi_haut'] else ''}")

        for nom, r in (("cams_seuil", r_cams), ("mos_seuil", r_mos),
                       ("cams_budget", r_cams_budget), ("mos_budget", r_mos_budget)):
            lignes.append({"polluant": polluant, "epreuve": ep, "detecteur": nom,
                           "seuil": seuil, "n_obs": len(d), "n_positifs": n_pos, **r, **ic})

    t = pd.DataFrame(lignes)
    sortie = RACINE / f"reports/detection_appariee_{polluant}{suffixe}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="PM10")
    p.add_argument("--typologie", action="store_true")
    p.add_argument("--epreuve", default="toutes",
                   help="'toutes', ou 'double aveugle' / 'spatiale' / 'temporelle'")
    a = p.parse_args()
    raise SystemExit(main(a.polluant, a.typologie, a.epreuve))
