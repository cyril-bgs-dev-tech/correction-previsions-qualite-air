#!/usr/bin/env python3
"""Comparer probabilités brutes, IVAP et CVAP sur les dépassements d'O3.

Le protocole par défaut est **double aveugle** : les modèles apprennent sur les dates
antérieures au 1er juillet 2024 et sont évalués de juillet à décembre 2024 sur des stations
entièrement exclues. Les trois groupes de stations couvrent le futur une seule fois chacun.

« Avec induction » signifie ici un IVAP à partage unique par stations : 75 % des stations
historiques ajustent LightGBM, 25 % calibrent Venn–Abers. « Sans induction » correspond au
paramètre usuel ``inductive=False`` des bibliothèques : un CVAP à trois plis de stations.
Ce n'est pas le Venn–Abers transductif complet, qui réentraînerait pour chaque objet test.

Pour ne pas confondre calibration, quantité d'apprentissage et effet d'ensemble, cinq
sorties sont évaluées : modèle brut entraîné sur tout le passé ; score brut et IVAP du
même modèle réduit ; ensemble brut et CVAP construits avec les mêmes modèles internes.

Sorties :
  reports/calibration_venn_abers_{polluant}.csv
  reports/calibration_venn_abers_{polluant}_plis.csv
  reports/calibration_venn_abers_{polluant}_predictions.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval.venn_abers import calibrer_venn_abers, fusionner_cvap  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from scores_episodes import scores as scores_episode  # noqa: E402

GRAINE = 20260802
# Sous ce nombre d'événements sur la période de test, le script refuse de comparer.
MIN_EVENEMENTS = 100

# ⚠️ **Pas `n_jobs=-1`.** Mesuré le 02/08/2026 : ce script lancé avec `-1` à côté d'un seul
# autre lot portait la charge à **67,7 sur 32 cœurs**, CPU à 99,7 % et **0 % au repos** — les
# deux lots se ralentissaient mutuellement au lieu de se partager la machine.
#
# La règle 1 de `CLAUDE.md` a été écrite après que trois ajustements `n_jobs=-1` simultanés
# aient été **tués à 90 minutes sans finir** : la contention porte sur la bande passante
# mémoire, pas sur les cœurs. Et LightGBM ne monte de toute façon pas en charge au-delà
# d'environ 1,5 cœur sur un jeu de cette taille — mesuré le même jour.
#
# Ce script ajuste **15 modèles par pli externe** (1 référence + 1 IVAP + 3 CVAP, × 3 plis) :
# c'est lui qui doit céder du terrain, pas les autres.
N_JOBS = 6


def modele(graine: int):
    """Même LightGBM que ``classification_depassement.py``."""
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        n_estimators=400, learning_rate=0.05, num_leaves=63,
        min_child_samples=200, subsample=0.8, subsample_freq=1,
        colsample_bytree=0.8, random_state=graine, n_jobs=N_JOBS, verbose=-1,
    )


def ajuster_predire(train: pd.DataFrame, test: pd.DataFrame,
                    predicteurs: list[str], graine: int) -> np.ndarray:
    m = modele(graine)
    m.fit(train[predicteurs], train["cible"])
    return np.clip(m.predict_proba(test[predicteurs])[:, 1], 0.0, 1.0)


def groupes_stations(stations, n: int, graine: int) -> list[np.ndarray]:
    uniques = np.asarray(sorted(pd.unique(stations)))
    rng = np.random.default_rng(graine)
    return [x for x in np.array_split(rng.permutation(uniques), n) if len(x)]


def ece_equal_mass(y: np.ndarray, p: np.ndarray, n_paniers: int = 10) -> float:
    """Erreur de calibration descriptive, avec paniers d'effectif comparable."""
    ordre = np.argsort(p)
    total = len(y)
    ece = 0.0
    for idx in np.array_split(ordre, n_paniers):
        if not len(idx):
            continue
        ece += len(idx) / total * abs(float(p[idx].mean() - y[idx].mean()))
    return ece


def metriques(y: np.ndarray, p: np.ndarray, p_reference: np.ndarray,
              seuil_decision: float, bas=None, haut=None) -> dict:
    eps = 1e-12
    bs = float(np.mean((p - y) ** 2))
    bs_ref = float(np.mean((p_reference - y) ** 2))
    s = scores_episode(y.astype(bool), p >= seuil_decision)
    sortie = {
        "n": len(y), "n_evenements": int(y.sum()), "frequence": float(y.mean()),
        "brier": bs, "brier_reference": bs_ref,
        "brier_skill": 1.0 - bs / bs_ref if bs_ref > 0 else np.nan,
        "log_loss": float(log_loss(y, np.clip(p, eps, 1 - eps), labels=[0, 1])),
        "average_precision": float(average_precision_score(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "ece_10_equal_mass": ece_equal_mass(y, p),
        "proba_moyenne": float(p.mean()),
        **s,
    }
    if bas is not None and haut is not None:
        largeur = np.asarray(haut) - np.asarray(bas)
        sortie |= {
            "largeur_va_moyenne": float(np.mean(largeur)),
            "largeur_va_p95": float(np.quantile(largeur, 0.95)),
        }
    return sortie


def main(polluant: str, horizon: int, seuil: float, coupure: str,
         n_plis_externes: int, n_plis_cvap: int, part_calibration: float,
         seuil_decision: float) -> int:
    depart = time.time()
    brut = charger(polluant, horizon)
    colonnes = colonnes_admises(brut)
    brut[colonnes] = brut[colonnes].replace([np.inf, -np.inf], 30_000.0)
    brut = brut.dropna(subset=["valeur"])
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(brut, colonnes, grandeur)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["cible"] = (d["valeur"] >= seuil).astype("int8")
    date_coupure = pd.Timestamp(coupure, tz=d["jour"].dt.tz)
    passe = d["jour"] < date_coupure
    futur = ~passe
    if not passe.any() or not futur.any():
        raise ValueError("la coupure doit laisser un passé d'apprentissage et un futur de test")

    # ⚠️ **Refuser plutôt que produire un tableau plausible.**
    #
    # Lancé le 02/08/2026 sur NO₂ au seuil 120 µg/m³, ce script a imprimé un classement des
    # cinq méthodes sur **35 événements** en 58 611 jours-station. L'average precision y
    # valait 0,00066 pour un taux de base de 0,00060, et l'AUC 0,549 : le hasard. Les cinq
    # colonnes comparaient donc cinq façons de calibrer **du bruit**, et rien dans la sortie
    # ne le disait — les Brier skill négatifs et les CSI à zéro se lisent, mais après coup.
    #
    # À titre de comparaison, l'ozone au même seuil compte **730 événements**, une AP de
    # 0,386 pour un taux de base de 0,0153 — soit 25 fois le hasard.
    #
    # Une calibration ne crée aucune information. S'il n'y a pas de discrimination à
    # calibrer, le résultat n'est pas « mauvais », il est **vide**.
    n_evenements = int(d.loc[futur, "cible"].sum())
    if n_evenements < MIN_EVENEMENTS:
        raise SystemExit(
            f"{n_evenements} dépassement(s) de {seuil:g} sur la période de test — "
            f"minimum {MIN_EVENEMENTS}.\n"
            f"Il n'y a rien à calibrer : une calibration ne crée pas d'information. "
            f"Choisir un seuil\nplus bas, ou conclure que ce seuil n'est pas prédictible "
            f"sur ce corpus — ce qui est\nun résultat en soi, pas un échec de méthode.")

    groupes_externes = groupes_stations(d["station_id"], n_plis_externes, GRAINE)
    predictions, details = [], []
    print(f"{polluant} J+{horizon} · {grandeur} ≥ {seuil:g} · {len(d):,} jours-station · "
          f"coupure {date_coupure.date()} · {int(futur.sum()):,} lignes futures", flush=True)

    for no, stations_test in enumerate(groupes_externes, start=1):
        masque_test = futur & d["station_id"].isin(stations_test)
        masque_pool = passe & ~d["station_id"].isin(stations_test)
        test = d[masque_test].copy()
        pool = d[masque_pool].copy()
        if test.empty or pool.empty or test["cible"].nunique() < 2:
            print(f"  pli {no}: ignoré, test ou classe vide", flush=True)
            continue
        frequence_train = float(pool["cible"].mean())

        # 1. Référence brute : toute l'information historique autorisée.
        p_brut = ajuster_predire(pool, test, predicteurs, GRAINE + no)

        # 2. IVAP : partage unique par stations, score brut et score calibré comparables.
        groupes_ivap = groupes_stations(pool["station_id"],
                                        max(2, round(1 / part_calibration)),
                                        GRAINE + 100 + no)
        stations_cal = groupes_ivap[0]
        cal = pool[pool["station_id"].isin(stations_cal)]
        propre = pool[~pool["station_id"].isin(stations_cal)]
        if cal["cible"].sum() < 20 or propre["cible"].sum() < 20:
            raise RuntimeError(f"pli {no}: trop peu d'événements pour l'IVAP")
        m_ivap = modele(GRAINE + 200 + no)
        m_ivap.fit(propre[predicteurs], propre["cible"])
        p_cal = m_ivap.predict_proba(cal[predicteurs])[:, 1]
        p_ivap_brut = m_ivap.predict_proba(test[predicteurs])[:, 1]
        p_ivap, p0_ivap, p1_ivap = calibrer_venn_abers(
            p_cal, cal["cible"].to_numpy(), p_ivap_brut)

        # 3. CVAP : chaque pli interne est à la fois calibration et modèle d'ensemble.
        groupes_cv = groupes_stations(pool["station_id"], n_plis_cvap,
                                      GRAINE + 300 + no)
        p0_folds, p1_folds, p_bruts_folds = [], [], []
        for k, stations_cal_cv in enumerate(groupes_cv, start=1):
            cal_cv = pool[pool["station_id"].isin(stations_cal_cv)]
            propre_cv = pool[~pool["station_id"].isin(stations_cal_cv)]
            if cal_cv["cible"].sum() < 20 or propre_cv["cible"].sum() < 20:
                raise RuntimeError(f"pli {no}/{k}: trop peu d'événements pour le CVAP")
            m_cv = modele(GRAINE + 400 + no * 10 + k)
            m_cv.fit(propre_cv[predicteurs], propre_cv["cible"])
            p_cal_cv = m_cv.predict_proba(cal_cv[predicteurs])[:, 1]
            p_test_cv = m_cv.predict_proba(test[predicteurs])[:, 1]
            _, p0_cv, p1_cv = calibrer_venn_abers(
                p_cal_cv, cal_cv["cible"].to_numpy(), p_test_cv)
            p0_folds.append(p0_cv); p1_folds.append(p1_cv); p_bruts_folds.append(p_test_cv)
        p_cvap, p0_cvap, p1_cvap = fusionner_cvap(
            np.column_stack(p0_folds), np.column_stack(p1_folds))
        p_cvap_brut = np.mean(np.column_stack(p_bruts_folds), axis=1)

        bloc = test[["station_id", "jour", "valeur", "cible"]].copy()
        bloc["pli"] = no
        bloc["frequence_train"] = frequence_train
        bloc["p_brut_complet"] = p_brut
        bloc["p_ivap_brut"] = p_ivap_brut
        bloc["p_ivap"] = p_ivap
        bloc["p0_ivap"] = p0_ivap
        bloc["p1_ivap"] = p1_ivap
        bloc["p_cvap_brut"] = p_cvap_brut
        bloc["p_cvap"] = p_cvap
        bloc["p0_cvap"] = p0_cvap
        bloc["p1_cvap"] = p1_cvap
        predictions.append(bloc)

        for methode, colonne, bornes in (
            ("brut complet", "p_brut_complet", None),
            ("IVAP · brut comparable", "p_ivap_brut", None),
            ("IVAP · calibré", "p_ivap", ("p0_ivap", "p1_ivap")),
            ("CVAP · ensemble brut", "p_cvap_brut", None),
            ("CVAP · calibré", "p_cvap", ("p0_cvap", "p1_cvap")),
        ):
            b0 = bloc[bornes[0]].to_numpy() if bornes else None
            b1 = bloc[bornes[1]].to_numpy() if bornes else None
            details.append({"pli": no, "methode": methode,
                            **metriques(bloc["cible"].to_numpy(), bloc[colonne].to_numpy(),
                                       bloc["frequence_train"].to_numpy(), seuil_decision,
                                       b0, b1)})
        print(f"  pli {no}/{len(groupes_externes)} · train {len(pool):,} · "
              f"test {len(test):,} · événements {int(test['cible'].sum())} · "
              f"{time.time() - depart:.0f}s", flush=True)

    pred = pd.concat(predictions, ignore_index=True)
    y = pred["cible"].to_numpy()
    p_ref = pred["frequence_train"].to_numpy()
    resume = []
    for methode, colonne, bornes in (
        ("brut complet", "p_brut_complet", None),
        ("IVAP · brut comparable", "p_ivap_brut", None),
        ("IVAP · calibré", "p_ivap", ("p0_ivap", "p1_ivap")),
        ("CVAP · ensemble brut", "p_cvap_brut", None),
        ("CVAP · calibré", "p_cvap", ("p0_cvap", "p1_cvap")),
    ):
        b0 = pred[bornes[0]].to_numpy() if bornes else None
        b1 = pred[bornes[1]].to_numpy() if bornes else None
        resume.append({"polluant": polluant, "horizon": horizon, "seuil": seuil,
                       "coupure": str(date_coupure.date()), "methode": methode,
                       **metriques(y, pred[colonne].to_numpy(), p_ref, seuil_decision,
                                  b0, b1)})
    r = pd.DataFrame(resume)

    sortie = RACINE / f"reports/calibration_venn_abers_{polluant}.csv"
    r.to_csv(sortie, index=False)
    pd.DataFrame(details).to_csv(
        RACINE / f"reports/calibration_venn_abers_{polluant}_plis.csv", index=False)
    pred.to_csv(
        RACINE / f"reports/calibration_venn_abers_{polluant}_predictions.csv", index=False)

    print("\n" + r[["methode", "brier", "brier_skill", "log_loss",
                     "average_precision", "ece_10_equal_mass", "POD", "FAR", "CSI",
                     "largeur_va_moyenne"]].to_string(index=False), flush=True)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--seuil", type=float, default=120.0)
    p.add_argument("--coupure", default="2024-07-01")
    p.add_argument("--plis-externes", type=int, default=3)
    p.add_argument("--plis-cvap", type=int, default=3)
    p.add_argument("--part-calibration", type=float, default=0.25)
    p.add_argument("--seuil-decision", type=float, default=0.20,
                   help="point de fonctionnement figé ; ne sert jamais à l'ajustement")
    a = p.parse_args()
    raise SystemExit(main(a.polluant, a.horizon, a.seuil, a.coupure,
                          a.plis_externes, a.plis_cvap, a.part_calibration,
                          a.seuil_decision))

