#!/usr/bin/env python3
"""Ce que chaque famille de la pile paie VRAIMENT — action A05.

La question, et pourquoi la colonne existante n'y répond pas
------------------------------------------------------------
`methode_maximale_*_h2.csv` porte une colonne `apport_marginal_pct`. Elle vaut la
différence à la ligne PRÉCÉDENTE, donc elle mesure l'apport d'une famille **dans l'ordre
d'empilement** — c'est-à-dire en présence de celles d'avant et en l'absence de celles
d'après. Deux conséquences :

* une famille placée tôt encaisse tout ce qu'elle partage avec les suivantes, et les
  suivantes n'en voient rien : c'est le biais de criblage, mesuré ×2 à ×4 sur ce dépôt ;
* sur les lignes d'ablation, la colonne ne veut plus rien dire du tout — elle y compare
  deux configurations qui diffèrent de deux familles, pas d'une.

Le seul apport interprétable est celui de la **dernière position** : `MAXIMALE` moins
`MAXIMALE privée de la famille`. C'est ce que ce script calcule, pli à pli, puis juge
avec l'instrument de `verdict_apports` — bootstrap par blocs de trois mois et conjonction
partielle sur les quatre polluants.

Ce que le verdict ajoute à un simple écart
-------------------------------------------
Un écart moyen ne dit pas s'il est séparable de zéro. `plus_petite_difference.py` mesure
la résolution du protocole — ±0,4 % en médiane sur cet axe — et le script la rappelle en
face de chaque famille. **Une famille dont l'apport tient sous la résolution n'est pas
une petite contribution : c'est une contribution que ce plan d'expérience ne voit pas.**
Elle n'est pas réfutée pour autant ; elle est indécidable ici, et le dire est le résultat.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))
from verdict_apports import (blocs_de, bootstrap_blocs,  # noqa: E402
                            conjonction_partielle, rendre_verdict)

POLLUANTS = ("NO2", "O3", "PM10", "PM25")
REFERENCE = "★ MAXIMALE — PARTOUT"
BLOC = 3


def series_par_famille(polluant: str, suffixe: str) -> dict[str, pd.Series]:
    """Rend {famille: série mensuelle de `gain(MAXIMALE) − gain(sans famille)`}."""
    f = RACINE / "reports" / f"methode_maximale_{polluant}_h2{suffixe}_par_pli.csv"
    if not f.exists():
        return {}
    t = pd.read_csv(f)
    large = t.pivot_table(index="mois", columns="configuration", values="gain_pct")
    if REFERENCE not in large.columns:
        raise SystemExit(f"{f.name} : configuration de référence « {REFERENCE} » absente")
    out = {}
    for c in large.columns:
        if not (c.startswith("−") and c.endswith("(ablation)")):
            continue
        fam = c.split()[1]
        # Jointure sur les mois COMMUNS aux deux configurations : un mois présent d'un
        # seul côté ferait une différence contre du vide, pas un écart apparié.
        paire = large[[REFERENCE, c]].dropna()
        if paire.empty:
            continue
        out[fam] = paire[REFERENCE] - paire[c]
    return out


def main(suffixe: str = "") -> int:
    par_famille: dict[str, dict[str, pd.Series]] = {}
    for p in POLLUANTS:
        for fam, s in series_par_famille(p, suffixe).items():
            par_famille.setdefault(fam, {})[p] = s
    if not par_famille:
        print("❌ aucune ablation trouvée — lancer methode_maximale.py --ablation")
        return 1

    res = {}
    fr = RACINE / "reports" / "plus_petite_difference.csv"
    if fr.exists():
        r = pd.read_csv(fr)
        res = dict(zip(r["polluant"], r["resolution_demi_ic95_pct"]))

    print(f"APPORT EN DERNIÈRE POSITION · pile{suffixe or ' (référence)'} · "
          f"blocs de {BLOC} mois · {len(par_famille)} familles")
    if res:
        print("contexte — résolution typique du protocole (autres contrastes, A04) : "
              + " · ".join(f"{p} ±{v:.2f}" for p, v in sorted(res.items())))
    print("═" * 100)
    lignes, resume = [], []
    for fam in sorted(par_famille, key=lambda f: -np.mean(
            [par_famille[f][p].mean() for p in par_famille[f]])):
        detail, pcs, signes = {}, {}, {}
        for L in (2, BLOC, 4):
            ps = {}
            for p, s in par_famille[fam].items():
                v = list(s.to_numpy())
                moy, bas, haut, p_plus, p_moins = bootstrap_blocs(v, L)
                b = blocs_de(v, L)
                ps[p] = (moy, bas, haut, p_plus, p_moins,
                         int(sum(1 for x in b if x > 0)), len(b))
            pcs[L] = conjonction_partielle([x[3] for x in ps.values()])
            signes[L] = {p: float(np.sign(np.mean(blocs_de(list(s.to_numpy()), L))))
                         for p, s in par_famille[fam].items()}
            if L == BLOC:
                detail = ps
        verdit, porteurs = rendre_verdict(detail, pcs, signes)

        print(f"\n  {fam}")
        for p, (moy, bas, haut, p_plus, p_moins, k, n_b) in detail.items():
            seuil = res.get(p, np.nan)
            # 🔴 Le drapeau porte sur l'IC de CETTE mesure, jamais sur la médiane venue
            # des mesures d'apport — celle-ci vient d'un autre jeu de contrastes, et
            # comparer une estimation à la résolution d'un AUTRE plan est l'axe emprunté
            # que la règle D interdit. La résolution typique reste imprimée une fois, en
            # contexte, pour situer l'ordre de grandeur ; elle ne juge aucune ligne.
            sous = "  · non résolu (l'IC contient 0)" if bas <= 0.0 <= haut else ""
            nuit = "  🔴 NUIT" if p_moins < 0.05 else ""
            print(f"    {p:5s} {moy:+6.3f} pt · IC95 [{bas:+6.3f} ; {haut:+6.3f}] · "
                  f"p⁺={p_plus:.4f} · ({k}/{n_b} blocs){sous}{nuit}")
            lignes.append({"pile": suffixe or "reference", "famille": fam, "polluant": p,
                           "apport_derniere_position_pt": moy, "ic95_bas": bas,
                           "ic95_haut": haut, "p_bootstrap_positif": p_plus,
                           "p_bootstrap_negatif": p_moins, "n_blocs": n_b,
                           "blocs_positifs": k, "non_resolu_ic_contient_zero": bool(bas <= 0.0 <= haut),
                           "resolution_typique_protocole_pct": seuil,
                           "p_conjonction_partielle": pcs[BLOC], "verdict": verdit})
        print(f"    → {verdit}")
        resume.append((fam, np.mean([d[0] for d in detail.values()]), verdit))

    print("\n" + "═" * 100)
    print(f"{'famille':14s} {'apport moyen':>13s}   verdict")
    for fam, moy, verdit in sorted(resume, key=lambda x: -x[1]):
        print(f"{fam:14s} {moy:+12.3f} pt   {verdit.split('—')[0].strip()}")

    t = pd.DataFrame(lignes)
    for c in ("famille", "polluant", "apport_derniere_position_pt", "verdict"):
        if c not in t:
            raise SystemExit(f"colonne absente du rapport : {c}")
    sortie = RACINE / "reports" / f"apport_derniere_position{suffixe}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--suffixe", default="", help="'' (PARTOUT) ou '_sc' (auditable)")
    sys.exit(main(**vars(a.parse_args())))
