#!/usr/bin/env python3
"""Le paysage : absence de signal, ou signal noyé dans la dimension ?

Le résultat que ce script conteste
----------------------------------
Le dossier publie que le bloc paysage **coûte 1,9 %** : le retirer améliore le modèle. La
conclusion écrite en face — *CAMS modélise déjà les émissions biogéniques, re-fournir la
forêt n'ajoute rien* — a été tirée d'un protocole qui ne pouvait pas la démontrer.

Le protocole retirait les **vingt-huit variables d'un coup**. Un tel retrait ne distingue pas :

* *il n'y a pas de signal forestier* — la conclusion publiée ;
* *il y a un signal, mais vingt-huit colonnes fortement corrélées coûtent plus en variance
  qu'elles ne rapportent en biais* — jamais testé.

Les deux hypothèses prédisent exactement la même mesure. Tant que la seconde n'est pas
écartée, la première n'est pas établie.

Ce que ce script mesure
-----------------------
Quatre jeux, **mêmes plis, mêmes lignes, même bootstrap de stations** :

| jeu | variables ajoutées | ce qu'il teste |
|---|---|---|
| ``base`` | aucune | la référence sans paysage |
| ``+ 28 brutes`` | le bloc tel qu'il est aujourd'hui | reproduit le résultat publié |
| ``+ 5 composites`` | agrégats à mécanisme nommé | l'hypothèse de la dimension |
| ``+ 2 BVOC`` | les deux seuls potentiels d'émission | l'hypothèse la plus serrée |

Les composites, et le mécanisme de chacun
-----------------------------------------
* ``bvoc_isoprene`` — le chêne est le grand émetteur d'isoprène en France, précurseur
  d'ozone. Les densités aux rayons emboîtés sont recombinées par un noyau en ``1/r``, qui
  est la décroissance d'une source surfacique diluée. **Un** nombre, pas six.
* ``bvoc_monoterpene`` — idem sur les conifères, émetteurs de monoterpènes.
* ``foret_composition`` — part du chêne dans la forêt à 3 km. C'est une **composition**, non
  une quantité : c'est exactement ce qu'un inventaire d'émission à huit kilomètres lisse, et
  donc le seul candidat plausible à une information neuve.
* ``foret_couverture`` — densité forestière totale à 3 km, une seule échelle.
* ``foret_proximite`` — ``1/(1 + d/1000)`` sur la distance à la forêt la plus proche.

Ce que le résultat voudra dire
------------------------------
* Si les composites gagnent là où les brutes perdent, la conclusion publiée est **fausse en
  tant que conclusion** — le signal existait, le codage le détruisait. Il faudra alors
  rejouer la même compression sur les autres blocs larges.
* S'ils perdent aussi, la conclusion publiée devient **beaucoup plus solide** : elle aura
  résisté à un codage construit pour la falsifier.

Usage : python3 scripts/compression_paysage.py [--polluant O3] [--plis 3]
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from apport_meteo import evaluer, ic_difference, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

sys.path.insert(0, str(RACINE / "src"))
from aq.ingest.controle import ControleEchec, exiger_variation  # noqa: E402

EST_PAYSAGE = re.compile(r"(chene|feuillu|conifere|resineux|foret|hetre|pin|prairie|"
                         r"culture|urbain|eau)")
RAYONS = [100, 300, 1000, 3000, 10000, 30000]


def noyau_dilution(prefixe: str, t: pd.DataFrame) -> pd.Series:
    """Recombine les densités aux rayons emboîtés par un noyau en 1/r.

    Les ``lambda`` sont des densités **cumulées** dans le disque de rayon r. La densité de
    la couronne entre deux rayons se retrouve par différence des masses ; on la pondère
    ensuite par ``1/r``, décroissance d'une source surfacique diluée jusqu'au récepteur.
    """
    presents = [r for r in RAYONS if f"{prefixe}_lambda{r}m" in t.columns]
    if len(presents) < 3:
        raise ControleEchec(
            f"{prefixe} : {len(presents)} rayons trouvés sur {len(RAYONS)} attendus "
            f"({presents}) — le noyau de dilution n'a pas de sens sur moins de trois")
    masse_prec, rayon_prec = 0.0, 0.0
    total = pd.Series(0.0, index=t.index)
    for r in presents:
        masse = t[f"{prefixe}_lambda{r}m"].fillna(0.0) * np.pi * r**2
        couronne = (masse - masse_prec).clip(lower=0.0)
        rayon_repr = max((r + rayon_prec) / 2.0, 50.0)
        total = total + couronne / rayon_repr
        masse_prec, rayon_prec = masse, r
    # Échelle arbitraire mais fixe : un arbre est invariant par transformation monotone,
    # la normalisation ne sert qu'à rendre les nombres lisibles dans les journaux.
    return total / 1e6


def composites(t: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Construit les cinq agrégats. Renvoie aussi les deux BVOC seuls."""
    out = pd.DataFrame(index=t.index)
    out["bvoc_isoprene"] = noyau_dilution("chene", t)
    out["bvoc_monoterpene"] = noyau_dilution("conifere", t)
    if {"chene_lambda3000m", "foret_tot_lambda3000m"} <= set(t.columns):
        out["foret_composition"] = (t["chene_lambda3000m"].fillna(0.0)
                                    / (t["foret_tot_lambda3000m"].fillna(0.0) + 1e-6))
        out["foret_couverture"] = t["foret_tot_lambda3000m"].fillna(0.0)
    else:
        raise ControleEchec("chene_lambda3000m ou foret_tot_lambda3000m absent — "
                            "la composition forestière ne peut pas être formée")
    if "foret_tot_dist_min_m" not in t.columns:
        raise ControleEchec("foret_tot_dist_min_m absent")
    d = t["foret_tot_dist_min_m"].replace([np.inf, -np.inf], 30_000.0).fillna(30_000.0)
    out["foret_proximite"] = 1.0 / (1.0 + d / 1000.0)
    exiger_variation(out, list(out.columns), "composites paysage")
    return out, list(out.columns), ["bvoc_isoprene", "bvoc_monoterpene"]


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])

    toutes = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    brutes = [c for c in toutes if EST_PAYSAGE.match(c)]
    base = [c for c in toutes if c not in brutes]
    if len(brutes) < 20:
        raise ControleEchec(
            f"{len(brutes)} variables de paysage trouvées, au moins 20 attendues — "
            f"le motif ne reconnaît pas le bloc : {brutes[:8]}")

    comp, cols_comp, cols_bvoc = composites(j)
    j = pd.concat([j, comp], axis=1)

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    print(f"{polluant} · {len(j):,} jours-station · {len(stations)} stations · "
          f"{len(base)} variables de base, {len(brutes)} de paysage brut, "
          f"{len(cols_comp)} composites", flush=True)

    jeux = {"base (sans paysage)": base,
            "+ 28 brutes": base + brutes,
            "+ 5 composites": base + cols_comp,
            "+ 2 BVOC seuls": base + cols_bvoc}

    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:22s} {len(predicteurs):3d} variables · "
              f"RMSE {resultats[nom]['rmse']:6.3f} · décile haut "
              f"{resultats[nom]['rmse_decile_haut']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    reference = resultats["base (sans paysage)"]
    print(f"\n{'─' * 78}\nContre la base sans paysage — un gain positif signifie "
          f"que l'ajout **aide** :")
    lignes = []
    for nom in list(jeux)[1:]:
        gain = reference["rmse"] - resultats[nom]["rmse"]
        bas, haut = ic_difference(predictions["base (sans paysage)"], predictions[nom])
        queue = reference["rmse_decile_haut"] - resultats[nom]["rmse_decile_haut"]
        signe = "aide" if bas > 0 else ("nuit" if haut < 0 else "indécis")
        print(f"  {nom:22s} gain {gain:+.3f} µg/m³  IC95 [{bas:+.3f} ; {haut:+.3f}]  "
              f"queue {queue:+.3f}  → {signe}")
        lignes.append({"jeu": nom, "n_variables": resultats[nom]["n_variables"],
                       "rmse": resultats[nom]["rmse"], "gain": gain,
                       "ic_bas": bas, "ic_haut": haut, "gain_queue": queue,
                       "verdict": signe})

    # Le seul écart qui répond à la question posée : composites contre brutes.
    ecart = resultats["+ 28 brutes"]["rmse"] - resultats["+ 5 composites"]["rmse"]
    bas, haut = ic_difference(predictions["+ 28 brutes"], predictions["+ 5 composites"])
    print(f"\n{'─' * 78}\nCompresser plutôt que retirer : {ecart:+.3f} µg/m³  "
          f"IC95 [{bas:+.3f} ; {haut:+.3f}]")
    if bas > 0 and resultats["+ 5 composites"]["rmse"] < reference["rmse"]:
        print("  → Le codage détruisait le signal. La conclusion publiée « la forêt "
              "n'ajoute rien »\n    est FAUSSE en tant que conclusion : c'étaient les "
              "vingt-huit colonnes qui coûtaient.\n    Rejouer la compression sur tous "
              "les blocs larges.")
    elif bas > 0:
        print("  → Compresser aide contre les brutes, mais l'ensemble reste sous la base : "
              "la dimension\n    coûtait bien quelque chose, sans qu'il y ait de signal "
              "forestier à récupérer.")
    else:
        print("  → Compresser n'aide pas. La conclusion publiée **résiste** à un codage "
              "construit\n    pour la falsifier : c'est bien l'information qui manque, "
              "pas son encodage.")

    sortie = RACINE / f"reports/compression_paysage_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.plis))
