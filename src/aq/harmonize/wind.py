"""Vent : conversions direction/composantes et statistiques circulaires.

Deux pièges que ce module existe pour neutraliser.

1. La direction météorologique indique d'où VIENT le vent (0° = vent de nord),
   en sens horaire depuis le nord. La convention mathématique indique où l'on VA,
   en sens trigonométrique depuis l'est. Les deux diffèrent d'une réflexion et
   d'une rotation. Se tromper fait pointer les panaches à l'opposé, ce qui
   ruinerait silencieusement toutes les variables d'exposition anisotrope.

2. La direction est une grandeur circulaire : la moyenne arithmétique de 350° et
   de 10° vaut 180°, soit exactement la direction opposée à la bonne réponse (0°).
   Toute agrégation passe par les composantes u/v, jamais par l'angle.
"""

from __future__ import annotations

import numpy as np


def direction_vitesse_vers_uv(direction_deg, vitesse):
    """Direction météorologique (origine du vent) + vitesse -> composantes u, v.

    u est la composante vers l'est, v la composante vers le nord.
    Un vent de nord (direction 0°) souffle vers le sud : v est négatif.
    """
    direction_rad = np.radians(np.asarray(direction_deg, dtype="float64"))
    vitesse = np.asarray(vitesse, dtype="float64")
    u = -vitesse * np.sin(direction_rad)
    v = -vitesse * np.cos(direction_rad)
    return u, v


def uv_vers_direction_vitesse(u, v):
    """Composantes u, v -> direction météorologique (origine) + vitesse."""
    u = np.asarray(u, dtype="float64")
    v = np.asarray(v, dtype="float64")
    vitesse = np.hypot(u, v)
    direction = (270.0 - np.degrees(np.arctan2(v, u))) % 360.0
    # Vent nul : la direction n'est pas définie. La renvoyer à 0 serait un
    # artefact qui créerait un pic parasite au nord dans les roses des vents.
    direction = np.where(vitesse == 0.0, np.nan, direction)
    return direction, vitesse


def moyenne_directionnelle(direction_deg, vitesse=None):
    """Moyenne circulaire de directions, éventuellement pondérée par la vitesse.

    Pondérer par la vitesse donne le vent moyen VECTORIEL : c'est celui qui a un
    sens physique pour le transport de polluants, car un vent fort compte plus
    qu'une brise. La moyenne non pondérée ne décrit que la direction dominante.
    """
    if vitesse is None:
        vitesse = np.ones_like(np.asarray(direction_deg, dtype="float64"))
    u, v = direction_vitesse_vers_uv(direction_deg, vitesse)
    direction, _ = uv_vers_direction_vitesse(np.nanmean(u), np.nanmean(v))
    return float(direction)


def ecart_angulaire(direction_a_deg, direction_b_deg):
    """Écart angulaire minimal entre deux directions, dans [0, 180].

    Brique de base du noyau angulaire des variables d'exposition au vent :
    une source ne compte que lorsqu'elle est au vent du point considéré.
    """
    diff = np.asarray(direction_a_deg, dtype="float64") - np.asarray(
        direction_b_deg, dtype="float64"
    )
    return np.abs((diff + 180.0) % 360.0 - 180.0)


def poids_secteur_au_vent(azimut_source_deg, direction_vent_deg, demi_ouverture_deg=45.0):
    """Poids angulaire d'une source selon qu'elle est au vent du récepteur.

    `azimut_source_deg` est l'azimut du récepteur VERS la source (convention
    géographique : 0° = nord, sens horaire). `direction_vent_deg` suit la
    convention météorologique : elle désigne déjà d'où vient le vent. Les deux
    coïncident donc quand la source est exactement au vent, ce qui rend la
    comparaison directe.

    Noyau en cosinus tronqué : décroissance douce jusqu'à l'ouverture, nul au-delà.
    """
    ecart = ecart_angulaire(azimut_source_deg, direction_vent_deg)
    poids = np.cos(np.pi / 2.0 * ecart / demi_ouverture_deg)
    return np.where(ecart <= demi_ouverture_deg, np.clip(poids, 0.0, 1.0), 0.0)
