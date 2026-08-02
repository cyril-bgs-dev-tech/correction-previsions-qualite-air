#!/usr/bin/env python3
"""De quoi la correction est faite — attribution de Shapley, groupée par famille.

Pourquoi ce script, et pourquoi maintenant
------------------------------------------
Le projet sait **combien** chaque source apporte : les `apport_*.py` mesurent un gain global
par famille de variables. Il ne sait pas **où ni quand** elle apporte, ni ce qui compose une
correction donnée. Or c'est cette seconde question qu'une AASQA pose avant de déployer :
personne ne laissera une boîte noire contredire un modèle physique sans savoir pourquoi.

Ce qui rend l'exercice particulièrement lisible ici : **le modèle prédit un résidu**,
`observation − CAMS`. Les valeurs de Shapley expliquent donc **la correction elle-même** —
« pourquoi ajoute-t-on +18 µg/m³ à CAMS ici aujourd'hui ? » — et non une concentration. C'est
exactement la question du prévisionniste.

Somme ou moyenne — la question n'est pas cosmétique
----------------------------------------------------
Les valeurs de Shapley sont **additives** : ``prédiction = valeur_de_base + Σ φᵢ``. Grouper en
**sommant** dans la famille préserve l'égalité, et la cascade se referme exactement sur la
prédiction. Grouper en **moyennant** la casse : la décomposition n'additionne plus rien et la
fiche d'épisode devient fausse.

La moyenne intervient sur l'**autre** axe, celui des lignes :

===================================================  ==============================
question                                             opération
===================================================  ==============================
de quoi est faite **cette** correction, ce jour-là ?  **somme** des φᵢ, par ligne
quelle famille pèse le plus **globalement** ?         moyenne de **|φ_famille|**
quelle famille pousse systématiquement **vers le      moyenne **signée** de φ_famille
haut** ?
===================================================  ==============================

Les deux dernières diffèrent et sont toutes deux utiles : ``moyenne(|φ|)`` dit *combien ça
bouge*, ``moyenne(φ)`` dit *dans quel sens ça penche*. C'est la seconde qui révèle qu'une
famille ajoute systématiquement aux stations trafic.

⚠️ Pourquoi grouper est **obligatoire** et non un confort de lecture
---------------------------------------------------------------------
Le modèle porte **30 colonnes de forêt** — six rayons emboîtés (100 m à 30 km) pour cinq
familles d'essences — et cinq de route sur les mêmes rayons. Des rayons emboîtés sont
quasi parfaitement corrélés, et Shapley répartit le crédit **arbitrairement** entre variables
corrélées : `chene_lambda1000m` contre `chene_lambda3000m`, la répartition est un artefact du
tirage, pas une information. **Les attributions individuelles y sont du bruit ; leur somme ne
l'est pas.** Publier un classement par variable serait ici une faute de méthode.

⚠️ Et ce que SHAP ne dit pas
-----------------------------
**Shapley explique le modèle, pas l'atmosphère.** Une forte contribution de
``route_lambda1000m`` ne signifie pas que les routes ont fabriqué l'ozone : elle signifie que
le modèle se sert de la densité routière pour **situer** la station. À écrire sur la figure,
sinon la lecture causale s'installe toute seule.

Hors échantillon, comme le reste
--------------------------------
Les attributions sont calculées **par stations exclues** : chaque station est expliquée par un
modèle qui ne l'a jamais vue. Une attribution en échantillon décrirait une mémorisation.

TreeSHAP est **exact** pour les arbres, et natif dans LightGBM (``pred_contrib=True``) — ni
approximation, ni échantillonnage, ni dépendance externe.

Usage :
  python3 scripts/shap_familles.py --polluant NO2
  python3 scripts/shap_familles.py --polluant O3 --fiches 12
Sortie : reports/shap_familles_{polluant}.csv · reports/shap_fiches_{polluant}.csv
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

from optuna_mos import (GRAINE, jeu_journalier, plis_alternes,  # noqa: E402
                        params_reference)

N_PLIS = 3
# Le nombre d'arbres mesuré le 02/08/2026 : la production à 400 est sous-ajustée d'un
# facteur huit (+4,68 points de gain entre 400 et 3288). On explique le modèle qu'il faut
# déployer, pas celui qui est bridé.
N_ARBRES = 2000

# ── Les familles, dans l'ordre où l'information entre dans la correction ────────
#
# L'ordre n'est pas décoratif : c'est celui de la page « Anatomie de la méthode », et il
# rend la cascade lisible de la physique vers le contexte local.
FAMILLES: list[tuple[str, str]] = [
    ("prévision CAMS", r"^(cams_jour|cams_moy_jour|cams)$"),
    ("échéance", r"^echeance_h$"),
    ("observation passée", r"^(obs_j_moins|err_j_moins|obs_moy_\d+j|err_moy_\d+j|"
                           r"err_ecart_\d+j|fraicheur_j)$"),
    ("satellite TROPOMI", r"^tropomi_"),
    ("typologie de station", r"^typo_"),
    ("position", r"^(lat_wgs84|lon_wgs84|altitude)$"),
    ("relief", r"^(altitude_mnt_m|tpi_\d+m|rugosite_\d+m|profondeur_vallee_m|pente_deg)$"),
    ("paysage — forêt", r"^(chene|feuillu_autre|conifere|foret_tot)_"),
    ("paysage — route", r"^route_"),
    ("calendrier", r"^(heure_(sin|cos)|jour_annee_(sin|cos)|jour_semaine|weekend|ferie)$"),
]


def repartir(colonnes: list[str]) -> dict[str, list[str]]:
    """Range chaque prédicteur dans **une** famille, et refuse les orphelins.

    Règle 2 bis : zéro correspondance et deux correspondances sont **toutes deux** des
    erreurs. Une variable qui n'entre dans aucune famille disparaîtrait silencieusement de
    la décomposition, et la cascade ne se refermerait plus sur la prédiction — sans que rien
    ne le signale.
    """
    import re

    familles: dict[str, list[str]] = {nom: [] for nom, _ in FAMILLES}
    place: dict[str, str] = {}
    for c in colonnes:
        touches = [nom for nom, motif in FAMILLES if re.match(motif, c)]
        if len(touches) > 1:
            raise SystemExit(f"« {c} » entre dans {len(touches)} familles ({touches}) — "
                             f"les motifs se chevauchent, corriger FAMILLES")
        if not touches:
            raise SystemExit(f"« {c} » n'entre dans aucune famille — ajouter son motif "
                             f"plutôt que de la laisser tomber de la décomposition")
        familles[touches[0]].append(c)
        place[c] = touches[0]
    vides = [n for n, v in familles.items() if not v]
    if vides:
        print(f"  familles sans variable (normal si la source n'est pas branchée) : "
              f"{', '.join(vides)}")
    return {n: v for n, v in familles.items() if v}


def contributions(j: pd.DataFrame, predicteurs: list[str],
                  n_plis: int) -> tuple[np.ndarray, np.ndarray]:
    """Valeurs de Shapley **hors échantillon** : chaque station expliquée sans avoir été vue.

    Rend la matrice (lignes × prédicteurs) et le vecteur des valeurs de base.
    """
    from lightgbm import LGBMRegressor

    stations = np.sort(j["station_id"].unique())
    pli_de_station = dict(zip(stations, plis_alternes(stations, n_plis)))
    pli = j["station_id"].map(pli_de_station).to_numpy()

    phi = np.full((len(j), len(predicteurs)), np.nan)
    base = np.full(len(j), np.nan)
    params = params_reference("lgbm")

    for g in range(n_plis):
        t0 = time.time()
        test = pli == g
        entr = j[~test]
        m = LGBMRegressor(n_estimators=N_ARBRES, random_state=GRAINE, verbose=-1,
                          n_jobs=8, **params)
        m.fit(entr[predicteurs], entr["obs_jour"] - entr["cams_jour"])
        # `pred_contrib=True` rend n_variables + 1 colonnes : la dernière est la valeur de
        # base (l'espérance du résidu sur l'entraînement).
        contrib = m.predict(j.loc[test, predicteurs], pred_contrib=True)
        phi[test] = contrib[:, :-1]
        base[test] = contrib[:, -1]
        print(f"  pli {g + 1}/{n_plis} · {int(test.sum()):,} lignes expliquées · "
              f"{time.time() - t0:.0f}s", flush=True)
    return phi, base


def main(polluant: str, n_fiches: int) -> int:
    depart = time.time()
    j, predicteurs = jeu_journalier(polluant)
    familles = repartir(predicteurs)
    print(f"\n{polluant} · {len(j):,} jours-station · {len(predicteurs)} prédicteurs "
          f"en {len(familles)} familles\n", flush=True)

    phi, base = contributions(j, predicteurs, N_PLIS)

    # ── Groupement : SOMME dans la famille, jamais moyenne ──────────────────────
    index = {c: i for i, c in enumerate(predicteurs)}
    groupe = pd.DataFrame(index=j.index)
    for nom, colonnes in familles.items():
        groupe[nom] = phi[:, [index[c] for c in colonnes]].sum(axis=1)

    # ── Le contrôle qui rend la décomposition réfutable ─────────────────────────
    # L'additivité de Shapley est une identité, pas une approximation : si elle ne tient
    # pas, une variable a été perdue en chemin et la cascade ment.
    residu_predit = base + phi.sum(axis=1)
    ecart = np.abs(groupe.sum(axis=1).to_numpy() + base - residu_predit).max()
    if ecart > 1e-6:
        raise SystemExit(f"additivité rompue : écart max {ecart:.2e} — une variable manque "
                         f"à la répartition par familles")
    print(f"\n  additivité vérifiée · écart max {ecart:.2e} µg/m³")

    # ── Les deux lectures globales, qui ne disent PAS la même chose ─────────────
    resume = pd.DataFrame({
        "ampleur_moy_abs": groupe.abs().mean(),
        "penchant_moy_signe": groupe.mean(),
        "ecart_type": groupe.std(),
        "p95_abs": groupe.abs().quantile(0.95),
        "n_variables": {n: len(c) for n, c in familles.items()},
    }).sort_values("ampleur_moy_abs", ascending=False)
    resume["part_ampleur_pct"] = (100 * resume["ampleur_moy_abs"]
                                  / resume["ampleur_moy_abs"].sum())

    print(f"\n{'─' * 78}")
    print("AMPLEUR (moyenne de |φ|) — combien la famille fait bouger la correction")
    print("PENCHANT (moyenne signée) — dans quel sens elle la pousse systématiquement")
    print(f"{'─' * 78}")
    print(resume.round(4).to_string())
    print(f"\nvaleur de base moyenne : {base.mean():+.4f} µg/m³")

    sortie = RACINE / f"reports/shap_familles_{polluant}.csv"
    resume.to_csv(sortie)

    # ── Les fiches d'épisode : la cascade sur les jours qui décident ────────────
    d = j[["station_id", "jour", "obs_jour", "cams_jour"]].copy()
    d["correction"] = base + phi.sum(axis=1)
    d["prevu"] = np.clip(d["cams_jour"] + d["correction"], 0, None)
    d = pd.concat([d.reset_index(drop=True), groupe.reset_index(drop=True)], axis=1)
    d["base"] = base

    fiches = d.nlargest(n_fiches, "obs_jour")
    print(f"\n{'─' * 78}\n{n_fiches} jours les plus chargés — de quoi la correction est faite"
          f"\n{'─' * 78}")
    colonnes_f = list(familles) + ["base"]
    for _, r in fiches.iterrows():
        detail = " · ".join(f"{n} {r[n]:+.1f}" for n in colonnes_f
                            if abs(r[n]) >= 0.5)
        print(f"  {r['jour']:%Y-%m-%d} {r['station_id']} · observé {r['obs_jour']:6.1f} · "
              f"CAMS {r['cams_jour']:6.1f} → prévu {r['prevu']:6.1f}")
        print(f"      correction {r['correction']:+6.1f} = {detail}")

    sortie_f = RACINE / f"reports/shap_fiches_{polluant}.csv"
    fiches.to_csv(sortie_f, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} et {sortie_f.relative_to(RACINE)} · "
          f"{(time.time() - depart) / 60:.0f} min")
    print("\n⚠️ Shapley explique le MODÈLE, pas l'atmosphère. Une contribution du paysage "
          "dit que\n   le modèle s'en sert pour SITUER la station, pas que les arbres "
          "fabriquent l'ozone.")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--fiches", type=int, default=10)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.fiches))
