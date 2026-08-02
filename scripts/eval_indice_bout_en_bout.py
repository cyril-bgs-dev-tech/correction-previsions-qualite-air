"""Mesure ce que la correction MOS change sur la **classe d'indice ATMO**, pas sur les
concentrations.

Usage : python scripts/eval_indice_bout_en_bout.py
Sortie : reports/INDICE_BOUT_EN_BOUT.md

**Pourquoi cette évaluation et pas une autre.** Un gain en µg/m³ n'est pas un gain pour
le métier : ce que l'AASQA publie, c'est une *classe* de 1 à 6, et une amélioration de
concentration qui ne fait franchir aucune borne ne change rien à ce qui est affiché. À
l'inverse, une petite erreur près d'une borne fait basculer la couleur. La seule mesure
qui parle est donc l'accord de classe.

**Trois indices sont calculés sur exactement les mêmes règles et les mêmes polluants**,
pour que la comparaison n'attribue à la correction que ce qu'elle fait vraiment :

- `observe` — depuis les concentrations mesurées : la référence de cette évaluation ;
- `cams` — depuis les prévisions brutes ;
- `mos` — depuis les prévisions corrigées.

⚠️ Ce n'est **pas** l'indice officiel publié. Celui-ci est spatialisé par commune puis
par EPCI, à partir d'un modèle méso-échelle, et porte cinq polluants. On mesure ici la
seule chose que la correction peut changer : la classe reconstituée en station, à
polluants constants. L'écart à l'officiel est un autre problème, déjà chiffré dans
`reports/INDICE_ATMO.md`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval import alerte  # noqa: E402
from aq.models import indice_atmo as idx  # noqa: E402

POLLUANTS = ["O3", "NO2", "PM25"]


def charger_predictions() -> pd.DataFrame:
    """Rassemble les sorties MOS des trois polluants en un tableau horaire long."""
    blocs = []
    for polluant in POLLUANTS:
        chemin = RACINE / f"reports/mos_{polluant}_J1.csv"
        if not chemin.exists():
            raise SystemExit(f"{chemin.name} absent — lancer fit_mos.py --polluant "
                             f"{polluant}")
        bloc = pd.read_csv(chemin, parse_dates=["timestamp_utc"])
        bloc["polluant"] = polluant
        blocs.append(bloc)
    return pd.concat(blocs, ignore_index=True)


def indices_journaliers(horaire: pd.DataFrame, colonne: str) -> pd.DataFrame:
    """Passe des concentrations horaires à un indice journalier par station.

    La grandeur retenue diffère selon le polluant — maximum horaire pour les gaz,
    moyenne journalière pour les particules. C'est `aq.models.indice_atmo` qui porte
    cette règle ; la réimplémenter ici la ferait diverger en silence.
    """
    jeu = horaire.rename(columns={colonne: "valeur"})[
        ["station_id", "timestamp_utc", "polluant", "valeur"]
    ]
    sous = idx.sous_indices_journaliers(jeu)
    return idx.indice_par_station(sous)


def accord(reference: pd.DataFrame, candidat: pd.DataFrame, nom: str) -> dict:
    """Compare deux séries d'indices sur les couples (station, jour) communs."""
    fusion = reference.merge(
        candidat, on=["station_id", "jour_local"], suffixes=("_ref", "_cand")
    )
    ecart = fusion["indice_cand"] - fusion["indice_ref"]
    return {
        "modele": nom,
        "n": len(fusion),
        "accord_exact_%": 100 * float((ecart == 0).mean()),
        "a_une_classe_pres_%": 100 * float((ecart.abs() <= 1).mean()),
        "biais_classe": float(ecart.mean()),
        "sous_estime_%": 100 * float((ecart < 0).mean()),
        "sur_estime_%": 100 * float((ecart > 0).mean()),
    }


def main() -> int:
    horaire = charger_predictions()
    print(f"{len(horaire):,} prévisions horaires · "
          f"{horaire['station_id'].nunique()} stations · "
          f"{sorted(horaire['polluant'].unique())}", flush=True)

    indices = {
        nom: indices_journaliers(horaire, colonne)
        for nom, colonne in [("observe", "observe"), ("cams", "cams"),
                             ("mos", "corrige")]
    }

    # Les trois indices doivent porter sur les **mêmes** couples (station, jour) et
    # sur le même nombre de polluants. Sans cette restriction, un modèle serait
    # avantagé par les seuls jours où il dispose de plus de données.
    complets = {
        nom: idx.indice_complet_seulement(table, n_requis=len(POLLUANTS))
        for nom, table in indices.items()
    }
    communs = set.intersection(*[
        set(map(tuple, table[["station_id", "jour_local"]].to_numpy()))
        for table in complets.values()
    ])
    print(f"{len(communs):,} couples (station, jour) complets et communs", flush=True)

    def restreindre(table: pd.DataFrame) -> pd.DataFrame:
        cles = list(map(tuple, table[["station_id", "jour_local"]].to_numpy()))
        return table[[c in communs for c in cles]]

    reference = restreindre(complets["observe"])

    # ── L'arbitrage par bande ────────────────────────────────────────────────────
    #
    # Mesuré le 02/08/2026 (`scripts/arbitrage_par_bande.py`) : **à la classe ≥ 2, la
    # correction est PIRE que CAMS brut** — 10 765 épisodes manqués contre 9 537. Le
    # mécanisme est mécanique : la correction retire un biais positif, donc elle pousse les
    # valeurs vers le bas et fait basculer sous la frontière. Là où CAMS sur-annonçait,
    # sur-annoncer était protecteur.
    #
    # L'aiguillage — publier la correction seulement quand elle prévoit une classe ≥ 2 —
    # rend **−27 % d'épisodes manqués** et **le meilleur accord exact du lot**, gain
    # confirmé sous F₁ et non seulement sous F₂, sur des stations jamais utilisées pour
    # choisir la bascule.
    #
    # ⚠️ **Ne PAS étendre aux classes 3 et 4.** Au seuil *b* lui-même, `arbitrage à ≥b`
    # dégénère en `(mos ≥ b) OU (cams ≥ b)` — l'union des deux détecteurs. Le rappel monte
    # forcément et la précision baisse forcément ; toute métrique privilégiant le rappel
    # récompense ça par construction. Aux classes hautes le gain disparaît sous F₁, voire
    # s'inverse. Seule la classe 2 y échappe, parce que la correction y **nuit réellement** :
    # ce que l'union récupère n'est pas du bruit, c'est ce que la correction avait détruit.
    BASCULE = 2
    # Jointure explicite plutôt qu'un alignement positionnel : deux tables restreintes au
    # même ensemble de clés peuvent ne pas être dans le même ordre, et un désalignement
    # d'index serait ici parfaitement silencieux.
    arbitre = restreindre(complets["mos"]).merge(
        restreindre(complets["cams"])[["station_id", "jour_local", "indice"]]
        .rename(columns={"indice": "indice_cams"}),
        on=["station_id", "jour_local"], how="left", validate="one_to_one")
    if arbitre["indice_cams"].isna().any():
        raise SystemExit(f"{int(arbitre['indice_cams'].isna().sum())} couples sans indice "
                         f"CAMS après jointure — les deux tables ne couvrent pas le même "
                         f"ensemble, l'arbitrage porterait sur un échantillon différent")
    arbitre["indice"] = np.where(arbitre["indice"] >= BASCULE,
                                 arbitre["indice"], arbitre["indice_cams"])
    complets["arbitre"] = arbitre.drop(columns="indice_cams")

    resultats = pd.DataFrame([
        accord(reference, restreindre(complets[nom]), nom)
        for nom in ("cams", "mos", "arbitre")
    ])

    print("\n" + resultats.round(2).to_string(index=False))

    ligne_cams = resultats[resultats["modele"] == "cams"].iloc[0]
    ligne_mos = resultats[resultats["modele"] == "mos"].iloc[0]
    gain = ligne_mos["accord_exact_%"] - ligne_cams["accord_exact_%"]
    print(f"\n→ accord exact : {ligne_cams['accord_exact_%']:.1f} % → "
          f"{ligne_mos['accord_exact_%']:.1f} %  ({gain:+.1f} points)")

    # **La détection compte plus que l'accord moyen.** Un taux d'accord global traite
    # les erreurs symétriquement ; le métier ne l'est pas. On aligne les trois séries
    # sur les mêmes couples avant de comparer, sans quoi les rappels porteraient sur
    # des événements différents.
    def aligner(table: pd.DataFrame) -> pd.DataFrame:
        return restreindre(table).sort_values(
            ["station_id", "jour_local"]
        ).reset_index(drop=True)

    ref_alignee = aligner(complets["observe"])
    detection = alerte.comparer_modeles(
        ref_alignee["indice"],
        {nom: aligner(complets[nom])["indice"] for nom in ("cams", "mos", "arbitre")},
    )

    print("\nDétection par seuil de classe — le rappel d'abord :")
    print(f"  {'seuil':>6s} {'modèle':>6s} {'n':>6s} {'rappel':>7s} "
          f"{'précis.':>7s} {'F₂':>6s} {'manqués':>8s}")
    for _, x in detection.sort_values(["seuil_classe", "modele"]).iterrows():
        print(f"  {'≥' + str(int(x['seuil_classe'])):>6s} {x['modele']:>6s} "
              f"{int(x['n_evenements']):>6,} {x['rappel']:7.3f} "
              f"{x['precision']:7.3f} {x['f2']:6.3f} "
              f"{int(x['faux_negatifs']):>8,}")

    dominants = reference["polluant_responsable"].value_counts(normalize=True) * 100
    print("\nPolluant qui impose l'indice (référence observée) :")
    for polluant, part in dominants.items():
        print(f"  {polluant:6s} {part:5.1f} %")

    detection.to_csv(RACINE / "reports/indice_detection.csv", index=False)
    ecrire_rapport(resultats, reference, len(communs), detection)
    return 0


def ecrire_rapport(resultats: pd.DataFrame, reference: pd.DataFrame,
                   n_couples: int, detection: pd.DataFrame) -> None:
    cams = resultats[resultats["modele"] == "cams"].iloc[0]
    mos = resultats[resultats["modele"] == "mos"].iloc[0]
    dominants = reference["polluant_responsable"].value_counts(normalize=True) * 100

    lignes_detection = "\n".join(
        f"| ≥{int(x['seuil_classe'])} | {x['modele']} | {int(x['n_evenements']):,} | "
        f"**{x['rappel']:.3f}** | {x['precision']:.3f} | {x['f2']:.3f} | "
        f"{int(x['faux_negatifs']):,} |"
        for _, x in detection.sort_values(["seuil_classe", "modele"]).iterrows()
    )

    texte = f"""# Ce que la correction change sur la **classe d'indice**

Un gain en µg/m³ n'est pas un gain pour le métier. Ce qu'une AASQA publie est une classe
de 1 à 6 : une amélioration de concentration qui ne fait franchir aucune borne ne change
rien à l'affichage, tandis qu'une petite erreur près d'une borne fait basculer la
couleur. La seule mesure qui parle est donc **l'accord de classe**.

Comparaison à règles et polluants **identiques** ({', '.join(POLLUANTS)}), sur
{n_couples:,} couples (station, jour) où les trois indices sont calculables.

| | Accord exact | À une classe près | Biais de classe |
|---|---|---|---|
| **CAMS brut** | {cams['accord_exact_%']:.1f} % | {cams['a_une_classe_pres_%']:.1f} % | {cams['biais_classe']:+.3f} |
| **MOS corrigé** | {mos['accord_exact_%']:.1f} % | {mos['a_une_classe_pres_%']:.1f} % | {mos['biais_classe']:+.3f} |

**Gain : {mos['accord_exact_%'] - cams['accord_exact_%']:+.1f} points d'accord exact.**

## Détection des épisodes — le critère qui décide

Un taux d'accord traite les erreurs symétriquement. Le métier ne l'est pas : ne pas
annoncer un épisode qui survient expose la population et engage la responsabilité de
l'AASQA, alors qu'une fausse alerte coûte de la crédibilité. L'arrêté du 07/04/2016
consacre d'ailleurs cette asymétrie en autorisant le déclenchement **sur prévision**.

Le F₂ pondère le rappel quatre fois plus que la précision.

| Seuil | Modèle | n | Rappel | Précision | F₂ | Épisodes manqués |
|---|---|---|---|---|---|---|
{lignes_detection}

## Polluant qui impose l'indice, sur les concentrations observées

{chr(10).join(f"- **{p}** : {v:.1f} %" for p, v in dominants.items())}

## ⚠️ Ce que cette mesure n'est pas

- **Ce n'est pas l'indice officiel publié.** Celui-ci est modélisé et spatialisé par
  commune puis agrégé à l'EPCI, et porte **cinq** polluants (PM10 et SO2 en plus). Il est
  ici reconstitué **en station**, sur trois polluants. L'écart à l'officiel est un autre
  problème, chiffré dans `reports/INDICE_ATMO.md` : 42,8 % d'accord et −0,72 classe de
  biais, dus à la spatialisation.
- **Ce n'est pas le système d'ATMO.** CAMS Europe (0,1°, ~8 × 11 km) n'est pas PREV'AIR
  (CHIMERE + MOCAGE, ~2 km), qui est la chaîne réellement employée. On mesure une chaîne
  opérationnelle de même nature, pas la leur.
- La référence est l'indice **calculé depuis les mesures**, pas l'indice publié. C'est ce
  qui isole l'apport de la correction du problème de spatialisation.
"""
    (RACINE / "reports/INDICE_BOUT_EN_BOUT.md").write_text(texte)
    print("\nÉcrit : reports/INDICE_BOUT_EN_BOUT.md")


if __name__ == "__main__":
    raise SystemExit(main())
