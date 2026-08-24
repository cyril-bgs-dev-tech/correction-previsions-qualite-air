#!/usr/bin/env python3
"""Le seuil de décision, calibré sous le plan RÉEL — chantier ③.

Le défaut mesuré
-----------------
La conjonction partielle de Benjamini-Heller, forme de Bonferroni
`p_PC = (n − r + 1) × p_(r)`, est valide sous dépendance arbitraire. Elle est aussi
**extrêmement conservatrice** : mesurée par permutation sous le plan exact, sa taille
réelle vaut **0,0015** pour un seuil annoncé à 0,05 — soit une marge de **34 ×**.

Conséquence : des familles dont les quatre polluants vont dans le même sens sont classées
« non confirmé » alors que la procédure, à son niveau nominal, les accepterait. On perd de
la puissance qu'on croyait dépenser ailleurs.

⚠️ **Ce n'est PAS un assouplissement post hoc.** Le seuil n'est pas déplacé pour faire
passer un résultat : il est calculé sous H₀ **avant** de regarder les résultats, par la
même permutation par retournement de signe qui sert déjà de test. Un seuil calibré à 5 %
contrôle l'erreur à 5 % ; un seuil de 0,05 sur une statistique de taille 0,0015 la contrôle
à 0,15 %, ce qui n'est pas plus rigoureux — c'est seulement moins puissant.

Ce que le script rend
----------------------
1. la **taille réelle** de la règle à 0,05, par simulation ;
2. le **seuil calibré** — la valeur `t` telle que `P(p_PC < t | H₀) = α` ;
3. le même seuil corrigé du **criblage**, sur K configurations examinées ensemble ;
4. le classement des configurations sous les deux seuils, avec ce qui bascule.

Usage  : python3 scripts/calibrer_decision.py [--axe double] [--alpha 0.05]
Sortie : reports/calibration_decision.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
from calibrer_criblage import charger  # noqa: E402
from verdict_apports import conjonction_partielle  # noqa: E402

POLLUANTS = ("NO2", "O3", "PM10", "PM25")
BLOC = 3


def main(axe: str, horizon: int, alpha: float, tirages: int, graine: int) -> int:
    series = charger(axe, horizon)
    complets = {k: v for k, v in series.items() if len(v) == len(POLLUANTS)}
    if not complets:
        raise SystemExit("aucune configuration complète sur les quatre polluants")
    cles = sorted(complets)
    rng = np.random.default_rng(graine)

    # Un vecteur de signes par (polluant, lot de mois) et par tirage — les configurations
    # d'un même lot les partagent, ce qui préserve leur corrélation.
    signes = {}
    for k in cles:
        for p, (b, sig) in complets[k].items():
            signes.setdefault((p, sig), rng.choice([-1.0, 1.0], size=(tirages, len(b))))

    def p_unilateral(ech, val):
        tri = np.sort(ech)
        return (1.0 + (len(tri) - np.searchsorted(tri, val, side="left"))) / (len(tri) + 1.0)

    pc_obs, pc_nul = {}, np.empty((len(cles), tirages))
    for i, k in enumerate(cles):
        ps_obs, ps_nul = [], []
        for p in POLLUANTS:
            b, sig = complets[k][p]
            nul = (signes[(p, sig)] * b).mean(axis=1)
            ps_obs.append(float(p_unilateral(nul, np.array([b.mean()]))[0]))
            ps_nul.append(p_unilateral(nul, nul))
        pc_obs[k] = conjonction_partielle(ps_obs)
        m = np.sort(np.vstack(ps_nul), axis=0)
        pc_nul[i] = np.minimum(1.0, (len(POLLUANTS) - 2 + 1) * m[1])

    # ① La taille réelle du seuil nominal, ② le seuil calibré pour UNE configuration,
    # ③ le même corrigé du criblage de K configurations examinées ensemble.
    tous = pc_nul.ravel()
    taille = float((tous < alpha).mean())
    seuil_1 = float(np.quantile(tous, alpha))
    seuil_K = float(np.quantile(pc_nul.min(axis=0), alpha))

    print(f"CALIBRATION DE LA DÉCISION · axe {axe} · {len(cles)} configurations · "
          f"{tirages:,} tirages · α = {alpha}")
    print("═" * 98)
    print(f"  taille RÉELLE du seuil nominal {alpha}    : {taille:.4f}  "
          f"(marge {alpha / max(taille, 1e-9):.0f} ×)")
    print(f"  seuil calibré, UNE configuration        : p_PC < {seuil_1:.4f}")
    print(f"  seuil calibré, criblage de {len(cles):2d} ensemble  : p_PC < {seuil_K:.4f}")
    print("═" * 98)
    print(f"  {'configuration':56s} {'p_PC':>8s} {'nominal':>9s} {'calibré':>9s}")
    lignes, bascules = [], 0
    for k in sorted(cles, key=lambda x: pc_obs[x]):
        n_ok, c_ok = pc_obs[k] < alpha, pc_obs[k] < seuil_K
        if c_ok and not n_ok:
            bascules += 1
        marque = " ⬆️ BASCULE" if (c_ok and not n_ok) else ""
        print(f"  {(k[0].replace('apport_', '') + ' · ' + k[1])[:56]:56s} {pc_obs[k]:8.4f} "
              f"{'✅' if n_ok else '🔴':>8s} {'✅' if c_ok else '🔴':>8s}{marque}")
        lignes.append({"axe": axe, "prefixe": k[0], "config": k[1], "p_PC": pc_obs[k],
                       "seuil_nominal": alpha, "taille_reelle": taille,
                       "seuil_calibre_1": seuil_1, "seuil_calibre_criblage": seuil_K,
                       "tient_nominal": bool(n_ok), "tient_calibre": bool(c_ok)})
    print("═" * 98)
    print(f"  {bascules} configuration(s) basculent — elles étaient rejetées par une marge")
    print(f"  de {alpha / max(taille, 1e-9):.0f} × que rien ne justifiait.")
    t = pd.DataFrame(lignes)
    sortie = RACINE / "reports/calibration_decision.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--axe", default="double")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--alpha", type=float, default=0.05)
    a.add_argument("--tirages", type=int, default=6000)
    a.add_argument("--graine", type=int, default=20260824)
    sys.exit(main(**vars(a.parse_args())))
