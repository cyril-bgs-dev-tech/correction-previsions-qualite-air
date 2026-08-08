#!/usr/bin/env python3
"""La méthode la plus puissante que ce projet sache construire — et ce que chaque pièce y ajoute.

La question
-------------
Le projet a mesuré une trentaine de leviers, **un par un, chacun contre la base**. Cela ne dit
pas ce que vaut leur somme : des leviers qui captent la même information ne s'additionnent
pas. `leviers_36mois.py` a commencé le travail mais il lui manque les deux sources acquises
depuis — **GEOS-CF** et la météo prévue — et il empile ERA5, qui est une réanalyse.

Ce script mesure l'empilement **complet et cumulatif**, dans l'ordre déclaré ci-dessous, et
rapporte pour chaque étage son **apport marginal une fois les précédents en place**. C'est le
seul chiffre honnête : l'apport d'une famille seule contre la base surestime toujours.

Les deux périmètres, qui ne se confondent jamais
--------------------------------------------------
* **PARTOUT** — utilisable en tout point du territoire, y compris là où aucune station
  n'existe. C'est le périmètre de la spatialisation.
* **AUX STATIONS** — exige l'historique d'observations du point. C'est le périmètre de
  l'exploitation sur réseau existant. `veille` bascule d'un périmètre à l'autre, et le
  projet a déjà confondu les deux.

ERA5 figure en dernier et **hors méthode** : c'est une réanalyse, elle n'existe pas quand la
prévision est émise. Son gain est un **plafond**, jamais une performance.

Deux familles écartées, et pourquoi — écrit AVANT de mesurer
--------------------------------------------------------------
* **La météo prévue (IFS).** Onze mois disponibles sur les vingt-neuf du corpus. Mesuré le
  05/08 sur GEOS-CF : à neuf mois, le gain d'une même famille balaie **−0,02 % à +3,76 %**
  selon les mois retenus (σ 1,31 pt) alors qu'il vaut 0,20 pt de dispersion sur le corpus
  entier. **Un corpus court ne mesure pas un petit gain** — il en affiche un. L'inscrire ici
  produirait un chiffre non réfutable. À reprendre quand la couverture sera faite.
* **Les dérivées d'ensemble** (asymétrie, aplatissement) : réfutées à +0,05 à +0,40 %, sous
  la barre de bruit.

La fenêtre d'évaluation, et pourquoi elle n'est pas celle du corpus complet
----------------------------------------------------------------------------
GEOS-CF v1 couvre **2023-08 → 2025-12** ; le corpus apparié va jusqu'à 2026-07. Laisser les
mois de 2026 avec une colonne GEOS-CF vide donnerait au modèle un **indicateur d'année
déguisé** : « geoscf est absent » vaut exactement « nous sommes en 2026 ». En validation par
mois cachés, c'est une fuite.

L'évaluation est donc **restreinte à la fenêtre de v1**, identique pour toutes les
configurations. Les gains absolus ne sont pas comparables à ceux de `leviers_36mois.py`, qui
porte sur 36 mois — seuls les **écarts entre étages** le sont, et c'est ce qu'on cherche.

⚠️ v1 et v2 de GEOS-CF ne sont pas le même prédicteur (ozone : +15,41 µg/m³ d'écart moyen sur
le mois de recouvrement). Ne jamais empiler les deux dans une même colonne.

Usage  : python3 scripts/methode_maximale.py --polluant NO2
Sortie : reports/methode_maximale_<polluant>_h<n>.csv
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

from apport_geoscf import charger_geoscf  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from leviers_36mois import (  # noqa: E402
    _fusion, gain, joindre_feux, joindre_membres, joindre_veille,
    joindre_meteo,
)

# L'ordre est **déclaré avant la mesure**. Le réordonner après coup pour flatter un étage
# serait choisir la conclusion : l'apport marginal dépend de la place dans la pile.
#
# `tendance` entre le 08/08 en DERNIÈRE position des familles PARTOUT, et c'est délibéré :
# c'est la place la plus dure, celle où il doit ajouter quelque chose que la typologie, les
# membres, les feux et GEOS-CF n'ont pas déjà capté. Le placer en tête l'aurait flatté.
# Le banc de préprocessing le donne gagnant sur **trois polluants sur quatre** en double
# aveugle, à l'écran comme en confirmation — O₃ +3,49 pt, PM10 +1,42, PM2,5 +1,63 — et
# **perdant sur le NO₂** (−0,10 pt, non significatif ; −0,61 significatif à l'écran).
# L'exception a un mécanisme : le résidu du NO₂ est attaché au site, pas à la dynamique.
ORDRE = ["typologie", "membres", "feux", "geoscf", "tendance"]
PERIMETRE = {"typologie": "PARTOUT", "membres": "PARTOUT", "feux": "PARTOUT",
             "geoscf": "PARTOUT", "tendance": "PARTOUT",
             "veille": "AUX STATIONS", "era5": "— (plafond)"}


def joindre_geoscf(d: pd.DataFrame, polluant: str) -> tuple[pd.DataFrame, list[str]]:
    """GEOS-CF **flux v1 uniquement** — le seul qui couvre une fenêtre mesurable."""
    g = charger_geoscf(GRANDEUR_PAR_POLLUANT[polluant], "v1")
    g["jour"] = pd.to_datetime(g["jour"]).dt.tz_localize(None)
    cols = [c for c in g.columns if c.startswith("geoscf_")]
    if not cols:
        raise SystemExit("aucune colonne GEOS-CF — le flux v1 est-il extrait ?")
    return _fusion(d, g, "geoscf"), cols


def main(polluant: str, horizon: int, n_spa: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    base_cols = colonnes_admises(jeu)
    jeu[base_cols] = jeu[base_cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, base_cols, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in base_cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    familles: dict[str, list[str]] = {}
    # ⚠️ La dynamique de CAMS se calcule **avant** toute restriction de fenêtre. Elle
    # décale la série d'un jour par station : la calculer après le filtrage sur la
    # couverture GEOS-CF ferait sauter le décalage par-dessus le bord de fenêtre, et la
    # veille du premier jour retenu viendrait du dernier jour d'une autre période.
    # Aucune observation n'entre ici — la prévision d'hier existe partout où celle
    # d'aujourd'hui existe, donc le périmètre PARTOUT est conservé.
    from banc_preprocessing import f_tendance_cams  # noqa: PLC0415
    tendance = f_tendance_cams(d)
    if collision := [c for c in tendance.columns if c in d.columns]:
        raise SystemExit(f"colonnes de tendance déjà présentes : {collision}")
    d = pd.concat([d, tendance], axis=1)
    familles["tendance"] = list(tendance.columns)

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    familles["typologie"] = list(cols_typo)

    d, familles["geoscf"] = joindre_geoscf(d, polluant)
    # ⚠️ La fenêtre se lit **dans les données**, jamais dans le nom des fichiers (règle 4 bis).
    couvert = d[familles["geoscf"][0]].notna()
    if not couvert.any():
        raise SystemExit("GEOS-CF ne couvre aucune ligne — jointure à vérifier")
    mois_ok = sorted(d.loc[couvert, "mois"].unique())
    avant = len(d)
    d = d[d["mois"].isin(mois_ok)].reset_index(drop=True)
    print(f"\n  fenêtre d'évaluation = couverture GEOS-CF v1 : {mois_ok[0]} → {mois_ok[-1]}"
          f" ({len(mois_ok)} mois) · {len(d):,} jours-station sur {avant:,}", flush=True)

    debut, fin = mois_ok[0].replace("-", ""), mois_ok[-1].replace("-", "")
    d, familles["membres"] = joindre_membres(d, polluant, debut, fin)
    d, familles["feux"] = joindre_feux(d, debut, fin)
    d, familles["veille"] = joindre_veille(d)
    d, familles["era5"] = joindre_meteo(d, debut, fin)
    for nom in list(familles):
        familles[nom] = [c for c in familles[nom] if c in d.columns]
        if not familles[nom]:
            print(f"  ⚠️ famille « {nom} » vide après jointure — écartée de la pile")
            del familles[nom]

    # ── Les configurations, cumulatives et déclarées ─────────────────────────────────
    configs: list[tuple[str, list[str], str]] = [("base (CAMS, terrain, calendrier)",
                                                  list(base), "PARTOUT")]
    cumul = list(base)
    for nom in ORDRE:
        if nom not in familles:
            continue
        cumul = cumul + familles[nom]
        configs.append((f"+ {nom}", list(cumul), PERIMETRE[nom]))
    partout = list(cumul)
    configs.append(("★ MAXIMALE — PARTOUT", list(partout), "PARTOUT"))
    if "veille" in familles:
        configs.append(("★ MAXIMALE — AUX STATIONS (+ veille)",
                        partout + familles["veille"], "AUX STATIONS"))
    if "era5" in familles:
        configs.append(("plafond ERA5 (NON déployable)",
                        partout + familles.get("veille", []) + familles["era5"],
                        "— (plafond)"))

    # ── Le protocole : double aveugle, station ET mois cachés ────────────────────────
    rng = np.random.default_rng(GRAINE)
    ids = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(ids), n_spa)
    plis = []
    for i, mm in enumerate(mois_ok):
        dans = d["station_id"].isin(groupes[i % n_spa])
        plis.append((mm, (d["mois"] == mm) & dans, (d["mois"] != mm) & ~dans))

    print(f"\n{'═' * 100}")
    print(f"MÉTHODE MAXIMALE — {polluant} J+{horizon} · double aveugle, station ET mois cachés")
    print(f"{'═' * 100}")
    print(f"  {'configuration':38s} {'périmètre':14s} {'col.':>5s} {'gain':>8s} "
          f"{'marginal':>9s} {'σ':>6s} {'plis<0':>7s}")
    # Le fichier `.partiel` est écrit après CHAQUE configuration. Un plantage machine a
    # déjà coûté trois configurations mesurées et perdues (05/08, 01 h 08) : un script qui
    # n'écrit qu'à la fin transforme n'importe quelle interruption en zéro résultat.
    partiel = RACINE / f"reports/methode_maximale_{polluant}_h{horizon}.csv.partiel"

    # ── Le PÉRIMÈTRE EFFECTIF, affiché avant la première mesure ──────────────────
    # `CLAUDE.md` § 2 quater : un pli écarté pour effectif insuffisant change le
    # dénominateur sans rien dire. C'est ainsi que PM10 a tourné sur 24 plis au lieu de
    # 29 — visible seulement parce que `n_plis` finit dans le CSV, et encore : sans le
    # nombre PRÉVU à côté, un compte ne dit pas qu'il en manque. Le rejet ne dépend pas
    # de la configuration (seulement des effectifs), il se calcule donc une seule fois.
    ecartes = [(e, int(d[m_te].shape[0]), int(d[m_tr].shape[0])) for e, m_te, m_tr in plis
               if len(d[m_te]) < 200 or len(d[m_tr]) < 1000]
    n_prevus = len(plis)
    if ecartes:
        print(f"  ⚠️ {len(ecartes)} pli(s) écarté(s) sur {n_prevus} pour effectif "
              f"insuffisant (test < 200 ou train < 1 000) :", flush=True)
        for e, nte, ntr in ecartes:
            print(f"       {e} — test {nte:,} · train {ntr:,}", flush=True)
    print(f"  périmètre effectif : {n_prevus - len(ecartes)} plis exécutés "
          f"sur {n_prevus} prévus", flush=True)

    # ── Reprise sur le `.partiel` (règle 4) ──────────────────────────────────────
    # Le segfault de chargement mesuré le 08/08 est **intermittent** : la même commande
    # tombe environ une fois sur deux, et les données ne sont pas en cause — le fichier
    # d'abord accusé (`..._o3_202406.parquet`) passe cinq fois de suite quand il est lu
    # seul. Sans reprise, chaque tentative rejoue les configurations déjà mesurées et le
    # lot n'aboutit jamais ; avec reprise, il aboutit en quelques tentatives.
    #
    # La reprise porte sur le **nom** des configurations, jamais sur leur nombre : un
    # `.partiel` écrit par une version antérieure n'a pas les mêmes étages, et un compte
    # ne le dirait pas. Et elle est invalidée si la fenêtre du corpus a changé — sinon on
    # recollerait des mesures faites sur deux périmètres différents.
    lignes, precedent = [], None
    fenetre_courante = f"{mois_ok[0]}→{mois_ok[-1]}"
    if partiel.exists():
        deja = pd.read_csv(partiel)
        attendues = {nom for nom, _, _ in configs}
        fenetres = set(deja.get("fenetre", pd.Series(dtype=str)).astype(str))
        if fenetres - {fenetre_courante}:
            print(f"  ⚠️ .partiel écarté — fenêtre {fenetres} ≠ {fenetre_courante}",
                  flush=True)
        else:
            for r in deja.to_dict("records"):
                if r["configuration"] not in attendues:
                    print(f"  ⚠️ .partiel : « {r['configuration']} » n'existe plus dans "
                          f"cette version — ligne ignorée", flush=True)
                    continue
                lignes.append(r)
                print(f"  {r['configuration']:38s} {r['perimetre']:14s} "
                      f"{r['n_colonnes']:>5d} {r['gain_pct']:+7.2f}%"
                      f"{'':>10}{'':>7}{'':>8}  ↷ repris du .partiel", flush=True)
                if not str(r["configuration"]).startswith(("★", "plafond")):
                    precedent = float(r["gain_pct"])
    faites = {r["configuration"] for r in lignes}

    for nom, colonnes, per in configs:
        if nom in faites:
            continue
        t0 = time.time()
        obs, cams, pred, gains = [], [], [], []
        for _, m_te, m_tr in plis:
            te, tr = d[m_te], d[m_tr]
            if len(te) < 200 or len(tr) < 1000:
                continue
            p = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
            o, c = te["valeur"].to_numpy(), te["cams_jour"].to_numpy()
            gains.append(gain(o, c, p))
            obs.append(o); cams.append(c); pred.append(p)
        g = gain(np.concatenate(obs), np.concatenate(cams), np.concatenate(pred))
        marge = np.nan if precedent is None else g - precedent
        neg = int(np.sum(np.array(gains) < 0))
        print(f"  {nom:38s} {per:14s} {len(colonnes):>5d} {g:+7.2f}% "
              f"{'—' if precedent is None else f'{marge:+8.2f}'} "
              f"{np.std(gains):6.2f} {neg:>4d}/{len(gains)}"
              f"  [{(time.time() - t0) / 60:.1f} min · cumul {(time.time() - depart) / 60:.1f}]",
              flush=True)
        lignes.append({"polluant": polluant, "horizon": horizon, "configuration": nom,
                       "perimetre": per, "n_colonnes": len(colonnes), "gain_pct": g,
                       "apport_marginal_pct": marge, "ecart_type": float(np.std(gains)),
                       "n_plis_negatifs": neg, "n_plis": len(gains),
                       "n_plis_prevus": n_prevus, "n_plis_ecartes": len(ecartes),
                       "fenetre": f"{mois_ok[0]}→{mois_ok[-1]}", "n_mois": len(mois_ok)})
        pd.DataFrame(lignes).to_csv(partiel, index=False)   # jamais le nom définitif
        if not nom.startswith("★") and not nom.startswith("plafond"):
            precedent = g

    # ⚠️ La table se construit APRÈS la dernière mesure (règle 2 ter), et l'on exige
    # nommément les colonnes attendues avant d'écrire.
    t = pd.DataFrame(lignes)
    for c in ("gain_pct", "apport_marginal_pct", "perimetre", "n_mois"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")
    f = RACINE / f"reports/methode_maximale_{polluant}_h{horizon}.csv"
    t.to_csv(f, index=False)
    partiel.unlink(missing_ok=True)   # le nom définitif ne paraît qu'une fois complet
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
