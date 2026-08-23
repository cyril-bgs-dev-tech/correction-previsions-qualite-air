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

MAX = "★ MAXIMALE — PARTOUT"


def main(polluant: str, horizon: int, axe: str, support_complet: bool,
         familles: str) -> int:
    fam = sorted(x.strip() for x in familles.split(",") if x.strip())
    if len(fam) < 2:
        raise SystemExit("--familles attend au moins deux noms séparés par des virgules")
    suff = "_sc" if support_complet else ""
    ref = RACINE / f"reports/methode_maximale_{polluant}_h{horizon}{suff}.csv"
    if not ref.exists():
        raise SystemExit(f"référence absente : {ref.name} — lancer la pile complète d'abord")

    cmd = [sys.executable, "-u", str(RACINE / "scripts/methode_maximale.py"),
           "--polluant", polluant, "--horizon", str(horizon), "--exclure", ",".join(fam)]
    if support_complet:
        cmd.append("--support-complet")
    print("  " + " ".join(cmd[2:]), flush=True)
    subprocess.run(cmd, check=False)

    # Le verdict porte sur l'ARTEFACT, jamais sur le code de sortie (§ 0-C).
    sans = RACINE / (f"reports/methode_maximale_{polluant}_h{horizon}{suff}"
                     f"_sans-{'-'.join(fam)}.csv")
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
    # La lecture n'est pas « joint > somme » ou l'inverse : c'est le SENS de l'écart.
    if somme < cout - 0.05:
        lecture = ("les retraits individuels SOUS-ESTIMENT le retrait joint : les familles "
                   "sont REDONDANTES, chacune masque l'autre à l'ablation")
    elif somme > cout + 0.05:
        lecture = ("les retraits individuels SURESTIMENT le retrait joint : les familles "
                   "se NUISENT en partie, la pile gagne à en perdre une")
    else:
        lecture = "retraits additifs : les familles portent de l'information disjointe"

    print(f"\n{'═' * 82}")
    print(f"ABLATION JOINTE · {polluant} · {' + '.join(fam)} · "
          f"pile {'auditable' if support_complet else 'comparable'} · "
          f"{fa[0]} ({fa[1]} mois)")
    print(f"{'═' * 82}")
    print(f"  pile complète                    {ga[MAX]:+7.2f} %")
    print(f"  pile SANS {', '.join(fam):<22s}  {gb[MAX]:+7.2f} %")
    print(f"  → coût du retrait joint          {cout:+7.2f} pt")
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
    a.add_argument("--familles", default="profil,fourier",
                   help="familles à retirer ensemble, séparées par des virgules")
    sys.exit(main(**vars(a.parse_args())))
