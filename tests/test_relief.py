"""Tests des indices topographiques.

Reliefs synthétiques : on vérifie que les indices disent bien ce qu'ils prétendent
dire, sur des formes dont la réponse est connue d'avance.
"""

import numpy as np
import pytest

from aq.features import relief


def test_dalle_nommee_par_son_coin_sud_ouest():
    """Les dalles GLO-30 portent le nom de leur coin sud-ouest. Arrondir au plus proche
    viserait la mauvaise dalle une fois sur deux — 404, pas un voisin plausible."""
    assert "N43_00_E001" in relief.url_dalle(1.44, 43.60)
    assert "N43_00_E001" in relief.url_dalle(1.99, 43.99)
    assert "N44_00_E002" in relief.url_dalle(2.01, 44.01)


def test_dalle_a_l_ouest_de_greenwich():
    """Brest est à −4,49° : la dalle est W005, pas W004. Le `floor` d'un négatif
    descend, il ne tronque pas vers zéro."""
    assert "W005" in relief.url_dalle(-4.4866, 48.386)
    assert "N48" in relief.url_dalle(-4.4866, 48.386)


def test_degre_de_longitude_plus_court_que_de_latitude_en_france():
    """Un degré de longitude vaut ~80 km à 45°, contre ~111 km pour la latitude.
    Confondre les deux étirerait la fenêtre d'analyse de 40 %."""
    d_lon, d_lat = relief.degres_par_metre(45.0)
    assert d_lon > d_lat, "il faut plus de degrés de longitude pour un même mètre"
    assert 1 / d_lon == pytest.approx(78_700, rel=0.02)
    assert 1 / d_lat == pytest.approx(111_320, rel=0.001)


def test_tpi_positif_sur_une_crete():
    voisinage = np.full((11, 11), 100.0)
    assert relief.indice_position_topographique(voisinage, 250.0) == pytest.approx(150.0)


def test_tpi_negatif_dans_une_vallee():
    """Le cas Chamonix : un point bas entouré de sommets. L'altitude brute le range
    avec les hauteurs, le TPI l'en sépare."""
    voisinage = np.full((11, 11), 2500.0)
    voisinage[5, 5] = 1035.0
    tpi = relief.indice_position_topographique(voisinage, 1035.0)
    assert tpi < -1000, "un fond de vallée doit être fortement négatif"


def test_tpi_nul_sur_une_plaine():
    plaine = np.full((9, 9), 120.0)
    assert relief.indice_position_topographique(plaine, 120.0) == pytest.approx(0.0)


def test_profondeur_vallee_resiste_a_un_pixel_aberrant():
    """Un seul pixel aberrant — antenne, artefact stéréo — ne doit pas fixer à lui seul
    la profondeur de toute une vallée. D'où le 90ᵉ centile plutôt que le maximum."""
    voisinage = np.full((20, 20), 1200.0)
    voisinage[0, 0] = 9000.0            # aberration
    profondeur = relief.profondeur_vallee(voisinage, 1000.0)
    assert profondeur == pytest.approx(200.0, abs=1.0), "l'aberration doit être ignorée"


def test_pente_nulle_sur_un_plateau_et_forte_sur_un_versant():
    plateau = np.full((10, 10), 500.0)
    assert relief.pente_moyenne(plateau, 30.0) == pytest.approx(0.0)

    # Versant à 30 m de dénivelé par pixel de 30 m : 45°.
    versant = np.tile(np.arange(10, dtype="float64") * 30.0, (10, 1))
    assert relief.pente_moyenne(versant, 30.0) == pytest.approx(45.0, abs=1.0)


def test_rugosite_distingue_plaine_et_relief():
    plaine = np.full((10, 10), 100.0)
    tourmente = np.random.default_rng(0).normal(1000, 200, (30, 30))
    assert relief.rugosite(plaine) == pytest.approx(0.0)
    assert relief.rugosite(tourmente) > 100


def test_indices_sur_voisinage_vide_donnent_nan():
    """Une fenêtre hors MNT (mer, bord de dalle) doit donner NaN, pas 0 : un zéro se
    lirait comme « plaine au niveau de la mer », valeur parfaitement plausible."""
    vide = np.full((5, 5), np.nan)
    assert np.isnan(relief.indice_position_topographique(vide, 100.0))
    assert np.isnan(relief.profondeur_vallee(vide, 100.0))
    assert np.isnan(relief.rugosite(vide))
