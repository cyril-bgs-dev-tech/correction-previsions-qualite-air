#!/usr/bin/env python3
"""Publie la matrice de prédictions 2026 — les valeurs réellement prédites, station par station.

Pourquoi ce script existe
--------------------------
Un score agrégé dit *combien* le système gagne ; il ne dit pas *ce qu'il prédit*. Une AASQA
qui veut se faire son propre avis a besoin des valeurs, aux heures et aux points qui
l'intéressent — pas d'un pourcentage.

Cette matrice porte donc, pour chaque station et chaque heure de 2026 :

* ``observe``  — la mesure de référence (µg/m³) ;
* ``cams``     — la prévision européenne brute, telle que reçue ;
* ``corrige``  — **notre sortie**, celle qu'on propose d'utiliser.

Les trois côte à côte permettent de recalculer n'importe quel score sans nous croire sur
parole, et de regarder les cas où la correction échoue autant que ceux où elle réussit.

L'échéance, et pourquoi elle est écrite partout
-----------------------------------------------
Le nom de fichier source ``mos_<P>_J<h>.csv`` porte l'**horizon**, pas l'échéance : ``J1``
y désigne l'horizon 1, c'est-à-dire **J0**. Ce projet a appelé « J+1 » du J0 pendant des
semaines à cause de ce nom (`CLAUDE.md` § 4 ter). L'échéance publiée ici est donc **dérivée**
par ``aq.rapport.libelle_echeance``, jamais recopiée.

Ce que la matrice N'EST PAS
----------------------------
Ce ne sont pas des prévisions opérationnelles produites en temps réel : ce sont les sorties
du modèle sur la période évaluée, rejouées dans le protocole du dossier. Un point donné est
prédit par un modèle qui **n'a pas vu ses observations** — c'est la condition de déploiement,
et c'est ce qui rend ces valeurs comparables à une prévision réelle.

Usage : python3 scripts/matrice_predictions.py [--horizon 2] [--annee 2026]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from aq.rapport import libelle_echeance  # noqa: E402

POLLUANTS = ("NO2", "O3", "PM10", "PM25")
JOLI = {"NO2": "NO₂", "O3": "O₃", "PM10": "PM10", "PM25": "PM2,5"}


def stations() -> pd.DataFrame:
    """Métadonnées, pour qu'un identifiant devienne un lieu."""
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    garde = [c for c in ("station_id", "nom", "commune", "lat_wgs84", "lon_wgs84",
                         "altitude", "typologie_zone", "type_station") if c in st.columns]
    return st[garde].drop_duplicates("station_id")


def matrice(polluant: str, horizon: int, annee: int, st: pd.DataFrame) -> pd.DataFrame | None:
    src = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    if not src.exists():
        print(f"  ⏭️  {polluant} — {src.name} absent")
        return None
    d = pd.read_csv(src, parse_dates=["timestamp_utc"])
    d = d[d.timestamp_utc.dt.year == annee]
    if d.empty:
        print(f"  ⏭️  {polluant} — aucune ligne en {annee}")
        return None
    d = d.merge(st, on="station_id", how="left")
    d.insert(1, "polluant", JOLI[polluant])
    d.insert(2, "echeance", libelle_echeance(horizon))
    # `CLAUDE.md` § 2 bis : compter le reçu contre le demandé, et refuser une colonne plate.
    for c in ("observe", "cams", "corrige"):
        assert c in d.columns, f"{polluant} : colonne {c} absente"
        assert d[c].nunique() > 10, f"{polluant} : {c} quasi constante — lecture suspecte"
    return d.sort_values(["station_id", "timestamp_utc"])


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--horizon", type=int, default=2, help="2 = J+1")
    a.add_argument("--annee", type=int, default=2026)
    o = a.parse_args()
    ech = libelle_echeance(o.horizon)

    dest = RACINE / f"reports/matrice_predictions_{o.annee}"
    dest.mkdir(parents=True, exist_ok=True)
    st = stations()
    print(f"═══ Matrice de prédictions {o.annee} · échéance {ech} ═══")

    resume, total = [], 0
    for p in POLLUANTS:
        d = matrice(p, o.horizon, o.annee, st)
        if d is None:
            continue
        f = dest / f"{p}_{ech.replace('+', 'plus')}.parquet"
        d.to_parquet(f, index=False, compression="zstd")
        # Un extrait lisible sans outil : les 2 000 premières lignes, en CSV.
        d.head(2000).to_csv(dest / f"{p}_{ech.replace('+', 'plus')}_extrait.csv", index=False)
        biais = (d.corrige - d.observe).mean()
        rmse = ((d.corrige - d.observe) ** 2).mean() ** 0.5
        rmse_cams = ((d.cams - d.observe) ** 2).mean() ** 0.5
        resume.append(dict(polluant=JOLI[p], echeance=ech, lignes=len(d),
                           stations=d.station_id.nunique(),
                           debut=d.timestamp_utc.min().date(), fin=d.timestamp_utc.max().date(),
                           rmse_cams=round(rmse_cams, 3), rmse_corrige=round(rmse, 3),
                           gain_pct=round(100 * (rmse_cams - rmse) / rmse_cams, 2),
                           biais_corrige=round(biais, 3)))
        total += f.stat().st_size
        print(f"  ✅ {JOLI[p]:6s} {len(d):>9,} lignes · {d.station_id.nunique():3d} stations · "
              f"{f.stat().st_size/1e6:6.1f} Mo · RMSE {rmse_cams:.2f} → {rmse:.2f}")

    if not resume:
        print("❌ aucune matrice produite — lancer fit_mos.py --horizon", o.horizon)
        return 1
    t = pd.DataFrame(resume)
    t.to_csv(dest / "resume.csv", index=False)
    print(f"\n{t.to_string(index=False)}")
    print(f"\nÉcrit : {dest.relative_to(RACINE)} · {total/1e6:.1f} Mo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
