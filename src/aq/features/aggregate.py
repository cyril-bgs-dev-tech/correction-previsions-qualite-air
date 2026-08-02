"""Agrégation des séries horaires en indicateurs réglementaires.

Les indicateurs sont définis en **jour local**, pas en jour UTC : agréger sur des
journées UTC décale les moyennes journalières d'une à deux heures et fausse la
qualification des dépassements de seuils.

Le **taux de couverture conditionne la validité** de tout indicateur agrégé. Une
moyenne annuelle calculée sur trois mois de mesure n'est pas une moyenne annuelle :
la réglementation exige 90 % de couverture pour les polluants du projet (75 % en
hiver pour l'ozone). Un indicateur sous le seuil est renvoyé en NaN, jamais calculé
« quand même » — sans quoi une station peu instrumentée paraîtrait simplement moins
polluée, puisque les pannes ne sont pas indépendantes des épisodes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FUSEAU_LOCAL = "Europe/Paris"

# Couverture minimale exigée pour qu'un indicateur soit réputé valide
# (directive 2008/50/CE, annexe I — voir REGLEMENTAIRE.md §6).
COUVERTURE_MIN_ANNUELLE = 0.90
COUVERTURE_MIN_JOURNALIERE = 0.75


def _avec_temps_local(panneau: pd.DataFrame) -> pd.DataFrame:
    out = panneau.copy()
    local = out["timestamp_utc"].dt.tz_convert(FUSEAU_LOCAL)
    out["annee"] = local.dt.year
    out["jour_local"] = local.dt.date
    out["heure_locale"] = local.dt.hour
    return out


def moyennes_journalieres(
    panneau: pd.DataFrame, couverture_min: float = COUVERTURE_MIN_JOURNALIERE
) -> pd.DataFrame:
    """Moyennes journalières en jour local, invalidées sous le seuil de couverture."""
    df = _avec_temps_local(panneau)
    groupes = df.groupby(["station_id", "polluant", "jour_local"])

    resultat = groupes.agg(
        moyenne=("valeur", "mean"),
        maximum=("valeur", "max"),
        n_valides=("valeur", "count"),
        n_heures=("valeur", "size"),
    ).reset_index()

    resultat["couverture"] = resultat["n_valides"] / resultat["n_heures"]
    insuffisant = resultat["couverture"] < couverture_min
    resultat.loc[insuffisant, ["moyenne", "maximum"]] = np.nan
    return resultat


def indicateurs_annuels(
    panneau: pd.DataFrame, couverture_min: float = COUVERTURE_MIN_ANNUELLE
) -> pd.DataFrame:
    """Indicateurs annuels par station et polluant.

    La moyenne annuelle est calculée sur les heures valides, et non sur la moyenne
    des moyennes journalières : cette dernière pondérerait également un jour à trois
    mesures et un jour complet.
    """
    df = _avec_temps_local(panneau)
    groupes = df.groupby(["station_id", "polluant", "annee"])

    annuel = groupes.agg(
        moyenne_annuelle=("valeur", "mean"),
        mediane=("valeur", "median"),
        p95=("valeur", lambda s: s.quantile(0.95)),
        p998=("valeur", lambda s: s.quantile(0.998)),
        maximum=("valeur", "max"),
        n_valides=("valeur", "count"),
        n_heures=("valeur", "size"),
    ).reset_index()

    annuel["couverture"] = annuel["n_valides"] / annuel["n_heures"]
    annuel["valide"] = annuel["couverture"] >= couverture_min
    annuel.loc[~annuel["valide"], ["moyenne_annuelle", "mediane", "p95", "p998"]] = np.nan
    return annuel


def maximum_glissant_8h(serie: pd.Series) -> pd.Series:
    """Maximum journalier de la moyenne glissante sur 8 h — grandeur de l'ozone.

    Fenêtre calée « à droite » : la valeur datée t couvre les 8 heures qui la
    précèdent, convention de l'indicateur réglementaire.
    """
    glissante = serie.rolling(window=8, min_periods=6).mean()
    local = glissante.index.tz_convert(FUSEAU_LOCAL)
    return glissante.groupby(local.date).max()


def profil_diurne(panneau: pd.DataFrame) -> pd.DataFrame:
    """Cycle moyen par heure locale, station et polluant.

    Diagnostic immédiat de typologie : une station trafic montre un double pic aux
    heures de pointe ; une station de fond urbaine l'atténue ; l'ozone est en
    opposition de phase, maximal l'après-midi par photochimie.
    """
    df = _avec_temps_local(panneau)
    return (
        df.groupby(["station_id", "polluant", "heure_locale"])["valeur"]
        .mean()
        .reset_index()
    )


def profil_mensuel(panneau: pd.DataFrame) -> pd.DataFrame:
    """Cycle saisonnier — sépare les régimes hivernal (PM, chauffage, inversions)
    et estival (ozone photochimique)."""
    df = _avec_temps_local(panneau)
    df["mois"] = df["timestamp_utc"].dt.tz_convert(FUSEAU_LOCAL).dt.month
    return (
        df.groupby(["station_id", "polluant", "mois"])["valeur"]
        .mean()
        .reset_index()
    )
