#!/usr/bin/env python3
"""Le POD mesure-t-il une capacité, ou un seuil mal placé ?

Le constat qui motive ce script
-------------------------------
Sur la période apprise, les métriques de rang (AUC-PR +0,098, VUS-PR +0,076) donnent la
correction franchement gagnante, alors que le POD ponctuel la donne légèrement **perdante**
(0,359 → 0,342). Les deux mesures ne peuvent pas décrire la même chose.

L'explication tient en une phrase : le POD applique le seuil réglementaire de 120 µg/m³ à la
**concentration prédite**, tandis que les métriques de rang n'appliquent aucun seuil. Un
modèle entraîné au moindre carré écrase les extrêmes — il conserve donc l'**ordre** des jours
tout en abaissant leur **niveau**. Le classement s'améliore, le franchissement du seuil se
perd. C'est un défaut de calibration, pas de capacité, et il se corrige sans réapprendre.

Ce que le script mesure
-----------------------
Pour chaque produit, on cherche le seuil de décision qui maximise le CSI **sur 2024**, puis on
l'applique tel quel **sur 2025**. Le seuil n'est jamais choisi sur les données où il est
évalué : l'optimisme de sélection est ainsi écarté, et le gain affiché est celui qu'un service
obtiendrait réellement en fixant sa règle une fois pour toutes.

**Le contrôle qui empêche de conclure trop vite** : la même recalibration est appliquée au MOS
officiel de Copernicus et au CAMS brut. Si tous en profitent également, la calibration est une
propriété générale du problème et non un avantage du projet — et il faut le dire ainsi.

Usage : python3 scripts/seuil_decision.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from comparer_mos_officiel import journalier, lire_officiel  # noqa: E402
from scores_episodes import scores  # noqa: E402

SEUILS = {"O3": 120.0, "NO2": 200.0, "PM25": 25.0}
PREFIXES = {"O3": "o3", "NO2": "no2", "PM25": "pm25"}
GRANDEURS = {"O3": "max_8h", "NO2": "max_horaire", "PM25": "moyenne_jour"}


def officiel_2024(polluant: str, appris: pd.DataFrame) -> pd.DataFrame:
    """Adjoint la colonne du MOS officiel à la période de calibration.

    **Sans cela, la comparaison serait truquée** : recalibrer notre seuil et laisser le
    produit officiel au seuil réglementaire brut lui ferait porter un handicap que nous nous
    serions retiré à nous-mêmes. Le gain affiché ne mesurerait plus une capacité, seulement
    l'asymétrie du protocole.
    """
    archives = sorted((RACINE / "data/raw/cams_mos_officiel").glob(
        f"{PREFIXES[polluant]}_2024*.zip"))
    if not archives:
        return appris
    blocs = []
    for archive in archives:
        off = lire_officiel(archive)
        blocs.append(journalier(off, ["officiel_mos"], GRANDEURS[polluant]))
    oj = pd.concat(blocs, ignore_index=True)
    oj["jour"] = pd.to_datetime(oj["jour"], utc=True)
    appris = appris.copy()
    appris["jour"] = pd.to_datetime(appris["jour"], utc=True)
    return appris.merge(oj, on=["station_id", "jour"], how="left")


def journalier_appris(polluant: str) -> pd.DataFrame:
    """La période apprise, agrégée au maximum journalier 8 h."""
    d = pd.read_csv(RACINE / f"reports/mos_{polluant}_J1.csv",
                    parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])
    d = d.sort_values(["station_id", "timestamp_utc"])
    d["jour"] = d["timestamp_utc"].dt.floor("D")
    for c in ("observe", "cams", "corrige"):
        d[c + "_8h"] = (d.groupby("station_id")[c]
                          .transform(lambda s: s.rolling(8, min_periods=6).mean()))
    j = (d.groupby(["station_id", "jour"])
           .agg(observe=("observe_8h", "max"), cams=("cams_8h", "max"),
                corrige=("corrige_8h", "max"), n=("timestamp_utc", "size"))
           .reset_index())
    return j[j["n"] >= 18].dropna(subset=["observe", "cams", "corrige"])


def seuil_optimal(observe: np.ndarray, predit: np.ndarray, seuil_obs: float,
                  critere: str = "CSI") -> tuple[float, float]:
    """Seuil de décision maximisant le critère, cherché sur la plage utile.

    On balaie les **quantiles** de la prédiction plutôt qu'une grille en µg/m³ : la plage
    utile dépend du produit — un modèle qui écrase les extrêmes n'atteint jamais 120 —
    et une grille fixe explorerait surtout des seuils sans aucun jour au-dessus.
    """
    depasse = observe >= seuil_obs
    if depasse.sum() < 20:
        return float("nan"), float("nan")
    candidats = np.unique(np.quantile(predit, np.linspace(0.80, 0.9995, 200)))
    meilleur, valeur = float("nan"), -1.0
    for s in candidats:
        v = scores(depasse, predit >= s).get(critere, 0.0)
        if v > valeur:
            meilleur, valeur = float(s), float(v)
    return meilleur, valeur


def main(polluant: str, critere: str) -> int:
    seuil = SEUILS[polluant]

    appris = officiel_2024(polluant, journalier_appris(polluant))
    chemin_2025 = RACINE / f"reports/test_hors_echantillon_2025_detail_{polluant}.csv"
    if not chemin_2025.exists():
        raise SystemExit(f"{chemin_2025.name} absent — relancer "
                         f"test_hors_echantillon_2025.py")
    hors = pd.read_csv(chemin_2025, parse_dates=["jour"]).rename(
        columns={"obs_jour": "observe", "cams_jour": "cams"})

    produits = [("CAMS brut", "cams"), ("NOTRE correction", "corrige")]
    if "officiel_mos" in hors:
        produits.insert(1, ("MOS officiel", "officiel_mos"))

    print(f"{polluant} · seuil réglementaire {seuil:.0f} µg/m³ · critère {critere}")
    print(f"  calibration : {len(appris):,} jours-station 2024 "
          f"({int((appris['observe'] >= seuil).sum())} dépassements)")
    print(f"  évaluation  : {len(hors):,} jours-station 2025 "
          f"({int((hors['observe'] >= seuil).sum())} dépassements)\n", flush=True)

    print(f"{'produit':20s} {'seuil calibré':>13s} │ "
          f"{'POD à 120':>9s} {'FAR':>6s} {'CSI':>6s} │ "
          f"{'POD calibré':>11s} {'FAR':>6s} {'CSI':>6s}")
    lignes = []
    depasse_2025 = (hors["observe"] >= seuil).to_numpy()
    for nom, col in produits:
        # Le seuil se cherche sur 2024 — la colonne du MOS officiel n'y existe pas dans
        # notre fichier de prédictions, on se rabat alors sur le seuil réglementaire brut
        # et on le signale : un produit non recalibrable ne doit pas passer pour recalibré.
        if col in appris:
            base = appris.dropna(subset=["observe", col])
            s_cal, _ = seuil_optimal(base["observe"].to_numpy(),
                                     base[col].to_numpy(), seuil, critere)
            n_cal = len(base)
        else:
            s_cal, n_cal = float("nan"), 0

        brut = scores(depasse_2025, (hors[col] >= seuil).to_numpy())
        if np.isnan(s_cal):
            cal = {}
        else:
            cal = scores(depasse_2025, (hors[col] >= s_cal).to_numpy())

        def _f(d, k):
            return f"{d[k]:6.3f}" if d else "   —  "

        etiquette = f"{s_cal:13.1f}" if not np.isnan(s_cal) else f"{'non calibrable':>13s}"
        print(f"{nom:20s} {etiquette} │ "
              f"{brut['POD']:9.3f} {brut['FAR']:6.3f} {brut['CSI']:6.3f} │ "
              f"{_f(cal, 'POD'):>11s} {_f(cal, 'FAR')} {_f(cal, 'CSI')}", flush=True)
        lignes.append({"produit": nom, "seuil_calibre": s_cal, "n_calibration": n_cal,
                       **{f"brut_{k}": v for k, v in brut.items()},
                       **{f"calibre_{k}": v for k, v in cal.items()}})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/seuil_decision_{polluant}.csv", index=False)

    print("\n" + "=" * 78)
    ligne_nous = table[table["produit"] == "NOTRE correction"].iloc[0]
    gain = ligne_nous.get("calibre_POD", np.nan) - ligne_nous["brut_POD"]
    print(f"Notre POD hors échantillon : {ligne_nous['brut_POD']:.3f} au seuil réglementaire "
          f"→ {ligne_nous.get('calibre_POD', float('nan')):.3f} au seuil calibré "
          f"({gain:+.3f}).")
    ligne_brut = table[table["produit"] == "CAMS brut"].iloc[0]
    gain_brut = ligne_brut.get("calibre_POD", np.nan) - ligne_brut["brut_POD"]
    print(f"Le CAMS brut gagne {gain_brut:+.3f} par la même opération.")
    if not np.isnan(gain) and not np.isnan(gain_brut):
        if gain > gain_brut + 0.05:
            print("→ la recalibration profite **davantage** à la correction : son POD brut "
                  "sous-estimait\n  bien une capacité réelle, masquée par l'écrasement des "
                  "extrêmes.")
        elif abs(gain - gain_brut) <= 0.05:
            print("→ les deux produits en profitent autant : la calibration est une propriété "
                  "générale\n  du seuillage, pas un avantage propre au modèle. À présenter "
                  "comme telle.")
        else:
            print("→ le CAMS brut en profite davantage : l'hypothèse de la capacité masquée "
                  "ne tient pas.")
    print(f"\nÉcrit : reports/seuil_decision_{polluant}.csv", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--critere", default="CSI", choices=("CSI", "POD"))
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.critere))
