"""Détection des signatures régionales dans un panneau de mesures.

Ces trois signatures ne sont pas des curiosités : chacune correspond à une **décision
que doit prendre une AASQA**.

- **Épisode importé** — l'article 20 de la directive 2008/50/CE autorise à déduire la
  contribution des **sources naturelles** (poussières sahariennes, embruns, feux) du
  décompte de conformité. Un tel épisode se reconnaît à ce qu'il est **synchrone et
  homogène** sur tout un territoire, là où une pollution locale reste contrastée d'une
  station à l'autre — et à ce que son aérosol est **grossier** plutôt que fin.

  ⚠️ Ce module **présélectionne**, il ne démontre pas. La déclaration relève de l'État,
  et le cadre probatoire (Commission, SEC(2011) 208) exige rétrotrajectoires ou imagerie
  satellitaire et, si possible, composition chimique crustale. Deux candidats de qualité
  pour compléter : les alertes de poussière du service CAMS, et les analyses du programme
  CARA du LCSQA.
- **Chauffage résidentiel au bois** — premier levier des plans de protection de
  l'atmosphère sur les particules. Sa signature est un **pic du soir présent en hiver et
  absent en été**, à la même heure : c'est ce qui le distingue du trafic, dont le cycle
  est bimodal et permanent.
- **Recirculation de brise de mer** — sur le littoral méditerranéen, la brise ramène en
  fin de journée des masses d'air enrichies en ozone. Le pic littoral est alors **plus
  précoce et plus élevé** que le pic continental, à l'inverse de ce que produirait la
  seule photochimie locale.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def episodes_importes(
    panneau: pd.DataFrame,
    quantile: float = 0.99,
    homogeneite_max: float = 0.35,
    n_stations_min: int = 6,
) -> pd.DataFrame:
    """Jours de forte concentration **homogène** sur le territoire.

    Deux conditions, et la seconde est celle qui discrimine :

    1. la moyenne territoriale dépasse le `quantile` demandé ;
    2. le **coefficient de variation entre stations** reste sous `homogeneite_max`.

    Une pollution locale — trafic, industrie, chauffage — produit des écarts marqués
    entre stations : quelques-unes s'envolent, les autres non. Un apport importé arrive
    par le haut de l'atmosphère et touche tout le monde à la fois. C'est cette
    **homogénéité**, et non le niveau seul, qui signe l'origine extérieure.

    Le seuil de niveau seul retiendrait aussi les inversions hivernales, qui sont
    intenses mais très contrastées spatialement.
    """
    jeu = panneau.copy()
    jeu["jour"] = jeu["timestamp_utc"].dt.tz_convert("Europe/Paris").dt.date

    par_station = (jeu.groupby(["jour", "station_id"], observed=True)["valeur"]
                   .mean().reset_index())
    par_jour = par_station.groupby("jour").agg(
        moyenne=("valeur", "mean"), ecart_type=("valeur", "std"),
        n_stations=("station_id", "nunique"),
    )
    par_jour = par_jour[par_jour["n_stations"] >= n_stations_min]
    if par_jour.empty:
        return par_jour.assign(coef_variation=[], importe=[])

    par_jour["coef_variation"] = par_jour["ecart_type"] / par_jour["moyenne"]
    seuil = par_jour["moyenne"].quantile(quantile)
    par_jour["importe"] = (
        (par_jour["moyenne"] >= seuil)
        & (par_jour["coef_variation"] < homogeneite_max)
    )
    return par_jour.reset_index()


# Rapport PM10/PM2.5 au-delà duquel l'aérosol est majoritairement **grossier**, donc
# d'origine mécanique — poussière minérale, embrun, remise en suspension. Mesuré sur
# 4 384 jours occitans : médiane 1,63, neuvième décile 2,16. Le seuil de 2,0 retient
# donc le décile supérieur, ce qui correspond aux épisodes sahariens documentés.
#
# ⚠️ **Ce seuil est empirique et propre à ce jeu de données, pas réglementaire.** La
# fraction grossière est un indice reconnu — le LCSQA observe bien un rapport PM2,5/PM10
# abaissé lors des brumes de sable — mais **aucun seuil universel français n'existe**.
# Le cadre probatoire de la Commission (SEC(2011) 208) exige davantage : station rurale
# de fond, cohérence spatio-temporelle, rétrotrajectoires ou imagerie satellitaire, et
# si possible **composition chimique crustale** (Al, Fe, Si, Ca, Mg, K, carbonates).
# Ce module fournit donc un **filtre de présélection**, pas une démonstration au sens de
# l'article 20 — et c'est l'État, non l'AASQA seule, qui porte la déclaration.
RAPPORT_GROSSIER = 2.0

# En deçà, l'aérosol est majoritairement fin : combustion (chauffage, trafic) ou
# aérosol secondaire formé sur place. Ces épisodes ne relèvent pas de l'article 20.
RAPPORT_FIN = 1.5


def classer_origine(pm10: float, pm25: float) -> str:
    """Origine probable d'un épisode de particules, d'après sa granulométrie.

    **C'est le critère qui manque à la seule synchronicité.** Un épisode peut être
    parfaitement homogène sur un territoire sans venir d'ailleurs : une inversion
    anticyclonique couvre toute une région et y piège les émissions locales. La
    synchronicité sépare *régional* de *local* ; elle ne sépare pas *importé* de
    *produit sur place*.

    La granulométrie, elle, tranche. Les poussières sahariennes sont des particules
    **minérales grossières** — le rapport PM10/PM2.5 y dépasse 2. La combustion, qu'il
    s'agisse de chauffage au bois ou de trafic, produit des particules **fines** :
    rapport voisin de 1,2.

    Mesuré sur l'Occitanie : l'épisode le plus intense de la série (2013-02-27,
    55,7 µg/m³) a un rapport de 1,19 — il n'est donc **pas** déductible au titre de
    l'article 20, alors que le seul critère de synchronicité l'aurait retenu.
    """
    if not np.isfinite(pm10) or not np.isfinite(pm25) or pm25 <= 0:
        return "indéterminé"
    rapport = pm10 / pm25
    if rapport >= RAPPORT_GROSSIER:
        return "minéral"
    if rapport <= RAPPORT_FIN:
        return "combustion"
    return "mixte"


def qualifier_episodes(
    episodes: pd.DataFrame, journalier_par_polluant: pd.DataFrame
) -> pd.DataFrame:
    """Ajoute le rapport PM10/PM2.5 et l'origine probable à des épisodes détectés.

    `journalier_par_polluant` porte une colonne par polluant, indexée par jour.
    """
    if episodes.empty:
        return episodes.assign(rapport_pm=[], origine=[])

    fusion = episodes.merge(journalier_par_polluant, on="jour", how="left")
    manquant = "PM10" not in fusion.columns or "PM25" not in fusion.columns
    if manquant:
        return fusion.assign(rapport_pm=np.nan, origine="indéterminé")

    fusion["rapport_pm"] = fusion["PM10"] / fusion["PM25"]
    fusion["origine"] = [
        classer_origine(a, b) for a, b in zip(fusion["PM10"], fusion["PM25"])
    ]
    return fusion


def profil_horaire(panneau: pd.DataFrame, mois: list[int]) -> pd.Series:
    """Concentration moyenne par heure **locale**, sur une sélection de mois.

    L'heure locale, et non UTC : les cycles d'émission suivent l'activité humaine, qui
    suit l'heure de la montre. Un profil calculé en UTC mélangerait 19 h d'hiver et 20 h
    d'été, effaçant précisément le pic qu'on cherche.
    """
    local = panneau["timestamp_utc"].dt.tz_convert("Europe/Paris")
    selection = panneau[local.dt.month.isin(mois)]
    return selection.groupby(local[local.dt.month.isin(mois)].dt.hour)["valeur"].mean()


def signature_chauffage_bois(panneau: pd.DataFrame) -> dict[str, float]:
    """Rapport pic du soir / creux de l'après-midi, en hiver puis en été.

    Le chauffage au bois se distingue du trafic par sa **saisonnalité** : un pic du soir
    marqué en hiver, quasi nul en été, alors que le trafic produit un cycle bimodal
    toute l'année. Comparer les deux saisons vaut mieux que regarder l'hiver seul.
    """
    resultat: dict[str, float] = {}
    for nom, mois in (("hiver", [12, 1, 2]), ("ete", [6, 7, 8])):
        profil = profil_horaire(panneau, mois)
        if profil.empty:
            continue
        soir = profil.loc[18:23]
        creux = profil.loc[13:16].min()
        resultat[f"{nom}_pic_soir"] = float(soir.max())
        resultat[f"{nom}_heure_pic"] = int(soir.idxmax())
        resultat[f"{nom}_creux_apres_midi"] = float(creux)
        resultat[f"{nom}_rapport"] = float(soir.max() / creux) if creux else np.nan

    if "hiver_rapport" in resultat and "ete_rapport" in resultat:
        # Le contraste entre saisons est le vrai indicateur : un rapport hivernal élevé
        # ne prouve rien s'il l'est autant en été.
        resultat["contraste_saisonnier"] = (
            resultat["hiver_rapport"] / resultat["ete_rapport"]
        )
    return resultat


def signature_brise_de_mer(
    panneau: pd.DataFrame, longitude_littoral: float = 3.0
) -> pd.DataFrame:
    """Compare le cycle diurne d'ozone entre littoral et intérieur, en été.

    Sous photochimie purement locale, l'ozone culmine plus tard et plus haut là où les
    précurseurs sont abondants — donc à l'intérieur, près des agglomérations. Observer
    l'inverse — un pic littoral **plus précoce et plus élevé** — signale un apport
    advecté : la brise ramène des masses d'air ayant vieilli au-dessus de la mer.
    """
    jeu = panneau.copy()
    jeu["zone"] = np.where(jeu["lon_wgs84"] > longitude_littoral,
                           "littoral", "interieur")
    lignes = []
    for zone, groupe in jeu.groupby("zone"):
        profil = profil_horaire(groupe, [6, 7, 8])
        if profil.empty:
            continue
        lignes.append({
            "zone": zone, "maximum": float(profil.max()),
            "heure_maximum": int(profil.idxmax()), "minimum": float(profil.min()),
            "amplitude": float(profil.max() - profil.min()),
            "n_stations": int(groupe["station_id"].nunique()),
        })
    return pd.DataFrame(lignes)
