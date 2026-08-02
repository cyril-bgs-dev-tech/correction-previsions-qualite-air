#!/usr/bin/env python3
"""Contre quoi faut-il vraiment se comparer ? Les concurrents dont dispose une AASQA.

Le reproche auquel ce script répond
-----------------------------------
Le projet démontre qu'il bat **CAMS brut**. Mais un prévisionniste d'AASQA ne travaille pas
avec CAMS brut : il a les **observations récentes** de ses stations, un produit CAMS déjà
optimisé aux sites d'observation, et son expérience. Se comparer au brut, c'est peut-être
« résoudre un problème artificiellement privé de l'information que possède l'utilisateur »
(`docs/GPT_ANGLES_MORTS.md` Q6).

Le concurrent sérieux est le **biais glissant** : à chaque jour, retrancher à CAMS la moyenne
de ses erreurs des N derniers jours à cette station. C'est ce que tout ingénieur fait en une
heure, et cela n'exige aucun apprentissage.

**La causalité est la difficulté du test.** Au moment d'émettre la prévision pour J+1, on ne
connaît les observations que jusqu'à J−1 au mieux. Le biais glissant est donc calculé sur une
fenêtre **strictement antérieure et décalée**, sans quoi il utiliserait l'observation qu'il
prétend prédire — et gagnerait pour de mauvaises raisons.

**Une comparaison n'est licite que sur stations VUES.** Un biais glissant exige un historique
à la station : il n'existe pas pour une station nouvelle. C'est la tension que ce script rend
explicite — le projet ne peut pas revendiquer à la fois « je prédis où l'on ne mesure pas »
et « je bats ce que vous faites sur vos stations ».

| Concurrent | Utilise les observations récentes ? | Applicable à une station nouvelle ? |
|---|---|---|
| CAMS brut | non | oui |
| biais fixe (global) | historique agrégé | oui |
| **biais glissant N jours** | **oui** | **non** |
| persistance | oui | non |
| notre modèle | non | **oui** |

Usage : python3 scripts/benchmark_concurrents_reels.py [--polluant O3] [--fenetres 3,7,14,30]
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
from aq.models import mos  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from scores_episodes import scores  # noqa: E402

SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0}


def biais_glissant(d: pd.DataFrame, fenetre: int, decalage: int = 1) -> pd.Series:
    """Biais moyen des `fenetre` jours précédents, par station, décalé de `decalage`.

    Le `shift(decalage)` est la clé : sans lui, le biais du jour J contiendrait
    l'observation du jour J, que la prévision est censée deviner. Le décalage de 1 jour
    reproduit la latence minimale d'une chaîne réelle.
    """
    d = d.sort_values(["station_id", "jour"])
    erreur = d["cams_jour"] - d["obs_jour"]
    return (erreur.groupby(d["station_id"])
                  .transform(lambda s: s.shift(decalage)
                                        .rolling(fenetre, min_periods=max(2, fenetre // 3))
                                        .mean()))


def _xgb(graine: int):
    return modele_mos(graine=graine)


def main(polluant: str, horizon: int, fenetres: list[int], n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    d = agreger_journalier(jeu, colonnes, grandeur).sort_values(["station_id", "jour"])
    seuil = SEUILS[polluant]

    # ── Le modèle, en validation TEMPORELLE (stations vues) ───────────────────
    # C'est le seul cadre où le biais glissant existe : il faut un historique à la station.
    d["mois"] = d["jour"].dt.strftime("%Y-%m")
    mois = np.sort(d["mois"].unique())
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    entree = d.rename(columns={"obs_jour": "valeur", "jour": "timestamp_utc"})

    morceaux = []
    for m in mois:
        test = entree["mois"] == m
        if test.sum() < 200 or (~test).sum() < 1000:
            continue
        from lightgbm import LGBMRegressor  # noqa: F401  (import différé, cohérence env)

        modele = _xgb(0)
        tr = entree[~test]
        modele.fit(tr[predicteurs], tr["valeur"] - tr["cams_jour"])
        bloc = entree[test][["station_id", "timestamp_utc", "valeur", "cams_jour"]].copy()
        bloc["mos"] = np.clip(
            bloc["cams_jour"] + modele.predict(entree[test][predicteurs]), 0, None)
        morceaux.append(bloc)

    p = pd.concat(morceaux, ignore_index=True).rename(
        columns={"valeur": "obs_jour", "timestamp_utc": "jour"})
    print(f"{polluant} · {grandeur} · {len(p):,} jours-station évalués "
          f"({len(mois)} mois, validation temporelle)\n", flush=True)

    # ── Les concurrents ───────────────────────────────────────────────────────
    p = p.sort_values(["station_id", "jour"])
    biais_global = float((p["cams_jour"] - p["obs_jour"]).mean())
    candidats = {
        "CAMS brut": p["cams_jour"],
        f"biais fixe ({biais_global:+.1f})": p["cams_jour"] - biais_global,
    }
    for f in fenetres:
        b = biais_glissant(p, f)
        candidats[f"biais glissant {f} j"] = (p["cams_jour"] - b.fillna(biais_global))
    candidats["persistance (obs J−1)"] = (
        p.sort_values(["station_id", "jour"]).groupby("station_id")["obs_jour"].shift(1))
    candidats["NOTRE MODÈLE"] = p["mos"]

    base = cmp.metriques(p["obs_jour"], p["cams_jour"])
    depasse = (p["obs_jour"] >= seuil).to_numpy()

    print(f"{'concurrent':30s} {'RMSE':>7s} {'gain/CAMS':>10s} {'POD':>6s} {'CSI':>6s} "
          f"{'couvert':>8s}")
    lignes = []
    for nom, predit in candidats.items():
        valide = predit.notna() & p["obs_jour"].notna()
        m = cmp.metriques(p.loc[valide, "obs_jour"], predit[valide])
        s = (scores(depasse[valide.to_numpy()],
                    (predit[valide] >= seuil).to_numpy())
             if depasse[valide.to_numpy()].sum() >= 30 else {})
        gain = 100 * (1 - m["rmse"] / base["rmse"])
        print(f"{nom:30s} {m['rmse']:7.2f} {gain:+9.1f} % {s.get('POD', np.nan):6.3f} "
              f"{s.get('CSI', np.nan):6.3f} {100 * valide.mean():7.1f} %", flush=True)
        lignes.append({"concurrent": nom, "gain_pct": gain,
                       "couverture_pct": 100 * float(valide.mean()), **m,
                       **{f"s_{k}": v for k, v in s.items()}})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/benchmark_concurrents_{polluant}.csv", index=False)

    notre = float(table.loc[table["concurrent"] == "NOTRE MODÈLE", "rmse"].iloc[0])
    glissants = table[table["concurrent"].str.startswith("biais glissant")]
    meilleur = glissants.loc[glissants["rmse"].idxmin()]

    print("\n" + "=" * 72)
    print(f"Meilleur biais glissant : {meilleur['concurrent']} · RMSE {meilleur['rmse']:.2f}")
    print(f"Notre modèle            : RMSE {notre:.2f} · écart "
          f"{meilleur['rmse'] - notre:+.2f} µg/m³")
    if notre <= meilleur["rmse"]:
        print("→ Le modèle bat le concurrent opérationnel **sur ses propres stations**.")
    else:
        print("→ ⚠️ Un biais glissant fait mieux sur les stations connues. Le dossier doit")
        print("  revendiquer explicitement l'usage « station nouvelle », pour lequel aucun")
        print("  biais glissant n'existe — et ne pas laisser croire à l'autre.")
    print(f"\nÉcrit : reports/benchmark_concurrents_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--fenetres", default="3,7,14,30")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon,
                          [int(f) for f in args.fenetres.split(",")], args.plis))
