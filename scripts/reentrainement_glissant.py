#!/usr/bin/env python3
"""À armes égales : notre correction réentraînée en continu, comme le produit officiel.

L'asymétrie que ce script corrige
----------------------------------
Le MOS officiel de Copernicus est **réentraîné en continu** sur une fenêtre glissante récente
et utilise les observations jusqu'à la veille. Notre modèle, sur les calendriers 2025, est
**figé au 31/12/2024** : il prédit six mois sans jamais voir une observation de 2025.

Sur le calendrier O₃ 2025 en Occitanie, le produit officiel annonce **109 jours-station** contre
**68** pour nous — l'inverse de 2024, où nous en annoncions 703 contre 237. La comparaison
n'était pas à armes égales, et l'écart n'était donc pas interprétable.

Ce que ce script mesure
-----------------------
Trois politiques, sur exactement les mêmes jours-station de 2025 :

1. **figé** — appris jusqu'au 31/12/2024, jamais réajusté (ce que montrent les calendriers) ;
2. **glissant mensuel** — réentraîné au début de chaque mois avec tout l'historique disponible
   jusqu'à la veille, ce qui approche la pratique du produit officiel ;
3. le **MOS officiel** lui-même, en référence.

**Le contrôle qui garde le test honnête** : à chaque réentraînement, les données ajoutées
s'arrêtent à **J−2** du premier jour prédit. Aucun modèle ne voit le jour qu'il annonce, ni la
veille — c'est plus strict que le produit officiel, qui utilise J−1.

Usage : python3 scripts/reentrainement_glissant.py [--polluant O3] [--annee 2025]
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

from aq.ingest import controle as ctl  # noqa: E402
from apport_observation_veille import variables_passees  # noqa: E402
from calendrier_annee import charger_annee  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from comparer_mos_officiel import journalier, lire_officiel  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from heatmap_annuelle import PREFIXE, SEUIL  # noqa: E402
from modele_final import REGLE  # noqa: E402

DECALAGE_JOURS = 2  # rien de plus récent que J−2 : plus strict que le produit officiel


def ajuster(entrainement: pd.DataFrame, predicteurs: list[str]):

    m = modele_mos(graine=0)
    m.fit(entrainement[predicteurs],
          entrainement["obs_jour"] - entrainement["cams_jour"])
    return m


def main(polluant: str, annee: int, n_plis: int) -> int:
    depart = time.time()
    seuil = SEUIL[polluant]
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]

    # ── Le socle : tout l'historique nationale jusqu'à fin 2024 ───────────────
    appris = charger(polluant, 1)
    colonnes = colonnes_admises(appris)
    appris[colonnes] = appris[colonnes].replace([np.inf, -np.inf], 30_000.0)
    appris = appris.dropna(subset=["valeur"])
    appris = appris[appris["timestamp_utc"].dt.year <= 2024]
    socle = agreger_journalier(appris, colonnes, grandeur)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    socle["jour"] = pd.to_datetime(socle["jour"]).dt.tz_localize(None)
    passees, obs = variables_passees(socle)
    socle = socle.merge(passees, on=["station_id", "jour"], how="left").dropna(subset=obs)
    predicteurs = base + obs
    print(f"socle : {len(socle):,} jours-station jusqu'au {socle['jour'].max():%Y-%m-%d}",
          flush=True)

    # ── L'année à prédire ─────────────────────────────────────────────────────
    d = charger_annee(polluant, annee)
    d[colonnes] = d[colonnes].replace([np.inf, -np.inf], 30_000.0)
    d = d.dropna(subset=["valeur"])
    cible = agreger_journalier(d, colonnes, grandeur)
    cible["jour"] = pd.to_datetime(cible["jour"]).dt.tz_localize(None)
    passees_c, _ = variables_passees(cible)
    cible = cible.merge(passees_c, on=["station_id", "jour"], how="left")
    cible = cible.dropna(subset=predicteurs)
    ctl.exiger_lignes(cible, 500, f"cible {annee}")
    print(f"cible : {len(cible):,} jours-station · {cible['station_id'].nunique()} stations · "
          f"{cible['jour'].min():%Y-%m-%d} → {cible['jour'].max():%Y-%m-%d}", flush=True)

    # ── Politique 1 : figé ────────────────────────────────────────────────────
    fige = ajuster(socle, predicteurs)
    cible["fige"] = np.clip(
        cible["cams_jour"] + fige.predict(cible[predicteurs]), 0, None)
    print(f"  figé ajusté · {time.time() - depart:.0f}s", flush=True)

    # ── Politique 2 : réentraînement glissant, au début de chaque mois ────────
    # Le produit officiel se réentraîne chaque jour ; un pas mensuel en approche la pratique
    # pour un coût praticable, et **désavantage** notre modèle plutôt que l'inverse : ses
    # données sont en moyenne plus anciennes que celles du produit auquel il se compare.
    cible["glissant"] = np.nan
    for mois in sorted(cible["jour"].dt.to_period("M").unique()):
        debut = mois.start_time
        limite = debut - pd.Timedelta(days=DECALAGE_JOURS)
        recent = cible[cible["jour"] <= limite]
        entrainement = (pd.concat([socle, recent[socle.columns]], ignore_index=True)
                        if not recent.empty else socle)
        modele = ajuster(entrainement, predicteurs)
        test = cible["jour"].dt.to_period("M") == mois
        cible.loc[test, "glissant"] = np.clip(
            cible.loc[test, "cams_jour"] + modele.predict(cible.loc[test, predicteurs]),
            0, None)
        print(f"  {mois} · entraîné sur {len(entrainement):,} (dont {len(recent):,} de "
              f"{annee}) · {int(test.sum()):,} jours prédits · {time.time() - depart:.0f}s",
              flush=True)

    # ── Le produit officiel, en référence ─────────────────────────────────────
    archives = sorted((RACINE / "data/raw/cams_mos_officiel").glob(
        f"{PREFIXE[polluant]}_{annee}*.zip"))
    if archives:
        o = pd.concat([journalier(lire_officiel(a), ["officiel_mos"], grandeur)
                       for a in archives], ignore_index=True)
        o["jour"] = pd.to_datetime(o["jour"]).dt.tz_localize(None)
        cible = cible.merge(o, on=["station_id", "jour"], how="left")

    produits = [("cams_jour", "CAMS brut"), ("fige", "nous, figé fin 2024"),
                ("glissant", "nous, réentraîné en continu")]
    if "officiel_mos" in cible:
        produits.insert(1, ("officiel_mos", "MOS officiel"))

    # Comparaison sur les **mêmes lignes** pour tous : sans cela, l'écart mesurerait la
    # couverture du produit officiel plutôt que sa qualité.
    communes = cible.dropna(subset=[c for c, _ in produits])
    print(f"\ncomparaison sur {len(communes):,} jours-station communs · "
          f"{int((communes['obs_jour'] >= seuil).sum())} dépassements observés\n", flush=True)

    from aq.eval import comparaison as cmp

    lignes = []
    print(f"{'produit':30s} {'RMSE':>7s} {'biais':>7s} {'signalements':>13s} {'pic':>5s}")
    reference = int((communes["obs_jour"] >= seuil).sum())
    for colonne, nom in produits:
        m = cmp.metriques(communes["obs_jour"], communes[colonne])
        s = communes[communes[colonne] >= seuil].groupby("jour").size()
        total, pic = int(s.sum()), int(s.max()) if len(s) else 0
        print(f"{nom:30s} {m['rmse']:7.2f} {m['biais']:+7.2f} "
              f"{total:6d} ({100 * total / max(reference, 1):3.0f} %) {pic:5d}", flush=True)
        lignes.append({"produit": nom, **m, "signalements": total, "pic": pic})
    print(f"{'la vérité':30s} {'—':>7s} {'—':>7s} {reference:6d} (100 %) "
          f"{int(communes[communes['obs_jour'] >= seuil].groupby('jour').size().max()):5d}")

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/reentrainement_glissant_{polluant}_{annee}.csv",
                 index=False)
    communes.to_csv(
        RACINE / f"reports/reentrainement_glissant_{polluant}_{annee}_detail.csv", index=False)

    fige_r = float(table.loc[table["produit"].str.contains("figé"), "rmse"].iloc[0])
    gliss_r = float(table.loc[table["produit"].str.contains("continu"), "rmse"].iloc[0])
    print(f"\n{'═' * 74}")
    print(f"Le réentraînement continu rend {fige_r - gliss_r:+.2f} µg/m³ "
          f"({100 * (fige_r - gliss_r) / fige_r:+.1f} %) contre le modèle figé.")
    if "officiel_mos" in cible:
        off = float(table.loc[table["produit"] == "MOS officiel", "rmse"].iloc[0])
        print(f"Contre le MOS officiel : figé {fige_r - off:+.2f}, "
              f"glissant {gliss_r - off:+.2f} µg/m³ (négatif = nous devançons).")
    print(f"\nÉcrit : reports/reentrainement_glissant_{polluant}_{annee}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--annee", type=int, default=2025)
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.annee, args.plis))
