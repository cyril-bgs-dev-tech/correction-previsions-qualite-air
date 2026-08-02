#!/usr/bin/env python3
"""Le MQI FAIRMODE calculé au grain que le référentiel définit — et pas un autre.

Le défaut corrigé
-----------------
`aq.eval.comparaison.indice_qualite_modele` applique les paramètres du tableau 6 de
JRC120649 v3.2 à des séries **horaires** pour les trois polluants. Or le document fixe un
temps d'agrégation **par polluant** : NO₂ en horaire, O₃ en **maximum journalier de la
moyenne glissante 8 h**, PM2,5 en **moyenne journalière**. Pour deux des trois, le nombre
publié ne correspond donc à aucune ligne du référentiel, et la mention de conformité sort
du cadre.

Le sens de l'erreur n'est pas neutre : l'agrégation journalière **réduit** la variance de
l'erreur bien plus que celle de l'incertitude de mesure, qui dépend surtout du niveau
observé. Un MQI horaire est donc attendu **plus élevé** — l'erreur allait dans le sens
pessimiste, ce qui explique qu'elle n'ait rien déclenché. Une erreur qui pénalise son auteur
reste une erreur : elle rend l'énoncé de conformité infondé dans les deux sens.

Ce que le script produit
------------------------
Le MQI des trois polluants, au **bon grain**, pour CAMS brut et pour la correction, avec le
MQI horaire en regard pour montrer l'écart. La conformité s'énonce **MQI ≤ 1**.

Usage : python3 scripts/mqi_bon_grain.py
Sortie : reports/mqi_bon_grain.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from cible_journaliere import _agregation, _preparer  # noqa: E402

# Temps d'agrégation imposés par JRC120649 v3.2, tableau 6. Le libellé accompagne la valeur
# pour que la sortie ne puisse pas être relue comme portant sur autre chose.
GRAIN_FAIRMODE = {"O3": ("max_8h", "max journalier 8 h"),
                  "NO2": ("horaire", "horaire"),
                  "PM25": ("moyenne_jour", "moyenne journalière")}
NOM = {"O3": "O₃", "NO2": "NO₂", "PM25": "PM2,5"}


def agreger(d: pd.DataFrame, grandeur: str) -> pd.DataFrame:
    """Passe les trois colonnes au grain demandé, en gardant la règle des 75 %."""
    if grandeur == "horaire":
        return d
    d = d.sort_values(["station_id", "timestamp_utc"]).copy()
    d["jour"] = d["timestamp_utc"].dt.floor("D")
    colonnes = ["observe", "cams", "corrige"]
    for c in colonnes:
        d[c + "_p"] = _preparer(d.groupby("station_id")[c], grandeur)
    agr = _agregation(grandeur)
    j = (d.groupby(["station_id", "jour"])
           .agg(**{c: (c + "_p", agr) for c in colonnes},
                n=("timestamp_utc", "size")).reset_index())
    # 75 % de couples valides dans la journée — la même règle que le référentiel impose
    # pour qu'un maximum journalier soit calculable.
    return j[j["n"] >= 18].dropna(subset=colonnes)


def main() -> int:
    lignes = []
    print(f"{'polluant':8s} {'grain FAIRMODE':22s} {'n':>9s} "
          f"{'MQI CAMS':>9s} {'MQI nous':>9s} │ {'MQI horaire (faux)':>19s}")
    for polluant, (grandeur, libelle) in GRAIN_FAIRMODE.items():
        chemin = RACINE / f"reports/mos_{polluant}_J1.csv"
        if not chemin.exists():
            continue
        d = pd.read_csv(chemin, parse_dates=["timestamp_utc"]).dropna(
            subset=["observe", "cams", "corrige"])

        horaire = {nom: cmp.indice_qualite_modele(d["observe"], d[col], polluant)
                   for nom, col in (("cams", "cams"), ("nous", "corrige"))}
        j = agreger(d, grandeur)
        bon = {nom: cmp.indice_qualite_modele(j["observe"], j[col], polluant)
               for nom, col in (("cams", "cams"), ("nous", "corrige"))}

        print(f"{NOM[polluant]:8s} {libelle:22s} {len(j):>9,} "
              f"{bon['cams']:9.3f} {bon['nous']:9.3f} │ "
              f"{horaire['cams']:8.3f} / {horaire['nous']:<8.3f}", flush=True)
        lignes.append({"polluant": polluant, "grain_fairmode": grandeur, "n": len(j),
                       "mqi_cams": bon["cams"], "mqi_nous": bon["nous"],
                       "mqi_horaire_cams": horaire["cams"],
                       "mqi_horaire_nous": horaire["nous"],
                       "conforme_cams": bon["cams"] <= 1,
                       "conforme_nous": bon["nous"] <= 1})

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / "reports/mqi_bon_grain.csv", index=False)

    print("\n" + "=" * 74)
    print("Conformité FAIRMODE (MQI ≤ 1), au grain du référentiel :")
    for _, r in table.iterrows():
        etat_c = "✅" if r["conforme_cams"] else "❌"
        etat_n = "✅" if r["conforme_nous"] else "❌"
        print(f"  {NOM[r['polluant']]:6s} CAMS brut {etat_c} {r['mqi_cams']:.3f}   "
              f"correction {etat_n} {r['mqi_nous']:.3f}")
    # **Le point à vérifier avant de publier** : un produit qui change de côté du seuil
    # entre les deux grains invalide toute conclusion de conformité déjà écrite.
    bascule = table[(table["mqi_nous"] <= 1) != (table["mqi_horaire_nous"] <= 1)]
    if not bascule.empty:
        print(f"\n⚠️ {len(bascule)} polluant(s) **changent de côté du seuil** entre le grain "
              f"horaire et le grain du référentiel :\n  "
              f"{', '.join(NOM[p] for p in bascule['polluant'])}\n  Toute mention de "
              f"conformité antérieure est à retirer, pas à corriger à la main.")
    else:
        print("\nAucun produit ne change de côté du seuil entre les deux grains : les "
              "conclusions\nde conformité déjà écrites restent valides, même si le chiffre "
              "cité était le mauvais.")
    print(f"\nÉcrit : reports/mqi_bon_grain.csv", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
