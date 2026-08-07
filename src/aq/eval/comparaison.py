"""Comparaison d'un modèle aux observations, aux conventions du métier.

Deux précautions structurent ce module.

**On compare ce qui est comparable.** Une prévision CAMS vaut pour une maille de
0,1° (~8 km) ; une station trafic mesure un micro-environnement de quelques mètres,
que cette maille ne peut pas résoudre. Mélanger les typologies impute au modèle une
erreur qui tient à la définition de la mesure, pas à sa qualité. Les métriques sont
donc systématiquement ventilables par typologie.

**Le R² se calcule contre la bonne référence.** Ici, la variance des observations —
pas celle d'une régression ajustée. Un modèle physique n'a pas été calibré sur ces
observations : son R² peut être négatif, et c'est une information, pas une anomalie.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ParametresQualite:
    """Paramètres d'incertitude de mesure d'un polluant, au sens FAIRMODE.

    **Ce qui est sourcé** — *Guidance Document on Modelling Quality Objectives and
    Benchmarking*, JRC120649, version 3.2 (2020), DOI 10.2760/30226 : la formule
    `MQI = RMSE / (β · RMS_U)`, le facteur `β = 2`, l'objectif `MQI ≤ 1` et le critère
    de conformité **sur 90 % des stations**.

    ✅ **Confronté au document le 30/07/2026** — v3.2, tableau 6 p. 43. NO₂ et O₃ étaient
    justes ; **α de PM2,5 valait 0,13, qui est l'α de PM10** — corrigé en **0,30**. L'erreur
    sur-estimait le MQI de PM2,5 de 2 à 20 % selon le niveau observé, donc dans le sens
    pessimiste : elle ne pouvait pas se trahir par une conformité usurpée.

    ⚠️ **Deux réserves qui subsistent.**

    1. **Version.** Ces valeurs sont celles de la **v3.2 (2020)**. La **v4.0 (mai 2026)**
       remplace le `β = 2` global par un β **par polluant** et change les `RV` — passer à
       la v4.0 est une refonte de cette structure, pas un changement de constantes. Le
       guide v4.0 annonce lui-même une révision fin 2026 par CEN/WG43.
    2. ✅ **Temps d'agrégation — levé le 06/08/2026.** Le tableau définit ses paramètres
       pour une grandeur précise : NO₂ **horaire**, O₃ en **maximum journalier 8 h**,
       PM2,5 en **journalier**. Ce module reste **agnostique** — il applique la formule à
       la série qu'on lui donne —, mais le dossier lui donnait des séries horaires pour
       les trois, si bien que le MQI d'O₃ et de PM2,5 ne correspondait à aucune ligne du
       document. C'est réparé **en amont** : `verite_dossier.GRAIN_REGLEMENTAIRE` impose
       désormais le grain par polluant et publie `reports/mqi_bon_grain.csv`, dont le § 5
       tire ses deux colonnes.

       L'erreur était **pessimiste** : l'agrégation journalière réduit la variance de
       l'erreur plus que celle de l'incertitude de mesure, qui dépend surtout du niveau
       observé. Aucun produit ne changeait de côté du seuil — l'énoncé de conformité
       tenait, seul le chiffre cité était le mauvais. ⚠️ **Appelant, à toi de fournir la
       bonne grandeur** : ce module ne peut pas la deviner depuis une série.
    """

    incertitude_relative: float   # U^RV_95, incertitude relative étendue à la valeur de référence
    alpha: float                  # part non proportionnelle de l'incertitude
    valeur_reference: float       # RV, en µg/m³


# Recopiés du tableau 6 p. 43 de JRC120649 v3.2 (2020), DOI 10.2760/30226.
# L'α de PM10 y vaut 0,13 et celui de PM2,5 0,30 : ne pas les intervertir — c'est l'erreur
# qui a été corrigée le 30/07/2026.
PARAMETRES_FAIRMODE = {
    "NO2": ParametresQualite(0.24, 0.20, 200.0),
    "O3": ParametresQualite(0.18, 0.79, 120.0),
    "PM25": ParametresQualite(0.36, 0.30, 25.0),
}

# Facteur d'élargissement, sourcé : JRC120649 v3.2 (2020), DOI 10.2760/30226.
BETA = 2.0

# La conformité s'apprécie sur **90 % des stations**, pas sur la moyenne — une AASQA
# peut donc être conforme avec une station décrochée. Même source.
PART_STATIONS_CONFORMES = 0.90


def metriques(observe, predit) -> dict[str, float]:
    """Métriques d'erreur élémentaires, sur les couples complets uniquement.

    Les paires incomplètes sont écartées **ensemble** : garder une observation sans
    prévision, ou l'inverse, décalerait les deux séries l'une par rapport à l'autre.
    """
    observe = np.asarray(observe, dtype="float64")
    predit = np.asarray(predit, dtype="float64")
    complet = np.isfinite(observe) & np.isfinite(predit)
    observe, predit = observe[complet], predit[complet]

    if observe.size == 0:
        return {"n": 0, "rmse": np.nan, "mae": np.nan, "biais": np.nan,
                "r2": np.nan, "correlation": np.nan, "ecart_type_obs": np.nan}

    erreur = predit - observe
    variance = float(observe.var())
    return {
        "n": int(observe.size),
        "rmse": float(np.sqrt((erreur**2).mean())),
        "mae": float(np.abs(erreur).mean()),
        "biais": float(erreur.mean()),
        # Contre la variance des observations : un modèle physique non calibré peut
        # donner un R² négatif, ce qui signifie « pire que prédire la moyenne ».
        "r2": float(1.0 - (erreur**2).mean() / variance) if variance > 0 else np.nan,
        "correlation": float(np.corrcoef(observe, predit)[0, 1])
        if observe.size > 1 and variance > 0 else np.nan,
        "ecart_type_obs": float(np.sqrt(variance)),
    }


def indice_qualite_modele(observe, predit, polluant: str) -> float:
    """Indicateur de qualité de modèle (MQI) au sens FAIRMODE.

    Rapporte l'erreur du modèle à l'incertitude de la mesure elle-même : un modèle
    dont l'erreur reste sous le bruit de l'observation ne peut pas être amélioré par
    des données de cette qualité. La conformité s'énonce **MQI ≤ 1**.

    Voir l'avertissement de `ParametresQualite` : les paramètres doivent être sourcés
    avant publication.
    """
    if polluant not in PARAMETRES_FAIRMODE:
        raise ValueError(
            f"Polluant sans paramètres d'incertitude : {polluant} "
            f"(connus : {sorted(PARAMETRES_FAIRMODE)})"
        )
    p = PARAMETRES_FAIRMODE[polluant]

    observe = np.asarray(observe, dtype="float64")
    predit = np.asarray(predit, dtype="float64")
    complet = np.isfinite(observe) & np.isfinite(predit)
    observe, predit = observe[complet], predit[complet]
    if observe.size == 0:
        return float("nan")

    incertitude = p.incertitude_relative * np.sqrt(
        (1 - p.alpha**2) * observe**2 + p.alpha**2 * p.valeur_reference**2
    )
    rmse = np.sqrt(((predit - observe) ** 2).mean())
    return float(rmse / (BETA * np.sqrt((incertitude**2).mean())))


def intervalle_bootstrap(
    observe,
    predit_a,
    predit_b,
    groupes=None,
    n_tirages: int = 500,
    graine: int = 0,
    niveau: float = 0.95,
) -> dict[str, float]:
    """Intervalle de confiance sur le **gain de RMSE** entre deux modèles.

    **Le rééchantillonnage porte sur les stations, pas sur les lignes.** Les heures
    d'une même station sont fortement corrélées : tirer des lignes au hasard traiterait
    24 heures consécutives comme 24 observations indépendantes et rétrécirait
    l'intervalle d'un facteur trompeur. Le nombre d'observations effectivement
    indépendantes est de l'ordre du nombre de **stations**, pas de celui des lignes.

    Sans `groupes`, on retombe sur un bootstrap ordinaire — utile seulement quand les
    lignes sont réellement indépendantes, ce qui n'est presque jamais le cas ici.
    """
    observe = np.asarray(observe, dtype="float64")
    a = np.asarray(predit_a, dtype="float64")
    b = np.asarray(predit_b, dtype="float64")
    complet = np.isfinite(observe) & np.isfinite(a) & np.isfinite(b)
    observe, a, b = observe[complet], a[complet], b[complet]

    rmse = lambda y, p: float(np.sqrt(((p - y) ** 2).mean()))
    gain = lambda idx: 100 * (1 - rmse(observe[idx], b[idx]) / rmse(observe[idx], a[idx]))

    rng = np.random.default_rng(graine)
    if groupes is None:
        n = observe.size
        tirages = [gain(rng.integers(0, n, n)) for _ in range(n_tirages)]
    else:
        groupes = np.asarray(groupes)[complet]
        uniques = np.unique(groupes)
        # Index des lignes de chaque groupe, calculés une fois : les recalculer à chaque
        # tirage coûterait cent fois plus cher pour le même résultat.
        par_groupe = {g: np.flatnonzero(groupes == g) for g in uniques}
        tirages = []
        for _ in range(n_tirages):
            choisis = rng.choice(uniques, size=uniques.size, replace=True)
            tirages.append(gain(np.concatenate([par_groupe[g] for g in choisis])))

    marge = (1 - niveau) / 2
    return {
        "gain_pct": gain(np.arange(observe.size)),
        "borne_basse": float(np.quantile(tirages, marge)),
        "borne_haute": float(np.quantile(tirages, 1 - marge)),
        "n_unites": int(len(uniques) if groupes is not None else observe.size),
        "part_tirages_positifs": float(np.mean(np.array(tirages) > 0)),
    }


def comparer(
    joint: pd.DataFrame,
    colonne_observe: str = "valeur",
    colonne_predit: str = "prediction",
    polluant: str | None = None,
    par: list[str] | None = None,
) -> pd.DataFrame:
    """Tableau de métriques, éventuellement ventilé par une ou plusieurs colonnes.

    `par=["type_station"]` sépare le fond du trafic — la ventilation la plus
    éclairante pour un modèle de chimie-transport, dont la maille ne résout pas le
    micro-environnement d'une station trafic.
    """
    def _ligne(sous: pd.DataFrame) -> dict:
        resultat = metriques(sous[colonne_observe], sous[colonne_predit])
        if polluant in PARAMETRES_FAIRMODE:
            resultat["mqi"] = indice_qualite_modele(
                sous[colonne_observe], sous[colonne_predit], polluant
            )
            resultat["conforme"] = resultat["mqi"] <= 1.0
        return resultat

    if not par:
        return pd.DataFrame([_ligne(joint)])

    lignes = []
    for cles, sous in joint.groupby(par, dropna=False, observed=True):
        cles = cles if isinstance(cles, tuple) else (cles,)
        lignes.append({**dict(zip(par, cles)), **_ligne(sous)})
    return pd.DataFrame(lignes)
