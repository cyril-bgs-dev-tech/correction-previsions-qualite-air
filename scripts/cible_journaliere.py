#!/usr/bin/env python3
"""Vaut-il mieux apprendre le maximum journalier 8 h que corriger l'horaire puis agréger ?

L'enjeu
-------
Le projet corrige des concentrations **horaires**, puis toute grandeur réglementaire est
obtenue par agrégation. Or Bertrand et al. (2023, doi:10.5194/acp-23-5317-2023) mesurent
**20,5 %** de gain en agrégeant une correction horaire contre **32,8 %** en apprenant
directement la statistique journalière — douze points d'écart pour un simple changement de
cible. Si cela se reproduit ici, notre +19,4 % horaire mesure moins la qualité du modèle que
la maladresse de la cible.

Et c'est la bonne grandeur par ailleurs : le maximum journalier de la moyenne glissante 8 h
est celle de la valeur cible européenne pour l'ozone, celle du MQI de FAIRMODE et celle du
sous-indice ATMO.

**La comparaison n'a de sens que sur une grandeur commune.** On évalue donc les deux
approches sur le **même** maximum journalier 8 h, aux **mêmes** jours-station :

- *voie horaire* — le modèle horaire déjà ajusté, dont on agrège les prédictions ;
- *voie journalière* — un modèle entraîné directement sur le résidu du max 8 h.

Comparer un RMSE horaire à un RMSE journalier n'aurait rien prouvé : les grandeurs n'ont ni
la même variance ni la même distribution.

Note d'échelle : l'agrégation ramène 3,2 M de lignes horaires à ~130 000 jours-station. La
voie journalière apprend donc sur **25 fois moins d'exemples** — moins de données, mais aussi
moins de bruit. C'est précisément l'arbitrage que ce test mesure.

Usage : python3 scripts/cible_journaliere.py [--polluant O3] [--plis 3]
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
from aq.models import mos  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

COUVERTURE_MIN = 0.75

# **La grandeur journalière n'est pas la même selon le polluant**, et c'est celle du texte
# réglementaire qu'il faut viser : le maximum de la moyenne glissante 8 h pour l'ozone
# (valeur cible européenne, MQI FAIRMODE, sous-indice ATMO), le maximum horaire pour le NO₂
# et le SO₂, la moyenne journalière pour les particules. Appliquer le max 8 h partout
# mesurerait une grandeur que personne n'utilise.
GRANDEUR_PAR_POLLUANT = {"O3": "max_8h", "NO2": "max_horaire", "PM25": "moyenne_jour",
                         # PM10 : moyenne journalière, grain du seuil d'information
                         # français de 50 µg/m³ (arrêté du 07/04/2016).
                         "PM10": "moyenne_jour"}


def moyenne_glissante_8h(d: pd.DataFrame, colonne: str,
                         temps: str = "timestamp_utc",
                         cle: str = "station_id") -> pd.Series:
    """Moyenne glissante sur 8 **heures d'horloge**, station par station.

    🔴 Le défaut que cette fonction remplace — mesuré le 22/08/2026
    ---------------------------------------------------------------
    La version précédente faisait `serie.rolling(8, min_periods=6)` : une fenêtre de
    **8 LIGNES**, sur une série qui n'est pas réindexée sur une grille horaire continue.
    Dès qu'une heure manque, la « moyenne 8 h » s'étale sur plus de 8 heures ; dès qu'une
    ligne est en double, elle se resserre sur moins. Aucune exception ne lève, et la valeur
    reste plausible — mais ce n'est plus la grandeur du texte réglementaire, qui est définie
    sur **8 heures d'horloge** (valeur cible européenne de l'ozone, MQI FAIRMODE,
    sous-indice ATMO).

    Ce que ça coûtait, mesuré sur l'ozone du corpus, à filtre de couverture identique :

    * **7,96 % des jours-station** portaient une cible différente de la bonne ;
    * sur ces jours-là, écart absolu médian **2,17 µg/m³**, p99 15,3, max 46,2, et un biais
      moyen de **+1,99 µg/m³** — la version en lignes **surestime** le maximum ;
    * et la casse n'était pas diffuse : **98,6 % des jours de 2024-01 et 99,9 % de 2024-02**
      étaient touchés, parce que le panel y porte chaque observation en double (cf.
      `fit_mos.paires_cams_observations`). Sur ces deux mois, la fenêtre couvrait donc
      **4 heures réelles** et la « moyenne 8 h » était une moyenne 4 h.

    Sur une grille propre et continue, `rolling("8h")` rend **exactement** ce que rendait
    `rolling(8)` : le correctif ne déplace que ce qui était faux.

    `min_periods=6` conserve la règle des 75 % : six valeurs au moins dans la fenêtre.
    """
    try:
        r = (d.set_index(temps).groupby(cle)[colonne]
              .rolling("8h", min_periods=6).mean())
    except ValueError as e:
        # pandas refuse un groupe non monotone, et son message renvoie dans ses propres
        # entrailles. On le retraduit en consigne : le lecteur doit savoir QUOI faire.
        raise SystemExit(
            f"moyenne_glissante_8h : l'ordre du glissement ne suit pas la table — "
            f"trier par [{cle}, {temps}] avant d'appeler ({e})") from e
    # Le résultat sort dans l'ordre (clé, temps). Il coïncide avec celui de `d` **parce
    # que** `d` est trié ainsi — ce que l'on VÉRIFIE plutôt que de le supposer : un appelant
    # qui aurait oublié le tri obtiendrait sinon des valeurs décalées d'une station à
    # l'autre, plausibles et fausses.
    if len(r) != len(d) or not np.array_equal(
            r.index.get_level_values(-1).to_numpy(), d[temps].to_numpy()):
        raise SystemExit(
            f"moyenne_glissante_8h : l'ordre du glissement ne suit pas la table "
            f"({len(r)} valeurs pour {len(d)} lignes). Trier par [{cle}, {temps}] avant "
            f"d'appeler.")
    return pd.Series(r.to_numpy(), index=d.index)


def max_glissant_8h(serie: pd.Series) -> pd.Series:
    """⛔ Retirée le 22/08/2026 — elle comptait 8 LIGNES au lieu de 8 HEURES.

    Elle lève au lieu de disparaître : un appelant oublié doit **échouer**, pas retomber en
    silence sur la grandeur fausse. Voir `moyenne_glissante_8h` pour le remplaçant et pour
    ce que le défaut coûtait.
    """
    raise SystemExit(
        "max_glissant_8h est retirée : sa fenêtre comptait 8 lignes, pas 8 heures. "
        "Utiliser moyenne_glissante_8h(d, colonne, temps=…, cle=…), qui prend la table "
        "et non la série, parce qu'une fenêtre temporelle a besoin des horodatages.")


def _preparer(d: pd.DataFrame, colonne: str, grandeur: str,
              temps: str = "timestamp_utc", cle: str = "station_id") -> pd.Series:
    """Transformation horaire préalable à l'agrégation du jour."""
    if grandeur == "max_8h":
        return moyenne_glissante_8h(d, colonne, temps, cle)
    return d[colonne]


def profil_horaire(jeu: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """La FORME du profil horaire CAMS, que l'agrégation journalière détruit.

    `agreger_journalier` réduit les 24 valeurs horaires de CAMS à deux nombres — le max 8 h
    et la moyenne. Une journée plate à 60 et une journée qui monte à 110 l'après-midi
    peuvent avoir la même moyenne ; leur mécanisme n'est pas le même, et le biais de CAMS
    non plus.

    Quatre descripteurs, aucun n'exigeant d'observation : amplitude, dispersion intra-jour,
    **heure** du maximum, et rapport pic/moyenne.
    """
    d = jeu[["station_id", "timestamp_utc", "cams"]].copy()
    d["jour"] = d["timestamp_utc"].dt.floor("D")
    d["heure"] = d["timestamp_utc"].dt.hour
    g = d.groupby(["station_id", "jour"], sort=False)
    p = g.agg(prof_max=("cams", "max"), prof_min=("cams", "min"),
              prof_sigma=("cams", "std"), prof_moy=("cams", "mean"),
              prof_n=("cams", "count")).reset_index()
    idx = d.loc[g["cams"].idxmax()]
    p = p.merge(idx[["station_id", "jour", "heure"]].rename(
        columns={"heure": "prof_heure_max"}), on=["station_id", "jour"], how="left")
    p["prof_amplitude"] = p["prof_max"] - p["prof_min"]
    p["prof_pic_sur_moy"] = p["prof_max"] / p["prof_moy"].replace(0, np.nan)
    cols = ["prof_amplitude", "prof_sigma", "prof_heure_max", "prof_pic_sur_moy"]
    return p[["station_id", "jour"] + cols], cols


def _agregation(grandeur: str) -> str:
    return "mean" if grandeur == "moyenne_jour" else "max"


def agreger_journalier(jeu: pd.DataFrame, colonnes: list[str],
                       grandeur: str = "max_8h") -> pd.DataFrame:
    """Passe à un enregistrement par station-jour, en grandeur « max 8 h ».

    Les prédicteurs deviennent des **moyennes journalières** — un modèle journalier ne peut
    pas recevoir des variables horaires. Les variables statiques (paysage, relief, trafic)
    sont invariantes dans la journée : leur moyenne est leur valeur.
    """
    d = jeu.sort_values(["station_id", "timestamp_utc"]).copy()
    d["jour"] = d["timestamp_utc"].dt.floor("D")

    for source, cible in (("valeur", "obs_prep"), ("cams", "cams_prep")):
        d[cible] = _preparer(d, source, grandeur)
    agr = _agregation(grandeur)

    # `cams` figure **parmi les prédicteurs** : agréger sous ce nom entrerait en collision
    # avec la colonne d'ancrage `cams_max8h` et produirait deux colonnes homonymes. Les deux
    # grandeurs sont d'ailleurs distinctes et toutes deux utiles — le **maximum** 8 h est la
    # cible à corriger, la **moyenne** journalière décrit le niveau général de la journée.
    autres = [c for c in colonnes if c != "cams"]

    groupes = d.groupby(["station_id", "jour"], sort=False)
    journalier = groupes.agg(
        obs_jour=("obs_prep", agr),
        cams_jour=("cams_prep", agr),
        cams_moy_jour=("cams", "mean"),
        n_heures=("valeur", "count"),
        **{c: (c, "mean") for c in autres},
    ).reset_index()

    # § 2 quater — une condition de DISPONIBILITÉ qui ne se compte pas change le périmètre
    # en silence. Ce filtre-ci écarte 1,15 % des jours-station de l'ozone (mesuré le
    # 22/08/2026), jusqu'à 5,6 % sur un mois de bord, et rien ne l'imprimait.
    avant = len(journalier)
    journalier = journalier[journalier["n_heures"] >= 24 * COUVERTURE_MIN]
    sans_couverture = avant - len(journalier)
    journalier = journalier.dropna(subset=["obs_jour", "cams_jour"])
    sans_valeur = avant - sans_couverture - len(journalier)
    if sans_couverture or sans_valeur:
        print(f"  agrégation journalière · {len(journalier):,} jours-station retenus sur "
              f"{avant:,} — écartés : {sans_couverture:,} sous "
              f"{COUVERTURE_MIN:.0%} de couverture horaire"
              + (f", {sans_valeur:,} sans cible" if sans_valeur else ""), flush=True)
    return journalier


def voie_horaire(polluant: str, horizon: int, jours_valides: pd.DataFrame,
                 grandeur: str = "max_8h") -> dict:
    """Agrège les prédictions horaires **déjà validées hors station** en max 8 h.

    On réutilise les prédictions du modèle horaire existant : les réajuster ne changerait
    rien et coûterait dix minutes.
    """
    chemin = RACINE / f"reports/mos_{polluant}_J{horizon}.csv"
    p = pd.read_csv(chemin, parse_dates=["timestamp_utc"]).dropna(subset=["observe"])
    p = p.sort_values(["station_id", "timestamp_utc"])
    p["jour"] = p["timestamp_utc"].dt.floor("D")
    for source, cible in (("observe", "obs_prep"), ("corrige", "corr_prep")):
        p[cible] = _preparer(p, source, grandeur)
    agr = _agregation(grandeur)

    agrege = (p.groupby(["station_id", "jour"], sort=False)
               .agg(obs_jour=("obs_prep", agr), pred_jour=("corr_prep", agr))
               .reset_index())

    # Restreindre aux **mêmes** jours-station que la voie journalière : sans quoi les deux
    # RMSE porteraient sur des échantillons différents et ne seraient pas comparables.
    commun = agrege.merge(jours_valides[["station_id", "jour"]], on=["station_id", "jour"])
    return cmp.metriques(commun["obs_jour"], commun["pred_jour"]) | {"n_jours": len(commun)}


def main(polluant: str, horizon: int, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    journalier = agreger_journalier(jeu, colonnes, grandeur)
    print(f"{polluant} J+{horizon} · grandeur **{grandeur}** · {len(jeu):,} lignes horaires "
          f"→ {len(journalier):,} jours-station · "
          f"{journalier['station_id'].nunique()} stations", flush=True)

    base = cmp.metriques(journalier["obs_jour"], journalier["cams_jour"])
    print(f"\nCAMS brut, en {grandeur:13s} RMSE {base['rmse']:6.2f} · "
          f"R² {base['r2']:+.3f}", flush=True)

    # ── Voie journalière : apprendre directement le résidu de la grandeur du jour ──
    # Les prédicteurs sont ceux du modèle horaire, `cams` remplacé par ses deux agrégats.
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    # `jour` devient `timestamp_utc` : le module attend ce nom pour horodater ses sorties,
    # et l'horodatage d'un enregistrement journalier est bien le jour lui-même.
    entree = journalier.rename(columns={"obs_jour": "valeur", "jour": "timestamp_utc"})
    resultat = mos.ajuster_par_stations_exclues(
        entree, predicteurs, colonne_cams="cams_jour", n_plis=n_plis, verbeux=True,
    )
    p = resultat.predictions.dropna(subset=["observe"])
    m_direct = cmp.metriques(p["observe"], p["corrige"])
    gain_direct = 100 * (1 - m_direct["rmse"] / base["rmse"])

    # ── Voie horaire : agréger les prédictions horaires existantes ─────────────
    m_agrege = voie_horaire(polluant, horizon, journalier, grandeur)
    gain_agrege = 100 * (1 - m_agrege["rmse"] / base["rmse"])

    print(f"\n{'voie':34s} {'n jours':>9s} {'RMSE':>7s} {'R²':>8s} {'gain/CAMS':>10s}")
    print(f"{'horaire corrigée puis agrégée':34s} {m_agrege['n_jours']:9,} "
          f"{m_agrege['rmse']:7.2f} {m_agrege['r2']:+8.3f} {gain_agrege:+9.1f} %")
    print(f"{grandeur + ' appris directement':34s} {len(p):9,} "
          f"{m_direct['rmse']:7.2f} {m_direct['r2']:+8.3f} {gain_direct:+9.1f} %", flush=True)

    ecart = gain_direct - gain_agrege
    print(f"\nécart en faveur de la cible directe : {ecart:+.1f} point(s)")
    verdict = ("CONCLUANT — la cible était mal choisie" if ecart >= 3
               else "NON CONCLUANT — moins de 3 points, la cible horaire tient")
    print(f"verdict (seuil d'abandon fixé à 3 points) : {verdict}", flush=True)

    pd.DataFrame([
        {"voie": "horaire agrégée", "gain_pct": gain_agrege, **m_agrege},
        {"voie": "cible du jour, directe", "gain_pct": gain_direct, "n_jours": len(p), **m_direct},
        {"voie": "CAMS brut", "gain_pct": 0.0, "n_jours": len(journalier), **base},
    ]).to_csv(RACINE / f"reports/cible_journaliere_{polluant}.csv", index=False)
    print(f"\nÉcrit : reports/cible_journaliere_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
