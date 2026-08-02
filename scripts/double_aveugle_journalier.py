#!/usr/bin/env python3
"""La généralisation temporelle, refaite sur la configuration retenue — et pli par pli.

Pourquoi rejouer ce test
------------------------
Le score temporel du projet (gain moyen +14,4 %, **pire pli −14,6 %**, et **−24,9 %** en
double aveugle) a été mesuré sur une configuration **abandonnée depuis** : cible horaire,
hyperparamètres par défaut. La configuration retenue apprend la grandeur réglementaire du
jour avec une capacité triplée. Rien ne dit que le diagnostic tienne encore, et deux effets
opposés sont en jeu :

- l'agrégation journalière **réduit le bruit** et devrait resserrer les écarts entre mois ;
- la capacité triplée **augmente la latitude** d'apprendre des relations propres à la
  période d'entraînement.

Le sens du résultat est donc indécidable a priori — d'où la mesure.

**Ce que l'ancien script ne faisait pas**, et qui a manqué toute la nuit : journaliser le
**détail par pli**. Un « pire pli à −14,6 % » sans savoir *quel mois* échoue n'autorise
aucun diagnostic. Ici chaque pli est écrit avec son mois, son effectif et son gain.

L'agrégation journalière rend ce test abordable : 134 000 exemples au lieu de 3,2 M, donc
39 ajustements en quelques minutes là où l'horaire en demandait cent.

**Trois épreuves, du plus facile au plus dur** — chacune cache davantage :

1. **spatiale** — stations jamais vues (le point fort du projet) ;
2. **temporelle** — mois jamais vu, toutes stations connues ;
3. **double aveugle** — stations *et* mois cachés simultanément.

Usage : python3 scripts/double_aveugle_journalier.py [--polluant O3]
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

from aq.eval import comparaison as cmp  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import DEFAUT, REGLE  # noqa: E402

GRAINE = 20260730

# ── Quatre configurations, choisies pour SÉPARER deux effets confondus ──────────
#
# Le 02/08/2026 a montré que la production tourne à **400 arbres** alors que l'arrêt anticipé
# en réclame ~3 300, et qu'une étude Optuna de 200 essais gagne +5,25 % sur la validation
# interne. Mais les deux gains ont été mesurés sur l'axe SPATIAL, précisément celui où ce
# script a déjà établi que le réglage **nuit** : double aveugle +4,02 % au défaut contre
# **+1,48 % au réglé**.
#
# Les deux effets sont donc à démêler, et une seule des quatre lignes ci-dessous peut le
# faire : `défaut + arbres` porte les hyperparamètres de production avec la seule capacité
# débridée. L'écart `défaut → défaut + arbres` isole le nombre d'arbres ; l'écart
# `défaut + arbres → optuna` isole le réglage proprement dit.
DEFAUT_ARBRES = dict(DEFAUT) | {"n_estimators": 3000}

# Meilleur essai admissible de `reports/optuna/mos_O3_lgbm.db` (201 essais complets,
# 94 élagués). ⚠️ Le nombre d'arbres est la moyenne des trois plis retenus par l'arrêt
# anticipé — dont **un a touché le plafond de 4 000**, donc la recherche était censurée à
# la borne et l'optimum vrai est peut-être au-delà.
OPTUNA = {"n_estimators": 3700, "learning_rate": 0.017037905389041038,
          "num_leaves": 397, "min_child_samples": 8, "min_split_gain": 0.15549171859083297,
          "reg_alpha": 0.227525239112976, "reg_lambda": 0.10972659657317346,
          "subsample": 0.9737952627416867, "colsample_bytree": 0.5562047385105412,
          "max_bin": 511}


def ajuster(params: dict, tr: pd.DataFrame, te: pd.DataFrame,
            colonnes: list[str], ancre: str) -> np.ndarray:
    from lightgbm import LGBMRegressor

    # ⚠️ `subsample` et `colsample_bytree` étaient écrits **en dur** puis `params` déballé
    # par-dessus : toute configuration portant ses propres valeurs — c'est le cas de tout
    # candidat issu d'une recherche — levait une collision d'arguments. On fusionne, en
    # laissant `params` gagner.
    defauts = {"subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8}
    modele = LGBMRegressor(random_state=GRAINE, n_jobs=8, verbose=-1,
                           **(defauts | params))
    modele.fit(tr[colonnes], tr["valeur"] - tr[ancre])
    return np.clip(te[ancre].to_numpy() + modele.predict(te[colonnes]), 0, None)


def gain(observe, cams, predit) -> float:
    rc = float(np.sqrt(np.mean((cams - observe) ** 2)))
    rm = float(np.sqrt(np.mean((predit - observe) ** 2)))
    return 100.0 * (1.0 - rm / rc) if rc > 0 else np.nan


def epreuve(d: pd.DataFrame, colonnes: list[str], ancre: str, params: dict,
            nom: str, plis: list[tuple[str, pd.Series, pd.Series]]) -> tuple[dict, list[dict]]:
    """Joue une épreuve, et **rend le détail de chaque pli** — pas seulement l'agrégat.

    Chaque pli porte **deux** masques, test et entraînement, et non un seul dont on
    prendrait le complément. C'est indispensable au double aveugle : son test est
    l'intersection « mois M **et** stations G », dont le complément contient encore le
    mois M sur d'autres stations et les stations G sur d'autres mois. Entraîner sur ce
    complément rendrait l'épreuve **plus facile** que les deux épreuves simples — ce qui
    s'est produit, et se voyait à un double aveugle meilleur que la validation
    temporelle, résultat impossible.
    """
    details, obs, cams, pred = [], [], [], []
    depart = time.time()

    for etiquette, masque_test, masque_train in plis:
        te = d[masque_test]
        tr = d[masque_train]
        if len(te) < 200 or tr.empty:
            continue
        p = ajuster(params, tr, te, colonnes, ancre)
        g = gain(te["valeur"].to_numpy(), te[ancre].to_numpy(), p)
        details.append({"epreuve": nom, "pli": etiquette, "n": len(te), "gain_pct": g})
        obs.append(te["valeur"].to_numpy()); cams.append(te[ancre].to_numpy()); pred.append(p)

    gains = np.array([x["gain_pct"] for x in details])
    global_ = gain(np.concatenate(obs), np.concatenate(cams), np.concatenate(pred))
    pire = details[int(np.argmin(gains))] if len(gains) else {}

    print(f"  {nom:16s} {len(details):2d} plis · gain {global_:+6.2f} % · "
          f"étendue {gains.min():+6.1f} à {gains.max():+6.1f} · σ {gains.std():4.1f} · "
          f"pire = {pire.get('pli', '?')} · {time.time() - depart:4.0f}s", flush=True)

    return ({"epreuve": nom, "n_plis": len(details), "gain_pct": global_,
             "gain_min": float(gains.min()), "gain_max": float(gains.max()),
             "ecart_type": float(gains.std()), "pire_pli": pire.get("pli"),
             "n_plis_negatifs": int((gains < 0).sum())}, details)


def main(polluant: str, horizon: int, n_plis_spatiaux: int,
         typologie: bool = False, rapide: bool = False) -> int:
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, colonnes, grandeur)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    # ── La typologie de station, en option ──────────────────────────────────────
    #
    # Mesurée le 02/08/2026 à **+16,5 % sur NO₂** en validation spatiale et +12,9 % sous
    # blocage — le seul levier retenu de la nuit. Mais **jamais testée sur l'axe qui
    # correspond au déploiement**, et cette nuit a montré trois fois qu'un gain spatial ne
    # survit pas nécessairement au double aveugle : la capacité du modèle y passe de +3,31 %
    # à −1,07 %, et la domination en détection contre le produit officiel s'y inverse de
    # ×4,1 à ×0,85.
    #
    # Un levier qu'on s'apprête à déployer doit être mesuré dans les conditions du
    # déploiement, sinon on déploie un chiffre d'axe.
    if typologie:
        from optuna_mos import typologie as charger_typologie  # noqa: PLC0415

        typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
        avant = len(d)
        d = d.merge(typo, on="station_id", how="left")
        if len(d) != avant:
            raise SystemExit(f"la jointure typologie a changé le nombre de lignes : "
                             f"{avant:,} → {len(d):,}")
        if d[cols_typo].isna().any().any():
            raise SystemExit("typologie manquante après jointure — ne pas imputer")
        predicteurs = predicteurs + cols_typo
        print(f"  + typologie de station : {len(cols_typo)} colonnes "
              f"({', '.join(cols_typo)})", flush=True)

    print(f"{polluant} · {grandeur} · {len(d):,} jours-station · "
          f"{d['station_id'].nunique()} stations · {d['mois'].nunique()} mois\n", flush=True)

    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), n_plis_spatiaux)
    mois = np.sort(d["mois"].unique())

    plis_spatiaux = [(f"stations-{i+1}", d["station_id"].isin(g), ~d["station_id"].isin(g))
                     for i, g in enumerate(groupes)]
    plis_temporels = [(m, d["mois"] == m, d["mois"] != m) for m in mois]
    # Double aveugle : le mois **et** un groupe de stations cachés ensemble. Le groupe
    # tourne avec le mois pour ne pas privilégier une partition particulière.
    #
    # L'entraînement exclut **tout ce qui partage le mois ou la station** — et non le
    # simple complément du test. Sans cela le modèle verrait le mois caché sur d'autres
    # stations et les stations cachées sur d'autres mois : l'épreuve serait plus facile
    # que chacune des deux prises séparément.
    plis_double = []
    for i, m in enumerate(mois):
        dans_groupe = d["station_id"].isin(groupes[i % n_plis_spatiaux])
        plis_double.append((f"{m}+s{i % n_plis_spatiaux + 1}",
                            (d["mois"] == m) & dans_groupe,
                            (d["mois"] != m) & ~dans_groupe))

    # ⚠️ `optuna` est **mesuré sans apport** — il perd ou égale `défaut` sur 4 polluants
    # × 2 tailles de corpus × avec et sans typologie, pour 8 à 18× le temps de calcul. La
    # cause est lue dans `optuna_mos.py` : la recherche partitionne **par station seule**,
    # sans blocage temporel, donc son critère ne représente pas la tâche cible (Roberts
    # et al. 2017 ; Cawley & Talbot 2010). Le garder par défaut coûtait 80 % du temps du
    # lot pour un point qu'on sait inutile.
    configs = (("défaut", DEFAUT), ("réglé", REGLE),
               ("défaut + arbres", DEFAUT_ARBRES), ("optuna", OPTUNA))
    if rapide:
        configs = configs[:1]
        print("  mode rapide : seule la configuration de production est évaluée",
              flush=True)

    resume, detail, echecs = [], [], []
    for nom_params, params in configs:
        print(f"— hyperparamètres {nom_params} —", flush=True)
        for nom, plis in (("spatiale", plis_spatiaux),
                          ("temporelle", plis_temporels),
                          ("double aveugle", plis_double)):
            # ⚠️ **Une configuration qui échoue ne doit pas emporter tout le lot.**
            # Le 02/08/2026, les PM10 ont perdu leurs quatre configurations parce que la
            # troisième a levé une `UnicodeDecodeError` **dans LightGBM lui-même**
            # (`model_to_string`, tampon de 14 Mo sur un modèle de 3 000 arbres). Les deux
            # premières avaient abouti ; leurs chiffres ont été perdus faute d'écriture.
            #
            # L'échec est **nommé et relayé**, jamais avalé — c'est la différence avec un
            # `except: continue`, que la règle 2 bis interdit. Ce qui a réussi est écrit.
            try:
                r, det = epreuve(d, predicteurs, "cams_jour", params, nom, plis)
            except Exception as e:  # noqa: BLE001 — on veut la config, l'épreuve ET la cause
                print(f"  ⚠️ {nom_params} · {nom} · ÉCHEC {type(e).__name__}: "
                      f"{str(e)[:120]}", flush=True)
                echecs.append({"reglage": nom_params, "epreuve": nom,
                               "cause": f"{type(e).__name__}: {str(e)[:200]}"})
                continue
            r["reglage"] = nom_params
            resume.append(r)
            detail += [{**x, "reglage": nom_params} for x in det]
        print(flush=True)

    if echecs:
        print(f"⚠️ {len(echecs)} épreuve(s) en échec — les autres sont écrites :", flush=True)
        for e in echecs:
            print(f"     {e['reglage']} · {e['epreuve']} · {e['cause'][:90]}", flush=True)

    # ⚠️ **Le nom de sortie porte la variante.** Sans ce suffixe, un run `--typologie`
    # écraserait le run sans, sous le même nom : on ne saurait plus lequel est sur le
    # disque, et la comparaison qui motive l'option deviendrait impossible à faire.
    suffixe = "_typo" if typologie else ""
    pd.DataFrame(resume).to_csv(
        RACINE / f"reports/double_aveugle_journalier_{polluant}{suffixe}.csv", index=False)
    pd.DataFrame(detail).to_csv(
        RACINE / f"reports/double_aveugle_plis_{polluant}{suffixe}.csv", index=False)

    # La comparaison qui motive tout le script.
    print("=" * 72)
    print("Ancienne configuration (cible horaire, défaut) : temporelle +14,4 % "
          "(pire −14,6 %) · double aveugle +8,7 % (pire −24,9 %)")
    for r in resume:
        if r["reglage"] == "réglé" and r["epreuve"] in ("temporelle", "double aveugle"):
            print(f"Nouvelle configuration, {r['epreuve']:15s} : {r['gain_pct']:+.1f} % "
                  f"(pire {r['gain_min']:+.1f} %, {r['n_plis_negatifs']} pli(s) négatif(s))")
    print(f"\nÉcrit : reports/double_aveugle_journalier_{polluant}.csv "
          f"et double_aveugle_plis_{polluant}.csv", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis-spatiaux", type=int, default=3)
    p.add_argument("--typologie", action="store_true",
                   help="ajoute les 4 colonnes de typologie de station aux prédicteurs")
    p.add_argument("--rapide", action="store_true",
                   help="n'évalue que la configuration de production (défaut) — les trois "
                        "autres sont mesurées sans apport, voir le commentaire sur `configs`")
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis_spatiaux,
                          args.typologie, args.rapide))
