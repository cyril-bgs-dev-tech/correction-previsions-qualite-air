"""Le contrôle de prétraitement voit-il la dérive dans les DEUX sens ?

Le défaut que ces tests figent
-------------------------------
Un plancher — « au moins N lignes » — ne voit rien d'un corpus qui GONFLE, et le défaut
d'appariement du 22/08 gonflait : 5 à 6 % de doublons entraient dans le modèle. Le seuil
doit donc porter sur l'écart relatif en valeur absolue (§ 2 quinquies).

Et un garde-fou non testé est une croyance : il se testera tout seul le jour où il aura
échoué (§ 1 quater).
"""

import math

import pytest

from controle_pretraitement import comparer

REF = {"NO2.n_lignes": 1_000_000.0, "O3.valeur_mediane": 58.9, "PM10.n_doublons_cle": 0.0,
       "PM25.valeur_min": -15.0, "O3.heures_par_jour_mediane": float("nan")}


def test_une_mesure_identique_ne_derive_pas():
    derives, nouveaux, disparus = comparer(REF, dict(REF), 0.005)
    assert derives == [] and nouveaux == [] and disparus == []


def test_un_corpus_qui_GONFLE_derive_autant_qu_un_corpus_qui_chute():
    """Le cas du doublon d'appariement : un plancher l'aurait laissé passer."""
    gonfle = comparer(REF, {**REF, "NO2.n_lignes": 1_060_000.0}, 0.005)[0]
    chute = comparer(REF, {**REF, "NO2.n_lignes": 940_000.0}, 0.005)[0]
    assert len(gonfle) == 1 and len(chute) == 1
    assert gonfle[0][0] == chute[0][0] == "NO2.n_lignes"
    assert gonfle[0][3] == pytest.approx(0.06) and chute[0][3] == pytest.approx(0.06)


def test_un_doublon_qui_apparait_derive_malgre_une_reference_a_zero():
    """La référence vaut 0 : l'écart relatif diviserait par zéro sans le plancher."""
    derives = comparer(REF, {**REF, "PM10.n_doublons_cle": 1.0}, 0.005)[0]
    assert [d[0] for d in derives] == ["PM10.n_doublons_cle"]
    assert math.isfinite(derives[0][3])


def test_une_sentinelle_qui_revient_est_vue():
    """−999 à la place du minimum : exactement ce que `valeur_min` existe pour attraper."""
    derives = comparer(REF, {**REF, "PM25.valeur_min": -999.0}, 0.005)[0]
    assert [d[0] for d in derives] == ["PM25.valeur_min"]


def test_deux_nan_sont_identiques_mais_un_seul_derive():
    assert comparer(REF, dict(REF), 0.005)[0] == []
    derives = comparer(REF, {**REF, "O3.heures_par_jour_mediane": 24.0}, 0.005)[0]
    assert [d[0] for d in derives] == ["O3.heures_par_jour_mediane"]


def test_un_invariant_disparu_se_distingue_d_un_invariant_nouveau():
    sans = {k: v for k, v in REF.items() if k != "NO2.n_lignes"}
    derives, nouveaux, disparus = comparer(REF, sans, 0.005)
    assert disparus == ["NO2.n_lignes"] and nouveaux == [] and derives == []
    derives, nouveaux, disparus = comparer(sans, REF, 0.005)
    assert nouveaux == ["NO2.n_lignes"] and disparus == []
