#!/usr/bin/env python3
"""Le sol apporte-t-il quelque chose ? Et sous quel codage ?

L'hypothèse, et la seule raison de la tester
--------------------------------------------
Le projet a une règle née d'un résultat négatif : *une correction n'ajoute que là où le
modèle amont est aveugle à lui-même*. La forêt a échoué à ce test parce que CAMS modélise
déjà les émissions biogéniques. Le sol n'est admissible que si le même argument ne
s'applique pas — et il ne s'applique pas de la même façon :

* **érosion éolienne.** Les modèles régionaux de CAMS portent bien un schéma d'érosion,
  mais leurs cartes de texture sont à la maille du modèle. À huit kilomètres, une station
  de plaine limoneuse et une station de terrasse sableuse partagent la même valeur.
* **volatilisation ammoniacale.** L'inventaire CAMS-REG répartit spatialement le NH₃
  agricole par proxy de surface agricole, sans le pH du sol — qui contrôle pourtant la
  fraction de l'azote ammoniacal présente sous forme volatile.

Ce sont donc deux hypothèses de **sous-maille**, comme le relief (qui, lui, rapporte
+4,0 %), et non de re-fourniture d'une entrée déjà modélisée.

Les deux codages testés
-----------------------
La mesure de compression du paysage a montré que douze colonnes corrélées coûtent en propre.
Le sol est donc testé sous ses deux formes dès le premier essai, jamais brutes seules :

* **12 brutes** — six propriétés × deux rayons (5 et 20 km).
* **3 composites** — un par mécanisme, plus la matière organique :
  * ``erodabilite`` = ``sable / (argile + 1)`` atténué par le pavage des fragments
    grossiers. Un sol sableux, pauvre en argile et sans cailloux, est mobilisable ;
  * ``nh3_fraction`` = ``1 / (1 + 10^(pKa − pH))`` avec pKa 9,25 — la part de l'azote
    ammoniacal réellement sous forme NH₃ volatile. C'est la loi d'équilibre, pas un
    ajustement : à pH 6,4 (médiane française) elle vaut 0,1 %, à pH 8 elle vaut 5 %, soit
    un facteur cinquante que le pH brut code mal pour un arbre ;
  * ``matiere_organique`` = carbone organique à 5 km.

Attendu, et ce qui compterait comme réfutation
----------------------------------------------
Le mécanisme désigne les **PM2,5** et les **PM10**, pas l'ozone. O₃ est donc traité comme
**témoin négatif** : un gain sur l'ozone signalerait que le sol code autre chose — de
l'occupation du sol, donc une variable déjà présente — et invaliderait le mécanisme
plutôt que de le confirmer.

Usage : python3 scripts/apport_sol.py [--polluant PM25] [--plis 3]
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

from apport_meteo import evaluer, ic_difference, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

from aq.ingest.controle import (  # noqa: E402
    ControleEchec,
    exiger_colonnes,
    exiger_couverture,
    exiger_variation,
)

PKA_AMMONIUM = 9.25


def composites(t: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Un agrégat par mécanisme nommé. Trois, pas douze."""
    exiger_colonnes(t, ["sol_sand_5km", "sol_clay_5km", "sol_cfvo_5km",
                        "sol_phh2o_5km", "sol_soc_5km"], "sol")
    out = pd.DataFrame(index=t.index)
    pavage = (1.0 - (t["sol_cfvo_5km"] / 100.0)).clip(lower=0.0, upper=1.0)
    out["erodabilite"] = (t["sol_sand_5km"] / (t["sol_clay_5km"] + 1.0)) * pavage
    out["nh3_fraction"] = 1.0 / (1.0 + 10.0 ** (PKA_AMMONIUM - t["sol_phh2o_5km"]))
    out["matiere_organique"] = t["sol_soc_5km"]
    exiger_variation(out, list(out.columns), "composites sol")
    return out, list(out.columns)


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    sol = pd.read_parquet(RACINE / "data/processed/sol_features_metropole.parquet")
    cols_sol = [c for c in sol.columns if c.startswith("sol_")]
    if len(cols_sol) != 12:
        raise ControleEchec(
            f"{len(cols_sol)} colonnes de sol trouvées, 12 attendues (6 propriétés × "
            f"2 rayons) — relancer scripts/extraire_sol.py")

    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])

    avant = len(j)
    j = j.merge(sol, on="station_id", how="left")
    if len(j) != avant:
        raise ControleEchec(f"la jointure du sol a changé le nombre de lignes "
                            f"({avant:,} → {len(j):,}) — clé non unique")
    # Une jointure « left » qui ne trouve rien ne lève pas : elle rend des colonnes vides.
    exiger_couverture(j, "sol_sand_5km", 0.95, "sol joint")

    comp, cols_comp = composites(j)
    j = pd.concat([j, comp], axis=1)

    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    temoin = " — TÉMOIN NÉGATIF, un gain ici réfuterait le mécanisme" if polluant == "O3" else ""
    print(f"{polluant} · {len(j):,} jours-station · {len(stations)} stations · "
          f"{len(base)} variables de base{temoin}", flush=True)

    jeux = {"base (sans sol)": base,
            "+ 12 brutes": base + cols_sol,
            "+ 3 composites": base + cols_comp}

    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:20s} {len(predicteurs):3d} variables · "
              f"RMSE {resultats[nom]['rmse']:6.3f} · décile haut "
              f"{resultats[nom]['rmse_decile_haut']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    reference = resultats["base (sans sol)"]
    print(f"\n{'─' * 78}\nContre la base sans sol — un gain positif signifie que "
          f"l'ajout **aide** :")
    lignes = []
    for nom in list(jeux)[1:]:
        gain = reference["rmse"] - resultats[nom]["rmse"]
        bas, haut = ic_difference(predictions["base (sans sol)"], predictions[nom])
        queue = reference["rmse_decile_haut"] - resultats[nom]["rmse_decile_haut"]
        signe = "aide" if bas > 0 else ("nuit" if haut < 0 else "indécis")
        print(f"  {nom:20s} gain {gain:+.3f} µg/m³  IC95 [{bas:+.3f} ; {haut:+.3f}]  "
              f"queue {queue:+.3f}  → {signe}")
        lignes.append({"polluant": polluant, "jeu": nom,
                       "n_variables": resultats[nom]["n_variables"],
                       "rmse": resultats[nom]["rmse"], "gain": gain, "ic_bas": bas,
                       "ic_haut": haut, "gain_queue": queue, "verdict": signe})

    # Le verdict porte sur **tout** codage significatif, pas sur celui de plus fort gain.
    # Une première version choisissait le maximum puis testait son intervalle : elle a
    # imprimé « aucun codage n'aide » alors qu'un autre codage aidait significativement.
    # C'est le contrôle mal posé de la règle 2 bis, dans sa forme la plus banale.
    aidants = [d for d in lignes if d["ic_bas"] > 0]
    print(f"\n{'─' * 78}")
    if not aidants:
        print("  → Aucun codage n'aide significativement. Le sol rejoint le paysage.")
    else:
        for d in aidants:
            print(f"  · {d['jeu']} aide significativement : {d['gain']:+.3f} µg/m³ "
                  f"[{d['ic_bas']:+.3f} ; {d['ic_haut']:+.3f}]")
        fort = max(aidants, key=lambda d: d["gain"])
        if polluant == "O3":
            print("\n  → GAIN SUR LE TÉMOIN NÉGATIF. L'érosion éolienne n'explique pas un "
                  "gain sur l'ozone :\n    le sol code alors de la géographie — occupation, "
                  "climat, position — déjà portée\n    ailleurs. Le mécanisme est RÉFUTÉ ; "
                  "ne pas présenter ce gain comme le confirmant.")
        else:
            print(f"\n  → {fort['jeu']} aide. Comparer au témoin O₃ avant toute conclusion : "
                  f"un gain\n    au moins aussi grand sur l'ozone désignerait la géographie, "
                  f"pas l'érosion.")
    # Le seuil du projet, pas un seuil de circonstance.
    if all(abs(d["gain"]) < 0.3 for d in lignes):
        print(f"\n  ⚠️ Tous les gains sont sous le critère d'arrêt de 0,3 µg/m³ du projet "
              f"(max {max(d['gain'] for d in lignes):+.3f}).\n     Significatif n'est pas "
              f"utile : le sol n'entre pas dans le modèle.")

    sortie = RACINE / f"reports/apport_sol_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM25")
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.plis))
