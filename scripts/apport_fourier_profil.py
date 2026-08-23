#!/usr/bin/env python3
"""Les descripteurs de forme à la main, contre les harmoniques de Fourier du jour.

Ce que ce test remet en cause
-------------------------------
`profil` — amplitude, dispersion, **heure du maximum**, pic sur moyenne — a été ajoutée à la
pile le 23/08 et y rend +0,31 à +0,62 pt à la place la plus dure, sans redondance avec
aucune autre famille. Le mécanisme est donc établi. Reste que ces quatre nombres sont un
**résumé grossier du spectre** du cycle diurne, et qu'ils portent deux défauts précis :

1. 🔴 **`prof_heure_max` a une couture à minuit.** 23 h et 0 h sont voisines dans la réalité
   et **maximalement distantes** pour un arbre, qui ne coupe que sur des seuils. Deux
   stations dont le pic diffère d'une heure se retrouvent aux deux bouts de la variable. Le
   dépôt sait pourtant faire : `variables_calendaires` encode l'heure en `cos`/`sin` depuis
   le premier jour — on l'a fait pour l'**index temporel**, jamais pour la **forme d'un
   profil**.
2. **C'est un estimateur d'un seul point.** L'heure du max dépend de la seule valeur la plus
   haute ; la phase de l'harmonique 1 utilise les 24, donc elle ne bouge pas si le bruit
   déplace le maximum d'une heure.

Ce qui est proposé à la place
-------------------------------
Les deux premières harmoniques du profil 24 h, **normalisées par la moyenne du jour** — donc
sans le niveau, que la pile porte déjà ailleurs :

    aₖ = 2·moyenne( x·cos(2πk·h/24) ) / moyenne(x)
    bₖ = 2·moyenne( x·sin(2πk·h/24) ) / moyenne(x)

`a₁, b₁` portent **amplitude et phase** du cycle diurne en continu, sans couture. `a₂, b₂`
portent la **semi-diurne** — la double bosse trafic matin/soir, qu'aucun « heure du max » ne
peut représenter puisqu'il n'en garde qu'une.

Les trois configurations, déclarées avant la mesure
-----------------------------------------------------
La question n'est pas « Fourier est-il meilleur » mais **« remplace-t-il, ou s'ajoute-t-il ? »** —
et les deux réponses ont des conséquences opposées sur ce qu'on met en production.

Usage  : python3 scripts/apport_fourier_profil.py --polluant NO2
Sortie : reports/apport_fourier_profil_<polluant>_h<n>_<axe>.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.rapport import ecrire_rapport, libelle_echeance  # noqa: E402
from cible_journaliere import profil_horaire  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)


def harmoniques(jeu: pd.DataFrame, colonne: str = "cams", prefixe: str = "fou",
                ordres: tuple[int, ...] = (1, 2)) -> tuple[pd.DataFrame, list[str]]:
    """Coefficients de Fourier du profil journalier, normalisés par la moyenne du jour.

    Normaliser retire le **niveau**, que la pile porte déjà par ailleurs : ce qui reste est
    la forme seule. Un jour plat rend des coefficients nuls quelle que soit sa hauteur.
    """
    d = jeu[["station_id", "timestamp_utc", colonne]].dropna(subset=[colonne]).copy()
    d["jour"] = d["timestamp_utc"].dt.floor("D")
    if getattr(d["jour"].dt, "tz", None) is not None:
        d["jour"] = d["jour"].dt.tz_localize(None)
    h = d["timestamp_utc"].dt.hour.to_numpy()
    x = d[colonne].to_numpy()
    agr = {"_moy": (colonne, "mean")}
    for k in ordres:
        angle = 2 * np.pi * k * h / 24.0
        d[f"_c{k}"] = x * np.cos(angle)
        d[f"_s{k}"] = x * np.sin(angle)
        agr[f"_c{k}"] = (f"_c{k}", "mean")
        agr[f"_s{k}"] = (f"_s{k}", "mean")
    p = d.groupby(["station_id", "jour"], sort=False).agg(**agr).reset_index()
    moy = p["_moy"].replace(0, np.nan)
    cols = []
    for k in ordres:
        p[f"{prefixe}_cos{k}"] = 2 * p[f"_c{k}"] / moy
        p[f"{prefixe}_sin{k}"] = 2 * p[f"_s{k}"] / moy
        cols += [f"{prefixe}_cos{k}", f"{prefixe}_sin{k}"]
    return p[["station_id", "jour"] + cols], cols


def rmse(o: np.ndarray, x: np.ndarray) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def main(polluant: str, horizon: int, n_spa: int, axe: str) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    prof, cols_prof = profil_horaire(jeu)
    fou, cols_fou = harmoniques(jeu)
    j = agreger_journalier(jeu, cols, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    from banc_preprocessing import f_tendance_cams  # noqa: PLC0415
    tend = f_tendance_cams(d)
    d = pd.concat([d, tend], axis=1)
    base += list(tend.columns)
    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    base += list(cols_typo)

    avant = len(d)
    prof["jour"] = pd.to_datetime(prof["jour"]).dt.tz_localize(None)
    d = d.merge(prof, on=["station_id", "jour"], how="left")
    d = d.merge(fou, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure : {avant:,} → {len(d):,} lignes — doublons de clé")

    # § 2 bis — les coefficients doivent être définis partout et varier, sinon ce n'est pas
    # une variable, c'est un artefact de calcul.
    for c in cols_fou:
        fini = float(np.isfinite(d[c]).mean())
        if fini < 0.999 or d[c].nunique() < 100:
            raise SystemExit(f"{c} : {100 * fini:.2f} % de valeurs finies, "
                             f"{d[c].nunique()} valeurs distinctes — inutilisable")
    print(f"  ✅ {len(cols_fou)} coefficients finis et variables", flush=True)
    # Ce que la couture de minuit coûte, montré plutôt qu'affirmé : la phase de
    # l'harmonique 1 est continue, l'heure du max ne l'est pas.
    phase = np.degrees(np.arctan2(d["fou_sin1"], d["fou_cos1"])) % 360
    print(f"  phase diurne : {phase.min():.0f}° → {phase.max():.0f}° (continue) · "
          f"heure du max : {d['prof_heure_max'].min():.0f} → "
          f"{d['prof_heure_max'].max():.0f} h (coupure entre 23 et 0)", flush=True)

    modes = {
        "① pile + profil à la main (4)": base + cols_prof,
        "② pile + Fourier à la place (4)": base + cols_fou,
        "③ pile + les deux (8)": base + cols_prof + cols_fou,
    }
    mois = np.sort(d["mois"].unique())
    ids = np.sort(d["station_id"].unique())
    print(f"\n{polluant} · {libelle_echeance(horizon)} · axe {axe} · {len(d):,} jours-station"
          f" · {len(ids)} stations · {len(mois)} mois", flush=True)

    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    plis = []
    for i, mm in enumerate(mois):
        m_te, m_tr = d["mois"] == mm, d["mois"] != mm
        if axe == "double":
            dans = d["station_id"].isin(groupes[i % n_spa])
            m_te, m_tr = m_te & dans, m_tr & ~dans
        plis.append((mm, m_te, m_tr))
    ecartes = [m for m, a, b in plis if a.sum() < 200 or b.sum() < 1000]
    print(f"  périmètre effectif : {len(plis) - len(ecartes)} plis sur {len(plis)} prévus",
          flush=True)

    pred = {k: np.full(len(d), np.nan) for k in modes}
    par_pli = []
    for i, (mm, m_te, m_tr) in enumerate(plis):
        if m_te.sum() < 200 or m_tr.sum() < 1000:
            continue
        te, tr = d[m_te], d[m_tr]
        idx = np.flatnonzero(m_te.to_numpy())
        o, c = te["valeur"].to_numpy(), te["cams_jour"].to_numpy()
        ligne = {"polluant": polluant, "horizon": horizon, "axe": axe, "mois": mm,
                 "n_test": len(te), "rmse_ancre": rmse(o, c)}
        for k, (nom, colonnes) in enumerate(modes.items()):
            p = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
            pred[nom][idx] = p
            ligne[f"rmse_config{k + 1}"] = rmse(o, p)
        par_pli.append(ligne)
        if (i + 1) % 8 == 0:
            print(f"  {i + 1}/{len(plis)} plis · {(time.time() - depart) / 60:.1f} min",
                  flush=True)

    ok = np.ones(len(d), bool)
    for v in pred.values():
        ok &= np.isfinite(v)
    o = d["valeur"].to_numpy()[ok]
    r_ancre = rmse(o, d["cams_jour"].to_numpy()[ok])
    tp = pd.DataFrame(par_pli)
    ref = tp["rmse_config1"].to_numpy()

    print(f"\n{'═' * 92}\nFOURIER CONTRE DESCRIPTEURS À LA MAIN · {polluant} · "
          f"{libelle_echeance(horizon)} · {int(ok.sum()):,} prédictions\n{'═' * 92}")
    print(f"  {'configuration':40s} {'RMSE':>8s} {'gain/CAMS':>10s} {'vs ①':>7s} "
          f"{'σ plis':>7s} {'plis>0':>8s}")
    lignes, ref_gain = [], None
    for k, nom in enumerate(modes):
        x = pred[nom][ok]
        gg = 100 * (1 - rmse(o, x) / r_ancre)
        dif = 100 * (1 - tp[f"rmse_config{k + 1}"].to_numpy() / ref)
        marge = np.nan if k == 0 else gg - ref_gain
        if ref_gain is None:
            ref_gain = gg
        print(f"  {nom:40s} {rmse(o, x):8.4f} {gg:+9.2f}% "
              f"{'—' if k == 0 else f'{marge:+7.2f}'} {np.std(dif):7.3f} "
              f"{int((dif > 0).sum()):4d}/{len(dif)}")
        lignes.append({"polluant": polluant, "horizon": horizon, "axe": axe,
                       "configuration": nom, "n_colonnes": len(modes[nom]),
                       "rmse_candidat": rmse(o, x), "rmse_ancre": r_ancre, "gain_pct": gg,
                       "apport_vs_main_pct": marge,
                       "ecart_apparie_moyen_pct": float(np.mean(dif)),
                       "ecart_apparie_sigma_pct": float(np.std(dif)),
                       "n_plis_positifs": int((dif > 0).sum()), "n_plis": len(dif),
                       "n_lignes": int(ok.sum()),
                       "fenetre": f"{mois[0]}→{mois[-1]}", "n_mois": len(mois)})

    contexte = {"polluant": polluant, "axe": axe, "echeance": libelle_echeance(horizon)}
    suff = f"{polluant}_h{horizon}_{axe}"
    ecrire_rapport(pd.DataFrame(lignes),
                   RACINE / f"reports/apport_fourier_profil_{suff}.csv", contexte,
                   attendues=["gain_pct", "apport_vs_main_pct", "ecart_apparie_moyen_pct"])
    ecrire_rapport(tp, RACINE / f"reports/apport_fourier_profil_{suff}_par_pli.csv",
                   contexte, attendues=["rmse_config1", "rmse_config2", "rmse_config3"])
    print(f"\nÉcrit : reports/apport_fourier_profil_{suff}.csv · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--axe", default="double", choices=("double", "temporel"))
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux, n.axe))
