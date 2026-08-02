"""Tests du modèle LUR.

Le régime est celui des très petits échantillons (~23 stations) face à des dizaines
de variables corrélées. Ces tests vérifient que les garde-fous tiennent : contrainte
de signe, unicité par famille, et absence de fuite dans la validation.
"""

import numpy as np
import pandas as pd
import pytest

from aq.models import lur


def test_famille_regroupe_les_lambdas_d_une_meme_couche():
    """Tous les λ d'une couche appartiennent à la même famille : en retenir deux
    reviendrait à compter deux fois le même effet."""
    assert lur.famille("chene_lambda1000m") == lur.famille("chene_lambda30000m")
    assert lur.famille("chene_lambda1000m") != lur.famille("conifere_lambda1000m")
    assert lur.famille("route_dist_min_m") != lur.famille("route_lambda100m")


def test_signe_attendu_selon_le_mecanisme():
    """Le trafic augmente le NO₂ ; une distance plus grande à la source le réduit.
    Les forêts sont ambivalentes (source de précurseurs et puits par dépôt)."""
    assert lur.signe_attendu("route_lambda300m") == +1
    assert lur.signe_attendu("route_dist_min_m") == -1
    assert lur.signe_attendu("chene_lambda10000m") == 0


def _jeu_synthetique(n=40, bruit=1.0, graine=0):
    """Concentration engendrée par le trafic seul, plus des variables parasites."""
    rng = np.random.default_rng(graine)
    route = rng.uniform(0, 100, n)
    X = pd.DataFrame(
        {
            "route_lambda300m": route,
            "route_lambda1000m": route * 0.9 + rng.normal(0, 1, n),  # quasi-colinéaire
            "chene_lambda10000m": rng.uniform(0, 50, n),             # parasite
            "conifere_lambda3000m": rng.uniform(0, 50, n),           # parasite
        }
    )
    y = 10.0 + 0.5 * route + rng.normal(0, bruit, n)
    return X, y


def test_retrouve_le_predicteur_veritable():
    X, y = _jeu_synthetique()
    modele = lur.ajuster(X, y)
    assert modele.variables[0].startswith("route")
    assert modele.r2_ajuste > 0.9


def test_une_seule_variable_par_famille():
    """Deux λ de la même couche ne peuvent pas être retenus ensemble."""
    X, y = _jeu_synthetique()
    modele = lur.ajuster(X, y, max_variables=4)
    familles = [lur.famille(v) for v in modele.variables]
    assert len(familles) == len(set(familles))


def test_contrainte_de_signe_rejette_une_variable_physiquement_absurde():
    """Une variable de trafic dont le coefficient serait NÉGATIF contredit le
    mécanisme : elle doit être écartée malgré son pouvoir explicatif.

    C'est ce qui distingue un modèle explicatif d'un ajustement de courbe.
    """
    rng = np.random.default_rng(1)
    n = 40
    route = rng.uniform(0, 100, n)
    X = pd.DataFrame({"route_lambda300m": route})
    y = 60.0 - 0.5 * route + rng.normal(0, 1, n)  # relation inversée, non physique

    contraint = lur.ajuster(X, y, respecter_signes=True)
    libre = lur.ajuster(X, y, respecter_signes=False)

    assert contraint.variables == [], "le signe négatif doit disqualifier la variable"
    assert libre.variables == ["route_lambda300m"]


def test_arret_sur_gain_insuffisant():
    """Sans gain réel, on n'ajoute pas de variable — un R² qui monte de 0,001 par
    variable ajoutée est du surajustement, pas de l'information."""
    rng = np.random.default_rng(2)
    X = pd.DataFrame({f"chene_lambda{i}m": rng.normal(0, 1, 30) for i in (100, 300, 1000)})
    y = rng.normal(0, 1, 30)
    modele = lur.ajuster(X, y, gain_min=0.05)
    assert len(modele.variables) <= 1


def test_variable_constante_ignoree():
    X, y = _jeu_synthetique()
    X["constante"] = 3.0
    modele = lur.ajuster(X, y)
    assert "constante" not in modele.variables


def test_validation_station_exclue_ne_teste_jamais_sur_l_apprentissage():
    """Chaque station est prédite par un modèle qui ne l'a jamais vue."""
    X, y = _jeu_synthetique(n=30)
    stations = pd.Series([f"S{i}" for i in range(30)])
    resultats = lur.valider_station_exclue(X, y, stations)

    assert len(resultats) == 30
    assert set(resultats["station_id"]) == set(stations)
    m = lur.metriques(resultats["observe"], resultats["predit"])
    assert m["r2"] > 0.8, "un signal net doit rester détectable hors échantillon"


def test_validation_honnete_sur_du_bruit_pur():
    """Sur des données sans structure, la validation par station exclue doit donner
    un R² proche de zéro ou NÉGATIF — pas un score flatteur.

    Une validation croisée ordinaire, elle, laisserait fuiter la station et
    produirait un score positif trompeur. C'est le test qui garantit l'honnêteté du
    protocole.
    """
    rng = np.random.default_rng(3)
    n = 25
    X = pd.DataFrame(
        {f"chene_lambda{lam}m": rng.normal(0, 1, n) for lam in (100, 300, 1000, 3000)}
    )
    y = rng.normal(50, 10, n)
    stations = pd.Series([f"S{i}" for i in range(n)])

    resultats = lur.valider_station_exclue(X, y, stations)
    assert lur.metriques(resultats["observe"], resultats["predit"])["r2"] < 0.3


def test_metriques_r2_negatif_quand_pire_que_la_moyenne():
    """Un R² négatif signale un modèle pire que « prédire la moyenne partout ».
    Le masquer donnerait une fausse impression de performance."""
    m = lur.metriques([10.0, 20.0, 30.0], [30.0, 20.0, 10.0])
    assert m["r2"] < 0
    assert m["biais"] == pytest.approx(0.0)


def test_modele_non_ajuste_refuse_de_predire():
    with pytest.raises(RuntimeError, match="non ajusté"):
        lur.ModeleLUR().predire(pd.DataFrame({"a": [1.0]}))
