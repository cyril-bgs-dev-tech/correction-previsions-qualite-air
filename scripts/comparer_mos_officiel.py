#!/usr/bin/env python3
"""Notre correction contre celle que Copernicus publie déjà.

Le test le plus dur, et le plus pertinent
-----------------------------------------
Copernicus publie `cams-europe-air-quality-forecasts-optimised-at-observation-sites` : des
prévisions **corrigées par apprentissage** aux stations européennes, depuis janvier 2024,
gratuitement. Sa méthode emploie « les observations de fond, les prévisions météo ECMWF et la
médiane de l'ensemble CAMS ».

C'est notre approche, faite officiellement. Se comparer à **CAMS brut** flattait donc le
projet : l'utilisateur professionnel dispose déjà d'un produit corrigé.

Deux questions, et la seconde est la vraie :

1. **Sur les stations qu'il couvre**, sommes-nous meilleurs ? Probablement non — il utilise
   les observations récentes, nous pas.
2. **Quelles stations ne couvre-t-il pas ?** C'est là que se trouve la seule valeur possible
   du projet : là où aucun produit corrigé n'existe.

La seconde question a une réponse chiffrable, et elle définit le périmètre défendable du
dossier bien mieux qu'un gain de RMSE.

**Alignement des grandeurs.** Le fichier officiel donne des concentrations **horaires** à
échéance 24-47 h. On agrège donc en maximum journalier 8 h — la grandeur réglementaire de
l'ozone — exactement comme pour notre modèle, et on restreint aux **mêmes** jours-station.

Usage : python3 scripts/comparer_mos_officiel.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from cible_journaliere import max_glissant_8h  # noqa: E402
from scores_episodes import scores  # noqa: E402

SEUILS = {"O3": 120.0}
GRANDEURS = {"O3": "max_8h", "NO2": "max_horaire", "PM25": "moyenne_jour"}


def lire_officiel(chemin: Path) -> pd.DataFrame:
    """Assemble les fichiers `mos_` et `raw_` de l'archive officielle."""
    blocs = {"mos": [], "raw": []}
    with zipfile.ZipFile(chemin) as z:
        for nom in z.namelist():
            if nom.startswith(("mos_", "raw_")):
                cle = nom[:3]
                d = pd.read_csv(io.BytesIO(z.read(nom)), sep=";")
                blocs[cle].append(d)

    mos = pd.concat(blocs["mos"], ignore_index=True)
    raw = pd.concat(blocs["raw"], ignore_index=True)
    col_mos = [c for c in mos.columns if c.startswith("conc_")][0]
    col_raw = [c for c in raw.columns if c.startswith("conc_")][0]

    fusion = mos[["station_id", "datetime", col_mos]].merge(
        raw[["station_id", "datetime", col_raw]], on=["station_id", "datetime"], how="outer")
    fusion["datetime"] = pd.to_datetime(fusion["datetime"], utc=True)
    return fusion.rename(columns={col_mos: "officiel_mos", col_raw: "officiel_raw"})


def journalier(d: pd.DataFrame, colonnes: list[str],
               grandeur: str = "max_8h") -> pd.DataFrame:
    """Agrège au jour selon la **grandeur réglementaire du polluant**.

    Le choix n'est pas cosmétique : c'est l'objet même de la comparaison. Un maximum est une
    **statistique d'ordre**, sensible à toute réduction de variabilité ; une moyenne
    journalière est une tendance centrale, qui ne l'est pas. Appliquer le max 8 h aux
    particules mesurerait une grandeur que personne n'utilise et fausserait le test.
    """
    d = d.sort_values(["station_id", "datetime"]).copy()
    d["jour"] = d["datetime"].dt.floor("D")

    if grandeur == "max_8h":
        for c in colonnes:
            d[c] = d.groupby("station_id")[c].transform(max_glissant_8h)
    agregation = "mean" if grandeur == "moyenne_jour" else "max"

    agr = d.groupby(["station_id", "jour"]).agg(
        **{c: (c, agregation) for c in colonnes},
        n=("datetime", "size"),
    ).reset_index()
    return agr[agr["n"] >= 18].drop(columns="n")


def main(polluant: str, horizon: int, archive: str) -> int:
    chemin = RACINE / "data/raw/cams_mos_officiel" / archive
    if not chemin.exists():
        print(f"ÉCHEC : {chemin.name} absent", file=sys.stderr)
        return 1

    officiel = lire_officiel(chemin)
    print(f"Officiel : {len(officiel):,} lignes · "
          f"{officiel['station_id'].nunique()} stations · "
          f"{officiel['datetime'].min():%Y-%m-%d} → {officiel['datetime'].max():%Y-%m-%d}")
    couvertes = officiel.dropna(subset=["officiel_mos"])["station_id"].nunique()
    print(f"  dont {couvertes} avec une valeur MOS "
          f"({100 * couvertes / officiel['station_id'].nunique():.0f} %)\n", flush=True)

    # ── Nos prédictions, sur la même grandeur ─────────────────────────────────
    notre = pd.read_csv(RACINE / f"reports/mos_{polluant}_J{horizon}.csv",
                        parse_dates=["timestamp_utc"]).dropna(subset=["observe"])
    notre = notre.rename(columns={"timestamp_utc": "datetime"})
    # **La grandeur dépend du polluant** — max 8 h pour l'ozone, max horaire pour le NO₂,
    # moyenne journalière pour les particules. Laisser le défaut agrégeait les trois en max 8 h,
    # c'est-à-dire mesurait pour NO₂ et PM2,5 une grandeur que personne n'utilise. Le jumeau
    # corrigé est `comparer_mos_officiel_annee.py`, qui porte le dictionnaire depuis le début :
    # la correction n'avait pas été propagée ici.
    grandeur = GRANDEURS[polluant]
    notre_j = journalier(notre, ["observe", "cams", "corrige"], grandeur)
    off_j = journalier(officiel, ["officiel_mos", "officiel_raw"], grandeur)

    commun = notre_j.merge(off_j, on=["station_id", "jour"], how="inner")
    print(f"Jours-station communs : {len(commun):,} · "
          f"{commun['station_id'].nunique()} stations", flush=True)

    # ── La question du périmètre : qui n'est PAS couvert ? ────────────────────
    nos_stations = set(notre_j["station_id"])
    couvertes_mos = set(off_j.dropna(subset=["officiel_mos"])["station_id"])
    sans_mos = nos_stations - couvertes_mos
    print(f"\nPÉRIMÈTRE — sur nos {len(nos_stations)} stations :")
    print(f"  couvertes par le MOS officiel : {len(nos_stations & couvertes_mos)}")
    print(f"  **NON couvertes**             : {len(sans_mos)} "
          f"({100 * len(sans_mos) / len(nos_stations):.0f} %)", flush=True)

    # ── Comparaison, sur les stations couvertes uniquement ────────────────────
    avec = commun.dropna(subset=["officiel_mos", "corrige", "observe"])
    if avec.empty:
        print("\nAucun jour-station comparable.")
        return 0

    seuil = SEUILS.get(polluant, 120.0)
    depasse = (avec["observe"] >= seuil).to_numpy()
    print(f"\nSur les {len(avec):,} jours-station où le MOS officiel existe :")
    print(f"{'produit':28s} {'RMSE':>7s} {'biais':>7s} {'R²':>8s} {'POD':>6s} {'CSI':>6s}")
    lignes = []
    for nom, col in (("CAMS brut (le nôtre)", "cams"),
                     ("CAMS brut (officiel)", "officiel_raw"),
                     ("MOS OFFICIEL Copernicus", "officiel_mos"),
                     ("NOTRE correction", "corrige")):
        if col not in avec or avec[col].isna().all():
            continue
        m = cmp.metriques(avec["observe"], avec[col])
        s = (scores(depasse, (avec[col] >= seuil).to_numpy())
             if depasse.sum() >= 20 else {})
        print(f"{nom:28s} {m['rmse']:7.2f} {m['biais']:+7.2f} {m['r2']:+8.3f} "
              f"{s.get('POD', np.nan):6.3f} {s.get('CSI', np.nan):6.3f}", flush=True)
        lignes.append({"produit": nom, **m, **{f"s_{k}": v for k, v in s.items()}})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/comparaison_mos_officiel_{polluant}.csv", index=False)

    r_off = float(table.loc[table["produit"].str.startswith("MOS OFF"), "rmse"].iloc[0])
    r_notre = float(table.loc[table["produit"].str.startswith("NOTRE"), "rmse"].iloc[0])
    print("\n" + "=" * 72)
    if r_notre < r_off:
        print(f"Nous devançons le MOS officiel de {r_off - r_notre:.2f} µg/m³ sur ses "
              f"propres stations.")
    else:
        print(f"Le MOS officiel nous devance de {r_notre - r_off:.2f} µg/m³ — attendu, il "
              f"utilise\nles observations récentes que nous n'utilisons pas.")
    print(f"\nMais il ne couvre pas {len(sans_mos)} de nos stations, et **aucun lieu sans "
          f"station**.\nC'est là, et seulement là, que le projet a une valeur propre.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--archive", default="o3_202412.zip")
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.archive))
