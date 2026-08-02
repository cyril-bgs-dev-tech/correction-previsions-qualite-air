"""Indice ATMO — calcul réglementaire.

Référence : arrêté du 10 juillet 2020 (JO n°185 du 29/07/2020), guide de calcul
Atmo France du 14/12/2020. Valeurs reprises de `REGLEMENTAIRE.md` §1.

**Ce module ne reproduit qu'une partie de la chaîne officielle**, et il faut être
clair sur laquelle.

L'indice publié n'est **pas** calculé depuis les stations : il provient d'une
modélisation méso-échelle spatialisée — maximum modélisé par commune, puis maximum
communal pour l'EPCI —, les mesures ne servant qu'en assimilation ou à défaut, et
seules les stations **de fond** y entrent.

Ce module couvre donc :
  ✅ le calcul des sous-indices à partir d'une concentration (déterministe, exact) ;
  ✅ la règle d'agrégation (le pire des sous-indices) ;
  ✅ les règles de grandeur par polluant (moyenne journalière ou maximum horaire) ;
  ❌ la spatialisation, qui exige leur modèle.

Un écart avec l'indice publié est donc **attendu par construction**. L'exercice
consiste à mesurer cet écart, pas à le faire disparaître.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Bornes SUPÉRIEURES de chaque classe, en µg/m³ (arrêté du 10/07/2020).
# La classe 6 (« Extrêmement mauvais ») est ouverte vers le haut.
BORNES = {
    "PM25": [10, 20, 25, 50, 75],
    "PM10": [20, 40, 50, 100, 150],
    "NO2": [40, 90, 120, 230, 340],
    "O3": [50, 100, 130, 240, 380],
    "SO2": [100, 200, 350, 500, 750],
}

# Grandeur retenue par polluant : les particules sur la moyenne journalière,
# les gaz sur le maximum horaire du jour. Confondre les deux fait basculer de
# plusieurs classes — un maximum horaire de NO₂ dépasse largement sa moyenne.
GRANDEUR = {
    "PM25": "moyenne_journaliere",
    "PM10": "moyenne_journaliere",
    "NO2": "max_horaire",
    "O3": "max_horaire",
    "SO2": "max_horaire",
}

QUALIFICATIFS = {
    1: "Bon",
    2: "Moyen",
    3: "Dégradé",
    4: "Mauvais",
    5: "Très mauvais",
    6: "Extrêmement mauvais",
}

COULEURS = {
    1: "#50F0E6",
    2: "#50CCAA",
    3: "#F0E641",
    4: "#FF5050",
    5: "#960032",
    6: "#872181",
    0: "#DDDDDD",  # indisponible
    7: "#888888",  # événement
}


def sous_indice(concentration, polluant: str) -> np.ndarray:
    """Classe 1 à 6 d'un polluant à partir de sa concentration.

    **Les bornes de l'arrêté sont des entiers avec discontinuité apparente** (0-10
    puis 11-20). Elles s'appliquent donc à des concentrations **arrondies à l'entier**,
    et non aux valeurs brutes : sans arrondi, 10,4 µg/m³ ne tomberait dans aucune
    classe. On arrondit d'abord, puis on classe sur la borne supérieure incluse.

    C'est exactement le genre de détail qui décide si un recalcul tombe juste.
    """
    if polluant not in BORNES:
        raise ValueError(f"Polluant hors indice ATMO : {polluant}")

    valeurs = np.asarray(concentration, dtype="float64")
    arrondies = np.round(valeurs)

    # searchsorted avec 'left' place une valeur ÉGALE à une borne dans la classe
    # inférieure — conforme à « 0-10 = Bon », où 10 appartient bien à Bon.
    classes = np.searchsorted(BORNES[polluant], arrondies, side="left") + 1
    return np.where(np.isnan(valeurs), np.nan, classes)


def sous_indices_journaliers(
    panneau: pd.DataFrame, couverture_min: float = 0.75
) -> pd.DataFrame:
    """Sous-indice quotidien par station et polluant, en jour local.

    La grandeur dépend du polluant (§ GRANDEUR). Un jour dont la couverture est
    insuffisante ne reçoit pas d'indice : le forcer donnerait un indice flatteur,
    puisque les heures manquantes ne sont pas indépendantes des épisodes.
    """
    df = panneau.copy()
    local = df["timestamp_utc"].dt.tz_convert("Europe/Paris")
    df["jour_local"] = local.dt.date

    groupes = df.groupby(["station_id", "polluant", "jour_local"], observed=True)
    agrege = groupes.agg(
        moyenne_journaliere=("valeur", "mean"),
        max_horaire=("valeur", "max"),
        n_valides=("valeur", "count"),
        n_heures=("valeur", "size"),
    ).reset_index()

    agrege["couverture"] = agrege["n_valides"] / agrege["n_heures"]
    agrege = agrege[agrege["polluant"].isin(BORNES)]

    agrege["grandeur_retenue"] = [
        ligne["moyenne_journaliere"]
        if GRANDEUR[ligne["polluant"]] == "moyenne_journaliere"
        else ligne["max_horaire"]
        for _, ligne in agrege.iterrows()
    ]
    agrege.loc[agrege["couverture"] < couverture_min, "grandeur_retenue"] = np.nan

    agrege["sous_indice"] = [
        float(sous_indice(v, p)) if pd.notna(v) else np.nan
        for v, p in zip(agrege["grandeur_retenue"], agrege["polluant"])
    ]
    return agrege


def indice_par_station(sous_indices: pd.DataFrame) -> pd.DataFrame:
    """Agrège les sous-indices en indice quotidien — le PIRE des sous-indices.

    Le polluant responsable est conservé : c'est l'information utile pour
    l'interprétation et la communication, et elle disparaîtrait d'un simple maximum.
    """
    valides = sous_indices.dropna(subset=["sous_indice"])
    if valides.empty:
        return pd.DataFrame()

    idx = valides.groupby(["station_id", "jour_local"], observed=True)[
        "sous_indice"
    ].idxmax()
    resultat = valides.loc[idx, ["station_id", "jour_local", "polluant", "sous_indice"]]
    resultat = resultat.rename(
        columns={"polluant": "polluant_responsable", "sous_indice": "indice"}
    )

    n_polluants = (
        valides.groupby(["station_id", "jour_local"], observed=True)["polluant"]
        .nunique()
        .rename("n_polluants")
        .reset_index()
    )
    resultat = resultat.merge(n_polluants, on=["station_id", "jour_local"])

    resultat["indice"] = resultat["indice"].astype(int)
    resultat["qualificatif"] = resultat["indice"].map(QUALIFICATIFS)
    resultat["couleur"] = resultat["indice"].map(COULEURS)
    return resultat.reset_index(drop=True)


def indice_complet_seulement(indices: pd.DataFrame, n_requis: int = 5) -> pd.DataFrame:
    """Ne conserve que les jours où les 5 sous-indices sont disponibles.

    Un indice calculé sur deux polluants n'est pas comparable à l'indice officiel :
    le maximum d'un sous-ensemble est nécessairement inférieur ou égal à celui de
    l'ensemble complet. Ignorer ce point produirait un **biais optimiste
    systématique** — et donnerait l'illusion d'un air meilleur qu'il n'est.
    """
    return indices[indices["n_polluants"] >= n_requis]
