#!/usr/bin/env python3
"""Le seul levier restant : gagner de l'**information**, pas du réglage.

Pourquoi ce script, et pourquoi maintenant
--------------------------------------------
`decomposition_information.py` a établi deux choses sur les quatre polluants :

* notre modèle est à **0,1 à 0,6 % de son propre plancher** `σy·√(1−r²)` ;
* ce plancher est **sous la RMSE de tous les concurrents**.

La première tue une famille entière d'idées. Une perte personnalisée agit sur deux
leviers : la **forme** de la fonction ajustée — donc `r` — et le **point de
fonctionnement** — biais et amplitude. Le second est libre et déjà optimal. Donc **toute
perte qui ne fait que déplacer le point de fonctionnement ne peut rien apporter** :
pinball, pondération des classes rares, coût asymétrique. Le projet l'avait mesuré comme
nul sans savoir pourquoi ; on le sait désormais, et on cesse d'y revenir.

Reste une seule question ouverte : **peut-on augmenter `r` ?**

Ce qui pourrait, en principe, augmenter `r`
---------------------------------------------
La perte L2 estime `E[y|x]`, qui **maximise la corrélation** parmi toutes les fonctions de
`x` — c'est la projection L2. Si le modèle estimait parfaitement cette espérance, aucune
perte ne pourrait faire mieux et ce script serait inutile.

Mais l'estimation est finie, et la L2 pondère chaque ligne à proportion de sa **variance de
bruit**. En qualité de l'air, l'erreur est plutôt **multiplicative** qu'additive : une
journée à 120 µg/m³ porte bien plus de bruit absolu qu'une journée à 12. La L2 sur résidu
brut consacre donc sa capacité aux lignes les plus bruitées. Une **stabilisation de
variance** — logarithme, racine, ratio — redistribue cette capacité vers le signal.

C'est la seule famille qui peut déplacer le plancher. Les sept variantes ci-dessous la
balaient, plus deux témoins qui doivent **échouer** si le raisonnement est juste.

Le critère de succès, et il n'est pas la RMSE
-----------------------------------------------
La RMSE confond information et réglage : une variante peut gagner en RMSE en se
recalibrant mieux, sans rien apprendre de plus. **Le juge est le plancher** — donc `r`. Une
variante qui baisse le plancher a gagné de l'information ; toute autre n'a bougé qu'un
paramètre libre, et ce paramètre était déjà réglé.

⚠️ Sélectionner la gagnante sur ces mêmes chiffres serait la choisir sur son test. Ce
script **rapporte toutes les variantes** ; une gagnante n'est retenue que si elle gagne
aussi sur un second polluant, ce qui est le rôle de `--polluant`.

Usage  : python3 scripts/repousser_le_plancher.py --polluant NO2 --horizon 2
Sortie : reports/repousser_le_plancher_<polluant>_h<n>.csv
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
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, charger, colonnes_admises,
)
from tableau_comparatif import NOM_POLLUANT, classe  # noqa: E402

EPS = 1.0     # µg/m³ — décale les cibles positives loin de zéro sans peser sur l'échelle


def params_perte(objectif: str, cible: np.ndarray) -> dict:
    """Les paramètres d'échelle d'une perte, **calculés sur la cible**.

    ⚠️ LightGBM prend `alpha` comme le **delta** de Huber — le seuil en deçà duquel la
    perte reste quadratique — et son défaut vaut **0,9**. Pour un résidu de NO₂ d'écart-type
    ≈ 20 µg/m³, cela place le coude à 4 % de l'écart-type : la perte est alors linéaire
    presque partout, donc une L1 mal conditionnée, et son résultat ne mesure plus rien de
    la robustesse. Mesuré le 03/08 : −3,10 % de plancher sur NO₂ contre +2,77 % sur PM10,
    incohérence qui trahissait le paramètre et non la méthode.

    On le pose donc à `1,345·σ̂`, le choix classique qui retient 95 % d'efficacité sous
    normalité, avec `σ̂` estimé par l'écart absolu médian — robuste, contrairement à
    l'écart-type qui serait tiré par les aberrations qu'on cherche justement à borner.
    """
    if objectif != "huber":
        return {}
    c = cible[np.isfinite(cible)]
    if c.size < 100:
        return {}
    sigma = 1.4826 * float(np.median(np.abs(c - np.median(c))))
    return {"alpha": float(max(1.345 * sigma, 1e-3))}


def _modele(objectif: str, params: dict, cible: np.ndarray | None = None):
    from lightgbm import LGBMRegressor

    defauts = {"subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8}
    extra = params_perte(objectif, cible) if cible is not None else {}
    return LGBMRegressor(objective=objectif, random_state=GRAINE, n_jobs=8, verbose=-1,
                         **(defauts | params | extra))


# ── Les variantes ────────────────────────────────────────────────────────────
# Chacune est (cible depuis y et l'ancre a) → (retour depuis la prédiction p et a).
# La transformation inverse doit être **exacte**, jamais approchée : une inverse fausse
# se lit comme une perte d'information et condamnerait une variante saine.
VARIANTES: dict[str, tuple[str, str, callable, callable]] = {
    "① résidu · L2 (référence)": (
        "regression", "la perte actuelle du projet",
        lambda y, a: y - a, lambda p, a: a + p),
    "② résidu · Huber": (
        "huber", "robuste aux aberrations d'entraînement",
        lambda y, a: y - a, lambda p, a: a + p),
    "③ résidu · L1 (médiane)": (
        "regression_l1", "témoin — estime la MÉDIANE, doit perdre en r",
        lambda y, a: y - a, lambda p, a: a + p),
    "④ log-ratio": (
        "regression", "erreur multiplicative — stabilise la variance",
        lambda y, a: np.log((y + EPS) / (a + EPS)),
        lambda p, a: (a + EPS) * np.exp(np.clip(p, -6, 6)) - EPS),
    "⑤ racine": (
        "regression", "stabilise la variance des positifs asymétriques",
        lambda y, a: np.sqrt(y) - np.sqrt(a),
        lambda p, a: np.clip(np.sqrt(a) + p, 0, None) ** 2),
    "⑥ Tweedie sur la valeur": (
        "tweedie", "variance ∝ moyenne^p — l'ancre reste une variable",
        lambda y, a: np.clip(y, 0, None), lambda p, a: p),
    "⑦ Gamma sur le ratio": (
        "gamma", "variance ∝ moyenne² — le cas multiplicatif pur",
        lambda y, a: (y + EPS) / (a + EPS), lambda p, a: p * (a + EPS) - EPS),
}


def plancher(y: np.ndarray, x: np.ndarray) -> tuple[float, float, float, float]:
    """r, σx/σy, RMSE, plancher σy·√(1−r²)."""
    r = float(np.corrcoef(y, x)[0, 1])
    sy = float(y.std())
    return (r, float(x.std()) / sy, float(np.sqrt(np.mean((x - y) ** 2))),
            sy * np.sqrt(max(1 - r ** 2, 0.0)))


def main(polluant: str, horizon: int, n_spa: int) -> int:
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
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")
    predicteurs = base + list(cols_typo)

    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    mois = np.sort(d["mois"].unique())
    ech = "J0" if horizon == 1 else f"J+{horizon - 1}"
    print(f"{NOM_POLLUANT[polluant]} · {ech} · {len(d):,} jours-station · "
          f"{len(mois)} mois · {len(VARIANTES)} variantes", flush=True)

    pred = {k: np.full(len(d), np.nan) for k in VARIANTES}
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        mt, mr = (d["mois"] == m) & dans, (d["mois"] != m) & ~dans
        te, tr = d[mt], d[mr]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(mt.to_numpy())
        ya, aa = tr["valeur"].to_numpy(), tr["cams_jour"].to_numpy()
        ae = te["cams_jour"].to_numpy()
        for nom, (obj, _, vers, retour) in VARIANTES.items():
            cible = vers(ya, aa)
            fini = np.isfinite(cible)
            if obj in ("gamma", "tweedie") and (cible[fini] <= 0).any():
                fini &= cible > 0        # ces pertes exigent une cible strictement positive
            if fini.sum() < 1000:
                continue
            mod = _modele(obj, DEFAUT, cible[fini]).fit(tr[predicteurs][fini],
                                                        cible[fini])
            pred[nom][idx] = np.clip(retour(mod.predict(te[predicteurs]), ae), 0, None)
        if (i + 1) % 9 == 0:
            print(f"  {i + 1}/{len(mois)} mois · {(time.time() - depart) / 60:.1f} min",
                  flush=True)

    ok = np.ones(len(d), bool)
    for nom, v in pred.items():
        if not np.isfinite(v).any():
            raise SystemExit(f"la variante « {nom} » n'a rien produit")
        ok &= np.isfinite(v)
    y = d["valeur"].to_numpy()[ok]
    crit = classe(y, polluant) >= 3
    n_crit = int(crit.sum())

    # ⑧ La moyenne des variantes — une variante à part entière. Moyenner des estimateurs
    # décorrélés réduit la variance d'estimation, donc peut relever `r` sans qu'aucune
    # variante prise seule n'y parvienne. C'est le seul « gain gratuit » du lot.
    empilees = np.column_stack([pred[k][ok] for k in VARIANTES])
    resultats = {k: pred[k][ok] for k in VARIANTES}
    resultats["⑧ moyenne des sept"] = empilees.mean(axis=1)

    ref = plancher(y, resultats["① résidu · L2 (référence)"])[3]
    print(f"\n{'═' * 102}\nREPOUSSER LE PLANCHER · {ok.sum():,} prédictions · "
          f"station ET mois cachés\n{'═' * 102}")
    print(f"  {'variante':32s} {'r':>6s} {'σx/σy':>7s} {'RMSE':>7s} {'plancher':>9s} "
          f"{'Δ plancher':>11s} {'détect.':>8s}")
    lignes = []
    for nom, x in resultats.items():
        r, s, rm, pl = plancher(y, x)
        vues = int(crit[np.argsort(-x, kind="stable")[:n_crit]].sum())
        marque = " ⬅" if pl < ref - 1e-9 else ""
        print(f"  {nom:32s} {r:6.4f} {s:7.3f} {rm:7.3f} {pl:9.4f} "
              f"{100 * (1 - pl / ref):+10.2f}% {vues:8d}{marque}")
        lignes.append({"polluant": polluant, "horizon": horizon, "variante": nom,
                       "r": r, "sigma_ratio": s, "rmse": rm, "plancher": pl,
                       "delta_plancher_pct": 100 * (1 - pl / ref),
                       "detections_budget_egal": vues, "n_critiques": n_crit,
                       "n": int(ok.sum())})

    t = pd.DataFrame(lignes)
    gagnantes = t[t["delta_plancher_pct"] > 0.5].sort_values("plancher")
    print(f"\n  Juge : la colonne `plancher` = σy·√(1−r²). Elle seule mesure "
          f"l'INFORMATION.")
    print(f"  Une variante qui gagne en RMSE sans baisser le plancher n'a rien appris :")
    print(f"  elle a déplacé un paramètre libre, et ce paramètre était déjà réglé.")
    if gagnantes.empty:
        print(f"\n  → AUCUNE variante ne baisse le plancher de plus de 0,5 %.")
        print(f"    La L2 sur résidu estime déjà `E[y|x]` aussi bien que cette classe de")
        print(f"    modèles le permet. Le plancher n'est pas un défaut de perte : c'est")
        print(f"    la limite de l'information contenue dans les variables disponibles.")
        print(f"    → Chercher des VARIABLES, pas des pertes.")
    else:
        print(f"\n  → {len(gagnantes)} variante(s) baissent le plancher :")
        for _, r in gagnantes.iterrows():
            print(f"      {r['variante']:32s} {r['delta_plancher_pct']:+.2f} %")
        print(f"\n  ⚠️ Résultat à confirmer sur un SECOND polluant avant d'être retenu.")
        print(f"     Choisi ici, il serait sélectionné sur son propre test.")
    temoin = t[t["variante"].str.contains("L1")]
    if not temoin.empty:
        dt = float(temoin["delta_plancher_pct"].iloc[0])
        etat = "perd comme attendu" if dt < 0 else "GAGNE — le raisonnement est à revoir"
        print(f"\n  Témoin ③ L1/médiane : {dt:+.2f} % — {etat}.")

    sortie = RACINE / f"reports/repousser_le_plancher_{polluant}_h{horizon}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
