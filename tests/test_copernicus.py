"""Tests de construction des requêtes Copernicus.

Aucun compte n'est nécessaire : ces tests valident la FORME des requêtes, vérifiée
contre les formulaires JSON publics du catalogue. C'est utile précisément parce
qu'une requête mal formée n'échoue pas toujours — elle peut renvoyer une zone vide
ou un domaine décalé, sans erreur.
"""

from datetime import date

import pytest

from aq.ingest import copernicus as cop


def test_emprise_dans_l_ordre_nord_ouest_sud_est():
    """L'API attend [N, O, S, E], pas l'ordre usuel d'une bbox.

    Intervertir renverrait une zone vide ou l'hémisphère opposé — silencieusement.
    Ce test fige l'ordre : Nord > Sud, et Ouest < Est.
    """
    nord, ouest, sud, est = cop.EMPRISE_FRANCE
    assert nord > sud, "le Nord doit précéder le Sud dans la liste"
    assert ouest < est, "l'Ouest doit précéder l'Est"
    assert (nord, sud) == (52, 41)
    assert (ouest, est) == (-5, 10)


def test_requete_era5_couvre_les_24_heures():
    r = cop.requete_era5(2020, 1)
    assert len(r["time"]) == 24
    assert r["time"][0] == "00:00"
    assert r["time"][-1] == "23:00"


def test_requete_era5_demande_tous_les_jours_possibles():
    """Les jours inexistants sont ignorés par l'API : filtrer soi-même sur la
    longueur du mois n'apporterait rien et ajouterait un risque d'erreur sur les
    années bissextiles."""
    fevrier = cop.requete_era5(2021, 2)
    assert len(fevrier["day"]) == 31
    assert fevrier["day"][-1] == "31"


def test_requete_era5_contient_la_couche_limite():
    """La hauteur de couche limite est la variable déterminante des épisodes
    hivernaux : elle fixe le volume de dilution des émissions."""
    r = cop.requete_era5(2020, 6)
    assert "boundary_layer_height" in r["variable"]


def test_requete_era5_demande_les_composantes_du_vent():
    """u et v, pas la force seule : la direction est indispensable aux variables
    d'exposition anisotrope, et ne se moyenne pas comme un angle."""
    r = cop.requete_era5(2020, 6)
    assert "10m_u_component_of_wind" in r["variable"]
    assert "10m_v_component_of_wind" in r["variable"]


def test_champs_de_format_actuels():
    """Après la migration, les champs sont `data_format` et `download_format` —
    l'ancien `format` n'existe plus."""
    r = cop.requete_era5(2020, 1)
    assert r["data_format"] == "netcdf"
    assert r["download_format"] == "unarchived"
    assert "format" not in r


def test_mois_invalide_rejete():
    with pytest.raises(ValueError, match="hors bornes"):
        cop.requete_era5(2020, 13)


def test_requete_cams_sans_emprise_ni_horaire():
    """Ce jeu ne propose ni découpage géographique ni sélection horaire : passer
    ces champs serait une erreur silencieuse. Le recadrage est local."""
    r = cop.requete_cams(2020, 1)
    assert "area" not in r
    assert "time" not in r
    assert "day" not in r
    assert r["level"] == ["0"]
    assert r["model"] == ["ensemble"]


def test_type_de_reanalyse_valide():
    assert cop.requete_cams(2020, 1, type_reanalyse="interim_reanalysis")
    with pytest.raises(ValueError, match="Type de réanalyse"):
        cop.requete_cams(2020, 1, type_reanalyse="brouillon")


def test_iteration_mensuelle_franchit_les_annees():
    mois = list(cop.mois_entre(date(2019, 11, 1), date(2020, 2, 28)))
    assert mois == [(2019, 11), (2019, 12), (2020, 1), (2020, 2)]


def test_iteration_sur_un_seul_mois():
    assert list(cop.mois_entre(date(2020, 5, 3), date(2020, 5, 27))) == [(2020, 5)]


def test_plan_era5_groupe_quatre_mois_par_requete():
    """2013-2024 : 144 mois × 2 flux = 288 mois-flux, mais **72 requêtes**.

    Un mois seul n'utilise que 22 % du plafond du service (26 784 champs sur 121 000) ;
    quatre montent à 86 %. Le coût étant *par requête* — l'attente en file compte pour
    84 % du temps, mesuré —, le découpage mensuel paie quatre fois le prix pour la même
    charge. Cette erreur a coûté treize heures avant d'être vue.
    """
    plan = cop.plan_telechargement(date(2013, 1, 1), date(2024, 12, 31))
    assert len(plan) == 72, "144 mois × 2 flux ÷ 4 mois par requête"
    assert plan[0][0] == "era5_instantane_201301_04.nc"
    assert len({nom for nom, _ in plan}) == 72, "noms de fichiers uniques"
    # Aucun mois perdu ni dupliqué : chaque flux doit couvrir les 144 mois.
    for flux in cop.FLUX_ERA5:
        couverts = [(r["year"][0], m) for nom, r in plan
                    if nom.startswith(f"era5_{flux}_") for m in r["month"]]
        assert len(couverts) == 144, f"{flux} : {len(couverts)} mois au lieu de 144"
        assert len(set(couverts)) == 144, f"{flux} : doublons"


def test_un_groupe_era5_ne_chevauche_jamais_deux_annees():
    """`year` et `month` sont des listes **croisées** : [2019, 2020] × [11, 12]
    demanderait aussi 2019-12 et 2020-11. Un groupe à cheval sur deux années livrerait
    donc des mois non demandés — silencieusement, puisque le service les servirait."""
    plan = cop.plan_telechargement(date(2019, 11, 1), date(2020, 2, 29))
    for nom, requete in plan:
        assert len(requete["year"]) == 1, f"{nom} porte plusieurs années"
    mois_par_flux = {}
    for nom, requete in plan:
        flux = nom.split("_")[1]
        mois_par_flux.setdefault(flux, []).extend(
            (requete["year"][0], m) for m in requete["month"])
    for flux, couverts in mois_par_flux.items():
        assert sorted(couverts) == [("2019", "11"), ("2019", "12"),
                                    ("2020", "01"), ("2020", "02")], flux


def test_le_plan_era5_reste_sous_le_plafond_mais_pres_de_lui():
    """Fige les deux bornes. Une requête à 22 % du plafond passe tous les tests de
    correction et coûte quatre fois trop cher en temps — c'est l'erreur des 13 heures."""
    plan = cop.plan_telechargement(date(2019, 1, 1), date(2020, 12, 31))
    for nom, requete in plan:
        n_mois = len(requete["month"])
        assert n_mois <= cop.MOIS_PAR_REQUETE_ERA5, f"{nom} : {n_mois} mois"
    # Sur une plage multiple de 4, aucune requête ne doit être sous-remplie.
    assert all(len(r["month"]) == cop.MOIS_PAR_REQUETE_ERA5 for _, r in plan)


def test_flux_era5_disjoints_et_exhaustifs():
    """La séparation doit partitionner : une variable oubliée ne serait jamais
    téléchargée, une variable en double doublerait le volume sans le dire."""
    instant = set(cop.VARIABLES_ERA5_INSTANTANEES)
    cumul = set(cop.VARIABLES_ERA5_CUMULEES)
    assert not instant & cumul, "aucune variable dans les deux flux"
    assert instant | cumul == set(cop.VARIABLES_ERA5)


def test_les_cumuls_sont_bien_precipitation_et_rayonnement():
    """`total_precipitation` et `surface_solar_radiation_downwards` sont des totaux sur
    l'heure écoulée, pas des valeurs instantanées. Les traiter comme les autres les
    décalerait d'une heure — silencieusement."""
    assert set(cop.VARIABLES_ERA5_CUMULEES) == {
        "total_precipitation", "surface_solar_radiation_downwards"
    }


def test_requete_era5_ne_melange_jamais_les_deux_flux():
    """Une requête mêlant instantanés et cumulés est livrée en ARCHIVE ZIP sous une
    extension `.nc`, malgré `download_format="unarchived"` (vérifié en réel)."""
    for flux, attendues in cop.FLUX_ERA5.items():
        assert cop.requete_era5(2024, 1, flux=flux)["variable"] == attendues


def test_flux_inconnu_rejete():
    with pytest.raises(ValueError, match="Flux inconnu"):
        cop.requete_era5(2024, 1, flux="moyenne")


def test_plan_cams_utilise_le_bon_constructeur():
    plan = cop.plan_telechargement(date(2020, 1, 1), date(2020, 3, 31), service="cams")
    assert len(plan) == 3
    assert all("area" not in requete for _, requete in plan)


def test_service_inconnu_rejete():
    with pytest.raises(ValueError, match="Service inconnu"):
        cop.plan_telechargement(date(2020, 1, 1), date(2020, 2, 1), service="meteo")


def test_les_deux_services_ont_des_urls_distinctes():
    """Un seul compte ECMWF, mais deux endpoints. Comme `~/.cdsapirc` ne porte
    qu'une URL, le client doit être instancié explicitement."""
    assert cop.URL_CDS != cop.URL_ADS
    assert "climate" in cop.URL_CDS
    assert "atmosphere" in cop.URL_ADS


def test_la_licence_requise_est_cc_by():
    """Vérifié par téléchargement réel le 2026-07-28. Accepter la
    `licence-to-use-copernicus-products` v12 de l'ancienne infrastructure ne débloque
    rien : le service renvoie le même 403, sans nommer la licence qui manque."""
    assert cop.LICENCE_REQUISE == ("cc-by", 1)


def test_prevision_cams_accepte_emprise_et_echeances():
    """Contrairement à la réanalyse, ce jeu accepte `area` et `leadtime_hour` —
    vérifié par téléchargement réel."""
    r = cop.requete_cams_prevision(2024, 1)
    assert r["area"] == cop.EMPRISE_FRANCE
    assert r["type"] == ["forecast"]
    assert r["leadtime_hour"][0] == "0"
    assert r["leadtime_hour"][-1] == "72", "J+3 est l'horizon réglementaire haut"


def test_la_plage_de_dates_finit_au_dernier_jour_reel_du_mois():
    """**Bug qui a coûté une demi-journée.** Le code fabriquait des plages finissant au
    « jour 31 » quel que soit le mois : `2024-02-01/2024-02-31` désigne une date qui
    n'existe pas. Le service répond alors HTTP 500 sans dire laquelle des bornes est
    fautive.

    Le piège est vicieux : il ne se manifeste que sur les mois de moins de 31 jours.
    Janvier, juillet et décembre passaient — les seuls testés au départ. Février et avril
    échouaient en silence, et l'erreur ressemblait à une panne de service.
    """
    assert cop.requete_cams_prevision(2024, 2)["date"] == ["2024-02-01/2024-02-29"]
    assert cop.requete_cams_prevision(2023, 2)["date"] == ["2023-02-01/2023-02-28"]
    assert cop.requete_cams_prevision(2024, 4)["date"] == ["2024-04-01/2024-04-30"]
    assert cop.requete_cams_prevision(2024, 7)["date"] == ["2024-07-01/2024-07-31"]


def test_aucune_plage_du_plan_ne_designe_une_date_inexistante():
    """Le même contrôle sur le plan groupé, où deux mois cohabitent dans une requête."""
    from datetime import date as _date

    plan = cop.plan_telechargement(
        _date(2024, 1, 1), _date(2024, 12, 31), service="cams_prevision"
    )
    for nom, requete in plan:
        for plage in requete["date"]:
            _, fin = plage.split("/")
            annee, mois, jour = (int(x) for x in fin.split("-"))
            # Lève ValueError si la date n'existe pas — c'est tout le test.
            _date(annee, mois, jour)


def test_espece_par_defaut_est_l_ozone_et_tient_sous_le_plafond():
    """Un défaut qui échoue toujours serait un piège. L'ozone est le choix qui a un
    sens métier : il pilote l'indice ATMO occitan dans 87,8 % des cas."""
    r = cop.requete_cams_prevision(2024, 1)
    assert r["variable"] == ["ozone"]
    assert cop.cout_champs(1, len(r["leadtime_hour"])) <= cop.PLAFOND_CHAMPS_ADS


def test_echeance_hors_bornes_rejetee():
    with pytest.raises(ValueError, match="0 à 96"):
        cop.requete_cams_prevision(2024, 1, echeances_h=[0, 120])


def test_cout_calcule_comme_le_service_le_facture():
    """Vérifié contre `estimate_costs` de l'ADS : 31 jours × 73 échéances × 3 espèces
    = 6789 champs, pour un plafond de 5000."""
    assert cop.cout_champs(3, 73) == 6789
    assert cop.cout_champs(1, 73) == 2263
    assert cop.PLAFOND_CHAMPS_ADS == 5000


def test_requete_cams_trop_grosse_refusee_avant_envoi():
    """Le service répondrait HTTP 403 avec un message tronqué qui ne dit pas de combien
    on dépasse. Autant le savoir sans faire l'aller-retour."""
    with pytest.raises(ValueError, match="plafond"):
        cop.requete_cams_prevision(2024, 12, variables=cop.VARIABLES_CAMS)


def test_plan_cams_prevision_groupe_deux_mois_par_espece():
    """Une espèce par requête, mais **deux mois** — et c'est la granularité qui compte.

    Le coût du service est *par requête*, l'attente en file étant largement dominante.
    Un seul mois n'utilise que 44 % du plafond : on paie deux fois le prix pour la même
    charge. Deux mois montent à 89 % et divisent les requêtes par deux.
    """
    plan = cop.plan_telechargement(
        date(2024, 1, 1), date(2024, 2, 29), service="cams_prevision"
    )
    assert len(plan) == 3, "2 mois groupés × 3 espèces"
    assert plan[0][0] == "cams_prevision_no2_202401_202402.nc"
    assert all(len(requete["variable"]) == 1 for _, requete in plan)
    assert all(len(requete["date"]) == 2 for _, requete in plan)


def test_le_plan_cams_reste_sous_le_plafond_mais_pres_de_lui():
    """Fige les deux bornes : ne jamais dépasser, ne jamais gaspiller.

    Une requête à 20 % du plafond passe tous les tests de correction et coûte quatre
    fois trop cher en temps — c'est l'erreur qui a coûté treize heures sur ERA5.
    """
    plan = cop.plan_telechargement(
        date(2024, 1, 1), date(2024, 4, 30), service="cams_prevision"
    )
    for nom, requete in plan:
        cout = cop.cout_champs(len(requete["variable"]),
                               len(requete["leadtime_hour"]),
                               n_jours=31 * len(requete["date"]))
        part = cout / cop.PLAFOND_CHAMPS_ADS
        assert part <= 1.0, f"{nom} dépasse le plafond ({part:.0%})"
        assert part >= 0.7, f"{nom} n'utilise que {part:.0%} du plafond — regrouper"


def test_plan_cams_sur_un_nombre_impair_de_mois():
    """Trois mois donnent deux groupes : une paire et un isolé. Le dernier ne doit pas
    être perdu."""
    plan = cop.plan_telechargement(
        date(2024, 1, 1), date(2024, 3, 31), service="cams_prevision"
    )
    assert len(plan) == 6, "(2 groupes) × 3 espèces"
    noms = {nom for nom, _ in plan}
    assert "cams_prevision_o3_202401_202402.nc" in noms
    assert "cams_prevision_o3_202403.nc" in noms


def test_prevision_et_reanalyse_sont_deux_jeux_distincts():
    """La réanalyse assimile les observations EEA, donc la cible du projet : elle ne
    peut pas servir de référence à battre. La prévision, si."""
    assert cop.JEU_CAMS_PREVISION != cop.JEU_CAMS_REANALYSE
    assert "forecast" in cop.JEU_CAMS_PREVISION


def test_longitudes_cams_ramenees_en_180():
    """Le piège central de CAMS Europe : sur une emprise à cheval sur Greenwich, l'axe
    des longitudes est livré en [0, 360] ET non monotone (358,05 … 359,95 puis
    0,05 … 4,95). Toute sélection au plus proche voisin y est fausse en silence."""
    xr = pytest.importorskip("xarray")
    import numpy as np

    lon_cams = np.concatenate([np.arange(358.05, 360.0, 0.1), np.arange(0.05, 5.0, 0.1)])
    lat_cams = np.arange(44.95, 42.0, -0.1)
    brut = xr.Dataset(
        {"o3_conc": (("latitude", "longitude"),
                     np.zeros((len(lat_cams), len(lon_cams))))},
        coords={"latitude": lat_cams, "longitude": lon_cams},
    )
    assert not np.all(np.diff(brut.longitude.values) > 0), "l'entrée doit être piégeuse"

    propre = cop.normaliser_longitudes(brut)
    lon = propre.longitude.values
    assert np.all(np.diff(lon) > 0), "longitudes croissantes après normalisation"
    assert lon.min() < 0, "l'ouest de Greenwich doit devenir négatif"
    assert -2.0 < lon.min() < -1.9
    assert np.all(np.diff(propre.latitude.values) > 0), "latitudes croissantes aussi"


def test_normalisation_preserve_les_longitudes_era5():
    """ERA5 est déjà en [-180, 180] : la normalisation doit être neutre, sinon elle
    déplacerait les champs météo d'un demi-tour de globe."""
    xr = pytest.importorskip("xarray")
    import numpy as np

    lon = np.arange(-5.0, 10.01, 0.25)
    lat = np.arange(52.0, 40.9, -0.25)
    brut = xr.Dataset(
        {"t2m": (("latitude", "longitude"), np.zeros((len(lat), len(lon))))},
        coords={"latitude": lat, "longitude": lon},
    )
    propre = cop.normaliser_longitudes(brut)
    np.testing.assert_allclose(propre.longitude.values, lon)
    np.testing.assert_allclose(propre.latitude.values, lat[::-1])
