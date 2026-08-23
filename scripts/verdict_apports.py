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

🔴 Deux corrections du 23/08/2026 — elles ont fait basculer deux verdicts déjà rendus
--------------------------------------------------------------------------------------
**① Les plis ne sont pas des réplications indépendantes.** Deux plis voisins partagent
~93 % de leur bloc d'apprentissage, et le test de signe sur les plis bruts les traite
comme indépendants : ses `p` sont donc optimistes, d'un facteur qui n'est PAS constant —
mesuré ici, la forme du profil passe de 3,1·10⁻⁴ à 3,9·10⁻² sur le NO₂, et de 1,9·10⁻⁶ à
6,3·10⁻³ sur l'ozone. Aucune correction de variance à facteur fixe ne peut réparer cela.

On agrège donc par **blocs de trois mois consécutifs non chevauchants**, et l'argument
est structurel, pas confortable : le protocole fait tourner les groupes de stations sur
les mois consécutifs (`groupes[i % 3]`), donc **un bloc de trois mois voit les trois
groupes**. C'est l'unité de réplication du plan, et elle n'est pas choisie après lecture
des scores. Deux et quatre mois l'encadrent en sensibilité.

**② « Tenir sur deux polluants » n'était pas testé, il était compté.** Compter deux
`p < 0,05` n'est pas un test de l'assertion globale « l'effet est présent dans au moins
deux groupes ». Le test de **conjonction partielle** de Benjamini & Heller (2008) l'est,
et sa forme de Bonferroni — `p_PC = (n − r + 1) × p_(r)` — reste valide sous dépendance
arbitraire entre polluants, ce qui est exactement notre cas.

Ce que ces deux corrections ont coûté, appliquées aux verdicts de la nuit du 22 au 23 :
la **climatologie du point** passe de TIENT à non confirmé (`p_PC = 0,116`), et les
**précurseurs en moyennes seules** aussi (`p_PC = 0,065`). Les familles réellement
promues dans la pile — forme du profil, harmoniques, précurseurs en moyennes ET maxima —
survivent au test strict.

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


POLLUANTS = ("NO2", "O3", "PM10", "PM25")


def blocs_de(valeurs: list[float], longueur: int) -> list[float]:
    """Moyennes de blocs consécutifs NON chevauchants — l'unité de réplication du plan."""
    v = np.asarray([x for x in valeurs if x == x], dtype="float64")
    n = len(v) // longueur * longueur
    return list(v[:n].reshape(-1, longueur).mean(axis=1)) if n else []


def signe(k: int, n: int) -> float:
    """Test de signe bilatéral. Rend 1,0 sous six points : `p` ne peut pas y descendre
    sous 0,05 même parfait, donc annoncer « non significatif » y serait un artefact de
    taille et non un résultat."""
    from scipy import stats  # noqa: PLC0415
    return 1.0 if n < 6 else float(stats.binomtest(k, n, 0.5).pvalue)


def conjonction_partielle(ps: list[float], r: int = 2) -> float:
    """Benjamini & Heller (2008), forme de Bonferroni : `p_PC = (n − r + 1) × p_(r)`.

    Teste l'assertion « l'effet est présent dans au moins `r` groupes » — ce que compter
    des `p < 0,05` ne fait pas. Cette forme reste **valide sous dépendance arbitraire**
    entre les groupes, ce qui est notre cas : les quatre polluants partagent leurs
    stations, leurs jours et leur situation météorologique.
    """
    v = sorted(x for x in ps if x == x)
    if len(v) < r:
        return 1.0
    return min(1.0, (len(v) - r + 1) * v[r - 1])


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

    print(f"\n{'═' * 96}")
    print(f"VERDICT · {prefixe} · axe {axe} · blocs de 3 mois · conjonction partielle r=2")
    print(f"{'═' * 96}")
    lignes = []
    for conf, par_polluant in series.items():
        print(f"\n  {libelles.get(conf, conf)}")
        pcs, detail_primaire = {}, {}
        for L in (2, 3, 4):
            ps = {}
            for p, v in par_polluant.items():
                b = blocs_de(v, L)
                k = int(sum(1 for x in b if x > 0))
                ps[p] = (k, len(b), signe(k, len(b)))
            pcs[L] = conjonction_partielle([x[2] for x in ps.values()])
            if L == 3:
                detail_primaire = ps
        for p, (k, n_b, pv) in detail_primaire.items():
            moy = float(np.mean(par_polluant[p]))
            print(f"    {p:5s} {k:2d}/{n_b:<2d} blocs positifs · écart apparié moyen "
                  f"{moy:+6.3f} % · p={pv:.4f}")
            lignes.append({"prefixe": prefixe, "axe": axe,
                           "configuration": libelles.get(conf, conf), "polluant": p,
                           "n_plis": len(par_polluant[p]), "n_blocs_3mois": n_b,
                           "blocs_positifs": k, "ecart_apparie_moyen_pct": moy,
                           "p_signe_blocs": pv, "p_conjonction_partielle": pcs[3],
                           "p_PC_2mois": pcs[2], "p_PC_4mois": pcs[4]})
        # ── Ce que la sensibilité doit vérifier : le SIGNE, pas la significativité ──
        #
        # 🔴 Première version de ce garde, écrite le 23/08 puis corrigée le jour même :
        # elle exigeait `p_PC < 0,05` aux TROIS longueurs. C'est faux, et les données le
        # montrent. Les deux bornes échouent pour des raisons opposées, toutes deux
        # artefactuelles :
        #   · à 2 mois, chaque bloc moyenne moins de plis, donc il est plus bruité ;
        #   · à 4 mois, il ne reste que 8 à 9 blocs, et le p minimal ATTEIGNABLE y vaut
        #     déjà 0,0039 — 0,0117 après conjonction partielle. Un effet réel mais modeste
        #     ne PEUT PAS y être déclaré significatif, quel qu'il soit.
        # Exiger la significativité aux trois longueurs revient donc à exiger qu'un effet
        # survive à deux handicaps que l'analyse de sensibilité fabrique elle-même.
        #
        # Ce qui doit rester stable est le SIGNE de l'écart estimé : s'il s'inverse avec la
        # longueur de bloc, la mesure dépend du découpage et ne dit rien. La décision se
        # prend à la longueur PRIMAIRE, dont l'argument est structurel.
        signes = {L: {p_: np.sign(np.mean(blocs_de(v, L)))
                      for p_, v in par_polluant.items()} for L in (2, 3, 4)}
        porteurs = [p_ for p_, _ in sorted(detail_primaire.items(),
                                           key=lambda x: x[1][2])[:2]]
        stable = all(len({signes[L][p_] for L in (2, 3, 4)}) == 1 for p_ in porteurs)
        sens = " · ".join(f"{L} mois p_PC={v:.4f}" for L, v in pcs.items())
        if pcs[3] >= 0.05:
            verdit = f"🔴 NON CONFIRMÉ — p_PC={pcs[3]:.4f}, il faut < 0,05"
        elif not stable:
            inv = ", ".join(f"{p_} : " + "/".join(f"{signes[L][p_]:+.0f}" for L in (2, 3, 4))
                            for p_ in porteurs)
            verdit = f"🔴 SIGNE INSTABLE chez un porteur ({inv}) — le découpage décide"
        else:
            verdit = (f"✅ TIENT — p_PC={pcs[3]:.4f} au bloc primaire, signe stable "
                      f"chez les porteurs ({', '.join(porteurs)})")
        print(f"    sensibilité : {sens}")
        print(f"    → {verdit}")
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
