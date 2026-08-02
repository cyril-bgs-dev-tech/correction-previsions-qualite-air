"""Tests des variables de trafic hiérarchisé et de population.

Chaque test fige une distinction que la physique impose et que la donnée brute ne donne
pas : une autoroute n'est pas une rue, un sentier n'est pas une route, et une distance
n'est pas une exposition.
"""

import numpy as np
import pytest

from aq.features import trafic_population as tp
from aq.ingest.geopf import Entite


def route(nature=None, importance=None, voies=None, x=0.0, y=0.0, longueur=1000.0):
    proprietes = {}
    if nature is not None:
        proprietes["nature"] = nature
    if importance is not None:
        proprietes["importance"] = importance
    if voies is not None:
        proprietes["nombre_de_voies"] = voies
    return Entite(x=x, y=y, masse=longueur, proprietes=proprietes)


def commune(population, x, y):
    return Entite(x=x, y=y, masse=1.0, proprietes={"population": population})


# ── Classement : la nature physique prime sur le classement administratif ──

def test_autoroute_reconnue_par_sa_nature():
    assert tp.classer_route(route(nature="Type autoroutier")) == "autoroute"
    assert tp.classer_route(route(nature="Bretelle")) == "autoroute"


def test_le_gabarit_autoroutier_prime_sur_l_importance():
    """Un tronçon de gabarit autoroutier reste une autoroute quel que soit son
    classement administratif : c'est le gabarit qui détermine le trafic."""
    assert tp.classer_route(
        route(nature="Type autoroutier", importance="3")) == "autoroute"


def test_la_nature_courante_ne_decide_pas_de_la_classe():
    """« Route à 1 chaussée » couvre 79 % du réseau : s'en servir comme critère
    rangerait presque tout dans la même classe. C'est `importance` qui hiérarchise."""
    assert tp.classer_route(
        route(nature="Route à 1 chaussée", importance="2")) == "principale"
    assert tp.classer_route(
        route(nature="Route à 1 chaussée", importance="6")) == "locale"


def test_importance_utilisee_quand_la_nature_ne_tranche_pas():
    assert tp.classer_route(route(importance="1")) == "autoroute"
    assert tp.classer_route(route(importance="6")) == "locale"


def test_sentier_ecarte_car_sans_trafic_motorise():
    """**Le piège que ce filtre évite.** Un sentier apporte du linéaire mais aucune
    émission. Sur les stations rurales, où les sentiers abondent, les compter gonflerait
    l'exposition routière exactement là où elle devrait être faible — et le modèle
    apprendrait l'inverse de la réalité."""
    assert tp.classer_route(route(nature="Sentier")) is None


# ── Masse : le trafic n'est pas le linéaire ──

def test_le_nombre_de_voies_pondere_la_longueur():
    """Une section à quatre voies porte davantage de trafic qu'une voie unique de même
    longueur. Les traiter à égalité ferait compter un boulevard comme une ruelle."""
    assert tp.masse_trafic(route(voies=4, longueur=1000)) == 4000.0
    assert tp.masse_trafic(route(voies=1, longueur=1000)) == 1000.0


def test_voies_manquantes_remplacees_par_la_mediane():
    """14 % des tronçons n'ont pas l'attribut, surtout en zone rurale. Les écarter
    biaiserait les stations de fond ; on retient la valeur médiane observée."""
    assert tp.masse_trafic(route(voies=None, longueur=500)) == 1000.0
    assert tp.masse_trafic(route(voies="inconnu", longueur=500)) == 1000.0


# ── Exposition : la décroissance doit se voir ──

def test_exposition_decroit_avec_la_distance():
    proche = [route(x=100.0, y=0.0)]
    loin = [route(x=5000.0, y=0.0)]
    e_proche = tp.exposition_ponderee(0, 0, proche, [1000.0], 300.0)
    e_loin = tp.exposition_ponderee(0, 0, loin, [1000.0], 300.0)
    assert e_proche > 100 * e_loin


def test_lambda_long_porte_plus_loin_qu_un_lambda_court():
    """C'est tout l'intérêt de balayer les échelles : λ court décrit la proximité
    immédiate, λ long l'environnement de fond."""
    entites = [route(x=2000.0, y=0.0)]
    court = tp.exposition_ponderee(0, 0, entites, [1000.0], 300.0)
    long = tp.exposition_ponderee(0, 0, entites, [1000.0], 3000.0)
    assert long > 50 * court


# ── Variables routières : les classes restent séparées ──

def test_les_classes_ne_sont_pas_fusionnees():
    """Fusionner les classes en un indice unique supposerait un rapport d'émission entre
    elles, que la donnée ne fournit pas. Les garder séparées laisse le modèle
    l'apprendre — même logique que la séparation des essences forestières."""
    routes = [route(nature="Type autoroutier", x=500.0, voies=6),
              route(x=100.0, importance="5", voies=2)]
    v = tp.variables_routieres(0, 0, routes)
    assert v["route_autoroute_lambda1000m"] > 0
    assert v["route_locale_lambda1000m"] > 0
    assert "route_autoroute_dist_min_m" in v and "route_locale_dist_min_m" in v


def test_classe_absente_donne_une_distance_indefinie_pas_zero():
    """Une distance de zéro se lirait comme « autoroute au pied de la station » —
    exactement l'inverse de la réalité. NaN dit « pas dans le rayon regardé »."""
    v = tp.variables_routieres(0, 0, [route(importance="6", x=50.0)])
    assert np.isnan(v["route_autoroute_dist_min_m"])
    assert v["route_autoroute_lambda1000m"] == 0.0


# ── Population : la taille compte autant que la distance ──

def test_une_metropole_lointaine_pese_plus_qu_un_village_proche():
    """**La raison d'être de cette variable.** Une simple distance au centre-ville
    placerait sur le même plan un village et une métropole à égale distance. Ici,
    500 000 habitants à 15 km pèsent plus que 800 habitants à 2 km."""
    communes = [commune(500_000, 15_000.0, 0.0), commune(800, 2_000.0, 0.0)]
    v = tp.variables_population(0, 0, communes)
    assert v["population_pole_dominant"] == 500_000
    assert v["distance_pole_dominant_m"] == pytest.approx(15_000.0)


def test_exposition_population_decroit_avec_l_echelle():
    communes = [commune(100_000, 10_000.0, 0.0)]
    v = tp.variables_population(0, 0, communes)
    assert v["population_lambda2000m"] < v["population_lambda20000m"]


def test_aucune_commune_ne_plante_pas():
    v = tp.variables_population(0, 0, [])
    assert v["population_lambda5000m"] == 0.0
    assert np.isnan(v["distance_pole_dominant_m"])


def test_population_absente_traitee_comme_zero():
    """Une commune sans population renseignée ne doit pas propager de NaN dans la somme
    — elle contribue simplement pour rien."""
    communes = [Entite(x=1000.0, y=0.0, masse=1.0, proprietes={"population": None}),
                commune(5_000, 2_000.0, 0.0)]
    v = tp.variables_population(0, 0, communes)
    assert np.isfinite(v["population_lambda5000m"])
    assert v["population_pole_dominant"] == 5_000
