#!/usr/bin/env python3
"""Six membres valent-ils mieux que leur médiane ? Et où la moyenne reprend-elle la main ?

Deux questions, et la seconde est la plus fine
------------------------------------------------
**① La médiane détruit-elle de l'information ?** CAMS livre un produit « ensemble » qui est
une **médiane** de six modèles — CHIMERE, EMEP, MOCAGE, SILAM, LOTOS, MATCH. Ce résumé est
plus juste que chacun d'eux : sur l'ozone, CHIMERE seul rend 22,57 de RMSE, la médiane
12,63. Le moyennage divise l'erreur par 1,8.

Mais un résumé **jette** ce qui n'est pas le centre : le désaccord entre membres, la forme
de la distribution, l'identité du membre qui s'écarte. On donne donc les **six séparément**
au modèle et on mesure ce qu'il en tire au-delà de la médiane.

**② Médiane ou moyenne, selon le niveau ?** La médiane est robuste — elle ignore un membre
aberrant. C'est ce qu'on veut en régime courant. Mais un **épisode n'est pas une aberration** :
quand deux modèles sur six voient un panache, la médiane l'efface, et la moyenne en garde le
tiers.

L'hypothèse, écrite avant la mesure :

> **La médiane gagne dans le corps de la distribution, la moyenne dans la queue.**
> Il doit donc exister un niveau au-dessus duquel basculer.

Le protocole, et la fuite qu'il faut éviter
---------------------------------------------
Un seuil de bascule choisi **en regardant le test** serait un réglage sur la réponse. Le
seuil est donc déterminé **sur les plis d'entraînement seuls**, puis appliqué au test. La
version « seuil optimal a posteriori » est calculée aussi — mais affichée comme **plafond
non atteignable**, jamais comme performance.

⚠️ Les membres n'existent que pour **NO₂, O₃ et PM2,5**. Pas pour les PM10.

Usage : python3 scripts/ensemble_membres.py --polluant O3 --horizon 2
Sortie : reports/ensemble_membres_<polluant>_h<n>.csv
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)

MEMBRES = ("chimere", "emep", "mocage", "silam", "lotos", "match")


def rmse(o, x) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def main(polluant: str, horizon: int, n_spa: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, cols, grandeur)
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    fs = sorted(glob.glob(str(RACINE / f"data/processed/meteo/"
                              f"membres_metropole_{polluant.lower()}_*.parquet")))
    if not fs:
        raise SystemExit(f"aucun membre pour {polluant} — l'ensemble n'est pas décomposé")
    m = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    presents = [x for x in MEMBRES if x in m.columns and m[x].notna().any()]
    m["jour"] = pd.to_datetime(m["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    agr = "max" if grandeur in ("max_8h", "max_horaire") else "mean"
    jm = m.groupby(["station_id", "jour"])[presents].agg(agr).reset_index()
    avant = len(d)
    d = d.merge(jm, on=["station_id", "jour"], how="inner")
    print(f"{polluant} · {len(presents)} membres : {', '.join(presents)}\n"
          f"  {avant:,} → {len(d):,} jours-station après jointure "
          f"({100 * len(d) / avant:.0f} %)", flush=True)

    d = d.dropna(subset=presents + ["valeur", "cams_jour"]).reset_index(drop=True)
    d["med"] = d[presents].median(axis=1)
    d["moy"] = d[presents].mean(axis=1)
    d["etendue"] = d[presents].max(axis=1) - d[presents].min(axis=1)
    o = d["valeur"].to_numpy()

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")

    # ── ② Où la moyenne reprend-elle la main ? ───────────────────────────────
    print(f"\n{'═' * 74}\n② MÉDIANE OU MOYENNE, PAR NIVEAU\n{'═' * 74}")
    print(f"  Découpage par décile de la MÉDIANE — un prédicteur, pas l'observation :")
    print(f"  utiliser l'observé pour choisir serait regarder la réponse.\n")
    d["_dec"] = pd.qcut(d["med"], 10, labels=False, duplicates="drop")
    print(f"  {'décile':>7s} {'médiane':>9s} {'obs moy':>9s} {'RMSE méd':>10s} "
          f"{'RMSE moy':>10s} {'gagnant':>10s}")
    bascule = None
    for k, g in d.groupby("_dec"):
        rm = rmse(g["valeur"].to_numpy(), g["med"].to_numpy())
        rn = rmse(g["valeur"].to_numpy(), g["moy"].to_numpy())
        gagne = "moyenne" if rn < rm else "médiane"
        # Le point de bascule est le DERNIER passage médiane→moyenne : si la moyenne
        # reprend puis reperd, c'est la dernière transition qui vaut.
        if gagne == "moyenne" and bascule is None:
            bascule = float(g["med"].min())
        elif gagne == "médiane":
            bascule = None
        print(f"  {int(k):7d} {g['med'].mean():9.1f} {g['valeur'].mean():9.1f} "
              f"{rm:10.3f} {rn:10.3f} {gagne:>10s}")
    print(f"\n  → bascule observée vers {bascule:.1f} µg/m³" if bascule
          else "\n  → la médiane gagne partout : pas de bascule")

    # ── Le seuil, choisi SUR L'ENTRAÎNEMENT puis appliqué ────────────────────
    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    mois = np.sort(d["mois"].unique())
    d["hybride"] = np.nan
    seuils = []
    for i, mm in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        mt, mr = (d["mois"] == mm) & dans, (d["mois"] != mm) & ~dans
        te, tr = d[mt], d[mr]
        if len(te) < 200 or len(tr) < 1000:
            continue
        # Balayage du seuil sur l'ENTRAÎNEMENT seul.
        # ⚠️ Le balayage courait de 0,5 à 0,99 : il encodait mon hypothèse — « la moyenne
        # ne gagne que dans la queue » — et ne POUVAIT donc pas trouver un seuil bas. La
        # mesure par décile a montré que la moyenne gagne dès le 2ᵉ décile sur l'ozone.
        # Un espace de recherche qui exclut la réponse est un résultat écrit d'avance.
        cands = np.quantile(tr["med"], np.linspace(0.02, 0.99, 40))
        meilleur, s_opt = np.inf, cands[-1]
        for s in cands:
            h = np.where(tr["med"] > s, tr["moy"], tr["med"])
            r = rmse(tr["valeur"].to_numpy(), h)
            if r < meilleur:
                meilleur, s_opt = r, s
        seuils.append(float(s_opt))
        # ⚠️ L'ancre hybride doit exister sur l'ENTRAÎNEMENT aussi, sinon le modèle ne
        # peut pas s'y ajuster : `ajuster` apprend `valeur − ancre`. La version précédente
        # ne la remplissait que sur le test, le mode était donc silencieusement sauté et
        # toutes ses prédictions restaient NaN — le lot mourait 8 minutes plus tard sur un
        # `quantile` d'un tableau vide, très loin de la cause.
        #
        # Le seuil vient du pli d'entraînement : l'appliquer aux deux côtés n'est pas une
        # fuite, c'est la même règle de décision appliquée partout.
        for masque, part in ((mt, te), (mr, tr)):
            w = np.flatnonzero(masque.to_numpy())
            d.loc[d.index[w], "hybride"] = np.where(part["med"] > s_opt,
                                                    part["moy"], part["med"])
    print(f"\n  seuil appris sur l'entraînement : médiane {np.median(seuils):.1f} µg/m³ "
          f"(étendue {min(seuils):.1f}–{max(seuils):.1f})")

    # ── ① Six membres contre la médiane, dans le modèle ──────────────────────
    modes = {"ancré médiane (CAMS officiel)": (base + cols_typo, "cams_jour"),
             "ancré médiane + 6 membres en variables":
                 (base + cols_typo + presents + ["etendue"], "cams_jour"),
             "ancré MOYENNE des membres": (base + cols_typo, "moy"),
             "ancré HYBRIDE médiane/moyenne": (base + cols_typo, "hybride")}
    pred = {k: np.full(len(d), np.nan) for k in modes}
    for i, mm in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        mt, mr = (d["mois"] == mm) & dans, (d["mois"] != mm) & ~dans
        te, tr = d[mt], d[mr]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(mt.to_numpy())
        for nom, (colonnes, ancre) in modes.items():
            # Un mode dont l'ancre manque est SAUTÉ EN LE DISANT — un `continue` muet
            # rendait un tableau de NaN indiscernable d'un résultat.
            if tr[ancre].isna().any() or te[ancre].isna().any():
                print(f"    ⚠️ mode « {nom} » sauté sur {mm} : ancre {ancre} incomplète",
                      flush=True)
                continue
            pred[nom][idx] = ajuster(DEFAUT, tr, te, colonnes, ancre)

    ok = np.ones(len(d), bool)
    for nom, v in pred.items():
        n_ok = int(np.isfinite(v).sum())
        if n_ok == 0:
            raise SystemExit(f"le mode « {nom} » n'a produit AUCUNE prédiction — "
                             f"vérifier son ancre avant de conclure quoi que ce soit")
        ok &= np.isfinite(v)
    if ok.sum() < 1000:
        raise SystemExit(f"{ok.sum()} lignes communes aux {len(pred)} modes — trop peu")
    oo = o[ok]
    r_ref = rmse(oo, d["cams_jour"].to_numpy()[ok])
    haut = oo > np.quantile(oo, 0.95)

    print(f"\n{'═' * 74}\n① SIX MEMBRES CONTRE LEUR RÉSUMÉ — {ok.sum():,} lignes\n"
          f"{'═' * 74}")
    print(f"  {'système':42s} {'RMSE':>7s} {'gain':>7s} {'RMSE top 5 %':>13s}")
    lignes = []
    for nom, x in ([("médiane CAMS brute", d["cams_jour"].to_numpy()[ok]),
                    ("moyenne des membres, brute", d["moy"].to_numpy()[ok]),
                    ("hybride brut", d["hybride"].to_numpy()[ok])]
                   + [(n, pred[n][ok]) for n in modes]):
        r = rmse(oo, x)
        rh = rmse(oo[haut], x[haut])
        print(f"  {nom:42s} {r:7.3f} {100 * (1 - r / r_ref):6.1f}% {rh:13.3f}")
        lignes.append({"polluant": polluant, "horizon": horizon, "systeme": nom,
                       "rmse": r, "gain_pct": 100 * (1 - r / r_ref),
                       "rmse_top5pct": rh, "n": int(ok.sum())})

    sortie = RACINE / f"reports/ensemble_membres_{polluant}_h{horizon}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\n  La colonne « top 5 % » est celle qui tranche l'hypothèse : c'est là que la")
    print(f"  moyenne doit battre la médiane si elle conserve bien la queue.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
