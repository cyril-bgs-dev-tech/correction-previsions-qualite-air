"""Tests du regroupement de stations pour l'extraction géospatiale.

Le regroupement est une optimisation : il doit donc être **strictement neutre** sur
le résultat. Ces tests vérifient qu'aucune station n'est perdue, qu'aucune n'hérite
d'objets hors de son rayon, et que les groupes restent d'une taille exploitable.
"""

import numpy as np
import pytest

from aq.features import extraction_groupee as eg
from aq.ingest.geopf import Entite


def _entite(x, y, masse=1.0):
    return Entite(x=x, y=y, masse=masse, proprietes={})


# --------------------------------------------------------------------------- #
# Regroupement
# --------------------------------------------------------------------------- #

def test_stations_proches_regroupees():
    x = np.array([0.0, 5_000.0, 10_000.0])
    y = np.array([0.0, 0.0, 0.0])
    groupes = eg.grouper_stations(x, y, seuil_m=30_000)
    assert len(groupes) == 1


def test_stations_eloignees_separees():
    x = np.array([0.0, 500_000.0])
    y = np.array([0.0, 0.0])
    groupes = eg.grouper_stations(x, y, seuil_m=30_000)
    assert len(groupes) == 2


def test_aucune_station_perdue_ni_dupliquee():
    """Invariant fondamental : le regroupement est une partition."""
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 400_000, 200)
    y = rng.uniform(0, 400_000, 200)
    groupes = eg.grouper_stations(x, y, seuil_m=30_000)

    indices = [i for groupe in groupes for i in groupe]
    assert sorted(indices) == list(range(200))


def test_groupe_trop_etendu_est_scinde():
    """La proximité transitive peut enchaîner des stations sur des centaines de
    kilomètres — une chaîne le long d'une vallée suffit. L'emprise deviendrait
    ingérable, d'où le découpage."""
    # Chaîne de 40 stations espacées de 20 km : 780 km d'étendue en transitif.
    x = np.arange(40, dtype="float64") * 20_000
    y = np.zeros(40)

    sans_limite = eg.grouper_stations(x, y, seuil_m=30_000, cote_max_m=1e9)
    avec_limite = eg.grouper_stations(x, y, seuil_m=30_000, cote_max_m=80_000)

    assert len(sans_limite) == 1, "en transitif, la chaîne forme un seul groupe"
    assert len(avec_limite) > 1
    for groupe in avec_limite:
        etendue = x[groupe].max() - x[groupe].min()
        assert etendue <= 80_000


def test_scission_conserve_toutes_les_stations():
    x = np.arange(50, dtype="float64") * 15_000
    y = np.zeros(50)
    groupes = eg.grouper_stations(x, y, seuil_m=30_000, cote_max_m=60_000)
    assert sorted(i for g in groupes for i in g) == list(range(50))


def test_stations_confondues_ne_bouclent_pas():
    """Cas dégénéré : plusieurs stations exactement au même point. La médiane ne
    sépare rien, il faut une coupe de secours pour que la récursion termine."""
    x = np.zeros(10)
    y = np.zeros(10)
    groupes = eg.grouper_stations(x, y, seuil_m=1_000, cote_max_m=100)
    assert sorted(i for g in groupes for i in g) == list(range(10))


# --------------------------------------------------------------------------- #
# Emprise
# --------------------------------------------------------------------------- #

def test_emprise_couvre_le_rayon_de_chaque_station():
    """Chaque station du groupe, y compris en bordure, doit disposer de son rayon
    complet — sinon ses variables d'exposition seraient amputées sans le signaler."""
    x = np.array([0.0, 40_000.0])
    y = np.array([0.0, 10_000.0])
    rayon = 30_000.0

    cx, cy, demi = eg.emprise_groupe(x, y, [0, 1], rayon)

    for i in (0, 1):
        assert cx - demi <= x[i] - rayon
        assert cx + demi >= x[i] + rayon
        assert cy - demi <= y[i] - rayon
        assert cy + demi >= y[i] + rayon


def test_emprise_station_unique_vaut_le_rayon():
    cx, cy, demi = eg.emprise_groupe(np.array([100.0]), np.array([200.0]), [0], 5_000.0)
    assert (cx, cy) == (100.0, 200.0)
    assert demi == 5_000.0


# --------------------------------------------------------------------------- #
# Filtrage — la neutralité du regroupement
# --------------------------------------------------------------------------- #

def test_filtrage_retire_les_objets_hors_rayon():
    """Sans filtre, une station de bordure hériterait d'objets au-delà de son rayon,
    et ses variables dépendraient de sa position dans le groupe — un biais qui
    n'apparaîtrait dans aucune vérification."""
    entites = [_entite(0.0, 0.0), _entite(10_000.0, 0.0), _entite(50_000.0, 0.0)]
    retenues = eg.filtrer_autour(entites, 0.0, 0.0, rayon_m=30_000)

    assert len(retenues) == 2
    assert all(np.hypot(e.x, e.y) <= 30_000 for e in retenues)


def test_filtrage_inclut_la_bordure_exacte():
    entites = [_entite(30_000.0, 0.0)]
    assert len(eg.filtrer_autour(entites, 0.0, 0.0, 30_000)) == 1


def test_filtrage_sur_liste_vide():
    assert eg.filtrer_autour([], 0.0, 0.0, 1_000) == []


def test_regroupement_donne_le_meme_resultat_que_station_par_station():
    """Test de neutralité : l'optimisation ne doit RIEN changer au résultat.

    On simule une extraction groupée puis on la compare à ce qu'aurait donné une
    requête par station sur le même univers d'objets.
    """
    rng = np.random.default_rng(1)
    univers = [_entite(a, b) for a, b in rng.uniform(-60_000, 60_000, (300, 2))]
    stations = np.array([[0.0, 0.0], [20_000.0, 5_000.0], [-15_000.0, 10_000.0]])

    for sx, sy in stations:
        groupe = eg.filtrer_autour(univers, sx, sy, 30_000)
        individuel = [
            e for e in univers if np.hypot(e.x - sx, e.y - sy) <= 30_000
        ]
        assert {(e.x, e.y) for e in groupe} == {(e.x, e.y) for e in individuel}


def test_resume_decrit_chaque_groupe():
    x = np.array([0.0, 5_000.0, 300_000.0])
    y = np.zeros(3)
    groupes = eg.grouper_stations(x, y, seuil_m=30_000)
    resume = eg.resume_groupes(x, y, groupes, 30_000)

    assert len(resume) == len(groupes)
    assert resume["n_stations"].sum() == 3
    assert (resume["surface_km2"] > 0).all()
