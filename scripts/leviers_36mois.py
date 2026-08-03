#!/usr/bin/env python3
"""Remesure **tous les leviers** sur le corpus à 36 mois, en double aveugle.

Pourquoi ce script existe
--------------------------
L'audit du 02/08/2026 a trouvé le défaut le plus coûteux de la session : **le panel unifié
à 36 mois ne contient aucun des enrichissements mesurés au cours du projet**. Il porte
CAMS, paysage, relief et calendrier — rien d'autre.

    famille                dans le panel   dans le modèle
    typologie              oui             EXCLUE (liste noire)
    observation de veille  ABSENTE         —
    météo                  ABSENTE         —
    feux                   ABSENTE         —
    dispersion d'ensemble  ABSENTE         —

Autrement dit, `+36,7 %` sur NO₂ est le score d'un modèle **amputé de quatre leviers déjà
démontrés**. En doublant le corpus, le projet a perdu ses enrichissements — et a ensuite
passé une nuit à chercher des sources nouvelles.

Ce script rebranche chaque famille et mesure sa contribution **sur le corpus complet**,
dans les conditions de déploiement.

Ce que chaque famille vaut, et ce qu'elle coûte en déployabilité
-----------------------------------------------------------------
Toutes les familles ne sont pas également utilisables en production. Le tableau est écrit
**avant** de mesurer, pour que le résultat ne choisisse pas sa propre interprétation :

* `typologie` — statique, connue le jour de l'installation d'une station. **Déployable
  partout**, coût nul.
* `veille` — observations antérieures de la station, décalées de 2 jours (convention
  conservatrice de `apport_observation_veille.py` : la prévision de J est émise en J−1,
  donc rien de plus récent que la fin de J−2). **Déployable uniquement là où une station
  existe** — c'est le périmètre `AUX_STATIONS`, pas `PARTOUT`.
* `membres` — dispersion entre les sept modèles de l'ensemble CAMS. **Déployable**, c'est
  un produit de prévision.
* `feux` — flux d'émissions GFAS. **Déployable**, mais la couverture s'arrête en 2025-05 :
  les mois postérieurs seront manquants et le modèle doit le supporter.
* `era5` — réanalyse. **NON déployable** : elle n'existe pas au moment où la prévision est
  émise. Son gain est un **plafond**, pas une performance. Le projet a déjà mesuré que la
  prévision IFS en récupère 64 %.

⚠️ Ne jamais présenter le gain `era5` comme un résultat du système. C'est une borne.

Usage : python3 scripts/leviers_36mois.py --polluant NO2 [--chronologique]
Sortie : reports/leviers_36mois_<polluant>[_chrono].csv
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from apport_observation_veille import variables_passees  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster,
    charger, colonnes_admises,
)

MET = RACINE / "data/processed/meteo"


def _mois_dans(nom: str) -> list[str]:
    """Tous les jetons de six chiffres du nom — **jamais seulement le dernier**.

    `_(\\d{6})\\.parquet$` sur `..._202308_202309.parquet` capture `202309` et perd
    `202308`. Ce défaut a déjà coûté 35 % du jeu d'entraînement dans ce projet.
    """
    return re.findall(r"(\d{6})", nom)


def _charger_famille(motif: str, colonnes: list[str] | None,
                     debut: str, fin: str) -> pd.DataFrame | None:
    fichiers = [f for f in sorted(glob.glob(str(MET / motif)))
                if any(debut <= m <= fin for m in _mois_dans(Path(f).name))]
    if not fichiers:
        return None
    morceaux = []
    for f in fichiers:
        try:
            t = pd.read_parquet(f, columns=colonnes)
        except Exception as e:  # noqa: BLE001
            # ⚠️ On journalise **et on lève** si tout échoue : un `except: continue` muet
            # transforme un plantage en table vide, indiscernable d'une absence de donnée.
            print(f"    ⚠️ illisible {Path(f).name} : {type(e).__name__}", flush=True)
            continue
        morceaux.append(t)
    if not morceaux:
        raise SystemExit(f"aucun fichier lisible pour {motif} — ne pas continuer en silence")
    return pd.concat(morceaux, ignore_index=True)


def joindre_meteo(d: pd.DataFrame, debut: str, fin: str) -> tuple[pd.DataFrame, list[str]]:
    """ERA5 agrégée au jour. **Réanalyse — plafond, pas performance.**"""
    t = _charger_famille("era5_metropole*.parquet", None, debut, fin)
    if t is None:
        return d, []
    t["jour"] = pd.to_datetime(t["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    vars_ = ["precipitation_mm", "rayonnement_w_m2", "temperature_c", "point_rosee_c",
             "pression_hpa", "couche_limite_m", "vent_vitesse_m_s"]
    vars_ = [v for v in vars_ if v in t.columns]
    agr = t.groupby(["station_id", "jour"])[vars_].agg(["mean", "max", "min"])
    agr.columns = [f"era5_{a}_{b}" for a, b in agr.columns]
    agr = agr.reset_index()
    return _fusion(d, agr, "era5"), [c for c in agr.columns if c.startswith("era5_")]


def joindre_membres(d: pd.DataFrame, polluant: str, debut: str,
                    fin: str) -> tuple[pd.DataFrame, list[str]]:
    """Dispersion de l'ensemble CAMS. Nulle comme prédicteur seule, mais elle discrimine
    la fiabilité : le gain de la correction est ×6,6 plus grand dans le décile divergent."""
    t = _charger_famille(f"membres_metropole_{polluant.lower()}_*.parquet", None, debut, fin)
    if t is None:
        return d, []
    t["jour"] = pd.to_datetime(t["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    vars_ = [c for c in t.columns if c.startswith("membres_")]
    agr = t.groupby(["station_id", "jour"])[vars_].mean().reset_index()
    agr = agr.rename(columns={c: f"ens_{c[8:]}" for c in vars_})
    return _fusion(d, agr, "membres"), [c for c in agr.columns if c.startswith("ens_")]


def joindre_feux(d: pd.DataFrame, debut: str, fin: str) -> tuple[pd.DataFrame, list[str]]:
    t = _charger_famille("feux_metropole_*.parquet", None, debut, fin)
    if t is None:
        return d, []
    t["jour"] = pd.to_datetime(t["jour"]).dt.tz_localize(None)
    vars_ = [c for c in t.columns if c.startswith("feu_")]
    agr = t.groupby(["station_id", "jour"])[vars_].mean().reset_index()
    return _fusion(d, agr, "feux"), vars_


def joindre_veille(d: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Observations antérieures — périmètre `AUX_STATIONS` uniquement."""
    j = d.rename(columns={"valeur": "obs_jour"})
    passees, noms = variables_passees(j)
    passees["jour"] = pd.to_datetime(passees["jour"]).dt.tz_localize(None)
    return _fusion(d, passees, "veille"), noms


def _fusion(d: pd.DataFrame, agr: pd.DataFrame, nom: str) -> pd.DataFrame:
    """Jointure à gauche, avec **contrôle du nombre de lignes** — une jointure qui
    duplique est un bogue silencieux qui fausse tout ce qui suit."""
    avant = len(d)
    d = d.copy()
    d["_j"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    agr = agr.rename(columns={"jour": "_j"})
    agr["_j"] = pd.to_datetime(agr["_j"]).dt.tz_localize(None)
    out = d.merge(agr, on=["station_id", "_j"], how="left").drop(columns="_j")
    if len(out) != avant:
        raise SystemExit(f"jointure {nom} : {avant:,} → {len(out):,} lignes")
    return out


def gain(o, c, p) -> float:
    rc = float(np.sqrt(np.mean((c - o) ** 2)))
    rm = float(np.sqrt(np.mean((p - o) ** 2)))
    return 100.0 * (1.0 - rm / rc) if rc > 0 else np.nan


def epreuve(d, colonnes, plis) -> tuple[float, float, int]:
    obs, cams, pred, gains = [], [], [], []
    for _, m_test, m_train in plis:
        te, tr = d[m_test], d[m_train]
        if len(te) < 200 or len(tr) < 1000:
            continue
        p = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
        gains.append(gain(te["valeur"].to_numpy(), te["cams_jour"].to_numpy(), p))
        obs.append(te["valeur"].to_numpy()); cams.append(te["cams_jour"].to_numpy())
        pred.append(p)
    g = gain(np.concatenate(obs), np.concatenate(cams), np.concatenate(pred))
    return g, float(np.std(gains)), int(np.sum(np.array(gains) < 0))


def main(polluant: str, horizon: int, n_spa: int, chronologique: bool) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    base_cols = colonnes_admises(jeu)
    jeu[base_cols] = jeu[base_cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, base_cols, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in base_cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["mois"] = pd.to_datetime(d["jour"]).dt.strftime("%Y-%m")
    debut, fin = d["mois"].min().replace("-", ""), d["mois"].max().replace("-", "")
    print(f"{polluant} · {len(d):,} jours-station · {debut}→{fin} · "
          f"{len(base)} prédicteurs de base", flush=True)

    familles: dict[str, list[str]] = {}
    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    familles["typologie"] = cols_typo
    for nom, fn in (("veille", lambda x: joindre_veille(x)),
                    ("membres", lambda x: joindre_membres(x, polluant, debut, fin)),
                    ("feux", lambda x: joindre_feux(x, debut, fin)),
                    ("era5", lambda x: joindre_meteo(x, debut, fin))):
        d, cols = fn(d)
        familles[nom] = cols
        couv = 100 * (1 - d[cols].isna().all(axis=1).mean()) if cols else 0.0
        print(f"  {nom:10s} {len(cols):3d} colonnes · couverture {couv:5.1f} %", flush=True)

    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), n_spa)
    mois = np.sort(d["mois"].unique())
    plis = []
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        train = (d["mois"] < m) if chronologique else (d["mois"] != m)
        plis.append((f"{m}+s{i % n_spa + 1}", (d["mois"] == m) & dans, train & ~dans))

    variantes = [("base", [])] + [(f"+ {k}", [k]) for k in familles] + \
                [("+ déployables", ["typologie", "membres", "feux"]),
                 ("+ TOUT (era5 = plafond)", list(familles))]

    lignes, g_base = [], None
    print(f"\n{'variante':26s} {'colonnes':>9s} {'gain':>8s} {'écart':>7s} {'σ':>6s} "
          f"{'plis<0':>7s}")
    for nom, fams in variantes:
        cols = base + [c for f in fams for c in familles[f]]
        try:
            g, sd, neg = epreuve(d, cols, plis)
        except Exception as e:  # noqa: BLE001
            print(f"{nom:26s} ÉCHEC {type(e).__name__}: {e}", flush=True)
            continue
        g_base = g if nom == "base" else g_base
        ecart = "" if nom == "base" else f"{g - g_base:+6.2f}"
        print(f"{nom:26s} {len(cols):9d} {g:7.2f}% {ecart:>7s} {sd:6.1f} {neg:7d}",
              flush=True)
        lignes.append({"polluant": polluant, "variante": nom, "n_colonnes": len(cols),
                       "gain_pct": g, "ecart_vs_base": np.nan if nom == "base" else g - g_base,
                       "ecart_type": sd, "n_plis_negatifs": neg,
                       "chronologique": chronologique})

    # L'échéance dans le nom : un lot J+1 écrasait un lot J0 sans laisser de trace.
    suff = f"_h{horizon}" + ("_chrono" if chronologique else "")
    sortie = RACINE / f"reports/leviers_36mois_{polluant}{suff}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\n⚠️ `era5` est une RÉANALYSE : son gain est un plafond, pas une performance.")
    print(f"   `veille` n'est déployable qu'aux stations existantes (périmètre AUX_STATIONS).")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="NO2")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis-spatiaux", type=int, default=3)
    p.add_argument("--chronologique", action="store_true")
    a = p.parse_args()
    raise SystemExit(main(a.polluant, a.horizon, a.plis_spatiaux, a.chronologique))
