#!/usr/bin/env python3
"""Le contrôle d'intégrité qui passe AVANT toute mesure — en quelques secondes.

Ce qu'il aurait évité, chiffré
------------------------------
La nuit du 23 au 24/08 a mesuré trois heures sur un corpus dont il manquait cinq mois de
spéciation sur vingt-neuf. Tout ce qui a été mesuré avant la découverte a dû être refait :
quatre piles, quatre apports, huit ablations jointes. La base s'est déplacée de 0,17 à
0,32 pt et deux familles « démontrées » ont cessé de l'être.

**Le défaut était visible dès la première exécution.** La pile imprimait
« speciation 13/29 mois · troués » à chaque lancement. Personne ne le lisait, parce que
c'était un AFFICHAGE et non une assertion.

    Un diagnostic imprimé qui n'arrête rien n'est pas un contrôle : c'est une décoration.

Ce script transforme cet affichage en refus. Il coûte quelques secondes et se lance avant
la première tâche d'une génération.

Ce qu'il vérifie
----------------
1. **Couverture par famille** — aucune famille ne doit manquer un mois ENTIER dans la
   fenêtre visée. C'est le défaut « un mois absent est un code d'époque » : sous validation
   mois-caché, « famille absente » équivaut à « nous sommes dans ces mois-là ».
2. **Continuité** — aucun trou au milieu d'une série de fichiers, ce que le seul comptage
   ne montre pas.
3. **Complétude des mois de bord** — un mois à moitié livré passe tous les comptages.
4. **Empreinte du corpus** — pour que la génération suivante sache sur quoi elle a tourné.

⚠️ Il ne remplace pas les contrôles au chargement : ceux-ci voient les valeurs, celui-ci
voit les FICHIERS. Un mois présent mais vide lui échappe, et c'est
`exiger_couverture` qui l'attrape.

Usage  : python3 scripts/preflight.py [--fenetre 2023-08:2026-08] [--strict]
Sortie : code 0 si tout est vert, 1 sinon. `--strict` refuse aussi les avertissements.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

# Les familles suivies, et le motif de leurs fichiers extraits aux stations.
FAMILLES = {
    "speciation": "speciation_metropole_{m}.parquet",
    "precurseurs": "precurseurs_metropole_{m}.parquet",
    "chimie": "chimie_metropole_{m}.parquet",
    "geoscf v1": "geoscf_metropole_{m}.parquet",
    "ifs": "ifs_metropole_{m}.parquet",
}
# Taille minimale plausible d'un mois complet, en octets — un mois à moitié livré pèse
# moitié moins, et aucun comptage de fichiers ne le voit.
PART_TAILLE_MIN = 0.5


def main(fenetre: str, strict: bool) -> int:
    d0, d1 = fenetre.split(":")
    mois = [f"{x:%Y%m}" for x in pd.date_range(d0, d1, freq="MS")]
    dossier = RACINE / "data/processed/meteo"
    rouge = orange = 0

    print(f"PRÉFLIGHT · fenêtre visée {d0} → {d1} ({len(mois)} mois)")
    print("═" * 92)
    for nom, motif in FAMILLES.items():
        presents, tailles = [], {}
        for m in mois:
            f = dossier / motif.format(m=m)
            if f.exists():
                presents.append(m)
                tailles[m] = f.stat().st_size
        if not presents:
            print(f"⬜ {nom:12s} aucun fichier — famille absente du corpus")
            continue
        manquants = [m for m in mois if m not in set(presents)]
        # Un trou AU MILIEU est plus grave qu'un bord manquant : le bord se lit comme une
        # fenêtre plus courte, le trou comme un indicateur d'époque.
        i0, i1 = mois.index(presents[0]), mois.index(presents[-1])
        trous = [m for m in mois[i0:i1 + 1] if m not in set(tailles)]
        med = sorted(tailles.values())[len(tailles) // 2]
        maigres = sorted(m for m, t in tailles.items() if t < med * PART_TAILLE_MIN)

        if trous:
            rouge += 1
            print(f"🔴 {nom:12s} {len(presents):2d}/{len(mois)} · TROU(S) AU MILIEU : "
                  f"{', '.join(trous[:6])}{' …' if len(trous) > 6 else ''}")
            print(f"   {'':12s} → « famille absente » vaut « nous sommes dans ces mois-là ».")
        elif maigres:
            orange += 1
            print(f"🟠 {nom:12s} {len(presents):2d}/{len(mois)} · mois à moitié livré(s) : "
                  + ", ".join(f"{m} ({100*tailles[m]/med:.0f} %)" for m in maigres[:5]))
        elif manquants:
            orange += 1
            print(f"🟠 {nom:12s} {len(presents):2d}/{len(mois)} · borne(s) manquante(s) : "
                  f"{presents[0]} → {presents[-1]}")
        else:
            print(f"✅ {nom:12s} {len(presents):2d}/{len(mois)} · complet et continu")

    # 🔴 LA question, et la seule que la nuit du 23/08 n'a pas su poser.
    #
    # Une borne manquante se lit comme une fenêtre plus courte — anodin. Elle devient un
    # TROU dès que la fenêtre d'évaluation, elle, va plus loin. C'est exactement ce qui
    # s'est produit : la spéciation commençait en 2024-01, GEOS-CF bornait l'évaluation à
    # 2023-08→2025-12, et cinq mois se sont retrouvés sans spéciation À L'INTÉRIEUR de la
    # fenêtre. Le premier contrôle, qui jugeait chaque famille isolément, aurait dit 🟠.
    #
    # On juge donc chaque famille CONTRE LA FENÊTRE D'ÉVALUATION, pas contre elle-même.
    print()
    bornante = None
    for nom, motif in FAMILLES.items():
        ms = [m for m in mois if (dossier / motif.format(m=m)).exists()]
        if nom.startswith("geoscf") and ms:
            bornante = (nom, ms)
    if bornante:
        nom_b, ms_b = bornante
        print(f"fenêtre d'ÉVALUATION = couverture {nom_b} : {ms_b[0]} → {ms_b[-1]} "
              f"({len(ms_b)} mois)")
        for nom, motif in FAMILLES.items():
            if nom == nom_b:
                continue
            absents = [m for m in ms_b if not (dossier / motif.format(m=m)).exists()]
            if absents:
                rouge += 1
                print(f"  🔴 {nom:12s} absent de {len(absents)} mois DANS la fenêtre : "
                      f"{', '.join(absents[:6])}{' …' if len(absents) > 6 else ''}")
            else:
                print(f"  ✅ {nom:12s} couvre toute la fenêtre d'évaluation")

    from aq.ingest.controle import empreinte_corpus
    emp = empreinte_corpus([f"data/processed/meteo/{m.format(m='*')}"
                            for m in FAMILLES.values()], RACINE)
    print("═" * 92)
    print(f"empreinte du corpus : {emp}")
    if rouge:
        print(f"\n🔴 {rouge} famille(s) à TROU — mesurer dessus produit un indicateur")
        print("   d'époque, et tout ce qui sera mesuré devra être refait. C'est exactement")
        print("   ce qui a coûté trois heures de mesures le 23/08.")
        return 1
    if orange and strict:
        print(f"\n🟠 {orange} avertissement(s) et --strict demandé.")
        return 1
    print("\n✅ aucun trou au milieu — le corpus est mesurable." if not orange
          else f"\n🟠 {orange} avertissement(s), aucun trou au milieu — mesurable, "
               f"mais la fenêtre effective sera plus courte que demandée.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fenetre", default="2023-08:2026-08")
    ap.add_argument("--strict", action="store_true")
    sys.exit(main(**vars(ap.parse_args())))
