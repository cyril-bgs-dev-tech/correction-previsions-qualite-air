"""Échantillonnage des champs Copernicus aux coordonnées des stations.

Un champ ERA5 ou CAMS est une grille ; une station est un point. Passer de l'un à
l'autre paraît trivial et concentre en réalité trois erreurs silencieuses, toutes
neutralisées ici :

1. **Les conventions d'axes diffèrent entre les deux services** — longitudes en
   [0, 360] et non monotones côté CAMS, latitudes décroissantes des deux côtés. Voir
   `copernicus.normaliser_longitudes`.
2. **`method="nearest"` ne signale pas qu'un point est hors domaine** : il rabat sur
   la cellule de bord et renvoie une valeur parfaitement plausible. Une station hors
   emprise recevrait la météo d'un autre lieu, sans le moindre avertissement.
3. **Les unités natives ne sont pas celles du métier** : kelvins, pascals, mètres de
   pluie, joules par mètre carré. Les laisser telles quelles ne casse rien — cela rend
   seulement les coefficients ininterprétables et les seuils faux.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from aq.harmonize import wind
from aq.ingest import copernicus

# Tolérance de rattachement, en nombre de mailles. La grille ERA5 fait 0,25° (~28 km à
# 45° de latitude) : une station à plus d'une maille du centre le plus proche est hors
# domaine, et `nearest` l'aurait rabattue sur le bord sans le dire.
TOLERANCE_MAILLES = 1.0

# Conversions vers les unités du métier. La clé est le nom court ERA5.
CONVERSIONS = {
    "t2m": ("temperature_c", lambda v: v - 273.15),
    "d2m": ("point_rosee_c", lambda v: v - 273.15),
    "sp": ("pression_hpa", lambda v: v / 100.0),
    "blh": ("couche_limite_m", lambda v: v),
    # `tp` est un cumul en MÈTRES sur l'heure écoulée, pas un taux instantané.
    "tp": ("precipitation_mm", lambda v: v * 1000.0),
    # `ssrd` est un cumul en J/m² sur l'heure écoulée ; divisé par 3600 s il redevient
    # un flux moyen en W/m², la grandeur que lit un physicien de l'atmosphère.
    "ssrd": ("rayonnement_w_m2", lambda v: v / 3600.0),
}


def _pas_de_grille(valeurs: np.ndarray) -> float:
    """Pas moyen d'un axe régulier, en degrés."""
    return float(np.abs(np.diff(np.asarray(valeurs, dtype="float64"))).mean())


def controler_couverture(jeu, lon, lat) -> None:
    """Vérifie que chaque point tombe réellement dans le domaine.

    Sans ce contrôle, une station hors emprise est rabattue sur la cellule de bord :
    elle reçoit une météo cohérente, continue, et fausse. Le cas est loin d'être
    théorique — Brest est à −4,49° de longitude, à 0,5° seulement du bord ouest de
    l'emprise France, et la Corse déborde à l'est de bien des emprises « France ».
    """
    nom_lon = "longitude" if "longitude" in jeu.coords else "lon"
    nom_lat = "latitude" if "latitude" in jeu.coords else "lat"
    axe_lon = jeu[nom_lon].values
    axe_lat = jeu[nom_lat].values

    marge_lon = TOLERANCE_MAILLES * _pas_de_grille(axe_lon)
    marge_lat = TOLERANCE_MAILLES * _pas_de_grille(axe_lat)

    hors = (
        (lon < axe_lon.min() - marge_lon) | (lon > axe_lon.max() + marge_lon)
        | (lat < axe_lat.min() - marge_lat) | (lat > axe_lat.max() + marge_lat)
    )
    if hors.any():
        raise ValueError(
            f"{int(hors.sum())} point(s) hors du domaine "
            f"[{axe_lon.min():.2f}, {axe_lon.max():.2f}] x "
            f"[{axe_lat.min():.2f}, {axe_lat.max():.2f}] — "
            "`nearest` les rabattrait silencieusement sur le bord. "
            "Élargir l'emprise de téléchargement plutôt que de les laisser passer."
        )


def extraire_aux_stations(
    chemin: str,
    stations: pd.DataFrame,
    colonne_lon: str = "lon_wgs84",
    colonne_lat: str = "lat_wgs84",
) -> pd.DataFrame:
    """Échantillonne un fichier Copernicus aux coordonnées des stations.

    Renvoie un tableau long : une ligne par (station, échéance), une colonne par
    variable, dans les unités du métier.

    Le plus proche voisin est préféré à une interpolation bilinéaire : les champs de
    couche limite et de précipitation sont discontinus par nature, et lisser entre
    mailles inventerait des valeurs intermédiaires que la physique ne produit pas.
    """
    import xarray as xr

    lon = stations[colonne_lon].to_numpy(dtype="float64")
    lat = stations[colonne_lat].to_numpy(dtype="float64")

    with xr.open_dataset(chemin) as brut:
        # On convertit les longitudes SANS trier le champ. Trier une grille CAMS, dont
        # l'axe arrive non monotone, réordonne tout le tableau de données : mesuré à
        # 52 s par journée de prévision, contre 0,7 s pour un mois entier d'ERA5 déjà
        # trié. Le rattachement par indices entiers donne le même résultat sans jamais
        # déplacer une donnée.
        # **Charger avant d'indexer, pas l'inverse.** Les indices des stations sont
        # désordonnés par nature ; sur un champ resté paresseux, le backend netCDF4
        # renonce à la lecture par hyperslab et lit point par point — mesuré à 52,5 s
        # pour une journée de prévisions CAMS, contre 0,04 s pour charger le champ
        # entier puis l'indexer en mémoire. Un membre pèse quelques mégaoctets : il n'y
        # a rien à économiser en restant paresseux.
        jeu = copernicus.normaliser_longitudes(brut, trier=False).load()
        controler_couverture(jeu, lon, lat)

        nom_lon = "longitude" if "longitude" in jeu.coords else "lon"
        nom_lat = "latitude" if "latitude" in jeu.coords else "lat"
        indexeurs = {
            nom_lon: xr.DataArray(
                indices_plus_proches(jeu[nom_lon].values, lon), dims="station"
            ),
            nom_lat: xr.DataArray(
                indices_plus_proches(jeu[nom_lat].values, lat), dims="station"
            ),
        }
        echantillon = jeu.isel(**indexeurs).load()

    echantillon = echantillon.assign_coords(
        station=("station", stations["station_id"].to_numpy())
    )
    tableau = echantillon.to_dataframe().reset_index()
    return convertir_unites(_normaliser_colonnes(tableau, chemin, jeu))


def indices_plus_proches(axe: np.ndarray, valeurs: np.ndarray) -> np.ndarray:
    """Indice de la maille la plus proche, pour chaque valeur demandée.

    Fait à la main plutôt que par `sel(method="nearest")` pour deux raisons : cela
    fonctionne sur un axe **non monotone** — le cas des grilles CAMS à cheval sur
    Greenwich — et cela n'oblige pas à trier le champ au préalable.
    """
    axe = np.asarray(axe, dtype="float64")
    valeurs = np.asarray(valeurs, dtype="float64")
    return np.abs(axe[None, :] - valeurs[:, None]).argmin(axis=1)


def date_base_prevision(chemin: str | Path,
                        jeu=None) -> pd.Timestamp | None:
    """Date de base d'une prévision CAMS — **dans le fichier d'abord, le nom ensuite**.

    Deux conventions coexistent, et l'ordre entre elles n'est pas indifférent :

    * les fichiers **journaliers** `ENS_FORECAST_AAAA-MM-JJ.nc` ne portent la date que
      dans leur nom — à l'intérieur, `time` ne compte que l'échéance, de 0 à 72 h ;
    * les fichiers **mensuels** de spéciation la portent dans l'attribut
      ``time.long_name`` — ``"FORECAST time from 20250101"`` — et leur nom ne dit que le
      mois.

    On lit donc **l'attribut en premier**. C'est la § 4 bis appliquée à la lettre : *un nom
    de fichier n'est pas une source de vérité*, et quand la donnée porte l'information,
    c'est elle qui fait foi. L'inverse a coûté une passe le 16/08 — l'extraction refusait
    un fichier dont la date de base était pourtant écrite trois octets plus loin.
    """
    if jeu is not None and "time" in getattr(jeu, "coords", {}):
        trouve = re.search(r"from\s*(\d{4})(\d{2})(\d{2})",
                           str(jeu["time"].attrs.get("long_name", "")))
        if trouve:
            return pd.Timestamp("-".join(trouve.groups()), tz="UTC")
    trouve = re.search(r"(\d{4})-(\d{2})-(\d{2})", Path(chemin).name)
    if not trouve:
        return None
    return pd.Timestamp("-".join(trouve.groups()), tz="UTC")


# Coordonnées dégénérées des fichiers ERA5 : `number` vaut 0 (membre unique de la
# réanalyse) et `expver` distingue les flux définitif et provisoire. Constantes ici,
# elles n'apportent rien et brouillent les jointures.
COORDONNEES_INUTILES = ("number", "expver")

RENOMMAGES = {
    "station": "station_id",
    # Aligné sur le panneau de mesures (`timestamp_utc`) : ERA5 est en UTC, comme les
    # données EEA. Une jointure sur des noms différents passerait par un renommage
    # implicite, c'est-à-dire par une occasion de se tromper de fuseau.
    "valid_time": "timestamp_utc",
    # Coordonnées de la MAILLE retenue, pas de la station : les garder permet de
    # vérifier après coup à quelle distance le rattachement s'est fait.
    "latitude": "maille_lat",
    "longitude": "maille_lon",
}


def _normaliser_colonnes(tableau: pd.DataFrame, chemin: str | Path,
                         jeu=None) -> pd.DataFrame:
    """Uniformise les colonnes, et surtout rétablit le temps absolu des prévisions.

    **Le piège que ce code existe pour éviter.** Dans un membre CAMS, la coordonnée
    `time` vaut 0, 1, … 72 : c'est l'**échéance en heures**, pas une date. La passer à
    `pd.to_datetime` produit `1970-01-01 + 72 nanosecondes` — une colonne d'apparence
    parfaitement valide, ordonnée, sans valeur manquante, et fausse de cinquante-cinq
    ans. La date de base ne vit que dans le nom du fichier.
    """
    tableau = tableau.drop(columns=list(COORDONNEES_INUTILES), errors="ignore")
    tableau = tableau.rename(columns=RENOMMAGES)

    if "time" in tableau.columns:
        est_horodatage = pd.api.types.is_datetime64_any_dtype(tableau["time"])
        if est_horodatage:
            tableau = tableau.rename(columns={"time": "timestamp_utc"})
        else:
            base = date_base_prevision(chemin, jeu)
            if base is None:
                raise ValueError(
                    f"{Path(chemin).name} : la coordonnée `time` porte des échéances "
                    "et non des dates, et le nom du fichier ne contient aucune date de "
                    "base. Impossible de reconstituer un temps absolu — refuser vaut "
                    "mieux que produire des horodatages de 1970."
                )
            tableau["echeance_h"] = tableau.pop("time").astype("int64")
            tableau["timestamp_utc"] = base + pd.to_timedelta(
                tableau["echeance_h"], unit="h"
            )

    if "timestamp_utc" in tableau.columns:
        horodatage = pd.to_datetime(tableau["timestamp_utc"])
        # ERA5 livre des horodatages naïfs, qui sont en UTC. Les laisser naïfs les
        # rendrait incomparables au panneau, lui explicitement UTC — et pandas
        # refuserait la jointure, ou pire, l'accepterait après une conversion locale.
        tableau["timestamp_utc"] = (
            horodatage.dt.tz_localize("UTC") if horodatage.dt.tz is None
            else horodatage.dt.tz_convert("UTC")
        )
    return tableau


def convertir_unites(tableau: pd.DataFrame) -> pd.DataFrame:
    """Traduit les noms courts ERA5 et leurs unités natives vers le vocabulaire métier.

    Les colonnes inconnues sont laissées intactes : c'est le cas des espèces CAMS, déjà
    livrées en µg/m³.
    """
    tableau = tableau.copy()
    for court, (nom, convertir) in CONVERSIONS.items():
        if court in tableau.columns:
            tableau[nom] = convertir(tableau.pop(court))

    if {"u10", "v10"}.issubset(tableau.columns):
        direction, vitesse = wind.uv_vers_direction_vitesse(
            tableau.pop("u10"), tableau.pop("v10")
        )
        # La direction est conservée telle quelle, jamais moyennée comme un nombre :
        # toute agrégation ultérieure doit repasser par les composantes.
        tableau["vent_direction_deg"] = direction
        tableau["vent_vitesse_m_s"] = vitesse

    return tableau
