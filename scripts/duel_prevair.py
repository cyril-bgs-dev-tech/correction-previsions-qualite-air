#!/usr/bin/env python3
"""PREV'AIR contre notre correction, sur les mêmes stations et les mêmes jours.

⚠️ CE QUE CE SCRIPT NE PEUT PAS FAIRE
=======================================
**Quatre jours ne concluent rien.** La fenêtre publique de PREV'AIR ne conserve qu'une
semaine ; l'intersection avec nos observations et nos prévisions CAMS tombe à quelques
journées. Un écart mesuré là-dessus n'a aucune valeur statistique, et le script le répète
à chaque sortie.

Ce qu'il fait, c'est **poser la comparaison** et la faire tourner. Le jour où l'archive
historique arrive — demandée à l'INERIS puis à Atmo Occitanie le 03/08 — il suffit de la
relancer.

La comparaison est-elle seulement équitable ?
-----------------------------------------------
Non, et dans les deux sens. Il faut le dire avant les chiffres.

**En notre défaveur :**
* PREV'AIR tourne à **≈ 1,7 km** ; nous corrigeons un ensemble européen à **10 km** ;
* PREV'AIR **assimile** les observations et applique déjà un **krigeage** ;
* PREV'AIR fait tourner CHIMERE **et** MOCAGE en configuration **nationale**, avec
  l'inventaire d'émissions français.

**En notre faveur :**
* notre modèle a **appris sur ces stations** (il est entraîné sur 2023-2024, testé ici en
  2026 — extrapolation temporelle, mais stations connues) ;
* PREV'AIR est jugé sur un produit livré au public, nous sur un calcul de laboratoire.

Autrement dit : c'est une comparaison de **chaînes d'ampleur différente**, pas de méthodes.
Le seul énoncé défendable est un ordre de grandeur.

Le grain, vérifié et non déduit
---------------------------------
PREV'AIR publie **deux** familles : `MAXJ*` (maximum journalier) et `MOYJ*` (moyenne
journalière). Le 03/08, le test des quatre appariements possibles a donné :

    MAXJ1 contre maximum     RMSE 35,95   corr 0,117
    MAXJ1 contre moyenne     RMSE 17,57   corr 0,192
    MOYJ1 contre moyenne     RMSE  7,51   corr 0,405   ← sans comparaison

Chaque polluant est donc comparé au produit de **son grain réglementaire** : `MOYJ` pour les
particules — seuil de 50 µg/m³ en moyenne journalière — et `MAXJ` pour O₃ et NO₂.

Usage : python3 scripts/duel_prevair.py --polluant PM10
Sortie : reports/duel_prevair_<polluant>.csv
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

from comparer_prevair import AGREGAT, PRODUIT, extraire  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)

# L'apprentissage s'arrête bien avant les jours testés : aucune fuite possible.
FIN_APPRENTISSAGE = "2024-12"

# **Le grain se lit dans le produit comparé, jamais dans notre convention.**
#
# Notre cible ozone est le **maximum glissant 8 h**, celle du seuil européen. Le produit
# `MAXJ` de PREV'AIR est le **maximum journalier horaire** — le rapport *Performances
# Prev'air en 2024* (INERIS/LCSQA, p. 17) le dit explicitement : « seul le maximum
# journalier d'ozone est ainsi considéré ». Laisser les deux se rencontrer jugeait les
# trois systèmes sur **trois grandeurs différentes**, et le défaut ne plantait pas : il
# sortait un biais PREV'AIR de **+1,36** quand tous les autres étaient négatifs, simple
# effet d'échelle du max horaire contre un max 8 h. Le 07/08/2026, cela donnait
# « PREV'AIR meilleur de 2,6 % » — un artefact de convention, pas une mesure.
#
# On aligne donc **tout le duel** sur le grain du produit comparé : l'observation,
# l'agrégat CAMS et notre modèle, qui est réajusté sur cette cible-là dans `main`. Les
# trois autres polluants concordaient déjà (NO₂ max horaire ↔ `MAXJ`, particules moyenne
# journalière ↔ `MOYJ`) et ne changent pas.
GRAIN_DU_DUEL = {**GRANDEUR_PAR_POLLUANT, "O3": "max_horaire"}


def scores(o, x) -> dict:
    e = x - o
    return {"n": len(o), "biais": float(e.mean()),
            "rmse": float(np.sqrt((e ** 2).mean())),
            "mae": float(np.abs(e).mean()),
            "correlation": float(np.corrcoef(o, x)[0, 1]) if o.std() and x.std() else np.nan}


def main(polluant: str, horizon: int, produit: str = "prevision") -> int:
    depart = time.time()
    agr, prod = AGREGAT[polluant], PRODUIT[polluant]
    ech = f"{prod}{horizon - 1}"

    # ── ① PREV'AIR aux stations ──────────────────────────────────────────────
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "lat_wgs84", "lon_wgs84"]
                         ).dropna().drop_duplicates("station_id").reset_index(drop=True)
    # ── PRÉVISION ou ANALYSE : ce ne sont PAS le même produit, et tout en dépend ────────
    #
    # 🔴 Mesuré le 16/08/2026. Leur rapport annuel annonce AS-CHI à **4,7** sur PM10 et
    # **3,05** sur PM2,5 ; ce duel mesurait leur produit à 8,23 et 4,54 — presque le double.
    # L'explication n'est pas une fenêtre défavorable : c'est que ce script lit
    # `PREVAIR.prevision.*` (échéance J+1) alors que leurs chiffres publiés portent sur
    # `PREVAIR.analyse.*` — le champ **assimilé du jour même**, qui a vu les observations
    # qu'on lui oppose.
    #
    # Les deux comparaisons sont légitimes et ne répondent pas à la même question :
    #   · `prevision` — leur J+1 contre notre J+1. **La seule comparaison à armes égales**,
    #      et la seule qui dise ce qu'un prévisionniste reçoit la veille.
    #   · `analyse`   — leur meilleur champ disponible, hors compétition par construction :
    #      aucun système sans assimilation ne peut l'égaler. C'est un PLAFOND, pas un
    #      adversaire.
    marque = "ANALYSE" if produit == "analyse" else "PREVISION"
    # L'analyse n'a pas d'échéance : `MAXJ` nu, sans le chiffre de la prévision.
    ech_f = ech if produit == "prevision" else ech.rstrip("0123456789")
    fichiers = [Path(f) for f in glob.glob(str(RACINE / "data/raw/prevair/*.nc"))
                if f".{ech_f}.{polluant}." in f.upper() and marque in f.upper()]
    if not fichiers:
        raise SystemExit(f"aucun fichier {marque} {ech_f}.{polluant} — "
                         f"lancer archiver_prevair.py")
    pv = pd.concat([extraire(f, st) for f in fichiers], ignore_index=True)
    print(f"{polluant} · {ech} · {len(fichiers)} jours PREV'AIR · "
          f"{len(pv):,} valeurs extraites", flush=True)

    # ── ② Notre correction, entraînée AVANT les jours testés ─────────────────
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    grain = GRAIN_DU_DUEL[polluant]
    if grain != GRANDEUR_PAR_POLLUANT[polluant]:
        print(f"  ⚠️ grain aligné sur le produit PREV'AIR : {grain} "
              f"(notre cible habituelle est {GRANDEUR_PAR_POLLUANT[polluant]})", flush=True)
    j = agreger_journalier(jeu, cols, grain)
    pred_cols = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    # ── L'étage `tendance`, et pourquoi c'est le SEUL des quatre qu'on puisse ajouter ici
    #
    # Le duel tournait sur la configuration `base` : ni GEOS-CF, ni membres d'ensemble, ni
    # feux, ni tendance. Sur l'ozone c'est +7,01 % au lieu de +15,83 % — les écarts publiés
    # étaient donc un MINORANT de notre système, ce qui est exact mais sous-déclaré.
    #
    # Mesuré le 11/08, les trois autres familles sont hors d'atteinte SUR CETTE FENÊTRE, et
    # c'est une limite de fraîcheur des flux, pas un choix :
    #   · feux    — dernier fichier 2025-06, quatorze mois de retard ;
    #   · membres — s'arrête au 2026-08-01, soit 5 jours sur les 10 testés ;
    #   · geoscf  — s'arrête au 2026-08-01, ET le dernier flux est en v2 : mélanger v1 et v2
    #               est interdit (VERITE_DOSSIER § 13).
    # Les faire entrer amputerait la moitié de la fenêtre ou la totalité. `tendance`, elle,
    # ne lit AUCUNE donnée extérieure : elle se dérive de CAMS, donc elle existe partout où
    # CAMS existe.
    #
    # ⚠️ Calculée AVANT toute restriction de fenêtre : elle décale la série d'un jour par
    # station, et la calculer après le filtrage ferait venir la veille du premier jour
    # retenu depuis le dernier jour d'une autre période.
    from banc_preprocessing import f_tendance_cams  # noqa: PLC0415
    tendance = f_tendance_cams(d)
    if collision := [c for c in tendance.columns if c in d.columns]:
        raise SystemExit(f"colonnes de tendance déjà présentes : {collision}")
    d = pd.concat([d, tendance], axis=1)
    pred_cols += list(tendance.columns)

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    pred_cols += cols_typo
    # ── Les familles externes : MESURÉES, jamais affirmées ──────────────────────────────
    #
    # ⚠️ Ce bloc imprimait « feux/membres/geoscf HORS ATTEINTE sur cette fenêtre » — une
    # chaîne CONSTANTE. Elle disait vrai le jour où elle a été écrite, et elle aurait
    # continué à le dire après un rafraîchissement des flux, en écartant en silence des
    # familles redevenues disponibles. Un contrôle qui ne peut pas changer d'avis n'est pas
    # un contrôle (§ 0, règle D : nommer ce qu'on mesure, mesurer ce qu'on nomme).
    #
    # Le critère est la couverture **de la fenêtre de test**, pas l'existence du fichier :
    # une famille présente sur l'apprentissage mais absente des jours testés est pire
    # qu'absente — elle entraîne le modèle sur un signal qu'il n'aura pas au moment de
    # prédire.
    jours_test = set(pd.to_datetime(list(pv["jour"].unique())))

    def tenter(nom: str, fn) -> list[str]:
        nonlocal d
        try:
            d2, cols = fn(d)
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ {nom} — {type(exc).__name__}: {exc}", flush=True)
            return []
        if not cols:
            print(f"    ✗ {nom} — flux absent (aucune colonne)", flush=True)
            return []
        vus = d2["jour"].isin(jours_test)
        couv = float(d2.loc[vus, cols].notna().any(axis=1).mean()) if vus.any() else 0.0
        if couv < 0.5:
            print(f"    ✗ {nom} — {len(cols)} colonnes mais {couv:.0%} de la fenêtre de "
                  f"test couverte : écartée", flush=True)
            return []
        d = d2
        print(f"    ✓ {nom} — {len(cols)} colonnes · {couv:.0%} de la fenêtre de test",
              flush=True)
        return cols

    print("  familles externes :", flush=True)
    from leviers_36mois import joindre_feux, joindre_membres  # noqa: PLC0415
    bornes = (d["mois"].min(), d["mois"].max())
    pred_cols += tenter("membres", lambda x: joindre_membres(x, polluant, *bornes))
    pred_cols += tenter("feux", lambda x: joindre_feux(x, *bornes))

    # ⚠️ La spéciation n'était pas dans cette liste, et pour une raison qui n'est plus vraie :
    # elle n'existait pas quand ce bloc a été écrit, le 11/08. Elle couvre 2024-01 → 2026-08,
    # donc toute la fenêtre du duel. C'est le seul étage de la pile publiée qui puisse y
    # entrer — et le garde `tenter` mesure sa couverture au lieu de la supposer.
    #
    # 🔴 On écarte le NITRATE : il n'existe qu'à partir de 2024-12, et une colonne absente
    # sur une partie du corpus d'apprentissage code l'époque au lieu du phénomène
    # (voir `methode_maximale.py --support-complet`).
    def _speciation(x):
        from ablation_speciation import charger_speciation  # noqa: PLC0415
        from leviers_36mois import _fusion  # noqa: PLC0415
        spe = charger_speciation()
        cols = [c for c in spe.columns if c.startswith("spe_") and "no3" not in c]
        return _fusion(x, spe[["station_id", "jour"] + cols], "speciation"), cols

    pred_cols += tenter("spéciation", _speciation)

    print(f"  familles retenues : base · tendance({len(tendance.columns)}) · "
          f"typologie({len(cols_typo)}) · {len(pred_cols)} prédicteurs au total",
          flush=True)

    jours_pv = set(pv["jour"].unique())
    test = d[d["jour"].isin(jours_pv)]
    if test.empty:
        raise SystemExit(f"aucun jour commun entre PREV'AIR ({sorted(jours_pv)[:3]}…) "
                         f"et nos prévisions CAMS — étendre l'extraction CAMS")

    # ── La borne d'apprentissage se DÉRIVE de la fenêtre de test (règle A de CLAUDE.md).
    #
    # Elle valait `FIN_APPRENTISSAGE = "2024-12"`, écrit en dur pour empêcher toute fuite.
    # L'intention était juste, la valeur périmée : la fenêtre testée est de **juillet-août
    # 2026**, et s'arrêter à décembre 2024 jetait **dix-huit mois** d'apprentissage
    # disponible. Une constante anti-fuite ne protège que la date à laquelle on l'a écrite ;
    # dérivée, elle protège toujours et ne coûte rien.
    #
    # On coupe au mois PRÉCÉDANT le premier jour testé — jamais au mois du test, qui
    # contiendrait les jours eux-mêmes.
    # ⚠️ **La fenêtre de test doit être CONTIGUË, et ce n'est pas gratuit.** L'archive
    # d'analyse porte deux dates isolées d'avril 2025, seize mois avant le bloc courant.
    # Les inclure faisait remonter la borne à mars 2025 et jetait seize mois
    # d'apprentissage — pour deux journées. On ne garde donc que le bloc **récent**, défini
    # par un écart maximal au dernier jour testé, et on DIT combien de jours ont été
    # écartés (§ 2 quater : afficher le périmètre effectif, pas le périmètre demandé).
    ECART_MAX = pd.Timedelta(days=90)
    dernier = max(pd.Timestamp(x) for x in jours_pv)
    recents = {x for x in jours_pv if dernier - pd.Timestamp(x) <= ECART_MAX}
    if len(recents) < len(jours_pv):
        ecartes = sorted(pd.Timestamp(x).date() for x in jours_pv - recents)
        print(f"  ⚠️ {len(ecartes)} jour(s) isolé(s) écarté(s) du test — hors du bloc des "
              f"{ECART_MAX.days} derniers jours : {', '.join(map(str, ecartes[:4]))}",
              flush=True)
        jours_pv = recents
        test = d[d["jour"].isin(jours_pv)]

    premier_test = min(pd.Timestamp(x) for x in jours_pv)
    appr = d[d["mois"] < premier_test.strftime("%Y-%m")]
    if appr.empty:
        raise SystemExit(f"aucun apprentissage avant {premier_test:%Y-%m} — "
                         f"la fenêtre de test précède nos données")
    if appr["mois"].max() >= premier_test.strftime("%Y-%m"):
        raise SystemExit("fuite : l'apprentissage atteint le mois testé")
    print(f"  apprentissage : {len(appr):,} jours-station jusqu'à {appr['mois'].max()} "
          f"(dérivé ; borne figée précédente : {FIN_APPRENTISSAGE})\n"
          f"  test          : {len(test):,} jours-station sur "
          f"{test['jour'].nunique()} jour(s) communs à partir du {premier_test}",
          flush=True)
    p = ajuster(DEFAUT, appr, test, pred_cols, "cams_jour")
    nous = test[["station_id", "jour", "valeur", "cams_jour"]].copy()
    nous["nous"] = p

    # ── ③ Les trois systèmes sur EXACTEMENT les mêmes lignes ─────────────────
    m = nous.merge(pv[["station_id", "jour", "prevair"]], on=["station_id", "jour"],
                   how="inner").dropna()
    if len(m) < 100:
        print(f"  ⚠️ {len(m)} lignes communes — trop peu même pour un ordre de grandeur.")
        return 1
    o = m["valeur"].to_numpy()
    print(f"\n{'═' * 76}\n{polluant} · {ech} · grain {grain} · {len(m):,} lignes communes · "
          f"{m['jour'].nunique()} jour(s) du {str(m['jour'].min())[:10]} au "
          f"{str(m['jour'].max())[:10]} · {m['station_id'].nunique()} stations\n"
          f"⚠️ {m['jour'].nunique()} jour(s) NE CONCLUENT RIEN — ordre de grandeur seul\n"
          f"{'═' * 76}")
    print(f"  {'système':34s} {'biais':>8s} {'RMSE':>8s} {'MAE':>8s} {'corr':>7s}")
    lignes = []
    for nom, col in (("CAMS Europe brut (10 km)", "cams_jour"),
                     ("notre correction de CAMS", "nous"),
                     ("PREV'AIR (1,7 km, assimilé, krigé)", "prevair")):
        s = scores(o, m[col].to_numpy())
        print(f"  {nom:34s} {s['biais']:+8.2f} {s['rmse']:8.2f} {s['mae']:8.2f} "
              f"{s['correlation']:7.3f}")
        lignes.append({"polluant": polluant, "echeance": ech, "grain": grain,
                       "jours": int(m["jour"].nunique()),
                       "debut": str(m["jour"].min())[:10], "fin": str(m["jour"].max())[:10],
                       "systeme": nom, **s})

    r_nous = scores(o, m["nous"].to_numpy())["rmse"]
    r_pv = scores(o, m["prevair"].to_numpy())["rmse"]
    ecart = 100 * (r_pv / r_nous - 1)
    print(f"\n  Écart PREV'AIR contre nous : {ecart:+.1f} % de RMSE "
          f"({'à notre avantage' if ecart > 0 else 'à leur avantage'})")
    print(f"\n  ⚠️ Rappel : ils tournent à 1,7 km avec assimilation et krigeage ; nous")
    print(f"     corrigeons un ensemble européen à 10 km. Nos stations sont connues de")
    print(f"     notre modèle, les leurs le sont aussi de leur krigeage. Ordre de")
    print(f"     grandeur, sur {m['jour'].nunique()} jour(s).")

    # Fichiers DISTINCTS : écrire l'analyse sous le nom de la prévision ferait
    # citer un plafond pour une comparaison à armes égales.
    suf = "" if produit == "prevision" else f"_{produit}"
    sortie = RACINE / f"reports/duel_prevair_{polluant}{suf}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--horizon", type=int, default=2, help="2 = J+1")
    a.add_argument("--produit", default="prevision",
                   choices=("prevision", "analyse"),
                   help="prevision : leur J+1, à armes égales (défaut) · "
                        "analyse : leur champ assimilé, un PLAFOND")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.produit))
