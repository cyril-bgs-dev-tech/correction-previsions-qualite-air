"""Tests du référentiel de stations.

Le fichier source est volumineux (7,9 Mo) et distant : les tests s'exécutent sur le
fichier déjà téléchargé dans `data/raw/` s'il est présent, et sont ignorés sinon.
Ils verrouillent des invariants métier, pas des détails d'implémentation.
"""

from pathlib import Path

import pandas as pd
import pytest

from aq.ingest import stations as st

FICHIER = Path(__file__).resolve().parents[1] / "data" / "raw" / "datasetD.xls"

pytestmark = pytest.mark.skipif(
    not FICHIER.exists(), reason="Dataset D absent de data/raw/ — lancer l'ingestion"
)


@pytest.fixture(scope="module")
def contenu() -> bytes:
    return FICHIER.read_bytes()


@pytest.fixture(scope="module")
def referentiel(contenu) -> pd.DataFrame:
    return st.construire_referentiel(contenu)


def test_effectifs_nationaux(referentiel):
    """868 stations enregistrées, 515 actives — millésime 09/12/2025.

    Ce chiffre de 515, celui qui circule, couvre la France ENTIÈRE : il inclut
    l'Outre-mer. C'est l'effectif métropolitain qui fonde le projet.
    """
    assert len(referentiel) == 868
    assert int(referentiel["active"].sum()) == 515


def test_outre_mer_distingue_de_la_metropole(referentiel):
    """55 stations sont hors emprise métropolitaine (Réunion, Antilles, Guyane,
    Mayotte, Saint-Martin). Les inclure dans un entraînement spatial métropolitain
    dégraderait le modèle : régime tropical, sources et chimie différentes.
    """
    hors = referentiel[~referentiel["metropole"]]
    assert len(hors) == 55
    assert (hors["reseau"] != st.RESEAU_OCCITANIE).all()

    metropole = referentiel[referentiel["metropole"] & referentiel["active"]]
    # L'effectif réellement mobilisable, à comparer aux 38 stations occitanes.
    assert 440 < len(metropole) < 490


def test_effectifs_occitanie(referentiel):
    """38 stations actives sur 61 enregistrées dans le réseau ATMO Occitanie.

    C'est l'effectif qui fonde la stratégie d'entraînement national : les variables
    purement spatiales s'estiment sur le nombre de stations, pas sur le nombre
    d'heures, et 38 points ne suffisent pas à ajuster une fonction de transfert
    spatiale robuste.
    """
    occitanie = referentiel[referentiel["reseau"] == st.RESEAU_OCCITANIE]
    assert len(occitanie) == 61
    assert int(occitanie["active"].sum()) == 38


def test_stations_de_fond_occitanie(referentiel):
    """23 stations de fond actives seulement.

    L'indice ATMO ne se calcule que sur les stations de fond — jamais trafic. C'est
    donc 23 points, et non 38, qui alimentent la reconstitution de l'indice.
    """
    occitanie = referentiel[
        (referentiel["reseau"] == st.RESEAU_OCCITANIE) & referentiel["active"]
    ]
    assert int((occitanie["type_station"] == "background").sum()) == 23


def test_le_code_station_n_est_pas_le_departement(referentiel):
    """Piège vérifié : FR34051 est à Châteauroux (Indre), pas dans l'Hérault.

    Sélectionner une région par le préfixe du code produirait un jeu silencieusement
    faux. L'appartenance passe par le réseau ou par une jointure spatiale.
    """
    ligne = referentiel.loc[referentiel["station_id"] == "FR34051"].iloc[0]
    assert ligne["commune"] == "CHÂTEAUROUX"
    assert ligne["lat_wgs84"] == pytest.approx(46.798, abs=0.01)
    assert ligne["reseau"] != st.RESEAU_OCCITANIE


def test_incoherences_de_classification_signalees(referentiel):
    """Certaines stations déclarent des classifications différentes selon le
    polluant (ex. MEZE TRAFIC : 4 points « traffic », 1 « background »). On retient
    le mode et on compte les divergences plutôt que de prendre la première valeur.
    """
    assert int((referentiel["n_types_distincts"] > 1).sum()) == 39
    meze = referentiel.loc[referentiel["station_id"] == "FR08026"].iloc[0]
    assert meze["type_station"] == "traffic"
    assert meze["n_types_distincts"] > 1


def test_coordonnees_metropolitaines_dans_l_emprise(referentiel):
    metropole = referentiel[referentiel["metropole"]]
    assert metropole["lat_wgs84"].between(41.0, 51.5).all()
    assert metropole["lon_wgs84"].between(-5.5, 9.7).all()
    assert referentiel["lat_wgs84"].notna().all(), "aucune coordonnée manquante attendue"


def test_projection_lambert93(referentiel):
    """La projection doit produire des coordonnées métriques dans l'emprise légale."""
    projete = st.ajouter_lambert93(referentiel)
    occitanie = projete[
        (projete["reseau"] == st.RESEAU_OCCITANIE) & projete["active"]
    ]
    assert occitanie["x_l93"].between(90_000, 1_250_000).all()
    assert occitanie["y_l93"].between(6_050_000, 7_120_000).all()

    # Contrôle d'échelle : l'emprise des stations occitanes doit se compter en
    # centaines de kilomètres. Une distance calculée en degrés serait ~10^5 fois
    # plus petite — ce test attraperait l'oubli de projection.
    etendue_x_km = (occitanie["x_l93"].max() - occitanie["x_l93"].min()) / 1000
    assert 200 < etendue_x_km < 600


def test_une_seule_projection_source(contenu):
    """Le SRS est déclaré ligne par ligne : on vérifie qu'il est bien homogène en
    EPSG:4326 plutôt que de le supposer."""
    stations = st.lire_stations(contenu)  # lève si hétérogène
    assert len(stations) == 868
