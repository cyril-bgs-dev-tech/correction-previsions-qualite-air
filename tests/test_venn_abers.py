import numpy as np

from aq.eval.venn_abers import calibrer_venn_abers, fusionner_cvap


def test_venn_abers_produit_des_probabilites_et_bornes_valides():
    scores = np.array([0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 0.95])
    y = np.array([0, 0, 0, 1, 0, 1, 1])
    point, bas, haut = calibrer_venn_abers(scores, y, np.linspace(0, 1, 31))

    assert np.all((0 <= bas) & (bas <= point))
    assert np.all((point <= haut) & (haut <= 1))
    assert np.all(np.diff(point) >= -1e-12)


def test_venn_abers_scores_constants_ajoute_le_label_hypothetique():
    # Deux positifs sur quatre calibrants. Si le score test est identique à tous les
    # autres, les deux fréquences isotones sont 2/5 et 3/5.
    point, bas, haut = calibrer_venn_abers(
        np.full(4, 0.3), np.array([0, 0, 1, 1]), np.array([0.3]))

    assert np.isclose(bas[0], 2 / 5)
    assert np.isclose(haut[0], 3 / 5)
    assert np.isclose(point[0], (3 / 5) / (1 - 2 / 5 + 3 / 5))


def test_fusion_cvap_suit_la_formule_geometrique():
    p0 = np.array([[0.1, 0.2], [0.3, 0.4]])
    p1 = np.array([[0.3, 0.4], [0.5, 0.6]])
    point, bas, haut = fusionner_cvap(p0, p1)

    gm0 = np.sqrt((1 - p0[:, 0]) * (1 - p0[:, 1]))
    gm1 = np.sqrt(p1[:, 0] * p1[:, 1])
    assert np.allclose(point, gm1 / (gm0 + gm1))
    assert np.allclose(bas, 1 - gm0)
    assert np.allclose(haut, gm1)

