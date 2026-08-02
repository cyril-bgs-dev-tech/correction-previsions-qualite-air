#!/usr/bin/env python3
"""Le témoin qui manquait : que vaut une correction **sans aucun apprentissage** ?

Pourquoi ce script existe
-------------------------
Le projet compare sa correction apprise à CAMS brut, à la persistance et à la
climatologie — mais **jamais à un simple débiaisage**. C'est le premier geste de tout
ingénieur : retrancher à la prévision le biais moyen constaté. Si ce geste capture
l'essentiel du gain, l'apport de l'apprentissage est faible, et mieux vaut le savoir avant
qu'on ne le demande en entretien.

**Le point de méthode qui fait l'intérêt du test.** Un débiaisage *par station* exige de
connaître la station : il est **structurellement impossible** sur une station jamais vue.
Les deux découpages ne posent donc pas la même question, et il faut les séparer :

- **Volet spatial** (stations exclues) — seuls les témoins *transférables* sont jouables :
  biais global, par mois calendaire, par type de station. C'est là que l'apprentissage a
  son avantage le plus net, puisque le débiaisage par station n'y a même pas droit de cité.
- **Volet temporel** (mois exclus, stations connues) — là, le débiaisage par station est
  légitime et devient un concurrent sérieux. C'est le volet honnête, celui qui peut faire
  mal.

Tous les biais sont estimés **sur le pli d'entraînement seul** et appliqués au pli de test :
une moyenne calculée sur le test serait une fuite.

Aucun LightGBM ici — que des moyennes de groupe. Le script tourne en quelques minutes et
peut cohabiter avec un ajustement en cours. La référence apprise est **relue** depuis
`reports/mos_{polluant}_J{horizon}.csv`, jamais réajustée.

Usage : python3 scripts/temoin_sans_apprentissage.py [--polluant O3] [--horizon 1]
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
from fit_mos import charger  # noqa: E402

GRAINE = 20260730


def _rmse(observe: pd.Series, predit: pd.Series) -> float:
    return float(cmp.metriques(observe, predit)["rmse"])


def debiaiser(entrainement: pd.DataFrame, test: pd.DataFrame,
              cles: list[str] | None) -> pd.Series:
    """Retranche à CAMS le biais moyen estimé **sur l'entraînement seul**.

    `cles=None` donne le biais global. Un groupe absent de l'entraînement retombe sur le
    biais global — sans quoi le témoin serait avantagé par des NaN silencieux là où il ne
    sait rien.
    """
    residu = entrainement["cams"] - entrainement["valeur"]
    global_ = float(residu.mean())

    if not cles:
        return test["cams"] - global_

    biais = residu.groupby([entrainement[c] for c in cles]).mean()
    index_test = pd.MultiIndex.from_arrays([test[c] for c in cles]) if len(cles) > 1 \
        else pd.Index(test[cles[0]])
    correction = pd.Series(biais.reindex(index_test).to_numpy(), index=test.index)
    return test["cams"] - correction.fillna(global_)


def _cles_temporelles(jeu: pd.DataFrame) -> pd.DataFrame:
    jeu = jeu.copy()
    jeu["mois_cal"] = jeu["timestamp_utc"].dt.month
    jeu["heure"] = jeu["timestamp_utc"].dt.hour
    jeu["mois_ym"] = jeu["timestamp_utc"].dt.strftime("%Y%m")
    return jeu


def volet(jeu: pd.DataFrame, plis: list[np.ndarray], colonne_pli: str,
          temoins: dict[str, list[str] | None], titre: str) -> list[dict]:
    """Évalue chaque témoin sur les mêmes plis, hors échantillon."""
    print(f"\n--- {titre} · {len(plis)} plis ---", flush=True)
    resultats = []

    for nom, cles in temoins.items():
        predictions, observes = [], []
        for groupe in plis:
            masque_test = jeu[colonne_pli].isin(groupe)
            test, entrainement = jeu[masque_test], jeu[~masque_test]
            if test.empty or entrainement.empty:
                continue
            predictions.append(debiaiser(entrainement, test, cles))
            observes.append(test["valeur"])

        obs = pd.concat(observes)
        rmse = _rmse(obs, pd.concat(predictions))
        base = _rmse(obs, jeu.loc[obs.index, "cams"])
        gain = 100 * (1 - rmse / base)
        print(f"  {nom:38s} {rmse:7.2f}   gain/CAMS {gain:+6.1f} %", flush=True)
        resultats.append({"volet": titre, "temoin": nom, "rmse": rmse,
                          "rmse_cams": base, "gain_pct": gain, "n": len(obs)})

    return resultats


def main(polluant: str, horizon: int, n_plis: int) -> int:
    jeu = _cles_temporelles(charger(polluant, horizon).dropna(subset=["valeur"]))
    print(f"{polluant} J+{horizon} · {len(jeu):,} paires · "
          f"{jeu['station_id'].nunique()} stations", flush=True)

    lignes = []
    rng = np.random.default_rng(GRAINE)

    # ── Volet spatial : stations entièrement exclues ──────────────────────────
    stations = jeu["station_id"].unique()
    plis_spatiaux = np.array_split(rng.permutation(stations), n_plis)
    lignes += volet(
        jeu, plis_spatiaux, "station_id",
        {
            "biais global": None,
            "biais par mois calendaire": ["mois_cal"],
            "biais par type de station": ["type_station"],
            "biais par type × mois": ["type_station", "mois_cal"],
        },
        "Volet spatial · stations jamais vues",
    )
    print("  (un débiaisage par station est impossible ici : la station est inconnue)",
          flush=True)

    # ── Volet temporel : mois exclus, stations connues ────────────────────────
    mois = np.sort(jeu["mois_ym"].unique())
    plis_temporels = np.array_split(mois, n_plis)
    lignes += volet(
        jeu, plis_temporels, "mois_ym",
        {
            "biais global": None,
            "biais par station": ["station_id"],
            "biais par station × mois calendaire": ["station_id", "mois_cal"],
            "biais par station × heure": ["station_id", "heure"],
        },
        "Volet temporel · mois jamais vus, stations connues",
    )

    # ── La référence apprise, relue et non réajustée ──────────────────────────
    chemin = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    if chemin.exists():
        mos = pd.read_csv(chemin, usecols=["observe", "cams", "corrige"])
        mos = mos.dropna(subset=["observe"])
        rmse_mos = _rmse(mos["observe"], mos["corrige"])
        rmse_cams = _rmse(mos["observe"], mos["cams"])
        gain = 100 * (1 - rmse_mos / rmse_cams)
        print(f"\nRéférence apprise (LightGBM, stations exclues) : {rmse_mos:.2f} "
              f"· gain/CAMS {gain:+.1f} %", flush=True)
        lignes.append({"volet": "référence", "temoin": "MOS appris",
                       "rmse": rmse_mos, "rmse_cams": rmse_cams,
                       "gain_pct": gain, "n": len(mos)})
    else:
        print(f"\n⚠️ {chemin.name} absent : référence apprise non comparée", flush=True)

    sortie = RACINE / f"reports/temoin_sans_apprentissage_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis", type=int, default=4)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
