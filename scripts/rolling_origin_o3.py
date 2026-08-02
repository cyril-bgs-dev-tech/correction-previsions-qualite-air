#!/usr/bin/env python3
"""Validation prospective stricte (rolling-origin) — O₃, grain max 8 h.

Critique adressée
-----------------
Le « mois caché » / « double aveugle » du projet n'impose pas
`max(date_train) < min(date_test)`. Des dates d'entraînement postérieures au mois
testé peuvent entrer. Ce script force l'ordre temporel et le **vérifie** à chaque pli.

Protocole
---------
Pour chaque mois M de la fenêtre (sauf le premier, sans passé) :
  - train = tous les jours-station avec jour < premier jour de M
  - test  = jours du mois M
  - assert max(train.jour) < min(test.jour)
  - LightGBM réglage retenu (REGLE), résidu vs cams_jour, stations toutes vues
    (la question est la prospectivité temporelle, pas le leave-station)

Passe unitaire : --un-mois YYYY-MM chronométré avant le lot.

Usage :
  python3 scripts/rolling_origin_o3.py --un-mois 2024-06
  python3 scripts/rolling_origin_o3.py
Sorties : reports/rolling_origin_O3.csv · reports/log_rolling_origin_O3.txt
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

GRAINE = 20260730
LOG = RACINE / "reports/log_rolling_origin_O3.txt"


def journal(msg: str) -> None:
    ligne = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}  {msg}"
    print(ligne, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def gain_rmse(observe, cams, predit) -> tuple[float, float, float]:
    rc = float(np.sqrt(np.mean((np.asarray(cams) - np.asarray(observe)) ** 2)))
    rm = float(np.sqrt(np.mean((np.asarray(predit) - np.asarray(observe)) ** 2)))
    g = 100.0 * (1.0 - rm / rc) if rc > 0 else float("nan")
    return rc, rm, g


def ajuster(tr: pd.DataFrame, te: pd.DataFrame, colonnes: list[str]) -> np.ndarray:
    from lightgbm import LGBMRegressor

    modele = LGBMRegressor(
        subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
        random_state=GRAINE, n_jobs=-1, verbose=-1, **REGLE,
    )
    modele.fit(tr[colonnes], tr["valeur"] - tr["cams_jour"])
    return np.clip(te["cams_jour"].to_numpy() + modele.predict(te[colonnes]), 0, None)


def preparer(horizon: int = 1) -> tuple[pd.DataFrame, list[str]]:
    jeu = charger("O3", horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    grandeur = GRANDEUR_PAR_POLLUANT["O3"]
    j = agreger_journalier(jeu, colonnes, grandeur)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")
    return d, predicteurs


def un_pli(d: pd.DataFrame, predicteurs: list[str], mois: str) -> dict:
    debut = pd.Timestamp(f"{mois}-01", tz="UTC")
    if debut.tzinfo is None:
        debut = debut.tz_localize("UTC")
    # jour may be timezone-naive after floor
    jours = d["jour"]
    if getattr(jours.dt, "tz", None) is not None:
        masque_train = jours < debut
        # fin de mois exclusive : mois calendaire
        fin = (debut + pd.offsets.MonthBegin(1))
        masque_test = (jours >= debut) & (jours < fin)
    else:
        debut_naive = pd.Timestamp(f"{mois}-01")
        fin_naive = debut_naive + pd.offsets.MonthBegin(1)
        masque_train = jours < debut_naive
        masque_test = (jours >= debut_naive) & (jours < fin_naive)

    tr, te = d.loc[masque_train], d.loc[masque_test]
    if len(tr) < 500 or len(te) < 50:
        return {
            "mois": mois, "n_train": len(tr), "n_test": len(te),
            "ok_ordre": False, "statut": "effectif_insuffisant",
            "rmse_cams": np.nan, "rmse_mos": np.nan, "gain_pct": np.nan,
            "max_train": None, "min_test": None, "duree_s": 0.0,
        }

    max_tr = pd.Timestamp(tr["jour"].max())
    min_te = pd.Timestamp(te["jour"].min())
    ok = max_tr < min_te
    if not ok:
        raise RuntimeError(
            f"VIOLATION prospectivité {mois}: max_train={max_tr} >= min_test={min_te}"
        )

    t0 = time.time()
    pred = ajuster(tr, te, predicteurs)
    duree = time.time() - t0
    rc, rm, g = gain_rmse(te["valeur"], te["cams_jour"], pred)
    return {
        "mois": mois, "n_train": len(tr), "n_test": len(te),
        "ok_ordre": True, "statut": "ok",
        "rmse_cams": rc, "rmse_mos": rm, "gain_pct": g,
        "max_train": str(max_tr.date()), "min_test": str(min_te.date()),
        "duree_s": round(duree, 2),
    }


def main(un_mois: str | None, horizon: int) -> int:
    # N'écrase le log qu'en lot complet (reprise unitaire = append).
    if un_mois is None:
        LOG.write_text("", encoding="utf-8")
    journal(f"démarrage rolling-origin O3 max_8h horizon={horizon} un_mois={un_mois}")

    t_prep = time.time()
    d, predicteurs = preparer(horizon)
    journal(
        f"préparé: {len(d):,} jours-station · {d['station_id'].nunique()} stations · "
        f"{d['mois'].nunique()} mois · {time.time() - t_prep:.1f}s · "
        f"{len(predicteurs)} prédicteurs"
    )

    mois_dispo = sorted(d["mois"].unique())
    if un_mois:
        if un_mois not in mois_dispo:
            journal(f"ÉCHEC: mois {un_mois} absent (dispo {mois_dispo[0]}…{mois_dispo[-1]})")
            return 1
        cibles = [un_mois]
    else:
        # premier mois = pas de passé → exclu
        cibles = mois_dispo[1:]

    journal(f"plis prévus: {len(cibles)} · premier={cibles[0]} · dernier={cibles[-1]}")

    # extrapolation si lot
    if not un_mois:
        journal("passe unitaire obligatoire d'abord sur le 2e mois de la fenêtre…")
        u = un_pli(d, predicteurs, cibles[0])
        journal(
            f"UNITAIRE {cibles[0]}: gain={u['gain_pct']:+.2f}% · "
            f"n_train={u['n_train']:,} · n_test={u['n_test']:,} · "
            f"durée={u['duree_s']}s · ordre_ok={u['ok_ordre']}"
        )
        total_est = u["duree_s"] * len(cibles)
        journal(
            f"extrapolation: t_unitaire×N = {u['duree_s']:.1f}×{len(cibles)} "
            f"= {total_est/60:.1f} min"
        )
        if total_est > 6 * 3600:
            journal("STOP: extrapolation > 6 h — réduire la fenêtre ou la capacité")
            return 2

    lignes = []
    for i, m in enumerate(cibles, 1):
        r = un_pli(d, predicteurs, m)
        lignes.append(r)
        journal(
            f"[{i}/{len(cibles)}] {m}  gain={r['gain_pct']:+.2f}%  "
            f"cams={r['rmse_cams']:.2f} mos={r['rmse_mos']:.2f}  "
            f"n_tr={r['n_train']:,} n_te={r['n_test']:,}  "
            f"{r['duree_s']}s  ordre={r['ok_ordre']}  {r['statut']}"
        )

    partiel = RACINE / "reports/rolling_origin_O3.csv.partiel"
    final = RACINE / "reports/rolling_origin_O3.csv"
    table = pd.DataFrame(lignes)
    table.to_csv(partiel, index=False)

    ok = table[table["statut"] == "ok"]
    if len(ok) == 0:
        journal("aucun pli ok")
        return 1
    # vérifier contenu attendu
    assert ok["ok_ordre"].all()
    assert ok["gain_pct"].notna().all()

    partiel.replace(final)
    moy = float(ok["gain_pct"].mean())
    med = float(ok["gain_pct"].median())
    pire = float(ok["gain_pct"].min())
    n_neg = int((ok["gain_pct"] < 0).sum())
    journal(
        f"RÉSUMÉ n={len(ok)}  gain_moyen={moy:+.2f}%  médiane={med:+.2f}%  "
        f"pire={pire:+.2f}%  plis_négatifs={n_neg}  "
        f"réf_blocage_conjoint=+1.5%"
    )
    journal(f"écrit {final}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--un-mois", default=None, help="YYYY-MM pour passe unitaire seule")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()
    raise SystemExit(main(args.un_mois, args.horizon))
