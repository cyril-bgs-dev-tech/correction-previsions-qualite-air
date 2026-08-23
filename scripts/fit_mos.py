"""Apprend une correction des prévisions CAMS et la mesure contre CAMS brut.

Usage : python scripts/fit_mos.py [--polluant O3] [--horizon 1]
Sorties : reports/MOS.md et reports/mos_{polluant}.csv

L'évaluation se fait par **stations entièrement exclues** : le modèle prédit des
stations qu'il n'a jamais vues. C'est la seule question qui compte pour une
spatialisation — savoir prédire là où l'on ne mesure pas.
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.eval import comparaison as cmp  # noqa: E402
from aq.rapport import libelle_echeance
from aq.harmonize.timegrid import mois_couverts  # noqa: E402
from aq.models import mos  # noqa: E402

ESPECES = {"o3": ("O3", "o3_conc"), "no2": ("NO2", "no2_conc"),
           "pm25": ("PM25", "pm2p5_conc"),
           # Les PM10 sont arrivées le 01/08/2026, depuis le flux national LCSQA pour les
           # observations et l'ADS pour les prévisions. Elles manquaient depuis le début,
           # et la mesure qui l'a rendu intenable : **40 des 52 vigilances réellement
           # déclarées** en Occitanie portent sur ce polluant, contre 12 sur l'ozone.
           "pm10": ("PM10", "pm10_conc")}

# ── Le panel unifié — EEA jusqu'à fin 2023, LCSQA ensuite ──────────────────────
#
# Le corpus apparié était borné à **18 mois** non par les prévisions mais par les
# observations **EEA**, qui s'arrêtent en décembre 2024. Le flux LCSQA couvre 2024-01 →
# 2026-07 ; les recoller porte le corpus à **36 mois** et les plis temporels de 17 à **29**.
#
# Le raccord n'est pas une hypothèse. `scripts/concordance_eea_lcsqa.py` l'a mesuré sur les
# **treize mois de recouvrement**, et les deux sources ne concordent pas — **elles sont
# identiques** : 100,0 % de couples strictement égaux sur O₃ et NO₂, 99,7 % sur PM2,5, écart
# absolu médian **0,0000 µg/m³**, convention horaire confirmée (le décalage nul gagne de 206×
# à 18 703× sur ses voisins), stabilité mensuelle parfaite. L'EEA reçoit les mesures
# françaises par le rapportage E2, celui-là même que publie le LCSQA.
#
# ⚠️ **La seule vraie différence était la population de stations** — le LCSQA en publie
# davantage. `scripts/panel_unifie.py` ne retient donc que les stations **communes aux deux
# sources**, sur toute la fenêtre : la population devient constante **par construction**.
# Sans cela, l'ensemble des stations aurait changé au milieu du corpus, et le double aveugle
# aurait lu ce déplacement comme une non-stationnarité de l'atmosphère.
#
# L'ancien panel EEA reste sur le disque et reste la source de tout ce qui précède 2023-06.
PANEL_UNIFIE = "data/processed/panel_unifie_lcsqa.parquet"
PANEL_PAR_POLLUANT = {p: PANEL_UNIFIE for p in ("O3", "NO2", "PM25", "PM10")}
PANEL_DEFAUT = "data/processed/panel_metropole_ds2.parquet"

# ⚠️ La clé est l'index de tranche, le libellé est J+(clé−1) : la tranche 1
# couvre les heures 1-24 d'une sortie 00 UTC, donc le JOUR MÊME. Voir
# `aq.rapport.libelle_echeance`, qui le dérive au lieu de le laisser écrire.
# La tranche 4 (73-96 h) est le dernier étage que CAMS Europe produise.
TRANCHES = {1: (1, 24), 2: (25, 48), 3: (49, 72), 4: (73, 96)}

# Bandes d'analyse, calées sur les classes de l'indice ATMO plutôt que sur des
# quantiles : ce sont elles qui décident de la couleur affichée au public.
BANDES = {
    "O3": [(0, 40), (40, 80), (80, 120), (120, 180), (180, np.inf)],
    "NO2": [(0, 20), (20, 40), (40, 90), (90, 200), (200, np.inf)],
    "PM25": [(0, 10), (10, 20), (20, 25), (25, 50), (50, np.inf)],
    # Bornes de sous-indice PM10 de l'arrêté du 10 juillet 2020.
    "PM10": [(0, 20), (20, 40), (40, 50), (50, 100), (100, np.inf)],
}

# Seuils réglementaires d'information et de recommandation (arrêté du 07/04/2016).
# Seul l'ozone en a un défini en moyenne horaire, d'où l'absence des deux autres.
SEUILS_INFORMATION = {"O3": 180.0}


def paires_cams_observations(polluant: str, horizon: int) -> pd.DataFrame:
    """Prévisions CAMS appariées aux observations — sans variable explicative.

    Sortie : `station_id`, `timestamp_utc`, `echeance_h`, `cams`, `valeur`.

    **Point d'entrée unique de l'appariement.** Tout ce qui a besoin du couple
    (prévision, observation) passe par ici — le MOS comme la surveillance de dérive.
    La fenêtre temporelle est délicate à établir et l'a déjà été de travers ; elle ne
    doit exister qu'à un seul endroit.
    """
    court = next(c for c, (p, _) in ESPECES.items() if p == polluant)
    colonne = ESPECES[court][1]
    bas, haut = TRANCHES[horizon]

    fichiers = sorted(glob.glob(
        str(RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_*.parquet")
    ))
    if not fichiers:
        raise SystemExit(f"Aucune prévision extraite pour {polluant}")

    blocs: list[pd.DataFrame] = []
    mois_prevus: set[pd.Period] = set()
    for fichier in fichiers:
        prev = pd.read_parquet(
            fichier, columns=["station_id", "timestamp_utc", "echeance_h", colonne]
        )
        prev = prev[prev["echeance_h"].between(bas, haut)]
        if prev.empty:
            continue

        # **La fenêtre d'observations se déduit des prévisions, jamais du nom du
        # fichier.** Un nom groupé `..._o3_202308_202309.parquet` porte deux mois ;
        # une expression ancrée à droite n'en capture qu'un, et le merge jette
        # silencieusement l'autre — c'est ainsi que six mois sur dix-sept avaient
        # disparu du jeu d'entraînement sans qu'aucune erreur ne soit levée. Les
        # prévisions débordent en outre sur le mois suivant, jusqu'à 72 h d'échéance :
        # leurs propres bornes sont la seule source exacte.
        debut = prev["timestamp_utc"].min()
        fin = prev["timestamp_utc"].max() + pd.Timedelta(hours=1)
        mois_prevus.update(mois_couverts(prev["timestamp_utc"]))

        obs = pd.read_parquet(
            RACINE / PANEL_PAR_POLLUANT.get(polluant, PANEL_DEFAUT),
            filters=[("timestamp_utc", ">=", debut), ("timestamp_utc", "<", fin),
                     ("polluant", "==", polluant)],
            columns=["station_id", "timestamp_utc", "valeur"],
        )
        blocs.append(prev.merge(obs, on=["station_id", "timestamp_utc"]))

    jeu = pd.concat(blocs, ignore_index=True).rename(columns={colonne: "cams"})

    # ── Les COPIES EXACTES, et pourquoi elles existaient — trouvé le 22/08/2026 ──────
    #
    # La clé (station, heure, échéance) n'était pas unique : **375 294 couples de l'ozone
    # et 418 039 des PM10** portaient deux lignes, soit 10,5 % du corpus horaire. Toutes
    # strictement identiques — même échéance, même valeur CAMS, même observation — et
    # toutes concentrées sur **2024-01, 2024-02 et le 1er mars 2024** : la fenêtre où le
    # panel recolle EEA et LCSQA, qui livrent la même mesure (mesuré à 100 % d'égalité sur
    # les treize mois de recouvrement) et dont l'union avait gardé les deux copies.
    #
    # Ce que ça faussait, et ce n'est pas anodin :
    #   * chaque ligne de ces deux mois pesait **double** à l'apprentissage comme au score ;
    #   * `n_heures` doublait, donc le filtre des 75 % ne filtrait plus rien ;
    #   * et surtout la moyenne glissante « 8 h », qui comptait alors **8 lignes = 4 heures
    #     réelles** : la cible ozone de 2024-01 et 2024-02 était un maximum de moyennes 4 h.
    #     98,6 % et 99,9 % des jours-station de ces deux mois en sortaient faux.
    #
    # On dédoublonne donc au **point d'entrée unique de l'appariement**, et l'on REFUSE de
    # le faire en silence si deux copies divergent : des lignes identiques se jettent sans
    # rien perdre, des lignes contradictoires posent une question de source qu'aucun
    # `drop_duplicates` ne doit trancher tout seul.
    cle = ["station_id", "timestamp_utc", "echeance_h"]
    doubles = jeu.duplicated(cle, keep=False)
    if doubles.any():
        divergents = jeu[doubles].groupby(cle)[["cams", "valeur"]].nunique().max()
        if (divergents > 1).any():
            raise SystemExit(
                f"{polluant} : des lignes partagent (station, heure, échéance) avec des "
                f"valeurs DIFFÉRENTES — {divergents.to_dict()} valeurs distinctes au pire. "
                f"Ce n'est plus un doublon, c'est un conflit de source : le trancher exige "
                f"de savoir laquelle fait foi.")
        mois_doubles = sorted(jeu.loc[doubles, "timestamp_utc"].dt.strftime("%Y-%m").unique())
        avant = len(jeu)
        jeu = jeu[~jeu.duplicated(cle)].reset_index(drop=True)
        print(f"doublons · {avant - len(jeu):,} copies exactes retirées sur {avant:,} "
              f"({100 * (avant - len(jeu)) / avant:.2f} %) · mois concernés : "
              f"{', '.join(mois_doubles)}", flush=True)

    # **Rendre la couverture visible.** Un mois de prévisions sans observation en face
    # disparaît du jeu sans lever d'erreur ; c'est légitime pour 2025, dont les
    # observations n'existent pas, et c'était un défaut pour les mois groupés. Dans les
    # deux cas la seule protection est de l'afficher.
    obtenus = mois_couverts(jeu["timestamp_utc"])
    manquants = sorted(mois_prevus - obtenus)
    print(f"couverture · {len(obtenus)} mois appariés sur {len(mois_prevus)} prévus"
          + (f" · sans observation : {', '.join(str(m) for m in manquants)}"
             if manquants else ""), flush=True)
    return jeu


def charger(polluant: str, horizon: int) -> pd.DataFrame:
    """Assemble prévisions CAMS, observations, et variables statiques."""
    jeu = paires_cams_observations(polluant, horizon)

    geo = pd.read_parquet(RACINE / "data/processed/geo_features_metropole.parquet")
    relief = pd.read_parquet(RACINE / "data/processed/relief_features_metropole.parquet")
    # **`altitude` était disponible depuis le début et n'était pas chargée.** C'est un
    # déterminant physique majeur de l'ozone — position par rapport à la couche limite
    # nocturne, gradient vertical, stations de montagne qui échappent à la titration
    # urbaine — et le jeu couvre de 0 à 1 750 m. Les neuf descripteurs de relief décrivent
    # la forme *locale* du terrain (position topographique, rugosité), jamais la hauteur
    # absolue. Candidat direct pour expliquer le biais de +28 µg/m³ observé dans le décile
    # **inférieur** d'ozone, où se mélangent creux nocturnes urbains et stations d'altitude.
    stations = pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "type_station", "lat_wgs84", "lon_wgs84", "altitude"],
    )

    jeu = jeu.merge(geo, on="station_id").merge(relief, on="station_id").merge(
        stations, on="station_id"
    )
    jeu = pd.concat([jeu, mos.variables_calendaires(jeu["timestamp_utc"])], axis=1)
    return neutraliser_infinis(jeu)


def neutraliser_infinis(jeu: pd.DataFrame, plafond: float = 30_000.0) -> pd.DataFrame:
    """Remplace l'infini **là où il a un sens**, et refuse de le faire ailleurs.

    Une quarantaine de scripts portent la ligne
    ``jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)``. Elle a été
    écrite pour une raison juste : une **distance** au plus proche objet vaut `inf` quand le
    rayon d'interrogation ne contient rien, et une valeur finie et interprétable vaut mieux
    qu'un infini que l'arbre rangerait dans une branche à part.

    Mais elle s'applique à **toutes** les colonnes admises. Le jour où une variable dérivée
    divise par zéro — un rapport d'échelles, un ratio pic/moyenne —, son infini deviendrait
    silencieusement `30 000`. Plausible pour une distance en mètres, absurde pour un
    rapport, et rien ne le dirait : c'est le même défaut que la sentinelle qui ment.

    ⚠️ **Aujourd'hui la sentinelle ne remplace rien** — vérifié le 22/08/2026 sur O₃ et
    PM2,5 : **zéro** valeur infinie sur les 53 colonnes admises, distances comprises. Ce
    n'est donc pas un défaut réalisé mais une mine dormante ; on la rend bruyante plutôt que
    de réécrire quarante appels qui ne changeraient aucun chiffre.
    """
    remplacees = {}
    for c in jeu.columns:
        v = jeu[c].to_numpy()
        if v.dtype.kind != "f":
            continue
        n = int(np.isinf(v).sum())
        if not n:
            continue
        if not c.endswith("_dist_min_m"):
            raise SystemExit(
                f"colonne « {c} » : {n:,} valeurs infinies, et ce n'est pas une distance. "
                f"La sentinelle {plafond:g} a un sens pour « aucun objet dans le rayon », "
                f"aucun pour un rapport ou une concentration — la remplacer en silence "
                f"produirait une valeur plausible et fausse. Traiter la cause.")
        jeu[c] = np.where(np.isinf(v), plafond, v)
        remplacees[c] = n
    if remplacees:
        print(f"distances infinies neutralisées à {plafond:g} m : "
              + ", ".join(f"{c} ({n:,})" for c, n in remplacees.items()), flush=True)
    return jeu


def colonnes_admises(jeu: pd.DataFrame) -> list[str]:
    """Variables disponibles **à l'heure de la prévision**, et elles seules.

    Les masses brutes (`_surface_m2`, `_longueur_m`) sont écartées : elles dépendent
    surtout du rayon d'interrogation, pas de la structure du paysage.
    """
    exclues = {"station_id", "timestamp_utc", "valeur", "type_station",
               "maille_lat", "maille_lon", "level"}
    return [
        c for c in jeu.columns
        if c not in exclues
        and not c.endswith(("_surface_m2", "_longueur_m"))
        and pd.api.types.is_numeric_dtype(jeu[c])
    ]


def main(polluant: str, horizon: int, n_plis: int) -> int:
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    # Les distances infinies signifient « aucun objet dans le rayon » : une valeur
    # finie et interprétable vaut mieux qu'un infini que l'arbre traiterait à part.
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)

    print(f"{polluant} {libelle_echeance(horizon)} · {len(jeu):,} paires · "
          f"{jeu['station_id'].nunique()} stations · {len(colonnes)} variables",
          flush=True)

    resultat = mos.ajuster_par_stations_exclues(
        jeu, colonnes, colonne_cams="cams", n_plis=n_plis
    )

    brut = cmp.metriques(resultat.predictions["observe"], resultat.predictions["cams"])
    corrige = cmp.metriques(resultat.predictions["observe"],
                            resultat.predictions["corrige"])

    print(f"\n{'':12s} {'RMSE':>7s} {'MAE':>7s} {'biais':>8s} {'R²':>8s}")
    for nom, m in [("CAMS brut", brut), ("MOS corrigé", corrige)]:
        print(f"{nom:12s} {m['rmse']:7.2f} {m['mae']:7.2f} "
              f"{m['biais']:+8.2f} {m['r2']:+8.3f}")
    gain = 100 * (1 - corrige["rmse"] / brut["rmse"])
    print(f"\n→ gain sur CAMS : {gain:+.1f} % de RMSE")

    # **Le RMSE global ne suffit pas à juger.** La distribution des concentrations est
    # fortement asymétrique : sur l'ozone, 83 % des points sont sous 80 µg/m³. Un
    # modèle qui traite bien le gros de la masse et écrase la queue affiche un RMSE
    # flatteur — alors qu'il est inutilisable pour une AASQA, dont le métier se joue
    # précisément dans la queue.
    print("\nPerformance par bande de concentration observée :")
    print(f"  {'bande':>16s} {'n':>9s} {'RMSE CAMS':>10s} {'RMSE MOS':>9s} {'':>6s}")
    for bas, haut in BANDES[polluant]:
        bande = resultat.predictions[
            resultat.predictions["observe"].between(bas, haut, inclusive="left")
        ]
        if bande.empty:
            continue
        a = cmp.metriques(bande["observe"], bande["cams"])["rmse"]
        b = cmp.metriques(bande["observe"], bande["corrige"])["rmse"]
        verdict = "mieux" if b < a else "PIRE"
        etiquette = f"{bas:.0f}-{haut:.0f}" if np.isfinite(haut) else f"≥{bas:.0f}"
        print(f"  {etiquette:>16s} {len(bande):>9,} {a:10.2f} {b:9.2f} {verdict:>6s}")

    seuil = SEUILS_INFORMATION.get(polluant)
    if seuil:
        reels = (resultat.predictions["observe"] >= seuil).sum()
        print(f"\nDétection du seuil d'information ({seuil:.0f} µg/m³) · "
              f"{reels} dépassement(s) réel(s) :")
        for nom, colonne in (("CAMS brut", "cams"), ("MOS corrigé", "corrige")):
            annonce = resultat.predictions[colonne] >= seuil
            reel = resultat.predictions["observe"] >= seuil
            print(f"  {nom:12s} détectés {int((annonce & reel).sum()):3d} · "
                  f"manqués {int((~annonce & reel).sum()):3d} · "
                  f"fausses alertes {int((annonce & ~reel).sum()):4d}")

    print("\nVariables les plus utilisées :")
    for _, ligne in resultat.importances.head(8).iterrows():
        print(f"  {ligne['variable']:28s} {100*ligne['importance']:5.1f} %")

    # Nom provisoire puis renommage (§ 4). Ces CSV pèsent 400 à 600 Mo : une écriture
    # interrompue — et sur cette machine un segfault tombe une fois sur deux — laissait
    # jusqu'ici un fichier TRONQUÉ portant le nom définitif, que toute reprise en aval
    # aurait compté comme complet.
    sortie = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    partiel = sortie.with_suffix(".csv.partiel")
    resultat.predictions.to_csv(partiel, index=False)
    partiel.replace(sortie)
    print(f"\nÉcrit : {sortie.name}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    # PM10 manquait ici — et NULLE PART ailleurs : `PANEL_PAR_POLLUANT`, `BANDES` et la table
    # des espèces le portent tous depuis le 01/08. Seul `choices` le refusait, si bien que la
    # démo Streamlit n'a jamais pu montrer que trois polluants sur les quatre du dossier.
    parseur.add_argument("--polluant", default="O3",
                         choices=["O3", "NO2", "PM25", "PM10"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    parseur.add_argument("--plis", type=int, default=5)
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
