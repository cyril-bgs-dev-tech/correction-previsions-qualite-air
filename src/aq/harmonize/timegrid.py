"""Grille temporelle canonique : UTC, pas horaire, horodatage en début d'intervalle.

C'est ici que se règle la synchronisation entre sources. Chaque producteur a sa
propre convention d'horodatage, et rien dans les données ne permet de la deviner :
elle doit être DÉCLARÉE par l'adaptateur d'ingestion, puis convertie ici.
"""

from __future__ import annotations

import pandas as pd

PAS_CANONIQUE = "1h"
FUSEAU_STOCKAGE = "UTC"
FUSEAU_LOCAL = "Europe/Paris"

# Conventions d'horodatage rencontrées, et décalage à appliquer pour ramener
# l'horodatage au DÉBUT de l'intervalle couvert.
CONVENTIONS = {
    "instantane": 0,      # valeur ponctuelle : rattachée à l'heure qui commence
    "moyenne_avant": -1,  # la valeur datée t couvre (t-1h, t]
    "cumul_avant": -1,
    "moyenne_apres": 0,   # la valeur datée t couvre [t, t+1h) : déjà canonique
    "cumul_apres": 0,
}


def vers_utc(index: pd.DatetimeIndex, fuseau_source: str = "UTC") -> pd.DatetimeIndex:
    """Rend l'index tz-aware en UTC.

    Si la source est en heure locale, `tz_localize` doit gérer les deux anomalies
    annuelles : l'heure inexistante du passage à l'heure d'été et l'heure
    dupliquée du retour à l'heure d'hiver. On échoue bruyamment plutôt que de
    deviner, car un mauvais choix décale silencieusement une heure par an.
    """
    index = pd.DatetimeIndex(index)
    if index.tz is None:
        index = index.tz_localize(
            fuseau_source, ambiguous="raise", nonexistent="raise"
        )
    return index.tz_convert(FUSEAU_STOCKAGE)


def vers_debut_intervalle(index: pd.DatetimeIndex, convention: str) -> pd.DatetimeIndex:
    """Ramène l'horodatage au début de l'intervalle couvert."""
    if convention not in CONVENTIONS:
        raise ValueError(
            f"Convention '{convention}' inconnue. Attendu : {sorted(CONVENTIONS)}"
        )
    decalage = CONVENTIONS[convention]
    if decalage == 0:
        return pd.DatetimeIndex(index)
    return pd.DatetimeIndex(index) + pd.Timedelta(hours=decalage)


def harmoniser(
    df: pd.DataFrame,
    convention: str,
    fuseau_source: str = "UTC",
    colonne_temps: str | None = None,
) -> pd.DataFrame:
    """Applique la chaîne complète : fuseau, convention d'intervalle, tri, doublons."""
    out = df.copy()
    if colonne_temps is not None:
        out = out.set_index(colonne_temps)

    out.index = vers_debut_intervalle(vers_utc(out.index, fuseau_source), convention)
    out.index.name = "timestamp_utc"

    doublons = out.index.duplicated().sum()
    if doublons:
        raise ValueError(
            f"{doublons} horodatages dupliqués après harmonisation. "
            "Cause fréquente : source en heure locale déclarée à tort en UTC, "
            "ou concaténation de fichiers qui se recouvrent."
        )
    return out.sort_index()


def grille_complete(debut, fin) -> pd.DatetimeIndex:
    """Grille horaire continue en UTC, bornes incluses.

    Réindexer dessus rend les trous EXPLICITES (NaN) au lieu de les laisser
    invisibles sous forme d'heures simplement absentes — un modèle de série
    temporelle traite très différemment ces deux situations.
    """
    return pd.date_range(
        _en_utc(debut), _en_utc(fin), freq=PAS_CANONIQUE
    )


def _en_utc(instant) -> pd.Timestamp:
    """Accepte indifféremment une date naïve ou déjà localisée.

    Une date naïve est réputée UTC ; une date localisée est convertie. Passer
    `tz=` à un Timestamp déjà localisé lève une erreur — d'où l'aiguillage.
    """
    horodatage = pd.Timestamp(instant)
    if horodatage.tzinfo is None:
        return horodatage.tz_localize(FUSEAU_STOCKAGE)
    return horodatage.tz_convert(FUSEAU_STOCKAGE)


def ajouter_temps_local(df: pd.DataFrame) -> pd.DataFrame:
    """Colonnes dérivées en heure locale, pour l'interprétation et le réglementaire.

    Les indicateurs réglementaires sont définis en JOUR LOCAL. Agréger en jour UTC
    décale les journées d'une à deux heures et fausse les moyennes journalières
    servant à qualifier les dépassements de seuils.
    """
    out = df.copy()
    local = out.index.tz_convert(FUSEAU_LOCAL)
    out["heure_locale"] = local.hour
    out["jour_local"] = local.date
    out["mois"] = local.month
    out["jour_semaine"] = local.dayofweek
    return out


def couverture_temporelle(serie: pd.Series, par: str = "jour_local") -> pd.Series:
    """Taux de données valides par période — critère de validité réglementaire.

    Une moyenne journalière calculée sur trois heures de mesure n'est pas une
    moyenne journalière. La réglementation impose un taux de couverture minimal ;
    ce taux doit être calculé, pas supposé.
    """
    df = ajouter_temps_local(serie.to_frame("valeur"))
    return df.groupby(par)["valeur"].apply(lambda s: s.notna().mean())
