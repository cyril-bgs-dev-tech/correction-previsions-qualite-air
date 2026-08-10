#!/usr/bin/env python3
"""Le panel unifié — EEA jusqu'à fin 2023, LCSQA ensuite, sur stations constantes.

Ce que ce script débloque
-------------------------
Le corpus apparié du projet fait **18 mois**, borné non par les prévisions mais par les
**observations EEA**, qui s'arrêtent en décembre 2024. Le flux LCSQA couvre 2024-01 → 2026-07.
Les recoller porte le corpus à **36 mois** et les plis temporels de 17 à **29** — ce dont le
double aveugle a précisément besoin, l'ozone y rendant +3,3 % avec 7 plis négatifs sur 17.

Pourquoi le raccord est légitime — mesuré, pas supposé
-------------------------------------------------------
`scripts/concordance_eea_lcsqa.py`, sur les **treize mois de recouvrement** 2024-01 → 2025-01 :

=========  =================  ===================  =====================  ==============
polluant   convention 0 h     écart absolu médian  couples identiques     stabilité
=========  =================  ===================  =====================  ==============
O₃         gagne **2 468×**   **0,0000 µg/m³**     **100,0 %**            amplitude 0,0000
NO₂        gagne **18 703×**  **0,0000**           **100,0 %**            amplitude 0,0000
PM2,5      gagne 206×         **0,0000**           99,7 %                 amplitude 0,0000
=========  =================  ===================  =====================  ==============

Ce ne sont pas deux sources qui concordent : **c'est la même donnée**. L'EEA reçoit les
mesures françaises par le rapportage E2, celui-là même que le LCSQA publie.

⚠️ La seule vraie différence, et le remède
--------------------------------------------
Les **populations de stations diffèrent** : le LCSQA en publie davantage. Selon le polluant,
6 à 24 stations sont présentes dans EEA seulement, et 32 à 50 dans LCSQA seulement.

Un corpus dont l'ensemble de stations change au milieu déplacerait le score **sans que rien
ne le signale** — et le double aveugle lirait ce déplacement comme une non-stationnarité de
l'atmosphère, donc l'attribuerait à la mauvaise cause. C'est exactement l'erreur commise le
02/08/2026 sur l'étalon ozone : une marche mesurée, attribuée au mauvais mécanisme, et
démolie par un témoin.

**Remède** : ne garder que les stations **communes aux deux sources**, sur toute la fenêtre.
La population devient constante **par construction** plutôt que par chance. Coût : 6 à 24
stations selon le polluant.

Ce n'est pas un relâchement du critère de contrôle — c'est en satisfaire l'intention par un
autre moyen. Les valeurs, elles, sont identiques à la sixième décimale : il n'y a aucun
désaccord à masquer.

Ce que le script vérifie plutôt que de le supposer
---------------------------------------------------
1. **Aucun doublon station × heure.** Un doublon doublerait le poids d'une observation dans
   l'apprentissage, en silence.
2. **Aucun trou à la jointure.** Décembre 2023 et janvier 2024 doivent tous deux être peuplés :
   un creux au raccord serait lu comme un événement.
3. **Population de stations constante**, vérifiée mois par mois et non seulement en moyenne.
4. **Couverture mensuelle** affichée, avec les mois creux nommés.

Usage : python3 scripts/panel_unifie.py
Sortie : data/processed/panel_unifie_lcsqa.parquet
"""

from __future__ import annotations

import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.harmonize.timegrid import en_mois  # noqa: E402
from aq.ingest.controle import ControleEchec, exiger_lignes, exiger_variation  # noqa: E402

POLLUANTS = ("O3", "NO2", "PM25", "PM10")
# Bascule : avant, on prend l'EEA ; à partir de là, le LCSQA. Le LCSQA commence en 2024-01
# et les deux sont identiques sur le recouvrement — la bascule est donc placée au premier
# mois où le LCSQA existe, pour ne jamais mélanger deux sources dans un même mois.
BASCULE = pd.Timestamp("2024-01-01", tz="UTC")
# Borne basse du panel. Le panel EEA remonte à 2013, mais les prévisions CAMS commencent en
# 2023-08 : tout ce qui précède serait joint puis jeté. Sans cette borne, le premier essai a
# produit **28 millions de lignes pour le seul ozone**, sur 164 mois dont 146 inutilisables.
# Deux mois de marge avant le début des prévisions suffisent aux variables retardées.
DEBUT = pd.Timestamp("2023-06-01", tz="UTC")
# Plafond horaire des particules, hérité de `panel_pm10.py` : choisi sur le p99,99 du réseau
# (228 µg/m³) et non par intuition. Une seule heure à 3 784 relève la moyenne journalière de
# 155 µg/m³ et fabrique un faux dépassement du seuil de 50.
PLAFOND = {"PM10": 500.0, "PM25": 500.0}
# Nombre de couples station × heure contradictoires tolérés avant refus. Au-delà, ce n'est
# plus un artefact de publication mais un problème de fond, et l'écarter le masquerait.
TOLERANCE_CONTRADICTIONS = 100


def lcsqa(polluant: str) -> pd.DataFrame:
    morceaux = []
    for f in sorted(glob.glob(str(RACINE / "data/interim/lcsqa/lcsqa_*.parquet"))):
        t = pd.read_parquet(f, columns=["station_id", "polluant", "timestamp_utc",
                                        "valeur"])
        t = t[t["polluant"] == polluant]
        if not t.empty:
            morceaux.append(t)
    if not morceaux:
        raise SystemExit(f"aucune ligne LCSQA pour {polluant}")
    return pd.concat(morceaux, ignore_index=True)


def eea(polluant: str) -> pd.DataFrame:
    t = pd.read_parquet(RACINE / "data/processed/panel_metropole_ds2.parquet",
                        columns=["station_id", "polluant", "timestamp_utc", "valeur"])
    return t[t["polluant"] == polluant]


def main() -> int:
    depart = time.time()
    blocs, resume = [], []

    for polluant in POLLUANTS:
        print(f"\n{'═' * 74}\n{polluant}\n{'═' * 74}", flush=True)
        lc = lcsqa(polluant)
        ee = eea(polluant)
        print(f"  LCSQA {len(lc):,} lignes · {lc['station_id'].nunique()} stations", flush=True)
        print(f"  EEA   {len(ee):,} lignes · {ee['station_id'].nunique()} stations", flush=True)

        if ee.empty:
            # Cas des PM10 : jamais ingérées côté EEA. Le panel commence donc au LCSQA,
            # et la population de référence est celle du LCSQA seul — il n'y a pas de
            # raccord, donc pas de risque de changement de population.
            communes = set(lc["station_id"].unique())
            print(f"  aucune donnée EEA — pas de raccord, {len(communes)} stations LCSQA")
            t = lc[lc["timestamp_utc"] >= max(BASCULE, DEBUT)]
        else:
            communes = set(lc["station_id"]) & set(ee["station_id"])
            perdues_eea = len(set(ee["station_id"]) - communes)
            perdues_lc = len(set(lc["station_id"]) - communes)
            print(f"  {len(communes)} stations communes · {perdues_eea} EEA seule écartées "
                  f"· {perdues_lc} LCSQA seule écartées", flush=True)
            if len(communes) < 100:
                raise ControleEchec(
                    f"{polluant} : seulement {len(communes)} stations communes — la "
                    f"correspondance des identifiants a probablement changé")
            avant = ee[(ee["timestamp_utc"] >= DEBUT)
                       & (ee["timestamp_utc"] < BASCULE)
                       & ee["station_id"].isin(communes)]
            apres = lc[(lc["timestamp_utc"] >= BASCULE)
                       & lc["station_id"].isin(communes)]
            print(f"  EEA avant bascule : {len(avant):,} · "
                  f"LCSQA après : {len(apres):,}", flush=True)
            t = pd.concat([avant, apres], ignore_index=True)

        # ── ① Doublons station × heure : distinguer l'identique du contradictoire ──
        #
        # Trouvé le 02/08/2026 : **1 728 lignes en doublon sur NO₂**, concentrées sur
        # **2 stations**, et **0 couple sur 864 portant des valeurs différentes**.
        #
        # Cause : le flux LCSQA publie une colonne `discriminant` — une station peut porter
        # **deux points de prélèvement** pour le même polluant, deux analyseurs distincts —
        # et `ingerer_lcsqa.py` ne la conserve pas. Les deux points tombent alors sous la
        # même clé.
        #
        # Les deux cas n'ont pas la même gravité et ne doivent pas recevoir le même
        # traitement : un doublon **identique** est une redondance de publication, sans
        # information perdue à le retirer ; un doublon **contradictoire** est un choix
        # arbitraire entre deux mesures, et il doit lever. Écraser les deux d'un même
        # `drop_duplicates` masquerait le second.
        cle = ["station_id", "timestamp_utc"]
        avant_dedup = len(t)
        t = t.drop_duplicates(subset=cle + ["valeur"])
        identiques = avant_dedup - len(t)
        if identiques:
            print(f"  {identiques:,} doublon(s) EXACT(s) retiré(s) — même station, même "
                  f"heure, même valeur", flush=True)
        contradictoires = int(t.duplicated(subset=cle).sum())
        if contradictoires:
            ex = t[t.duplicated(subset=cle, keep=False)].sort_values(cle)
            # Trouvé le 02/08/2026 sur PM2,5 : **3 couples** sur la station FR18058, valeurs
            # 14,2 contre 15,4 et 18,1 contre 17,6 µg/m³. Deux points de prélèvement qui ne
            # mesurent pas la même chose — rien ne dit lequel a raison.
            #
            # On **écarte les deux lignes** plutôt que d'en choisir une : moyenner
            # inventerait une valeur, garder la première serait arbitraire. Mais avec un
            # **seuil**, sans quoi cette règle masquerait un jour un désaccord massif au
            # lieu de le signaler.
            if contradictoires > TOLERANCE_CONTRADICTIONS:
                raise ControleEchec(
                    f"{polluant} : {contradictoires:,} doublons station × heure avec des "
                    f"valeurs DIFFÉRENTES,\nau-delà des {TOLERANCE_CONTRADICTIONS} tolérés. "
                    f"Ce n'est plus un artefact ponctuel : comprendre\nla cause avant "
                    f"d'écarter quoi que ce soit.\n\n{ex.head(6).to_string(index=False)}")
            print(f"  ⚠️ {contradictoires} couple(s) CONTRADICTOIRE(s) écarté(s) — "
                  f"{ex['station_id'].nunique()} station(s), valeurs divergentes entre "
                  f"points de prélèvement :", flush=True)
            print("     " + ex.head(4).to_string(index=False).replace("\n", "\n     "),
                  flush=True)
            t = t[~t.duplicated(subset=cle, keep=False)]

        # ── Écrêtage des particules, comme dans panel_pm10 ─────────────────────
        if polluant in PLAFOND:
            ab = t["valeur"] > PLAFOND[polluant]
            if ab.any():
                print(f"  {int(ab.sum()):,} heures au-dessus de {PLAFOND[polluant]:.0f} "
                      f"µg/m³ écartées ({ab.mean():.5%})", flush=True)
            if ab.mean() > 0.001:
                raise ControleEchec(
                    f"{polluant} : {ab.mean():.3%} au-dessus du plafond — au-delà de "
                    f"l'artefact ponctuel, comprendre la cause avant d'écrêter")
            t = t[~ab]

        t = t.dropna(subset=["valeur"])
        cv = (t.assign(mois=en_mois(t["timestamp_utc"]))
               .groupby("mois").agg(n=("valeur", "size"),
                                    stations=("station_id", "nunique")))

        # ── ② Aucun trou à la jointure ─────────────────────────────────────────
        if not ee.empty:
            for bord in (pd.Period("2023-12", "M"), pd.Period("2024-01", "M")):
                if bord not in cv.index or cv.loc[bord, "stations"] < 50:
                    raise ControleEchec(
                        f"{polluant} : {bord} vide ou quasi vide au raccord. Un creux à la "
                        f"jointure serait lu comme un événement atmosphérique.")
            print(f"  jointure · 2023-12 : {int(cv.loc[pd.Period('2023-12','M'),'stations'])} "
                  f"stations → 2024-01 : "
                  f"{int(cv.loc[pd.Period('2024-01','M'),'stations'])} stations ✓")

        # ── ③ Population constante, vérifiée mois par mois ─────────────────────
        amplitude = int(cv["stations"].max() - cv["stations"].min())
        part = amplitude / max(int(cv["stations"].max()), 1)
        print(f"  population · {int(cv['stations'].min())} à "
              f"{int(cv['stations'].max())} stations selon le mois "
              f"(amplitude {part:.0%})"
              f"{' ✓' if part < 0.25 else '  ⚠️ variable'}")

        creux = cv[cv["stations"] < 0.6 * cv["stations"].max()]
        if len(creux):
            print(f"  ⚠️ {len(creux)} mois sous 60 % des stations : "
                  f"{', '.join(str(m) for m in creux.index[:6])}")

        print(f"  → {len(t):,} lignes · {t['station_id'].nunique()} stations · "
              f"{cv.index.min()} → {cv.index.max()} ({len(cv)} mois)")
        blocs.append(t)
        resume.append({"polluant": polluant, "lignes": len(t),
                       "stations": t["station_id"].nunique(), "mois": len(cv),
                       "debut": str(cv.index.min()), "fin": str(cv.index.max())})

    panel = pd.concat(blocs, ignore_index=True)
    panel = panel.assign(flag_qualite="valide", n_points=1)[
        ["station_id", "polluant", "timestamp_utc", "valeur", "flag_qualite", "n_points"]]
    panel = panel.sort_values(["polluant", "station_id", "timestamp_utc"])
    exiger_variation(panel, ["valeur"], "panel unifié")
    exiger_lignes(panel, 5_000_000, "panel unifié")

    # Règle 4 : nom provisoire, relecture, puis renommage.
    final = RACINE / "data/processed/panel_unifie_lcsqa.parquet"
    prov = final.with_suffix(".parquet.partiel")
    panel.to_parquet(prov, index=False)
    relu = pd.read_parquet(prov, columns=["station_id", "valeur"])
    exiger_lignes(relu, len(panel), "panel relu")
    prov.replace(final)

    print(f"\n{'═' * 74}")
    print(pd.DataFrame(resume).to_string(index=False))
    print(f"\nÉcrit : {final.relative_to(RACINE)} · "
          f"{final.stat().st_size / 1e6:.0f} Mo · {len(panel):,} lignes · "
          f"{(time.time() - depart) / 60:.0f} min")
    print("\n⚠️ Pour que ce panel serve, `fit_mos.PANEL_PAR_POLLUANT` doit y router les "
          "quatre\n   polluants. Tant que ce n'est pas fait, il existe sans être utilisé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
