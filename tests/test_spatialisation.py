"""Tests de la chaîne de spatialisation.

C'est l'étape qui referme l'écart à l'indice officiel : mesuré, elle fait passer
l'accord de 42,8 % à 90,9 % et annule un biais de −0,72 classe. Ces tests figent
ses propriétés, notamment celles qui sont des LIMITES à connaître.
"""

import json

import numpy as np
import pandas as pd
import pytest

from aq.models import spatialisation as sp


# --------------------------------------------------------------------------- #
# Grille
# --------------------------------------------------------------------------- #

def test_grille_alignee_sur_la_resolution():
    """L'alignement garantit qu'une même maille porte les mêmes coordonnées d'une
    exécution à l'autre — sans quoi deux calculs ne seraient pas superposables."""
    grille = sp.grille_reguliere(1_234, 5_678, 11_234, 15_678, resolution_m=1_000)
    assert (grille["x"] % 1_000 == 0).all()
    assert (grille["y"] % 1_000 == 0).all()


def test_grille_couvre_l_emprise_demandee():
    grille = sp.grille_reguliere(0, 0, 10_000, 5_000, resolution_m=1_000)
    assert grille["x"].min() <= 0 and grille["x"].max() >= 10_000
    assert grille["y"].min() <= 0 and grille["y"].max() >= 5_000


def test_resolution_gouverne_le_nombre_de_mailles():
    fine = sp.grille_reguliere(0, 0, 10_000, 10_000, resolution_m=1_000)
    grossiere = sp.grille_reguliere(0, 0, 10_000, 10_000, resolution_m=2_000)
    assert len(fine) > len(grossiere)


# --------------------------------------------------------------------------- #
# Interpolation
# --------------------------------------------------------------------------- #

def test_interpolation_restitue_la_valeur_a_la_station():
    """Au point de mesure, l'IDW doit rendre la valeur observée."""
    valeur = sp.interpoler_idw([0.0], [0.0], [0.0, 10_000.0], [0.0, 0.0], [42.0, 10.0])
    assert valeur[0] == pytest.approx(42.0, rel=1e-3)


def test_influence_decroit_avec_la_distance():
    proche = sp.interpoler_idw([1_000.0], [0.0], [0.0, 20_000.0], [0.0, 0.0], [100.0, 0.0])
    loin = sp.interpoler_idw([19_000.0], [0.0], [0.0, 20_000.0], [0.0, 0.0], [100.0, 0.0])
    assert proche[0] > loin[0]


def test_idw_ne_peut_pas_extrapoler():
    """**Limite structurelle, à énoncer en présentation.**

    L'IDW est une moyenne pondérée : son résultat reste borné par l'intervalle des
    observations. Elle ne prédira donc jamais un maximum supérieur au maximum mesuré,
    alors que le modèle officiel, lui, modélise et peut dépasser. C'est une cause
    identifiée du biais résiduel — et une limite que la LUR n'a pas.
    """
    rng = np.random.default_rng(0)
    xs = rng.uniform(0, 50_000, 10)
    ys = rng.uniform(0, 50_000, 10)
    v = rng.uniform(20.0, 80.0, 10)

    cible = sp.grille_reguliere(0, 0, 50_000, 50_000, resolution_m=5_000)
    champ = sp.interpoler_idw(cible["x"], cible["y"], xs, ys, v)

    assert champ.min() >= v.min() - 1e-9
    assert champ.max() <= v.max() + 1e-9


def test_valeurs_manquantes_ignorees():
    """Une station en panne ne doit pas contaminer tout le champ."""
    valeur = sp.interpoler_idw(
        [5_000.0], [0.0], [0.0, 10_000.0], [0.0, 0.0], [10.0, np.nan]
    )
    assert valeur[0] == pytest.approx(10.0)


def test_aucune_source_donne_nan():
    """Sans observation, on renvoie NaN plutôt qu'une valeur inventée."""
    assert np.isnan(sp.interpoler_idw([0.0], [0.0], [], [], [])[0])


def test_nombre_de_voisins_limite_le_lissage():
    """Sans restriction du voisinage, une station de l'autre bout de la région
    contribuerait encore, et le champ perdrait tout contraste local."""
    rng = np.random.default_rng(1)
    xs = rng.uniform(0, 200_000, 40)
    ys = rng.uniform(0, 200_000, 40)
    v = rng.uniform(0, 100, 40)
    cible = sp.grille_reguliere(0, 0, 200_000, 200_000, resolution_m=20_000)

    peu = sp.interpoler_idw(cible["x"], cible["y"], xs, ys, v, n_voisins=3)
    beaucoup = sp.interpoler_idw(cible["x"], cible["y"], xs, ys, v, n_voisins=40)
    assert peu.std() > beaucoup.std()


# --------------------------------------------------------------------------- #
# Zones et agrégation
# --------------------------------------------------------------------------- #

def _zone_carree(code, x0, y0, cote):
    return {
        "properties": {"code_siren": code},
        "geometry": json.loads(
            json.dumps(
                {
                    "type": "Polygon",
                    "coordinates": [[
                        [x0, y0], [x0 + cote, y0],
                        [x0 + cote, y0 + cote], [x0, y0 + cote], [x0, y0],
                    ]],
                }
            )
        ),
    }


def test_mailles_rattachees_a_leur_zone():
    grille = sp.grille_reguliere(0, 0, 20_000, 10_000, resolution_m=5_000)
    zones = [_zone_carree("A", 0, 0, 10_000), _zone_carree("B", 12_000, 0, 8_000)]

    indexee = sp.indexer_grille_par_zone(grille, zones)

    assert set(indexee["code_zone"]) == {"A", "B"}
    # Les mailles hors de toute zone sont écartées, pas affectées arbitrairement.
    assert len(indexee) < len(grille)


def test_agregation_expose_maximum_et_moyenne():
    """L'officiel agrège par le MAXIMUM. La moyenne est conservée pour comparaison :
    l'écart entre les deux mesure l'hétérogénéité interne de la zone, donc la part
    du biais ponctuel imputable à sa taille."""
    valorisee = pd.DataFrame(
        {"code_zone": ["A", "A", "A", "B"], "valeur": [10.0, 20.0, 60.0, 5.0]}
    )
    agrege = sp.agreger_par_zone(valorisee).set_index("code_zone")

    assert agrege.loc["A", "maximum"] == 60.0
    assert agrege.loc["A", "moyenne"] == pytest.approx(30.0)
    assert agrege.loc["A", "n_mailles"] == 3
    assert agrege.loc["B", "maximum"] == agrege.loc["B", "moyenne"] == 5.0


def test_maximum_superieur_ou_egal_a_la_moyenne():
    """Propriété qui explique le biais mesuré : un maximum sur une surface est
    nécessairement ≥ une valeur ponctuelle."""
    rng = np.random.default_rng(2)
    valorisee = pd.DataFrame(
        {"code_zone": rng.choice(["A", "B", "C"], 300), "valeur": rng.uniform(0, 100, 300)}
    )
    agrege = sp.agreger_par_zone(valorisee)
    assert (agrege["maximum"] >= agrege["moyenne"]).all()
