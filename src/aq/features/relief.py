"""Indices topographiques dérivés d'un MNT, pour la dispersion des polluants.

**Pourquoi le relief, et pas seulement l'altitude.** L'altitude brute ne dit pas si une
station est au fond d'une vallée ou sur une crête — or c'est cette position *relative*
qui gouverne la dispersion. Mesuré sur ce projet : les résidus de la LUR ozone sont
corrélés à l'altitude (−0,22), mais Chamonix, fond de vallée à 1035 m, est sur-prédit
de 33 µg/m³. L'altitude seule range Chamonix avec les crêtes alpines, alors que la
physique l'en sépare radicalement — l'air y stagne sous inversion.

**Source : Copernicus DEM GLO-30**, distribué en COG (Cloud Optimized GeoTIFF) sur un
stockage objet public. On lit **la fenêtre utile autour de chaque station**, sans
télécharger la moindre dalle : mesuré à 2,6 s pour 30 km de rayon à 31 m de résolution.
Le RGE ALTI, plus fin (1 m), n'a aucun service OGC et pèse 5,5 Go pour la seule
Occitanie — inutilisable pour un modèle national, et sa finesse ne sert pas ici : le TPI
et la profondeur de vallée se jouent sur des centaines de mètres, pas sur la
microtopographie.
"""

from __future__ import annotations

import numpy as np

URL_GLO30 = (
    "/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM/"
    "Copernicus_DSM_COG_10_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM.tif"
)

# Rayons d'analyse, en mètres. Le TPI dépend entièrement de l'échelle à laquelle on le
# calcule : à 500 m il décrit une butte locale, à 10 km la position dans un bassin.
# Aucune de ces échelles n'est « la bonne » — c'est le modèle qui tranchera.
RAYONS_TPI = (500.0, 2_000.0, 10_000.0)

# Rayon d'analyse de la vallée. Au-delà, on capte le relief régional plutôt que la
# cuvette dans laquelle l'air stagne.
RAYON_VALLEE = 5_000.0


def url_dalle(lon: float, lat: float) -> str:
    """URL de la dalle GLO-30 contenant un point.

    Les dalles couvrent 1° × 1° et sont nommées par le coin **sud-ouest**, d'où le
    `floor` — arrondir au plus proche viserait la mauvaise dalle une fois sur deux,
    et le serveur répondrait 404 plutôt que de livrer un voisin.
    """
    lat_dalle = int(np.floor(lat))
    lon_dalle = int(np.floor(lon))
    return URL_GLO30.format(
        ns="N" if lat_dalle >= 0 else "S",
        lat=abs(lat_dalle),
        ew="E" if lon_dalle >= 0 else "W",
        lon=abs(lon_dalle),
    )


def degres_par_metre(lat: float) -> tuple[float, float]:
    """Taille d'un mètre en degrés de longitude et de latitude, à une latitude donnée.

    La conversion n'est **pas** la même sur les deux axes : un degré de longitude vaut
    111 320 m à l'équateur mais seulement 80 000 m à 45°. Appliquer le facteur des
    latitudes aux longitudes étirerait la fenêtre d'analyse de 40 % en France, et tous
    les indices topographiques seraient calculés sur une emprise déformée.
    """
    metres_par_degre_lat = 111_320.0
    metres_par_degre_lon = 111_320.0 * np.cos(np.radians(lat))
    return 1.0 / metres_par_degre_lon, 1.0 / metres_par_degre_lat


def indice_position_topographique(
    altitudes: np.ndarray, altitude_point: float
) -> float:
    """TPI : altitude du point moins l'altitude moyenne de son voisinage.

    Positif sur une crête, négatif dans une vallée, nul sur un versant régulier ou une
    plaine. C'est la grandeur qui sépare Chamonix des sommets qui l'entourent, là où
    l'altitude brute les confond.
    """
    valides = altitudes[np.isfinite(altitudes)]
    if valides.size == 0:
        return float("nan")
    return float(altitude_point - valides.mean())


def profondeur_vallee(altitudes: np.ndarray, altitude_point: float) -> float:
    """Encaissement : de combien le point est-il dominé par son voisinage.

    On prend le 90ᵉ centile des altitudes environnantes plutôt que le maximum : un seul
    pixel aberrant — antenne, artefact de corrélation stéréo — fixerait sinon à lui seul
    la profondeur de toute une vallée.
    """
    valides = altitudes[np.isfinite(altitudes)]
    if valides.size == 0:
        return float("nan")
    return float(np.percentile(valides, 90) - altitude_point)


def pente_moyenne(altitudes: np.ndarray, pas_m: float) -> float:
    """Pente moyenne du voisinage, en degrés.

    Calculée par gradient sur la grille : une pente forte signale un versant, où l'air
    se draine, par opposition à un fond plat où il s'accumule.
    """
    if altitudes.size < 4 or not np.isfinite(altitudes).any():
        return float("nan")
    dy, dx = np.gradient(np.asarray(altitudes, dtype="float64"), pas_m)
    return float(np.degrees(np.arctan(np.hypot(dx, dy))).mean())


def rugosite(altitudes: np.ndarray) -> float:
    """Écart-type des altitudes du voisinage — mesure du relief local.

    Distingue une plaine (rugosité nulle) d'un relief tourmenté, indépendamment de
    l'altitude absolue.
    """
    valides = altitudes[np.isfinite(altitudes)]
    return float(valides.std()) if valides.size else float("nan")
