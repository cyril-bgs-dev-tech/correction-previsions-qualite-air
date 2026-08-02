"""Client WFS de la Géoplateforme IGN — extraction d'emprises réduites.

**Pourquoi le WFS plutôt que le téléchargement départemental.** Les archives couvrant
les 13 départements d'Occitanie pèsent ~10,1 Go (BD Forêt 535 Mo, BD TOPO 4,0 Go,
RGE ALTI 5,5 Go). Or les variables d'exposition ne s'évaluent qu'**autour des stations** :
interroger un disque de quelques dizaines de kilomètres autour de 38 points est de
plusieurs ordres de grandeur plus économique, et donne exactement la même information.

Le RGE ALTI fait exception : **aucun service OGC ne l'expose** (WFS et WCS testés,
respectivement absent et 404). Le relief impose donc le téléchargement départemental.

**Deux pièges vérifiés par test :**

- En `EPSG:4326`, ce serveur attend l'ordre **`lon,lat`**, contrairement à l'ordre
  officiel de WFS 2.0 pour ce système. L'ordre inverse renvoie **HTTP 200 avec zéro
  entité** — aucune erreur, juste un résultat vide. On travaille donc directement en
  Lambert-93, ce qui supprime le problème et évite une reprojection.
- Le service applique une **limitation de débit** (en-têtes `ratelimit-limit: 10`,
  `x-ratelimit-limit-second: 1`).
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import requests
from shapely.geometry import shape

WFS_URL = "https://data.geopf.fr/wfs/ows"
CRS_CALCUL = "EPSG:2154"

# Plafond réel du service, mesuré : une requête à 10 000 renvoie 5 000 entités sans
# le signaler. Demander davantage tronque donc en SILENCE — et une forêt manquante ne
# se voit dans aucune variable d'exposition.
TAILLE_PAGE = 5000

# Concurrence sur les pages d'une même couche. Le service annonce ses limites par les
# en-têtes `ratelimit-limit: 10` et `x-ratelimit-limit-second: 1` : on reste en deçà.
PAGES_PARALLELES = 4

# Couches vérifiées accessibles en WFS (test réel, HTTP 200 avec entités).
COUCHES = {
    # BD Forêt V2 — l'attribut `essence` porte le potentiel d'émission d'isoprène :
    # les feuillus (chênes en particulier) sont de gros émetteurs, les conifères non.
    "foret": "LANDCOVER.FORESTINVENTORY.V2:formation_vegetale",
    "route": "BDTOPO_V3:troncon_de_route",
    "batiment": "BDTOPO_V3:batiment",
    "cours_eau": "BDTOPO_V3:cours_d_eau",
    # Repli pour le trait de côte : HISTOLITT (SHOM) n'est pas téléchargeable
    # automatiquement — distribution par boutique avec panier. Cette couche est
    # moins spécialisée mais librement et immédiatement accessible.
    "trait_cote": "BDTOPO_V3:limite_terre_mer",
}


@dataclass(frozen=True)
class Entite:
    """Entité géographique réduite à ce dont les variables d'exposition ont besoin."""

    x: float          # centroïde, Lambert-93
    y: float
    masse: float      # surface (m²) pour un polygone, longueur (m) pour une ligne
    proprietes: dict


def _bbox_autour(x: float, y: float, rayon_m: float) -> str:
    """Emprise carrée en Lambert-93, exprimée dans l'ordre attendu par le service."""
    return f"{x - rayon_m},{y - rayon_m},{x + rayon_m},{y + rayon_m},{CRS_CALCUL}"


def _parametres(nom_couche: str, bbox: str) -> dict:
    return {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": nom_couche,
        "SRSNAME": CRS_CALCUL,
        "BBOX": bbox,
    }


def compter(couche: str, x: float, y: float, rayon_m: float, timeout: int = 60) -> int:
    """Nombre d'entités dans l'emprise, sans les télécharger (`RESULTTYPE=hits`).

    Réponse en ~0,3 s pour quelques centaines d'octets. Connaître le total d'avance
    permet de charger toutes les pages **en parallèle**, au lieu de les enchaîner en
    attendant de découvrir qu'il en reste une.
    """
    parametres = _parametres(COUCHES.get(couche, couche), _bbox_autour(x, y, rayon_m))
    parametres["RESULTTYPE"] = "hits"
    reponse = requests.get(WFS_URL, params=parametres, timeout=timeout)
    reponse.raise_for_status()
    trouve = re.search(r'numberMatched="(\d+)"', reponse.text)
    return int(trouve.group(1)) if trouve else 0


def interroger(
    couche: str,
    x: float,
    y: float,
    rayon_m: float,
    max_entites: int = 100_000,
    timeout: int = 180,
) -> list[Entite]:
    """Récupère les entités d'une couche dans un disque autour d'un point.

    L'emprise interrogée est un carré circonscrit : on récupère un peu plus que le
    disque, sans conséquence puisque la pondération par distance fait décroître la
    contribution des objets éloignés.

    Le total est d'abord obtenu par `RESULTTYPE=hits`, puis les pages sont chargées
    **en parallèle**. Sur une emprise typique de 60 km, cela ramène une vingtaine de
    requêtes séquentielles à trois requêtes simultanées.
    """
    nom_couche = COUCHES.get(couche, couche)
    bbox = _bbox_autour(x, y, rayon_m)

    disponible = compter(couche, x, y, rayon_m, timeout=60)
    if disponible == 0:
        return []
    if disponible > max_entites:
        # Tronquer en silence serait le pire des comportements : l'ordre du service
        # n'est pas spatial, on obtiendrait un sous-ensemble arbitraire, et une forêt
        # manquante ne se voit dans aucune variable d'exposition.
        raise ValueError(
            f"{disponible:,} entités '{couche}' dans une emprise de "
            f"{2 * rayon_m / 1000:.0f} km, au-delà du plafond de {max_entites:,}. "
            "Réduire l'emprise plutôt que tronquer."
        )
    total = disponible

    departs = list(range(0, total, TAILLE_PAGE))

    def _page(depart: int) -> list[dict]:
        parametres = _parametres(nom_couche, bbox)
        parametres |= {
            "OUTPUTFORMAT": "application/json",
            "COUNT": TAILLE_PAGE,
            "STARTINDEX": depart,
        }
        reponse = requests.get(WFS_URL, params=parametres, timeout=timeout)
        reponse.raise_for_status()
        return reponse.json().get("features", [])

    with ThreadPoolExecutor(max_workers=min(PAGES_PARALLELES, len(departs))) as pool:
        lots = list(pool.map(_page, departs))

    entites = (
        _convertir(f) for lot in lots for f in lot if f.get("geometry")
    )
    return [e for e in entites if e is not None]


def _convertir(feature: dict) -> Entite | None:
    """Réduit une entité GeoJSON à son centroïde et à sa masse.

    La « masse » est la grandeur qui pondère l'exposition : surface pour une forêt,
    longueur pour un tronçon de route. Un point reçoit une masse unitaire — sans
    quoi il disparaîtrait de la somme pondérée.

    Renvoie `None` sur une géométrie inexploitable. Les données réelles en
    contiennent : polygones vides, coordonnées non scalaires, géométries invalides.
    Une seule suffit à faire échouer la conversion en tableau numpy de tout un lot —
    et donc à perdre une station entière. On la saute plutôt que de tout perdre.
    """
    try:
        geometrie = shape(feature["geometry"])
        if geometrie.is_empty:
            return None

        centroide = geometrie.centroid
        if centroide.is_empty:
            return None

        if geometrie.geom_type in {"Polygon", "MultiPolygon"}:
            masse = geometrie.area
        elif geometrie.geom_type in {"LineString", "MultiLineString"}:
            masse = geometrie.length
        else:
            masse = 1.0

        # Conversion explicite en scalaire : une coordonnée non scalaire passerait
        # ici sans bruit et ferait échouer un `np.asarray` bien plus loin, sur un
        # message incompréhensible.
        return Entite(
            x=float(centroide.x),
            y=float(centroide.y),
            masse=float(masse),
            proprietes=feature.get("properties", {}),
        )
    except (TypeError, ValueError, AttributeError):
        return None


def separer_par_essence(entites: list[Entite]) -> dict[str, list[Entite]]:
    """Regroupe les formations végétales par essence dominante.

    La distinction est physiquement décisive : les **feuillus**, chênes en tête, sont
    de gros émetteurs d'isoprène — précurseur d'ozone dont l'émission croît
    exponentiellement avec la température. Les **conifères** émettent surtout des
    monoterpènes, à un potentiel de formation d'ozone nettement moindre. Agréger les
    deux sous « forêt » dilue le signal jusqu'à le rendre indétectable.
    """
    groupes: dict[str, list[Entite]] = {}
    for entite in entites:
        essence = entite.proprietes.get("essence") or "Inconnue"
        groupes.setdefault(essence, []).append(entite)
    return groupes
