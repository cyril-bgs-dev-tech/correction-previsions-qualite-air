#!/usr/bin/env python3
"""À précision égale au produit officiel, combien de moments à risque en plus ? — double aveugle.

La question, posée dans les termes d'un service d'alerte
---------------------------------------------------------
Un CSI inchangé dit que le **classifieur** ne discrimine pas mieux. Ce n'est pas la question
d'une AASQA, qui demande : *à un niveau de fausses alertes que j'accepte, combien de journées
à risque est-ce que j'attrape de plus qu'aujourd'hui ?*

Le projet répond déjà à cette question — `front_precision_rappel.py` mesure **1,7× à 4,1×**
plus de dépassements détectés à précision égale — mais sur le protocole **spatial** : stations
exclues, dates connues. Ce script la repose dans la seule condition qui corresponde à un
déploiement : **stations exclues ET période future**, sur les prédictions calibrées du
double aveugle de `calibration_venn_abers.py`.

⚠️ Ce que « officiel » désigne ici, et ce qu'il ne désigne pas
---------------------------------------------------------------
La barre est le **MOS officiel de Copernicus** —
``cams-europe-air-quality-forecasts-optimised-at-observation-sites`` — parce que c'est le seul
produit corrigé dont on dispose ligne à ligne.

**Ce n'est pas le modèle régional d'une AASQA**, que nous n'avons pas, et pour lequel aucun
bilan chiffré public n'existe. Écrire « nous battons la méthode officielle de l'AASQA » serait
faux. La formulation défendable est : *« contre le post-traitement officiel de Copernicus,
sur la période et les stations qu'il n'a pas vues »*.

Pourquoi comparer à précision égale et non à seuil égal
--------------------------------------------------------
Un seuil est une convention interne à chaque produit ; le comparer d'un modèle à l'autre n'a
pas de sens. Ce qui se compare, c'est **le front** : pour chaque niveau de précision que le
service accepte, le rappel atteint. On lit alors le rapport des rappels **au même coût en
fausses alertes**, qui est la grandeur qu'un décideur peut interpréter.

Le produit officiel n'ayant qu'un seul point de fonctionnement — il rend une concentration,
pas une probabilité — c'est **sa** précision qui fixe le niveau de comparaison.

Usage : python3 scripts/front_contre_officiel_double_aveugle.py [--polluant O3] [--seuil 120]
Sortie : reports/front_double_aveugle_{polluant}.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from cible_journaliere import GRANDEUR_PAR_POLLUANT  # noqa: E402
from comparer_mos_officiel import journalier, lire_officiel  # noqa: E402

PREFIXE = {"O3": "o3", "NO2": "no2", "PM25": "pm25"}


def scores(vrai: np.ndarray, annonce: np.ndarray) -> dict:
    a = int((vrai & annonce).sum())
    b = int((~vrai & annonce).sum())
    c = int((vrai & ~annonce).sum())
    return {"detectes": a, "fausses": b, "manques": c,
            "rappel": a / (a + c) if a + c else np.nan,
            "precision": a / (a + b) if a + b else np.nan}


def front(vrai: np.ndarray, score: np.ndarray) -> pd.DataFrame:
    """Le front précision–rappel complet, par balayage du seuil sur le score."""
    ordre = np.argsort(-score)
    v = vrai[ordre]
    detectes = np.cumsum(v)
    annonces = np.arange(1, len(v) + 1)
    return pd.DataFrame({
        "annonces": annonces, "detectes": detectes,
        "precision": detectes / annonces,
        "rappel": detectes / max(int(vrai.sum()), 1),
        "seuil": score[ordre],
    })


def rappel_a_precision(f: pd.DataFrame, precision_cible: float) -> dict:
    """Le meilleur rappel atteignable **sans descendre sous** la précision visée.

    On balaie du seuil le plus haut vers le plus bas et on retient le dernier point dont la
    précision reste au-dessus de la cible. Prendre le maximum du rappel sur *tous* les points
    au-dessus de la cible serait le même résultat, la précision étant décroissante en
    moyenne — mais elle ne l'est pas monotonement, et un maximum choisirait un point isolé
    dû au bruit.
    """
    admissibles = f[f["precision"] >= precision_cible]
    if admissibles.empty:
        return {"rappel": np.nan, "precision": np.nan, "annonces": np.nan,
                "detectes": np.nan, "seuil": np.nan}
    ligne = admissibles.iloc[-1]
    return {"rappel": float(ligne["rappel"]), "precision": float(ligne["precision"]),
            "annonces": int(ligne["annonces"]), "detectes": int(ligne["detectes"]),
            "seuil": float(ligne["seuil"])}


def main(polluant: str, seuil: float) -> int:
    chemin = RACINE / f"reports/calibration_venn_abers_{polluant}_predictions.csv"
    if not chemin.exists():
        raise SystemExit(f"{chemin.name} absent — lancer d'abord "
                         f"scripts/calibration_venn_abers.py --polluant {polluant}")
    p = pd.read_csv(chemin, parse_dates=["jour"])
    p["jour"] = p["jour"].dt.tz_localize(None) if p["jour"].dt.tz else p["jour"]
    print(f"{polluant} · {len(p):,} jours-station en double aveugle · "
          f"{p['station_id'].nunique()} stations · {int(p['cible'].sum())} dépassements de "
          f"{seuil:g} µg/m³\n"
          f"  période {p['jour'].min():%Y-%m-%d} → {p['jour'].max():%Y-%m-%d}", flush=True)

    # ── Le produit officiel, sur EXACTEMENT les mêmes couples ────────────────────
    archives = sorted((RACINE / "data/raw/cams_mos_officiel")
                      .glob(f"{PREFIXE[polluant]}_2024*.zip"))
    if not archives:
        raise SystemExit(f"aucune archive du MOS officiel pour {polluant}")
    off = pd.concat([journalier(lire_officiel(a), ["officiel_mos"],
                                GRANDEUR_PAR_POLLUANT[polluant]) for a in archives],
                    ignore_index=True)
    off["jour"] = pd.to_datetime(off["jour"])
    off["jour"] = off["jour"].dt.tz_localize(None) if off["jour"].dt.tz else off["jour"]

    avant = len(p)
    d = p.merge(off, on=["station_id", "jour"], how="inner", validate="one_to_one")
    print(f"  {len(d):,} couples communs au produit officiel "
          f"({100 * len(d) / avant:.0f} % conservés)", flush=True)
    if len(d) < avant * 0.5:
        raise SystemExit("moins de la moitié des couples se retrouvent dans le produit "
                         "officiel — la comparaison porterait sur un autre échantillon")
    if int(d["cible"].sum()) < 100:
        raise SystemExit(f"{int(d['cible'].sum())} dépassements après jointure — trop peu")

    vrai = d["cible"].to_numpy().astype(bool)

    # ── Le point de fonctionnement du produit officiel : il n'en a qu'un ─────────
    annonce_off = (d["officiel_mos"] >= seuil).to_numpy()
    s_off = scores(vrai, annonce_off)
    print(f"\n{'─' * 84}")
    print(f"MOS officiel de Copernicus · son unique point de fonctionnement")
    print(f"  rappel {s_off['rappel']:.3f} · précision {s_off['precision']:.3f} · "
          f"{s_off['detectes']} détectés · {s_off['manques']} manqués · "
          f"{s_off['fausses']} fausses")

    # ── Nos fronts, à SA précision ──────────────────────────────────────────────
    voies = {"CAMS brut seuillé": None,
             "notre score brut": "p_cvap_brut",
             "notre proba calibrée (CVAP)": "p_cvap",
             "notre proba calibrée (IVAP)": "p_ivap"}
    lignes = [{"voie": "MOS officiel Copernicus", **s_off, "rapport_rappel": 1.0}]
    print(f"\n{'─' * 84}")
    print(f"À **précision égale** ({s_off['precision']:.3f}) — le seul niveau comparable")
    print(f"{'─' * 84}")
    print(f"  {'voie':30s} {'rappel':>7s} {'précis.':>8s} {'détectés':>9s} "
          f"{'manqués':>8s} {'×':>6s}")
    print(f"  {'MOS officiel Copernicus':30s} {s_off['rappel']:7.3f} "
          f"{s_off['precision']:8.3f} {s_off['detectes']:9d} {s_off['manques']:8d} "
          f"{1.0:6.2f}")
    for nom, colonne in voies.items():
        if colonne is None:
            continue
        f = front(vrai, d[colonne].to_numpy())
        r = rappel_a_precision(f, s_off["precision"])
        if not np.isfinite(r["rappel"]):
            print(f"  {nom:30s} précision inatteignable")
            continue
        rapport = r["rappel"] / s_off["rappel"] if s_off["rappel"] else np.nan
        manques = int(vrai.sum()) - r["detectes"]
        lignes.append({"voie": nom, "detectes": r["detectes"], "manques": manques,
                       "fausses": r["annonces"] - r["detectes"], "rappel": r["rappel"],
                       "precision": r["precision"], "rapport_rappel": rapport})
        print(f"  {nom:30s} {r['rappel']:7.3f} {r['precision']:8.3f} "
              f"{r['detectes']:9d} {manques:8d} {rapport:6.2f}")

    t = pd.DataFrame(lignes)
    sortie = RACINE / f"reports/front_double_aveugle_{polluant}.csv"
    t.to_csv(sortie, index=False)

    print(f"\n{'─' * 84}")
    print("⚠️ « Officiel » = le post-traitement de **Copernicus**, seul produit corrigé")
    print("   disponible ligne à ligne. **Pas** le modèle régional d'une AASQA, dont aucun")
    print("   bilan chiffré public n'existe. Ne jamais écrire « nous battons l'AASQA ».")
    print("\n⚠️ Et ce front est mesuré en **double aveugle** — stations exclues ET période")
    print("   future — donc dans la condition la plus dure, celle du déploiement.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--seuil", type=float, default=120.0)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.seuil))
