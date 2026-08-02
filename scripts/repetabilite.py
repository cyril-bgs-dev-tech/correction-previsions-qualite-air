#!/usr/bin/env python3
"""De combien un chiffre du dossier bouge-t-il si l'on change seulement la graine ?

Pourquoi ce test passe avant les autres
---------------------------------------
Chaque mesure du projet vient d'**une seule graine** : une partition en plis, un tirage de
sous-échantillonnage, un ordre de colonnes. Tant que la dispersion graine-à-graine n'est pas
connue, on ne sait pas lire les écarts qu'on publie.

L'enjeu est concret. Le balayage de réglage vient de mesurer un écart de **2,4 points** entre
deux réglages voisins, et le blocage spatial un écart de **10 points**. Si la dispersion de
graine vaut 0,3 point, les deux écarts sont réels. Si elle vaut 3 points, le premier est du
bruit et j'aurais tiré une conclusion de rien.

**Ce test ne mesure aucun gain. Il mesure la barre d'erreur de tous les autres.**

Deux sources d'aléa, séparées
-----------------------------
* **partition** — quelles stations tombent dans quel pli. C'est l'aléa qui domine en
  validation par groupes, et le seul que le bootstrap de stations approxime déjà.
* **ajustement** — sous-échantillonnage des lignes et des colonnes, à partition **fixée**.
  C'est l'aléa purement algorithmique.

Les mesurer séparément dit *où* est l'instabilité : une dispersion portée par la partition
signale que le résultat dépend de quelques stations ; portée par l'ajustement, qu'il faut
moyenner plusieurs modèles avant de publier.

Usage : python3 scripts/repetabilite.py [--polluant O3] [--graines 8]
Sortie : reports/repetabilite_{polluant}.csv
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

from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE, SEUILS  # noqa: E402
from scores_episodes import scores  # noqa: E402

from aq.ingest.controle import ControleEchec  # noqa: E402


def modele(graine: int):
    return modele_mos(graine=graine)


def un_tirage(d: pd.DataFrame, predicteurs: list[str], groupe: np.ndarray,
              graine: int, seuil: float) -> dict:
    obs = d["valeur"].to_numpy()
    cams = d["cams_jour"].to_numpy()
    pred = np.full(len(d), np.nan)
    for p in sorted(set(groupe)):
        test = groupe == p
        m = modele(graine)
        m.fit(d.loc[~test, predicteurs], obs[~test] - cams[~test])
        pred[test] = np.clip(cams[test] + m.predict(d.loc[test, predicteurs]), 0, None)
    rc = float(np.sqrt(np.mean((cams - obs) ** 2)))
    rm = float(np.sqrt(np.mean((pred - obs) ** 2)))
    haut = obs >= np.quantile(obs, 0.9)
    s = scores(obs >= seuil, pred >= seuil)
    return {"gain_pct": 100 * (1 - rm / rc), "rmse": rm,
            "rmse_decile_haut": float(np.sqrt(np.mean((pred[haut] - obs[haut]) ** 2))),
            "POD": s["POD"], "CSI": s["CSI"]}


def main(polluant: str, n_graines: int, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    d = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    d = d.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    stations = np.sort(d["station_id"].unique())
    seuil = SEUILS[polluant]
    print(f"{polluant} · {len(d):,} jours-station · {len(stations)} stations · "
          f"{n_graines} graines × 2 sources d'aléa", flush=True)

    lignes = []
    # ── Aléa d'AJUSTEMENT : partition figée, seule la graine du modèle change. ────────
    fixe = d["station_id"].map({s: i % n_plis for i, s in enumerate(stations)}).to_numpy()
    for g in range(n_graines):
        r = un_tirage(d, predicteurs, fixe, 1000 + g, seuil)
        lignes.append({"source": "ajustement", "graine": 1000 + g} | r)
        print(f"  ajustement  graine {1000 + g} · gain {r['gain_pct']:+6.2f} % · "
              f"CSI {r['CSI']:.3f} · {time.time() - depart:5.0f}s", flush=True)

    # ── Aléa de PARTITION : graine du modèle figée, les plis changent. ────────────────
    for g in range(n_graines):
        rng = np.random.default_rng(2000 + g)
        melange = rng.permutation(stations)
        part = d["station_id"].map({s: i % n_plis
                                    for i, s in enumerate(melange)}).to_numpy()
        r = un_tirage(d, predicteurs, part, 0, seuil)
        lignes.append({"source": "partition", "graine": 2000 + g} | r)
        print(f"  partition   graine {2000 + g} · gain {r['gain_pct']:+6.2f} % · "
              f"CSI {r['CSI']:.3f} · {time.time() - depart:5.0f}s", flush=True)

    t = pd.DataFrame(lignes)
    if len(t) != 2 * n_graines:
        raise ControleEchec(f"{len(t)} tirages sur {2 * n_graines} attendus")

    print(f"\n{'─' * 82}\n{'source':12s} {'gain moyen':>11s} {'écart-type':>11s} "
          f"{'étendue':>9s} {'CSI σ':>8s}")
    resume = []
    for source, g in t.groupby("source"):
        et = float(g["gain_pct"].std(ddof=1))
        etendue = float(g["gain_pct"].max() - g["gain_pct"].min())
        print(f"{source:12s} {g['gain_pct'].mean():+10.2f} % {et:10.3f} pt "
              f"{etendue:8.3f} pt {g['CSI'].std(ddof=1):8.4f}")
        resume.append({"source": source, "ecart_type_pt": et, "etendue_pt": etendue})

    total = float(t["gain_pct"].std(ddof=1))
    print(f"\nDispersion toutes sources : **±{total:.3f} point** (écart-type), "
          f"soit ±{1.96 * total:.3f} à 95 %.")

    # Ce que cette barre autorise à dire des écarts déjà publiés.
    print(f"\n{'─' * 82}\nCe que cette barre autorise sur les écarts mesurés aujourd'hui :")
    for nom, ecart in (("blocs spatiaux contre i % 3 (O₃)", 10.13),
                       ("« très contraint » contre REGLE, axe temporel", 3.96),
                       ("« capacité réduite » contre REGLE, axe temporel", 2.40)):
        rapport = ecart / max(1.96 * total, 1e-9)
        verdict = ("solide" if rapport >= 2 else
                   ("à la limite" if rapport >= 1 else "DANS LE BRUIT"))
        print(f"  {nom:46s} {ecart:+6.2f} pt = {rapport:4.1f}× la barre → {verdict}")

    sortie = RACINE / f"reports/repetabilite_{polluant}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--graines", type=int, default=8)
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.graines, n.plis))
