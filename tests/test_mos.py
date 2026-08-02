"""Tests de la correction apprise des sorties CAMS.

Deux choses sont vérifiées ici, et ce sont les deux qui décident si le résultat veut
dire quelque chose : l'encodage cyclique du temps, et le fait que l'évaluation exclue
bien des **stations entières**.
"""

import numpy as np
import pandas as pd
import pytest

from aq.models import mos


def horodatages(debut="2024-01-01", n=48):
    return pd.Series(pd.date_range(debut, periods=n, freq="h", tz="UTC"))


def test_minuit_et_23h_sont_voisins_apres_encodage():
    """Le piège de l'encodage du temps : sur une échelle 0-23, minuit et 23 h sont aux
    extrémités opposées alors qu'ils se suivent d'une heure. Un arbre devrait dépenser
    plusieurs coupures pour reconstituer cette continuité."""
    t = mos.variables_calendaires(
        pd.Series(pd.to_datetime(["2024-01-01 23:00", "2024-01-02 00:00"], utc=True))
    )
    distance = np.hypot(
        t["heure_cos"].iloc[0] - t["heure_cos"].iloc[1],
        t["heure_sin"].iloc[0] - t["heure_sin"].iloc[1],
    )
    # Deux heures consécutives sur un cercle de rayon 1 : 2·sin(π/24) ≈ 0,26.
    assert distance == pytest.approx(0.26, abs=0.02)


def test_decembre_et_janvier_sont_voisins():
    """Même piège à l'échelle de l'année : le 31 décembre et le 1er janvier sont
    séparés de 364 jours sur une échelle linéaire, d'un jour dans la réalité."""
    t = mos.variables_calendaires(
        pd.Series(pd.to_datetime(["2024-12-31", "2025-01-01"], utc=True))
    )
    distance = np.hypot(
        t["jour_annee_cos"].iloc[0] - t["jour_annee_cos"].iloc[1],
        t["jour_annee_sin"].iloc[0] - t["jour_annee_sin"].iloc[1],
    )
    assert distance < 0.05


def test_encodage_cyclique_reste_borne():
    t = mos.variables_calendaires(horodatages(n=24 * 40))
    for colonne in ("heure_cos", "heure_sin", "jour_annee_cos", "jour_annee_sin"):
        assert t[colonne].between(-1, 1).all()


def test_weekend_correctement_identifie():
    """Le rythme hebdomadaire des émissions n'est pas circulaire : samedi et dimanche
    se ressemblent, lundi et dimanche non. D'où un indicateur, pas un cycle."""
    t = mos.variables_calendaires(
        pd.Series(pd.to_datetime(
            ["2024-01-05", "2024-01-06", "2024-01-07", "2024-01-08"], utc=True
        ))
    )
    assert list(t["weekend"]) == [0, 1, 1, 0], "vendredi, samedi, dimanche, lundi"


def jeu_synthetique(n_stations=20, n_heures=200, graine=0):
    """Jeu où la correction à apprendre est connue : CAMS surestime d'autant plus que
    la station est haute."""
    rng = np.random.default_rng(graine)
    lignes = []
    for s in range(n_stations):
        altitude = rng.uniform(0, 1000)
        temps = pd.date_range("2024-01-01", periods=n_heures, freq="h", tz="UTC")
        vrai = 40 + 10 * np.sin(np.arange(n_heures) * 2 * np.pi / 24)
        lignes.append(pd.DataFrame({
            "station_id": f"S{s:03d}",
            "timestamp_utc": temps,
            "altitude_mnt_m": altitude,
            "cams": vrai + altitude * 0.01 + rng.normal(0, 1, n_heures),
            "valeur": vrai + rng.normal(0, 1, n_heures),
        }))
    return pd.concat(lignes, ignore_index=True)


def test_evaluation_exclut_des_stations_entieres():
    """**Le point décisif.** Découper au hasard dans les lignes laisserait, pour chaque
    station de test, des milliers d'heures de cette même station dans l'entraînement :
    le modèle apprendrait son niveau moyen par cœur et afficherait un score qui ne dit
    rien de sa capacité à prédire là où l'on ne mesure pas.

    Ce test vérifie que chaque station apparaît **exactement une fois** en test, donc
    qu'aucune n'a servi à la fois d'entraînement et d'évaluation.
    """
    jeu = jeu_synthetique()
    resultat = mos.ajuster_par_stations_exclues(
        jeu, ["altitude_mnt_m", "cams"], colonne_cams="cams", n_plis=4
    )
    comptes = resultat.predictions.groupby("station_id").size()
    assert len(comptes) == 20, "toutes les stations doivent être évaluées"
    assert (comptes == 200).all(), "chacune exactement une fois, sur toutes ses heures"


def test_la_correction_ameliore_un_biais_apprenable():
    """Sur un jeu où CAMS surestime proportionnellement à l'altitude, la correction
    doit récupérer l'essentiel — y compris sur des stations jamais vues."""
    jeu = jeu_synthetique()
    r = mos.ajuster_par_stations_exclues(
        jeu, ["altitude_mnt_m", "cams"], colonne_cams="cams", n_plis=4
    )
    erreur_brute = np.sqrt(((r.predictions["cams"] - r.predictions["observe"])**2).mean())
    erreur_corrigee = np.sqrt(
        ((r.predictions["corrige"] - r.predictions["observe"])**2).mean()
    )
    assert erreur_corrigee < erreur_brute / 2


def jeu_asymetrique(n_stations=25, n_heures=400, graine=1):
    """Jeu à distribution asymétrique, avec de rares épisodes — comme l'ozone réel.

    83 % des points sont bas, quelques pourcents forment une queue haute. C'est cette
    forme qui piège un modèle entraîné à minimiser l'erreur quadratique.
    """
    rng = np.random.default_rng(graine)
    lignes = []
    for s in range(n_stations):
        base = rng.uniform(20, 40)
        fond = rng.gamma(2.0, 12.0, n_heures) + base
        episode = rng.random(n_heures) < 0.02
        vrai = fond + episode * rng.uniform(80, 140, n_heures)
        lignes.append(pd.DataFrame({
            "station_id": f"S{s:03d}",
            "timestamp_utc": pd.date_range("2024-06-01", periods=n_heures,
                                           freq="h", tz="UTC"),
            "altitude_mnt_m": rng.uniform(0, 800),
            "cams": vrai * 0.85 + rng.normal(0, 5, n_heures),
            "valeur": vrai,
        }))
    return pd.concat(lignes, ignore_index=True)


def test_la_correction_ne_doit_pas_ecraser_la_queue():
    """**Régression majeure déjà rencontrée sur données réelles.** En apprenant
    l'observation directement, le modèle traitait bien les 83 % de valeurs basses et
    écrasait les fortes : le RMSE global gagnait 13 %, mais la détection des
    dépassements du seuil d'information passait de 5 sur 15 à 0 sur 15.

    Apprendre le **résidu** ancre la prédiction à la physique de CAMS. Ce test vérifie
    que la correction ne dégrade pas la queue haute de la distribution.
    """
    jeu = jeu_asymetrique()
    colonnes = ["altitude_mnt_m", "cams"]

    residu = mos.ajuster_par_stations_exclues(
        jeu, colonnes, colonne_cams="cams", n_plis=4, cible_residu=True
    ).predictions
    haut = residu[residu["observe"] >= residu["observe"].quantile(0.98)]

    rmse_cams = np.sqrt(((haut["cams"] - haut["observe"]) ** 2).mean())
    rmse_mos = np.sqrt(((haut["corrige"] - haut["observe"]) ** 2).mean())
    assert rmse_mos < rmse_cams * 1.1, (
        "la correction ne doit pas dégrader la queue haute — c'est là que se jouent "
        "les épisodes, donc l'indice ATMO"
    )


def test_cible_directe_ecrase_davantage_la_queue_que_le_residu():
    """Fige la raison du choix : sur une distribution asymétrique, prédire
    l'observation directement amortit plus fortement les valeurs hautes que prédire
    le résidu. Si cet écart disparaissait, le choix mériterait d'être réexaminé."""
    jeu = jeu_asymetrique()
    colonnes = ["altitude_mnt_m", "cams"]

    def erreur_en_queue(cible_residu: bool) -> float:
        p = mos.ajuster_par_stations_exclues(
            jeu, colonnes, colonne_cams="cams", n_plis=4, cible_residu=cible_residu
        ).predictions
        haut = p[p["observe"] >= p["observe"].quantile(0.98)]
        return float(np.sqrt(((haut["corrige"] - haut["observe"]) ** 2).mean()))

    assert erreur_en_queue(True) < erreur_en_queue(False)


def test_aucune_concentration_negative():
    """Une concentration négative n'existe pas : la correction peut en produire là où
    CAMS est déjà bas, et le modèle serait pénalisé pour une valeur impossible."""
    jeu = jeu_asymetrique(n_stations=12, n_heures=150)
    p = mos.ajuster_par_stations_exclues(
        jeu, ["altitude_mnt_m", "cams"], colonne_cams="cams", n_plis=3
    ).predictions
    assert (p["corrige"] >= 0).all()


def test_cibles_manquantes_ecartees_de_l_entrainement():
    """Le panneau conserve des lignes horaires sans mesure valide — 11 % sur données
    réelles, et 49 couples (station, polluant) entièrement vides. Le gradient boosting
    les absorbe sans se plaindre, et la correction s'en trouve amortie.

    Ce test vérifie qu'un jeu massivement lacunaire donne le même modèle que le même
    jeu nettoyé : autrement dit, que les lignes sans cible n'influencent rien.
    """
    jeu = jeu_synthetique(n_stations=16, n_heures=200)
    colonnes = ["altitude_mnt_m", "cams"]

    troue = jeu.copy()
    rng = np.random.default_rng(3)
    manquantes = rng.random(len(troue)) < 0.35
    troue.loc[manquantes, "valeur"] = np.nan

    r_troue = mos.ajuster_par_stations_exclues(
        troue, colonnes, colonne_cams="cams", n_plis=4
    ).predictions.dropna(subset=["observe"])
    r_propre = mos.ajuster_par_stations_exclues(
        troue.dropna(subset=["valeur"]), colonnes, colonne_cams="cams", n_plis=4
    ).predictions

    erreur = lambda p: float(np.sqrt(((p["corrige"] - p["observe"]) ** 2).mean()))
    assert erreur(r_troue) == pytest.approx(erreur(r_propre), rel=0.08), (
        "les lignes sans observation ne doivent pas peser sur le modèle"
    )


def test_aucune_prediction_nan_sur_cible_presente():
    """Une station dont toutes les mesures manquent ne doit pas empêcher de prédire
    les autres."""
    jeu = jeu_synthetique(n_stations=12, n_heures=120)
    jeu.loc[jeu["station_id"] == "S000", "valeur"] = np.nan
    p = mos.ajuster_par_stations_exclues(
        jeu, ["altitude_mnt_m", "cams"], colonne_cams="cams", n_plis=3
    ).predictions
    avec_cible = p.dropna(subset=["observe"])
    assert len(avec_cible) > 0
    assert avec_cible["corrige"].notna().all()


def test_importances_normalisees():
    jeu = jeu_synthetique(n_stations=12, n_heures=100)
    r = mos.ajuster_par_stations_exclues(
        jeu, ["altitude_mnt_m", "cams"], colonne_cams="cams", n_plis=3
    )
    assert r.importances["importance"].sum() == pytest.approx(1.0)
    assert list(r.importances.columns) == ["variable", "importance"]
