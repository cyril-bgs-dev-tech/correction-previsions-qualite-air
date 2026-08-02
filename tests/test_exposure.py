"""Tests des variables d'exposition géospatiale.

Ces tests encodent la PHYSIQUE attendue, pas seulement l'arithmétique : une source
plus massive compte davantage, une source plus lointaine compte moins, et une source
sous le vent ne compte pas du tout. Un signe inversé ici retournerait silencieusement
toutes les conclusions d'attribution.
"""

import numpy as np
import pytest

from aq.features import exposure


# --------------------------------------------------------------------------- #
# Géométrie
# --------------------------------------------------------------------------- #

def test_distances_en_metres():
    d = exposure.distances([0.0], [0.0], [3_000.0], [4_000.0])
    assert d.shape == (1, 1)
    assert d[0, 0] == pytest.approx(5_000.0)


def test_azimut_suit_la_convention_geographique():
    """0° = nord, sens horaire — pour se comparer directement à la direction du vent."""
    # Source plein nord, plein est, plein sud, plein ouest.
    az = exposure.azimuts([0.0], [0.0], [0.0, 100.0, 0.0, -100.0], [100.0, 0.0, -100.0, 0.0])
    np.testing.assert_allclose(az[0], [0.0, 90.0, 180.0, 270.0], atol=1e-9)


def test_distance_plus_proche_sans_source():
    """Sans source, la distance est infinie — pas zéro, qui signifierait « collée »."""
    d = exposure.distance_plus_proche([0.0], [0.0], [], [])
    assert np.isinf(d[0])


# --------------------------------------------------------------------------- #
# Exposition pondérée — le cœur du sujet
# --------------------------------------------------------------------------- #

def test_la_masse_compte_autant_que_la_distance():
    """Le point central : à distance égale, un massif pèse plus qu'un bosquet.

    Une variable de distance seule les confondrait — c'est précisément la limite
    qu'une exposition pondérée existe pour lever.
    """
    commun = dict(x_recepteurs=[0.0], y_recepteurs=[0.0],
                  x_sources=[500.0], y_sources=[0.0], lambda_m=1_000.0)
    bosquet = exposure.exposition_ponderee(**commun, poids_sources=[30_000.0])
    massif = exposure.exposition_ponderee(**commun, poids_sources=[300_000_000.0])

    assert massif[0] > bosquet[0]
    assert massif[0] / bosquet[0] == pytest.approx(10_000.0)


def test_decroissance_exponentielle_avec_la_distance():
    """À λ, la contribution doit être divisée par e."""
    proche = exposure.exposition_ponderee([0.0], [0.0], [0.0], [0.0], lambda_m=1_000.0,
                                          distance_min_m=0.0)
    a_lambda = exposure.exposition_ponderee([0.0], [0.0], [1_000.0], [0.0],
                                            lambda_m=1_000.0)
    assert a_lambda[0] / proche[0] == pytest.approx(np.exp(-1.0), rel=1e-3)


def test_lambda_gouverne_l_echelle_d_influence():
    """Un λ court ignore les sources lointaines, un λ long les intègre.

    C'est ce qui rend le balayage de λ informatif : le λ retenu par le modèle
    révèle l'échelle spatiale du mécanisme (NO₂ ~ centaines de mètres, ozone
    d'origine biogénique ~ dizaines de kilomètres).
    """
    lointaine = dict(x_recepteurs=[0.0], y_recepteurs=[0.0],
                     x_sources=[20_000.0], y_sources=[0.0])
    court = exposure.exposition_ponderee(**lointaine, lambda_m=300.0)
    long = exposure.exposition_ponderee(**lointaine, lambda_m=30_000.0)

    assert court[0] < 1e-20
    assert long[0] > 0.5


def test_sources_multiples_s_additionnent():
    deux = exposure.exposition_ponderee([0.0], [0.0], [1_000.0, 1_000.0],
                                        [0.0, 0.0], lambda_m=1_000.0)
    une = exposure.exposition_ponderee([0.0], [0.0], [1_000.0], [0.0], lambda_m=1_000.0)
    assert deux[0] == pytest.approx(2 * une[0])


def test_plancher_de_distance_evite_la_domination_d_une_source():
    """Sans plancher, une source confondue avec le récepteur écraserait tout le
    reste du paysage."""
    colle = exposure.exposition_ponderee([0.0], [0.0], [0.0], [0.0],
                                         lambda_m=1_000.0, distance_min_m=1.0)
    assert np.isfinite(colle[0])
    assert colle[0] <= 1.0


def test_lambda_negatif_rejete():
    with pytest.raises(ValueError, match="strictement positif"):
        exposure.exposition_ponderee([0.0], [0.0], [1.0], [1.0], lambda_m=-100.0)


def test_poids_de_longueur_incompatible_rejete():
    with pytest.raises(ValueError, match="incompatibles"):
        exposure.exposition_ponderee([0.0], [0.0], [1.0, 2.0], [1.0, 2.0],
                                     poids_sources=[1.0])


def test_balayage_produit_une_colonne_par_lambda():
    df = exposure.balayer_lambdas([0.0, 5_000.0], [0.0, 0.0], [1_000.0], [0.0],
                                  prefixe="foret")
    assert list(df.columns) == [
        f"foret_lambda{int(lam)}m" for lam in exposure.LAMBDAS_DEFAUT
    ]
    assert len(df) == 2
    # Le récepteur proche est toujours plus exposé, quel que soit λ.
    assert (df.iloc[0] >= df.iloc[1]).all()


# --------------------------------------------------------------------------- #
# Exposition anisotrope — le levier de performance
# --------------------------------------------------------------------------- #

def test_source_au_vent_compte_source_sous_le_vent_ne_compte_pas():
    """Le test qui fonde toute la famille 3.

    Source plein nord. Vent de nord (direction 0°) : la source est au vent, elle
    influence le récepteur. Vent de sud (180°) : elle est sous le vent, sa
    contribution doit être nulle.
    """
    commun = dict(x_recepteurs=[0.0], y_recepteurs=[0.0],
                  x_sources=[0.0], y_sources=[5_000.0], lambda_m=10_000.0)
    au_vent = exposure.exposition_au_vent(**commun, direction_vent_deg=[0.0])
    sous_le_vent = exposure.exposition_au_vent(**commun, direction_vent_deg=[180.0])

    assert au_vent[0] > 0.5
    assert sous_le_vent[0] == 0.0


def test_ouverture_du_secteur_respectee():
    """Au-delà de la demi-ouverture, la contribution est strictement nulle."""
    commun = dict(x_recepteurs=[0.0], y_recepteurs=[0.0],
                  x_sources=[0.0], y_sources=[5_000.0], lambda_m=10_000.0,
                  demi_ouverture_deg=45.0)
    dans = exposure.exposition_au_vent(**commun, direction_vent_deg=[30.0])
    hors = exposure.exposition_au_vent(**commun, direction_vent_deg=[60.0])

    assert dans[0] > 0.0
    assert hors[0] == 0.0


def test_vent_indetermine_donne_exposition_nulle():
    """Sans direction (vent nul), aucune source ne peut être déclarée au vent :
    on renvoie zéro plutôt qu'une valeur arbitraire."""
    e = exposure.exposition_au_vent([0.0], [0.0], [0.0], [5_000.0],
                                    direction_vent_deg=[np.nan], lambda_m=10_000.0)
    assert e[0] == 0.0


def test_exposition_au_vent_bornee_par_l_isotrope():
    """Le noyau angulaire ne peut qu'atténuer : l'anisotrope reste inférieure ou
    égale à l'isotrope, jamais supérieure."""
    sources_x = np.array([0.0, 3_000.0, -3_000.0, 0.0])
    sources_y = np.array([5_000.0, 0.0, 0.0, -5_000.0])
    iso = exposure.exposition_ponderee([0.0], [0.0], sources_x, sources_y,
                                       lambda_m=10_000.0)
    aniso = exposure.exposition_au_vent([0.0], [0.0], sources_x, sources_y,
                                        direction_vent_deg=[0.0], lambda_m=10_000.0)
    assert aniso[0] <= iso[0]


def test_nombre_de_directions_doit_egaler_le_nombre_de_recepteurs():
    with pytest.raises(ValueError, match="directions"):
        exposure.exposition_au_vent([0.0, 1.0], [0.0, 1.0], [0.0], [1.0],
                                    direction_vent_deg=[0.0])


# --------------------------------------------------------------------------- #
# Couronnes concentriques (forme LUR classique)
# --------------------------------------------------------------------------- #

def test_couronnes_sont_cumulatives():
    df = exposure.surface_par_couronne(
        [0.0], [0.0], [50.0, 500.0, 2_000.0], [0.0, 0.0, 0.0],
        poids_sources=[1.0, 1.0, 1.0], rayons=(100.0, 1_000.0, 5_000.0),
    )
    assert df["buffer_100m"].iloc[0] == 1.0
    assert df["buffer_1000m"].iloc[0] == 2.0
    assert df["buffer_5000m"].iloc[0] == 3.0


def test_couronnes_sans_source():
    df = exposure.surface_par_couronne([0.0], [0.0], [], [], rayons=(100.0, 1_000.0))
    assert (df.iloc[0] == 0.0).all()
