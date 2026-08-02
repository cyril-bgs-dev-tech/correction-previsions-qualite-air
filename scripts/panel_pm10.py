#!/usr/bin/env python3
"""Panel d'observations PM10, au format attendu par `fit_mos.charger`.

Pourquoi un panel séparé
------------------------
Les PM10 n'ont jamais été ingérées : ni dans `panel_metropole_ds2.parquet`, ni dans le flux
EEA que le projet utilise. Elles viennent du **flux national LCSQA** publié sur data.gouv.fr,
ingéré par `scripts/ingerer_lcsqa.py`.

On écrit un fichier **dédié** plutôt que d'ajouter les lignes au panel existant : celui-ci est
un artefact central dont dépendent tous les résultats publiés, et le modifier pour une espèce
nouvelle ferait porter à trois polluants établis le risque d'une ingestion neuve. `fit_mos`
choisit la source selon le polluant.

Ce que le script vérifie plutôt que de le supposer
--------------------------------------------------
* **la correspondance des identifiants** — 327 des 355 stations PM10 du flux LCSQA sont dans
  nos métadonnées, soit 92 %. Les 28 autres sont comptées et nommées, jamais écartées en
  silence : une station qui disparaît d'une jointure ne laisse aucune trace ;
* **l'unicité du couple station × heure** — un doublon doublerait le poids d'une observation
  dans l'apprentissage sans que rien ne le signale ;
* **la couverture temporelle** — mois par mois, contre ce qui a été ingéré.

⚠️ Les lignes conservées sont celles de **validité 1** uniquement, filtre déjà appliqué à
l'ingestion. Le flux porte aussi des codes 4 et −1 dont la signification doit être lue dans la
note explicative du LCSQA avant tout usage — c'est notamment le cas de **tout l'ozone après le
1ᵉʳ juillet 2025**, qui bascule intégralement en code 4.

Usage : python3 scripts/panel_pm10.py
Sortie : data/processed/panel_pm10_lcsqa.parquet
"""

from __future__ import annotations

import glob
import sys
import time
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.ingest.controle import (  # noqa: E402
    ControleEchec,
    exiger_colonnes,
    exiger_lignes,
    exiger_variation,
)


def main() -> int:
    depart = time.time()
    fichiers = sorted(glob.glob(str(RACINE / "data/interim/lcsqa/*.parquet")))
    if not fichiers:
        raise ControleEchec("aucun fichier LCSQA — lancer scripts/ingerer_lcsqa.py d'abord")

    blocs = []
    for f in fichiers:
        t = pd.read_parquet(f, columns=["station_id", "polluant", "timestamp_utc",
                                        "valeur", "validite"])
        blocs.append(t[t["polluant"] == "PM10"])
    t = pd.concat(blocs, ignore_index=True)
    exiger_colonnes(t, ["station_id", "timestamp_utc", "valeur"], "PM10 LCSQA")
    exiger_lignes(t, 1_000_000, "PM10 LCSQA")
    print(f"{len(fichiers)} mois lus · {len(t):,} lignes PM10 · "
          f"{t['station_id'].nunique()} stations", flush=True)

    # ── Correspondance des identifiants, comptée et nommée ────────────────────
    meta = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                           columns=["station_id", "metropole"])
    connues = set(meta[meta["metropole"].fillna(False)]["station_id"])
    presentes = set(t["station_id"])
    inconnues = sorted(presentes - connues)
    if inconnues:
        print(f"  ⚠️ {len(inconnues)} stations PM10 absentes de nos métadonnées, donc "
              f"écartées : {', '.join(inconnues[:8])}"
              + (" …" if len(inconnues) > 8 else ""), flush=True)
    t = t[t["station_id"].isin(connues)]
    part = len(presentes & connues) / max(len(presentes), 1)
    if part < 0.85:
        raise ControleEchec(
            f"seules {part:.0%} des stations PM10 sont connues — un défaut de format "
            "d'identifiant, pas un simple écart de réseau")

    # ── Unicité du couple station × heure ─────────────────────────────────────
    avant = len(t)
    t = t.drop_duplicates(subset=["station_id", "timestamp_utc"], keep="first")
    if avant != len(t):
        print(f"  {avant - len(t):,} doublons station × heure retirés "
              f"({(avant - len(t)) / avant:.3%})", flush=True)

    # ── Valeurs horaires physiquement impossibles ─────────────────────────────
    # Le flux porte des valeurs jusqu'à **3 784 µg/m³ en moyenne horaire**, dont cinq des
    # six plus fortes sur une **seule station urbaine de fond** (FR23110), toutes à l'aube
    # sur une semaine de mai 2026. Cette station a une médiane de 11,8 et un p99,9 de
    # 125 µg/m³ : 3 784 en vaut **trente fois** le p99,9. Ce n'est pas un épisode, c'est un
    # instrument.
    #
    # L'enjeu n'est pas cosmétique. La cible réglementaire des PM10 est la **moyenne
    # journalière** : une seule heure à 3 784 relève la moyenne du jour de 155 µg/m³ et
    # fabrique un faux dépassement du seuil de 50.
    #
    # Le plafond est fixé à **500 µg/m³**, choisi sur la distribution du réseau et non par
    # intuition : le p99,99 toutes stations vaut **228 µg/m³**, et les épisodes sahariens
    # réels en France culminent vers 300 à 400. Cinq cents garde donc les épisodes vrais et
    # écarte l'impossible. Le compte est affiché, jamais tu.
    PLAFOND_HORAIRE = 500.0
    aberrantes = t["valeur"] > PLAFOND_HORAIRE
    if aberrantes.any():
        pires = (t[aberrantes].groupby("station_id")["valeur"]
                 .agg(n="size", maxi="max").nlargest(3, "maxi"))
        print(f"  {aberrantes.sum()} heures au-dessus de {PLAFOND_HORAIRE:.0f} µg/m³ "
              f"écartées ({aberrantes.mean():.5%}), sur "
              f"{t.loc[aberrantes, 'station_id'].nunique()} stations", flush=True)
        for st_id, r in pires.iterrows():
            print(f"    {st_id} · {int(r['n'])} heures · max {r['maxi']:.0f} µg/m³",
                  flush=True)
    if aberrantes.mean() > 0.001:
        raise ControleEchec(
            f"{aberrantes.mean():.3%} des heures au-dessus de {PLAFOND_HORAIRE:.0f} — "
            "au-delà de l'artefact ponctuel, il faudrait comprendre la cause avant "
            "d'écrêter")
    t = t[~aberrantes]

    # ── Format attendu par le reste de la chaîne ──────────────────────────────
    t = t.assign(polluant="PM10", flag_qualite="valide", n_points=1)[
        ["station_id", "polluant", "timestamp_utc", "valeur", "flag_qualite", "n_points"]]
    t = t.dropna(subset=["valeur"]).sort_values(["station_id", "timestamp_utc"])
    exiger_variation(t, ["valeur"], "PM10")
    exiger_lignes(t, 1_000_000, "PM10 final")

    couverture = (t.assign(mois=pd.PeriodIndex(t["timestamp_utc"], freq="M"))
                   .groupby("mois").agg(n=("valeur", "size"),
                                        stations=("station_id", "nunique")))
    print(f"\n{len(t):,} lignes retenues · {t['station_id'].nunique()} stations · "
          f"{couverture.index.min()} → {couverture.index.max()}")
    creux = couverture[couverture["stations"] < 0.6 * couverture["stations"].max()]
    if len(creux):
        print(f"  ⚠️ {len(creux)} mois à moins de 60 % des stations : "
              f"{', '.join(str(m) for m in creux.index[:6])}", flush=True)
    print(f"  médiane {t['valeur'].median():.1f} µg/m³ · "
          f"p99 {t['valeur'].quantile(0.99):.1f} · max {t['valeur'].max():.1f}")

    # Règle 4 : nom provisoire, vérification, puis renommage.
    final = RACINE / "data/processed/panel_pm10_lcsqa.parquet"
    prov = final.with_suffix(".parquet.partiel")
    t.to_parquet(prov, index=False)
    relu = pd.read_parquet(prov, columns=["station_id", "valeur"])
    exiger_lignes(relu, len(t), "panel relu")
    prov.replace(final)
    print(f"\nÉcrit : {final.relative_to(RACINE)} · "
          f"{final.stat().st_size / 1e6:.0f} Mo · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
