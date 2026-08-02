#!/usr/bin/env python3
"""Rejoue le capteur d'anomalie sur variables *dynamiques* seules (mission 3.3).

Critique : 40/53 variables sont statiques → IForest voyait surtout « paysage rare ».
Ici : (A) cams_jour, cams_moy_jour, echeance absente au journalier, calendrier
       (B) variante ERA5 si disponible.

Sans réapprendre le modèle dédié CUDA (Q3 allégée : corriger vs s'abstenir seulement).

Usage : python3 scripts/capteur_dynamique_seul.py [--polluant O3] [--variante dynamique|era5]
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

RUPTURES = [pd.Timestamp("2024-11-13"), pd.Timestamp("2024-12-03")]
FENETRE = 7
LOG = RACINE / "reports/log_capteur_dynamique.txt"


def journal(msg: str) -> None:
    ligne = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}  {msg}"
    print(ligne, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def cols_dynamiques(predicteurs: list[str]) -> list[str]:
    """CAMS du jour + calendrier (heure agrégée absente ; jour_annee, etc.)."""
    mots = ("cams_jour", "cams_moy_jour", "jour_annee", "mois", "heure",
            "sin_", "cos_", "dow", "week", "calendrier", "dayof", "weekend")
    out = []
    for c in predicteurs:
        cl = c.lower()
        if c in ("cams_jour", "cams_moy_jour"):
            out.append(c)
        elif any(m in cl for m in mots):
            out.append(c)
    return out


def scores_iforest(x: pd.DataFrame, groupes: pd.Series) -> np.ndarray:
    from sklearn.ensemble import IsolationForest

    score = np.full(len(x), np.nan)
    for g in sorted(groupes.unique()):
        te = groupes == g
        tr = ~te
        if tr.sum() < 200:
            continue
        clf = IsolationForest(
            n_estimators=200, contamination="auto", random_state=0, n_jobs=-1,
        )
        clf.fit(x.loc[tr].to_numpy())
        # score_samples : plus bas = plus anormal → on inverse
        score[te.to_numpy()] = -clf.score_samples(x.loc[te].to_numpy())
    return score


def main(polluant: str, variante: str, n_plis: int) -> int:
    LOG.write_text("", encoding="utf-8")
    t0 = time.time()
    journal(f"capteur dynamique {polluant} variante={variante}")

    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    if variante == "dynamique":
        feats = cols_dynamiques(predicteurs)
    else:
        # ERA5 joint
        fichiers = sorted(glob.glob(str(
            RACINE / "data/processed/meteo/era5_metropole_*.parquet")))
        if not fichiers:
            journal("pas d'ERA5")
            return 1
        met = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
        met["jour"] = pd.to_datetime(met["timestamp_utc"], utc=True).dt.floor("D")
        num = [c for c in met.columns
               if c not in ("station_id", "timestamp_utc", "jour")
               and pd.api.types.is_numeric_dtype(met[c])]
        met_j = met.groupby(["station_id", "jour"], as_index=False)[num].mean()
        j["jour"] = pd.to_datetime(j["jour"], utc=True)
        met_j["jour"] = pd.to_datetime(met_j["jour"], utc=True)
        avant = len(j)
        j = j.merge(met_j, on=["station_id", "jour"], how="inner")
        journal(f"jointure ERA5 {avant:,} → {len(j):,}")
        feats = [c for c in num if c in j.columns]

    journal(f"features ({len(feats)}): {feats}")
    if len(feats) < 2:
        journal("trop peu de features dynamiques détectées — listing predicteurs:")
        journal(", ".join(predicteurs[:40]))
        return 1

    # corrige déjà calculé
    ref = pd.read_csv(RACINE / f"reports/mos_{polluant}_J1.csv",
                      parse_dates=["timestamp_utc"]).dropna(subset=["observe", "corrige"])
    ref["jour"] = ref["timestamp_utc"].dt.floor("D")
    ref = ref.sort_values(["station_id", "timestamp_utc"])
    ref["c8"] = ref.groupby("station_id")["corrige"].transform(
        lambda s: s.rolling(8, min_periods=6).mean())
    corrige = (ref.groupby(["station_id", "jour"])
               .agg(corrige=("c8", "max"), n=("timestamp_utc", "size")).reset_index())
    corrige = corrige[corrige["n"] >= 18].drop(columns="n")
    j["jour"] = pd.to_datetime(j["jour"], utc=True)
    corrige["jour"] = pd.to_datetime(corrige["jour"], utc=True)
    j = j.merge(corrige, on=["station_id", "jour"], how="inner").dropna(subset=["corrige"])

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    x = j[feats].replace([np.inf, -np.inf], np.nan).fillna(j[feats].median(numeric_only=True))
    j["score"] = scores_iforest(x, j["groupe"])
    journal(f"scores en {time.time()-t0:.0f}s · n={len(j):,}")

    # Q1 dérive
    j["jour_naive"] = j["jour"].dt.tz_localize(None) if j["jour"].dt.tz is not None else j["jour"]
    ordinaire = j["score"].dropna()
    scores_r = []
    for r in RUPTURES:
        lo, hi = r - pd.Timedelta(days=FENETRE), r + pd.Timedelta(days=FENETRE)
        sous = j[(j["jour_naive"] >= lo) & (j["jour_naive"] <= hi)]["score"].dropna()
        scores_r.append(sous)
    post = pd.concat(scores_r) if scores_r else pd.Series(dtype=float)
    if len(post) and len(ordinaire):
        pct = float((ordinaire < post.mean()).mean() * 100)
        journal(f"Q1 dérive: score_rupture={post.mean():.4f} ordinaire={ordinaire.mean():.4f} "
                f"→ percentile {pct:.0f}")
        v1 = "signal" if pct >= 80 else "aucun_signal"
    else:
        pct, v1 = float("nan"), "indetermine"
    journal(f"Q1 verdict={v1}")

    # Q2 gain par décile de score + contrôle CAMS
    j["gain_mse"] = (j["obs_jour"] - j["cams_jour"]) ** 2 - (j["obs_jour"] - j["corrige"]) ** 2
    j["decile_score"] = pd.qcut(j["score"], 10, labels=False, duplicates="drop")
    j["decile_cams"] = pd.qcut(j["cams_jour"], 10, labels=False, duplicates="drop")
    print("\nQ2 gain MSE par décile de score:")
    for dec, sous in j.groupby("decile_score"):
        print(f"  decile {int(dec)} n={len(sous):,} gain_mse={sous['gain_mse'].mean():.2f} "
              f"cams={sous['cams_jour'].mean():.1f}")

    ecarts = []
    for dec, sous in j.groupby("decile_cams"):
        thr = sous["score"].quantile(0.9)
        g_n = sous.loc[sous["score"] < thr, "gain_mse"].mean()
        g_a = sous.loc[sous["score"] >= thr, "gain_mse"].mean()
        ecarts.append(g_a - g_n)
    ecarts = np.array(ecarts, dtype=float)
    constance = max(float((ecarts < 0).mean()), float((ecarts > 0).mean()))
    journal(f"Q2 contrôle CAMS: constance={constance*100:.0f}% écart_médian={np.nanmedian(ecarts):+.2f}")
    v2 = "info_au_dela_cams" if constance >= 0.7 else "pas_plus_que_cams"

    # Q3 politiques sur décile haut
    thr = j["score"].quantile(0.9)
    an = j[j["score"] >= thr]
    m_cor = cmp.metriques(an["obs_jour"], an["corrige"])
    m_abs = cmp.metriques(an["obs_jour"], an["cams_jour"])
    delta = m_abs["rmse"] - m_cor["rmse"]
    journal(f"Q3 décile haut: RMSE corriger={m_cor['rmse']:.3f} abstention={m_abs['rmse']:.3f} "
            f"delta_corriger_mieux={delta:+.3f}")
    v3 = "aucune_ne_bat_corriger" if delta >= -0.3 else "abstention_ou_autre_utile"
    # si abstention meilleure de >0.3
    if m_abs["rmse"] + 0.3 < m_cor["rmse"]:
        v3 = "abstention_bat_corriger"

    out = pd.DataFrame([{
        "polluant": polluant, "variante": variante, "n_features": len(feats),
        "features": "|".join(feats),
        "q1_percentile": pct, "q1_verdict": v1,
        "q2_constance": constance, "q2_verdict": v2,
        "q3_rmse_corriger": m_cor["rmse"], "q3_rmse_abstention": m_abs["rmse"],
        "q3_verdict": v3,
        "duree_s": round(time.time() - t0, 1),
    }])
    path = RACINE / f"reports/capteur_dynamique_{polluant}_{variante}.csv"
    partiel = path.with_suffix(".csv.partiel")
    out.to_csv(partiel, index=False)
    partiel.replace(path)
    journal(f"écrit {path}")
    journal(f"VERDICT GLOBAL: Q1={v1} Q2={v2} Q3={v3}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--variante", choices=["dynamique", "era5"], default="dynamique")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.variante, args.plis))
