#!/usr/bin/env python3
"""À quelle échelle faut-il décider ? — l'agrégateur de zone et le critère de persistance.

Le défaut que ce script attaque
---------------------------------
`episodes_reels.py` confronte nos prédictions aux **52 procédures préfectorales réellement
déclarées** en Occitanie. Il agrège les stations d'un département par le **maximum** :
« au moins une station dépasse ». C'est l'agrégateur qui **maximise les fausses alertes** —
et c'est exactement là que le dossier est mauvais : sur l'ozone, 473 fausses contre 102 à
CAMS brut.

Or la décision n'a jamais été posée comme un choix. Le maximum n'a pas été retenu : il a été
**subi**. Deux leviers, jamais testés, ne demandent aucun réentraînement :

1. **L'agrégateur de zone.** Les erreurs se décorrèlent entre stations d'un même
   département ; exiger deux stations plutôt qu'une, ou un quantile de zone, doit couper les
   fausses alertes plus vite qu'il ne coupe les épisodes installés.
2. **La persistance.** La procédure préfectorale exige persistance et superficie ; notre
   règle est **instantanée**. Exiger un dépassement prédit deux jours de suite tue l'alerte
   isolée sans toucher à l'épisode installé.

Les deux se composent : ce script mesure la **grille complète** agrégateur × persistance.

Les trois garde-fous, posés AVANT de mesurer
----------------------------------------------
* **La même règle est appliquée à tous les systèmes** — observation, CAMS brut, chaîne
  AASQA, notre modèle. Choisir notre agrégateur et laisser aux autres le maximum serait se
  comparer à armes inégales, **en notre faveur** cette fois. Le projet a déjà commis la
  faute symétrique (`CLAUDE.md` § 4 ter).
* **L'effectif est petit** — 52 épisodes, ~5 200 zones-jours. Tout écart se lit avec son
  intervalle, obtenu par bootstrap sur les zones-jours. Un écart dont l'intervalle enjambe
  zéro ne se publie pas comme un résultat.
* **La règle retenue est choisie hors échantillon** — sur la première moitié du calendrier,
  évaluée sur la seconde, et **la sélection est faite séparément pour chaque système**, avec
  la même liberté pour tous. Choisir la règle sur les données qui l'évaluent fabriquerait un
  score, défaut déjà corrigé ailleurs dans ce projet.

Ce que ce script ne peut pas faire
------------------------------------
Il ne crée aucune information : il **déplace un point de fonctionnement**. Un gain de
précision se paie en rappel, sauf si les erreurs sont réellement décorrélées entre stations
— c'est précisément l'hypothèse testée, et elle peut être fausse.

Usage  : python3 scripts/agregation_zone.py [--horizon 1]
Sortie : reports/agregation_zone_occitanie.csv        (grille complète)
         reports/agregation_zone_hors_echantillon.csv (règle choisie hors échantillon)
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

from appariement import presence, valeur_associee  # noqa: E402
from episodes_reels import EPISODES, POLLUANT_DE, SEUILS, sans_accent  # noqa: E402
from episodes_reels import stations_par_departement  # noqa: E402
from pages_soutenance import charger, recaler  # noqa: E402

SYSTEMES = {"observation": "valeur", "CAMS brut": "cams",
            "chaîne AASQA": "aasqa_r", "notre modèle": "nous_r"}
GRAINE = 12345
N_BOOT = 2000


# ── Les agrégateurs de zone ────────────────────────────────────────────────────────────
#
# Chacun prend les valeurs des stations d'une zone-jour et rend UN nombre, comparé ensuite
# au seuil. Le maximum est l'existant ; les autres sont les candidats.
#
# ⚠️ `k parmi n` est structurellement pénalisé dans un département à une seule station : il
# n'y déclenche jamais. Ce n'est pas un défaut de la règle, c'est une propriété du réseau,
# et le rapport publie donc le nombre de stations par département.
AGREGATEURS = {
    "max (existant)":  lambda v, s: np.max(v),
    "2ᵉ plus forte":   lambda v, s: np.sort(v)[-2] if len(v) >= 2 else -np.inf,
    "3ᵉ plus forte":   lambda v, s: np.sort(v)[-3] if len(v) >= 3 else -np.inf,
    "quantile 75 %":   lambda v, s: np.quantile(v, 0.75),
    "médiane":         lambda v, s: np.median(v),
    "moyenne":         lambda v, s: np.mean(v),
}
# Part des stations de la zone au-dessus du seuil — exprimé en fraction, comparé à sa
# propre borne et non au seuil de concentration. Traité à part pour cette raison.
FRACTIONS = {"≥ 25 % des stations": 0.25, "≥ 50 % des stations": 0.50}


def scores(vu: np.ndarray, reel: np.ndarray) -> dict:
    att = int((vu & reel).sum())
    faux = int((vu & ~reel).sum())
    rate = int((~vu & reel).sum())
    return {"attrapes": att, "rates": rate, "fausses": faux,
            "n_alertes": int(vu.sum()),
            "rappel_pct": 100 * att / max(int(reel.sum()), 1),
            "precision_pct": 100 * att / max(att + faux, 1),
            "csi": att / max(att + faux + rate, 1)}


def bornes_bootstrap(vu: np.ndarray, reel: np.ndarray, rng) -> dict:
    """Intervalle à 90 % par rééchantillonnage des zones-jours.

    L'effectif d'épisodes est de l'ordre de la dizaine : sans cet intervalle, un écart de
    deux détections se lirait comme un résultat.

    **Le rééchantillonnage se fait sur la table de contingence, pas sur les zones-jours.**
    C'est exact et non une approximation : chaque zone-jour tombe dans exactement une des
    quatre cases (VP, FP, FN, VN), donc tirer n zones-jours avec remise revient à tirer
    les quatre effectifs dans une multinomiale de mêmes proportions. Le rééchantillonnage
    naïf coûtait ici 1,3 milliard d'opérations Python ; celui-ci en coûte 2 000.
    """
    n = len(vu)
    vp = int((vu & reel).sum()); fp = int((vu & ~reel).sum())
    fn = int((~vu & reel).sum()); vn = n - vp - fp - fn
    tirs = rng.multinomial(n, np.array([vp, fp, fn, vn]) / n, size=N_BOOT)
    a, f, r = tirs[:, 0], tirs[:, 1], tirs[:, 2]
    rap = 100 * a / np.maximum(a + r, 1)
    pre = 100 * a / np.maximum(a + f, 1)
    return {"rappel_b5": float(np.percentile(rap, 5)), "rappel_b95": float(np.percentile(rap, 95)),
            "precision_b5": float(np.percentile(pre, 5)),
            "precision_b95": float(np.percentile(pre, 95))}


def table_zone_jour(d: pd.DataFrame, deps: set) -> pd.DataFrame:
    """Une ligne par (département, jour), portant les valeurs agrégées de chaque système.

    Les colonnes sont **nommées**, jamais prises par position, et leur présence est exigée
    avant tout calcul (`CLAUDE.md` § 2 bis).
    """
    manquantes = [c for c in SYSTEMES.values() if c not in d.columns]
    if manquantes:
        raise SystemExit(f"colonnes absentes des prédictions : {manquantes}")

    lignes = []
    for (dep, jour), bloc in d.groupby(["dep", "jour"], sort=True):
        ligne = {"dep": dep, "jour": jour, "n_stations": len(bloc)}
        for nom, col in SYSTEMES.items():
            v = bloc[col].to_numpy(float)
            v = v[np.isfinite(v)]
            if len(v) == 0:
                ligne[f"{nom}|vide"] = True
                continue
            for a, f in AGREGATEURS.items():
                ligne[f"{nom}|{a}"] = f(v, None)
            ligne[f"{nom}|__valeurs__"] = v
        lignes.append(ligne)
    return pd.DataFrame(lignes)


def appliquer(g: pd.DataFrame, systeme: str, regle: str, seuil: float,
              persistance: bool) -> np.ndarray:
    """Vrai/faux par zone-jour, pour un système, une règle et un critère de persistance."""
    if regle in FRACTIONS:
        part = FRACTIONS[regle]
        vu = np.array([
            (np.mean(v >= seuil) >= part) if isinstance(v, np.ndarray) and len(v) else False
            for v in g[f"{systeme}|__valeurs__"]])
    else:
        col = g[f"{systeme}|{regle}"].to_numpy(float)
        vu = np.nan_to_num(col, nan=-np.inf) >= seuil

    if not persistance:
        return vu
    # Persistance : la règle doit tenir aujourd'hui **et** la veille, dans la même zone.
    # Le décalage se fait par (zone, jour−1) explicitement — jamais par `shift()` sur un
    # tableau dont l'ordre est supposé (`CLAUDE.md` § 4 bis).
    # L'appariement passe par `appariement.valeur_associee` et non par un dictionnaire de
    # tuples : itérer une colonne de dates matérialise chaque valeur en `Timestamp`, et ce
    # chemin échoue systématiquement sur cette machine (10/08/2026, six tentatives sur six).
    # Le décalage reste explicite — c'est bien (zone, jour−1) qui est cherché.
    veille = valeur_associee(g, g, ("dep", "jour"), vu,
                             decalage=-pd.Timedelta(days=1), defaut=False)
    return vu & veille


def main(horizon: int, min_stations: int) -> int:
    depart = time.time()
    rng = np.random.default_rng(GRAINE)

    ep = pd.read_parquet(EPISODES)
    ep["jour"] = pd.to_datetime(ep["date_ech"]).dt.normalize()
    ep["dep"] = ep["lib_zone"].map(sans_accent)
    ep["polluant"] = ep["lib_pol"].map(POLLUANT_DE)
    ep = ep.dropna(subset=["polluant"])

    par_dep = stations_par_departement()
    inconnus = sorted(set(ep["dep"]) - set(par_dep))
    if inconnus:
        n_perdus = int(ep["dep"].isin(inconnus).sum())
        print(f"⚠️ {n_perdus} épisode(s) INÉVALUABLES — aucune station dans : "
              f"{', '.join(inconnus)}", flush=True)
        ep = ep[~ep["dep"].isin(inconnus)]

    lignes, hors_ech = [], []
    for polluant, (seuil, nature) in SEUILS.items():
        vrais = ep[ep["polluant"] == polluant]
        if vrais.empty:
            continue
        d = charger(polluant, horizon)
        if d is None:
            print(f"  {polluant} : aucune prédiction", flush=True)
            continue
        d = recaler(d, ["nous", "aasqa"])
        d["jour"] = pd.to_datetime(d["jour"]).dt.normalize()
        appartenance = {s: dep for dep, ss in par_dep.items() for s in ss}
        d["dep"] = d["station_id"].map(appartenance)
        d = d[d["dep"].isin(set(ep["dep"]))]
        if d.empty:
            continue

        # Second contrôle d'inévaluabilité, **par polluant** — voir `episodes_reels.py`.
        # Un département peut porter une station et aucune prédiction (ARIÈGE) : ses
        # épisodes sortaient du dénominateur en silence, ce qui gonfle le rappel.
        muets = sorted(set(vrais["dep"]) - set(d["dep"]))
        if muets:
            print(f"\n⚠️ {polluant} : {int(vrais['dep'].isin(muets).sum())} épisode(s) "
                  f"INÉVALUABLES — aucune station prédite dans : {', '.join(muets)}",
                  flush=True)
            vrais = vrais[~vrais["dep"].isin(muets)]
            if vrais.empty:
                continue

        # ⚠️ **Séparer les deux mécanismes.** Une règle « k parmi n » ne peut pas déclencher
        # dans un département de moins de k stations : elle l'éteint. Le réseau occitan a une
        # **médiane de 2 stations par département** et seuls 3 départements sur 9 en ont ≥ 3,
        # qui portent 11 des 12 épisodes d'ozone. Sans ce filtre, la baisse de fausses alertes
        # se lirait comme une décorrélation entre stations alors qu'elle vient d'un
        # **silence sélectif** là où le réseau ne peut pas confirmer. `--min-stations 3`
        # restreint l'évaluation aux départements où la règle est réellement applicable, et
        # ce qui subsiste alors est le mécanisme, pas l'artefact.
        if min_stations > 1:
            n_par_dep = d.groupby("dep")["station_id"].nunique()
            gardes = set(n_par_dep[n_par_dep >= min_stations].index)
            perdus = int(vrais["dep"].isin(set(n_par_dep.index) - gardes).sum())
            print(f"\n  filtre ≥ {min_stations} stations : {len(gardes)} départements sur "
                  f"{len(n_par_dep)} retenus · {perdus} épisode(s) écarté(s)", flush=True)
            d = d[d["dep"].isin(gardes)]
            vrais = vrais[vrais["dep"].isin(gardes)]
            if d.empty or vrais.empty:
                continue

        g = table_zone_jour(d, set(ep["dep"]))
        g["reel"] = presence(g, vrais, ("dep", "jour"))
        reel = g["reel"].to_numpy()
        n_ep = int(reel.sum())

        print(f"\n{'═' * 104}")
        print(f"{polluant} · seuil {seuil:.0f} µg/m³ — {nature}")
        print(f"{len(g):,} zones-jours · {g['dep'].nunique()} départements · "
              f"{n_ep} épisodes retrouvés · médiane {g['n_stations'].median():.0f} "
              f"stations/zone (min {g['n_stations'].min():.0f}, max {g['n_stations'].max():.0f})")
        print(f"{'═' * 104}")
        print(f"  {'règle':22s} {'pers.':>5s} {'système':14s} {'attr':>5s} {'fausses':>8s} "
              f"{'rappel':>8s} {'  IC 90 %':>15s} {'précis.':>8s} {'  IC 90 %':>15s}")

        toutes = list(AGREGATEURS) + list(FRACTIONS)
        for regle in toutes:
            for pers in (False, True):
                for systeme in SYSTEMES:
                    vu = appliquer(g, systeme, regle, seuil, pers)
                    m = scores(vu, reel)
                    ic = bornes_bootstrap(vu, reel, rng)
                    lignes.append({"polluant": polluant, "seuil": seuil, "regle": regle,
                                   "persistance": pers, "systeme": systeme,
                                   "n_episodes": n_ep, "n_zones_jours": len(g),
                                   **m, **ic})
                    if systeme in ("CAMS brut", "notre modèle"):
                        print(f"  {regle:22s} {'oui' if pers else '—':>5s} {systeme:14s} "
                              f"{m['attrapes']:5d} {m['fausses']:8d} "
                              f"{m['rappel_pct']:7.1f}% "
                              f"[{ic['rappel_b5']:5.1f};{ic['rappel_b95']:5.1f}] "
                              f"{m['precision_pct']:7.1f}% "
                              f"[{ic['precision_b5']:5.1f};{ic['precision_b95']:5.1f}]")

        # ── La règle choisie HORS ÉCHANTILLON, séparément pour chaque système ──────────
        #
        # ⚠️ **Un département exclu à la fois, jamais une découpe chronologique.** La
        # première version coupait le calendrier en deux : les 12 épisodes d'ozone sont
        # tombés **tous les 12** dans la première moitié et la seconde en contenait zéro —
        # l'évaluation portait sur un ensemble vide et rendait 0,0 % partout. Un phénomène
        # saisonnier ne se coupe pas dans le temps. Exclure un département teste en outre
        # ce qui nous intéresse vraiment : la règle **transfère-t-elle à une zone inconnue**.
        deps = np.sort(g["dep"].unique())
        print(f"\n  ── règle choisie sur les autres départements, appliquée au "
              f"département exclu ({len(deps)} départements, {n_ep} épisodes) ──")
        for systeme in SYSTEMES:
            annonce = np.zeros(len(g), bool)
            choisies: dict[tuple, int] = {}
            for dd in deps:
                test = (g["dep"] == dd).to_numpy()
                appr = ~test
                if reel[appr].sum() == 0:
                    continue            # aucun épisode pour choisir : on n'annonce rien
                meilleur, best = None, -1.0
                for regle in toutes:
                    for pers in (False, True):
                        vu = appliquer(g, systeme, regle, seuil, pers)
                        c = scores(vu[appr], reel[appr])["csi"]
                        if c > best:
                            meilleur, best = (regle, pers), c
                annonce[test] = appliquer(g, systeme, *meilleur[:1], seuil,
                                          meilleur[1])[test]
                choisies[meilleur] = choisies.get(meilleur, 0) + 1
            m = scores(annonce, reel)
            ic = bornes_bootstrap(annonce, reel, rng)
            majoritaire = max(choisies, key=choisies.get) if choisies else ("—", False)
            etiquette = f"{majoritaire[0]}{' + persistance' if majoritaire[1] else ''}"
            print(f"    {systeme:14s} → {etiquette:36s} "
                  f"rappel {m['rappel_pct']:5.1f}% [{ic['rappel_b5']:.1f};{ic['rappel_b95']:.1f}]"
                  f"  précision {m['precision_pct']:5.1f}% "
                  f"[{ic['precision_b5']:.1f};{ic['precision_b95']:.1f}]"
                  f"  ({m['fausses']} fausses)")
            hors_ech.append({"polluant": polluant, "systeme": systeme,
                             "regle_choisie": majoritaire[0], "persistance": majoritaire[1],
                             "n_regles_distinctes": len(choisies),
                             "n_departements": len(deps),
                             "n_episodes_test": n_ep,
                             "n_zones_jours_test": len(g), **m, **ic})

    if not lignes:
        raise SystemExit("rien à évaluer")

    # ⚠️ Les tables se construisent APRÈS la dernière mesure, et l'on exige nommément les
    # colonnes attendues avant d'écrire (`CLAUDE.md` § 2 ter).
    t = pd.DataFrame(lignes)
    for c in ("rappel_pct", "precision_pct", "rappel_b5", "precision_b95", "regle"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")
    suffixe = "" if min_stations <= 1 else f"_min{min_stations}"
    t["min_stations"] = min_stations
    f1 = RACINE / f"reports/agregation_zone_occitanie{suffixe}.csv"
    t.to_csv(f1, index=False)

    t2 = pd.DataFrame(hors_ech)
    for c in ("regle_choisie", "rappel_pct", "precision_pct"):
        if c not in t2:
            raise SystemExit(f"colonne « {c} » absente du rapport hors échantillon")
    t2["min_stations"] = min_stations
    f2 = RACINE / f"reports/agregation_zone_hors_echantillon{suffixe}.csv"
    t2.to_csv(f2, index=False)

    print(f"\n⚠️ Effectif d'épisodes de l'ordre de la dizaine : un écart dont l'intervalle")
    print(f"   enjambe celui du système comparé n'est PAS un résultat.")
    print(f"\nÉcrit : {f1.relative_to(RACINE)} · {f2.relative_to(RACINE)} · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--horizon", type=int, default=1)
    a.add_argument("--min-stations", type=int, default=1,
                   help="n'évaluer que les départements portant au moins N stations — "
                        "sépare le silence sélectif du vrai effet d'agrégation")
    n = a.parse_args()
    raise SystemExit(main(n.horizon, n.min_stations))
