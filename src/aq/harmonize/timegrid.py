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


def en_mois(ts: pd.Series) -> pd.Series:
    """Le mois calendaire de chaque horodatage — en vectorisé, jamais objet par objet.

    **Ce n'est pas une optimisation de confort.** `pd.PeriodIndex(série, freq="M")`
    n'a aucun chemin vectorisé pour une série *tz-aware* : `period_array` appelle
    `np.asarray`, qui retombe sur `DatetimeArray.__iter__` et **boxe une `Timestamp`
    puis une `Period` par ligne**. Or tout `timestamp_utc` de ce projet est stocké en
    `timestamp[ns, tz=UTC]` — le chemin lent est donc le chemin par défaut.

    Sur les 23 fichiers de prévision d'un polluant cela fait de l'ordre de plusieurs
    dizaines de millions d'allocations d'objets Python, et c'est exactement là que le
    lot du 10/08 00 h 09 est mort : **12 des 14 segfauts** de ses 18 tentatives portent
    ce site en tête de pile (`logs/production_tendance_*.log`). Les quatre exceptions
    levées au même endroit sont la même corruption vue de l'autre côté — une valeur qui
    atterrit dans le mauvais emplacement d'argument : `'UTC' object cannot be
    interpreted as an integer`, `Invalid frequency: 2024-10-23 00:00:00+00:00`,
    `'Timestamp' object has no attribute 'ordinal'`, `… no attribute 'minute'`.

    `.dt.to_period()` emprunte `dt64arr_to_periodarr`, une boucle Cython sur int64 qui
    ne crée aucun objet intermédiaire. **Mesuré sur 1,8 M de lignes de prévision O₃ :
    2 260 ms → 49 ms (×46)**, et les ensembles de mois obtenus sont *identiques* sur les
    six fichiers testés — vérifié, pas supposé.

    Le `tz_convert(None)` est écrit à dessein plutôt que tu par un filtre de warnings :
    `to_period` prévient qu'il perd le fuseau. Ici les horodatages sont en UTC, donc
    l'heure murale *est* l'heure UTC et la perte est nulle — mais elle est dite.
    """
    if ts.dt.tz is not None:
        ts = ts.dt.tz_convert(None)
    return ts.dt.to_period("M")


def mois_couverts(ts: pd.Series) -> set[pd.Period]:
    """Les mois calendaires touchés par une série d'horodatages. Voir `en_mois`."""
    return set(en_mois(ts).unique())


def couverture_temporelle(serie: pd.Series, par: str = "jour_local") -> pd.Series:
    """Taux de données valides par période — critère de validité réglementaire.

    Une moyenne journalière calculée sur trois heures de mesure n'est pas une
    moyenne journalière. La réglementation impose un taux de couverture minimal ;
    ce taux doit être calculé, pas supposé.
    """
    df = ajouter_temps_local(serie.to_frame("valeur"))
    return df.groupby(par)["valeur"].apply(lambda s: s.notna().mean())
