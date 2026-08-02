#!/usr/bin/env python3
"""Trois matinées d'astreinte, rejouées — avec et sans l'observation de la veille.

Pourquoi ce script existe
-------------------------
Deux relectures indépendantes ont fait le même reproche, dans les mêmes termes : *« beaucoup de
RMSE, encore peu de matins rejoués sur vos épisodes »*, et *« montrez-moi trois jours
d'Occitanie où vous m'évitez une bêtise »*. Un tableau de gains sur 134 000 jours-station ne dit
pas ce qu'un prévisionniste aurait fait à 10 h.

Les trois journées ne sont pas choisies pour flatter : ce sont les **seules** de juillet 2026
où l'Occitanie a connu un dépassement PM, dont le 25/07 constaté seulement *a posteriori*.

Ce que le rejeu montre déjà, sans modèle nouveau
------------------------------------------------
La station FR12095 est sous-estimée par CAMS les trois jours — 6,4 contre 51,2 ; 28,4 contre
46,8 ; 15,1 contre 44,8. La correction actuelle n'y change presque rien, et le 26/07 elle
**éloigne** la prévision de l'observation. Sur les mêmes jours, elle **sauve** deux autres
stations où CAMS sur-estime.

Le motif : la correction rattrape les sur-estimations et échoue sur les **sous-estimations
locales persistantes**. Or une sous-estimation persistante laisse une trace dans l'observation
de la veille — c'est précisément le prédicteur mesuré à +8,9 % (O₃) et +21,9 % (NO₂).

Ce script vérifie si cette lecture tient sur ces trois matins, au lieu de l'affirmer.

**Ce qu'il ne peut pas montrer.** L'épisode du 25/07 était un dépassement **PM10**, que le
projet ne modélise pas. On rejoue les PM2,5, corrélées mais distinctes : aucune conclusion sur
le dépassement lui-même.

Usage : python3 scripts/trois_matins.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from apport_observation_veille import variables_passees  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402
from rejeu_episode import charger_rejeu  # noqa: E402

JOURS = ["2026-07-25", "2026-07-26", "2026-07-27"]
SEUIL_INFO_PM25 = 25.0  # seuil du sous-indice ATMO « mauvais » pour les PM2,5


def entrainer(predicteurs: list[str], j: pd.DataFrame):

    m = modele_mos(graine=0)
    m.fit(j[predicteurs], j["obs_jour"] - j["cams_jour"])
    return m


def main(polluant: str = "PM25", horizon: int = 1) -> int:
    depart = time.time()
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]

    appris = charger(polluant, horizon)
    colonnes = colonnes_admises(appris)
    appris[colonnes] = appris[colonnes].replace([np.inf, -np.inf], 30_000.0)
    appris = appris.dropna(subset=["valeur"])
    ja = agreger_journalier(appris, colonnes, grandeur)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    passees_a, noms = variables_passees(ja)
    ja["jour"] = pd.to_datetime(ja["jour"])
    ja = ja.merge(passees_a, on=["station_id", "jour"], how="left").dropna(subset=noms)
    print(f"appris sur {len(ja):,} jours-station · {len(noms)} variables d'observation passée",
          flush=True)

    sans = entrainer(base, ja)
    avec = entrainer(base + noms, ja)

    # ── Le rejeu de juillet 2026 ──────────────────────────────────────────────
    rejeu = charger_rejeu(polluant, horizon)
    rejeu[colonnes] = rejeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    rejeu = rejeu.dropna(subset=["valeur"])
    jr = agreger_journalier(rejeu, colonnes, grandeur)
    jr["jour"] = pd.to_datetime(jr["jour"])
    passees_r, _ = variables_passees(jr)
    jr = jr.merge(passees_r, on=["station_id", "jour"], how="left")

    jr["sans_obs"] = np.clip(jr["cams_jour"] + sans.predict(jr[base]), 0, None)
    complet = jr.dropna(subset=noms)
    jr["avec_obs"] = np.nan
    jr.loc[complet.index, "avec_obs"] = np.clip(
        complet["cams_jour"] + avec.predict(complet[base + noms]), 0, None)

    jr["date"] = jr["jour"].dt.strftime("%Y-%m-%d")
    lignes = []
    for jour in JOURS:
        s = jr[jr["date"] == jour]
        if s.empty:
            continue
        pire = s.loc[s["obs_jour"].idxmax()]
        print(f"\n{'═' * 74}\n{jour} · {len(s)} stations · station la plus chargée "
              f"{pire['station_id']}")
        print(f"{'station':10s} {'observé':>8s} {'CAMS':>8s} {'sans obs':>9s} "
              f"{'avec obs':>9s}   décision")
        for _, r in s.sort_values("obs_jour", ascending=False).head(5).iterrows():
            def _annonce(v):
                return "ALERTE" if v >= SEUIL_INFO_PM25 else "—"
            print(f"{r['station_id']:10s} {r['obs_jour']:8.1f} {r['cams_jour']:8.1f} "
                  f"{r['sans_obs']:9.1f} {r['avec_obs']:9.1f}   "
                  f"réel {_annonce(r['obs_jour']):6s} · CAMS {_annonce(r['cams_jour']):6s} · "
                  f"sans {_annonce(r['sans_obs']):6s} · avec {_annonce(r['avec_obs'])}")

        # Ce qui compte pour un service : le **maximum régional**, qui décide de l'indice.
        m = {k: s[k].max() for k in ("obs_jour", "cams_jour", "sans_obs", "avec_obs")}
        detecte = {k: int((s[k] >= SEUIL_INFO_PM25).sum()) for k in m}
        print(f"\n  maximum régional : observé {m['obs_jour']:.1f} · CAMS {m['cams_jour']:.1f} "
              f"· sans obs {m['sans_obs']:.1f} · avec obs {m['avec_obs']:.1f}")
        print(f"  stations au-dessus de {SEUIL_INFO_PM25:.0f} µg/m³ : "
              f"réel {detecte['obs_jour']} · CAMS {detecte['cams_jour']} · "
              f"sans obs {detecte['sans_obs']} · avec obs {detecte['avec_obs']}", flush=True)
        lignes.append({"jour": jour, "n_stations": len(s),
                       **{f"max_{k}": v for k, v in m.items()},
                       **{f"n_depasse_{k}": v for k, v in detecte.items()}})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / "reports/trois_matins_PM25.csv", index=False)
    jr[["station_id", "date", "obs_jour", "cams_jour", "sans_obs", "avec_obs"]].to_csv(
        RACINE / "reports/trois_matins_PM25_detail.csv", index=False)
    print(f"\nÉcrit : reports/trois_matins_PM25.csv · {time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
