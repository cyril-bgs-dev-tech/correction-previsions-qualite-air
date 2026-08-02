"""Métadonnées des stations de mesure — « Dataset D » (LCSQA / Ineris).

Fichier de rapportage réglementaire européen (format AQD), publié sur data.gouv.fr
sans authentification. Il porte les informations indispensables à la modélisation
spatiale : coordonnées, altitude, typologie de zone, classification de station,
et surtout l'historique d'activité qui permet de tracer les ruptures de série.

**Piège vérifié :** le préfixe numérique du code station n'est PAS le département.
`FR34051` est « Chateauroux Sud », à Châteauroux dans l'Indre — pas dans l'Hérault.
Toute sélection régionale doit passer par le réseau exploitant (`BelongsTo`) ou par
une jointure spatiale sur les coordonnées, jamais par le code.
"""

from __future__ import annotations

import io

import pandas as pd
import requests

URL_DATASET_D = (
    "https://static.data.gouv.fr/resources/"
    "donnees-temps-reel-de-mesure-des-concentrations-de-polluants-atmospheriques-reglementes-1/"
    "20251210-084445/fr-2025-d-lcsqa-ineris-20251209.xls"
)

# Réseau de l'AASQA d'Occitanie, vérifié dans la feuille AirQualityNetworks.
RESEAU_OCCITANIE = "NET-FR068A"

# Emprise de la France métropolitaine, Corse comprise.
# Le fichier couvre aussi l'Outre-mer (Réunion, Antilles, Guyane, Mayotte,
# Saint-Martin) : les chiffres nationaux publiés incluent ces stations. Les
# retenir dans un entraînement spatial métropolitain serait contre-productif —
# régime tropical, autres sources, autre chimie —, d'où ce marquage explicite.
EMPRISE_METROPOLE = {"lat": (41.0, 51.5), "lon": (-5.5, 9.7)}

# Les colonnes du format AQD portent des URI de vocabulaire contrôlé Eionet plutôt
# que des libellés : on ne garde que le dernier segment.
COLONNES_VOCABULAIRE = [
    "AreaClassification",
    "StationClassification",
    "AltitudeUnit",
    "MainEmmissionSources",
]


def _dernier_segment(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.rsplit("/", n=1).str[-1]


def telecharger(url: str = URL_DATASET_D, timeout: int = 300) -> bytes:
    reponse = requests.get(url, timeout=timeout)
    reponse.raise_for_status()
    return reponse.content


def lire_stations(contenu: bytes) -> pd.DataFrame:
    """Feuille AirQualityStations → schéma canonique du projet.

    Les stations fermées sont conservées : elles portent l'historique nécessaire à
    l'entraînement, et les exclure biaiserait le jeu vers les stations pérennes.
    Le filtrage sur l'activité se fait au moment de l'usage, pas à l'ingestion.
    """
    brut = pd.read_excel(io.BytesIO(contenu), sheet_name="AirQualityStations")

    df = pd.DataFrame(
        {
            "station_id": brut["EUStationCode"].astype("string"),
            "code_national": brut["NatlStationCode"].astype("string"),
            "nom": brut["Name"].astype("string"),
            "commune": brut["Municipality"].astype("string"),
            "lat_wgs84": pd.to_numeric(brut["Latitude"], errors="coerce"),
            "lon_wgs84": pd.to_numeric(brut["Longitude"], errors="coerce"),
            "altitude": pd.to_numeric(brut["Altitude"], errors="coerce"),
            "typologie_zone": _dernier_segment(brut["AreaClassification"]),
            "reseau": brut["BelongsTo"].astype("string").str.rsplit("/", n=1).str[-1],
            "version": pd.to_numeric(brut["Version"], errors="coerce"),
        }
    )

    # Horodatages porteurs d'un décalage horaire local : on normalise en UTC pour
    # rester cohérent avec la grille temporelle du projet.
    for source, cible in [("ActivityBegin", "date_ouverture"), ("ActivityEnd", "date_fermeture")]:
        df[cible] = pd.to_datetime(brut[source], errors="coerce", utc=True)

    df["active"] = df["date_fermeture"].isna()

    lat_min, lat_max = EMPRISE_METROPOLE["lat"]
    lon_min, lon_max = EMPRISE_METROPOLE["lon"]
    df["metropole"] = df["lat_wgs84"].between(lat_min, lat_max) & df[
        "lon_wgs84"
    ].between(lon_min, lon_max)

    # Le SRS est déclaré ligne par ligne : on refuse de supposer qu'il est homogène.
    srs = brut["SRSName"].astype("string").str.rsplit(":", n=1).str[-1].unique()
    if len(srs) != 1 or srs[0] != "4326":
        raise ValueError(f"Systèmes de coordonnées hétérogènes ou inattendus : {srs}")

    return df


def lire_conditions_emission(contenu: bytes) -> pd.DataFrame:
    """Feuille EmissionConditions → classification par point de prélèvement.

    La classification (fond / trafic / industriel) est portée par le POINT DE
    PRÉLÈVEMENT, pas par la station : une même station peut en principe déclarer
    des conditions différentes selon le polluant. On remonte au niveau station en
    vérifiant explicitement la cohérence plutôt qu'en prenant la première valeur.
    """
    brut = pd.read_excel(io.BytesIO(contenu), sheet_name="EmissionConditions")

    df = pd.DataFrame(
        {
            "point_prelevement": brut["LocalId"].astype("string"),
            "type_station": _dernier_segment(brut["StationClassification"]),
            "source_emission": _dernier_segment(brut["MainEmmissionSources"]),
        }
    )
    df["station_id"] = (
        df["point_prelevement"].str.removeprefix("SPO-").str.rsplit("_", n=1).str[0]
    )
    return df


def type_par_station(conditions: pd.DataFrame) -> pd.DataFrame:
    """Agrège la classification au niveau station, en signalant les incohérences."""
    groupes = conditions.groupby("station_id")["type_station"]
    resume = pd.DataFrame(
        {
            "type_station": groupes.agg(lambda s: s.dropna().mode().iloc[0] if s.notna().any() else pd.NA),
            "n_types_distincts": groupes.nunique(dropna=True),
        }
    )
    return resume.reset_index()


def construire_referentiel(contenu: bytes) -> pd.DataFrame:
    """Référentiel complet : stations enrichies de leur classification."""
    stations = lire_stations(contenu)
    types = type_par_station(lire_conditions_emission(contenu))
    return stations.merge(types, on="station_id", how="left")


def ajouter_lambert93(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les coordonnées projetées en Lambert-93 (EPSG:2154).

    Toute distance du projet se calcule dans ce système. Calculer en degrés
    introduirait une distorsion anisotrope d'environ 27 % à la latitude de
    l'Occitanie, orientée selon l'axe mer/intérieur — précisément celui que les
    variables d'exposition cherchent à exploiter.
    """
    from pyproj import Transformer

    transformateur = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    out = df.copy()
    x, y = transformateur.transform(out["lon_wgs84"].values, out["lat_wgs84"].values)
    out["x_l93"] = x
    out["y_l93"] = y
    return out
