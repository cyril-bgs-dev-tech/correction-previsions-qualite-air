"""Tests des signatures régionales.

Chaque test fige une distinction que le domaine impose et que les données seules ne
donnent pas : régional contre local, importé contre produit sur place, chauffage contre
trafic.
"""

import numpy as np
import pandas as pd
import pytest

from aq.eval import phenomenes


def panneau(valeurs_par_station: dict, debut="2024-01-01", freq="h") -> pd.DataFrame:
    """Panneau horaire à partir d'un dictionnaire {station: [valeurs]}."""
    blocs = []
    for station, valeurs in valeurs_par_station.items():
        blocs.append(pd.DataFrame({
            "station_id": station,
            "timestamp_utc": pd.date_range(debut, periods=len(valeurs),
                                           freq=freq, tz="UTC"),
            "valeur": valeurs,
        }))
    return pd.concat(blocs, ignore_index=True)


# ── Origine : la granulométrie tranche là où la synchronicité ne dit rien ──

def test_poussiere_minerale_reconnue_a_son_rapport_eleve():
    """Les poussières sahariennes sont des particules **grossières** : le rapport
    PM10/PM2.5 y dépasse 2. Mesuré sur les épisodes occitans de juin 2022 : 2,44."""
    assert phenomenes.classer_origine(38.4, 15.7) == "minéral"


def test_combustion_reconnue_a_son_rapport_bas():
    """Chauffage au bois et trafic produisent du **fin** : rapport voisin de 1,2."""
    assert phenomenes.classer_origine(44.9, 41.5) == "combustion"


def test_l_episode_le_plus_intense_n_est_pas_forcement_importe():
    """**Le cas qui justifie ce module.** Le 27/02/2013 est l'épisode le plus intense
    de la série occitane — 55,7 µg/m³ de PM10 — et parfaitement homogène entre stations.
    Son rapport de 1,19 le classe pourtant en combustion : il n'est **pas** déductible
    au titre de l'article 20 de la directive 2008/50/CE.

    Le seul critère de synchronicité l'aurait retenu à tort, et une AASQA aurait
    déclaré comme naturel un dépassement qui ne l'est pas.
    """
    assert phenomenes.classer_origine(55.7, 46.9) == "combustion"


def test_origine_indeterminee_sans_donnee_exploitable():
    """Mieux vaut « indéterminé » qu'une classification inventée : la conséquence est
    réglementaire."""
    assert phenomenes.classer_origine(np.nan, 20.0) == "indéterminé"
    assert phenomenes.classer_origine(40.0, 0.0) == "indéterminé"


# ── Épisodes importés : l'homogénéité, pas le niveau ──

def test_episode_homogene_retenu():
    """Un apport extérieur touche toutes les stations à la fois."""
    n = 24 * 40
    fond = [10.0] * n
    pointe = fond.copy()
    for h in range(24 * 20, 24 * 21):
        pointe[h] = 60.0
    jeu = panneau({f"S{i}": pointe for i in range(8)})
    resultat = phenomenes.episodes_importes(jeu)
    assert resultat["importe"].sum() >= 1


def test_pointe_locale_ecartee_malgre_un_niveau_eleve():
    """**Le critère décisif.** Une seule station qui s'envole produit une moyenne
    territoriale élevée, mais un coefficient de variation énorme. Sans ce test, une
    pollution industrielle ponctuelle serait déclarée d'origine naturelle."""
    n = 24 * 40
    calme = [10.0] * n
    envolee = calme.copy()
    for h in range(24 * 20, 24 * 21):
        envolee[h] = 400.0
    jeu = panneau({"S0": envolee, **{f"S{i}": calme for i in range(1, 8)}})
    resultat = phenomenes.episodes_importes(jeu)
    assert not resultat["importe"].any(), (
        "une pointe sur une seule station n'est pas un apport régional"
    )


def test_jours_a_trop_peu_de_stations_ecartes():
    """Trois stations ne permettent pas de juger d'une homogénéité territoriale."""
    jeu = panneau({f"S{i}": [10.0] * 240 for i in range(3)})
    resultat = phenomenes.episodes_importes(jeu, n_stations_min=6)
    assert resultat.empty


# ── Chauffage au bois : c'est le contraste entre saisons qui signe ──

def test_chauffage_bois_signe_par_le_contraste_saisonnier():
    """Un pic du soir existe aussi l'été (trafic, brise). Ce qui distingue le chauffage,
    c'est qu'il **disparaît** hors saison — d'où le rapport entre les deux saisons."""
    heures = pd.date_range("2024-01-01", "2024-12-31 23:00", freq="h", tz="UTC")
    locale = heures.tz_convert("Europe/Paris")
    hiver = locale.month.isin([12, 1, 2])
    soir = locale.hour.isin([19, 20, 21, 22])

    valeurs = np.full(len(heures), 10.0)
    valeurs[soir] += 3.0                    # trafic du soir, toute l'année
    valeurs[hiver & soir] += 15.0           # chauffage, hiver seulement

    jeu = pd.DataFrame({"station_id": "S0", "timestamp_utc": heures,
                        "valeur": valeurs})
    signature = phenomenes.signature_chauffage_bois(jeu)
    assert signature["hiver_rapport"] > 2.0
    assert signature["ete_rapport"] < 1.5
    assert signature["contraste_saisonnier"] > 1.5


# ── Brise de mer : un pic littoral plus précoce trahit l'advection ──

def test_brise_de_mer_detectee_par_un_pic_littoral_precoce():
    """Sous photochimie locale, l'ozone culmine plus tard là où les précurseurs
    abondent — donc à l'intérieur. Un pic littoral **plus précoce et plus élevé**
    signale un apport advecté par la brise."""
    heures = pd.date_range("2024-06-01", "2024-08-31 23:00", freq="h", tz="UTC")
    locale = heures.tz_convert("Europe/Paris")
    blocs = []
    for station, lon, pic in (("LITT", 4.0, 16), ("INT", 1.5, 18)):
        cycle = 40 + 45 * np.clip(np.cos((locale.hour.to_numpy() - pic) * np.pi / 12), 0, None)
        blocs.append(pd.DataFrame({"station_id": station, "timestamp_utc": heures,
                                   "valeur": cycle, "lon_wgs84": lon}))
    table = phenomenes.signature_brise_de_mer(pd.concat(blocs, ignore_index=True))
    littoral = table[table["zone"] == "littoral"].iloc[0]
    interieur = table[table["zone"] == "interieur"].iloc[0]
    assert littoral["heure_maximum"] < interieur["heure_maximum"]


def test_profil_horaire_calcule_en_heure_locale():
    """Les cycles d'émission suivent l'activité humaine, donc l'heure de la montre. Un
    profil en UTC mélangerait 19 h d'hiver et 20 h d'été, effaçant le pic cherché."""
    heures = pd.date_range("2024-07-01", periods=48, freq="h", tz="UTC")
    locale = heures.tz_convert("Europe/Paris")
    valeurs = np.where(locale.hour == 21, 50.0, 10.0)
    jeu = pd.DataFrame({"station_id": "S0", "timestamp_utc": heures,
                        "valeur": valeurs})
    profil = phenomenes.profil_horaire(jeu, [7])
    assert profil.idxmax() == 21, "le pic doit tomber à 21 h locales, pas 19 h UTC"
