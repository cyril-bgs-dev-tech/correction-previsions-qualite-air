"""Tests des conventions d'harmonisation.

Ces tests ne vérifient pas tant du code que des CONVENTIONS. Chacun correspond à
une erreur silencieuse classique du domaine : elle ne provoque aucun plantage et
ne se voit dans aucune métrique.
"""

import numpy as np
import pandas as pd
import pytest

from aq.harmonize import timegrid, units, wind


# --------------------------------------------------------------------------- #
# Unités
# --------------------------------------------------------------------------- #

def test_facteurs_conversion_conformes_valeurs_ue():
    """Valeurs de référence UE à 20 °C : NO2 ~1,91 · O3 ~2,00 · SO2 ~2,66."""
    assert units.facteur_ppb_vers_ug_m3("NO2") == pytest.approx(1.913, abs=0.005)
    assert units.facteur_ppb_vers_ug_m3("O3") == pytest.approx(1.996, abs=0.005)
    assert units.facteur_ppb_vers_ug_m3("SO2") == pytest.approx(2.663, abs=0.005)


def test_convention_epa_differe_de_la_convention_ue():
    """L'écart UE/EPA (~1,7 %) est un biais systématique, pas un détail."""
    ue = units.facteur_ppb_vers_ug_m3("NO2")
    epa = units.facteur_ppb_vers_ug_m3("NO2", temperature_K=units.T_REF_EPA_K)
    assert epa < ue
    assert (ue - epa) / ue == pytest.approx(0.0168, abs=0.002)


def test_conversion_particules_refusee():
    """Convertir des PM en ppb n'a pas de sens : échouer plutôt que de produire
    un nombre plausible mais faux."""
    with pytest.raises(ValueError, match="particulaire"):
        units.facteur_ppb_vers_ug_m3("PM25")


def test_aller_retour_ppb():
    valeurs = np.array([0.0, 10.0, 42.5])
    retour = units.ug_m3_vers_ppb(units.ppb_vers_ug_m3(valeurs, "NO2"), "NO2")
    np.testing.assert_allclose(retour, valeurs)


# --------------------------------------------------------------------------- #
# Vent
# --------------------------------------------------------------------------- #

def test_vent_de_nord_souffle_vers_le_sud():
    """Direction 0° = vent VENANT du nord, donc composante v négative.
    C'est le test qui empêche d'inverser tous les panaches."""
    u, v = wind.direction_vitesse_vers_uv(0.0, 10.0)
    assert u == pytest.approx(0.0, abs=1e-9)
    assert v == pytest.approx(-10.0)


def test_vent_d_ouest_souffle_vers_l_est():
    u, v = wind.direction_vitesse_vers_uv(270.0, 5.0)
    assert u == pytest.approx(5.0)
    assert v == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("direction", [0.0, 45.0, 90.0, 180.0, 275.0, 359.0])
def test_aller_retour_direction(direction):
    u, v = wind.direction_vitesse_vers_uv(direction, 7.0)
    retour, vitesse = wind.uv_vers_direction_vitesse(u, v)
    assert float(retour) == pytest.approx(direction, abs=1e-6)
    assert float(vitesse) == pytest.approx(7.0)


def test_moyenne_circulaire_ne_donne_pas_l_oppose():
    """Moyenne de 350° et 10° : la bonne réponse est 0°, pas 180°.
    La moyenne arithmétique naïve donne exactement la direction opposée."""
    assert wind.moyenne_directionnelle([350.0, 10.0]) == pytest.approx(0.0, abs=1e-6)
    assert np.mean([350.0, 10.0]) == pytest.approx(180.0)  # le piège, explicité


def test_vent_nul_ne_pointe_pas_au_nord():
    """Un vent nul n'a pas de direction : renvoyer 0° créerait un pic artificiel
    au nord dans toutes les roses des vents."""
    direction, vitesse = wind.uv_vers_direction_vitesse(0.0, 0.0)
    assert np.isnan(direction)
    assert float(vitesse) == 0.0


def test_ecart_angulaire_passe_par_zero():
    assert wind.ecart_angulaire(350.0, 10.0) == pytest.approx(20.0)
    assert wind.ecart_angulaire(10.0, 350.0) == pytest.approx(20.0)
    assert wind.ecart_angulaire(0.0, 180.0) == pytest.approx(180.0)


def test_poids_secteur_maximal_quand_source_au_vent():
    """Source plein nord et vent de nord : la source est au vent, poids maximal.
    Source au sud avec le même vent : sous le vent, contribution nulle."""
    assert wind.poids_secteur_au_vent(0.0, 0.0) == pytest.approx(1.0)
    assert wind.poids_secteur_au_vent(180.0, 0.0) == pytest.approx(0.0)
    assert wind.poids_secteur_au_vent(60.0, 0.0, demi_ouverture_deg=45.0) == 0.0


# --------------------------------------------------------------------------- #
# Grille temporelle
# --------------------------------------------------------------------------- #

def _df_horaire(debut, n, tz=None):
    idx = pd.date_range(debut, periods=n, freq="1h", tz=tz)
    return pd.DataFrame({"valeur": np.arange(n, dtype="float64")}, index=idx)


def test_convention_moyenne_avant_decale_d_une_heure():
    """Une valeur datée 10:00 couvrant (09:00, 10:00] devient datée 09:00."""
    df = _df_horaire("2020-01-01 10:00", 3, tz="UTC")
    out = timegrid.harmoniser(df, convention="moyenne_avant")
    assert out.index[0] == pd.Timestamp("2020-01-01 09:00", tz="UTC")


def test_convention_moyenne_apres_ne_decale_pas():
    df = _df_horaire("2020-01-01 10:00", 3, tz="UTC")
    out = timegrid.harmoniser(df, convention="moyenne_apres")
    assert out.index[0] == pd.Timestamp("2020-01-01 10:00", tz="UTC")


def test_convention_inconnue_rejetee():
    df = _df_horaire("2020-01-01", 3, tz="UTC")
    with pytest.raises(ValueError, match="inconnue"):
        timegrid.harmoniser(df, convention="a_peu_pres")


def test_heure_dupliquee_du_changement_d_heure_echoue_bruyamment():
    """Le 26/10/2025 à 02:30, l'heure locale française existe deux fois.
    Deviner laquelle déplacerait silencieusement une heure par an."""
    idx = pd.DatetimeIndex(["2025-10-26 02:30", "2025-10-26 02:30"])
    with pytest.raises(Exception):
        timegrid.vers_utc(idx, fuseau_source="Europe/Paris")


def test_heure_inexistante_du_changement_d_heure_echoue_bruyamment():
    """Le 30/03/2025 à 02:30, l'heure locale française n'existe pas."""
    idx = pd.DatetimeIndex(["2025-03-30 02:30"])
    with pytest.raises(Exception):
        timegrid.vers_utc(idx, fuseau_source="Europe/Paris")


def test_doublons_detectes():
    idx = pd.DatetimeIndex(["2020-01-01 00:00", "2020-01-01 00:00"], tz="UTC")
    df = pd.DataFrame({"valeur": [1.0, 2.0]}, index=idx)
    with pytest.raises(ValueError, match="dupliqués"):
        timegrid.harmoniser(df, convention="instantane")


def test_jour_local_differe_du_jour_utc_en_ete():
    """En été, 22:00 UTC est déjà le lendemain en heure locale. Agréger en jour
    UTC fausserait les moyennes journalières servant aux seuils réglementaires."""
    df = _df_horaire("2020-06-15 22:00", 3, tz="UTC")
    out = timegrid.ajouter_temps_local(df)
    assert str(out["jour_local"].iloc[0]) == "2020-06-16"
    assert out["heure_locale"].iloc[0] == 0


def test_couverture_temporelle_compte_les_trous():
    """24 heures UTC ne forment PAS une journée locale.

    En janvier (UTC+1), les 24 heures UTC du 1er janvier couvrent 01:00 locale
    jusqu'à minuit du lendemain : la journée locale du 1er n'a donc que 23 heures
    dans cet échantillon, et la 24e tombe déjà le 2. Six heures UTC manquantes en
    tête retirent six valeurs à cette journée de 23 heures : 17/23, pas 18/24.

    Attendre 18/24 est exactement l'erreur que le découpage en jour local existe
    pour éviter : appliquée à un contrôle de couverture réglementaire, elle
    validerait ou invaliderait à tort des moyennes journalières.
    """
    idx = pd.date_range("2020-01-01", periods=24, freq="1h", tz="UTC")
    serie = pd.Series(np.arange(24, dtype="float64"), index=idx)
    serie.iloc[:6] = np.nan

    couverture = timegrid.couverture_temporelle(serie)

    assert len(couverture) == 2, "les 24 h UTC débordent sur deux journées locales"
    assert couverture.iloc[0] == pytest.approx(17 / 23)
    assert couverture.iloc[1] == pytest.approx(1.0)


def test_couverture_temporelle_sur_une_journee_locale_alignee():
    """Contrôle de cohérence : sur une journée locale correctement alignée
    (23:00 UTC la veille en hiver), le compte redevient celui qu'on attend."""
    idx = pd.date_range("2019-12-31 23:00", periods=24, freq="1h", tz="UTC")
    serie = pd.Series(np.arange(24, dtype="float64"), index=idx)
    serie.iloc[:6] = np.nan

    couverture = timegrid.couverture_temporelle(serie)

    assert len(couverture) == 1
    assert couverture.iloc[0] == pytest.approx(18 / 24)


def test_grille_complete_rend_les_trous_explicites():
    """Réindexer sur une grille continue transforme des heures absentes en NaN :
    un modèle de série temporelle traite très différemment ces deux cas."""
    df = pd.concat(
        [_df_horaire("2020-01-01 00:00", 3, tz="UTC"),
         _df_horaire("2020-01-01 06:00", 2, tz="UTC")]
    )
    grille = timegrid.grille_complete("2020-01-01 00:00", "2020-01-01 07:00")
    reindexe = df.reindex(grille)
    assert len(reindexe) == 8
    assert reindexe["valeur"].isna().sum() == 3


def test_grille_complete_accepte_dates_naives_et_localisees():
    """Régression : passer une date déjà localisée levait une ValueError.

    Le cas se présente systématiquement en usage réel, où les bornes viennent
    d'un index déjà en UTC (`panneau["timestamp_utc"].min()`).
    """
    naive = timegrid.grille_complete("2020-01-01 00:00", "2020-01-01 03:00")
    localisee = timegrid.grille_complete(
        pd.Timestamp("2020-01-01 00:00", tz="UTC"),
        pd.Timestamp("2020-01-01 03:00", tz="UTC"),
    )
    assert len(naive) == len(localisee) == 4
    assert naive.equals(localisee)

    # Une borne en heure locale doit être convertie, pas réinterprétée.
    depuis_local = timegrid.grille_complete(
        pd.Timestamp("2020-01-01 01:00", tz="Europe/Paris"),
        pd.Timestamp("2020-01-01 04:00", tz="Europe/Paris"),
    )
    assert depuis_local[0] == pd.Timestamp("2020-01-01 00:00", tz="UTC")
