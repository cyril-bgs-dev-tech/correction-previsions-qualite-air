"""Conversions d'unités vers le référentiel canonique du contrat de données.

Les conditions de référence des gaz sont celles de la réglementation européenne
(20 °C, 1013,25 hPa). Elles diffèrent de la convention américaine (25 °C), et
l'écart de ~1,8 % est un biais systématique indétectable a posteriori : d'où le
choix d'un paramètre explicite plutôt que d'une constante magique.
"""

from __future__ import annotations

import numpy as np

# Constante des gaz parfaits (CODATA), J.mol-1.K-1
R_GAZ = 8.314462618

# Conditions de référence UE pour les polluants gazeux
T_REF_UE_K = 293.15
P_REF_UE_PA = 101325.0

# Conditions EPA, fournies uniquement pour rendre l'écart explicite et testable
T_REF_EPA_K = 298.15

MASSES_MOLAIRES_G_MOL = {
    "NO2": 46.0055,
    "O3": 47.9982,
    "SO2": 64.0638,
    "CO": 28.0101,
    "NO": 30.0061,
    "NH3": 17.0305,
}

# Les particules sont mesurées en conditions ambiantes : aucune conversion
# molaire n'a de sens pour elles.
POLLUANTS_PARTICULAIRES = {"PM10", "PM25", "PM1", "BC"}


def facteur_ppb_vers_ug_m3(
    polluant: str,
    temperature_K: float = T_REF_UE_K,
    pression_Pa: float = P_REF_UE_PA,
) -> float:
    """Facteur multiplicatif pour passer de ppb à µg.m-3.

    Aux conditions UE : NO2 ≈ 1,913 · O3 ≈ 1,996 · SO2 ≈ 2,663.
    """
    if polluant in POLLUANTS_PARTICULAIRES:
        raise ValueError(
            f"{polluant} est un polluant particulaire, mesuré en conditions "
            "ambiantes : la conversion ppb -> µg.m-3 n'a pas de sens."
        )
    try:
        masse_molaire = MASSES_MOLAIRES_G_MOL[polluant]
    except KeyError as exc:
        raise KeyError(f"Masse molaire inconnue pour '{polluant}'.") from exc

    # Densité molaire de l'air (mol.m-3) aux conditions de référence
    densite_molaire = pression_Pa / (R_GAZ * temperature_K)
    # 1 ppb = 1e-9 en fraction molaire ; g -> µg = 1e6
    return densite_molaire * 1e-9 * masse_molaire * 1e6


def ppb_vers_ug_m3(valeurs, polluant, temperature_K=T_REF_UE_K, pression_Pa=P_REF_UE_PA):
    return np.asarray(valeurs, dtype="float64") * facteur_ppb_vers_ug_m3(
        polluant, temperature_K, pression_Pa
    )


def ug_m3_vers_ppb(valeurs, polluant, temperature_K=T_REF_UE_K, pression_Pa=P_REF_UE_PA):
    return np.asarray(valeurs, dtype="float64") / facteur_ppb_vers_ug_m3(
        polluant, temperature_K, pression_Pa
    )


def kelvin_vers_celsius(valeurs):
    return np.asarray(valeurs, dtype="float64") - 273.15


def pascal_vers_hectopascal(valeurs):
    return np.asarray(valeurs, dtype="float64") / 100.0


def metres_vers_millimetres(valeurs):
    """Précipitations : les réanalyses les expriment en mètres d'eau."""
    return np.asarray(valeurs, dtype="float64") * 1000.0


def joules_m2_vers_watts_m2(valeurs, duree_accumulation_s: float = 3600.0):
    """Rayonnement : les réanalyses accumulent en J.m-2 sur le pas de temps.

    Diviser par la durée d'accumulation, pas par une constante supposée : si le
    pas natif n'est pas horaire, une division par 3600 introduit un facteur
    d'échelle silencieux.
    """
    return np.asarray(valeurs, dtype="float64") / duree_accumulation_s
