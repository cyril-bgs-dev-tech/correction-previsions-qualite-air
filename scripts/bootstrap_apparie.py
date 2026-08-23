#!/usr/bin/env python3
"""L'incertitude d'un écart entre deux modèles — APPARIÉE, par blocs de mois et de stations.

Pourquoi ce script, et pourquoi la barre de bruit du dépôt ne convient pas
---------------------------------------------------------------------------
Ce dépôt a mesuré une barre de bruit de **±2,02 pt**, dominée par la composition des plis.
Elle porte sur un **score absolu, non apparié**. Or deux configurations comparées ici sont
ajustées et notées sur **exactement les mêmes lignes** : le déplacement commun causé par
une partition se **soustrait**. Comparer un écart apparié à une barre non appariée
surestime l'incertitude de plusieurs fois, et ferait déclarer « dans le bruit » des effets
qui n'y sont pas.

La quantité à estimer n'est donc pas la dispersion de chaque score, mais celle de la
**différence de pertes sur les mêmes observations** :

    d(s,t) = (obs − pred_candidat)² − (obs − pred_reference)²

Pourquoi des blocs, et pourquoi DEUX familles
-----------------------------------------------
Les résidus de qualité de l'air sont corrélés **dans le temps** (un épisode dure des jours)
et **dans l'espace** (les résidus PM restent corrélés sur des centaines de kilomètres). Un
bootstrap sur les lignes traiterait 200 000 observations comme 200 000 informations
indépendantes et rendrait un intervalle absurdement étroit. On rééchantillonne donc des
**mois entiers** et des **groupes géographiques**, puis on garde leur produit.

⚠️ **Ce que cet intervalle ne restaure pas.** Le bloc de test a déjà été consulté — pour
choisir des hyperparamètres, arrêter un réseau, lire un résultat. L'intervalle est
**conditionnel à ce test** ; il ne rend pas au bloc sa virginité. Une conclusion
confirmatoire demande une origine future.

Usage : python3 scripts/bootstrap_apparie.py --predictions reports/predictions_speciation_PM10.parquet
Sortie : reports/bootstrap_<nom>.csv
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

GRAINE = 20260817


def clusters_stations(d: pd.DataFrame, n: int) -> pd.Series:
    """Groupes géographiques fixes — la corrélation spatiale des résidus l'impose.

    Un découpage ALÉATOIRE des stations serait un aveu : il supposerait indépendantes des
    stations voisines dont les résidus sont précisément corrélés.

    🔴 Deux défauts corrigés le 23/08/2026, relevés par une revue externe et vérifiés ici
    -----------------------------------------------------------------------------------
    ① **Le partitionnement était ajusté sur les LIGNES de prédiction, pas sur les
       stations.** Une station présente sur 900 jours pesait donc 900 fois dans KMeans,
       une station sur 200 jours 200 fois : les centres étaient tirés vers les stations à
       long historique, et les grappes ne décrivaient plus la géographie mais la durée de
       fonctionnement du réseau. Le bootstrap rééchantillonnait alors des blocs dont la
       définition dépendait de ce qu'on cherchait à mesurer.

    ② **Les distances étaient calculées en degrés.** À la latitude de la France, un degré
       de longitude vaut ~0,68 degré de latitude en mètres : KMeans y voit un espace étiré
       d'un tiers selon l'axe est-ouest. Le référentiel porte déjà `x_l93`/`y_l93`
       (Lambert-93, EPSG:2154) — la projection existait, elle n'était pas utilisée. C'est
       la même erreur que `aq.features.exposure` documente pour l'exposition, à un autre
       endroit du dépôt.

    Aucun des deux ne lève : les grappes existaient, le bootstrap tournait, l'intervalle
    sortait. Ils déplaçaient seulement ce que « bloc géographique » voulait dire.
    """
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "x_l93", "y_l93"]).dropna()
    st = st.drop_duplicates("station_id")

    # Une ligne par STATION : c'est l'unité géographique, pas la ligne de prédiction.
    uniques = pd.DataFrame({"station_id": d["station_id"].unique()}).merge(
        st, on="station_id", how="left")
    if (manque := int(uniques["x_l93"].isna().sum())):
        raise SystemExit(f"{manque} station(s) sans coordonnées projetées — "
                         f"clusters impossibles")
    from sklearn.cluster import KMeans  # noqa: PLC0415

    km = KMeans(n_clusters=min(n, len(uniques)), random_state=GRAINE, n_init=10)
    uniques["cl"] = km.fit_predict(uniques[["x_l93", "y_l93"]].to_numpy())
    return d["station_id"].map(uniques.set_index("station_id")["cl"])


def main(chemin: str, tirages: int, n_clusters: int, bloc_mois: int,
         axe: str = "double") -> int:
    t0 = time.time()
    f = Path(chemin)
    d = pd.read_parquet(f)
    for c in ("obs", "pred_reference", "pred_candidat", "station_id", "jour"):
        if c not in d.columns:
            raise SystemExit(f"colonne absente : {c}")
    d["mois"] = pd.to_datetime(d["jour"]).dt.strftime("%Y-%m")

    # ── ④ Les pertes doivent être ATOMIQUES, pas agrégées ──────────────────────────
    #
    # 🔴 Une RMSE déjà moyennée par pli ne permet pas de reconstruire la variance du
    # différentiel : l'agrégation a détruit la covariance entre les deux séries de
    # prédictions sur les mêmes lignes, qui est précisément ce que l'appariement exploite.
    # Un fichier d'entrée à une ligne par (station, mois) au lieu de (station, jour)
    # produirait un intervalle plausible et faux — plus étroit ou plus large selon le sens
    # de la corrélation détruite, sans qu'aucune exception ne lève.
    #
    # Le contrôle porte sur la GRANULARITÉ effective : au moins 20 jours distincts par
    # mois en médiane. Un jeu journalier en a 28 à 31 ; un jeu agrégé au mois en a 1.
    jours_par_mois = d.groupby("mois")["jour"].nunique()
    if float(jours_par_mois.median()) < 20:
        raise SystemExit(
            f"pertes NON atomiques : {jours_par_mois.median():.0f} jour(s) distinct(s) par "
            f"mois en médiane. Le bootstrap apparié exige une ligne par (station, jour) — "
            f"une RMSE agrégée a déjà détruit la covariance que l'appariement exploite.")
    if d.duplicated(["station_id", "jour"]).any():
        n_dup = int(d.duplicated(["station_id", "jour"]).sum())
        raise SystemExit(f"{n_dup:,} lignes en double sur (station, jour) — le "
                         f"rééchantillonnage compterait deux fois les mêmes observations")

    # ── L'écart ponctuel, sur toutes les lignes ────────────────────────────────────────
    def rmse(p):
        return float(np.sqrt(np.mean((d["obs"].to_numpy() - p) ** 2)))

    r_ref, r_cand = rmse(d["pred_reference"].to_numpy()), rmse(d["pred_candidat"].to_numpy())
    gain = 100 * (1 - r_cand / r_ref)
    print(f"{f.name}\n  {len(d):,} lignes · {d['station_id'].nunique()} stations · "
          f"{d['mois'].nunique()} mois", flush=True)
    print(f"  référence {r_ref:7.4f} · candidat {r_cand:7.4f} · "
          f"gain ponctuel {gain:+.2f} %", flush=True)

    d["cl"] = clusters_stations(d, n_clusters)
    mois = np.sort(d["mois"].unique())
    cl = np.sort(d["cl"].unique())
    obs = d["obs"].to_numpy()
    pr, pc = d["pred_reference"].to_numpy(), d["pred_candidat"].to_numpy()

    def tirer(bloc_mois: int) -> tuple[np.ndarray, int]:
        """Bootstrap par blocs de `bloc_mois` mois × grappes géographiques."""
        blocs = [tuple(mois[i:i + bloc_mois]) for i in range(0, len(mois), bloc_mois)]
        m_bloc = {m: k for k, b in enumerate(blocs) for m in b}
        bl = d["mois"].map(m_bloc)
        par_cellule = {(b, c): g.index.to_numpy()
                       for (b, c), g in d.groupby([bl, d["cl"]], sort=False)}
        rng = np.random.default_rng(GRAINE)      # même graine : seuls les blocs changent
        g = np.empty(tirages)
        for k in range(tirages):
            bb = rng.choice(len(blocs), len(blocs), replace=True)
            cc = rng.choice(cl, len(cl), replace=True)
            idx = np.concatenate([par_cellule[(b, c)] for b in bb for c in cc
                                  if (b, c) in par_cellule])
            e_ref = np.sqrt(np.mean((obs[idx] - pr[idx]) ** 2))
            e_can = np.sqrt(np.mean((obs[idx] - pc[idx]) ** 2))
            g[k] = 100 * (1 - e_can / e_ref)
        return g, len(blocs)

    # ── ③ La longueur de bloc n'est plus un choix, c'est une SENSIBILITÉ ────────────
    #
    # 🔴 Le défaut : un mois par bloc était le défaut, et un seul chiffre sortait. Or la
    # longueur de bloc est exactement ce qui décide de la dépendance qu'on reconnaît —
    # publier un intervalle sans montrer sa sensibilité à ce choix revient à publier le
    # choix, pas la mesure.
    #
    # Trois mois est le bloc PRIMAIRE, et l'argument est structurel : le protocole fait
    # tourner les groupes de stations sur les mois consécutifs (`groupes[i % 3]`), donc un
    # bloc de trois mois voit les TROIS groupes. C'est l'unité de réplication naturelle du
    # plan, et elle n'est pas choisie après lecture des scores. Deux et quatre mois
    # encadrent ce choix ; un verdict qui change entre eux n'est pas un verdict.
    primaire = bloc_mois if bloc_mois else 3
    longueurs = sorted({2, primaire, 4})
    lignes, verdicts = [], {}
    from aq.rapport import ecrire_rapport, libelle_echeance  # noqa: PLC0415, F401

    print(f"  {len(cl)} groupes géographiques · longueurs de bloc testées : "
          f"{', '.join(str(x) for x in longueurs)} mois", flush=True)
    for L in longueurs:
        gains, n_blocs = tirer(L)
        bas, haut = np.percentile(gains, [2.5, 97.5])
        part_pos = float((gains > 0).mean())
        verdicts[L] = bas > 0
        marque = "  ← primaire" if L == primaire else ""
        print(f"    blocs de {L} mois ({n_blocs:2d} blocs) : IC95 "
              f"[{bas:+.2f} ; {haut:+.2f}] · {100*part_pos:5.1f} % positifs{marque}",
              flush=True)
        lignes.append({"gain_ponctuel_pct": gain, "ic95_bas": bas, "ic95_haut": haut,
                       "part_tirages_positifs": part_pos, "n_lignes": len(d),
                       "bloc_mois": L, "n_blocs": n_blocs, "primaire": L == primaire,
                       "n_clusters": len(cl), "tirages": tirages,
                       "rmse_reference": r_ref, "rmse_candidat": r_cand})

    stable = len(set(verdicts.values())) == 1
    for ligne in lignes:
        ligne["verdict_stable_sur_les_longueurs"] = stable
    if not stable:
        detail = ", ".join(
            f"{L} mois → {'exclut' if v else 'contient'} zéro"
            for L, v in verdicts.items())
        print("\n  🔴 VERDICT INSTABLE : la conclusion change avec la "
              f"longueur de bloc ({detail}). Un intervalle qui dépend de ce "
              "choix ne tranche rien.", flush=True)
    elif verdicts[primaire]:
        print("\n  → DÉMONTRÉ — la borne basse exclut zéro "
              "aux trois longueurs de bloc", flush=True)
    else:
        print("\n  → NON DÉMONTRÉ — l'intervalle contient zéro "
              "aux trois longueurs", flush=True)

    nom = f.stem.replace("predictions_", "")
    # ⚠️ L'axe était écrit EN DUR à « temporel » dans le contexte, quel que soit le fichier
    # jugé. Une étiquette qui ment est pire qu'une étiquette absente (§ 0-H) : ce script
    # sert aussi bien un double aveugle qu'un axe temporel, et rien ne le distinguait.
    ecrire_rapport(pd.DataFrame(lignes),
                   RACINE / f"reports/bootstrap_{nom}.csv",
                   contexte={"axe": axe},
                   attendues=["gain_ponctuel_pct", "ic95_bas", "ic95_haut",
                              "verdict_stable_sur_les_longueurs"])
    print(f"Écrit : reports/bootstrap_{nom}.csv · {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--predictions", required=True)
    a.add_argument("--tirages", type=int, default=2000)
    a.add_argument("--clusters-stations", type=int, default=20)
    a.add_argument("--bloc-mois", type=int, default=3,
                   help="longueur de bloc PRIMAIRE ; 2 et 4 mois sont toujours "
                        "calculés en sensibilité et le verdict doit tenir aux trois")
    a.add_argument("--axe", default="double", choices=("double", "temporel", "spatial"),
                   help="l'axe RÉELLEMENT jugé — il était écrit en dur")
    n = a.parse_args()
    raise SystemExit(main(n.predictions, n.tirages, n.clusters_stations,
                          n.bloc_mois, n.axe))
