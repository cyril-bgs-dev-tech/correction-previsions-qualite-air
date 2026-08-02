"""Tests des métriques de détection d'épisode.

Le rappel est la grandeur déterminante d'un usage d'alerte : ne pas annoncer un épisode
qui survient expose la population, alors qu'une fausse alerte coûte de la crédibilité.
Ces tests figent cette asymétrie, qu'aucune métrique moyenne ne porte.
"""

import numpy as np
import pandas as pd
import pytest

from aq.eval import alerte


def test_rappel_est_la_part_des_episodes_annonces():
    observe = [True, True, True, True, False, False]
    predit = [True, True, False, False, False, False]
    m = alerte.metriques_alerte(observe, predit)
    assert m["rappel"] == pytest.approx(0.5)
    assert m["faux_negatifs"] == 2
    assert m["n_evenements"] == 4


def test_precision_est_la_part_des_alertes_justifiees():
    observe = [True, True, False, False]
    predit = [True, True, True, False]
    m = alerte.metriques_alerte(observe, predit)
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["faux_positifs"] == 1


def test_f2_privilegie_le_rappel_sur_la_precision():
    """**Le cœur du module.** À précision et rappel échangés, le F₂ doit préférer la
    variante qui rappelle davantage — parce que manquer un épisode coûte plus qu'une
    fausse alerte. Un F1 les jugerait équivalentes, et c'est ce qu'on refuse."""
    observe = [True] * 10 + [False] * 90

    # Variante prudente : annonce large, rappelle tout, se trompe souvent.
    prudente = [True] * 10 + [True] * 20 + [False] * 70
    # Variante avare : n'annonce que du sûr, mais manque la moitié des épisodes.
    avare = [True] * 5 + [False] * 5 + [False] * 90

    m_prudente = alerte.metriques_alerte(observe, prudente)
    m_avare = alerte.metriques_alerte(observe, avare)

    assert m_prudente["rappel"] > m_avare["rappel"]
    assert m_prudente["precision"] < m_avare["precision"]
    assert m_prudente["f2"] > m_avare["f2"], (
        "le F₂ doit préférer la variante qui manque moins d'épisodes"
    )


def test_modele_qui_n_annonce_jamais_rien():
    """Cas dégénéré à ne pas laisser passer : un modèle muet a une précision
    indéfinie, pas parfaite. La coder à 1 le ferait paraître excellent."""
    m = alerte.metriques_alerte([True, True, False], [False, False, False])
    assert m["rappel"] == 0.0
    assert np.isnan(m["precision"])
    assert m["faux_negatifs"] == 2


def test_taux_de_fausse_alerte_rapporte_aux_non_evenements():
    """Rapporter les fausses alertes au nombre d'alertes émises dépend de la rareté de
    l'épisode ; les rapporter aux non-événements dit combien de fois on a dérangé pour
    rien, indépendamment de cette rareté."""
    observe = [True] + [False] * 99
    predit = [True] + [True] * 9 + [False] * 90
    m = alerte.metriques_alerte(observe, predit)
    assert m["taux_fausse_alerte"] == pytest.approx(9 / 99)


def test_seuils_cumules_et_non_classes_isolees():
    """Ce qui déclenche une communication, c'est « dégradé **ou pire** », jamais
    « exactement dégradé »."""
    observe = pd.Series([1, 2, 3, 4, 5])
    predit = pd.Series([1, 2, 2, 4, 4])
    table = alerte.par_seuil_de_classe(observe, predit, classes=(3, 4)).set_index(
        "seuil_classe"
    )
    # Classe ≥ 3 : trois événements (3, 4, 5), deux annoncés (4 et 4).
    assert table.loc[3, "n_evenements"] == 3
    assert table.loc[3, "rappel"] == pytest.approx(2 / 3)
    # Classe ≥ 4 : deux événements (4, 5), les deux annoncés.
    assert table.loc[4, "n_evenements"] == 2
    assert table.loc[4, "rappel"] == pytest.approx(1.0)


def test_comparaison_de_modeles_aligne_les_seuils():
    observe = pd.Series([1, 3, 4, 2, 5, 1])
    table = alerte.comparer_modeles(
        observe,
        {"a": pd.Series([1, 3, 4, 2, 5, 1]), "b": pd.Series([1, 1, 1, 1, 1, 1])},
        classes=(3, 4),
    )
    parfait = table[table["modele"] == "a"]
    muet = table[table["modele"] == "b"]
    assert (parfait["rappel"] == 1.0).all()
    assert (muet["rappel"] == 0.0).all()
    # Les deux modèles doivent être jugés sur exactement les mêmes événements.
    assert list(parfait["n_evenements"]) == list(muet["n_evenements"])


def test_une_meilleure_precision_ne_compense_pas_un_rappel_effondre():
    """Régression métier à interdire : un modèle qui réduit les fausses alertes en
    manquant davantage d'épisodes est une **régression**, quelles que soient ses
    métriques moyennes."""
    observe = [True] * 20 + [False] * 80
    reference = [True] * 15 + [False] * 5 + [True] * 15 + [False] * 65
    candidat = [True] * 5 + [False] * 15 + [False] * 80  # zéro fausse alerte

    m_ref = alerte.metriques_alerte(observe, reference)
    m_cand = alerte.metriques_alerte(observe, candidat)

    assert m_cand["precision"] > m_ref["precision"], "le candidat semble meilleur"
    assert m_cand["f2"] < m_ref["f2"], "mais le F₂ doit le rejeter"
