#!/usr/bin/env python3
"""Corriger l'ensemble CAMS, ou corriger CHIMERE seul ? — l'analogue de la chaîne AASQA.

Pourquoi cette comparaison est la plus pertinente du projet
------------------------------------------------------------
Tous nos résultats corrigent la **médiane de l'ensemble** CAMS Europe. Or Atmo Occitanie
ne fait pas tourner cet ensemble : elle exploite **CHIMERE**, qui est précisément l'un des
membres de cet ensemble.

Les deux ne sont pas le même produit :

| | CHIMERE dans CAMS | CHIMERE chez PREV'AIR / AASQA |
|---|---|---|
| emprise | Europe | France |
| maille | 0,1° ≈ 10 km | plus fine |
| inventaire | CAMS-REG européen | inventaire national |
| assimilation | non | oui |
| adaptation statistique | non | oui |

Le membre CHIMERE de CAMS n'est donc **pas** la chaîne d'Atmo Occitanie. Mais c'est le plus
proche analogue accessible sans leurs données, et il tranche une question qu'aucun de nos
résultats précédents n'aborde :

> Une correction statistique apprise sur les résidus d'un **modèle unique** vaut-elle plus,
> autant ou moins que la même correction apprise sur les résidus d'une **médiane
> d'ensemble** ?

Les deux hypothèses sont défendables, et c'est pourquoi la mesure vaut d'être faite :

* **En faveur de l'ensemble** — la médiane annule une partie des erreurs indépendantes des
  membres ; son résidu serait donc plus proche d'un biais structurel, plus apprenable.
* **En faveur du membre seul** — un modèle unique a des biais *cohérents* (sa chimie, ses
  émissions, sa couche limite), alors que la médiane mélange les défauts de sept modèles
  différents et peut produire un résidu moins structuré.

Ce que le script mesure
------------------------
Quatre systèmes, sur exactement les mêmes lignes et les mêmes plis double aveugle :

    ENSEMBLE_BRUT    la médiane CAMS, telle quelle
    CHIMERE_BRUT     le membre CHIMERE, tel quel
    ENSEMBLE_CORRIGE notre correction appliquée à la médiane
    CHIMERE_CORRIGE  notre correction appliquée à CHIMERE seul

⚠️ Réserve à porter partout : **le membre CHIMERE de CAMS n'est pas le CHIMERE d'une
AASQA.** Un résultat favorable ici ne démontre pas que la méthode améliorerait leur chaîne ;
il indique seulement qu'elle ne dépend pas de l'effet de moyennage d'ensemble.

⚠️ Les membres ne sont disponibles que pour **NO₂, O₃ et PM2,5** — pas pour les PM10, qui
sont pourtant le polluant des procédures préfectorales.

Usage : python3 scripts/corriger_chimere.py --polluant O3 [--horizon 2]
Sortie : reports/corriger_chimere_<polluant>.csv
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

from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster,
    charger, colonnes_admises,
)

MEMBRES = ("chimere", "emep", "mocage", "silam", "lotos", "match")


def charger_membres(polluant: str) -> pd.DataFrame:
    """Sorties horaires des membres, agrégées au jour.

    ⚠️ Tous les jetons de six chiffres du nom sont capturés — pas seulement le dernier.
    Une expression ancrée à droite perdrait le premier mois des fichiers bi-mensuels, ce
    qui a déjà coûté 35 % du jeu d'entraînement à ce projet.
    """
    motif = str(RACINE / f"data/processed/meteo/membres_metropole_{polluant.lower()}_*.parquet")
    fichiers = sorted(glob.glob(motif))
    if not fichiers:
        raise SystemExit(f"aucun membre pour {polluant} — l'ensemble n'est pas décomposé")
    morceaux = []
    for f in fichiers:
        t = pd.read_parquet(f)
        garde = ["station_id", "timestamp_utc"] + [m for m in MEMBRES if m in t.columns]
        morceaux.append(t[garde])
    d = pd.concat(morceaux, ignore_index=True)
    mois = sorted({m for f in fichiers for m in re.findall(r"(\d{6})", Path(f).name)})
    print(f"  membres : {len(fichiers)} fichiers · {mois[0]}→{mois[-1]} · "
          f"{len(d):,} lignes horaires", flush=True)
    presents = [m for m in MEMBRES if m in d.columns]
    if "chimere" not in presents:
        raise SystemExit("CHIMERE absent des membres — la comparaison n'a pas d'objet")
    # Contrôle : un membre entièrement constant serait le signe qu'on lit autre chose.
    for m in presents:
        if d[m].nunique(dropna=True) <= 1:
            raise SystemExit(f"membre {m} constant — lecture fautive")
    d["jour"] = pd.to_datetime(d["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    return d, presents


def gain(o, c, p) -> float:
    rc = float(np.sqrt(np.mean((c - o) ** 2)))
    return 100.0 * (1.0 - float(np.sqrt(np.mean((p - o) ** 2))) / rc) if rc > 0 else np.nan


def main(polluant: str, horizon: int, n_spa: int) -> int:
    depart = time.time()
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, cols, grandeur)
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    mem, presents = charger_membres(polluant)
    # Même grandeur journalière que la cible : un maximum 8 h se compare à un maximum 8 h.
    agr = "max" if grandeur in ("max_8h", "max_horaire") else "mean"
    jour_mem = mem.groupby(["station_id", "jour"])[presents].agg(agr).reset_index()
    avant = len(d)
    d = d.merge(jour_mem, on=["station_id", "jour"], how="inner")
    print(f"  intersection avec les membres : {avant:,} → {len(d):,} jours-station "
          f"({100 * len(d) / avant:.0f} %)", flush=True)

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    from apport_observation_veille import variables_passees  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    p, noms_mem = variables_passees(d.rename(columns={"valeur": "obs_jour"}))
    p["jour"] = pd.to_datetime(p["jour"]).dt.tz_localize(None)
    d = d.merge(p, on=["station_id", "jour"], how="left")

    d = d.dropna(subset=["chimere", "cams_jour", "valeur"]).reset_index(drop=True)
    predicteurs = base + cols_typo + noms_mem

    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), n_spa)
    mois = np.sort(d["mois"].unique())

    # ── Deux ancres : la médiane d'ensemble, et CHIMERE seul ─────────────────────
    #
    # L'ancre est la quantité dont on apprend le RÉSIDU et à laquelle on ajoute la
    # correction. Changer d'ancre change la cible d'apprentissage, pas seulement la
    # référence de comparaison — c'est bien deux modèles distincts qu'on ajuste.
    pred = {a: np.full(len(d), np.nan) for a in ("cams_jour", "chimere")}
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        m_test, m_train = (d["mois"] == m) & dans, (d["mois"] != m) & ~dans
        te, tr = d[m_test], d[m_train]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(m_test.to_numpy())
        for ancre in pred:
            pred[ancre][idx] = ajuster(DEFAUT, tr, te, predicteurs, ancre)

    ok = np.isfinite(pred["cams_jour"]) & np.isfinite(pred["chimere"])
    d = d[ok].reset_index(drop=True)
    o = d["valeur"].to_numpy()
    ens, chi = d["cams_jour"].to_numpy(), d["chimere"].to_numpy()
    p_ens, p_chi = pred["cams_jour"][ok], pred["chimere"][ok]

    def rmse(x):
        return float(np.sqrt(np.mean((x - o) ** 2)))

    print(f"\n{'═' * 74}\n{polluant} · {len(d):,} jours-station · échéance "
          f"{'J0' if horizon == 1 else f'J+{horizon - 1}'} · double aveugle\n{'═' * 74}")
    print(f"  {'système':26s} {'RMSE':>8s} {'vs son brut':>12s} {'vs ensemble brut':>17s}")
    lignes, r_ens = [], rmse(ens)
    for nom, brut, corrige in (("ensemble CAMS", ens, p_ens),
                               ("membre CHIMERE seul", chi, p_chi)):
        rb, rc = rmse(brut), rmse(corrige)
        print(f"  {nom + ' — brut':26s} {rb:8.3f} {'—':>12s} "
              f"{100 * (1 - rb / r_ens):16.2f}%")
        print(f"  {nom + ' — CORRIGÉ':26s} {rc:8.3f} {100 * (1 - rc / rb):11.2f}% "
              f"{100 * (1 - rc / r_ens):16.2f}%")
        lignes += [{"polluant": polluant, "systeme": nom, "etat": "brut", "rmse": rb,
                    "gain_vs_son_brut_pct": 0.0,
                    "gain_vs_ensemble_brut_pct": 100 * (1 - rb / r_ens), "n": len(d)},
                   {"polluant": polluant, "systeme": nom, "etat": "corrigé", "rmse": rc,
                    "gain_vs_son_brut_pct": 100 * (1 - rc / rb),
                    "gain_vs_ensemble_brut_pct": 100 * (1 - rc / r_ens), "n": len(d)}]

    # ── Les autres membres, bruts — pour situer CHIMERE parmi ses pairs ──────────
    print(f"\n  Les membres bruts, pour situer CHIMERE :")
    for m in presents:
        if d[m].notna().mean() > 0.5:
            print(f"    {m:10s} RMSE {rmse(d[m].to_numpy()):7.3f}")

    meilleur = "CHIMERE seul" if rmse(p_chi) < rmse(p_ens) else "l'ensemble"
    print(f"\n  → La correction est meilleure appliquée à **{meilleur}** "
          f"({abs(100 * (1 - rmse(p_chi) / rmse(p_ens))):.2f} % d'écart)")
    print(f"\n⚠️ Le membre CHIMERE de CAMS n'est PAS le CHIMERE d'une AASQA : emprise,")
    print(f"   maille, inventaire et assimilation diffèrent. Ce résultat indique seulement")
    print(f"   si la méthode dépend de l'effet de moyennage d'ensemble.")

    sortie = RACINE / f"reports/corriger_chimere_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=2, help="2 = J+1 réel (échéances 25-48 h)")
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
