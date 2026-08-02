#!/usr/bin/env python3
"""MQI FAIRMODE par station (mission 3.4) — distribution, taux de conformité, typologie.

Usage : python3 scripts/mqi_par_station.py
Sortie : reports/mqi_par_station.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from mqi_bon_grain import GRAIN_FAIRMODE, NOM, agreger  # noqa: E402


def main() -> int:
    stations = pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "type_station"],
    )
    lignes = []
    resumes = []

    for polluant, (grandeur, libelle) in GRAIN_FAIRMODE.items():
        chemin = RACINE / f"reports/mos_{polluant}_J1.csv"
        if not chemin.exists():
            continue
        d = pd.read_csv(chemin, parse_dates=["timestamp_utc"]).dropna(
            subset=["observe", "cams", "corrige"])
        j = agreger(d, grandeur)
        j = j.merge(stations, on="station_id", how="left")
        j["type_station"] = j["type_station"].fillna("unknown")

        for sid, sous in j.groupby("station_id"):
            if len(sous) < 30:
                continue
            mqi_c = cmp.indice_qualite_modele(sous["observe"], sous["cams"], polluant)
            mqi_n = cmp.indice_qualite_modele(sous["observe"], sous["corrige"], polluant)
            typ = sous["type_station"].iloc[0]
            lignes.append({
                "polluant": polluant, "grain": grandeur, "station_id": sid,
                "type_station": typ, "n": len(sous),
                "mqi_cams": mqi_c, "mqi_nous": mqi_n,
                "conforme_cams": mqi_c <= 1.0, "conforme_nous": mqi_n <= 1.0,
            })

        t = pd.DataFrame([x for x in lignes if x["polluant"] == polluant])
        if t.empty:
            continue
        print(f"\n{NOM[polluant]} · {libelle} · {len(t)} stations")
        for col, lab in (("mqi_nous", "correction"), ("mqi_cams", "CAMS")):
            s = t[col]
            print(f"  {lab:12s} médiane={s.median():.3f}  p90={s.quantile(0.9):.3f}  "
                  f"pire={s.max():.3f}  conforme={100*(s<=1).mean():.1f}%")
        print("  par typologie (correction):")
        for typ, sous in t.groupby("type_station"):
            print(f"    {typ:20s} n={len(sous):3d}  méd={sous['mqi_nous'].median():.3f}  "
                  f"conforme={100*sous['conforme_nous'].mean():.0f}%  "
                  f"pire_décile={sous['mqi_nous'].quantile(0.9):.3f}")
        resumes.append({
            "polluant": polluant, "grain": grandeur, "n_stations": len(t),
            "taux_conforme_nous": float(t["conforme_nous"].mean()),
            "taux_conforme_cams": float(t["conforme_cams"].mean()),
            "mqi_nous_median": float(t["mqi_nous"].median()),
            "mqi_nous_p90": float(t["mqi_nous"].quantile(0.9)),
            "mqi_nous_max": float(t["mqi_nous"].max()),
            "mqi_cams_median": float(t["mqi_cams"].median()),
        })

    detail = pd.DataFrame(lignes)
    partiel = RACINE / "reports/mqi_par_station.csv.partiel"
    final = RACINE / "reports/mqi_par_station.csv"
    detail.to_csv(partiel, index=False)
    assert len(detail) > 0
    partiel.replace(final)

    pd.DataFrame(resumes).to_csv(RACINE / "reports/mqi_par_station_resume.csv", index=False)
    print(f"\nÉcrit reports/mqi_par_station.csv ({len(detail)} lignes)")
    # enterrement
    for r in resumes:
        ok = r["taux_conforme_nous"] >= 0.999
        print(f"  {r['polluant']}: taux conformité correction={100*r['taux_conforme_nous']:.1f}% "
              f"{'→ agrégat ne masquait rien' if ok else '→ des stations non conformes existent'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
