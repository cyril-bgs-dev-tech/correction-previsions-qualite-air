#!/usr/bin/env python3
"""Un intervalle de prédiction dont la couverture est **mesurée**, pas promise.

Pourquoi le dossier en a besoin
---------------------------------
Le système rend une valeur nue. Atmo Occitanie publie désormais des fourchettes
d'incertitude sur ses indicateurs d'exposition. Une prévision sans incertitude ne se
branche pas sur une décision : *« 48 µg/m³ »* et *« 48 ± 3 »* ou *« 48 ± 25 »* n'appellent
pas la même action à deux unités du seuil.

La méthode, et la garantie qu'elle donne **vraiment**
------------------------------------------------------
**Régression quantile conformalisée** (Romano, Patterson & Candès, 2019) :

1. deux modèles quantiles, `q_bas` à α/2 et `q_haut` à 1−α/2, ajustés par perte pinball ;
2. sur un jeu de **calibration disjoint**, le score de non-conformité
   `r = max(q_bas − y, y − q_haut)` — positif quand la vérité sort de l'intervalle ;
3. l'intervalle final est `[q_bas − q̂, q_haut + q̂]`, où `q̂` est le quantile
   `⌈(n+1)(1−α)⌉/n` des scores de calibration.

⚠️ **La garantie suppose l'échangeabilité entre calibration et test.** Notre protocole cache
station **et** mois : elle est donc **violée par construction**. Ce script ne revendique
aucune garantie théorique — il **mesure la couverture obtenue** et la publie, ventilée.

C'est la position que R15 recommande explicitement : *« couverture empirique sous protocole
station × mois cachés »*, jamais *« intervalle valide sous tout décalage »*.

La calibration est **chronologique**, donc sans fuite et déployable
--------------------------------------------------------------------
Pour le mois `m`, les scores de non-conformité viennent des mois **antérieurs à m**
uniquement. C'est à la fois sans fuite et exactement ce qu'on ferait en service : calibrer
sur l'historique. Un calage sur le mois testé donnerait un chiffre irreproductible en
opérationnel.

Les premiers mois n'ont pas d'historique : ils sont **exclus et comptés**.

Ce qu'on publie, et pourquoi ces trois choses ensemble
-------------------------------------------------------
Un intervalle `[−∞, +∞]` couvre parfaitement et ne vaut rien. La couverture seule ne dit
donc rien ; il faut la **finesse** avec elle, et un score propre qui arbitre les deux.

* **couverture** — part des observations dans l'intervalle, cible 1−α ;
* **largeur** médiane — la finesse ;
* **score de Winkler** — règle propre qui pénalise à la fois la largeur et les sorties.

Et la ventilation, parce qu'une couverture moyenne correcte peut masquer des sous-groupes
systématiquement découverts : par typologie, par saison, par décile de concentration.

Usage : python3 scripts/intervalle_conforme.py --polluant PM10 --horizon 2
Sortie : reports/intervalle_conforme_<polluant>_h<n>.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, charger,
    colonnes_admises,
)

ALPHA = 0.10          # intervalle à 90 %
MIN_CALIBRATION = 500  # en deçà, le quantile conforme est trop bruité pour valoir mieux


def modele_quantile(alpha: float, graine: int = GRAINE):
    from lightgbm import LGBMRegressor

    defauts = {"subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8}
    return LGBMRegressor(objective="quantile", alpha=alpha, random_state=graine,
                         n_jobs=8, verbose=-1, **(defauts | DEFAUT))


def winkler(y, bas, haut, alpha: float) -> float:
    """Score de Winkler — largeur, plus une pénalité pour chaque sortie.

    Règle **propre** : elle ne peut pas être améliorée en trichant sur l'un des deux
    termes. Un intervalle immense paie sa largeur, un intervalle étroit paie ses sorties.
    """
    largeur = haut - bas
    sous = np.where(y < bas, 2 / alpha * (bas - y), 0.0)
    sur = np.where(y > haut, 2 / alpha * (y - haut), 0.0)
    return float(np.mean(largeur + sous + sur))


def main(polluant: str, horizon: int, n_spa: int, alpha: float) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, cols, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    predicteurs = base + cols_typo

    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), n_spa)
    mois = list(np.sort(d["mois"].unique()))
    echeance = "J0" if horizon == 1 else f"J+{horizon - 1}"
    print(f"{polluant} · {echeance} · {len(d):,} jours-station · {len(mois)} mois · "
          f"intervalle à {100 * (1 - alpha):.0f} %", flush=True)

    d["q_bas"] = np.nan
    d["q_haut"] = np.nan
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        m_test = (d["mois"] == m) & dans
        m_train = (d["mois"] != m) & ~dans
        te, tr = d[m_test], d[m_train]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(m_test.to_numpy())
        cible = tr["valeur"] - tr["cams_jour"]
        for nom, a in (("q_bas", alpha / 2), ("q_haut", 1 - alpha / 2)):
            mod = modele_quantile(a).fit(tr[predicteurs], cible)
            d.loc[d.index[idx], nom] = np.clip(
                te["cams_jour"].to_numpy() + mod.predict(te[predicteurs]), 0, None)
        if (i + 1) % 6 == 0:
            print(f"  {i + 1}/{len(mois)} mois · {time.time() - depart:4.0f}s", flush=True)

    e = d.dropna(subset=["q_bas", "q_haut"]).copy()
    # ⚠️ Les quantiles peuvent se croiser : un `q_bas` au-dessus de `q_haut` rendrait
    # l'intervalle vide et la couverture nulle sans raison. On les réordonne.
    croises = int((e["q_bas"] > e["q_haut"]).sum())
    if croises:
        print(f"  ⚠️ {croises:,} intervalles croisés ({100 * croises / len(e):.2f} %) — "
              f"bornes réordonnées", flush=True)
        bas = np.minimum(e["q_bas"], e["q_haut"])
        e["q_haut"] = np.maximum(e["q_bas"], e["q_haut"])
        e["q_bas"] = bas

    # ── Conformalisation chronologique — scores des mois ANTÉRIEURS seulement ──
    e = e.sort_values("jour").reset_index(drop=True)
    e["score"] = np.maximum(e["q_bas"] - e["valeur"], e["valeur"] - e["q_haut"])
    e["qhat"] = np.nan
    sans_hist = []
    for m in mois:
        hist = e[e["mois"] < m]["score"].to_numpy()
        cur = e["mois"] == m
        if len(hist) < MIN_CALIBRATION:
            sans_hist.append(m)
            continue
        n = len(hist)
        rang = min(int(np.ceil((n + 1) * (1 - alpha))), n)
        e.loc[cur, "qhat"] = float(np.sort(hist)[rang - 1])
    print(f"  {len(sans_hist)} mois sans historique de calibration, exclus", flush=True)

    c = e.dropna(subset=["qhat"]).copy()
    c["bas"] = c["q_bas"] - c["qhat"]
    c["haut"] = c["q_haut"] + c["qhat"]
    y = c["valeur"].to_numpy()
    dedans = (y >= c["bas"]) & (y <= c["haut"])
    largeur = (c["haut"] - c["bas"]).to_numpy()

    print(f"\n{'═' * 74}\nCOUVERTURE OBTENUE — cible {100 * (1 - alpha):.0f} %, "
          f"{len(c):,} prédictions\n{'═' * 74}")
    print(f"  avant conformalisation : {100 * ((y >= c['q_bas']) & (y <= c['q_haut'])).mean():5.1f} %"
          f" · largeur médiane {np.median(c['q_haut'] - c['q_bas']):5.1f} µg/m³")
    print(f"  APRÈS conformalisation : {100 * dedans.mean():5.1f} %"
          f" · largeur médiane {np.median(largeur):5.1f} µg/m³")
    print(f"  score de Winkler       : {winkler(y, c['bas'].to_numpy(), c['haut'].to_numpy(), alpha):7.2f}")

    lignes = [{"polluant": polluant, "horizon": horizon, "groupe": "ensemble",
               "n": len(c), "couverture_pct": 100 * dedans.mean(),
               "largeur_mediane": float(np.median(largeur)),
               "winkler": winkler(y, c["bas"].to_numpy(), c["haut"].to_numpy(), alpha)}]

    # ── La ventilation : une couverture moyenne juste peut cacher des trous ────
    print(f"\n  ── ventilation — une moyenne correcte peut masquer un sous-groupe ──")
    c["decile"] = pd.qcut(c["valeur"], 10, labels=False, duplicates="drop")
    c["saison"] = c["jour"].dt.month % 12 // 3
    for nom, cle in (("type de station", "type_station"), ("décile d'observation", "decile"),
                     ("saison", "saison")):
        if cle not in c:
            continue
        g = c.assign(_ok=dedans, _l=largeur).groupby(cle).agg(
            n=("valeur", "size"), couv=("_ok", "mean"), larg=("_l", "median"))
        g = g[g["n"] >= 200]
        if g.empty:
            continue
        print(f"\n    {nom}")
        for k, r in g.iterrows():
            drapeau = "  ⚠️" if abs(100 * r["couv"] - 100 * (1 - alpha)) > 5 else ""
            print(f"      {str(k)[:22]:24s} {int(r['n']):7,d} · {100 * r['couv']:5.1f} % · "
                  f"largeur {r['larg']:5.1f}{drapeau}")
            lignes.append({"polluant": polluant, "horizon": horizon, "groupe": f"{nom}={k}",
                           "n": int(r["n"]), "couverture_pct": 100 * r["couv"],
                           "largeur_mediane": float(r["larg"])})

    print(f"\n⚠️ La garantie théorique de la régression quantile conformalisée suppose")
    print(f"   l'échangeabilité, que ce protocole viole en cachant station ET mois.")
    print(f"   Ce qui est publié est une **couverture empirique mesurée**, pas une garantie.")

    sortie = RACINE / f"reports/intervalle_conforme_{polluant}_h{horizon}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--alpha", type=float, default=ALPHA)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux, n.alpha))
