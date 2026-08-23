#!/usr/bin/env python3
"""Le verdict d'un apport — un polluant ne fait pas un mécanisme.

Ce script ne mesure rien : il **juge** ce que `apport_ratios_echelle.py` et
`apport_leviers_gratuits.py` ont écrit pli par pli. La question qu'il pose est celle de la
règle 0-E : *l'effet tient-il sur au moins deux sous-ensembles indépendants ?*

Les quatre polluants sont les groupes. Pour chacun, la série jugée est l'écart **apparié**
pli à pli entre la configuration candidate et la base — appariée parce que les deux
configurations partagent exactement les mêmes lignes, la même graine et le même découpage,
donc le déplacement commun causé par une partition se soustrait.

Le test est un test de **signe** : ni normalité ni variance commune ne sont supposées.
Un polluant significatif dans l'autre sens ne se tait pas — il réfute, et le motif le nomme.

Usage : python3 scripts/verdict_apports.py --prefixe apport_ratios_echelle --axe double
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval.critere import tient_sur_sous_ensembles  # noqa: E402

POLLUANTS = ("NO2", "O3", "PM10", "PM25")


def main(prefixe: str, horizon: int, axe: str) -> int:
    series: dict[str, dict[str, list[float]]] = {}
    libelles: dict[str, str] = {}
    for p in POLLUANTS:
        f = RACINE / f"reports/{prefixe}_{p}_h{horizon}_{axe}_par_pli.csv"
        if not f.exists():
            print(f"  ✘ absent : {f.name} — ce polluant ne peut pas voter", flush=True)
            continue
        tp = pd.read_csv(f)
        ref = tp["rmse_config1"].to_numpy()
        for c in [c for c in tp.columns if c.startswith("rmse_config") and c != "rmse_config1"]:
            series.setdefault(c, {})[p] = list(100 * (1 - tp[c].to_numpy() / ref))
        r = RACINE / f"reports/{prefixe}_{p}_h{horizon}_{axe}.csv"
        if r.exists():
            t = pd.read_csv(r)
            for k, nom in enumerate(t["configuration"], start=1):
                libelles[f"rmse_config{k}"] = str(nom)
    if not series:
        raise SystemExit(f"aucun fichier « {prefixe}_*_h{horizon}_{axe}_par_pli.csv »")

    print(f"\n{'═' * 92}")
    print(f"VERDICT · {prefixe} · axe {axe} · groupes = polluants (disjoints par construction)")
    print(f"{'═' * 92}")
    lignes = []
    for conf, par_polluant in series.items():
        v = tient_sur_sous_ensembles(par_polluant, minimum=2)
        print(f"\n  {libelles.get(conf, conf)}")
        for p, det in v.par_groupe.items():
            moy = float(np.mean(par_polluant[p]))
            pp = det["part_positive"]
            pv = det["p"]
            print(f"    {p:5s} n={det['n']:3d} · écart apparié moyen {moy:+6.3f} % · "
                  f"plis positifs {'—' if pp is None else f'{100 * pp:5.1f} %'} · "
                  f"p={'—' if pv is None else f'{pv:.4f}'} · {det['verdict']}")
            lignes.append({"prefixe": prefixe, "axe": axe, "configuration":
                           libelles.get(conf, conf), "polluant": p, "n_plis": det["n"],
                           "ecart_apparie_moyen_pct": moy,
                           "part_plis_positifs": pp, "p_signe": pv,
                           "verdict_groupe": det["verdict"]})
        print(f"    → {v}")
    t = pd.DataFrame(lignes)
    sortie = RACINE / f"reports/verdict_{prefixe}_{axe}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--prefixe", default="apport_ratios_echelle")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--axe", default="double")
    n = a.parse_args()
    raise SystemExit(main(n.prefixe, n.horizon, n.axe))
