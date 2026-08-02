"""Variables d'exposition géospatiale — *Land-Use Regression*.

Trois familles, de valeur croissante :

1. **Distance simple** au plus proche objet. Isotrope et aveugle à la masse : une
   forêt de 3 ha et un massif de 30 000 ha à la même distance donnent la même
   valeur, alors que leur influence n'a rien de comparable.

2. **Exposition pondérée par décroissance de distance** — fusionne distance et
   surface en une grandeur physiquement motivée :

       exposition(p, λ) = Σᵢ poidsᵢ × exp(−dᵢ / λ)

   Le balayage de λ est un résultat en soi : il mesure l'échelle spatiale
   d'influence, qui diffère par polluant. Le NO₂ retombe au fond en 150-300 m ;
   l'isoprène émis par les chênes met plusieurs heures à produire de l'ozone, donc
   son influence porte à des dizaines de kilomètres.

3. **Exposition anisotrope conditionnée au vent** — une source n'influence un point
   que lorsqu'elle est *au vent*. C'est ce qui transforme des couches statiques en
   variables spatio-temporelles, et empêche le modèle de se contenter de mémoriser
   l'identité de chaque station.

**Toutes les coordonnées sont attendues en mètres, en Lambert-93 (EPSG:2154).**
Calculer sur des degrés introduirait à la latitude de l'Occitanie une distorsion
anisotrope d'environ 27 %, orientée selon l'axe mer/intérieur — précisément celui
que ces variables cherchent à exploiter.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aq.harmonize import wind

# Longueurs de décroissance balayées par défaut, en mètres. La gamme couvre de la
# rue canyon (100 m) au transport régional (30 km).
LAMBDAS_DEFAUT = (100.0, 300.0, 1_000.0, 3_000.0, 10_000.0, 30_000.0)


def _en_tableau(valeurs, nom: str) -> np.ndarray:
    tableau = np.asarray(valeurs, dtype="float64")
    if tableau.ndim != 1:
        raise ValueError(f"{nom} doit être unidimensionnel, reçu {tableau.shape}")
    return tableau


def distances(
    x_recepteurs, y_recepteurs, x_sources, y_sources
) -> np.ndarray:
    """Matrice des distances euclidiennes (récepteurs × sources), en mètres."""
    xr = _en_tableau(x_recepteurs, "x_recepteurs")[:, None]
    yr = _en_tableau(y_recepteurs, "y_recepteurs")[:, None]
    xs = _en_tableau(x_sources, "x_sources")[None, :]
    ys = _en_tableau(y_sources, "y_sources")[None, :]
    return np.hypot(xr - xs, yr - ys)


def azimuts(x_recepteurs, y_recepteurs, x_sources, y_sources) -> np.ndarray:
    """Azimut géographique du récepteur VERS chaque source, en degrés.

    Convention géographique : 0° = nord, sens horaire. Elle se compare directement
    à la direction météorologique du vent, qui désigne déjà l'origine du vent : les
    deux coïncident quand la source est exactement au vent.
    """
    xr = _en_tableau(x_recepteurs, "x_recepteurs")[:, None]
    yr = _en_tableau(y_recepteurs, "y_recepteurs")[:, None]
    xs = _en_tableau(x_sources, "x_sources")[None, :]
    ys = _en_tableau(y_sources, "y_sources")[None, :]
    return np.degrees(np.arctan2(xs - xr, ys - yr)) % 360.0


def distance_plus_proche(x_recepteurs, y_recepteurs, x_sources, y_sources) -> np.ndarray:
    """Famille 1 — distance au plus proche objet, en mètres."""
    if len(_en_tableau(x_sources, "x_sources")) == 0:
        return np.full(len(_en_tableau(x_recepteurs, "x_recepteurs")), np.inf)
    return distances(x_recepteurs, y_recepteurs, x_sources, y_sources).min(axis=1)


def exposition_ponderee(
    x_recepteurs,
    y_recepteurs,
    x_sources,
    y_sources,
    poids_sources=None,
    lambda_m: float = 1_000.0,
    distance_min_m: float = 1.0,
) -> np.ndarray:
    """Famille 2 — Σ poids × exp(−distance / λ).

    `poids_sources` porte la masse de chaque source : surface pour une forêt,
    longueur pour un tronçon de route, tonnage émis pour un site industriel. C'est
    ce terme qui distingue un massif d'un bosquet à distance égale.

    `distance_min_m` évite qu'une source confondue avec le récepteur ne domine
    tout : sans plancher, une distance nulle donnerait un poids maximal à un seul
    objet, quelle que soit la structure du reste du paysage.
    """
    if lambda_m <= 0:
        raise ValueError(f"λ doit être strictement positif, reçu {lambda_m}")

    xs = _en_tableau(x_sources, "x_sources")
    n_recepteurs = len(_en_tableau(x_recepteurs, "x_recepteurs"))
    if len(xs) == 0:
        return np.zeros(n_recepteurs)

    poids = (
        np.ones(len(xs))
        if poids_sources is None
        else _en_tableau(poids_sources, "poids_sources")
    )
    if len(poids) != len(xs):
        raise ValueError(
            f"{len(poids)} poids pour {len(xs)} sources : longueurs incompatibles"
        )

    d = np.maximum(
        distances(x_recepteurs, y_recepteurs, x_sources, y_sources), distance_min_m
    )
    return (poids[None, :] * np.exp(-d / lambda_m)).sum(axis=1)


def balayer_lambdas(
    x_recepteurs,
    y_recepteurs,
    x_sources,
    y_sources,
    poids_sources=None,
    lambdas=LAMBDAS_DEFAUT,
    prefixe: str = "expo",
) -> pd.DataFrame:
    """Une colonne d'exposition par longueur de décroissance.

    Les colonnes obtenues sont fortement corrélées entre elles : la sélection doit
    être supervisée et explicite (VIF, sélection par groupe), avec contrainte de
    signe conforme au mécanisme physique attendu. Une variable dont le signe
    contredit la physique se rejette, même si elle améliore le score.
    """
    return pd.DataFrame(
        {
            f"{prefixe}_lambda{int(lam)}m": exposition_ponderee(
                x_recepteurs, y_recepteurs, x_sources, y_sources,
                poids_sources, lambda_m=lam,
            )
            for lam in lambdas
        }
    )


def exposition_au_vent(
    x_recepteurs,
    y_recepteurs,
    x_sources,
    y_sources,
    direction_vent_deg,
    poids_sources=None,
    lambda_m: float = 10_000.0,
    demi_ouverture_deg: float = 45.0,
    distance_min_m: float = 1.0,
) -> np.ndarray:
    """Famille 3 — exposition anisotrope conditionnée au vent.

        Σᵢ poidsᵢ × exp(−dᵢ/λ) × w(Δθᵢ)

    `direction_vent_deg` suit la convention météorologique (origine du vent), une
    valeur par récepteur. Seules les sources situées dans le secteur au vent
    contribuent, avec une décroissance en cosinus tronqué jusqu'à l'ouverture.

    Un vent de direction indéterminée (NaN, cas du vent nul) donne une exposition
    nulle plutôt qu'une valeur arbitraire : sans direction, aucune source ne peut
    être déclarée au vent.
    """
    xs = _en_tableau(x_sources, "x_sources")
    directions = _en_tableau(direction_vent_deg, "direction_vent_deg")
    n_recepteurs = len(_en_tableau(x_recepteurs, "x_recepteurs"))

    if len(directions) != n_recepteurs:
        raise ValueError(
            f"{len(directions)} directions pour {n_recepteurs} récepteurs"
        )
    if len(xs) == 0:
        return np.zeros(n_recepteurs)

    poids = (
        np.ones(len(xs))
        if poids_sources is None
        else _en_tableau(poids_sources, "poids_sources")
    )

    d = np.maximum(
        distances(x_recepteurs, y_recepteurs, x_sources, y_sources), distance_min_m
    )
    theta = azimuts(x_recepteurs, y_recepteurs, x_sources, y_sources)

    poids_angulaire = wind.poids_secteur_au_vent(
        theta, directions[:, None], demi_ouverture_deg=demi_ouverture_deg
    )
    poids_angulaire = np.where(np.isnan(directions)[:, None], 0.0, poids_angulaire)

    return (poids[None, :] * np.exp(-d / lambda_m) * poids_angulaire).sum(axis=1)


def surface_par_couronne(
    x_recepteurs,
    y_recepteurs,
    x_sources,
    y_sources,
    poids_sources=None,
    rayons=(100.0, 300.0, 1_000.0, 5_000.0),
    prefixe: str = "buffer",
) -> pd.DataFrame:
    """Variante LUR classique — masse cumulée dans des disques concentriques.

    Plus fruste que l'exposition exponentielle (seuil net plutôt que décroissance
    continue), mais c'est la forme historique de la littérature ESCAPE : la
    conserver permet de comparer les résultats du projet à cette référence.
    """
    xs = _en_tableau(x_sources, "x_sources")
    n_recepteurs = len(_en_tableau(x_recepteurs, "x_recepteurs"))
    if len(xs) == 0:
        return pd.DataFrame(
            {f"{prefixe}_{int(r)}m": np.zeros(n_recepteurs) for r in rayons}
        )

    poids = (
        np.ones(len(xs))
        if poids_sources is None
        else _en_tableau(poids_sources, "poids_sources")
    )
    d = distances(x_recepteurs, y_recepteurs, x_sources, y_sources)
    return pd.DataFrame(
        {
            f"{prefixe}_{int(r)}m": (poids[None, :] * (d <= r)).sum(axis=1)
            for r in rayons
        }
    )
