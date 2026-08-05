#!/usr/bin/env python3
"""Un tableau par polluant — cinq systèmes, mêmes lignes, et la loi des erreurs.

Ce que ce tableau veut permettre
----------------------------------
Qu'un lecteur technique comprenne en trente secondes **où se situe chaque approche**, sans
avoir à recouper cinq rapports. Cinq systèmes, dans l'ordre de la chaîne opérationnelle :

| # | système | ce qu'il représente |
|---|---|---|
| 1 | **CAMS brut** | l'ensemble européen, 0,1° — notre point de départ |
| 2 | **CHIMERE seul** | le membre que fait tourner PREV'AIR, ici en version européenne |
| 3 | **CHIMERE + krigeage** | la **stratégie AASQA** : biais récent interpolé, réglages usuels |
| 4 | **CHIMERE + krigeage optimisé** | la même, poussée avec ce que ce projet a appris |
| 5 | **notre modèle** | résidu appris, toutes familles déployables |

⚠️ Trois réserves, sans lesquelles le tableau ment
----------------------------------------------------
1. **Le CHIMERE d'ici n'est pas celui de PREV'AIR.** C'est le membre de l'ensemble CAMS —
   emprise européenne, maille 0,1°, inventaire CAMS-REG, **sans assimilation**. Leur version
   est nationale, plus fine, assimilée. La ligne 2 ne mesure donc pas leur modèle.
2. **La ligne 3 n'est pas PREV'AIR.** C'est leur *famille* de méthode — biais récent
   interpolé spatialement — dont la formule exacte n'est pas publiée et a depuis évolué vers
   de l'apprentissage. Aucune ligne de ce tableau ne mesure leur produit.
3. **Les membres PM10 n'existent que depuis 2025-01** — téléchargés le 04/08/2026. La
   réserve précédente (« les lignes 2 à 4 sont absentes sur PM10 ») est **levée** : le
   polluant qui déclenche le plus de procédures a enfin sa comparaison au concurrent.
   Le prix est une **fenêtre plus courte** — 19 mois contre 36 pour les trois autres —
   parce que les six systèmes partagent les mêmes lignes, et que cet invariant prime sur
   la taille du corpus. Comparer nos 36 mois à leurs 19 serait la comparaison inéquitable
   que ce fichier existe pour éviter.
   ⚠️ **La fenêtre est donc écrite dans le CSV** (`fenetre`, `n_mois`) : `n` seul ne dit
   pas si 56 238 lignes couvrent 19 mois ou 31.

Le réglage de la ligne 4, et d'où il vient
--------------------------------------------
Trois enseignements de ce projet, tous mesurés, tous appliqués à leur famille :

* **fenêtre de 30 jours** plutôt que 3 — trois jours de biais sont du bruit
  (0,26 % contre 7,77 % à rayon égal) ;
* **portée de 200 km** plutôt que 50 — le biais de CAMS est **régional**
  (9,19 % contre 4,41 %) ;
* **donneurs de même typologie** — une station trafic ne se corrige pas depuis une station
  de fond (+2,3 points à rayon égal).

Cumulés : **9,19 % → 13,59 %.** C'est ce qui rend la comparaison équitable — une méthode
non réglée n'est pas un adversaire.

La loi des erreurs
--------------------
Un gain de RMSE ne dit pas **où** l'erreur a bougé. Le tableau donne donc, pour chaque
système, la part des prédictions par tranche d'erreur absolue. Une correction qui améliore
la RMSE en resserrant le centre tout en aggravant la queue se voit ici, et nulle part
ailleurs.

Usage : python3 scripts/tableau_comparatif.py --polluant NO2 --horizon 2
Sortie : reports/TABLEAU_<polluant>.md et reports/tableau_comparatif_<polluant>.csv
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
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from krigeage_du_biais import biais_interpole, matrice_distances  # noqa: E402

DECALAGE = 2
TRANCHES = [(0, 2), (2, 5), (5, 10), (10, 20), (20, np.inf)]
NOM_POLLUANT = {"PM10": "Particules PM10", "PM25": "Particules fines PM2,5",
                "O3": "Ozone", "NO2": "Dioxyde d'azote"}
SEUIL = {"PM10": 50.0, "PM25": 50.0, "O3": 120.0, "NO2": 200.0}

# Les bandes de sous-indice ATMO — ce sont ELLES qui décident de la couleur publiée, et
# les deux dernières qui déclenchent une communication. Un gain de RMSE qui ne fait
# franchir aucune borne ne change rien à ce que voit le public.
BANDES = {"O3": [(0, 40), (40, 80), (80, 120), (120, 180), (180, np.inf)],
          "NO2": [(0, 20), (20, 40), (40, 90), (90, 200), (200, np.inf)],
          "PM25": [(0, 10), (10, 20), (20, 25), (25, 50), (50, np.inf)],
          "PM10": [(0, 20), (20, 40), (40, 50), (50, 100), (100, np.inf)]}
NOM_BANDE = ["bon", "moyen", "dégradé", "MAUVAIS", "TRÈS MAUVAIS"]


def classe(x: np.ndarray, polluant: str) -> np.ndarray:
    """Numéro de bande ATMO — 0 à 4."""
    bornes = np.array([b for _, b in BANDES[polluant][:-1]])
    return np.searchsorted(bornes, x, side="right")


def charger_membres(polluant: str, jours: pd.Series) -> pd.DataFrame | None:
    fs = sorted(glob.glob(str(RACINE / f"data/processed/meteo/"
                              f"membres_metropole_{polluant.lower()}_*.parquet")))
    if not fs:
        return None
    t = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    # ⚠️ PREV'AIR fait tourner **DEUX** modèles — CHIMERE *et* MOCAGE (page « Le système
    # PREV'AIR »). Ancrer la ligne « stratégie AASQA » sur CHIMERE seul décrirait une
    # chaîne qui n'existe pas.
    if "chimere" not in t.columns:
        return None
    t["jour"] = pd.to_datetime(t["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    return t


def cle_tranche(a: float, b: float) -> str:
    return f"err_{int(a)}_{'inf' if np.isinf(b) else int(b)}"


def libelle_tranche(a: float, b: float) -> str:
    return f"{int(a)}-{'∞' if np.isinf(b) else int(b)}"


def loi_des_erreurs(o: np.ndarray, x: np.ndarray) -> dict:
    e = np.abs(x - o)
    return {cle_tranche(a, b): 100 * float(((e >= a) & (e < b)).mean())
            for a, b in TRANCHES}


def scores(o: np.ndarray, x: np.ndarray, ref: np.ndarray,
           ref_aasqa: np.ndarray | None = None) -> dict:
    """Les scores d'un système, contre **deux** références.

    ⚠️ Mesurer un gain contre CAMS brut seul flatte tout le monde : personne n'exploite
    CAMS brut. La référence qui décide, c'est la chaîne **en service** — un modèle
    déterministe corrigé par interpolation du biais récent. C'est contre elle qu'il faut
    se situer, et c'est la colonne `gain_vs_aasqa_pct`.
    """
    r = float(np.sqrt(np.mean((x - o) ** 2)))
    rr = float(np.sqrt(np.mean((ref - o) ** 2)))
    s = {"rmse": r, "gain_vs_cams_pct": 100 * (1 - r / rr) if rr else np.nan,
         "biais": float(np.mean(x - o)), "mae": float(np.mean(np.abs(x - o))),
         "correlation": float(np.corrcoef(o, x)[0, 1])}
    if ref_aasqa is not None:
        ra = float(np.sqrt(np.mean((ref_aasqa - o) ** 2)))
        s["gain_vs_aasqa_pct"] = 100 * (1 - r / ra) if ra else np.nan
    return s | loi_des_erreurs(o, x)


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

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")
    familles = list(cols_typo)

    from leviers_36mois import joindre_feux, joindre_membres  # noqa: PLC0415
    debut, fin = d["mois"].min().replace("-", ""), d["mois"].max().replace("-", "")
    for nom_f, fn in (("feux", lambda x: joindre_feux(x, debut, fin)),
                      ("membres", lambda x: joindre_membres(x, polluant, debut, fin))):
        try:
            d, aj = fn(d)
            familles += aj
        except Exception:  # noqa: BLE001
            pass

    # ── CHIMERE, s'il existe pour ce polluant ────────────────────────────────
    mem = charger_membres(polluant, d["jour"])
    a_chimere = mem is not None
    if a_chimere:
        agr = "max" if grandeur in ("max_8h", "max_horaire") else "mean"
        dispo = [m for m in ("chimere", "mocage") if m in mem.columns]
        jm = mem.groupby(["station_id", "jour"])[dispo].agg(agr).reset_index()
        if len(dispo) == 2:
            # La médiane de deux valeurs est leur moyenne — c'est la composition de
            # PREV'AIR, dans sa configuration européenne.
            jm["prevair_like"] = jm[["chimere", "mocage"]].mean(axis=1)
        avant = len(d)
        d = d.merge(jm, on=["station_id", "jour"], how="left")
        assert len(d) == avant
        a_chimere = d["chimere"].notna().mean() > 0.3
    a_prevair = a_chimere and "prevair_like" in d and d["prevair_like"].notna().mean() > 0.3
    print(f"{polluant} · {len(d):,} jours-station · {len(ids)} stations · "
          f"CHIMERE {'disponible' if a_chimere else 'ABSENT (pas de membres)'}", flush=True)

    # ── Les deux krigeages, ancrés sur CHIMERE quand il existe ───────────────
    dist, st = matrice_distances(ids)
    t = st["type_station"].fillna("?").to_numpy()
    memes = (t[:, None] == t[None, :]).astype(float)
    idx = {s: i for i, s in enumerate(ids)}
    lig = None
    krig = {}
    # L'ancre du krigeage est la composition de PREV'AIR quand elle existe — c'est ce que
    # « stratégie AASQA » veut dire.
    ancre_k = "prevair_like" if a_prevair else ("chimere" if a_chimere else "cams_jour")
    nom_ancre = {"prevair_like": "CHIMERE+MOCAGE", "chimere": "CHIMERE",
                 "cams_jour": "CAMS"}[ancre_k]
    d["_b"] = d["valeur"] - d[ancre_k]
    piv = d.pivot_table(index="jour", columns="station_id", values="_b",
                        aggfunc="mean").reindex(columns=ids)
    piv = piv.reindex(pd.date_range(piv.index.min(), piv.index.max(), freq="D"))
    lig = pd.Index(piv.index).get_indexer(pd.DatetimeIndex(d["jour"]))
    col = d["station_id"].map(idx).to_numpy()
    for nom, (fen, rayon, p, ty) in {
            "usuel": (7, 50.0, 2.0, None), "optimisé": (30, 200.0, 1.0, memes)}.items():
        roul = piv.shift(DECALAGE).rolling(fen, min_periods=max(2, fen // 3)).mean()
        corr = biais_interpole(roul, dist, 0, rayon, p, ty)[lig, col]
        krig[nom] = np.where(np.isfinite(corr), d[ancre_k].to_numpy() + corr,
                             d[ancre_k].to_numpy())

    # ── Notre modèle, toutes familles déployables ────────────────────────────
    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    mois = np.sort(d["mois"].unique())
    nous = np.full(len(d), np.nan)
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        mt, mr = (d["mois"] == m) & dans, (d["mois"] != m) & ~dans
        te, tr = d[mt], d[mr]
        if len(te) < 200 or len(tr) < 1000:
            continue
        nous[np.flatnonzero(mt.to_numpy())] = ajuster(DEFAUT, tr, te, base + familles,
                                                      "cams_jour")

    # ── Tous sur EXACTEMENT les mêmes lignes ─────────────────────────────────
    EUR = "Europe 0,1° · sans assimilation"
    systemes = [("① CAMS brut — ensemble 6 modèles", EUR, d["cams_jour"].to_numpy())]
    if a_chimere:
        systemes.append(("② CHIMERE seul", EUR + " ⚠️", d["chimere"].to_numpy()))
    if a_prevair:
        systemes.append(("③ CHIMERE+MOCAGE — composition PREV'AIR",
                         EUR + " ⚠️", d["prevair_like"].to_numpy()))
    systemes += [
        (f"④ {nom_ancre} + krigeage — réglages usuels", EUR + " ⚠️", krig["usuel"]),
        (f"⑤ {nom_ancre} + krigeage — OPTIMISÉ ici", EUR + " ⚠️", krig["optimisé"]),
        ("⑥ notre modèle — toutes familles", "CAMS Europe 0,1°", nous)]

    ok = np.isfinite(nous)
    for *_, x in systemes:
        ok &= np.isfinite(x)
    o = d["valeur"].to_numpy()[ok]
    ref = d["cams_jour"].to_numpy()[ok]
    # ── La référence qui compte : la chaîne EN SERVICE, pas le modèle brut ────
    # C'est la ligne « krigeage — réglages usuels » : un modèle déterministe corrigé par
    # interpolation du biais récent des stations voisines. Elle est ancrée sur
    # CHIMERE+MOCAGE quand les membres existent, sur CAMS sinon — le nom `nom_ancre` le dit.
    ref_aasqa = krig["usuel"][ok]
    print(f"  {ok.sum():,} lignes communes aux {len(systemes)} systèmes", flush=True)

    lignes = [{"systeme": n, "configuration": cfg, **scores(o, x[ok], ref, ref_aasqa)}
              for n, cfg, x in systemes]
    print(f"\n{'═' * 104}\n{NOM_POLLUANT[polluant]} · échéance "
          f"{'J0' if horizon == 1 else f'J+{horizon - 1}'} · {ok.sum():,} prédictions · "
          f"station ET mois cachés\n{'═' * 104}")
    print(f"  {'système':40s} {'configuration':30s} {'RMSE':>7s} {'/CAMS':>7s} "
          f"{'/AASQA':>7s} {'biais':>7s} {'r':>6s}    "
          + "".join(libelle_tranche(a, b).rjust(8) for a, b in TRANCHES))
    for r in lignes:
        tr = "".join(f"{r[cle_tranche(a, b)]:7.1f}%" for a, b in TRANCHES)
        print(f"  {r['systeme']:40s} {r['configuration']:30s} {r['rmse']:7.2f} "
              f"{r['gain_vs_cams_pct']:6.1f}% {r['gain_vs_aasqa_pct']:6.1f}% "
              f"{r['biais']:+7.2f} {r['correlation']:6.3f}    {tr}")
    print(f"\n  Colonne /CAMS : gain contre le modèle brut — flatte tout le monde, personne")
    print(f"  n'exploite CAMS brut. Colonne /AASQA : gain contre « {nom_ancre} + krigeage,")
    print(f"  réglages usuels » — la chaîne réellement en service. C'est celle qui décide.")
    print(f"\n  ⚠️ Les lignes marquées portent des modèles en configuration **européenne**")
    print(f"     à 0,1° sans assimilation. PREV'AIR fait tourner les MÊMES modèles en")
    print(f"     version **nationale** — maille plus fine, inventaire français, assimilation.")
    print(f"     Leur chaîne réelle est donc MEILLEURE que la ligne ④ qui la simule : le")
    print(f"     gain /AASQA affiché ici est un **majorant** de notre avance réelle sur eux.")
    print(f"     Nous ne pouvons pas corriger ce biais — leurs sorties nationales ne sont")
    print(f"     pas publiques. C'est l'objet de la demande d'archive envoyée à PREV'AIR.")
    # ── Ce qui décide vraiment : les situations critiques VUES ──────────────
    cl_obs = classe(o, polluant)
    critique = cl_obs >= 3            # classes MAUVAIS et TRÈS MAUVAIS
    n_crit = int(critique.sum())
    print(f"\n{'═' * 96}\nSITUATIONS CRITIQUES DÉTECTÉES — classes « mauvais » et pire\n"
          f"{'═' * 96}")
    print(f"  {n_crit:,} occurrences observées en classe ≥ 3 sur {len(o):,} "
          f"({100 * n_crit / len(o):.2f} %)")
    if n_crit < 30:
        print(f"  ⚠️ {n_crit} occurrences — mesuré, pas conclu.")
    else:
        print(f"\n  {'système':40s} {'vues':>7s} {'/':>1s}{'total':>7s} {'taux':>7s} "
              f"{'fausses':>9s} {'précision':>10s}")
        for nom, cfg, x in systemes:
            cl = classe(x[ok], polluant)
            vues = int(((cl >= 3) & critique).sum())
            fausses = int(((cl >= 3) & ~critique).sum())
            prec = vues / max(vues + fausses, 1)
            print(f"  {nom:40s} {vues:7d} /{n_crit:7d} {100 * vues / n_crit:6.1f}% "
                  f"{fausses:9d} {100 * prec:9.1f}%")
            for r in lignes:
                if r["systeme"] == nom:
                    r.update(critiques_observees=n_crit, critiques_vues=vues,
                             critiques_fausses=fausses,
                             taux_detection_pct=100 * vues / n_crit,
                             precision_critique_pct=100 * prec)
        print(f"\n  Bandes de sous-indice ATMO : "
              + " · ".join(f"{NOM_BANDE[i]} {int(a)}-{'∞' if np.isinf(b) else int(b)}"
                           for i, (a, b) in enumerate(BANDES[polluant])))
        print(f"  Une classe ≥ 3 déclenche une communication. C'est le seul compte qui")
        print(f"  décide de ce que le public voit.")

    print(f"\n  Les cinq dernières colonnes : part des prédictions dont l'erreur absolue")
    print(f"  tombe dans chaque tranche, en µg/m³. Une correction qui resserre le centre")
    print(f"  en aggravant la queue se voit ici, et nulle part dans la RMSE.")

    # ⚠️ Le DataFrame se construit **ici**, après le bloc critique — pas avant. Construit
    # en amont, il aurait figé une copie que les `r.update(...)` du bloc ci-dessus ne
    # touchent pas : les comptes de situations critiques s'affichaient à l'écran et
    # n'entraient dans aucun fichier. Défaut silencieux, quinze colonnes d'allure normale.
    t = pd.DataFrame(lignes)
    manquantes = [c for c in ("critiques_vues", "taux_detection_pct") if c not in t]
    if n_crit >= 30 and manquantes:
        raise SystemExit(f"comptes critiques absents du tableau : {manquantes}")
    t.insert(0, "polluant", polluant)
    t.insert(1, "horizon", horizon)
    t.insert(2, "n", int(ok.sum()))
    # ⚠️ **La fenêtre s'écrit dans le fichier, lue dans les données.** Sans elle, `n` seul
    # ne dit pas si 56 238 lignes couvrent 19 mois ou 31. Le cas s'est produit le 05/08 :
    # l'arrivée des membres d'ensemble PM10 (téléchargés le 04/08, disponibles seulement à
    # partir de 2025-01) a restreint tout le tableau PM10 à 19 mois — car les six systèmes
    # partagent les mêmes lignes, ce qui est l'invariant du tableau. PM10 se retrouve donc
    # sur une fenêtre différente des trois autres polluants, et rien ne le disait.
    mois = pd.to_datetime(d.loc[ok, "jour"]).dt.strftime("%Y-%m")
    t.insert(3, "fenetre", f"{mois.min()}→{mois.max()}")
    t.insert(4, "n_mois", int(mois.nunique()))
    t.to_csv(RACINE / f"reports/tableau_comparatif_{polluant}_h{horizon}.csv", index=False)

    # ── Les prédictions ligne à ligne, pour tout ce qui se calcule après coup ────
    # Sans ce fichier, chaque question posée au tableau — décomposition, recalage,
    # budget d'alerte — impose de refaire les 36 ajustements. Il coûte 2 Mo.
    brut = pd.DataFrame({"jour": d["jour"].to_numpy()[ok],
                         "station_id": d["station_id"].to_numpy()[ok],
                         "mois": d["mois"].to_numpy()[ok], "valeur": o})
    for i, (nom, _, x) in enumerate(systemes, 1):
        brut[f"sys{i}"] = x[ok]
    brut.attrs["systemes"] = [n for n, _, _ in systemes]
    dossier = RACINE / "data/processed/predictions"
    dossier.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"code": [f"sys{i}" for i in range(1, len(systemes) + 1)],
                  "systeme": [n for n, _, _ in systemes],
                  "configuration": [c for _, c, _ in systemes]}).to_csv(
        dossier / f"systemes_{polluant}_h{horizon}.csv", index=False)
    brut.to_parquet(dossier / f"comparatif_{polluant}_h{horizon}.parquet", index=False)

    print(f"\nÉcrit : reports/tableau_comparatif_{polluant}_h{horizon}.csv")
    print(f"        data/processed/predictions/comparatif_{polluant}_h{horizon}.parquet "
          f"({len(brut):,} lignes × {len(systemes)} systèmes) · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
