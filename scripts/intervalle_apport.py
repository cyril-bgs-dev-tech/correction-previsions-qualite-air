#!/usr/bin/env python3
"""L'intervalle qui manquait — apport apparié de la spéciation, par bootstrap circulaire.

Le trou que ce script comble
------------------------------
Le dossier publiait quatre gains **sans aucun intervalle** sur son protocole principal. Le
seul intervalle disponible venait d'un bootstrap sur l'axe *temporel*, un autre corpus et un
autre découpage — donc inutilisable ici.

Pourquoi un bootstrap CIRCULAIRE PAR BLOCS, et pas un tirage sur les plis
--------------------------------------------------------------------------
Les plis ne sont pas indépendants, et deux mécanismes s'y opposent :

1. **la rotation des groupes de stations.** Le protocole répartit les stations en 3 groupes
   et fait tourner le groupe de test (`i mod 3`) : deux plis distants de trois mois testent
   donc **exactement les mêmes stations** ;
2. **le recouvrement des apprentissages.** Deux plis partagent ~93 % de leurs lignes
   d'entraînement.

Un bootstrap qui rééchantillonnerait les plis un par un les traiterait comme indépendants et
rendrait un intervalle trop étroit. Des **blocs contigus de trois mois** capturent un cycle
complet de rotation ; la version à six mois est la sensibilité obligatoire — si le verdict
change entre les deux, il n'est pas robuste.

Ce qui est rééchantillonné
----------------------------
L'objet apparié : pour chaque pli, `RMSE_cams`, `RMSE_sans` et `RMSE_avec` sur les **mêmes
lignes**, avec la même graine et le même découpage. On reconstruit les RMSE agrégées par
`Σ n·RMSE² / Σ n` — jamais par une moyenne de RMSE, qui n'a pas de sens.

La grandeur publiée est l'**amélioration relative** de la pile avec spéciation contre la
pile sans : `100 × (1 − RMSE_avec / RMSE_sans)`. C'est ce qu'un lecteur comprend par
« la spéciation apporte tant », et c'est apparié.

🔴 Seuils fixés avant lecture
------------------------------
* borne basse de l'IC95 **> 0**, après correction de Holm sur les quatre polluants ;
* **même verdict** avec des blocs de trois et de six mois.

Une seule violation, et l'apport n'est pas déclaré pour ce polluant.

Usage  : python3 scripts/intervalle_apport.py [--tirages 10000]
Sortie : reports/intervalle_apport_speciation.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.rapport import ecrire_rapport  # noqa: E402

POLLUANTS = ("NO2", "O3", "PM10", "PM25")
AVEC = "★ MAXIMALE — PARTOUT"
SANS = "− speciation (ablation)"
SUFFIXES = ("_spe-core7_sc_sans-feux-membres", "_spe-core7_sc", "_spe-core7", "")


def charger_plis(polluant: str) -> tuple[pd.DataFrame, str]:
    """Le fichier par pli le plus contrôlé disponible — support commun d'abord."""
    for suf in SUFFIXES:
        f = RACINE / f"reports/methode_maximale_{polluant}_h2{suf}_par_pli.csv"
        if f.exists():
            t = pd.read_csv(f)
            a = t[t["configuration"].str.contains("MAXIMALE — PARTOUT", na=False)]
            s = t[t["configuration"].str.contains("− speciation", na=False)]
            if len(a) and len(s):
                m = a.set_index("mois").join(s.set_index("mois"), lsuffix="_avec",
                                             rsuffix="_sans", how="inner")
                # Les deux configurations doivent porter EXACTEMENT les mêmes plis et les
                # mêmes effectifs — sinon la différence n'est pas appariée (§ 2 quater).
                if not (m["n_test_avec"] == m["n_test_sans"]).all():
                    raise SystemExit(f"{polluant} : effectifs de test différents entre "
                                     f"configurations — la comparaison n'est pas appariée")
                if not np.allclose(m["rmse_cams_avec"], m["rmse_cams_sans"]):
                    raise SystemExit(f"{polluant} : RMSE CAMS différentes entre "
                                     f"configurations — les lignes ne sont pas les mêmes")
                return m.sort_index(), suf or "(publié)"
    raise SystemExit(f"aucun fichier par pli exploitable pour {polluant}")


def agreger(n: np.ndarray, rmse: np.ndarray) -> float:
    """RMSE globale d'un ensemble de plis : Σ n·RMSE² / Σ n, jamais la moyenne des RMSE."""
    return float(np.sqrt(np.sum(n * rmse ** 2) / np.sum(n)))


def apport(n, r_sans, r_avec) -> float:
    return 100.0 * (1.0 - agreger(n, r_avec) / agreger(n, r_sans))


def bootstrap(m: pd.DataFrame, bloc: int, tirages: int, graine: int) -> np.ndarray:
    """Bootstrap circulaire par blocs contigus de `bloc` mois."""
    rng = np.random.default_rng(graine)
    n = m["n_test_avec"].to_numpy(dtype=float)
    rs, ra = m["rmse_corrige_sans"].to_numpy(), m["rmse_corrige_avec"].to_numpy()
    k = len(m)
    n_blocs = int(np.ceil(k / bloc))
    out = np.empty(tirages)
    for t in range(tirages):
        # départs tirés au hasard, blocs pris circulairement — le corpus est traité comme
        # un anneau pour que chaque pli ait la même chance d'entrer, bords compris.
        deps = rng.integers(0, k, n_blocs)
        idx = np.concatenate([(np.arange(d, d + bloc) % k) for d in deps])[:k]
        out[t] = apport(n[idx], rs[idx], ra[idx])
    return out


def holm(p: dict[str, float], alpha: float = 0.05) -> dict[str, bool]:
    """Holm–Bonferroni : la correction qui préserve le contrôle du FWER sans supposer
    l'indépendance des tests, contrairement à Šidák."""
    ordre = sorted(p, key=p.get)
    seuils, rejette, encore = {}, {}, True
    for i, cle in enumerate(ordre):
        seuils[cle] = alpha / (len(p) - i)
        encore = encore and p[cle] <= seuils[cle]
        rejette[cle] = encore
    return rejette


def main(tirages: int, graine: int) -> int:
    lignes = []
    p_val: dict[str, float] = {}
    for pol in POLLUANTS:
        m, source = charger_plis(pol)
        n = m["n_test_avec"].to_numpy(dtype=float)
        point = apport(n, m["rmse_corrige_sans"].to_numpy(), m["rmse_corrige_avec"].to_numpy())
        ligne = {"polluant": pol, "source": source, "n_plis": len(m),
                 "n_jours_station": int(n.sum()), "apport_pct": point}
        for bloc in (3, 6):
            ech = bootstrap(m, bloc, tirages, graine + bloc)
            bas, haut = np.percentile(ech, [2.5, 97.5])
            # p unilatéral : part des tirages qui n'atteignent pas zéro.
            p = float(np.mean(ech <= 0))
            ligne |= {f"ic_bas_b{bloc}": bas, f"ic_haut_b{bloc}": haut,
                      f"p_b{bloc}": p, f"positif_b{bloc}": bool(bas > 0)}
            if bloc == 3:
                p_val[pol] = max(p, 1.0 / tirages)   # jamais 0 : borné par la résolution
        lignes.append(ligne)

    t = pd.DataFrame(lignes)
    # 🔴 Les quatre polluants doivent porter la MÊME pile. Les suffixes peuvent différer —
    # le garde de couverture écarte déjà membres et feux sur NO₂/O₃/PM10, alors que PM2,5
    # exige une exclusion explicite — mais le CONTENU doit coïncider, sinon les colonnes du
    # tableau final ne se comparent pas. On vérifie les étages, pas les noms de fichiers.
    piles = {}
    for pol in POLLUANTS:
        for suf in SUFFIXES:
            f = RACINE / f"reports/methode_maximale_{pol}_h2{suf}.csv"
            if f.exists() and (RACINE / f"reports/methode_maximale_{pol}_h2{suf}_par_pli.csv").exists():
                cfg = pd.read_csv(f)["configuration"]
                piles[pol] = tuple(sorted(c.strip("+ ") for c in cfg if c.startswith("+")))
                break
    distinctes = set(piles.values())
    if len(distinctes) != 1:
        for pol, pile in piles.items():
            print(f"    {pol:6s} {len(pile)} étages : {', '.join(pile)}")
        raise SystemExit(f"PILES DIFFÉRENTES entre polluants ({len(distinctes)} variantes) — "
                         f"les colonnes du tableau ne seraient pas comparables. "
                         f"Relancer les manquants avec --exclure.")
    print(f"  pile commune vérifiée : {', '.join(next(iter(distinctes)))}\n")

    rej = holm(p_val)
    t["holm_rejette"] = t["polluant"].map(rej)
    # Le verdict EXIGE les deux tailles de bloc — une stabilité qui dépend du bloc n'en est pas.
    t["declarable"] = t["positif_b3"] & t["positif_b6"] & t["holm_rejette"]

    print(f"  Bootstrap circulaire par blocs · {tirages:,} tirages · graine {graine}\n")
    print(f"  {'':6s} {'apport':>7s} {'IC95 blocs de 3 mois':>24s} {'IC95 blocs de 6':>20s} "
          f"{'p':>8s} {'Holm':>5s} {'verdict':>10s}")
    for r in t.itertuples():
        print(f"  {r.polluant:6s} {r.apport_pct:+6.2f}% "
              f"[{r.ic_bas_b3:+6.2f} ; {r.ic_haut_b3:+6.2f}]      "
              f"[{r.ic_bas_b6:+6.2f} ; {r.ic_haut_b6:+6.2f}] {r.p_b3:8.4f} "
              f"{'✓' if r.holm_rejette else '✗':>5s} "
              f"{'DÉCLARABLE' if r.declarable else 'non déclaré':>10s}")
    print(f"\n  {t['n_plis'].iloc[0]} plis · {t['n_jours_station'].sum():,} jours-station")
    for r in t.itertuples():
        print(f"    {r.polluant:6s} lit {r.source}")
    if not t["declarable"].all():
        manque = list(t.loc[~t["declarable"], "polluant"])
        print(f"  🔴 non déclarable pour : {', '.join(manque)} — l'apport ne se cite pas "
              f"pour ce·s polluant·s.")

    ecrire_rapport(t, RACINE / "reports/intervalle_apport_speciation.csv",
                   contexte={"axe": "double aveugle", "echeance": "j1"},
                   attendues=["polluant", "apport_pct", "ic_bas_b3", "declarable"])
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--tirages", type=int, default=10000)
    a.add_argument("--graine", type=int, default=20260817)
    n = a.parse_args()
    raise SystemExit(main(n.tirages, n.graine))
