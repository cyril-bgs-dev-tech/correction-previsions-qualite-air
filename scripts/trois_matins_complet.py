#!/usr/bin/env python3
"""Les trois matinées rejouées avec **tout** ce que le projet a mesuré depuis.

La question posée
-----------------
*Les nouvelles informations changent-elles ce qu'un prévisionniste aurait décidé ces matins-là ?*

Le rejeu initial (`scripts/trois_matins.py`) comparait trois produits : CAMS brut, la correction
du dossier, et la même avec les observations de l'avant-veille. Depuis, deux leviers ont été
mesurés et se sont révélés additifs en détection — les **six membres de l'ensemble CAMS** et
l'**exposition aux feux**.

Ce que ce rejeu peut, et ce qu'il ne peut pas
----------------------------------------------
| source | couvre juillet 2026 ? |
|---|---|
| observations à J−2 | ✅ |
| membres d'ensemble | ✅ — téléchargés pour l'occasion |
| feux GFAS | ❌ le jeu s'arrête au **03/12/2025** |

Les feux restent donc hors du rejeu. Ce n'est pas une perte majeure pour ces trois journées :
le gradient ouest-est de 200 km observé le 25/07 — Rodez à 51 µg/m³, Montpellier à 12 — ne
ressemble pas à un panache local mais à une advection régionale, poussière ou transport
ibérique.

**Ce que le rejeu ne dit toujours pas.** L'épisode du 25/07 était un dépassement **PM10**, que
le projet ne modélise pas ; on rejoue les PM2,5. Et le modèle n'a pas tourné en direct ce
jour-là.

Usage : python3 scripts/trois_matins_complet.py
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
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import controle as ctl  # noqa: E402
from apport_observation_veille import variables_passees  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402
from rejeu_episode import charger_rejeu  # noqa: E402

JOURS = ["2026-07-25", "2026-07-26", "2026-07-27"]
SEUIL = 25.0  # sous-indice ATMO « mauvais » pour les PM2,5
MEMBRES = ["chimere", "emep", "mocage", "silam", "lotos", "match"]


def entrainer(j: pd.DataFrame, predicteurs: list[str]):

    m = modele_mos(graine=0)
    m.fit(j[predicteurs], j["obs_jour"] - j["cams_jour"])
    return m


def joindre_membres(d: pd.DataFrame, court: str, mois: str | None) -> tuple[pd.DataFrame, list]:
    """Joint les membres horaires ; `mois=None` couvre toute la fenêtre d'entraînement."""
    motif = (f"membres_metropole_{court}_*.parquet" if mois is None
             else f"membres_metropole_{court}_{mois}.parquet")
    fichiers = sorted(glob.glob(str(RACINE / "data/processed/meteo" / motif)))
    if not fichiers:
        return d, []
    m = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    ctl.exiger_colonnes(m, MEMBRES, "membres")
    ctl.exiger_variation(m, MEMBRES, "membres")
    avant = len(d)
    d = d.merge(m[["station_id", "timestamp_utc"] + MEMBRES],
                on=["station_id", "timestamp_utc"], how="inner")
    ctl.exiger_lignes(d, max(100, avant // 10), "après jointure membres")
    return d, MEMBRES


def main(polluant: str = "PM25", horizon: int = 1) -> int:
    depart = time.time()
    court = {"O3": "o3", "NO2": "no2", "PM25": "pm25"}[polluant]
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]

    appris = charger(polluant, horizon)
    colonnes = colonnes_admises(appris)
    appris[colonnes] = appris[colonnes].replace([np.inf, -np.inf], 30_000.0)
    appris = appris.dropna(subset=["valeur"])
    appris, membres = joindre_membres(appris, court, None)
    ja = agreger_journalier(appris, colonnes + membres, grandeur)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    passees_a, obs = variables_passees(ja)
    ja["jour"] = pd.to_datetime(ja["jour"])
    ja = ja.merge(passees_a, on=["station_id", "jour"], how="left").dropna(subset=obs)
    print(f"appris sur {len(ja):,} jours-station · {len(membres)} membres · "
          f"{len(obs)} variables d'observation passée", flush=True)

    modeles = {
        "correction": entrainer(ja, base),
        "+ obs J−2": entrainer(ja, base + obs),
    }
    if membres:
        modeles["+ obs + membres"] = entrainer(ja, base + obs + membres)
    print(f"  {len(modeles)} modèles ajustés · {time.time() - depart:.0f}s", flush=True)

    # ── Le rejeu ──────────────────────────────────────────────────────────────
    rejeu = charger_rejeu(polluant, horizon)
    rejeu[colonnes] = rejeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    rejeu = rejeu.dropna(subset=["valeur"])
    rejeu, membres_r = joindre_membres(rejeu, court, "202607")
    if membres and not membres_r:
        print("⚠️ membres absents pour juillet 2026 — le rejeu se limite aux observations",
              flush=True)
        modeles.pop("+ obs + membres", None)

    jr = agreger_journalier(rejeu, colonnes + membres_r, grandeur)
    jr["jour"] = pd.to_datetime(jr["jour"])
    passees_r, _ = variables_passees(jr)
    jr = jr.merge(passees_r, on=["station_id", "jour"], how="left")

    predicteurs = {"correction": base, "+ obs J−2": base + obs,
                   "+ obs + membres": base + obs + membres}
    for nom, m in modeles.items():
        p = predicteurs[nom]
        complet = jr.dropna(subset=[c for c in p if c in jr.columns])
        jr[nom] = np.nan
        if complet.empty:
            continue
        jr.loc[complet.index, nom] = np.clip(
            complet["cams_jour"] + m.predict(complet[p]), 0, None)

    jr["date"] = jr["jour"].dt.strftime("%Y-%m-%d")
    produits = ["cams_jour"] + list(modeles)
    lignes = []
    for jour in JOURS:
        s = jr[jr["date"] == jour]
        if s.empty:
            continue
        print(f"\n{'═' * 78}\n{jour} · {len(s)} stations")
        entete = f"{'station':10s} {'observé':>8s} {'CAMS':>7s}"
        for nom in modeles:
            entete += f" {nom:>16s}"
        print(entete)
        for _, r in s.sort_values("obs_jour", ascending=False).head(4).iterrows():
            ligne = f"{r['station_id']:10s} {r['obs_jour']:8.1f} {r['cams_jour']:7.1f}"
            for nom in modeles:
                v = r[nom]
                ligne += f" {v:16.1f}" if pd.notna(v) else f" {'—':>16s}"
            print(ligne)

        detecte = {c: int((s[c] >= SEUIL).sum()) for c in produits if s[c].notna().any()}
        reel = int((s["obs_jour"] >= SEUIL).sum())
        print(f"\n  stations au-dessus de {SEUIL:.0f} µg/m³ — réel {reel} · "
              + " · ".join(f"{k} {v}" for k, v in detecte.items()), flush=True)
        lignes.append({"jour": jour, "n_stations": len(s), "reel": reel,
                       **{f"detecte_{k}": v for k, v in detecte.items()},
                       **{f"max_{c}": float(s[c].max()) for c in produits
                          if s[c].notna().any()}})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/trois_matins_complet_{polluant}.csv", index=False)
    jr[["station_id", "date", "obs_jour", "cams_jour"] + list(modeles)].to_csv(
        RACINE / f"reports/trois_matins_complet_{polluant}_detail.csv", index=False)
    print(f"\nÉcrit : reports/trois_matins_complet_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
