#!/usr/bin/env python3
"""Ce que coûte le retrait CONJOINT de plusieurs familles — action A05.

Le défaut de lecture que ce script existe pour supprimer
---------------------------------------------------------
Deux familles qui décrivent la même chose s'annulent à l'ablation individuelle : retirez
l'une, l'autre rattrape, et chacune paraît inutile. `reports/ABLATION.md` le dit déjà —
*« deux familles qui captent la même information s'annulent mutuellement à l'ablation
alors que retirer les deux coûterait cher »*. L'ablation individuelle ne mesure alors que
ce qu'elles **ne partagent pas**.

La question que cela pose à toute famille invisible
----------------------------------------------------
`apport_en_derniere_position.py` trouve quatre familles dont l'apport n'est pas séparable
de zéro, voire négatif : `membres`, `profil`, `tendance`, `feux`. Il y a deux causes
possibles, et elles appellent des décisions opposées :

* **elles sont redondantes** avec une autre famille — le retrait joint coûte cher, il faut
  en garder au moins une ;
* **elles ne valent rien** — le retrait joint ne coûte rien, on les retire toutes.

Ce script tranche, en rejouant `methode_maximale` avec `--exclure` plutôt qu'en
réimplémentant : la seule différence entre les deux nombres est le retrait, puisque les
plis, la graine, la fenêtre et le code sont les mêmes.

🔴 Le garde de fenêtre, et pourquoi il ne peut pas être facultatif
-------------------------------------------------------------------
Retirer une famille **lève sa restriction de support**. Le 23/08, retirer GEOS-CF a
rallongé la fenêtre sans lever celle de la spéciation : la pile réduite tournait sur
36 plis quand la référence en avait 32, et la différence lue mélangeait le retrait avec
quatre mois de plus. Le défaut ne s'est vu que parce qu'une prédiction écrite — « 32
plis » — a été démentie par le journal.

Ici, le script REFUSE de conclure si la fenêtre diffère. Un écart mesuré entre deux
fenêtres n'est pas un écart : c'est deux mesures.

Usage  : python3 scripts/ablation_jointe.py --polluant NO2 --familles feux,tendance
Sortie : reports/ablation_jointe_<familles>_<polluant>_h<n>[_sc].csv
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from verdict_apports import bootstrap_blocs, permutation_blocs  # noqa: E402

MAX = "★ MAXIMALE — PARTOUT"


# Le socle du contrat de produit s'obtient en retirant `geoscf` et `feux` ET en ouvrant la
# fenêtre. Les deux vont ensemble : garder les colonnes GEOS-CF hors de leur couverture
# donnerait au modèle un indicateur d'année déguisé.
HORS_SOCLE = ("feux", "geoscf")


def chemins(polluant: str, horizon: int, fam: list[str], support_complet: bool,
            socle: bool) -> tuple[Path, Path, list[str], str]:
    """(référence, pile réduite, familles à `--exclure`, suffixe du RAPPORT).

    🔴 Le quatrième élément n'est pas cosmétique. Sans lui, l'ablation sur le socle écrirait
    son verdict dans le fichier de l'ablation historique — « une variante écrase sa jumelle »,
    déjà payé une fois sur ce dépôt quand un suffixe couvrait le parquet mais pas la légende.
    Deux mesures différentes ne partagent jamais un nom.

    Le nom de sortie de `methode_maximale` est `_sans-` + les exclusions TRIÉES, puis
    `_fenetre-complete`. Le reconstruire ici plutôt que le deviner : un nom faux ferait
    échouer le contrôle d'artefact — ou pire, comparerait le mauvais fichier.
    """
    base = f"reports/methode_maximale_{polluant}_h{horizon}"
    if socle:
        excl = sorted(set(fam) | set(HORS_SOCLE))
        ref = RACINE / f"{base}_sans-{'-'.join(sorted(HORS_SOCLE))}_fenetre-complete.csv"
        sans = RACINE / f"{base}_sans-{'-'.join(excl)}_fenetre-complete.csv"
        return ref, sans, excl, "_socle"
    suff = "_sc" if support_complet else ""
    return (RACINE / f"{base}{suff}.csv",
            RACINE / f"{base}{suff}_sans-{'-'.join(fam)}.csv", fam, suff)


def main(polluant: str, horizon: int, axe: str, support_complet: bool,
         familles: str, socle: bool = False) -> int:
    fam = sorted(x.strip() for x in familles.split(",") if x.strip())
    if len(fam) < 2:
        raise SystemExit("--familles attend au moins deux noms séparés par des virgules")
    if socle and support_complet:
        raise SystemExit("--socle et --support-complet définissent deux piles différentes : "
                         "en choisir une. Les mêler comparerait deux mesures.")
    if socle and (chevauche := sorted(set(fam) & set(HORS_SOCLE))):
        raise SystemExit(f"⛔ {', '.join(chevauche)} ne fait pas partie du socle — le retirer "
                         f"du socle ne retire rien. Mesurer un module se fait apparié sur "
                         f"son propre support, pas par ablation du socle.")
    ref, sans, excl, suff = chemins(polluant, horizon, fam, support_complet, socle)
    if not ref.exists():
        raise SystemExit(f"référence absente : {ref.name} — lancer la pile complète d'abord")
    # Reprise sur l'ARTEFACT : la pile réduite est un ajustement de vingt minutes, et
    # relire son verdict ne doit pas la refaire. Le contrôle porte sur le contenu — le
    # fichier doit porter la configuration de référence — jamais sur la seule existence.
    # 🔴 La reprise doit vérifier le CORPUS, pas seulement l'existence — 24/08/2026.
    #
    # Sauter l'ajustement quand l'artefact existe est correct tant que la référence n'a pas
    # changé. Elle a changé cette nuit : la spéciation complétée a déplacé la base de 0,17
    # à 0,32 pt, et une pile réduite écrite avant serait comparée à une référence écrite
    # après. Ni la fenêtre ni le nombre de plis ne le montrent — c'est le défaut que
    # l'empreinte des entrées existe pour attraper.
    deja = (sans.exists()
            and MAX in set(pd.read_csv(sans)["configuration"])
            and sans.with_name(sans.name.replace(".csv", "_par_pli.csv")).exists())
    if deja:
        tr, tv = pd.read_csv(ref), pd.read_csv(sans)
        er = str(tr["empreinte_entrees"].iloc[0]) if "empreinte_entrees" in tr else ""
        ev = str(tv["empreinte_entrees"].iloc[0]) if "empreinte_entrees" in tv else ""
        # Les empreintes d'une pile complète et d'une pile RÉDUITE diffèrent forcément —
        # il y a moins de familles. On ne peut donc pas les comparer entre elles : ce qui
        # se compare est leur présence. Une variante SANS empreinte face à une référence
        # qui en porte une date d'avant le corpus corrigé, et doit être refaite.
        if er and not ev:
            print(f"  pile réduite {sans.name} antérieure au corpus actuel "
                  f"(pas d'empreinte, référence {er}) — ajustement REFAIT", flush=True)
            deja = False
        # 🔴 Et la DATE tranche quand aucune empreinte n'existe — 24/08/2026.
        #
        # Les deux fichiers peuvent être antérieurs à l'empreinte : le test ci-dessus est
        # alors muet, et la reprise a comparé une référence du 24/08 à une pile réduite du
        # 23/08 18 h 45, en annonçant « REDONDANTES, +0,317 pt ». Deux corpus, un verdict.
        #
        # Une pile réduite plus ANCIENNE que sa référence n'a pas pu voir les mêmes
        # données. C'est plus grossier qu'une empreinte, mais ça ne dépend de rien.
        elif sans.stat().st_mtime < ref.stat().st_mtime:
            from datetime import datetime  # noqa: PLC0415
            print(f"  pile réduite {sans.name} ({datetime.fromtimestamp(sans.stat().st_mtime):%d/%m %H:%M})"
                  f" plus ANCIENNE que sa référence "
                  f"({datetime.fromtimestamp(ref.stat().st_mtime):%d/%m %H:%M})"
                  f" — ajustement REFAIT", flush=True)
            deja = False
    if deja:
        print(f"  pile réduite déjà écrite : {sans.name} — ajustement sauté", flush=True)
    else:
        cmd = [sys.executable, "-u", str(RACINE / "scripts/methode_maximale.py"),
               "--polluant", polluant, "--horizon", str(horizon), "--exclure", ",".join(excl)]
        if support_complet:
            cmd.append("--support-complet")
        if socle:
            cmd += ["--fenetre", "complete"]
            # 🔴 Épingler la fenêtre sur celle de la RÉFÉRENCE, systématiquement.
            #
            # Retirer une famille lève sa restriction de support : sur le socle, retirer
            # `precurseurs` rend 2023-08 et la pile réduite passe à 34 mois quand la
            # référence en a 33. Le garde de fenêtre refuserait alors — à raison, mais la
            # mesure serait perdue.
            #
            # Épingler sans condition plutôt que « si ça déborde » : la condition serait un
            # jugement à porter à chaque appel, et c'est exactement le genre de vigilance qui
            # a échoué ailleurs sur ce dépôt. Quand les fenêtres coïncident déjà, l'épinglage
            # imprime « rien à épingler » et ne fait rien.
            ref_plis = ref.with_name(ref.name.replace(".csv", "_par_pli.csv"))
            if ref_plis.exists():
                cmd += ["--mois-de", str(ref_plis.relative_to(RACINE))]
        print("  " + " ".join(cmd[2:]), flush=True)
        subprocess.run(cmd, check=False)

    # Le verdict porte sur l'ARTEFACT, jamais sur le code de sortie (§ 0-C).
    if not sans.exists():
        raise SystemExit(f"aucun artefact écrit : {sans.name}")

    ta, tb = pd.read_csv(ref), pd.read_csv(sans)
    # 🔴 Le garde de fenêtre — voir la docstring. Deux fenêtres, deux mesures.
    fa = str(ta["fenetre"].iloc[0]), int(ta["n_mois"].iloc[0])
    fb = str(tb["fenetre"].iloc[0]), int(tb["n_mois"].iloc[0])
    if fa != fb:
        raise SystemExit(
            f"❌ FENÊTRES DIFFÉRENTES — référence {fa[0]} ({fa[1]} mois) contre "
            f"réduite {fb[0]} ({fb[1]} mois). Retirer {', '.join(fam)} a levé une "
            f"restriction de support : l'écart mélangerait le retrait et les mois en plus. "
            f"Relancer les deux avec --support-complet, ou aligner les fenêtres.")

    ga = ta.set_index("configuration")["gain_pct"]
    gb = tb.set_index("configuration")["gain_pct"]
    cout = float(ga[MAX] - gb[MAX])
    ind = {n: float(ga[MAX] - ga.get(f"− {n} (ablation)", np.nan)) for n in fam}
    somme = float(np.nansum(list(ind.values())))

    # 🔴 La lecture ne se tire pas de deux scalaires — corrigé le 23/08/2026
    # -------------------------------------------------------------------------------
    # La première version comparait `somme` à `cout` et concluait « redondantes » dès que
    # la somme était la plus petite. Deux défauts, vus sur le premier résultat réel :
    #
    #   ① elle supposait des apports POSITIFS. Sur NO₂, feux −0,14 et tendance −0,23
    #      donnent somme = −0,37 contre un coût joint de −0,01 : la condition rendait
    #      « REDONDANTES » là où les deux familles ne valent rien, dans un sens comme dans
    #      l'autre. Quand les quantités changent de signe, les étiquettes s'inversent ;
    #   ② surtout, elle interprétait des écarts SOUS LA RÉSOLUTION. −0,01 et −0,37 pt sur
    #      un protocole qui résout ±0,36 ne se distinguent ni l'un de l'autre ni de zéro.
    #
    # On mesure donc l'écart APPARIÉ pli à pli, dont on tire un IC95 et un `p` exact. Une
    # lecture ne s'énonce que si l'écart est résolu ; sinon le résultat est « la pile ne
    # voit pas la différence », qui est une information et non un échec.
    pa = pd.read_csv(str(ref).replace(".csv", "_par_pli.csv"))
    pb = pd.read_csv(str(sans).replace(".csv", "_par_pli.csv"))
    def _serie(t):
        return t[t["configuration"] == MAX].set_index("mois")["gain_pct"]
    paire = pd.concat({"complete": _serie(pa), "reduite": _serie(pb)}, axis=1).dropna()
    ecart = list((paire["complete"] - paire["reduite"]).to_numpy())
    moy, bas, haut, _, _ = bootstrap_blocs(ecart, 3)
    p_plus, p_moins = permutation_blocs(ecart, 3)
    resolu = not (bas <= 0.0 <= haut)
    # 🔴 La marge n'est pas une constante devinée (§ 0-A) : c'est la demi-largeur de l'IC95
    # de CETTE mesure. Comparer `somme` et `moy` à 0,05 près revenait à trancher sous la
    # résolution — le défaut même que ce script a corrigé une heure plus tôt sur son
    # verdict principal, et que j'avais laissé dans la comparaison des deux quantités.
    marge = (haut - bas) / 2.0
    if not resolu:
        lecture = (f"NON RÉSOLU — l'écart apparié vaut {moy:+.3f} pt, IC95 "
                   f"[{bas:+.3f} ; {haut:+.3f}], qui contient zéro. Retirer "
                   f"{' et '.join(fam)} ne change rien que ce plan sache voir.")
    elif moy > 0 and somme < moy - marge:
        lecture = (f"REDONDANTES — le retrait joint ({moy:+.2f}) coûte PLUS que la somme "
                   f"des retraits individuels ({somme:+.2f}) : chacune masque l'autre à "
                   f"l'ablation, et prise seule elle paraît inutile.")
    elif moy > 0 and somme > moy + marge:
        lecture = (f"SUBSTITUABLES — la somme des retraits individuels ({somme:+.2f}) "
                   f"SURESTIME le retrait joint ({moy:+.2f}) : les deux portent en partie "
                   f"la même information, et l'addition la compte deux fois.")
    elif moy > 0:
        # 🔴 Ni redondance ni substitution DÉMONTRÉE n'est la même chose qu'additivité
        # démontrée. L'écart |somme − joint| est sous la résolution : le plan ne les
        # sépare pas, et l'écrire « information disjointe » affirmerait un troisième
        # résultat qu'on n'a pas mesuré. C'est la § 4 ter — signaler une limite ne
        # dispense pas de la nommer correctement.
        lecture = (f"GROUPE RÉEL, STRUCTURE NON DISCRIMINÉE — le retrait joint "
                   f"({moy:+.2f}) est résolu, mais son écart à la somme des individuels "
                   f"({somme:+.2f}) vaut {abs(somme - moy):.2f} pour une résolution de "
                   f"±{marge:.2f} : additif, redondant et substituable sont indiscernables "
                   f"ici.")
    else:
        lecture = ("LA PILE GAGNE À LES PERDRE — le retrait joint AMÉLIORE le score, et "
                   "l'écart est résolu.")

    print(f"\n{'═' * 82}")
    print(f"ABLATION JOINTE · {polluant} · {' + '.join(fam)} · "
          f"pile {'auditable' if support_complet else 'comparable'} · "
          f"{fa[0]} ({fa[1]} mois)")
    print(f"{'═' * 82}")
    print(f"  pile complète                    {ga[MAX]:+7.2f} %")
    print(f"  pile SANS {', '.join(fam):<22s}  {gb[MAX]:+7.2f} %")
    print(f"  → coût du retrait joint          {cout:+7.2f} pt")
    print(f"     apparié sur {len(ecart)} plis : {moy:+.3f} pt · IC95 "
          f"[{bas:+.3f} ; {haut:+.3f}] · p⁺={p_plus:.4f}")
    print(f"     retraits individuels : "
          + " · ".join(f"{n} {v:+.2f}" for n, v in ind.items())
          + f" — somme {somme:+.2f}")
    print(f"     → {lecture}")

    from aq.rapport import ecrire_rapport, libelle_echeance  # noqa: PLC0415
    ligne = {"polluant": polluant, "horizon": horizon, "axe": axe,
             "pile": "auditable" if support_complet else "comparable",
             "familles_retirees": "+".join(fam), "fenetre": fa[0], "n_mois": fa[1],
             "gain_pile_complete_pct": float(ga[MAX]),
             "gain_pile_reduite_pct": float(gb[MAX]),
             "cout_retrait_joint_pt": cout,
             "ecart_apparie_pt": moy, "ic95_bas": bas, "ic95_haut": haut,
             "p_permutation_positif": p_plus, "p_permutation_negatif": p_moins,
             "n_plis_apparies": len(ecart), "resolu": bool(resolu),
             "somme_des_retraits_individuels_pt": somme, "lecture": lecture}
    ligne.update({f"cout_retrait_{n}_pt": v for n, v in ind.items()})
    ecrire_rapport(
        pd.DataFrame([ligne]),
        RACINE / (f"reports/ablation_jointe_{'-'.join(fam)}_{polluant}_h{horizon}{suff}.csv"),
        {"polluant": polluant, "axe": axe, "echeance": libelle_echeance(horizon)},
        attendues=["cout_retrait_joint_pt", "somme_des_retraits_individuels_pt", "lecture"])
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--axe", default="double")
    a.add_argument("--support-complet", action="store_true")
    a.add_argument("--socle", action="store_true",
                   help="mesurer sur le SOCLE du contrat de produit (sans feux ni geoscf, "
                        "fenêtre complète) plutôt que sur la pile historique")
    a.add_argument("--familles", default="profil,fourier",
                   help="familles à retirer ensemble, séparées par des virgules")
    sys.exit(main(**vars(a.parse_args())))
