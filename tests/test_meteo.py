"""Tests de l'échantillonnage des champs Copernicus aux stations.

Les grilles sont fabriquées à la main : le but n'est pas de vérifier que xarray sait
interpoler, mais que les **conventions** sont les bonnes. Chacune des erreurs visées
ici produit des valeurs plausibles, donc aucune alerte.
"""

import numpy as np
import pandas as pd
import pytest

from aq.features import meteo

xr = pytest.importorskip("xarray")


def grille(lon, lat, variables, heures=1):
    """Petit champ ERA5-like, latitudes décroissantes comme le service les livre."""
    temps = pd.date_range("2024-12-01", periods=heures, freq="h")
    donnees = {
        nom: (("valid_time", "latitude", "longitude"),
              np.broadcast_to(valeur, (heures, len(lat), len(lon))).astype("float64"))
        for nom, valeur in variables.items()
    }
    return xr.Dataset(
        donnees,
        coords={"valid_time": temps, "latitude": lat, "longitude": lon},
    )


def stations(**colonnes):
    return pd.DataFrame(colonnes)


def test_kelvins_convertis_en_celsius(tmp_path):
    """273,15 K doit valoir 0 °C. Laisser des kelvins ne casse rien : cela rend
    seulement tous les seuils métier faux de 273 degrés."""
    champ = grille([1.0, 2.0], [46.0, 45.0], {"t2m": 283.15})
    chemin = tmp_path / "era5.nc"
    champ.to_netcdf(chemin)

    tableau = meteo.extraire_aux_stations(
        str(chemin),
        stations(station_id=["A"], lon_wgs84=[1.4], lat_wgs84=[45.6]),
    )
    assert "t2m" not in tableau.columns, "le nom court ERA5 doit disparaître"
    assert tableau["temperature_c"].iloc[0] == pytest.approx(10.0)


def test_precipitation_convertie_de_metres_en_millimetres(tmp_path):
    """`tp` est un cumul en MÈTRES sur l'heure écoulée. 0,001 m = 1 mm."""
    champ = grille([1.0, 2.0], [46.0, 45.0], {"tp": 0.001})
    chemin = tmp_path / "era5.nc"
    champ.to_netcdf(chemin)

    tableau = meteo.extraire_aux_stations(
        str(chemin), stations(station_id=["A"], lon_wgs84=[1.4], lat_wgs84=[45.6])
    )
    assert tableau["precipitation_mm"].iloc[0] == pytest.approx(1.0)


def test_rayonnement_converti_de_joules_en_watts(tmp_path):
    """`ssrd` est un cumul en J/m² sur l'heure. Divisé par 3600 s il redevient un flux
    moyen en W/m² — la grandeur que lit un physicien de l'atmosphère."""
    champ = grille([1.0, 2.0], [46.0, 45.0], {"ssrd": 3_600_000.0})
    chemin = tmp_path / "era5.nc"
    champ.to_netcdf(chemin)

    tableau = meteo.extraire_aux_stations(
        str(chemin), stations(station_id=["A"], lon_wgs84=[1.4], lat_wgs84=[45.6])
    )
    assert tableau["rayonnement_w_m2"].iloc[0] == pytest.approx(1000.0)


def test_vent_de_nord_donne_une_direction_de_zero(tmp_path):
    """Convention météorologique : la direction dit d'où VIENT le vent. Un vent de
    nord souffle vers le sud, donc v est négatif et la direction vaut 0°.

    Se tromper de sens ferait pointer tous les panaches à l'opposé — et les variables
    d'exposition anisotrope seraient exactement à l'envers, sans rien casser.
    """
    champ = grille([1.0, 2.0], [46.0, 45.0], {"u10": 0.0, "v10": -5.0})
    chemin = tmp_path / "era5.nc"
    champ.to_netcdf(chemin)

    tableau = meteo.extraire_aux_stations(
        str(chemin), stations(station_id=["A"], lon_wgs84=[1.4], lat_wgs84=[45.6])
    )
    assert tableau["vent_direction_deg"].iloc[0] == pytest.approx(0.0)
    assert tableau["vent_vitesse_m_s"].iloc[0] == pytest.approx(5.0)


def test_station_hors_domaine_refusee(tmp_path):
    """Le piège central : `method="nearest"` rabat un point hors emprise sur la
    cellule de bord et renvoie une valeur parfaitement plausible. Une station
    recevrait la météo d'un autre lieu, sans le moindre signal."""
    champ = grille(np.arange(0.0, 5.01, 0.25), np.arange(46.0, 44.99, -0.25),
                   {"t2m": 280.0})
    chemin = tmp_path / "era5.nc"
    champ.to_netcdf(chemin)

    with pytest.raises(ValueError, match="hors du domaine"):
        meteo.extraire_aux_stations(
            str(chemin),
            stations(station_id=["Brest"], lon_wgs84=[-4.4866], lat_wgs84=[48.386]),
        )


def test_station_juste_en_bordure_acceptee(tmp_path):
    """La tolérance vaut une maille : une station à l'intérieur du domaine, même
    proche du bord, doit passer. Un contrôle trop strict rejetterait des stations
    littorales parfaitement couvertes."""
    champ = grille(np.arange(0.0, 5.01, 0.25), np.arange(46.0, 44.99, -0.25),
                   {"t2m": 280.0})
    chemin = tmp_path / "era5.nc"
    champ.to_netcdf(chemin)

    tableau = meteo.extraire_aux_stations(
        str(chemin), stations(station_id=["bord"], lon_wgs84=[0.02], lat_wgs84=[45.01])
    )
    assert len(tableau) == 1


def test_longitudes_cams_en_360_correctement_rattachees(tmp_path):
    """Sur une grille CAMS livrée en [0, 360] et non monotone, une station à l'ouest
    de Greenwich doit retrouver SA maille, pas celle du bord."""
    lon_cams = np.concatenate([np.arange(358.0, 360.0, 0.5), np.arange(0.0, 3.01, 0.5)])
    lat = np.arange(45.0, 42.99, -0.5)
    valeurs = np.zeros((1, len(lat), len(lon_cams)))
    # On marque la maille attendue pour une station à -1,0° : c'est 359,0 en [0, 360].
    valeurs[:, :, list(lon_cams).index(359.0)] = 42.0

    champ = xr.Dataset(
        {"o3_conc": (("time", "latitude", "longitude"), valeurs)},
        coords={"time": pd.date_range("2024-01-01", periods=1, freq="h"),
                "latitude": lat, "longitude": lon_cams},
    )
    chemin = tmp_path / "cams.nc"
    champ.to_netcdf(chemin)

    tableau = meteo.extraire_aux_stations(
        str(chemin), stations(station_id=["ouest"], lon_wgs84=[-1.0], lat_wgs84=[44.0])
    )
    assert tableau["o3_conc"].iloc[0] == 42.0, "la maille 359° = -1° doit être retenue"
    assert tableau["maille_lon"].iloc[0] == pytest.approx(-1.0)


def test_horodatage_explicitement_en_utc(tmp_path):
    """ERA5 livre des horodatages naïfs, qui sont en UTC. Les laisser naïfs empêche la
    jointure avec le panneau — ou pire, la fait passer par une conversion locale."""
    champ = grille([1.0, 2.0], [46.0, 45.0], {"t2m": 280.0}, heures=3)
    chemin = tmp_path / "era5.nc"
    champ.to_netcdf(chemin)

    tableau = meteo.extraire_aux_stations(
        str(chemin), stations(station_id=["A"], lon_wgs84=[1.4], lat_wgs84=[45.6])
    )
    assert str(tableau["timestamp_utc"].dt.tz) == "UTC"
    assert "valid_time" not in tableau.columns


def champ_prevision(tmp_path, nom="ENS_FORECAST_2024-12-01.nc", echeances=(0, 1, 72)):
    """Membre CAMS réaliste : `time` porte l'ÉCHÉANCE en heures, pas une date."""
    lon = np.arange(0.0, 3.01, 0.5)
    lat = np.arange(45.0, 42.99, -0.5)
    valeurs = np.zeros((len(echeances), len(lat), len(lon)))
    champ = xr.Dataset(
        {"o3_conc": (("time", "latitude", "longitude"), valeurs)},
        coords={"time": np.array(echeances, dtype="float32"),
                "latitude": lat, "longitude": lon},
    )
    chemin = tmp_path / nom
    champ.to_netcdf(chemin)
    return chemin


def test_echeance_cams_n_est_pas_un_horodatage(tmp_path):
    """Le piège le plus coûteux du jeu CAMS : `time` vaut 0…72 heures d'échéance.
    Le passer à `pd.to_datetime` produit `1970-01-01 + 72 nanosecondes` — une colonne
    d'apparence valide, ordonnée, sans manquant, et fausse de cinquante-cinq ans.

    La date de base ne vit QUE dans le nom du fichier.
    """
    chemin = champ_prevision(tmp_path)
    tableau = meteo.extraire_aux_stations(
        str(chemin), stations(station_id=["A"], lon_wgs84=[1.4], lat_wgs84=[44.0])
    )

    assert set(tableau["echeance_h"]) == {0, 1, 72}
    horodatages = tableau.set_index("echeance_h")["timestamp_utc"]
    assert horodatages[0] == pd.Timestamp("2024-12-01 00:00", tz="UTC")
    assert horodatages[72] == pd.Timestamp("2024-12-04 00:00", tz="UTC"), "J+3"
    assert horodatages.dt.year.min() == 2024, "aucun horodatage de 1970"


def test_prevision_sans_date_dans_le_nom_refusee(tmp_path):
    """Sans date de base, aucun temps absolu n'est reconstituable. Échouer vaut mieux
    que produire des horodatages de 1970 que rien ne signalerait."""
    chemin = champ_prevision(tmp_path, nom="sans_date.nc")
    with pytest.raises(ValueError, match="date de base"):
        meteo.extraire_aux_stations(
            str(chemin), stations(station_id=["A"], lon_wgs84=[1.4], lat_wgs84=[44.0])
        )


def test_indices_plus_proches_sur_axe_non_monotone():
    """Le rattachement par indices doit fonctionner sur un axe non trié — c'est le cas
    des grilles CAMS à cheval sur Greenwich, et c'est ce qui permet de ne pas trier."""
    axe = np.array([358.0, 359.0, 0.0, 1.0, 2.0])
    indices = meteo.indices_plus_proches(axe, np.array([0.9, 358.2, 2.0]))
    np.testing.assert_array_equal(indices, [3, 0, 4])


def test_coordonnees_degenerees_supprimees(tmp_path):
    """`number` et `expver` sont constants dans nos requêtes : les garder alourdit les
    jointures sans rien apporter."""
    champ = grille([1.0, 2.0], [46.0, 45.0], {"t2m": 280.0})
    champ = champ.assign_coords(number=0, expver="0001")
    chemin = tmp_path / "era5.nc"
    champ.to_netcdf(chemin)

    tableau = meteo.extraire_aux_stations(
        str(chemin), stations(station_id=["A"], lon_wgs84=[1.4], lat_wgs84=[45.6])
    )
    assert "number" not in tableau.columns
    assert "expver" not in tableau.columns
