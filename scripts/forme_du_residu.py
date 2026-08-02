#!/usr/bin/env python3
"""Quelle **forme** de résidu apprendre ? Différence, rapport, ou racine.

Le trou que ce script comble
----------------------------
Le projet a mesuré que la cible doit être un **résidu** et non la concentration : apprendre
l'observation directement gagne 13 % de RMSE et détecte **zéro** dépassement sur quinze.
Il a aussi mesuré que le **grain** doit être réglementaire et non horaire (+5 à 6 points).

Mais il n'a jamais interrogé la **forme** du résidu. Depuis le premier jour, c'est
``obs − CAMS``, une différence, choisie sans comparaison. Or la concentration d'un polluant
est une grandeur **positive et fortement dissymétrique** : sa variance croît avec son niveau.
Une différence suppose une erreur homoscédastique — un biais de 10 µg/m³ compterait autant à
20 qu'à 150 µg/m³. C'est faux pour l'ozone, et le décile haut est précisément ce qui décide.

Les quatre formes comparées
---------------------------
Toutes sur les **mêmes plis**, les mêmes lignes, le même modèle, la même graine. Seule la
cible change — c'est le protocole de l'expérience contrôlée déjà utilisée par le projet.

==================  ==========================  ================================
forme               cible apprise               reconstruction
==================  ==========================  ================================
``différence``      ``obs − cams``              ``cams + f``
``rapport``         ``log(obs / cams)``         ``cams · exp(f)``
``racine``          ``√obs − √cams``            ``(√cams + f)²``
``log-additif``     ``log1p(obs) − log1p(cams)``  ``expm1(log1p(cams) + f)``
==================  ==========================  ================================

Le **rapport** est celui qui porte l'hypothèse : il rend l'erreur proportionnelle au niveau,
et garantit la positivité sans écrêtage. Il a un coût — une prévision CAMS proche de zéro
rend le rapport instable — d'où un plancher explicite, et une vérification que ce plancher ne
touche qu'une part négligeable des lignes.

Ce que le résultat voudra dire
------------------------------
Si le rapport gagne sur le **décile haut** et en **détection** sans perdre en RMSE global, la
forme additive coûtait quelque chose depuis le début. S'il perd, la différence est justifiée
et on saura enfin pourquoi — ce qui n'est pas le cas aujourd'hui.

Usage : python3 scripts/forme_du_residu.py [--polluant O3] [--plis 3]
Sortie : reports/forme_du_residu_{polluant}.csv
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

from apport_meteo import ic_difference  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE, SEUILS  # noqa: E402
from scores_episodes import scores  # noqa: E402

from aq.ingest.controle import ControleEchec  # noqa: E402

GRAINE = 20260731
# Plancher sur CAMS pour le rapport et le log. Une valeur de prévision sous ce seuil rendrait
# le rapport instable ; on vérifie plus bas que cela ne concerne qu'une part négligeable.
PLANCHER = 1.0


def modele():
    """Le moteur unique du projet — voir `aq.models.moteur`.

    ⚠️ Ce docstring affirmait « XGB ≈ LGBM à ±0,3 point ». **Aucune mesure de ce type
    n'existe dans le dépôt** : le seul banc, `comparaison_algorithmes_O3.csv`, oppose
    LightGBM, Ridge et forêt aléatoire. Affirmation retirée le 02/08/2026.
    """
    return modele_mos(graine=GRAINE)


# Chaque forme est un couple (cible, reconstruction). Les écrire ensemble interdit le défaut
# classique : apprendre une cible transformée et reconstruire avec la mauvaise inverse.
FORMES = {
    "différence (actuel)": (
        lambda o, c: o - c,
        lambda c, f: c + f),
    "rapport (log)": (
        lambda o, c: np.log(np.maximum(o, PLANCHER) / c),
        lambda c, f: c * np.exp(f)),
    "racine": (
        lambda o, c: np.sqrt(np.maximum(o, 0.0)) - np.sqrt(c),
        lambda c, f: np.square(np.maximum(np.sqrt(c) + f, 0.0))),
    "log-additif": (
        lambda o, c: np.log1p(np.maximum(o, 0.0)) - np.log1p(c),
        lambda c, f: np.expm1(np.log1p(c) + f)),
}


def evaluer(d: pd.DataFrame, predicteurs: list[str], groupe: np.ndarray,
            cible, reconstruire) -> np.ndarray:
    """Prédit hors pli, dans l'espace transformé, puis revient en µg/m³."""
    obs, cams = d["valeur"].to_numpy(), d["cams_jour"].to_numpy()
    y = cible(obs, cams)
    if not np.isfinite(y).all():
        raise ControleEchec(
            f"{(~np.isfinite(y)).sum()} cibles non finies — la transformation est mal "
            "définie sur ces lignes, elles ne doivent pas être silencieusement écartées")
    pred = np.full(len(d), np.nan)
    for p in sorted(set(groupe)):
        test = groupe == p
        m = modele()
        m.fit(d.loc[~test, predicteurs], y[~test])
        pred[test] = np.clip(reconstruire(cams[test], m.predict(d.loc[test, predicteurs])),
                             0, None)
    return pred


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    d = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    d = d.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    # Le plancher doit être négligeable, sinon le rapport ne mesure plus ce qu'on croit.
    sous = float((d["cams_jour"] < PLANCHER).mean())
    if sous > 0.01:
        raise ControleEchec(
            f"{sous:.1%} des prévisions CAMS sont sous le plancher de {PLANCHER} µg/m³ — "
            "le rapport serait dominé par l'écrêtage, pas par la forme du résidu")
    d["cams_jour"] = d["cams_jour"].clip(lower=PLANCHER)

    # Les observations négatives — artefacts près de la limite de détection — laissent la
    # différence indifférente mais rendent la racine indéfinie. Les écrêter dans la boucle
    # ferait porter les quatre formes sur des lignes différentes, ce qui est exactement le
    # défaut que l'expérience contrôlée existe pour éviter. On le fait donc **une fois, avant**,
    # et on le dit.
    neg = int((d["valeur"] < 0).sum())
    if neg / len(d) > 0.01:
        raise ControleEchec(
            f"{neg / len(d):.1%} d'observations négatives — au-delà de l'artefact de mesure, "
            "il faudrait comprendre la cause avant d'écrêter")
    d["valeur"] = d["valeur"].clip(lower=0.0)
    print(f"  {neg} observations négatives écrêtées à 0 ({neg / len(d):.4%}) — artefacts de "
          f"limite de détection", flush=True)

    stations = np.sort(d["station_id"].unique())
    groupe = d["station_id"].map({s: i % n_plis for i, s in enumerate(stations)}).to_numpy()
    seuil_ep = SEUILS[polluant]
    obs = d["valeur"].to_numpy()
    haut = obs >= np.quantile(obs, 0.9)
    print(f"{polluant} · {len(d):,} jours-station · {len(stations)} stations · "
          f"plancher touché sur {sous:.3%} des lignes · seuil épisode {seuil_ep:.0f}",
          flush=True)

    lignes, predictions = [], {}
    for nom, (cible, reconstruire) in FORMES.items():
        t0 = time.time()
        pred = evaluer(d, predicteurs, groupe, cible, reconstruire)
        predictions[nom] = pd.DataFrame({"station_id": d["station_id"], "obs_jour": obs,
                                         "pred": pred})
        rmse = float(np.sqrt(np.mean((pred - obs) ** 2)))
        queue = float(np.sqrt(np.mean((pred[haut] - obs[haut]) ** 2)))
        s = scores(obs >= seuil_ep, pred >= seuil_ep)
        lignes.append({"forme": nom, "rmse": rmse, "rmse_decile_haut": queue,
                       "biais": float(np.mean(pred - obs)),
                       "POD": s["POD"], "FAR": s["FAR"], "CSI": s["CSI"],
                       "duree_s": time.time() - t0})
        print(f"  {nom:22s} RMSE {rmse:6.3f} · décile haut {queue:6.3f} · "
              f"biais {lignes[-1]['biais']:+6.3f} · CSI {s['CSI']:.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    t = pd.DataFrame(lignes)
    ref = t.iloc[0]
    print(f"\n{'─' * 86}\nContre la différence, forme actuelle — IC95 par bootstrap de "
          f"stations :")
    for nom in list(FORMES)[1:]:
        gain = ref["rmse"] - float(t.loc[t["forme"] == nom, "rmse"].iloc[0])
        bas, hautic = ic_difference(predictions["différence (actuel)"], predictions[nom])
        gq = ref["rmse_decile_haut"] - float(
            t.loc[t["forme"] == nom, "rmse_decile_haut"].iloc[0])
        dcsi = float(t.loc[t["forme"] == nom, "CSI"].iloc[0]) - ref["CSI"]
        signe = "aide" if bas > 0 else ("nuit" if hautic < 0 else "indécis")
        print(f"  {nom:22s} RMSE {gain:+.3f} [{bas:+.3f} ; {hautic:+.3f}] → {signe:8s} · "
              f"queue {gq:+.3f} · ΔCSI {dcsi:+.3f}")

    meilleure_queue = t.loc[t["rmse_decile_haut"].idxmin()]
    meilleur_csi = t.loc[t["CSI"].idxmax()]
    print(f"\n{'─' * 86}")
    if meilleure_queue["forme"] == ref["forme"] and meilleur_csi["forme"] == ref["forme"]:
        print("  → La différence gagne sur la queue ET la détection. La forme additive "
              "était le bon\n    choix, et on sait maintenant pourquoi — ce n'était "
              "jusqu'ici qu'un défaut par défaut.")
    else:
        print(f"  → Meilleure queue : **{meilleure_queue['forme']}** "
              f"({meilleure_queue['rmse_decile_haut']:.3f} contre "
              f"{ref['rmse_decile_haut']:.3f})")
        print(f"    Meilleure détection : **{meilleur_csi['forme']}** "
              f"(CSI {meilleur_csi['CSI']:.3f} contre {ref['CSI']:.3f})")
        print("    La forme du résidu n'était pas neutre. Rejouer les mesures d'apport "
              "avec la\n    forme retenue avant d'en tirer un chiffre de dossier.")

    sortie = RACINE / f"reports/forme_du_residu_{polluant}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.plis))
