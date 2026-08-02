#!/usr/bin/env python3
"""Table de contingence et scores d'épisode, au format du référentiel LCSQA.

Pourquoi ce script existe
-------------------------
Le projet annonçait un **rappel** (0,24 → 0,47) sans jamais publier la table de
contingence qui va avec. Or le guide LCSQA *Évaluation des performances des prévisions de
la qualité de l'air* (applicable au 01/01/2022) impose **POD, FAR, SR, FB et CSI**, une
disponibilité de **75 % de couples**, et pour l'O₃ une évaluation en **maximum journalier**
d'avril à septembre. Sans ces scores, aucune comparaison à la littérature n'est possible :
les repères publiés (CSI 0,30-0,40 pour l'O₃ à 180 µg/m³ chez Bertrand et al. 2023) sont
exprimés dans cette grille et dans aucune autre.

Deux agrégations journalières, parce que les seuils réglementaires ne portent pas sur la
même grandeur :

- **maximum horaire du jour** — grandeur du seuil d'information (180 µg/m³) et du seuil
  d'alerte ;
- **maximum journalier de la moyenne glissante 8 h** — grandeur de la valeur cible
  (120 µg/m³) et celle qu'emploie FAIRMODE pour l'O₃.

Le script travaille sur les prédictions **déjà écrites** (`reports/mos_{p}_J{h}.csv`) : il
ne réajuste rien et peut tourner pendant un ajustement.

Usage : python3 scripts/scores_episodes.py [--polluant O3] [--horizon 1]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]

# Seuils par polluant et par grandeur, en µg/m³. Sources : directive 2008/50/CE et
# arrêté français ; le seuil ATMO « Mauvais » vient de l'arrêté du 10 juillet 2020.
SEUILS = {
    "O3": {"max_horaire": [150.0, 180.0], "max_8h": [120.0, 130.0]},
    "NO2": {"max_horaire": [120.0, 200.0], "max_8h": []},
    "PM25": {"moyenne_jour": [25.0, 50.0], "max_horaire": [], "max_8h": []},
}

# Couverture minimale d'une journée pour qu'elle compte, au sens du référentiel.
COUVERTURE_MIN = 0.75


def scores(observe_depasse: np.ndarray, predit_depasse: np.ndarray) -> dict:
    """POD, FAR, SR, FB, CSI depuis la table de contingence.

    `a` bonnes détections · `b` fausses alertes · `c` non-détections · `d` bons rejets.
    `FB` est le **biais de fréquence** `(a+b)/(a+c)` : au-dessus de 1 le modèle
    sur-annonce, en dessous il sous-annonce. Ce n'est pas le biais fractionnel de
    concentration — les deux se notent parfois pareil, d'où la précision.
    """
    a = int(np.sum(observe_depasse & predit_depasse))
    b = int(np.sum(~observe_depasse & predit_depasse))
    c = int(np.sum(observe_depasse & ~predit_depasse))
    d = int(np.sum(~observe_depasse & ~predit_depasse))

    def _div(num, den):
        return float(num / den) if den else np.nan

    return {
        "a_detections": a, "b_fausses_alertes": b,
        "c_manques": c, "d_bons_rejets": d,
        "n_observes": a + c,
        "POD": _div(a, a + c),
        "FAR": _div(b, a + b),
        "SR": _div(a, a + b),
        "FB": _div(a + b, a + c),
        "CSI": _div(a, a + b + c),
    }


def agreger(horaire: pd.DataFrame, grandeur: str) -> pd.DataFrame:
    """Passe de l'horaire au journalier, en rejetant les jours trop lacunaires."""
    d = horaire.copy()
    d["jour"] = d["timestamp_utc"].dt.floor("D")
    colonnes = ["observe", "cams", "corrige"]

    if grandeur == "max_8h":
        # Moyenne glissante 8 h par station, puis maximum du jour. `min_periods=6`
        # applique la règle des 75 % à la fenêtre elle-même.
        d = d.sort_values(["station_id", "timestamp_utc"])
        for c in colonnes:
            d[c] = (d.groupby("station_id")[c]
                      .transform(lambda s: s.rolling(8, min_periods=6).mean()))
        agregation = "max"
    elif grandeur == "max_horaire":
        agregation = "max"
    else:
        agregation = "mean"

    groupes = d.groupby(["station_id", "jour"])
    journalier = groupes[colonnes].agg(agregation)
    # Couverture : nombre d'heures effectivement observées sur 24.
    journalier["couverture"] = groupes["observe"].count() / 24.0
    journalier = journalier[journalier["couverture"] >= COUVERTURE_MIN]
    return journalier.dropna(subset=colonnes).reset_index()


def main(polluant: str, horizon: int, mois_ozone: bool) -> int:
    chemin = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    if not chemin.exists():
        print(f"ÉCHEC : {chemin.name} absent", file=sys.stderr)
        return 1

    horaire = pd.read_csv(chemin, parse_dates=["timestamp_utc"])
    horaire = horaire.dropna(subset=["observe", "cams", "corrige"])
    print(f"{polluant} J+{horizon} · {len(horaire):,} couples horaires · "
          f"{horaire['station_id'].nunique()} stations", flush=True)

    lignes = []
    for grandeur, seuils in SEUILS.get(polluant, {}).items():
        if not seuils:
            continue
        journalier = agreger(horaire, grandeur)

        # Le référentiel évalue l'O₃ d'avril à septembre : la saison photochimique est la
        # seule où le dépassement a un sens, et l'inclure en janvier dilue le score.
        if mois_ozone and polluant == "O3":
            journalier = journalier[journalier["jour"].dt.month.between(4, 9)]

        print(f"\n--- {grandeur} · {len(journalier):,} jours-station "
              f"({journalier['jour'].dt.strftime('%Y-%m').nunique()} mois) ---", flush=True)
        print(f"{'seuil':>7s} {'modèle':10s} {'n obs':>6s} {'POD':>6s} {'FAR':>6s} "
              f"{'SR':>6s} {'FB':>6s} {'CSI':>6s}")

        for seuil in seuils:
            observe = (journalier["observe"] >= seuil).to_numpy()
            if observe.sum() == 0:
                print(f"{seuil:7.0f} — aucun dépassement observé, score sans objet")
                continue
            for nom, colonne in (("CAMS brut", "cams"), ("corrigé", "corrige")):
                s = scores(observe, (journalier[colonne] >= seuil).to_numpy())
                print(f"{seuil:7.0f} {nom:10s} {s['n_observes']:6d} "
                      f"{s['POD']:6.3f} {s['FAR']:6.3f} {s['SR']:6.3f} "
                      f"{s['FB']:6.3f} {s['CSI']:6.3f}", flush=True)
                lignes.append({"polluant": polluant, "horizon": horizon,
                               "grandeur": grandeur, "seuil": seuil,
                               "modele": nom, **s})

    if not lignes:
        print("\n⚠️ aucun seuil exploitable pour ce polluant", flush=True)
        return 0

    sortie = RACINE / f"reports/scores_episodes_{polluant}_J{horizon}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--toute-annee", action="store_true",
                   help="ne pas restreindre l'O₃ à avril-septembre")
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, not args.toute_annee))
