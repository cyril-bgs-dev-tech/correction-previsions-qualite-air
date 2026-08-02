#!/usr/bin/env python3
"""Le trafic : le bloc qui rapporte — compresser peut-il lui faire rapporter plus ?

Le jumeau du test précédent
---------------------------
``compression_paysage.py`` a établi que vingt-huit colonnes corrélées **coûtent en propre**
0,060 µg/m³, et que cinq agrégats à mécanisme nommé récupèrent ce coût. Sur le paysage, il
n'y avait rien dessous à récupérer. Le trafic est l'autre bloc large — trente variables — et
c'est **le seul qui rapporte vraiment** : +13,0 % sur le NO₂, IC95 [+10,4 ; +15,5].

D'où la question, qui n'est pas la même : si la dimension coûte là où il n'y a pas de signal,
combien coûte-t-elle là où il y en a un ? Le gain publié est peut-être un gain **amputé**.

Les composites, et le mécanisme de chacun
-----------------------------------------
Le NO₂ est dominé par des sources **linéaires**, dont l'intensité dépend du débit et
l'influence de la distance. Cinq agrégats :

* ``nox_routier`` — l'index d'émission. Chaque classe de voirie est pondérée par un ordre de
  grandeur de débit journalier, et chaque couronne par ``1/r``, dilution d'une source
  linéaire. C'est la variable que la hiérarchie routière était censée porter, écrite en une
  fois plutôt qu'éparpillée sur vingt colonnes.
* ``nox_proximite`` — la source majeure la plus proche, ``1/(1 + d/300)`` sur l'autoroute et
  la principale. Le panache d'un axe décroît en quelques centaines de mètres : c'est
  l'échelle qui décide, et une distance brute la code mal pour un arbre.
* ``part_axes_lourds`` — part de l'autoroute et de la principale dans la voirie à 1 km.
  Composition, non quantité : distingue une station d'échangeur d'une station de centre-ville
  à voirie dense mais lente.
* ``population_5km`` — une seule échelle. Le bloc en portait trois, quasi colinéaires.
* ``urbanite`` — ``population_5km / (population_20km + ε)``, le gradient centre-périphérie.

Usage : python3 scripts/compression_trafic.py [--polluant NO2] [--plis 3]
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

from aq.ingest.controle import ControleEchec, exiger_variation  # noqa: E402

EST_TRAFIC = re.compile(r"(route|trafic|autoroute|importance|pop|distance_pole)")
RAYONS = [100, 300, 1000, 3000]
# Ordres de grandeur de débit journalier par classe, en véhicules. Ce sont des ordres, pas
# des mesures : un arbre est invariant par transformation monotone, seule leur **hiérarchie**
# porte de l'information, et elle, elle est sûre.
DEBIT = {"autoroute": 40_000.0, "principale": 10_000.0,
         "secondaire": 3_000.0, "locale": 500.0}


def noyau_lineaire(t: pd.DataFrame) -> pd.Series:
    """Index d'émission routière : classes pondérées par le débit, couronnes par 1/r."""
    total = pd.Series(0.0, index=t.index)
    vues = 0
    for classe, debit in DEBIT.items():
        presents = [r for r in RAYONS if f"route_{classe}_lambda{r}m" in t.columns]
        if len(presents) < 3:
            continue
        vues += 1
        masse_prec, rayon_prec = 0.0, 0.0
        for r in presents:
            masse = t[f"route_{classe}_lambda{r}m"].fillna(0.0) * np.pi * r**2
            couronne = (masse - masse_prec).clip(lower=0.0)
            total = total + debit * couronne / max((r + rayon_prec) / 2.0, 50.0)
            masse_prec, rayon_prec = masse, r
    if vues < 3:
        raise ControleEchec(
            f"{vues} classes de voirie exploitables sur {len(DEBIT)} — l'index d'émission "
            "n'a pas de sens sans hiérarchie")
    return total / 1e9


def composites(t: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    out = pd.DataFrame(index=t.index)
    out["nox_routier"] = noyau_lineaire(t)

    proche = None
    for classe in ("autoroute", "principale"):
        col = f"route_{classe}_dist_min_m"
        if col not in t.columns:
            raise ControleEchec(f"{col} absent — la proximité aux axes lourds est indéfinie")
        d = t[col].replace([np.inf, -np.inf], 30_000.0).fillna(30_000.0)
        v = 1.0 / (1.0 + d / 300.0)
        proche = v if proche is None else np.maximum(proche, v)
    out["nox_proximite"] = proche

    lourds = ["route_autoroute_lambda1000m", "route_principale_lambda1000m"]
    tous = lourds + ["route_secondaire_lambda1000m", "route_locale_lambda1000m"]
    manquants = [c for c in tous if c not in t.columns]
    if manquants:
        raise ControleEchec(f"part des axes lourds indéfinie : {manquants} absents")
    num = sum(t[c].fillna(0.0) for c in lourds)
    out["part_axes_lourds"] = num / (sum(t[c].fillna(0.0) for c in tous) + 1e-9)

    for c in ("population_lambda5000m", "population_lambda20000m"):
        if c not in t.columns:
            raise ControleEchec(f"{c} absent")
    out["population_5km"] = t["population_lambda5000m"].fillna(0.0)
    out["urbanite"] = (t["population_lambda5000m"].fillna(0.0)
                       / (t["population_lambda20000m"].fillna(0.0) + 1e-6))

    exiger_variation(out, list(out.columns), "composites trafic")
    return out, list(out.columns)


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    # La voirie hiérarchisée ne fait pas partie de `charger()` : elle est jointe par chaque
    # script de mesure et par le pipeline gelé. Sans cette jointure, le bloc « trafic » se
    # réduirait aux cinq colonnes génériques et le test ne porterait pas sur ce qu'il annonce.
    hierarchie = pd.read_parquet(
        RACINE / "data/processed/trafic_population_metropole.parquet")
    avant = len(jeu)
    jeu = jeu.merge(hierarchie, on="station_id", how="left")
    if len(jeu) != avant:
        raise ControleEchec(
            f"la jointure de la voirie hiérarchisée a changé le nombre de lignes "
            f"({avant:,} → {len(jeu):,}) — clé non unique")
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])

    toutes = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    brutes = [c for c in toutes if EST_TRAFIC.match(c)]
    base = [c for c in toutes if c not in brutes]
    if len(brutes) < 20:
        raise ControleEchec(
            f"{len(brutes)} variables de trafic trouvées, au moins 20 attendues : "
            f"{brutes[:8]}")

    comp, cols_comp = composites(j)
    j = pd.concat([j, comp], axis=1)

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    print(f"{polluant} · {len(j):,} jours-station · {len(stations)} stations · "
          f"{len(base)} de base, {len(brutes)} de trafic brut, {len(cols_comp)} composites",
          flush=True)

    jeux = {"base (sans trafic)": base,
            f"+ {len(brutes)} brutes": base + brutes,
            f"+ {len(cols_comp)} composites": base + cols_comp,
            "+ brutes ET composites": base + brutes + cols_comp}

    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:26s} {len(predicteurs):3d} variables · "
              f"RMSE {resultats[nom]['rmse']:6.3f} · décile haut "
              f"{resultats[nom]['rmse_decile_haut']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    reference = resultats["base (sans trafic)"]
    print(f"\n{'─' * 82}\nContre la base sans trafic — un gain positif signifie que "
          f"l'ajout **aide** :")
    lignes = []
    for nom in list(jeux)[1:]:
        gain = reference["rmse"] - resultats[nom]["rmse"]
        bas, haut = ic_difference(predictions["base (sans trafic)"], predictions[nom])
        queue = reference["rmse_decile_haut"] - resultats[nom]["rmse_decile_haut"]
        signe = "aide" if bas > 0 else ("nuit" if haut < 0 else "indécis")
        print(f"  {nom:26s} gain {gain:+.3f} µg/m³  IC95 [{bas:+.3f} ; {haut:+.3f}]  "
              f"queue {queue:+.3f}  → {signe}")
        lignes.append({"jeu": nom, "n_variables": resultats[nom]["n_variables"],
                       "rmse": resultats[nom]["rmse"], "gain": gain, "ic_bas": bas,
                       "ic_haut": haut, "gain_queue": queue, "verdict": signe})

    nom_brut, nom_comp = list(jeux)[1], list(jeux)[2]
    ecart = resultats[nom_brut]["rmse"] - resultats[nom_comp]["rmse"]
    bas, haut = ic_difference(predictions[nom_brut], predictions[nom_comp])
    print(f"\n{'─' * 82}\nCompresser plutôt que garder les brutes : {ecart:+.3f} µg/m³  "
          f"IC95 [{bas:+.3f} ; {haut:+.3f}]")
    if bas > 0:
        print("  → Le gain publié du trafic était AMPUTÉ par son encodage. Réécrire le bloc\n"
              "    en composites, et rejouer la mesure d'apport publiée.")
    elif haut < 0:
        print("  → Compresser PERD ici : contrairement au paysage, les vingt colonnes\n"
              "    portent de l'information que les cinq agrégats ne capturent pas.\n"
              "    La dimension n'est donc pas un coût en soi — elle l'est quand elle est vide.")
    else:
        print("  → Écart indécis : les deux codages valent autant. Préférer alors le plus\n"
              "    court, qui se maintient et s'explique.")

    sortie = RACINE / f"reports/compression_trafic_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.plis))
