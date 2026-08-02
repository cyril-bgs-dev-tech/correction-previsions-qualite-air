"""Tests de la surveillance de dérive du modèle amont.

Un détecteur de rupture se juge sur deux propriétés opposées, et les deux doivent être
tenues **ensemble** : il doit se taire quand rien ne se passe, et parler quand quelque
chose se passe. Un détecteur qui ne fait que l'un des deux est trivial à écrire.
"""

import numpy as np
import pandas as pd
import pytest

from aq.eval import derive


def _serie_journaliere(n_jours: int, biais, debut="2023-08-01", graine=0,
                       n_par_jour=200):
    """Paires (prévu, observé) dont le biais journalier est imposé."""
    rng = np.random.default_rng(graine)
    dates = pd.date_range(debut, periods=n_jours, freq="D", tz="UTC")
    valeurs = np.asarray(biais, dtype="float64")
    if valeurs.ndim == 0:
        valeurs = np.full(n_jours, float(valeurs))

    lignes = []
    for date, b in zip(dates, valeurs):
        observe = rng.normal(60.0, 15.0, n_par_jour)
        lignes.append(pd.DataFrame({
            "timestamp_utc": date + pd.to_timedelta(np.arange(n_par_jour) % 24, "h"),
            "valeur": observe,
            "cams": observe + b + rng.normal(0.0, 2.0, n_par_jour),
        }))
    return pd.concat(lignes, ignore_index=True)


# --------------------------------------------------------------------------- #
# Saisonnalité
# --------------------------------------------------------------------------- #

def test_saisonnalite_retrouve_un_cycle_annuel():
    jours = np.arange(1, 366)
    verite = 5.0 + 3.0 * np.sin(2 * np.pi * jours / derive.JOURS_AN)
    coefficients = derive.ajuster_saisonnalite(jours, verite)
    predit = derive.predire_saisonnalite(coefficients, jours)
    assert np.max(np.abs(predit - verite)) < 1e-6


def test_echelon_survit_a_la_deseasonnalisation():
    """C'est l'usage réel : la saisonnalité s'ajuste sur la **référence seule**, puis
    sert à juger la suite. Un décalage postérieur doit se retrouver intact dans le
    résidu — sinon la rupture serait expliquée par le cycle et jamais signalée."""
    jours_reference = np.arange(1, 366)
    cycle = 5.0 + 3.0 * np.sin(2 * np.pi * jours_reference / derive.JOURS_AN)
    coefficients = derive.ajuster_saisonnalite(jours_reference, cycle)

    jours_suivi = np.arange(1, 121)
    observe = (5.0 + 3.0 * np.sin(2 * np.pi * jours_suivi / derive.JOURS_AN)) + 6.0
    residu = observe - derive.predire_saisonnalite(coefficients, jours_suivi)
    assert np.allclose(residu, 6.0, atol=1e-6)


# --------------------------------------------------------------------------- #
# CUSUM
# --------------------------------------------------------------------------- #

def test_cusum_reste_muet_sur_du_bruit():
    z = np.random.default_rng(0).normal(0, 1, 2000)
    assert len(derive.cusum(z, k=0.5, h=12.0).alarmes) == 0


def test_cusum_detecte_un_decalage_permanent():
    z = np.concatenate([np.zeros(100), np.full(100, 1.0)])
    trace = derive.cusum(z, k=0.5, h=5.0)
    assert len(trace.alarmes) >= 1
    assert trace.alarmes[0] >= 100, "aucune alarme avant le décalage"
    assert trace.sens[0] == 1


def test_cusum_detecte_les_deux_sens():
    z = np.concatenate([np.zeros(50), np.full(100, -1.0)])
    trace = derive.cusum(z, k=0.5, h=5.0)
    assert trace.sens[0] == -1


def test_cusum_se_remet_a_zero_apres_alarme():
    """Sans remise à zéro, la statistique resterait au-dessus du seuil et chaque jour
    suivant compterait comme une alarme — l'indicateur deviendrait illisible."""
    z = np.full(300, 1.0)
    trace = derive.cusum(z, k=0.5, h=5.0)
    ecarts = np.diff(trace.alarmes)
    assert (ecarts > 1).all(), "les alarmes doivent être espacées, pas continues"


def test_cusum_ignore_les_valeurs_manquantes():
    z = np.array([0.0, np.nan, 0.0, np.nan, 0.0])
    trace = derive.cusum(z, k=0.5, h=5.0)
    assert np.isfinite(trace.haut).all()


def test_seuil_calibre_annule_les_fausses_alertes():
    z = np.random.default_rng(3).normal(0, 1, 400)
    seuil = derive.calibrer_seuil(z, fausses_alertes_tolerees=0)
    assert len(derive.cusum(z, h=seuil).alarmes) == 0


def test_seuil_calibre_est_le_plus_petit_possible():
    """Un seuil inutilement haut retarderait la détection sans rien garantir de plus."""
    z = np.random.default_rng(4).normal(0, 1, 400)
    seuil = derive.calibrer_seuil(z, fausses_alertes_tolerees=0)
    assert len(derive.cusum(z, h=seuil - 0.5).alarmes) >= 1


# --------------------------------------------------------------------------- #
# Concordance spatiale
# --------------------------------------------------------------------------- #

def test_concordance_elevee_quand_tout_le_reseau_bouge():
    assert derive.part_stations_concordantes(pd.Series([2.0, 3.0, 1.5, 2.5])) == 1.0


def test_concordance_moyenne_quand_le_signal_est_regional():
    part = derive.part_stations_concordantes(pd.Series([5.0, 4.0, -1.0, -2.0]))
    assert 0.4 <= part <= 0.6


# --------------------------------------------------------------------------- #
# Surveillance de bout en bout
# --------------------------------------------------------------------------- #

DEBUT = "2023-08-01"
DEBUT_SUIVI = "2024-08-01"          # un an de référence, comme sur les données réelles
JOUR_RUPTURE = 470                  # ≈ 13 novembre 2024


def _avec_rupture(n=560, rupture=JOUR_RUPTURE, avant=5.0, apres=8.0, graine=0):
    biais = np.concatenate([np.full(rupture, avant), np.full(n - rupture, apres)])
    return _serie_journaliere(n, biais=biais, debut=DEBUT, graine=graine)


def _date(jour: int) -> pd.Timestamp:
    return pd.Timestamp(DEBUT, tz="UTC") + pd.Timedelta(days=jour)


def test_surveillance_muette_sans_rupture():
    paires = _serie_journaliere(560, biais=5.0, debut=DEBUT)
    resultat = derive.surveiller(paires, debut_suivi=DEBUT_SUIVI)
    assert resultat.alarmes.empty


def test_surveillance_detecte_une_rupture_et_la_date():
    resultat = derive.surveiller(_avec_rupture(), debut_suivi=DEBUT_SUIVI)

    assert not resultat.alarmes.empty
    delai = derive.delai_de_detection(resultat, _date(JOUR_RUPTURE))
    assert delai is not None and delai <= 30, f"détection en {delai} jours"


def test_surveillance_ne_detecte_pas_avant_la_rupture():
    resultat = derive.surveiller(_avec_rupture(), debut_suivi=DEBUT_SUIVI)
    assert (resultat.alarmes["date"] >= _date(JOUR_RUPTURE)).all()


def test_une_derive_permanente_ne_donne_quun_episode():
    """Sans regroupement, une dérive qui dure déclencherait tous les jours."""
    resultat = derive.surveiller(_avec_rupture(apres=20.0), debut_suivi=DEBUT_SUIVI)
    assert len(resultat.alarmes) == 1


def test_surveillance_refuse_une_reference_trop_courte():
    paires = _serie_journaliere(90, biais=5.0)
    with pytest.raises(ValueError, match="référence trop courte"):
        derive.surveiller(paires, debut_suivi="2023-09-01")


def test_surveillance_refuse_une_reference_sans_cycle_complet():
    """Le défaut trouvé par ce test : une référence de huit mois force l'ajustement
    harmonique à extrapoler sur les jours de l'année qu'il n'a jamais vus, et
    l'indicateur signale ce trou plutôt qu'une dérive."""
    paires = _serie_journaliere(500, biais=5.0, debut=DEBUT)
    with pytest.raises(ValueError, match="cycle annuel"):
        derive.surveiller(paires, debut_suivi="2024-04-01")


def test_la_rupture_reste_dans_le_residu():
    """La saisonnalité n'est ajustée que sur la référence : si la rupture entrait dans
    l'ajustement, elle serait expliquée par le cycle et jamais signalée."""
    resultat = derive.surveiller(_avec_rupture(), debut_suivi=DEBUT_SUIVI)
    apres = resultat.journalier[resultat.journalier["date"] >= _date(JOUR_RUPTURE)]
    assert apres["ecart"].mean() > 2.0
