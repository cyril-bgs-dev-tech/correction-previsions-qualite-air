#!/usr/bin/env python3
"""Rendre à la prédiction l'amplitude que la perte quadratique lui a retirée.

Le problème, diagnostiqué avant d'être traité
-----------------------------------------------
Sur les jours de dépassement PM10, le rang percentile moyen de notre prédiction vaut
**0,872** — contre 0,500 pour un prédicteur sans information. Le classement est donc bon.
Mais l'amplitude médiane prédite ces jours-là vaut **51 % de l'observé** : 28,6 µg/m³ pour
56,4 mesurés. Rien ne franchit le seuil de 50 parce que rien ne s'en approche.

Trois tentatives d'ajouter de l'information ont échoué — contexte spatial du champ CAMS,
ancrage sur le biais glissant, et l'hypothèse d'un écrasement de queue, réfutée. Ce n'est
pas un défaut d'information : c'est un défaut de **mise à l'échelle**.

Et ce n'est pas un bogue. Une perte quadratique vise l'**espérance conditionnelle**, qui
est structurellement plus proche de la climatologie que de la vérité. Le modèle fait
exactement ce qu'on lui demande ; c'est la demande qui ne convient pas à la détection.

La correction, et pourquoi elle ne fuit pas
---------------------------------------------
**Cartographie de quantiles** : on remplace `ŷ` par `F_obs⁻¹(F_préd(ŷ))`, c'est-à-dire on
transporte la prédiction sur la distribution des observations. Le **rang est préservé
exactement** — donc rien ne change à budget d'alerte constant — mais les franchissements de
seuil deviennent ceux qu'impose la vraie distribution.

⚠️ Les deux fonctions de répartition sont estimées **uniquement sur les mois antérieurs**
au mois évalué. C'est à la fois sans fuite et **exactement ce qu'on ferait en déploiement** :
calibrer sur l'historique disponible. Un calage sur le mois testé donnerait un chiffre que
personne ne pourrait reproduire en opérationnel.

Le premier mois n'a pas d'historique : il est **exclu**, et le nombre de mois écartés est
affiché plutôt que dissimulé.

⚠️ Ce n'est pas « mieux », c'est **un autre point de fonctionnement**
----------------------------------------------------------------------
La recalibration augmente les détections et **dégrade la précision** — mécaniquement, car
elle émet davantage d'alertes. Aucun score unique ne tranche entre les deux ; c'est une
décision qui dépend du coût relatif d'une alerte manquée et d'une fausse alerte.

D'où la **courbe de valeur économique relative** (Murphy 1977, Richardson 2000), qui est le
cadre standard en météorologie :

    V(α) = (E_clim − E_prévision) / (E_clim − E_parfait)

où `α = C/L` est le rapport du coût de l'action à la perte subie en cas d'événement non
annoncé. `V > 0` signifie « mieux que la meilleure stratégie climatologique pour cet
utilisateur ». Un système peut dominer sur une plage de `α` sans dominer partout — et le
dire ainsi est plus informatif que d'imposer un seuil unique.

Usage : python3 scripts/recalibrer_amplitude.py --polluant PM10
Sortie : reports/recalibrage_<polluant>.csv · reports/valeur_economique_<polluant>.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]

SEUILS = {"PM10": (50.0, "seuil d'information français"),
          "PM25": (50.0, "AUCUN seuil français — repère indicatif"),
          "O3": (120.0, "valeur cible européenne — PAS le seuil 180"),
          "NO2": (200.0, "seuil d'information français")}


def cartographie_quantiles(pred_hist: np.ndarray, obs_hist: np.ndarray,
                           pred: np.ndarray) -> np.ndarray:
    """`F_obs⁻¹(F_préd(ŷ))` — transport de la prédiction sur la loi des observations.

    Estimée sur l'historique seul. Le rang est préservé exactement : deux prédictions
    ordonnées le restent, donc **rien ne change à budget d'alerte constant**. Seuls les
    franchissements de seuil bougent.
    """
    if len(pred_hist) < 500 or len(obs_hist) < 500:
        return np.full_like(pred, np.nan)
    # Rang de chaque prédiction dans l'historique des prédictions, puis quantile
    # correspondant de l'historique des observations.
    ph = np.sort(pred_hist)
    oh = np.sort(obs_hist)
    u = np.searchsorted(ph, pred, side="left") / max(len(ph), 1)
    u = np.clip(u, 0.0, 1.0)
    return np.quantile(oh, u)


def contingence(v: np.ndarray, a: np.ndarray) -> dict:
    tp, fp, fn, tn = (int((v & a).sum()), int((~v & a).sum()),
                      int((v & ~a).sum()), int((~v & ~a).sum()))
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "alertes": tp + fp,
            "POD": tp / (tp + fn) if tp + fn else np.nan,
            "precision": tp / (tp + fp) if tp + fp else np.nan,
            "CSI": tp / (tp + fp + fn) if tp + fp + fn else np.nan,
            "biais_frequence": (tp + fp) / (tp + fn) if tp + fn else np.nan}


def valeur_economique(v: np.ndarray, a: np.ndarray, alphas: np.ndarray) -> np.ndarray:
    """Valeur économique relative, pour une gamme de rapports coût/perte.

    Formulation de Murphy (1977) telle que présentée par Richardson (2000). `V > 0` :
    mieux que la meilleure stratégie climatologique — n'agir jamais si `α > p`, agir
    toujours sinon.
    """
    n = len(v)
    p = v.mean()
    h = (v & a).sum() / n          # succès
    f = (~v & a).sum() / n         # fausses alertes
    m = (v & ~a).sum() / n         # manqués
    out = np.empty_like(alphas)
    for i, al in enumerate(alphas):
        e_prev = al * (h + f) + m                      # dépense, en unités de L
        e_clim = min(al, p)
        e_parf = al * p
        out[i] = (e_clim - e_prev) / (e_clim - e_parf) if e_clim != e_parf else np.nan
    return out


def main(polluant: str, typologie: bool, horizon: int = 1) -> int:
    suff = f"_h{horizon}" + ("_typo" if typologie else "")
    f = RACINE / f"data/interim/oof/oof_{polluant}{suff}.parquet"
    if not f.exists():
        raise SystemExit(f"absent : {f.name} — lancer oof_double_aveugle.py d'abord")
    o = pd.read_parquet(f)
    d = o[o["epreuve"] == "double aveugle"].copy()
    d["jour"] = pd.to_datetime(d["jour"])
    d["mois"] = d["jour"].dt.strftime("%Y-%m")
    d = d.sort_values("jour").reset_index(drop=True)
    seuil, statut = SEUILS[polluant]

    # ── Recalibration mois par mois, sur l'historique ANTÉRIEUR uniquement ────────
    d["pred_qm"] = np.nan
    d["cams_qm"] = np.nan
    mois = sorted(d["mois"].unique())
    sans_historique = []
    for m in mois:
        hist = d[d["mois"] < m]
        cur = d["mois"] == m
        if len(hist) < 500:
            sans_historique.append(m)
            continue
        d.loc[cur, "pred_qm"] = cartographie_quantiles(
            hist["pred"].to_numpy(), hist["valeur"].to_numpy(),
            d.loc[cur, "pred"].to_numpy())
        d.loc[cur, "cams_qm"] = cartographie_quantiles(
            hist["cams_jour"].to_numpy(), hist["valeur"].to_numpy(),
            d.loc[cur, "cams_jour"].to_numpy())

    print(f"{polluant} · {len(d):,} jours-station · seuil {seuil:.0f} µg/m³ ({statut})")
    print(f"  {len(sans_historique)} mois sans historique, exclus : "
          f"{', '.join(sans_historique) if sans_historique else 'aucun'}")
    e = d.dropna(subset=["pred_qm", "cams_qm"]).reset_index(drop=True)
    o_v = e["valeur"].to_numpy()
    v = o_v > seuil
    print(f"  {len(e):,} évalués · {int(v.sum())} dépassements ({100 * v.mean():.2f} %)")
    if v.sum() < 30:
        print(f"  ⚠️ moins de 30 dépassements — mesuré, pas conclu.")

    systemes = {"CAMS brut": e["cams_jour"].to_numpy(),
                "CAMS recalibré": e["cams_qm"].to_numpy(),
                "modèle": e["pred"].to_numpy(),
                "modèle RECALIBRÉ": e["pred_qm"].to_numpy()}

    print(f"\n{'═' * 76}\n① AMPLITUDE ET DÉTECTION AU SEUIL RÉGLEMENTAIRE\n{'═' * 76}")
    print(f"  {'système':20s} {'RMSE':>7s} {'SDR':>6s} {'alertes':>8s} {'TP':>5s} "
          f"{'POD':>7s} {'préc.':>7s} {'CSI':>7s}")
    lignes = []
    for nom, x in systemes.items():
        c = contingence(v, x > seuil)
        rmse = float(np.sqrt(np.mean((x - o_v) ** 2)))
        sdr = float(x.std() / o_v.std())
        print(f"  {nom:20s} {rmse:7.3f} {sdr:6.3f} {c['alertes']:8d} {c['TP']:5d} "
              f"{c['POD']:7.3f} {c['precision']:7.3f} {c['CSI']:7.3f}")
        lignes.append({"polluant": polluant, "systeme": nom, "rmse": rmse, "sdr": sdr,
                       "seuil": seuil, "n": len(e), **c})
    pd.DataFrame(lignes).to_csv(RACINE / f"reports/recalibrage_{polluant}.csv", index=False)

    # ── ② Valeur économique relative — pour quels utilisateurs le système sert ────
    alphas = np.concatenate([np.linspace(0.002, 0.05, 25), np.linspace(0.06, 0.5, 23)])
    courbes = {nom: valeur_economique(v, x > seuil, alphas)
               for nom, x in systemes.items()}
    tab = pd.DataFrame({"alpha_cout_sur_perte": alphas, **courbes})
    tab.to_csv(RACINE / f"reports/valeur_economique_{polluant}.csv", index=False)

    print(f"\n{'═' * 76}\n② VALEUR ÉCONOMIQUE RELATIVE — V(α), α = coût d'action / perte\n"
          f"{'═' * 76}")
    print(f"  taux climatologique de l'événement : {v.mean():.4f}")
    print(f"  {'α':>7s}  " + "  ".join(f"{n[:14]:>14s}" for n in systemes))
    for a in (0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40):
        i = int(np.argmin(np.abs(alphas - a)))
        print(f"  {alphas[i]:7.3f}  " + "  ".join(
            f"{courbes[n][i]:14.3f}" for n in systemes))
    for nom in systemes:
        util = alphas[np.nan_to_num(courbes[nom]) > 0]
        if util.size:
            i = int(np.nanargmax(courbes[nom]))
            print(f"  {nom:20s} V>0 pour α ∈ [{util.min():.3f} ; {util.max():.3f}] · "
                  f"maximum {np.nanmax(courbes[nom]):.3f} en α={alphas[i]:.3f}")
        else:
            print(f"  {nom:20s} V ≤ 0 partout — aucun utilisateur n'y gagne")

    print(f"\n⚠️ La recalibration n'est PAS « meilleure » : elle échange de la précision")
    print(f"   contre du rappel. La courbe ci-dessus dit **pour qui** l'échange est bon.")
    print(f"\nÉcrit : reports/recalibrage_{polluant}.csv · "
          f"reports/valeur_economique_{polluant}.csv")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--sans-typologie", action="store_true")
    a.add_argument("--horizon", type=int, default=1,
                   help="1 = J0 (échéances 1-24 h) · 2 = J+1 réel (25-48 h)")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, not n.sans_typologie, n.horizon))
