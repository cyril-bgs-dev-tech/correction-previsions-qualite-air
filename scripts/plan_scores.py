#!/usr/bin/env python3
"""Ce qui reste à mesurer — dérivé des ARTEFACTS, jamais d'une liste figée.

Pourquoi ce script existe
--------------------------
L'orchestration de la nuit du 23 au 24/08 vivait dans le répertoire temporaire de la
session : des lanceurs et des listes de tâches qui disparaissent avec elle. Une reprise
dans une autre fenêtre repartait donc de rien, alors que des heures de calcul étaient
déjà faites.

Le plan se **recalcule** ici, ce qui vaut mieux qu'une liste sauvegardée : une liste ment
dès qu'une tâche aboutit, alors qu'un artefact daté dit la vérité.

Le critère de « déjà fait », et pourquoi ce n'est pas l'existence
------------------------------------------------------------------
Beaucoup d'artefacts existent mais datent d'AVANT la correction du corpus — cinq mois de
spéciation ajoutés le 23/08 vers 20 h 26, qui ont déplacé la base de 0,17 à 0,32 pt et fait
tomber `fourier` de « démontré » à « non confirmé ». Les comparer à des mesures récentes
mélange deux corpus, ce que ni la fenêtre ni le nombre de plis ne montrent (règle M).

Une tâche est donc **à refaire** si son artefact est plus ANCIEN que le plus récent
fichier de spéciation. Le repère se lit sur disque, il n'est pas écrit en dur.

Usage
-----
  python3 scripts/plan_scores.py              # l'état, lisible
  python3 scripts/plan_scores.py --taches     # les tâches restantes, pour file_ressource
  python3 scripts/plan_scores.py --tout       # y compris ce qui est déjà fait
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
P4 = ("NO2", "O3", "PM10", "PM25")
PY_ = "python3 -u"


def repere() -> float:
    """L'instant de la dernière correction du corpus, lu sur disque."""
    fs = glob.glob(str(RACINE / "data/processed/meteo/speciation_metropole_*.parquet"))
    if not fs:
        raise SystemExit("aucune spéciation extraite — le repère de corpus est indéfini")
    return max(Path(f).stat().st_mtime for f in fs)


def repere_code() -> float:
    """L'instant de la dernière modification des scripts qui décident du contenu.

    🔴 Le repère de CORPUS ne suffit pas — constaté le 24/08 à 02 h 43. Le résultat
    `core7` de NO₂ était plus récent que le corpus et pourtant invalide : son processus
    avait chargé `ablation_speciation` AVANT une reclassification commitée quatorze
    minutes plus tôt, et n'écartait donc que quatre colonnes au lieu de huit. Sa fenêtre
    s'en trouvait tronquée de 29 à 24 mois.

    Python lit un module à l'import : une tâche longue porte le code de son DÉBUT, pas
    celui de sa fin. Un artefact plus récent qu'un correctif n'a donc pas forcément été
    produit avec.

    ⚠️ Ce repère AVERTIT, il n'invalide pas : ces scripts changent sans cesse, et invalider
    à chaque édition referait tout en permanence. C'est un signalement à l'humain — ou à
    l'agent — qui décide.
    """
    fs = ["scripts/methode_maximale.py", "scripts/ablation_speciation.py",
          "scripts/apport_precurseurs.py", "scripts/ablation_jointe.py"]
    return max((RACINE / f).stat().st_mtime for f in fs if (RACINE / f).exists())


def etapes() -> list[tuple[str, str, list[tuple[str, str]]]]:
    """(clé, ce que l'étape débloque, [(artefact, commande)])."""
    m = f"{PY_} scripts/methode_maximale.py --polluant %s --horizon 2"
    a = f"{PY_} scripts/apport_precurseurs.py --polluant %s --horizon 2 --axe double"
    return [
        ("reference", "tout se compare à elles — un apport sur base périmée est deux mesures",
         [(f"reports/predictions_methode_maximale_{p}_h2.parquet", (m % p) + " --ablation")
          for p in P4]),
        ("precurseurs", "les quatre gaz : aucune configuration ne tenait au dernier verdict",
         [(f"reports/apport_precurseurs_{p}_h2_double.csv", (a % p) + " --lot precurseurs")
          for p in P4]),
        ("chimie", "formaldéhyde, glyoxal, NO, CO — tient sur l'ozone seul (+1,17 pt)",
         [(f"reports/apport_chimie_{p}_h2_double.csv", (a % p) + " --lot chimie")
          for p in P4]),
        ("fenetre-complete", "onze blocs rendent-ils testable ce que neuf ne résolvent pas ?",
         [(f"reports/methode_maximale_{p}_h2_sans-feux-geoscf_fenetre-complete.csv",
           (m % p) + " --ablation --exclure geoscf,feux --fenetre complete") for p in P4]),
        ("pre-moyennes", "précurseurs à 4 colonnes au lieu de 8 — prédiction bb74bc95",
         [(f"reports/methode_maximale_{p}_h2_pre-moyennes.csv",
           (m % p) + " --precurseurs moyennes") for p in P4]),
        ("core7", "la pile sans indicateur d'époque dans la spéciation — prédiction 281e97ca",
         [(f"reports/methode_maximale_{p}_h2_spe-core7.csv", (m % p) + " --speciation core7")
          for p in P4]),
        # ⬆️ Remonté avant l'IFS le 24/08, sur revue exécutive externe. L'argument : cribler
        # une information neuve sur une base qui porte encore des mois entièrement absents
        # oblige à la re-cribler ensuite. La pile auditable EST la référence propre — elle
        # écarte mécaniquement toute famille trouée — et geler cette référence coûte quatre
        # exécutions, contre huit si l'IFS doit être refait.
        ("auditable", "LA RÉFÉRENCE PROPRE — écarte les familles trouées ; à geler avant tout ajout",
         [(f"reports/methode_maximale_{p}_h2_sc.csv", (m % p) + " --support-complet")
          for p in P4]),
        # 🔴 Le repère porte sur la PILE RÉDUITE, pas sur le verdict qui la relit. Le
        # verdict est réécrit en quelques secondes ; la pile demande vingt minutes, et
        # c'est elle qui doit dater du corpus courant. Cinq des huit ablations semblaient
        # « faites » sur la foi de leur CSV final, alors que leur pile venait d'avant la
        # correction — exactement la confusion que la règle M interdit.
        ("ifs", "la pile ne porte AUCUNE météo ; l'IFS est prévu donc déployable",
         [(f"reports/apport_ifs_{p}_h2_double.csv", (a % p) + " --lot ifs") for p in P4]),
        ("ablations-jointes", "feux+tendance et geoscf+membres — conclusions à re-mesurer",
         [(f"reports/methode_maximale_{p}_h2_sans-{'-'.join(sorted(f.split(',')))}.csv",
           f"{PY_} scripts/ablation_jointe.py --polluant {p} --familles {f}")
          for f in ("feux,tendance", "membres,geoscf") for p in P4]),
    ]


def main(taches: bool, tout: bool, code: bool) -> int:
    t0 = repere()
    tc = repere_code()
    lignes, reste, suspects = [], 0, []
    for cle, pourquoi, travaux in etapes():
        faits = [c for c, _ in travaux
                 if (RACINE / c).exists() and (RACINE / c).stat().st_mtime >= t0]
        suspects += [c for c in faits if (RACINE / c).stat().st_mtime < tc]
        manquants = [(c, k) for c, k in travaux
                     if not ((RACINE / c).exists() and (RACINE / c).stat().st_mtime >= t0)]
        reste += len(manquants)
        lignes.append((cle, pourquoi, len(faits), len(travaux), manquants))
    if taches:
        for _, _, _, _, manquants in lignes:
            for c, k in manquants:
                print(f"{c} :: {k}")
        return 0
    from datetime import datetime
    print(f"PLAN · repère de corpus : {datetime.fromtimestamp(t0):%Y-%m-%d %H:%M} "
          f"(dernière spéciation écrite)")
    print("═" * 96)
    for cle, pourquoi, n, total, manquants in lignes:
        etat = "✅" if n == total else ("⚙️ " if n else "⬜")
        print(f"{etat} {cle:18s} {n:2d}/{total:2d}   {pourquoi}")
        if manquants and (tout or n < total):
            for c, _ in manquants[:4]:
                print(f"       ↳ {c}")
            if len(manquants) > 4:
                print(f"       ↳ … et {len(manquants) - 4} autre(s)")
    print("═" * 96)
    # ⚠️ Ce signal est GROSSIER par construction : il compare des dates, pas des
    # sémantiques, et ces scripts changent sans cesse. Il tient donc en une ligne par
    # défaut — un garde qui écrit vingt lignes à chaque exécution rend ses vraies alertes
    # invisibles. `--code` donne la liste.
    if suspects:
        print(f"\n⚠️ {len(suspects)} artefact(s) antérieur(s) au dernier correctif de code "
              f"({datetime.fromtimestamp(tc):%d/%m %H:%M}) — `--code` pour la liste.")
        print("   Une tâche longue porte le code de son DÉBUT, pas de sa fin.")
        if code:
            for c in suspects:
                print(f"     {c}")
            print("   À refaire seulement si le correctif touchait ce qu'elle mesure ; "
                  "supprimer l'artefact suffit, le plan le re-listera.")
    print(f"\n{reste} tâche(s) restante(s) · lancer :  scripts/reprise/relancer.sh")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--taches", action="store_true", help="liste pour file_ressource.sh")
    ap.add_argument("--tout", action="store_true")
    ap.add_argument("--code", action="store_true",
                    help="lister les artefacts antérieurs au dernier correctif de code")
    sys.exit(main(**vars(ap.parse_args())))
