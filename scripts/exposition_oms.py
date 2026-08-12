#!/usr/bin/env python3
"""Distribution des moyennes annuelles 2025 face aux lignes directrices OMS 2021.

Dérivé de `reports/seuils_2030.csv`, écrit par `scripts/seuils_2030.py` — même
population de stations, même filtre de taux de saisie (≥ 75 %), même année.
Ce script n'ingère rien : il ne fait que résumer une table déjà contrôlée.

`VERITE_DOSSIER` § 5 bis compte les stations au-dessus des valeurs LIMITES.
Ici on compte au-dessus des lignes directrices **sanitaires** de l'OMS, qui sont
plus basses — c'est la question « où en est-on du point de vue de la santé »,
pas « où en est-on du point de vue du droit ». Les deux ne se citent jamais
l'une pour l'autre.

L'ozone est absent : il n'a pas de moyenne annuelle réglementaire, et la ligne
directrice OMS porte sur un maximum 8 h et sur un pic saisonnier.

Sortie : `reports/exposition_oms.csv`
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "reports" / "seuils_2030.csv"
CIBLE = RACINE / "reports" / "exposition_oms.csv"

# OMS 2021, moyenne annuelle (µg/m³) — REGLEMENTAIRE.md § 5.
OMS = {"NO2": 10.0, "PM10": 15.0, "PM25": 5.0}
# Valeurs limites en vigueur et au 01/01/2030 — REGLEMENTAIRE.md § 3 et § 4.1.
VL_ACTUELLE = {"NO2": 40.0, "PM10": 40.0, "PM25": 25.0}
VL_2030 = {"NO2": 20.0, "PM10": 20.0, "PM25": 10.0}

REGION_OCCITANIE = 76.0


def resume(jeu: pd.DataFrame, perimetre: str) -> list[dict]:
    lignes = []
    for polluant, groupe in jeu.groupby("polluant"):
        if polluant not in OMS:
            continue
        m = groupe["moyenne"]
        lignes.append(
            {
                "perimetre": perimetre,
                "polluant": polluant,
                "n_stations": len(groupe),
                "mediane": round(m.median(), 2),
                "q25": round(m.quantile(0.25), 2),
                "q75": round(m.quantile(0.75), 2),
                "maximum": round(m.max(), 2),
                "ligne_oms": OMS[polluant],
                "n_sup_oms": int((m > OMS[polluant]).sum()),
                "part_sup_oms": round((m > OMS[polluant]).mean() * 100, 1),
                "vl_2030": VL_2030[polluant],
                "n_sup_2030": int((m > VL_2030[polluant]).sum()),
                "vl_actuelle": VL_ACTUELLE[polluant],
                "n_sup_actuelle": int((m > VL_ACTUELLE[polluant]).sum()),
            }
        )
    return lignes


def main() -> int:
    if not SOURCE.exists():
        raise SystemExit(f"absent : {SOURCE} — lancer d'abord scripts/seuils_2030.py")

    jeu = pd.read_csv(SOURCE)

    # Contrôle de chargement : exiger nommément les colonnes utilisées (règle 2 bis).
    attendues = {"station_id", "polluant", "moyenne", "region", "departement"}
    if manque := attendues - set(jeu.columns):
        raise SystemExit(f"colonnes absentes de {SOURCE.name} : {sorted(manque)}")
    if jeu["moyenne"].nunique() <= 1:
        raise SystemExit("colonne `moyenne` constante — lecture suspecte")

    occitanie = jeu[jeu["region"] == REGION_OCCITANIE]

    table = pd.DataFrame(resume(jeu, "France") + resume(occitanie, "Occitanie"))
    table.to_csv(CIBLE, index=False)

    # Le périmètre effectif, pas le périmètre demandé (règle 2 quater).
    print(f"France    : {jeu['station_id'].nunique()} stations distinctes")
    print(f"Occitanie : {occitanie['station_id'].nunique()} stations distinctes, "
          f"départements {sorted(occitanie['departement'].astype(str).unique())}")
    print()
    print(table.to_string(index=False))
    print(f"\nÉcrit : {CIBLE.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
