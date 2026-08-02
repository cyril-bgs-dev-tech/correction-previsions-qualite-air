"""Tests du calcul de l'indice ATMO.

Ces tests vérifient la conformité aux bornes de l'arrêté du 10 juillet 2020. Une
erreur de classe ici se propage jusqu'à la communication au public, et se compare
directement à un indice officiellement publié — elle est donc visible et coûteuse.
"""

import numpy as np
import pandas as pd
import pytest

from aq.models import indice_atmo as ia


# --------------------------------------------------------------------------- #
# Bornes de classe
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "polluant,valeur,attendu",
    [
        # Bornes supérieures INCLUSES dans leur classe (« 0-10 = Bon »).
        ("PM25", 10, 1), ("PM25", 11, 2), ("PM25", 20, 2), ("PM25", 21, 3),
        ("PM25", 25, 3), ("PM25", 26, 4), ("PM25", 75, 5), ("PM25", 76, 6),
        ("NO2", 40, 1), ("NO2", 41, 2), ("NO2", 340, 5), ("NO2", 341, 6),
        ("O3", 50, 1), ("O3", 130, 3), ("O3", 380, 5), ("O3", 381, 6),
        ("PM10", 20, 1), ("PM10", 150, 5), ("PM10", 151, 6),
        ("SO2", 100, 1), ("SO2", 750, 5), ("SO2", 751, 6),
    ],
)
def test_bornes_conformes_a_l_arrete(polluant, valeur, attendu):
    assert int(ia.sous_indice(valeur, polluant)) == attendu


def test_arrondi_avant_classement():
    """Les bornes de l'arrêté sont entières et discontinues (0-10 puis 11-20) :
    elles s'appliquent à des concentrations arrondies. Sans arrondi, 10,4 µg/m³ ne
    tomberait dans aucune classe."""
    assert int(ia.sous_indice(10.4, "PM25")) == 1   # arrondi à 10 → Bon
    assert int(ia.sous_indice(10.6, "PM25")) == 2   # arrondi à 11 → Moyen
    assert int(ia.sous_indice(10.5, "PM25")) == 1   # arrondi pair de numpy → 10


def test_valeur_nulle_est_bonne():
    assert int(ia.sous_indice(0.0, "NO2")) == 1


def test_valeur_extreme_plafonne_a_six():
    assert int(ia.sous_indice(10_000.0, "NO2")) == 6


def test_manquant_reste_manquant():
    assert np.isnan(ia.sous_indice(np.nan, "NO2"))


def test_polluant_hors_indice_rejete():
    """Le CO ne fait pas partie de l'indice ATMO depuis 2021."""
    with pytest.raises(ValueError, match="hors indice"):
        ia.sous_indice(5.0, "CO")


def test_couleurs_officielles():
    assert ia.COULEURS[1] == "#50F0E6"
    assert ia.COULEURS[6] == "#872181"
    assert ia.COULEURS[0] == "#DDDDDD"   # indisponible
    assert len(set(ia.COULEURS.values())) == len(ia.COULEURS)


def test_grandeur_par_polluant():
    """Particules sur la moyenne journalière, gaz sur le maximum horaire.
    Les confondre fait basculer de plusieurs classes."""
    assert ia.GRANDEUR["PM25"] == "moyenne_journaliere"
    assert ia.GRANDEUR["NO2"] == "max_horaire"
    assert ia.GRANDEUR["O3"] == "max_horaire"


# --------------------------------------------------------------------------- #
# Chaîne journalière
# --------------------------------------------------------------------------- #

def _jour(station, polluant, valeurs, jour="2023-06-15"):
    """Fabrique une journée LOCALE complète, pas 24 heures UTC.

    Piège vérifié ailleurs dans la suite : en été (UTC+2), les 24 heures UTC du
    15 juin couvrent 02:00 locale jusqu'à 01:00 le lendemain — elles chevauchent
    donc DEUX journées locales, et le calcul d'indice en produirait deux au lieu
    d'un. La journée locale démarre à 22:00 UTC la veille.
    """
    debut = pd.Timestamp(f"{jour} 00:00", tz="Europe/Paris").tz_convert("UTC")
    index = pd.date_range(debut, periods=len(valeurs), freq="1h", tz="UTC")
    return pd.DataFrame(
        {"station_id": station, "polluant": polluant,
         "timestamp_utc": index, "valeur": valeurs}
    )


def test_no2_utilise_le_maximum_pas_la_moyenne():
    """23 heures à 10 µg/m³ et une pointe à 200 : la moyenne donnerait « Bon »,
    le maximum horaire donne « Mauvais ». C'est le maximum qui fait foi."""
    valeurs = [10.0] * 23 + [200.0]
    si = ia.sous_indices_journaliers(_jour("A", "NO2", valeurs))
    assert si["sous_indice"].iloc[0] == 4          # 200 → Mauvais
    assert si["max_horaire"].iloc[0] == 200.0


def test_pm25_utilise_la_moyenne_pas_le_maximum():
    valeurs = [5.0] * 23 + [200.0]
    si = ia.sous_indices_journaliers(_jour("A", "PM25", valeurs))
    # moyenne ≈ 13,1 → Moyen, malgré une pointe qui serait « Extrêmement mauvais »
    assert si["sous_indice"].iloc[0] == 2


def test_couverture_insuffisante_invalide_le_jour():
    """Un jour à 5 heures de mesure ne donne pas d'indice : les heures manquantes
    ne sont pas indépendantes des épisodes, et forcer le calcul flatterait le
    résultat."""
    valeurs = [30.0] * 5 + [np.nan] * 19
    si = ia.sous_indices_journaliers(_jour("A", "NO2", valeurs))
    assert np.isnan(si["sous_indice"].iloc[0])


def test_indice_est_le_pire_sous_indice():
    """Règle d'agrégation de l'arrêté, et traçabilité du polluant responsable."""
    panneau = pd.concat([
        _jour("A", "NO2", [10.0] * 24),    # Bon
        _jour("A", "O3", [140.0] * 24),    # Mauvais
        _jour("A", "PM25", [15.0] * 24),   # Moyen
    ])
    indices = ia.indice_par_station(ia.sous_indices_journaliers(panneau))

    assert len(indices) == 1
    assert indices["indice"].iloc[0] == 4
    assert indices["polluant_responsable"].iloc[0] == "O3"
    assert indices["qualificatif"].iloc[0] == "Mauvais"
    assert indices["couleur"].iloc[0] == "#FF5050"


def test_indice_partiel_est_biaise_a_la_baisse():
    """Le maximum d'un sous-ensemble est ≤ celui de l'ensemble complet.

    Comparer un indice calculé sur 2 polluants à l'indice officiel calculé sur 5
    produit donc un **biais optimiste systématique** — l'air paraît meilleur qu'il
    n'est. D'où le filtre sur le nombre de sous-indices disponibles.
    """
    panneau = pd.concat([
        _jour("A", "NO2", [10.0] * 24),
        _jour("A", "PM25", [5.0] * 24),
    ])
    indices = ia.indice_par_station(ia.sous_indices_journaliers(panneau))

    assert indices["n_polluants"].iloc[0] == 2
    assert len(ia.indice_complet_seulement(indices)) == 0, (
        "un indice sur 2 polluants ne doit pas être comparé à l'officiel"
    )


def test_aucune_donnee_ne_plante_pas():
    panneau = _jour("A", "NO2", [np.nan] * 24)
    assert ia.indice_par_station(ia.sous_indices_journaliers(panneau)).empty
