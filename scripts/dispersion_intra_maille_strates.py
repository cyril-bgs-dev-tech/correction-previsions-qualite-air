#!/usr/bin/env python3
"""Dispersion intra-maille : paires simultanées, strates typologie × distance, bootstrap maille.

Critique : les 3,61 µg/m³ ne sont pas un « plancher » tant qu'on n'a pas décomposé.
Protocole mission agent 3.2.

Usage : python3 scripts/dispersion_intra_maille_strates.py [--polluant O3]
Sortie : reports/dispersion_intra_maille_O3.csv · log_dispersion_intra_maille.txt
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from fit_mos import ESPECES  # noqa: E402

LOG = RACINE / "reports/log_dispersion_intra_maille.txt"
N_BOOT = 500
GRAINE = 20260730


def journal(msg: str) -> None:
    ligne = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}  {msg}"
    print(ligne, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def charger_mailles(polluant: str) -> pd.DataFrame:
    court = next(c for c, (p, _) in ESPECES.items() if p == polluant)
    fichiers = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_*.parquet")))
    if not fichiers:
        raise SystemExit(f"aucune prévision pour {polluant}")
    d = pd.read_parquet(fichiers[0], columns=["station_id", "maille_lat", "maille_lon"])
    return d.drop_duplicates("station_id")


def bande_distance(m: float) -> str:
    if m < 2000:
        return "0-2 km"
    if m < 5000:
        return "2-5 km"
    return "5 km+"


def main(polluant: str, horizon: int) -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.time()
    journal(f"démarrage dispersion strates {polluant} J+{horizon}")

    p = pd.read_csv(RACINE / f"reports/mos_{polluant}_J{horizon}.csv",
                    parse_dates=["timestamp_utc"]).dropna(subset=["observe"])
    stations = pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "type_station", "lat_wgs84", "lon_wgs84", "x_l93", "y_l93"],
    )
    m = charger_mailles(polluant)
    d = p.merge(m, on="station_id").merge(stations, on="station_id", how="left")
    d["maille"] = (d["maille_lat"].round(3).astype(str) + "_"
                   + d["maille_lon"].round(3).astype(str))
    d["type_station"] = d["type_station"].fillna("unknown")

    # Paires *simultanées* au grain journalier (moyenne des obs horaires du jour) :
    # même jour civil, même maille — évite le produit cartésien horaire (×24) sans
    # changer la question de représentativité spatiale.
    d["jour"] = d["timestamp_utc"].dt.floor("D")
    d = (d.groupby(["maille", "jour", "station_id", "type_station"], as_index=False)
          .agg(observe=("observe", "mean")))

    n_par = d.groupby("maille")["station_id"].nunique()
    mailles_multi = n_par[n_par >= 2].index
    d = d[d["maille"].isin(mailles_multi)]
    journal(f"mailles multi-stations: {len(mailles_multi)} · jours-station {len(d):,}")

    coords = stations.set_index("station_id")[["x_l93", "y_l93"]].dropna()

    paires = []
    t_p = time.time()
    for (maille, jour), g in d.groupby(["maille", "jour"], sort=False):
        ids = g["station_id"].to_numpy()
        if len(ids) < 2:
            continue
        obs = g.set_index("station_id")["observe"]
        types = g.set_index("station_id")["type_station"]
        for a, b in combinations(ids, 2):
            if a not in coords.index or b not in coords.index:
                continue
            dx = float(coords.loc[a, "x_l93"] - coords.loc[b, "x_l93"])
            dy = float(coords.loc[a, "y_l93"] - coords.loc[b, "y_l93"])
            dist = float(np.hypot(dx, dy))
            ta, tb = str(types.loc[a]), str(types.loc[b])
            paires.append({
                "maille": maille,
                "station_a": a, "station_b": b,
                "ecart_abs": abs(float(obs.loc[a]) - float(obs.loc[b])),
                "distance_m": dist,
                "bande_dist": bande_distance(dist),
                "typo_homogene": ta if ta == tb else "mixte",
            })
    journal(f"construction paires en {time.time()-t_p:.1f}s")
    if not paires:
        journal("aucune paire")
        return 1

    pa = pd.DataFrame(paires)
    journal(f"paires simultanées: {len(pa):,} · mailles {pa['maille'].nunique()}")

    # moyenne d'écart par maille (unité de bootstrap)
    def resume_strates(frame: pd.DataFrame) -> pd.DataFrame:
        lignes = []
        for (typo, bande), sous in frame.groupby(["typo_homogene", "bande_dist"]):
            par_m = sous.groupby("maille")["ecart_abs"].mean()
            if len(par_m) < 2:
                continue
            lignes.append({
                "typo_homogene": typo,
                "bande_dist": bande,
                "n_mailles": len(par_m),
                "n_paires": len(sous),
                "dispersion": float(par_m.mean()),
            })
        for typo, sous in frame.groupby("typo_homogene"):
            par_m = sous.groupby("maille")["ecart_abs"].mean()
            if len(par_m) < 2:
                continue
            lignes.append({
                "typo_homogene": typo,
                "bande_dist": "toutes",
                "n_mailles": len(par_m),
                "n_paires": len(sous),
                "dispersion": float(par_m.mean()),
            })
        par_m = frame.groupby("maille")["ecart_abs"].mean()
        lignes.append({
            "typo_homogene": "toutes",
            "bande_dist": "toutes",
            "n_mailles": len(par_m),
            "n_paires": len(frame),
            "dispersion": float(par_m.mean()),
        })
        return pd.DataFrame(lignes)

    base = resume_strates(pa)

    # bootstrap par maille
    rng = np.random.default_rng(GRAINE)
    mailles = pa["maille"].unique()
    boots = []
    for b in range(N_BOOT):
        choisies = rng.choice(mailles, size=len(mailles), replace=True)
        # map: take all pairs from chosen mailles (with replacement of mailles)
        blocs = []
        for i, maille in enumerate(choisies):
            sous = pa[pa["maille"] == maille].copy()
            sous["maille"] = f"{maille}__{i}"  # unique pour re-moyenne
            blocs.append(sous)
        boots.append(resume_strates(pd.concat(blocs, ignore_index=True)))
        if (b + 1) % 200 == 0:
            journal(f"bootstrap {b+1}/{N_BOOT}")

    boot = pd.concat(boots, ignore_index=True)
    ic = (boot.groupby(["typo_homogene", "bande_dist"])["dispersion"]
          .agg(ic_lo=lambda s: float(np.quantile(s, 0.025)),
               ic_hi=lambda s: float(np.quantile(s, 0.975)),
               boot_mean="mean")
          .reset_index())
    out = base.merge(ic, on=["typo_homogene", "bande_dist"], how="left")

    partiel = RACINE / f"reports/dispersion_intra_maille_{polluant}.csv.partiel"
    final = RACINE / f"reports/dispersion_intra_maille_{polluant}.csv"
    out.to_csv(partiel, index=False)
    assert out["dispersion"].notna().all()
    partiel.replace(final)

    journal(f"durée totale {time.time()-t0:.0f}s")
    print("\n" + out.sort_values(["typo_homogene", "bande_dist"]).to_string(index=False))

    # critère enterrement : variation < 30 % entre typologies homogènes (hors mixte)
    homo = out[(out["typo_homogene"] != "mixte") & (out["typo_homogene"] != "toutes")
               & (out["bande_dist"] == "toutes")]
    if homo.empty:
        # try any bande
        homo = out[(out["typo_homogene"] != "mixte") & (out["typo_homogene"] != "toutes")]
        homo = homo.groupby("typo_homogene", as_index=False)["dispersion"].mean()
    if len(homo) >= 2:
        dmin, dmax = homo["dispersion"].min(), homo["dispersion"].max()
        var_rel = 100 * (dmax - dmin) / dmin if dmin > 0 else np.nan
        journal(f"variation relative max/min typologies = {var_rel:.1f} % "
                f"(seuil enterrement 30 %)")
    global_ = out[(out["typo_homogene"] == "toutes") & (out["bande_dist"] == "toutes")]
    if len(global_):
        g = global_.iloc[0]
        journal(f"global dispersion={g['dispersion']:.3f} IC95=[{g['ic_lo']:.3f}; {g['ic_hi']:.3f}]")
    journal(f"écrit {final}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
