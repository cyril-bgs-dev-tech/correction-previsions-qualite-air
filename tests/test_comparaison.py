"""Tests des métriques de comparaison modèle / observations."""

import numpy as np
import pandas as pd
import pytest

from aq.eval import comparaison as cmp


def test_modele_parfait():
    m = cmp.metriques([10.0, 20.0, 30.0], [10.0, 20.0, 30.0])
    assert m["rmse"] == 0.0
    assert m["biais"] == 0.0
    assert m["r2"] == 1.0


def test_r2_negatif_quand_pire_que_la_moyenne():
    """Un modèle physique n'est pas calibré sur ces observations : son R² PEUT être
    négatif, et cela veut dire quelque chose — pire que prédire la moyenne. Le tronquer
    à zéro masquerait le seul cas qui doit alerter."""
    m = cmp.metriques([10.0, 20.0, 30.0], [30.0, 20.0, 10.0])
    assert m["r2"] < 0


def test_biais_signe_dans_le_sens_modele_moins_observation():
    """Un biais positif doit signifier « le modèle surestime ». Le signe inverse
    ferait lire toutes les corrections de biais à l'envers."""
    m = cmp.metriques([10.0, 10.0], [15.0, 15.0])
    assert m["biais"] == pytest.approx(+5.0)


def test_paires_incompletes_ecartees_ensemble():
    """Écarter une observation sans sa prévision, ou l'inverse, décalerait les deux
    séries l'une par rapport à l'autre — et toutes les métriques avec."""
    m = cmp.metriques([10.0, np.nan, 30.0, 40.0], [10.0, 20.0, np.nan, 40.0])
    assert m["n"] == 2
    assert m["rmse"] == 0.0


def test_serie_vide_ne_plante_pas():
    m = cmp.metriques([], [])
    assert m["n"] == 0
    assert np.isnan(m["rmse"])


def test_mqi_nul_pour_un_modele_parfait():
    assert cmp.indice_qualite_modele([20.0, 40.0], [20.0, 40.0], "NO2") == 0.0


def test_mqi_croit_avec_l_erreur():
    faible = cmp.indice_qualite_modele([20.0, 40.0], [22.0, 42.0], "NO2")
    forte = cmp.indice_qualite_modele([20.0, 40.0], [60.0, 80.0], "NO2")
    assert 0 < faible < forte


def test_mqi_refuse_un_polluant_sans_parametres():
    """Inventer des paramètres d'incertitude produirait un seuil de conformité
    arbitraire, présenté comme réglementaire."""
    with pytest.raises(ValueError, match="paramètres d'incertitude"):
        cmp.indice_qualite_modele([20.0], [20.0], "SO2")


def test_ventilation_par_typologie():
    """La ventilation fond / trafic est la plus éclairante : une maille de 8 km ne
    résout pas le micro-environnement d'une station trafic."""
    joint = pd.DataFrame({
        "valeur": [10.0, 12.0, 40.0, 44.0],
        "prediction": [10.0, 12.0, 20.0, 22.0],
        "type_station": ["background", "background", "traffic", "traffic"],
    })
    table = cmp.comparer(joint, polluant="NO2", par=["type_station"]).set_index(
        "type_station"
    )
    assert table.loc["background", "rmse"] == pytest.approx(0.0)
    assert table.loc["traffic", "rmse"] > 15
    assert table.loc["traffic", "biais"] < 0, "le modèle sous-estime le trafic"


def jeu_correle(n_stations=25, n_heures=200, graine=0):
    """Stations dont les heures sont fortement corrélées entre elles.

    C'est la structure réelle des données horaires : le niveau d'une station dérive
    lentement, si bien que ses heures se ressemblent bien plus qu'elles ne ressemblent
    à celles d'une autre station.
    """
    rng = np.random.default_rng(graine)
    blocs = []
    for s in range(n_stations):
        niveau = rng.normal(40, 12)
        vrai = niveau + rng.normal(0, 2, n_heures)
        blocs.append(pd.DataFrame({
            "station_id": f"S{s:03d}",
            "observe": vrai,
            "a": vrai * 1.25 + rng.normal(0, 3, n_heures),
            "b": vrai + rng.normal(0, 3, n_heures),
        }))
    return pd.concat(blocs, ignore_index=True)


def test_bootstrap_par_station_bien_plus_large_que_par_ligne():
    """**Le piège que ce bootstrap existe pour éviter.** Tirer des lignes traite
    24 heures consécutives d'une même station comme 24 observations indépendantes, et
    rétrécit l'intervalle d'un facteur trompeur.

    Mesuré sur les données réelles du projet : l'intervalle par ligne fait ±0,15 point
    de gain, celui par station ±3,5 — un facteur 23. Publier le premier reviendrait à
    annoncer une précision qu'on n'a pas.
    """
    jeu = jeu_correle()
    par_ligne = cmp.intervalle_bootstrap(jeu["observe"], jeu["a"], jeu["b"],
                                         n_tirages=200)
    par_station = cmp.intervalle_bootstrap(jeu["observe"], jeu["a"], jeu["b"],
                                           groupes=jeu["station_id"], n_tirages=200)
    largeur = lambda r: r["borne_haute"] - r["borne_basse"]
    assert largeur(par_station) > 2 * largeur(par_ligne), (
        "le bootstrap par station doit être nettement plus large"
    )


def test_l_intervalle_encadre_le_gain_observe():
    jeu = jeu_correle()
    r = cmp.intervalle_bootstrap(jeu["observe"], jeu["a"], jeu["b"],
                                 groupes=jeu["station_id"], n_tirages=200)
    assert r["borne_basse"] <= r["gain_pct"] <= r["borne_haute"]
    assert r["n_unites"] == 25, "l'effectif utile est le nombre de stations"


def test_deux_modeles_equivalents_donnent_un_intervalle_traversant_zero():
    """Si les deux modèles se valent, l'intervalle doit contenir zéro — sans quoi on
    déclarerait une amélioration là où il n'y en a pas."""
    jeu = jeu_correle()
    r = cmp.intervalle_bootstrap(jeu["observe"], jeu["b"], jeu["b"].copy(),
                                 groupes=jeu["station_id"], n_tirages=200)
    assert r["borne_basse"] <= 0 <= r["borne_haute"]


def test_part_des_tirages_positifs_rapportee():
    """Un gain moyen positif dont seuls 60 % des tirages sont positifs n'est pas le même
    résultat qu'un gain positif dans 100 % des cas."""
    jeu = jeu_correle()
    r = cmp.intervalle_bootstrap(jeu["observe"], jeu["a"], jeu["b"],
                                 groupes=jeu["station_id"], n_tirages=200)
    assert 0.0 <= r["part_tirages_positifs"] <= 1.0
    assert r["part_tirages_positifs"] > 0.9, "le gain simulé est franc"


def test_colonne_de_conformite_presente_avec_un_polluant_connu():
    joint = pd.DataFrame({"valeur": [20.0, 30.0], "prediction": [20.5, 30.5]})
    table = cmp.comparer(joint, polluant="NO2")
    assert bool(table["conforme"].iloc[0]) is True
    assert table["mqi"].iloc[0] < 1
