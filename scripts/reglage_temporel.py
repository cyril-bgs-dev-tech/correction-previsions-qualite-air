#!/usr/bin/env python3
"""Régler contre le temps, pas contre les stations — et mesurer ce que ça coûte.

Le constat qui motive ce script
-------------------------------
Le réglage `REGLE` du projet a été choisi en **validation par stations exclues**. Une mesure
antérieure a montré qu'un réglage optimisé sur cet axe **gagne +5 points en spatial et en
perd 3 en temporel** : les deux axes ne demandent pas la même capacité. Or le point faible
mesuré du projet est précisément le temporel — c'est lui qui décide de ce qui se passera en
2026 avec un modèle figé en 2024.

La question posée ici : *quel réglage un critère purement prospectif choisirait-il, et que
coûte-t-il sur l'axe spatial ?*

L'hypothèse, et pourquoi elle est réfutable
-------------------------------------------
Le calendrier est la famille de variables la plus utile du modèle (+9,1 %) **et** celle qui
rend la généralisation temporelle fragile : un modèle à forte capacité apprend *quelle
saison*, ce qui ne se transporte pas à un régime inconnu. On s'attend donc à ce que le
critère temporel préfère **moins de capacité et plus de régularisation** que `REGLE`.

Si le balayage retient `REGLE` ou plus gros, l'hypothèse est fausse et il faut le dire : la
fragilité temporelle viendrait d'ailleurs que de la capacité.

Le protocole
------------
* **Axe temporel** — rolling-origin strict, réutilisé de `rolling_origin_o3.py` :
  `max(train.jour) < min(test.jour)`, vérifié à chaque pli, exception si violé.
* **Axe spatial** — stations entièrement exclues, mêmes plis pour tous les réglages.
* Les deux axes sont rapportés **pour chaque réglage**, jamais l'un sans l'autre : c'est
  exactement l'erreur que ce script existe pour ne pas refaire.

Passe unitaire obligatoire avant le lot (règle 1) : `--passe-unitaire` chronomètre un pli et
extrapole le coût total.

Usage :
  python3 scripts/reglage_temporel.py --passe-unitaire
  python3 scripts/reglage_temporel.py
Sortie : reports/reglage_temporel_O3.csv
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

from modele_final import DEFAUT, REGLE  # noqa: E402
from rolling_origin_o3 import GRAINE, gain_rmse, preparer  # noqa: E402

from aq.ingest.controle import ControleEchec  # noqa: E402

# Les candidats descendent en capacité et montent en régularisation depuis `REGLE`. Chacun
# porte le nom du mécanisme qu'il teste, pas un numéro : un tableau de résultats doit se lire
# sans revenir au code.
CANDIDATS = {
    "REGLE (réglé sur les stations)": dict(REGLE),
    "DÉFAUT": dict(DEFAUT),
    "capacité réduite": {"num_leaves": 63, "learning_rate": 0.03, "n_estimators": 900,
                         "min_child_samples": 200, "reg_lambda": 10.0},
    "régularisation forte": {"num_leaves": 255, "learning_rate": 0.03, "n_estimators": 900,
                             "min_child_samples": 200, "reg_lambda": 100.0},
    "très contraint": {"num_leaves": 31, "learning_rate": 0.03, "n_estimators": 900,
                       "min_child_samples": 400, "reg_lambda": 50.0},
    "colonnes décorrélées": {"num_leaves": 255, "learning_rate": 0.03, "n_estimators": 900,
                             "min_child_samples": 50, "reg_lambda": 10.0,
                             "colsample_bytree": 0.5},
}
# Une bibliothèque qui prend déjà tous les cœurs ne se parallélise pas en la lançant plusieurs
# fois : les réglages s'enchaînent, `n_jobs` reste à −1, et rien d'autre ne tourne.
N_JOBS = -1


def modele(params: dict, n_jobs: int = N_JOBS):
    from lightgbm import LGBMRegressor

    p = {"subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8,
         "random_state": GRAINE, "n_jobs": n_jobs, "verbose": -1} | params
    return LGBMRegressor(**p)


def pli_temporel(d: pd.DataFrame, predicteurs: list[str], mois: str,
                 params: dict, n_jobs: int = N_JOBS) -> dict | None:
    """Un mois prédit par tout son passé, et rien que son passé."""
    debut = pd.Timestamp(f"{mois}-01")
    fin = debut + pd.offsets.MonthBegin(1)
    jours = d["jour"]
    if getattr(jours.dt, "tz", None) is not None:
        debut, fin = debut.tz_localize("UTC"), fin.tz_localize("UTC")
    tr = d.loc[jours < debut]
    te = d.loc[(jours >= debut) & (jours < fin)]
    if len(tr) < 500 or len(te) < 50:
        return None

    # La prospectivité est **vérifiée**, jamais supposée : c'est la seule chose qui distingue
    # ce protocole d'une validation croisée ordinaire, et une inversion ne lèverait rien.
    if pd.Timestamp(tr["jour"].max()) >= pd.Timestamp(te["jour"].min()):
        raise ControleEchec(
            f"{mois} : max(train) >= min(test) — la prospectivité est violée")

    t0 = time.time()
    m = modele(params, n_jobs)
    m.fit(tr[predicteurs], tr["valeur"] - tr["cams_jour"])
    pred = np.clip(te["cams_jour"].to_numpy() + m.predict(te[predicteurs]), 0, None)
    rc, rm, g = gain_rmse(te["valeur"], te["cams_jour"], pred)
    return {"mois": mois, "n_test": len(te), "rmse_cams": rc, "rmse_mos": rm,
            "gain_pct": g, "duree_s": time.time() - t0}


def axe_spatial(d: pd.DataFrame, predicteurs: list[str], params: dict,
                n_plis: int = 3) -> dict:
    """Stations entièrement exclues — mêmes plis pour tous les réglages."""
    stations = np.sort(d["station_id"].unique())
    groupe = d["station_id"].map({s: i % n_plis for i, s in enumerate(stations)}).to_numpy()
    pred = np.full(len(d), np.nan)
    for g in range(n_plis):
        test = groupe == g
        m = modele(params)
        m.fit(d.loc[~test, predicteurs], d.loc[~test, "valeur"] - d.loc[~test, "cams_jour"])
        pred[test] = np.clip(
            d.loc[test, "cams_jour"].to_numpy() + m.predict(d.loc[test, predicteurs]), 0, None)
    rc, rm, g = gain_rmse(d["valeur"], d["cams_jour"], pred)
    return {"rmse_cams": rc, "rmse_mos": rm, "gain_pct": g}


def main(passe_unitaire: bool, n_plis: int) -> int:
    depart = time.time()
    d, predicteurs = preparer()
    d["mois"] = pd.to_datetime(d["jour"]).dt.strftime("%Y-%m")
    mois = sorted(d["mois"].unique())[1:]  # le premier mois n'a pas de passé
    print(f"O₃ · {len(d):,} jours-station · {len(mois)} mois évaluables · "
          f"{len(predicteurs)} prédicteurs", flush=True)

    if passe_unitaire:
        # Le pli le plus coûteux est le dernier : son entraînement porte tout l'historique.
        r = pli_temporel(d, predicteurs, mois[-1], CANDIDATS["REGLE (réglé sur les stations)"])
        if r is None:
            raise ControleEchec(f"{mois[-1]} : effectif insuffisant pour la passe unitaire")
        # Coût moyen ≈ moitié du pli le plus lourd, l'historique croissant linéairement.
        total = 0.5 * r["duree_s"] * len(mois) * len(CANDIDATS)
        spatial = r["duree_s"] * n_plis * len(CANDIDATS)
        print(f"\npli le plus lourd ({mois[-1]}) : {r['duree_s']:.0f} s · "
              f"gain {r['gain_pct']:+.1f} %")
        print(f"extrapolation — temporel {total / 60:.0f} min · spatial "
              f"{spatial / 60:.0f} min · TOTAL {(total + spatial) / 60:.0f} min")
        print("\nRelancer sans --passe-unitaire si ce coût est acceptable.")
        return 0

    lignes = []
    for nom, params in CANDIDATS.items():
        t0 = time.time()
        plis = [r for m in mois if (r := pli_temporel(d, predicteurs, m, params))]
        if len(plis) < len(mois) - 2:
            raise ControleEchec(
                f"{nom} : {len(plis)} plis sur {len(mois)} attendus — un pli sauté en "
                "silence fausserait la comparaison entre réglages")
        t = pd.DataFrame(plis)
        # Moyenne **pondérée par l'effectif du mois** : un mois de 300 jours-station ne pèse
        # pas comme un mois de 7 000, et la moyenne simple donnerait le contraire.
        temporel = float((t["gain_pct"] * t["n_test"]).sum() / t["n_test"].sum())
        pire = float(t["gain_pct"].min())
        spa = axe_spatial(d, predicteurs, params, n_plis)
        lignes.append({"reglage": nom, "gain_temporel_pct": temporel,
                       "pire_mois_pct": pire, "mois_negatifs": int((t["gain_pct"] < 0).sum()),
                       "gain_spatial_pct": spa["gain_pct"],
                       "rmse_spatial": spa["rmse_mos"], "duree_s": time.time() - t0})
        print(f"  {nom:32s} temporel {temporel:+6.2f} % (pire {pire:+6.1f} %, "
              f"{lignes[-1]['mois_negatifs']} mois négatifs) · spatial "
              f"{spa['gain_pct']:+6.2f} % · {time.time() - depart:5.0f}s", flush=True)

    t = pd.DataFrame(lignes)
    ref = t[t["reglage"].str.startswith("REGLE")].iloc[0]
    meilleur = t.loc[t["gain_temporel_pct"].idxmax()]
    print(f"\n{'─' * 88}")
    print(f"Référence  {ref['reglage']:32s} temporel {ref['gain_temporel_pct']:+.2f} % · "
          f"spatial {ref['gain_spatial_pct']:+.2f} %")
    print(f"Meilleur   {meilleur['reglage']:32s} temporel "
          f"{meilleur['gain_temporel_pct']:+.2f} % · spatial "
          f"{meilleur['gain_spatial_pct']:+.2f} %")
    dt = meilleur["gain_temporel_pct"] - ref["gain_temporel_pct"]
    ds = meilleur["gain_spatial_pct"] - ref["gain_spatial_pct"]
    if meilleur["reglage"] == ref["reglage"]:
        print("\n→ Le critère temporel retient le réglage déjà en place. L'hypothèse est "
              "FAUSSE :\n  la fragilité temporelle ne vient pas de la capacité du modèle. "
              "Chercher ailleurs\n  — vraisemblablement dans le calendrier lui-même.")
    else:
        print(f"\n→ Régler contre le temps rend {dt:+.2f} point de gain temporel et "
              f"{ds:+.2f} en spatial.")
        if ds < 0:
            print(f"  C'est un ARBITRAGE, pas une amélioration : {abs(ds):.2f} point "
                  f"d'un axe payé\n  par {dt:.2f} de l'autre. Le choix dépend de l'usage — "
                  f"un modèle figé et appliqué\n  l'année suivante vit sur l'axe temporel.")
        else:
            print("  Les deux axes gagnent : le réglage en place était simplement "
                  "sous-optimal.")

    sortie = RACINE / "reports/reglage_temporel_O3.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--passe-unitaire", action="store_true")
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.passe_unitaire, n.plis))
