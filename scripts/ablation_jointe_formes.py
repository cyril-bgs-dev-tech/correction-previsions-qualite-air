#!/usr/bin/env python3
"""Ce que coûte le retrait des DEUX familles de forme du jour — la mesure que l'ablation
famille par famille ne peut pas donner.

Le défaut de lecture que ce script existe pour supprimer — 23/08/2026
----------------------------------------------------------------------
Dans la pile auditable à huit familles, retirer `profil` coûte −0,04 à +0,58 pt selon le
polluant, et retirer `fourier` −0,08 à +0,37. Lu tel quel, on conclurait qu'aucune des deux
ne sert. C'est faux : elles décrivent **la même journée**, l'une par son ampleur (amplitude,
dispersion, pic sur moyenne), l'autre par sa phase et sa structure harmonique. Retirez-en
une, l'autre rattrape — et l'ablation individuelle ne mesure alors que ce qu'elles **ne
partagent pas**.

`reports/ABLATION.md` le dit déjà en toutes lettres : *« deux familles qui captent la même
information s'annulent mutuellement à l'ablation alors que retirer les deux coûterait
cher »*. Ce script mesure ce coût-là.

⚠️ Ce n'est pas une sélection. On ne retire rien de la pile : on chiffre ce que la pile
perdrait si la forme du jour n'y était pas — c'est-à-dire ce que ces huit colonnes valent,
indépendamment de l'ordre dans lequel elles sont entrées.

Usage  : python3 scripts/ablation_jointe_formes.py --polluant NO2 [--support-complet]
Sortie : reports/ablation_jointe_formes_<polluant>_h<n>_<axe>.csv
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


def main(polluant: str, horizon: int, axe: str, support_complet: bool) -> int:
    """On rejoue `methode_maximale` avec `--exclure profil,fourier`, puis on compare au
    MAXIMALE déjà écrit. Rejouer plutôt que réimplémenter garantit que la seule différence
    entre les deux nombres est le retrait des deux familles — mêmes plis, même graine,
    même fenêtre, même code.
    """
    suff = "_sc" if support_complet else ""
    ref = RACINE / f"reports/methode_maximale_{polluant}_h{horizon}{suff}.csv"
    if not ref.exists():
        raise SystemExit(f"référence absente : {ref.name} — lancer la pile complète d'abord")

    cmd = [sys.executable, "-u", str(RACINE / "scripts/methode_maximale.py"),
           "--polluant", polluant, "--horizon", str(horizon),
           "--exclure", "profil,fourier"]
    if support_complet:
        cmd.append("--support-complet")
    print("  " + " ".join(cmd[2:]), flush=True)
    subprocess.run(cmd, check=False)

    # Le verdict porte sur l'ARTEFACT, jamais sur le code de sortie (§ 0-C).
    sans = RACINE / (f"reports/methode_maximale_{polluant}_h{horizon}"
                     f"{suff}_sans-fourier-profil.csv")
    if not sans.exists():
        raise SystemExit(f"aucun artefact écrit : {sans.name}")

    ta = pd.read_csv(ref).set_index("configuration")["gain_pct"]
    tb = pd.read_csv(sans).set_index("configuration")["gain_pct"]
    m = "★ MAXIMALE — PARTOUT"
    cout = float(ta[m] - tb[m])
    ind = {n: float(ta[m] - ta.get(f"− {n} (ablation)", np.nan)) for n in ("profil", "fourier")}
    print(f"\n{'═' * 78}")
    print(f"ABLATION JOINTE · {polluant} · pile {'auditable' if support_complet else 'comparable'}")
    print(f"{'═' * 78}")
    print(f"  pile complète                       {ta[m]:+7.2f} %")
    print(f"  pile SANS profil ni fourier         {tb[m]:+7.2f} %")
    print(f"  → coût du retrait des deux          {cout:+7.2f} pt")
    print(f"     (retraits individuels : profil {ind['profil']:+.2f} · "
          f"fourier {ind['fourier']:+.2f} — leur somme {sum(ind.values()):+.2f} "
          f"{'SOUS-ESTIME' if sum(ind.values()) < cout - 0.05 else 'approche'} le retrait joint)")

    from aq.rapport import ecrire_rapport  # noqa: PLC0415
    from aq.rapport import libelle_echeance  # noqa: PLC0415
    ecrire_rapport(
        pd.DataFrame([{
            "polluant": polluant, "horizon": horizon, "axe": axe,
            "pile": "auditable" if support_complet else "comparable",
            "gain_pile_complete_pct": float(ta[m]), "gain_sans_formes_pct": float(tb[m]),
            "cout_retrait_joint_pt": cout,
            "cout_retrait_profil_pt": ind["profil"],
            "cout_retrait_fourier_pt": ind["fourier"],
            "somme_des_retraits_individuels_pt": float(sum(ind.values()))}]),
        RACINE / f"reports/ablation_jointe_formes_{polluant}_h{horizon}{suff}.csv",
        {"polluant": polluant, "axe": axe, "echeance": libelle_echeance(horizon)},
        attendues=["cout_retrait_joint_pt", "somme_des_retraits_individuels_pt"])
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--axe", default="double")
    a.add_argument("--support-complet", action="store_true")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.axe, n.support_complet))
