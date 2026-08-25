#!/usr/bin/env python3
"""La matrice de prédictions du SOCLE — les valeurs du modèle que le dossier revendique.

Pourquoi une seconde matrice
-----------------------------
`matrice_predictions.py` publie les sorties de la chaîne **horaire** (`fit_mos.py`) : fine en
temps, mais bâtie sur le post-traitement de base. Son `resume.csv` annonce **+19,2 %** sur le
NO₂ — ce qui est juste, et n'est pas le chiffre du dossier.

Le socle est un modèle **journalier** à huit familles, et c'est lui qui rend **≈ 41 %**. Ses
prédictions hors échantillon existent déjà, pli par pli — elles n'avaient simplement jamais été
publiées. **Ce script ne calcule rien** : il met en forme ce qui est mesuré.

> **Deux produits, pas deux versions.** Le premier répond à « que prédit-on, ici, à cette
> heure » ; le second à « de combien peut-on corriger, partout ». Les confondre est le risque
> n° 1 de ce dossier, et c'est pourquoi chaque fichier porte son protocole.

Ce que la matrice N'EST PAS
----------------------------
Ce ne sont pas des prévisions opérationnelles. Ce sont les sorties du modèle dans le protocole
du dossier : **chaque point est prédit par un modèle qui n'a vu ni sa station ni son mois.**
C'est plus dur qu'un déploiement réel, où le passé de la station serait connu.

Usage : python3 scripts/matrice_socle.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from aq.rapport import libelle_echeance  # noqa: E402

V = "_sans-feux-geoscf_fenetre-complete"
PRED = "pred__maximale___partout"
# ⚠️ Pas d'année dans le nom : la matrice couvre 2023-09 → 2026-07, et un « 2026 » y aurait
# menti dès la première lecture. Sur ce dépôt, un nom de fichier n'est jamais une source de
# vérité (§ 4 bis) — autant qu'il ne raconte rien plutôt qu'une fausseté.
SORTIE = RACINE / "reports/matrice_socle"
JOLI = {"NO2": "NO₂", "O3": "O₃", "PM10": "PM10", "PM25": "PM2,5"}
HORIZON = 2


def stations() -> pd.DataFrame:
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    # 🔴 Les noms de colonnes se LISENT dans le référentiel, ils ne se supposent pas.
    # Premier jet : « typologie », « latitude », « longitude », « departement » — aucun
    # n'existe. Le filtre `if c in st.columns` les écartait EN SILENCE, et le README que
    # j'avais écrit les annonçait quand même. Un filtre permissif transforme une faute de
    # nom en colonne absente, et rien ne lève (§ 2 bis).
    VOULUES = ("station_id", "nom", "commune", "typologie_zone", "type_station",
               "lat_wgs84", "lon_wgs84", "altitude", "metropole")
    if manque := [c for c in VOULUES if c not in st.columns]:
        raise SystemExit(f"⛔ colonne(s) absente(s) de stations.parquet : {manque}. "
                         f"Disponibles : {sorted(st.columns)}")
    return st[list(VOULUES)].drop_duplicates("station_id")


def matrice(pol: str, st: pd.DataFrame) -> pd.DataFrame | None:
    f = RACINE / f"reports/predictions_methode_maximale_{pol}_h2{V}.parquet"
    if not f.exists():
        print(f"  ⏭️  {pol} — {f.name} absent")
        return None
    t = pd.read_parquet(f)
    manque = [c for c in ("station_id", "jour", "obs", "cams_jour", PRED) if c not in t.columns]
    if manque:
        raise SystemExit(f"⛔ {pol} : colonne(s) absente(s) des prédictions : {manque}")
    d = pd.DataFrame({
        "station_id": t["station_id"],
        "polluant": JOLI[pol],
        "echeance": libelle_echeance(HORIZON),
        "jour": pd.to_datetime(t["jour"]).dt.date,
        "observe": t["obs"].astype(float),
        "cams": t["cams_jour"].astype(float),
        "corrige": t[PRED].astype(float),
    }).merge(st, on="station_id", how="left")
    # § 2 bis — compter le reçu contre le demandé, et refuser une colonne plate.
    for c in ("observe", "cams", "corrige"):
        if d[c].nunique() <= 10:
            raise SystemExit(f"⛔ {pol} : « {c} » quasi constante — lecture suspecte.")
    if d[["station_id", "jour"]].duplicated().any():
        raise SystemExit(f"⛔ {pol} : la clé (station, jour) n'est pas unique.")
    return d.sort_values(["station_id", "jour"]).reset_index(drop=True)


def main() -> int:
    SORTIE.mkdir(parents=True, exist_ok=True)
    st, resume = stations(), []
    for pol in ("NO2", "O3", "PM10", "PM25"):
        d = matrice(pol, st)
        if d is None:
            continue
        base = SORTIE / f"{pol}_socle_{libelle_echeance(HORIZON).replace('+', 'plus')}"
        # § 4 — écrire sous un nom provisoire, vérifier, puis renommer.
        prov = base.with_suffix(".parquet.partiel")
        d.to_parquet(prov, index=False, compression="zstd")
        relu = pd.read_parquet(prov)
        if len(relu) != len(d):
            raise SystemExit(f"⛔ {pol} : {len(relu):,} lignes relues pour {len(d):,} écrites.")
        prov.rename(base.with_suffix(".parquet"))
        d.head(2000).to_csv(base.with_name(base.name + "_extrait.csv"), index=False)
        e_c = float(np.sqrt(np.mean((d.observe - d.cams) ** 2)))
        e_k = float(np.sqrt(np.mean((d.observe - d.corrige) ** 2)))
        resume.append({"polluant": JOLI[pol], "echeance": libelle_echeance(HORIZON),
                       "lignes": len(d), "stations": d.station_id.nunique(),
                       "debut": str(d.jour.min()), "fin": str(d.jour.max()),
                       "mois": pd.to_datetime(d.jour).dt.to_period("M").nunique(),
                       "rmse_cams": round(e_c, 3), "rmse_corrige": round(e_k, 3),
                       "gain_pct": round(100 * (1 - e_k / e_c), 2),
                       "biais_corrige": round(float((d.corrige - d.observe).mean()), 3)})
        print(f"  {JOLI[pol]:5s} {len(d):>7,} lignes · {d.station_id.nunique():3d} stations · "
              f"{resume[-1]['mois']:2d} mois · gain {resume[-1]['gain_pct']:+.2f} %")
    if not resume:
        raise SystemExit("⛔ aucune matrice écrite — les prédictions du socle sont-elles là ?")
    r = pd.DataFrame(resume)
    for c in ("gain_pct", "rmse_cams", "rmse_corrige", "mois"):
        if c not in r:  # pragma: no cover — un garde, pas une branche
            raise SystemExit(f"colonne absente du résumé : {c}")
    r.to_csv(SORTIE / "resume.csv", index=False)
    print(f"\nÉcrit : {SORTIE.relative_to(RACINE)}/ — {len(r)} polluants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
