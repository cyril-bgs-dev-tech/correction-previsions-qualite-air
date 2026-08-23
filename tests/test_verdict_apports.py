"""Un groupe significatif dans l'AUTRE sens réfute — le test qui le fige.

Le défaut, mesuré le 23/08/2026
--------------------------------
La conjonction partielle de Benjamini-Heller teste « l'effet est présent dans au moins
`r` groupes ». Alimentée par des `p` **bilatéraux**, elle ne distingue pas le sens : un
groupe fortement négatif y compte comme une confirmation.

Mesuré sur les 28 ratios d'échelle, axe double aveugle :

    NO2   +1,212 %  p=0,0002      PM10  −0,657 %  p=0,0002

Deux groupes significatifs, `p_PC = 0,0006`, verdict rendu « ✅ TIENT » — alors que la
configuration **aide le NO₂ et nuit au PM10 avec la même force**. La règle du dépôt
(§ 0-E) disait l'inverse depuis toujours ; elle avait été perdue en réécrivant le verdict.

Le correctif tient en un mot : les `p` du bootstrap deviennent **unilatéraux**. `p_plus`
alimente la conjonction, `p_moins` réfute, et la réfutation est testée AVANT elle.

Ces tests figent les quatre propriétés dans l'ordre où elles ont manqué : le sens réfute,
la réfutation prime sur la conjonction, les `p` unilatéraux séparent bien les deux sens,
et les blocs ne se chevauchent pas.
"""

import numpy as np
import pytest

from verdict_apports import (blocs_de, bootstrap_blocs, conjonction_partielle,
                             rendre_verdict)

# (moy, ic_bas, ic_haut, p_plus, p_moins, blocs_positifs, n_blocs)
PORTE = (+1.2, +0.7, +1.7, 0.0001, 1.0000, 11, 12)
NUIT = (-0.7, -0.9, -0.4, 1.0000, 0.0001, 1, 12)
MUET = (-0.2, -0.6, +0.2, 0.8000, 0.2000, 5, 12)
SIGNES_STABLES = {L: {"NO2": 1, "O3": -1, "PM10": -1, "PM25": -1} for L in (2, 3, 4)}


def test_un_groupe_significativement_negatif_refute():
    """Le cas réel des 28 ratios : deux `p` minuscules, de signes opposés."""
    detail = {"NO2": PORTE, "O3": MUET, "PM10": NUIT, "PM25": MUET}
    verdit, _ = rendre_verdict(detail, {2: 0.0006, 3: 0.0006, 4: 0.0006}, SIGNES_STABLES)
    assert "RÉFUTÉ" in verdit, "un groupe en sens inverse ne se tait pas"
    assert "PM10" in verdit, "le verdict doit NOMMER le groupe qui réfute"
    assert "TIENT" not in verdit


def test_la_refutation_prime_sur_une_conjonction_parfaite():
    """Même avec `p_PC` au plancher, un groupe qui nuit interdit de promouvoir."""
    detail = {"NO2": PORTE, "O3": PORTE, "PM10": NUIT, "PM25": PORTE}
    verdit, _ = rendre_verdict(detail, {2: 1e-9, 3: 1e-9, 4: 1e-9}, SIGNES_STABLES)
    assert "RÉFUTÉ" in verdit


def test_un_echec_par_PUISSANCE_se_distingue_d_une_absence_d_effet():
    """Le cas réel du 23/08 : spéciation p_PC=0,065 avec quatre groupes positifs contre
    feux p_PC=1,0 avec trois négatifs. Les deux disaient « NON CONFIRMÉ »."""
    faible = (+1.2, -0.3, +2.7, 0.09, 0.91, 6, 9)
    puissance = {"NO2": PORTE, "O3": faible, "PM10": faible, "PM25": faible}
    v, _ = rendre_verdict(puissance, {2: 0.065, 3: 0.065, 4: 0.065},
                          {L: dict.fromkeys(puissance, 1) for L in (2, 3, 4)})
    assert "PUISSANCE" in v and "🟠" in v

    negatif = (-0.5, -1.1, +0.2, 0.80, 0.20, 3, 9)
    vide = {"NO2": negatif, "O3": negatif, "PM10": negatif, "PM25": MUET}
    v, _ = rendre_verdict(vide, {2: 1.0, 3: 1.0, 4: 1.0},
                          {L: dict.fromkeys(vide, -1) for L in (2, 3, 4)})
    assert "NON CONFIRMÉ" in v and "PUISSANCE" not in v


def test_tous_positifs_ne_suffit_pas_a_invoquer_la_puissance():
    """Le cas réel du 24/08 : la chimie rendait p_PC=0,86 avec les quatre estimations
    au-dessus de zéro, dont trois à +0,007, +0,117 et +0,197 pt. Le verdict annonçait
    « gagner des mois » pour un effet inexistant sur trois polluants."""
    porteur = (+0.73, +0.35, +1.13, 0.0063, 0.99, 8, 9)
    plat = (+0.12, -0.40, +0.71, 0.3515, 0.65, 4, 8)
    vide = {"O3": porteur, "NO2": plat, "PM10": plat, "PM25": plat}
    v, _ = rendre_verdict(vide, {2: 1.0, 3: 0.8646, 4: 0.79},
                          {L: dict.fromkeys(vide, 1) for L in (2, 3, 4)})
    assert "PUISSANCE" not in v, "un seul groupe qui penche n'est pas un manque de puissance"

    # Deux groupes qui penchent, eux, le sont — c'est la spéciation en dernière position.
    penche = (+1.67, -0.36, +3.16, 0.0216, 0.98, 7, 9)
    puissance = {"NO2": porteur, "PM25": penche, "O3": plat, "PM10": plat}
    v, _ = rendre_verdict(puissance, {2: 0.07, 3: 0.0648, 4: 0.08},
                          {L: dict.fromkeys(puissance, 1) for L in (2, 3, 4)})
    assert "PUISSANCE" in v


def test_quatre_groupes_positifs_tiennent():
    """Le témoin : sans groupe en sens inverse, la conjonction décide seule."""
    detail = {p: PORTE for p in ("NO2", "O3", "PM10", "PM25")}
    signes = {L: dict.fromkeys(detail, 1) for L in (2, 3, 4)}
    verdit, porteurs = rendre_verdict(detail, {2: 0.0003, 3: 0.0003, 4: 0.0003}, signes)
    assert "TIENT" in verdit and len(porteurs) == 2


def test_un_signe_qui_s_inverse_avec_le_decoupage_ne_conclut_pas():
    detail = {p: PORTE for p in ("NO2", "O3", "PM10", "PM25")}
    signes = {2: dict.fromkeys(detail, 1), 3: dict.fromkeys(detail, 1),
              4: dict.fromkeys(detail, 1)}
    signes[4]["NO2"] = -1
    verdit, _ = rendre_verdict(detail, {2: 0.0003, 3: 0.0003, 4: 0.0003}, signes)
    assert "SIGNE INSTABLE" in verdit


def test_les_p_unilateraux_separent_les_deux_sens():
    """Sur une série franchement positive, `p_plus` au plancher et `p_moins` à 1 — et
    l'inverse sur son opposée. C'est ce que le `p` bilatéral confondait."""
    positif = list(np.linspace(0.8, 1.6, 36))
    _, _, _, p_plus, p_moins = bootstrap_blocs(positif, 3, tirages=999, graine=1)
    assert p_plus < 0.01 < p_moins
    _, _, _, q_plus, q_moins = bootstrap_blocs([-x for x in positif], 3, tirages=999,
                                               graine=1)
    assert q_moins < 0.01 < q_plus


def test_le_p_unilateral_ne_descend_pas_sous_son_plancher():
    """Un `p` bootstrap ne peut pas valoir zéro : le plancher est 1/(B+1)."""
    _, _, _, p_plus, _ = bootstrap_blocs([1.0] * 36, 3, tirages=99, graine=1)
    assert p_plus == pytest.approx(1 / 100)


def test_les_blocs_ne_se_chevauchent_pas():
    """12 mois, blocs de 3 → 4 blocs disjoints, et le reliquat est jeté."""
    assert blocs_de(list(range(12)), 3) == [1.0, 4.0, 7.0, 10.0]
    assert len(blocs_de(list(range(11)), 3)) == 3


def test_la_conjonction_partielle_suit_benjamini_heller():
    """`p_PC = (n − r + 1) × p_(r)` — le DEUXIÈME plus petit, jamais le plus petit."""
    assert conjonction_partielle([0.001, 0.02, 0.30, 0.40]) == pytest.approx(3 * 0.02)
    assert conjonction_partielle([0.001, 0.90, 0.90, 0.90]) == pytest.approx(1.0)
    assert conjonction_partielle([0.001]) == 1.0
