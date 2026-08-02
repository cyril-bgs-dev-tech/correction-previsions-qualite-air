"""Indice ATMO officiel publié par Atmo Occitanie (portail ArcGIS, accès libre).

Ce jeu est précieux pour deux raisons distinctes.

1. Il expose **les cinq sous-indices en clair**, pas seulement l'indice agrégé. On
   peut donc vérifier la règle d'agrégation — « le pire des sous-indices » — sur des
   données officielles, **sans avoir besoin de leur modèle de spatialisation**. C'est
   une vérification exacte, contrairement à la comparaison des concentrations.

2. Il est publié à la maille **EPCI**, avec le libellé et les coordonnées de la zone.
   La comparaison avec un indice calculé en station mesure alors précisément l'écart
   dû à la spatialisation — la partie de la chaîne officielle qu'on ne peut pas
   reproduire.

Accès libre, sans authentification — contrairement à l'API Atmo France, qui exige un
jeton et ne sert de toute façon pas les concentrations.
"""

from __future__ import annotations

import pandas as pd
import requests

SERVICE = (
    "https://services9.arcgis.com/7Sr9Ek9c1QTKmbwr/arcgis/rest/services/"
    "Indice_quotidien_de_qualit%C3%A9_de_l%E2%80%99air_pour_les_collectivit%C3%A9s_"
    "territoriales_en_Occitanie/FeatureServer/0"
)

COLONNES_SOUS_INDICES = ["code_no2", "code_so2", "code_o3", "code_pm10", "code_pm25"]

# Correspondance avec les noms canoniques du projet.
VERS_POLLUANT = {
    "code_no2": "NO2",
    "code_so2": "SO2",
    "code_o3": "O3",
    "code_pm10": "PM10",
    "code_pm25": "PM25",
}


def telecharger(
    taille_page: int = 2000, max_enregistrements: int = 200_000, timeout: int = 120
) -> pd.DataFrame:
    """Récupère tout le jeu, en paginant.

    La pagination est explicite : le service plafonne les réponses et **tronque en
    silence** au-delà. Sans `exceededTransferLimit`, on croirait avoir tout reçu.
    """
    lignes: list[dict] = []
    depart = 0

    while len(lignes) < max_enregistrements:
        reponse = requests.get(
            f"{SERVICE}/query",
            params={
                "where": "1=1",
                "outFields": "*",
                "resultOffset": depart,
                "resultRecordCount": taille_page,
                "f": "json",
            },
            timeout=timeout,
        )
        reponse.raise_for_status()
        charge = reponse.json()
        lot = charge.get("features", [])
        if not lot:
            break
        lignes += [entite["attributes"] for entite in lot]
        if len(lot) < taille_page and not charge.get("exceededTransferLimit"):
            break
        depart += taille_page

    return _normaliser(pd.DataFrame(lignes))


def _normaliser(brut: pd.DataFrame) -> pd.DataFrame:
    if brut.empty:
        return brut

    df = brut.copy()
    # Horodatages ArcGIS : millisecondes depuis l'époque, en UTC. L'échéance désigne
    # une JOURNÉE, on la ramène donc à une date locale plutôt qu'à un instant.
    for source, cible in [("date_ech", "jour_local"), ("date_dif", "date_diffusion")]:
        if source in df.columns:
            horodatage = pd.to_datetime(df[source], unit="ms", utc=True)
            df[cible] = (
                horodatage.dt.tz_convert("Europe/Paris").dt.date
                if cible == "jour_local"
                else horodatage
            )

    # Le code 0 signifie « indisponible » et le 7 « événement » : ce ne sont pas des
    # classes de qualité, les traiter comme telles fausserait toute comparaison.
    for colonne in ["code_qual", *COLONNES_SOUS_INDICES]:
        if colonne in df.columns:
            df[colonne] = df[colonne].where(df[colonne].between(1, 6))

    return df


def verifier_regle_agregation(indices: pd.DataFrame) -> pd.DataFrame:
    """Confronte l'indice publié au maximum de ses propres sous-indices.

    C'est la seule vérification **exacte** possible sans le modèle de spatialisation :
    on n'interroge pas la valeur des sous-indices, seulement la règle qui les combine.
    Les lignes dont un sous-indice manque sont écartées — le maximum d'un
    sous-ensemble est nécessairement ≤ celui de l'ensemble, et les inclure produirait
    de faux écarts.
    """
    df = indices.dropna(subset=["code_qual", *COLONNES_SOUS_INDICES]).copy()
    df["max_sous_indices"] = df[COLONNES_SOUS_INDICES].max(axis=1)
    df["conforme"] = df["code_qual"] == df["max_sous_indices"]
    df["polluant_responsable"] = (
        df[COLONNES_SOUS_INDICES].idxmax(axis=1).map(VERS_POLLUANT)
    )
    return df


def en_format_long(indices: pd.DataFrame) -> pd.DataFrame:
    """Passe les sous-indices en colonnes vers un format long, comparable au nôtre."""
    return (
        indices.melt(
            id_vars=["jour_local", "code_zone", "lib_zone", "type_zone"],
            value_vars=COLONNES_SOUS_INDICES,
            var_name="colonne",
            value_name="sous_indice_officiel",
        )
        .assign(polluant=lambda d: d["colonne"].map(VERS_POLLUANT))
        .drop(columns="colonne")
        .dropna(subset=["sous_indice_officiel"])
    )
