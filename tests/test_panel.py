"""Tests de l'assemblage en panneau et des indicateurs de qualité.

Le cœur du sujet : une couverture rapportée à la grille globale confond trois
situations distinctes. Ces tests figent la distinction, parce que s'en remettre au
seul chiffre global conduit à écarter des stations parfaitement saines.
"""

import numpy as np
import pandas as pd
import pytest

from aq.ingest import panel


def _serie(station, polluant, debut, valeurs):
    """Fabrique une série horaire à partir d'une liste de valeurs (NaN = trou)."""
    index = pd.date_range(debut, periods=len(valeurs), freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "station_id": station,
            "polluant": polluant,
            "timestamp_utc": index,
            "valeur": valeurs,
            "flag_qualite": "valide",
            "n_points": 1,
        }
    )


def test_reindexage_rend_les_trous_explicites():
    """Une heure absente et une heure vide ne sont pas la même chose : la première
    est invisible pour un modèle de série temporelle, la seconde est un fait."""
    partiel = pd.concat(
        [
            _serie("A", "NO2", "2020-01-01 00:00", [1.0, 2.0]),
            _serie("A", "NO2", "2020-01-01 05:00", [3.0]),
        ]
    )
    plein = panel.reindexer_grille(partiel)
    assert len(plein) == 6
    assert plein["valeur"].isna().sum() == 3


def test_grille_commune_a_toutes_les_series():
    """Sans grille commune, une station démarrant tard paraîtrait complète et son
    défaut de couverture disparaîtrait de l'analyse."""
    deux = pd.concat(
        [
            _serie("A", "NO2", "2020-01-01 00:00", [1.0] * 10),
            _serie("B", "NO2", "2020-01-01 06:00", [2.0] * 4),
        ]
    )
    plein = panel.reindexer_grille(deux)
    assert (plein.groupby("station_id").size() == 10).all()
    assert plein[plein["station_id"] == "B"]["valeur"].isna().sum() == 6


def test_station_ouverte_tard_nest_pas_degradee():
    """Cas « Montpellier Antigone » : 8 % de couverture sur la grille, mais ~100 %
    sur sa propre durée de vie. Ce n'est pas un défaut de qualité, c'est une
    censure à gauche — et l'ancien calcul la condamnait à tort.
    """
    tardive = _serie("A", "NO2", "2020-01-01 00:00", [np.nan] * 90 + [5.0] * 10)
    rapport = panel.rapport_qualite(tardive).iloc[0]

    assert rapport["couverture_grille"] == pytest.approx(0.10)
    assert rapport["couverture_active"] == pytest.approx(1.0)
    assert rapport["plus_long_trou_interne_h"] == 0
    assert rapport["debut_mesure"] == pd.Timestamp("2020-01-04 18:00", tz="UTC")


def test_mesure_interrompue_est_detectee():
    """Cas « Perpignan bd Pyrénées » : censure à DROITE. La station reste active
    mais la mesure s'arrête — fait à documenter, pas à confondre avec un trou."""
    interrompue = _serie("A", "PM25", "2020-01-01 00:00", [3.0] * 10 + [np.nan] * 90)
    rapport = panel.rapport_qualite(interrompue).iloc[0]

    assert rapport["couverture_active"] == pytest.approx(1.0)
    assert rapport["fin_mesure"] == pd.Timestamp("2020-01-01 09:00", tz="UTC")
    assert rapport["plus_long_trou_interne_h"] == 0


def test_trou_interne_est_le_seul_vrai_defaut():
    """Seul un trou entre deux mesures relève du critère réglementaire."""
    trouee = _serie(
        "A", "O3", "2020-01-01 00:00", [1.0] * 10 + [np.nan] * 20 + [2.0] * 10
    )
    rapport = panel.rapport_qualite(trouee).iloc[0]

    assert rapport["couverture_active"] == pytest.approx(20 / 40)
    assert rapport["plus_long_trou_interne_h"] == 20


def test_capteur_gele_detecte():
    """Une valeur répétée à l'identique pendant des heures signale un capteur bloqué,
    pas une atmosphère stable. Défaut classique, invisible dans les statistiques."""
    gelee = _serie("A", "NO2", "2020-01-01 00:00", [7.0] * 12 + [1.0, 2.0, 3.0])
    rapport = panel.rapport_qualite(gelee).iloc[0]
    assert rapport["repetition_max_h"] == 12


def test_valeurs_negatives_comptees_non_ecretees():
    """Les négatives proches de la limite de détection sont du bruit instrumental
    normal. On les compte pour les surveiller ; les ramener à zéro fabriquerait un
    biais positif systématique sur les faibles concentrations."""
    avec_negatives = _serie("A", "PM25", "2020-01-01 00:00", [-0.5, -1.2, 3.0, 4.0])
    rapport = panel.rapport_qualite(avec_negatives).iloc[0]

    assert rapport["n_negatives"] == 2
    assert rapport["median"] == pytest.approx(1.25)  # les négatives sont conservées


def test_serie_entierement_vide_ne_plante_pas():
    """Une station morte existe dans les données réelles : le rapport doit la
    décrire, pas échouer."""
    morte = _serie("A", "O3", "2020-01-01 00:00", [np.nan] * 24)
    rapport = panel.rapport_qualite(morte).iloc[0]

    assert rapport["n_valides"] == 0
    assert rapport["couverture_grille"] == 0.0
    assert pd.isna(rapport["couverture_active"])


def test_points_de_prelevement_dupliques_moyennes():
    """Une station peut exposer deux points de prélèvement pour un même polluant
    (remplacement d'analyseur). Les empiler créerait des horodatages en double."""
    brut = pd.concat(
        [
            pd.DataFrame(
                {
                    "point_prelevement": "FR/SPO-FR12031_8",
                    "polluant": "NO2",
                    "timestamp_utc": pd.date_range(
                        "2020-01-01", periods=3, freq="1h", tz="UTC"
                    ),
                    "valeur": [10.0, 20.0, 30.0],
                    "flag_qualite": "valide",
                }
            ),
            pd.DataFrame(
                {
                    "point_prelevement": "FR/SPO-FR12031_8b",
                    "polluant": "NO2",
                    "timestamp_utc": pd.date_range(
                        "2020-01-01", periods=3, freq="1h", tz="UTC"
                    ),
                    "valeur": [12.0, 22.0, 32.0],
                    "flag_qualite": "valide",
                }
            ),
        ]
    )
    p = panel.construire_panneau(brut)

    assert len(p) == 3, "un horodatage par station, polluant et heure"
    assert not p.duplicated(["station_id", "polluant", "timestamp_utc"]).any()
    assert p["valeur"].tolist() == [11.0, 21.0, 31.0]
