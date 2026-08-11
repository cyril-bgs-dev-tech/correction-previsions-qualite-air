#!/usr/bin/env python3
"""Combien de stations basculent en dépassement au seuil 2030 ?

La question, et pourquoi elle n'avait jamais été posée
------------------------------------------------------
La directive (UE) 2024/2881 fait deux choses que tout le monde a lues séparément :

  ① elle rend la **modélisation obligatoire** dans toutes les zones où un polluant dépasse
     une valeur limite ou une valeur cible ;
  ② elle **divise par deux** les valeurs limites annuelles au 1ᵉʳ janvier 2030.

Leur produit n'est écrit nulle part : **abaisser le seuil multiplie mécaniquement le nombre
de zones où modéliser devient une obligation légale.** Une station conforme aujourd'hui peut
être en dépassement en 2030 sans qu'un gramme de plus n'ait été émis.

Ce script fait le calcul local que personne n'avait fait. Les seuils sont publics depuis
octobre 2024, les mesures sont dans le dépôt : il ne manquait que de regarder.

Les conventions, déclarées avant la mesure
-------------------------------------------
- **Valeurs limites en moyenne annuelle** uniquement. L'ozone n'en a pas — il relève de
  valeurs cibles sur le maximum 8 h — il est donc **exclu et l'exclusion est imprimée**,
  jamais silencieuse.
- **Validité** : on garde `validite > 0`, exactement la convention de `ingerer_lcsqa.py`.
  Le filtre `== 1` qui régnait avant le 01/08/2026 jetait des données valides au nouvel
  étalon — 13 mois d'ozone. Ne pas le réintroduire ici.
- **Couverture** : une moyenne annuelle n'est retenue qu'au-dessus d'un taux de saisie
  (défaut 75 %). La colonne `taux_saisie` du flux est **vide sur 100 % des lignes** —
  vérifié — donc la couverture est **recalculée** depuis le nombre d'heures présentes.
- Les stations écartées pour couverture insuffisante sont **comptées et imprimées**
  (§ 2 quater : une condition de disponibilité ne change jamais le périmètre en silence).

Usage : python3 scripts/seuils_2030.py [--annee 2025] [--capture 0.75]
Sortie : reports/seuils_2030.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

# ── Valeurs limites en MOYENNE ANNUELLE, µg/m³ ──────────────────────────────────────────
# Sources : directive 2008/50/CE (actuelles) et directive (UE) 2024/2881 annexe I (2030).
VL = {
    "NO2":  {"actuelle": 40.0, "en_2030": 20.0},
    "PM10": {"actuelle": 40.0, "en_2030": 20.0},
    "PM25": {"actuelle": 25.0, "en_2030": 10.0},
}
# L'ozone n'a PAS de valeur limite annuelle : valeur cible sur le maximum journalier des
# moyennes 8 h. Le comparer à un seuil annuel n'aurait aucun sens réglementaire.
SANS_VL_ANNUELLE = ("O3",)

NOM = {"NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}


def charger_annee(annee: int) -> pd.DataFrame:
    """Les douze mois de l'année, ou l'erreur qui nomme ceux qui manquent (§ 4)."""
    attendus = [f"{annee}{m:02d}" for m in range(1, 13)]
    fichiers = {a: RACINE / f"data/interim/lcsqa/lcsqa_{a}.parquet" for a in attendus}
    manquants = [a for a, f in fichiers.items() if not f.exists()]
    if manquants:
        raise SystemExit(f"année {annee} incomplète — mois absents : {', '.join(manquants)}. "
                         f"Choisir une année pleine avec --annee.")
    cols = ["station_id", "polluant", "timestamp_utc", "valeur", "validite"]
    t = pd.concat([pd.read_parquet(f, columns=cols) for f in fichiers.values()],
                  ignore_index=True)
    avant = len(t)
    t = t[t["validite"] > 0].dropna(subset=["valeur"])
    print(f"  {annee} · {avant:,} mesures lues · {len(t):,} valides "
          f"({len(t) / avant:.1%}) · 12 mois sur 12", flush=True)
    return t


def moyennes_annuelles(t: pd.DataFrame, annee: int, capture: float) -> pd.DataFrame:
    """Moyenne par station × polluant, avec le taux de saisie RECALCULÉ."""
    heures = 8784 if (annee % 4 == 0 and (annee % 100 != 0 or annee % 400 == 0)) else 8760
    g = (t.groupby(["station_id", "polluant"])
           .agg(moyenne=("valeur", "mean"), n_heures=("valeur", "size"))
           .reset_index())
    g["taux_saisie"] = g["n_heures"] / heures

    # Périmètre EFFECTIF, jamais le périmètre demandé (§ 2 quater).
    retenu = g["taux_saisie"] >= capture
    for p in sorted(g["polluant"].unique()):
        m = g["polluant"] == p
        print(f"    {NOM.get(p, p):6s} {retenu[m].sum():3d} station(s) retenue(s) sur "
              f"{m.sum():3d} — {(~retenu[m]).sum()} écartée(s) sous {capture:.0%} de saisie",
              flush=True)
    return g[retenu].reset_index(drop=True)


def rattacher_territoires(codes: pd.Series) -> pd.DataFrame:
    """station_id → région et département, par point-dans-polygone."""
    from pyproj import Transformer

    from pages_regions import (SOURCE_DEPARTEMENTS, charger_regions,  # noqa: PLC0415
                               charger_territoires, rattacher)

    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "nom", "commune", "lat_wgs84", "lon_wgs84"])
    st = st.dropna(subset=["lat_wgs84", "lon_wgs84"]).drop_duplicates("station_id")
    st = st[st["station_id"].isin(set(codes))].reset_index(drop=True)
    vers93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    st["x_l93"], st["y_l93"] = vers93.transform(st["lon_wgs84"].to_numpy(),
                                                st["lat_wgs84"].to_numpy())
    reg = rattacher(st, charger_regions())[["station_id", "nom", "commune", "region"]]
    dep = rattacher(st, charger_territoires(SOURCE_DEPARTEMENTS))[["station_id", "region"]]
    return reg.merge(dep.rename(columns={"region": "departement"}), on="station_id")


def main(annee: int, capture: float) -> int:
    print(f"\nSeuils 2030 — combien de stations basculent ?\n{'─' * 78}")
    t = charger_annee(annee)

    exclus = [p for p in sorted(t["polluant"].unique()) if p in SANS_VL_ANNUELLE]
    if exclus:
        print(f"  ⚠️ exclu(s) — aucune valeur limite ANNUELLE : {', '.join(exclus)} "
              f"(l'ozone relève d'une valeur cible sur le max 8 h)", flush=True)
    t = t[t["polluant"].isin(VL)]

    print("  couverture :")
    g = moyennes_annuelles(t, annee, capture)
    g = g.merge(rattacher_territoires(g["station_id"]), on="station_id", how="left")

    for etat, col in (("actuelle", "depasse_actuel"), ("en_2030", "depasse_2030")):
        g[col] = g.apply(lambda r: r["moyenne"] > VL[r["polluant"]][etat], axis=1)
    g["bascule"] = ~g["depasse_actuel"] & g["depasse_2030"]

    sortie = RACINE / "reports/seuils_2030.csv"
    attendues = ["station_id", "polluant", "moyenne", "taux_saisie", "region",
                 "departement", "depasse_actuel", "depasse_2030", "bascule"]
    if manque := [c for c in attendues if c not in g]:
        raise SystemExit(f"colonnes absentes du rapport : {manque}")
    g.to_csv(sortie, index=False)

    def bilan(d: pd.DataFrame, titre: str) -> None:
        print(f"\n{titre}\n{'─' * 78}")
        print(f"  {'polluant':8s} {'stations':>9s} {'VL act.':>8s} {'> act.':>7s} "
              f"{'VL 2030':>8s} {'> 2030':>7s} {'BASCULENT':>10s}")
        for p in ("NO2", "PM10", "PM25"):
            s = d[d["polluant"] == p]
            if s.empty:
                continue
            print(f"  {NOM[p]:8s} {len(s):9d} {VL[p]['actuelle']:8.0f} "
                  f"{s['depasse_actuel'].sum():7d} {VL[p]['en_2030']:8.0f} "
                  f"{s['depasse_2030'].sum():7d} {s['bascule'].sum():10d}")
        n_st = d.loc[d["depasse_2030"], "station_id"].nunique()
        tot = d["station_id"].nunique()
        print(f"  → {n_st} station(s) distincte(s) sur {tot} en dépassement d'au moins un "
              f"polluant en 2030 ({n_st / tot:.0%})")

    bilan(g, f"FRANCE MÉTROPOLITAINE — année {annee}")
    occ = g[g["region"] == "76"]
    bilan(occ, f"OCCITANIE — année {annee}")

    if not occ.empty:
        print(f"\n  Occitanie, par département — stations en dépassement 2030 :")
        d = (occ[occ["depasse_2030"]].groupby("departement")["station_id"].nunique()
             .sort_values(ascending=False))
        tous = occ.groupby("departement")["station_id"].nunique()
        for dep in tous.index:
            print(f"    {dep:4s} {d.get(dep, 0):2d} / {tous[dep]:2d}")

    print(f"\nÉcrit : {sortie.relative_to(RACINE)} ({len(g)} lignes)")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--annee", type=int, default=2025, help="dernière année PLEINE")
    a.add_argument("--capture", type=float, default=0.75, help="taux de saisie minimal")
    raise SystemExit(main(**vars(a.parse_args())))
