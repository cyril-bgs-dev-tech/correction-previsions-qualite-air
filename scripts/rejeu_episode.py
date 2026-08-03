#!/usr/bin/env python3
"""Rejeu d'épisodes réels — ce que le modèle aurait dit, dix-neuf mois après son apprentissage.

Ce que ce script démontre, et ce qu'il ne démontre pas
-----------------------------------------------------
Le modèle est entraîné sur **août 2023 → décembre 2024**. On l'applique à **juillet 2026**,
sur des épisodes qu'ATMO Occitanie a réellement traités et publiés. C'est donc à la fois :

- une **preuve d'usage** — la seule qu'un candidat puisse produire sans accès au système de
  l'AASQA : à date fixée, entrée brute, correction, et ce qui aurait été recommandé ;
- une **épreuve de généralisation temporelle à dix-neuf mois**, bien plus dure que les plis
  mensuels, où l'écart au domaine d'apprentissage se compte en semaines.

Deux épisodes, choisis pour leur asymétrie :

| Date | Polluant | Ce que la chaîne officielle a fait |
|---|---|---|
| 08-09/07/2026 | O₃ | information puis **alerte** (30, 31, 34, 65) — épisode **anticipé** |
| 25/07/2026 | PM10 | **constaté *a posteriori*** (46, 12) — épisode **manqué** |

**Deux limites à énoncer avant tout résultat.**

1. *(levée le 03/08)* Le projet **modélise désormais les PM10**, depuis le flux LCSQA. Le
   25/07 est donc rejoué sur le polluant qui a réellement déclenché la procédure, et non
   plus sur les PM2,5 prises comme approximation.
2. Le modèle n'a **pas** tourné en direct ce jour-là. On montre ce qu'il aurait produit avec
   les entrées de l'époque, ce qui n'est pas la même chose qu'une prévision émise à temps.

**Une troisième limite a été retirée, et son histoire vaut la règle.** Ce fichier annonçait
« la météo reste ERA5, une réanalyse indisponible en temps réel ». C'était **faux** : les
prédicteurs viennent de `fit_mos.charger`, qui n'en charge aucune — 53 variables, toutes
disponibles à l'heure d'émission. Une jointure ERA5 traînait ici sans qu'aucune de ses
colonnes n'entre dans `colonnes_admises`.

Le coût de ce code mort n'était pas le temps de lecture : il **fabriquait l'objection la
plus grave qu'on puisse opposer à un travail de prévision** — utiliser une information que
la chaîne n'a pas au moment de prévoir — et la faisait publier par le projet lui-même.
Vérifier ce qu'un modèle consomme réellement vaut mieux que relire le commentaire qui le
dit.

Usage : python3 scripts/rejeu_episode.py [--polluant O3] [--horizon 1]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import ESPECES, TRANCHES, charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402
from scores_episodes import scores  # noqa: E402

MOIS_REJEU = "202607"
SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0, "PM10": 50.0}
EPISODES = {
    "O3": [("2026-07-08", "information"), ("2026-07-09", "ALERTE")],
    # ⚠️ Le 25/07 est un épisode **PM10**, et le projet les modélise depuis le flux LCSQA.
    # Il était rejoué sur les PM2,5 faute de mieux ; il ne l'est plus.
    "PM10": [("2026-07-25", "constaté a posteriori"), ("2026-07-26", "information/alerte"),
             ("2026-07-27", "information/alerte")],
    "PM25": [("2026-07-25", "constaté a posteriori"), ("2026-07-26", "information/alerte"),
             ("2026-07-27", "information/alerte")],
}


def charger_rejeu(polluant: str, horizon: int) -> pd.DataFrame:
    """Jeu de juillet 2026, apparié au **panel occitan** — le seul qui couvre cette date.

    Le panel métropolitain s'arrête au 31/12/2024 ; l'appariement standard le lit et
    rendrait donc une table vide, sans lever d'erreur.
    """
    court = next(c for c, (p, _) in ESPECES.items() if p == polluant)
    colonne = ESPECES[court][1]
    bas, haut = TRANCHES[horizon]

    chemin = (RACINE / "data/processed/meteo"
              / f"cams_prevision_metropole_{court}_{MOIS_REJEU}.parquet")
    if not chemin.exists():
        raise SystemExit(f"{chemin.name} absent — extraire d'abord juillet 2026")

    prev = pd.read_parquet(
        chemin, columns=["station_id", "timestamp_utc", "echeance_h", colonne])
    prev = prev[prev["echeance_h"].between(bas, haut)]
    debut, fin = prev["timestamp_utc"].min(), prev["timestamp_utc"].max()

    # ⚠️ Le panel occitan a longtemps été « le seul qui couvre cette date ». Ce n'est plus
    # vrai : le flux LCSQA a porté le corpus à 2026-07 sur les quatre polluants, ozone
    # compris. Lire l'ancien panel faisait échouer le rejeu d'ozone avec un message
    # affirmant que « le flux temps réel est rompu depuis le 01/07/2025 » — devenu faux, et
    # publié par le projet contre lui-même. On lit le panel unifié, et l'ancien en secours.
    sources = [RACINE / "data/processed/panel_unifie_lcsqa.parquet",
               RACINE / "data/processed/panel_occitanie_complet.parquet"]
    obs = None
    for src in sources:
        if not src.exists():
            continue
        t = pd.read_parquet(
            src,
            filters=[("timestamp_utc", ">=", debut), ("timestamp_utc", "<=", fin),
                     ("polluant", "==", polluant)],
            columns=["station_id", "timestamp_utc", "valeur"])
        if t["valeur"].notna().any():
            print(f"  observations lues dans {src.name}", flush=True)
            obs = t
            break
    if obs is None:
        raise SystemExit(f"{polluant} : aucune observation renseignée en {MOIS_REJEU} "
                         f"dans {[s.name for s in sources]}")
    jeu = prev.merge(obs, on=["station_id", "timestamp_utc"]).rename(
        columns={colonne: "cams"})
    renseignees = int(jeu["valeur"].notna().sum())
    print(f"  juillet 2026 · {len(prev):,} prévisions → {len(jeu):,} appariées "
          f"({renseignees:,} renseignées) · {jeu['station_id'].nunique()} stations "
          f"occitanes", flush=True)

    # **S'apparier n'est pas être renseigné.** Le panneau porte des lignes horaires dont la
    # valeur est nulle : la jointure réussit, l'effectif paraît bon, et le jeu est vide. Sans
    # ce contrôle, le script allait jusqu'à formater une date manquante et échouait sur un
    # `NaTType` — un message qui ne nomme pas la cause et envoie chercher le défaut ailleurs.
    if renseignees == 0:
        raise SystemExit(
            f"{polluant} : {len(jeu):,} lignes appariées en {MOIS_REJEU}, **aucune "
            f"renseignée** — alors que les sources ont été parcourues jusqu'à en trouver "
            f"une qui le soit.\nLa cause est donc dans l'appariement (station, horodatage, "
            f"fuseau), pas dans la disponibilité.")

    # Aucune météo : cf. l'en-tête. Les prédicteurs sortent de `colonnes_admises` sur le jeu
    # d'entraînement, qui n'en contient pas.
    geo = pd.read_parquet(RACINE / "data/processed/geo_features_metropole.parquet")
    relief = pd.read_parquet(RACINE / "data/processed/relief_features_metropole.parquet")
    trafic = pd.read_parquet(RACINE / "data/processed/trafic_population_metropole.parquet")
    stations = pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        # `altitude` doit figurer ici : `fit_mos.charger` la charge, donc elle est dans
        # `colonnes_admises`, donc le modèle l'attend. L'omettre cassait le rejeu depuis
        # qu'elle a été ajoutée à l'entraînement — un ajout de variable se propage à **tout**
        # ce qui applique le modèle, pas seulement à ce qui l'entraîne.
        columns=["station_id", "type_station", "lat_wgs84", "lon_wgs84", "altitude"])

    for table in (geo, relief, trafic, stations):
        jeu = jeu.merge(table, on="station_id", how="left")

    # Les variables calendaires sont **calculées**, pas jointes : `charger()` les ajoute en
    # fin de chaîne et les oublier ici laisserait le modèle sans sa famille la plus utile
    # (retirer le calendrier coûte 9,1 % de RMSE).
    from aq.models import mos as _mos

    return pd.concat([jeu, _mos.variables_calendaires(jeu["timestamp_utc"])], axis=1)


def main(polluant: str, horizon: int) -> int:
    depart = time.time()
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    seuil = SEUILS[polluant]

    # ── Apprentissage : les 17 mois, configuration retenue ─────────────────────
    print(f"{polluant} · apprentissage sur les 17 mois (août 2023 → décembre 2024)",
          flush=True)
    appris = charger(polluant, horizon)
    colonnes = colonnes_admises(appris)
    appris[colonnes] = appris[colonnes].replace([np.inf, -np.inf], 30_000.0)
    appris = appris.dropna(subset=["valeur"])
    j_appris = agreger_journalier(appris, colonnes, grandeur)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    # ⚠️ Ce commentaire affirmait « les deux tiennent en 0,3 point sur ce problème
    # (mesuré) ». **Aucune mesure de ce type n'existe dans le dépôt** — quatrième occurrence
    # de la même affirmation non sourcée, retirée le 02/08/2026. Le moteur est désormais
    # unique et le double aveugle montre que le choix, lui, porte bien le résultat.
    modele = modele_mos(graine=0)
    modele.fit(j_appris[predicteurs], j_appris["obs_jour"] - j_appris["cams_jour"])
    print(f"  {len(j_appris):,} jours-station appris · {len(predicteurs)} variables",
          flush=True)

    # ── Application : juillet 2026 ─────────────────────────────────────────────
    print(f"\n{polluant} · rejeu de juillet 2026", flush=True)
    rejeu = charger_rejeu(polluant, horizon)
    rejeu[colonnes] = rejeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    rejeu = rejeu.dropna(subset=["valeur"])

    j_rejeu = agreger_journalier(rejeu, colonnes, grandeur)

    # Le contrôle vient **après** l'agrégation : `cams_jour` et `cams_moy_jour` sont
    # produites par elle, et les chercher avant les déclarerait manquantes à tort. Un
    # modèle appliqué à un jeu dont il manque des colonnes échouerait de toute façon —
    # mais autant nommer lesquelles.
    manquantes = [c for c in predicteurs if c not in j_rejeu.columns]
    if manquantes:
        raise SystemExit(f"variables absentes du rejeu : {manquantes[:8]}")
    j_rejeu["corrige"] = np.clip(
        j_rejeu["cams_jour"] + modele.predict(j_rejeu[predicteurs]), 0, None)
    print(f"  {len(j_rejeu):,} jours-station · "
          f"{j_rejeu['jour'].min():%d/%m} → {j_rejeu['jour'].max():%d/%m}", flush=True)

    # ── Performance globale sur le mois rejoué ─────────────────────────────────
    m_cams = cmp.metriques(j_rejeu["obs_jour"], j_rejeu["cams_jour"])
    m_mos = cmp.metriques(j_rejeu["obs_jour"], j_rejeu["corrige"])
    gain = 100 * (1 - m_mos["rmse"] / m_cams["rmse"])
    print(f"\n  Sur tout juillet 2026 — dix-neuf mois après la fin de l'apprentissage :")
    print(f"    CAMS brut  RMSE {m_cams['rmse']:6.2f} · biais {m_cams['biais']:+6.2f}")
    print(f"    corrigé    RMSE {m_mos['rmse']:6.2f} · biais {m_mos['biais']:+6.2f} · "
          f"gain {gain:+.1f} %", flush=True)

    depasse = (j_rejeu["obs_jour"] >= seuil).to_numpy()
    if depasse.sum() >= 10:
        s_c = scores(depasse, (j_rejeu["cams_jour"] >= seuil).to_numpy())
        s_m = scores(depasse, (j_rejeu["corrige"] >= seuil).to_numpy())
        print(f"    dépassements {seuil:.0f} µg/m³ : {int(depasse.sum())} observés · "
              f"POD {s_c['POD']:.3f} → {s_m['POD']:.3f} · "
              f"FAR {s_c['FAR']:.3f} → {s_m['FAR']:.3f}", flush=True)

    # ── La timeline des épisodes ───────────────────────────────────────────────
    print(f"\n  {'jour':12s} {'n st.':>6s} {'obs max':>8s} {'CAMS':>8s} {'corrigé':>8s} "
          f"{'écart':>7s}  épisode publié")
    lignes = []
    for jour, g in j_rejeu.groupby(j_rejeu["jour"].dt.strftime("%Y-%m-%d")):
        etiquette = dict(EPISODES.get(polluant, [])).get(jour, "")
        marque = f"  ← {etiquette}" if etiquette else ""
        obs_max = g["obs_jour"].max()
        cams_max = g["cams_jour"].max()
        corr_max = g["corrige"].max()
        print(f"  {jour:12s} {len(g):6d} {obs_max:8.1f} {cams_max:8.1f} {corr_max:8.1f} "
              f"{corr_max - cams_max:+7.1f}{marque}", flush=True)
        lignes.append({"jour": jour, "n_stations": len(g), "obs_max": obs_max,
                       "cams_max": cams_max, "corrige_max": corr_max,
                       "episode_publie": etiquette})

    sortie = RACINE / f"reports/rejeu_episode_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)

    # **Sauver aussi le détail par station.** Le tableau ci-dessus ne porte que des maxima
    # journaliers, et un maximum agrège des **lieux** : le 26/07, `obs max` était à FR12095
    # et `CAMS max` à FR12053. Croiser ces deux valeurs a produit un récit faux — « CAMS
    # prévoyait 49,6 pour 46,8 observés » — alors qu'aucune station ne présentait ce couple.
    # Toute figure « un jour, trois barres » doit donc se lire dans ce fichier-ci.
    detail = j_rejeu[["station_id", "jour", "obs_jour", "cams_jour", "corrige"]].copy()
    detail["jour"] = detail["jour"].dt.strftime("%Y-%m-%d")
    detail["err_cams"] = (detail["cams_jour"] - detail["obs_jour"]).abs()
    detail["err_mos"] = (detail["corrige"] - detail["obs_jour"]).abs()
    detail["correction_utile"] = detail["err_mos"] < detail["err_cams"]
    chemin_detail = RACINE / f"reports/rejeu_stations_{polluant}.csv"
    detail.to_csv(chemin_detail, index=False)
    print(f"Écrit : {chemin_detail.relative_to(RACINE)} · {len(detail):,} lignes "
          f"station × jour · correction utile sur "
          f"{100 * detail['correction_utile'].mean():.1f} % d'entre elles")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    print("Rappel des limites : stations connues du modèle · le modèle n'a pas tourné en direct "
          "ce jour-là.\nToutes les entrées sont disponibles à l'heure d'émission : aucune "
          "réanalyse, aucune météo.", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
