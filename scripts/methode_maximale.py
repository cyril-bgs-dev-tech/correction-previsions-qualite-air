#!/usr/bin/env python3
"""La méthode la plus puissante que ce projet sache construire — et ce que chaque pièce y ajoute.

La question
-------------
Le projet a mesuré une trentaine de leviers, **un par un, chacun contre la base**. Cela ne dit
pas ce que vaut leur somme : des leviers qui captent la même information ne s'additionnent
pas. `leviers_36mois.py` a commencé le travail mais il lui manque les deux sources acquises
depuis — **GEOS-CF** et la météo prévue — et il empile ERA5, qui est une réanalyse.

Ce script mesure l'empilement **complet et cumulatif**, dans l'ordre déclaré ci-dessous, et
rapporte pour chaque étage son **apport marginal une fois les précédents en place**. C'est le
seul chiffre honnête : l'apport d'une famille seule contre la base surestime toujours.

Les deux périmètres, qui ne se confondent jamais
--------------------------------------------------
* **PARTOUT** — utilisable en tout point du territoire, y compris là où aucune station
  n'existe. C'est le périmètre de la spatialisation.
* **AUX STATIONS** — exige l'historique d'observations du point. C'est le périmètre de
  l'exploitation sur réseau existant. `veille` bascule d'un périmètre à l'autre, et le
  projet a déjà confondu les deux.

ERA5 figure en dernier et **hors méthode** : c'est une réanalyse, elle n'existe pas quand la
prévision est émise. Son gain est un **plafond**, jamais une performance.

Deux familles écartées, et pourquoi — écrit AVANT de mesurer
--------------------------------------------------------------
* **La météo prévue (IFS).** Onze mois disponibles sur les vingt-neuf du corpus. Mesuré le
  05/08 sur GEOS-CF : à neuf mois, le gain d'une même famille balaie **−0,02 % à +3,76 %**
  selon les mois retenus (σ 1,31 pt) alors qu'il vaut 0,20 pt de dispersion sur le corpus
  entier. **Un corpus court ne mesure pas un petit gain** — il en affiche un. L'inscrire ici
  produirait un chiffre non réfutable. À reprendre quand la couverture sera faite.
* **Les dérivées d'ensemble** (asymétrie, aplatissement) : réfutées à +0,05 à +0,40 %, sous
  la barre de bruit.

La fenêtre d'évaluation, et pourquoi elle n'est pas celle du corpus complet
----------------------------------------------------------------------------
GEOS-CF v1 couvre **2023-08 → 2025-12** ; le corpus apparié va jusqu'à 2026-07. Laisser les
mois de 2026 avec une colonne GEOS-CF vide donnerait au modèle un **indicateur d'année
déguisé** : « geoscf est absent » vaut exactement « nous sommes en 2026 ». En validation par
mois cachés, c'est une fuite.

L'évaluation est donc **restreinte à la fenêtre de v1**, identique pour toutes les
configurations. Les gains absolus ne sont pas comparables à ceux de `leviers_36mois.py`, qui
porte sur 36 mois — seuls les **écarts entre étages** le sont, et c'est ce qu'on cherche.

⚠️ v1 et v2 de GEOS-CF ne sont pas le même prédicteur (ozone : +15,41 µg/m³ d'écart moyen sur
le mois de recouvrement). Ne jamais empiler les deux dans une même colonne.

Usage  : python3 scripts/methode_maximale.py --polluant NO2
Sortie : reports/methode_maximale_<polluant>_h<n>.csv
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from apport_geoscf import charger_geoscf  # noqa: E402
from apport_fourier_profil import harmoniques  # noqa: E402
from apport_precurseurs import charger_lot  # noqa: E402
from cible_journaliere import profil_horaire  # noqa: E402
from aq.rapport import libelle_echeance  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from leviers_36mois import (  # noqa: E402
    _fusion, gain, joindre_feux, joindre_membres, joindre_veille,
    joindre_meteo,
)

# L'ordre est **déclaré avant la mesure**. Le réordonner après coup pour flatter un étage
# serait choisir la conclusion : l'apport marginal dépend de la place dans la pile.
#
# `tendance` entre le 08/08 en DERNIÈRE position des familles PARTOUT, et c'est délibéré :
# c'est la place la plus dure, celle où il doit ajouter quelque chose que la typologie, les
# membres, les feux et GEOS-CF n'ont pas déjà capté. Le placer en tête l'aurait flatté.
# Le banc de préprocessing le donne gagnant sur **trois polluants sur quatre** en double
# aveugle, à l'écran comme en confirmation — O₃ +3,49 pt, PM10 +1,42, PM2,5 +1,63 — et
# **perdant sur le NO₂** (−0,10 pt, non significatif ; −0,61 significatif à l'écran).
# L'exception a un mécanisme : le résidu du NO₂ est attaché au site, pas à la dynamique.
# ⚠️ `speciation` ajoutée le 17/08/2026, en DERNIER de l'ordre cumulatif — la place la plus
# dure : elle n'hérite que de ce que les cinq autres n'ont pas pris. Mesurée à part sur
# l'axe temporel, elle rend +5,4 à +12,1 % au-delà de la forme du total, IC95 excluant zéro.
# Ici on demande autre chose : ce qu'elle ajoute à une pile DÉJÀ complète, en double aveugle.
#
# ⚠️ Elle ne couvre que **2024-01 → 2026-08**. Comme GEOS-CF, elle restreint donc la fenêtre
# quand elle entre : le script le dit déjà pour geoscf, et `--ablation` reste la lecture
# honnête — l'ordre cumulatif attribue à un étage tardif ce qu'un étage précoce a pris.
# Au-delà de ce taux de manque sur un mois, la famille code l'époque plutôt que le
# phénomène. 0,5 sépare nettement les cas mesurés — 97 % et 100 % d'un côté, des
# trous épars de quelques pour cent de l'autre.
TAUX_MANQUE_MAX = 0.5

# ⚠️ `profil` ajoutée le 23/08/2026, en DERNIER — après la spéciation, donc à la place la
# plus dure : elle n'hérite que de ce que les six autres n'ont pas pris. Mesurée à part
# contre une base portant déjà `tendance`, la forme du profil horaire rend +0,70 à +1,21 %
# en écart apparié et TIENT sur les quatre polluants (p ≤ 0,011). Ici on demande autre
# chose : ce qu'elle ajoute à une pile DÉJÀ complète. Le gain mesuré ailleurs est un
# majorant, celui-ci est le chiffre publiable.
# ⚠️ `fourier` ajoutée le 23/08/2026, APRÈS `profil` — donc la place la plus dure de toutes :
# elle n'hérite que de ce que sept familles, forme du jour comprise, n'ont pas pris. Mesurée
# à part, la question posée était « remplace-t-elle les descripteurs à la main, ou s'y
# ajoute-t-elle ? » : remplacer ne TIENT pas (1 polluant sur 4), **ajouter TIENT sur 3/4**
# (NO₂ p<10⁻⁴, O₃ p=0,003, PM10 p=0,020). Les deux encodages portent des choses
# différentes — l'ampleur de l'excursion d'un côté, la phase et la structure harmonique de
# l'autre. D'où deux familles distinctes, et non huit colonnes dans une seule : c'est la
# seule forme qui permette à l'ablation de dire ce que chacune vaut.
# ⚠️ `precurseurs` ajoutée le 23/08/2026, en NEUVIÈME et dernière position. Quatre gaz que
# le dépôt n'avait jamais téléchargés — ammoniac, SO₂, PAN, COV non méthaniques — mesurés à
# part contre la pile à huit familles moins GEOS-CF, sur 32 plis : ils TIENNENT sur O₃
# (+1,34 pt, p=0,020), PM10 (+0,74, p=0,0005) et PM2,5 (+1,07, p<10⁻⁴), et **rien sur le
# NO₂** — qui est lui-même un précurseur, donc exempté par la chimie et non par la mesure.
# Ici on demande ce qu'ils ajoutent avec GEOS-CF PRÉSENT : c'est l'amplitude publiable.
# `ifs` est en DERNIÈRE position par construction : c'est un module au sens du contrat de
# produit, et sa confirmation se lit en dernière position sur le socle restreint à son
# propre support. Il n'entre que sur `--avec-ifs`.
ORDRE = ["typologie", "membres", "feux", "geoscf", "tendance", "speciation", "profil",
         "fourier", "precurseurs", "ifs", "chimie"]
PERIMETRE = {"typologie": "PARTOUT", "membres": "PARTOUT", "feux": "PARTOUT",
             "geoscf": "PARTOUT", "tendance": "PARTOUT", "speciation": "PARTOUT",
             "profil": "PARTOUT", "fourier": "PARTOUT", "precurseurs": "PARTOUT",
             "ifs": "PARTOUT", "chimie": "PARTOUT",
             "veille": "AUX STATIONS", "era5": "— (plafond)"}


def anomaliser(ref: pd.DataFrame, tr: pd.DataFrame, te: pd.DataFrame,
               cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remplace les colonnes de spéciation par leur écart à la climatologie station × mois.

    Pourquoi — mesuré le 17/08 par `mecanisme_speciation.py` : la valeur brute d'une
    composante mélange **le niveau habituel du lieu** et **l'écart du jour**, et seul le
    second porte l'information (la permutation conditionnelle efface 100 % du gain). Retirer
    le premier a rendu +1,12 pt sur O₃ et +0,63 pt sur PM2,5 sur l'axe temporel.

    🔴 D'où vient `ref`, et pourquoi ce n'est PAS le pli d'apprentissage
    --------------------------------------------------------------------
    Première version écrite ce jour-là : climatologie ajustée sur `tr`. **Elle est fausse
    ici**, et le défaut est invisible dans le résultat. Le protocole cache la station *et*
    le mois, donc **les stations de test sont absentes de `tr` par construction** : leur
    climatologie n'existe pas, la ligne replie sur la moyenne globale, et le modèle apprend
    sur des anomalies centrées puis prédit sur des valeurs brutes décalées d'une constante.
    Deux échelles de part et d'autre du modèle, sans qu'aucune assertion ne lève.

    `ref` est donc **toutes les stations, mois de test exclu**. C'est ce que la production
    peut faire : en un point non instrumenté l'archive CAMS existe — seul le futur n'existe
    pas. Aucune observation n'entre ici ; ce sont des champs prévus.

    Les couples (station, mois) absents de `ref` replient sur la station, puis sur sa
    moyenne. Un repli **conserve le périmètre**, là où écarter la ligne le détruirait
    (§ 2 quater).
    """
    m_ref = pd.to_datetime(ref["jour"]).dt.month
    m_tr = pd.to_datetime(tr["jour"]).dt.month
    m_te = pd.to_datetime(te["jour"]).dt.month
    par_sm = ref[cols].groupby([ref["station_id"], m_ref]).mean()
    par_s = ref[cols].groupby(ref["station_id"]).mean()
    glob = ref[cols].mean()

    def ecart(bloc: pd.DataFrame, mois: pd.Series, quoi: str) -> pd.DataFrame:
        r = par_sm.reindex(pd.MultiIndex.from_arrays([bloc["station_id"], mois])).to_numpy()
        sec = par_s.reindex(bloc["station_id"]).to_numpy()
        manque = np.isnan(r[:, 0])
        r[manque] = sec[manque]
        orphelin = np.isnan(r[:, 0])
        r[orphelin] = glob.to_numpy()
        # 🔴 Le contrôle qui aurait attrapé le défaut du 17/08 : si la quasi-totalité d'un
        # bloc replie sur la moyenne globale, ses « anomalies » sont la valeur brute décalée
        # d'une constante — et l'autre bloc, lui, est bien centré. Le modèle apprendrait et
        # prédirait alors sur deux échelles, sans qu'aucune exception ne lève.
        if orphelin.mean() > 0.5:
            raise SystemExit(
                f"anomaliser : {100 * orphelin.mean():.0f} % du bloc « {quoi} » replie sur la "
                f"moyenne globale — la référence ne couvre pas ces stations, les anomalies "
                f"seraient sur une autre échelle que l'autre bloc")
        out = bloc.copy()
        out[cols] = bloc[cols].to_numpy() - r
        return out

    return ecart(tr, m_tr, "apprentissage"), ecart(te, m_te, "test")


def epingler_fenetre(mois_ok: list[str], vises: list[str],
                     nom: str = "la référence") -> tuple[list[str], list[str]]:
    """Restreindre la fenêtre à celle d'une référence — jamais l'élargir.

    Le défaut que cela lève
    ------------------------
    Retirer une famille **lève sa restriction de support**. Sur le socle, la fenêtre est
    bornée par `precurseurs` (2023-08 absent à 54 %) ; retirer cette famille rend le mois, et
    la pile réduite tourne sur 34 mois quand sa référence en a 33. `ablation_jointe` refuse
    alors — l'écart mélangerait le retrait avec les mois en plus — et ce refus juste bloquait
    la mesure au lieu de la rendre possible.

    Pourquoi l'épinglage ne peut que RESTREINDRE
    ---------------------------------------------
    Un mois demandé mais absent de la couverture n'est pas un mois vide : c'est un mois **sans
    données**, et le réclamer produirait un pli sans lignes de test plutôt qu'une erreur. Le
    silence est le mode de panne que tout ce dépôt traque — donc on lève, en nommant les mois.

    Rend `(fenêtre retenue, mois retirés)`.
    """
    vus, cibles = set(mois_ok), set(vises)
    if manquants := sorted(m for m in vises if m not in vus):
        raise SystemExit(
            f"⛔ épinglage sur {nom} : {len(manquants)} mois de la référence sont ABSENTS de "
            f"cette pile ({manquants[0]} → {manquants[-1]}). Épingler ne peut que restreindre ; "
            f"réclamer un mois sans données rendrait un pli vide, pas une erreur.")
    retenus = [m for m in mois_ok if m in cibles]
    if not retenus:
        raise SystemExit(
            f"⛔ épinglage sur {nom} : la fenêtre retenue serait VIDE. Une référence sans mois "
            f"commun n'est pas une fenêtre étroite, c'est une erreur de cible — et une pile à "
            f"zéro pli s'écrirait sans rien lever.")
    retires = [m for m in mois_ok if m not in cibles]
    if retires:
        print(f"  fenêtre ÉPINGLÉE sur {nom} — {len(retires)} mois retiré(s) "
              f"({retires[0]} → {retires[-1]})", flush=True)
    else:
        print(f"  fenêtre déjà identique à {nom} — rien à épingler", flush=True)
    return retenus, retires


def joindre_module(d: pd.DataFrame, familles: dict, mois_ok: list[str],
                   lot: str) -> tuple[pd.DataFrame, list[str]]:
    """Un MODULE conditionnel, joint en dernière position — `ifs`, `chimie`.

    Un module n'entre pas dans le socle : sa couverture est plus courte que la fenêtre
    canonique. Son gain se mesure donc sur SON PROPRE SUPPORT, la fenêtre étant restreinte
    ici plutôt que ses colonnes écartées comme indicateurs d'époque — sans quoi la règle de
    couverture en deux passes le retirerait purement et simplement.

    ⚠️ Le placement de l'appel n'est pas libre : APRÈS que `mois_ok` existe, et AVANT
    l'échelle des configurations. Placé plus haut il lève `UnboundLocalError`, plus bas le
    module n'entre jamais dans la pile — les deux ont été faits.

    Moyennes seules : le criblage a montré que les maxima n'ajoutent rien de démontrable
    (`p_PC` 0,0435 contre 0,0003 sur l'IFS).
    """
    from apport_precurseurs import charger_lot as _cl  # noqa: PLC0415
    t, moyennes, _maxima = _cl(lot)
    t["jour"] = pd.to_datetime(t["jour"]).dt.tz_localize(None)
    avant = len(d)
    d = d.merge(t[["station_id", "jour"] + moyennes], on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure {lot} : {avant:,} → {len(d):,} lignes — la clé "
                         f"(station, jour) n'est pas unique dans le lot.")
    familles[lot] = moyennes
    # La fenêtre se restreint au support du module, et le retrait est COMPTÉ (§ 2 quater).
    mois_module = sorted(d.loc[d[moyennes[0]].notna(), "mois"].unique())
    hors = [m for m in mois_ok if m not in set(mois_module)]
    if hors:
        print(f"  module {lot} : fenêtre restreinte à son support — {len(hors)} mois "
              f"retiré(s) ({hors[0]} → {hors[-1]})", flush=True)
        mois_ok = [m for m in mois_ok if m in set(mois_module)]
        d = d[d["mois"].isin(mois_ok)].reset_index(drop=True)
    if not mois_ok:
        raise SystemExit(f"⛔ module {lot} : aucun mois commun avec la fenêtre. Un module "
                         f"sans support n'est pas un module vide, c'est une erreur.")
    print(f"  module {lot} : {len(moyennes)} colonnes · {mois_ok[0]} → {mois_ok[-1]} "
          f"({len(mois_ok)} mois)", flush=True)
    return d, mois_ok


def joindre_geoscf(d: pd.DataFrame, polluant: str) -> tuple[pd.DataFrame, list[str]]:
    """GEOS-CF **flux v1 uniquement** — le seul qui couvre une fenêtre mesurable."""
    g = charger_geoscf(GRANDEUR_PAR_POLLUANT[polluant], "v1")
    g["jour"] = pd.to_datetime(g["jour"]).dt.tz_localize(None)
    cols = [c for c in g.columns if c.startswith("geoscf_")]
    if not cols:
        raise SystemExit("aucune colonne GEOS-CF — le flux v1 est-il extrait ?")
    return _fusion(d, g, "geoscf"), cols


def trier_couverture(couv, familles: dict, seuil_mois: float = 0.8,
                     seuil_colonne: float = 0.01):
    """Sépare les colonnes d'ÉPOQUE des mois AMPUTÉS. Fonction pure, donc testable.

    `couv` : table mois × colonne des taux de présence (0 à 1).
    Rend `(colonnes_epoque, mois_amputes)`.

    🔴 L'ordre des deux passes décide, et une première version les confondait — voir le
    commentaire de l'appelant. Une colonne absente de mois ENTIERS est elle-même
    l'indicateur d'époque et doit sortir ; un mois où une colonne CONSERVÉE n'est qu'à
    moitié servie est un mois amputé et doit sortir. Juger les mois avant d'avoir retiré
    les colonnes d'époque fait supprimer seize mois pour en gagner huit.
    """
    cols = [c for cols in familles.values() for c in cols if c in couv.columns]
    epoque = [c for c in cols if (couv[c] < seuil_colonne).any()]
    restantes = [c for c in cols if c not in set(epoque)]
    if not restantes:
        return epoque, []
    amputes = sorted(m for m in couv.index if couv.loc[m, restantes].min() < seuil_mois)
    return epoque, amputes


def main(polluant: str, horizon: int, n_spa: int, ablation: bool = False,
         speciation: str = "brute", support_complet: bool = False,
         exclure: tuple[str, ...] = (), precurseurs: str = "completes",
         fenetre: str = "geoscf", avec_ifs: bool = False,
         avec_chimie: bool = False, mois_de: str = "",
         suffixe_extra: str = "") -> int:
    # Le garde à l'ENTRÉE, avant tout chargement : refuser après deux minutes de lecture
    # de parquets est un refus tardif, et le coût est payé pour rien.
    if fenetre == "complete" and "geoscf" not in exclure:
        raise SystemExit(
            "--fenetre complete exige --exclure geoscf : garder les colonnes GEOS-CF hors "
            "de leur couverture donne au modèle un indicateur d'année déguisé — « geoscf "
            "est absent » vaut exactement « nous sommes après 2025-12 ».")
    # 🔴 Les refus d'ARGUMENTS passent avant le premier parquet — 25/08/2026.
    # Posée près de son usage, la validation du suffixe ne levait qu'APRÈS le chargement :
    # quelques minutes de lecture payées pour une faute de frappe. Ce fichier porte déjà la
    # leçon vingt lignes plus haut — « un refus tardif, et le coût est payé pour rien ».
    if suffixe_extra and not re.fullmatch(r"_[A-Za-z0-9-]+", suffixe_extra):
        raise SystemExit(f"⛔ --suffixe-extra « {suffixe_extra} » : attendu « _mot-cle » "
                         f"(underscore, puis lettres, chiffres et tirets).")
    if mois_de:
        _r = Path(mois_de) if Path(mois_de).is_absolute() else RACINE / mois_de
        if not _r.exists():
            raise SystemExit(f"⛔ --mois-de : {_r} introuvable. On n'épingle pas sur une "
                             f"référence qui n'existe pas.")

    depart = time.time()
    jeu = charger(polluant, horizon)
    base_cols = colonnes_admises(jeu)
    jeu[base_cols] = jeu[base_cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    # La forme du profil horaire se lit sur les 24 valeurs de CAMS. `agreger_journalier`
    # les réduit à deux nombres : après lui, elle n'existe plus. Donc avant.
    prof, cols_prof = profil_horaire(jeu)
    fou, cols_fou = harmoniques(jeu)
    j = agreger_journalier(jeu, base_cols, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in base_cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    familles: dict[str, list[str]] = {}
    prof["jour"] = pd.to_datetime(prof["jour"]).dt.tz_localize(None)
    avant_prof = len(d)
    d = d.merge(prof, on=["station_id", "jour"], how="left")
    if len(d) != avant_prof:
        raise SystemExit(f"jointure du profil : {avant_prof:,} → {len(d):,} lignes — "
                         f"doublons de clé (station, jour)")
    familles["profil"] = cols_prof
    fou["jour"] = pd.to_datetime(fou["jour"]).dt.tz_localize(None)
    avant_fou = len(d)
    d = d.merge(fou, on=["station_id", "jour"], how="left")
    if len(d) != avant_fou:
        raise SystemExit(f"jointure des harmoniques : {avant_fou:,} → {len(d):,} lignes")
    familles["fourier"] = cols_fou

    pre, moy_pre, max_pre = charger_lot("precurseurs")
    avant_pre = len(d)
    d = d.merge(pre, on=["station_id", "jour"], how="left")
    if len(d) != avant_pre:
        raise SystemExit(f"jointure des précurseurs : {avant_pre:,} → {len(d):,} lignes")
    # 🔴 Quatre colonnes ou huit ? La question a une réponse mesurée — 23/08/2026.
    # Testé au double aveugle, « moyennes seules » (4) tient sur les DEUX axes ;
    # « moyennes ET maxima » (8) tombe sur l'axe complet dès qu'on juge à la permutation
    # exacte plutôt qu'au bootstrap saturé — p_PC 0,0288 → 0,1185. Les huit colonnes
    # restent le défaut pour ne pas changer la pile sans mesure ; `--precurseurs moyennes`
    # rend la variante parcimonieuse mesurable sur les mêmes plis.
    familles["precurseurs"] = moy_pre if precurseurs == "moyennes" else moy_pre + max_pre

    # ⚠️ La dynamique de CAMS se calcule **avant** toute restriction de fenêtre. Elle
    # décale la série d'un jour par station : la calculer après le filtrage sur la
    # couverture GEOS-CF ferait sauter le décalage par-dessus le bord de fenêtre, et la
    # veille du premier jour retenu viendrait du dernier jour d'une autre période.
    # Aucune observation n'entre ici — la prévision d'hier existe partout où celle
    # d'aujourd'hui existe, donc le périmètre PARTOUT est conservé.
    from banc_preprocessing import f_tendance_cams  # noqa: PLC0415
    tendance = f_tendance_cams(d)
    if collision := [c for c in tendance.columns if c in d.columns]:
        raise SystemExit(f"colonnes de tendance déjà présentes : {collision}")
    d = pd.concat([d, tendance], axis=1)
    familles["tendance"] = list(tendance.columns)

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    familles["typologie"] = list(cols_typo)

    d, familles["geoscf"] = joindre_geoscf(d, polluant)
    # ⚠️ La fenêtre se lit **dans les données**, jamais dans le nom des fichiers (règle 4 bis).
    couvert = d[familles["geoscf"][0]].notna()
    if not couvert.any():
        raise SystemExit("GEOS-CF ne couvre aucune ligne — jointure à vérifier")
    # 🔴 `--fenetre complete` échange GEOS-CF contre huit mois — ouvert le 23/08/2026.
    #
    # La restriction ci-dessous s'applique AVANT `--exclure` : retirer geoscf des colonnes
    # ne libère donc PAS la fenêtre, et c'est voulu — sinon deux piles comparées auraient
    # des fenêtres différentes, ce qui n'est plus une comparaison (l'erreur du 23/08 au
    # matin). Ouvrir la fenêtre est un geste distinct, qui doit être demandé.
    #
    # L'arbitrage qu'il rend mesurable : GEOS-CF v1 vaut +0,48 pt démontrés mais borne le
    # corpus à 29 mois, soit 9 blocs, où le plancher de `p_PC` vaut 0,0059. À 37 mois le
    # plan a 12 blocs et ce plancher tombe à 0,0007 — et trois familles échouent
    # aujourd'hui par PUISSANCE, pas par absence d'effet.
    if fenetre == "complete":
        mois_ok = sorted(d["mois"].unique())
        print(f"\n  fenêtre COMPLÈTE demandée : {mois_ok[0]} → {mois_ok[-1]} "
              f"({len(mois_ok)} mois) au lieu de la couverture GEOS-CF", flush=True)
    else:
        mois_ok = sorted(d.loc[couvert, "mois"].unique())
    avant = len(d)
    d = d[d["mois"].isin(mois_ok)].reset_index(drop=True)
    # 🔴 L'étiquette doit nommer ce qui a DÉCIDÉ, pas une identité supposée (§ 0-H). Sous
    # `--fenetre complete`, ce message annonçait « couverture GEOS-CF v1 » pour une fenêtre
    # dont GEOS-CF n'était plus la cause — le nom aurait survécu au changement, pas ce
    # qu'il affirme.
    origine = ("couverture GEOS-CF v1" if fenetre == "geoscf"
               else "corpus apparié complet (--fenetre complete)")
    print(f"\n  fenêtre d'évaluation = {origine} : {mois_ok[0]} → {mois_ok[-1]}"
          f" ({len(mois_ok)} mois) · {len(d):,} jours-station sur {avant:,}", flush=True)

    debut, fin = mois_ok[0].replace("-", ""), mois_ok[-1].replace("-", "")
    from ablation_speciation import charger_speciation  # noqa: PLC0415

    spe = charger_speciation()
    cols_spe = [c for c in spe.columns if c.startswith("spe_")]

    # ═══ SUPPORT COMMUN — le défaut que la revue externe a trouvé le 17/08 ═══════════
    #
    # 🔴 Joindre la spéciation en `how="left"` préserve le corpus, et c'est exactement le
    # problème. Sur les mois antérieurs à 2024-01 la spéciation N'EXISTE PAS : les 16
    # colonnes y sont entièrement NaN, LightGBM apprend une direction par défaut pour les
    # NaN, et « tout est absent » devient un **indicateur d'année parfaitement apprenable**.
    # Le protocole cachant les mois, c'est une fuite.
    #
    # Mesuré : sur les 5 plis de 2023 où la variable n'existe pas, l'ajout du bloc produit
    # tout de même +2,64 pt de différence moyenne sur PM2,5 (−3,40 à +5,86). Le modèle
    # exploite donc le motif d'absence.
    #
    # ⚠️ C'est le défaut que la docstring de ce fichier documente déjà pour GEOS-CF —
    # « geoscf est absent » vaut « nous sommes en 2026 » — et qui lui a valu sa restriction
    # de fenêtre. Il a été réintroduit par une autre porte.
    #
    # Le nitrate est écarté pour la même raison : il n'existe qu'à partir de 2024-12, donc
    # sa seule absence date le mois à l'intérieur même de la fenêtre commune.
    if speciation == "core7":
        # 🔴 Le test portait sur la sous-chaîne « no3 », donc sur UNE tardive nommée à la
        # main. Depuis le 23/08 la matière organique en est une aussi — absente de
        # 2023-08, 09 et 10 — et `core7` la gardait, laissant trois mois datables au
        # milieu d'une pile censée être propre. On écarte par la LISTE, qui a une seule
        # source de vérité.
        from extraire_speciation import TARDIVES as _TARDIVES  # noqa: PLC0415
        nitrate = [c for c in cols_spe if any(t in c for t in _TARDIVES)]
        cols_spe = [c for c in cols_spe if c not in nitrate]
        spe = spe.drop(columns=nitrate)
        mois_spe = set(pd.to_datetime(spe["jour"]).dt.strftime("%Y-%m"))
        avant_sc = sorted(set(d["mois"]))
        d = d[d["mois"].isin(mois_spe)].reset_index(drop=True)
        garde = sorted(set(d["mois"]))
        print(f"  SUPPORT COMMUN : {len(cols_spe)} colonnes (tardives écartées : "
              f"{len(nitrate)} — {', '.join(nitrate)}) · fenêtre {len(avant_sc)} → "
              f"{len(garde)} mois "
              f"({garde[0]} → {garde[-1]})", flush=True)
    if speciation == "anomalie":
        print(f"  spéciation en ANOMALIE : les {len(cols_spe)} colonnes seront remplacées, "
              f"pli par pli, par leur écart à la climatologie station × mois-calendaire "
              f"ajustée sur le SEUL pli d'apprentissage", flush=True)
    avant_spe = len(d)
    d = d.merge(spe, on=["station_id", "jour"], how="left")
    if len(d) != avant_spe:
        raise SystemExit(f"la spéciation a changé le compte de lignes "
                         f"({avant_spe} → {len(d)}) — doublons de clé")
    familles["speciation"] = cols_spe
    if speciation == "core7":
        # Il reste des trous à l'intérieur même de la fenêtre commune : la spéciation
        # commence le 2024-01-02, donc le 1er janvier n'en a pas. On retire ces lignes —
        # pour LES DEUX configurations à l'identique, puisque le filtre précède la
        # construction des plis. Le repli est COMPTÉ (§ 2 quater), jamais silencieux.
        trous = d[cols_spe].isna().any(axis=1)
        if trous.any():
            jours = sorted(d.loc[trous, "jour"].dt.strftime("%Y-%m-%d").unique())
            print(f"  support commun : {int(trous.sum()):,} lignes retirées "
                  f"({100 * trous.mean():.2f} %) sur {len(jours)} jour(s) — "
                  f"{', '.join(jours[:4])}{' …' if len(jours) > 4 else ''}", flush=True)
            d = d[~trous].reset_index(drop=True)
        # Seuil fixé avant lecture : zéro valeur manquante, sinon le score n'est pas
        # publiable. Un support « commun » qui ne l'est pas rendrait le lot inutile.
        manquants = int(d[cols_spe].isna().sum().sum())
        if manquants:
            raise SystemExit(f"support commun VIOLÉ après nettoyage : {manquants:,} "
                             f"valeurs manquantes. Le score n'est pas publiable.")
        print(f"  ✅ support commun vérifié : 0 valeur manquante sur "
              f"{len(d):,} lignes × {len(cols_spe)} colonnes", flush=True)

    d, familles["membres"] = joindre_membres(d, polluant, debut, fin)
    d, familles["feux"] = joindre_feux(d, debut, fin)
    d, familles["veille"] = joindre_veille(d)
    d, familles["era5"] = joindre_meteo(d, debut, fin)
    for nom in list(familles):
        familles[nom] = [c for c in familles[nom] if c in d.columns]
        if not familles[nom]:
            print(f"  ⚠️ famille « {nom} » vide après jointure — écartée de la pile")
            del familles[nom]

    # ═══ UN MOIS ENTIÈREMENT ABSENT EST UN CODE D'ÉPOQUE ═══════════════════════════
    #
    # 🔴 La règle générale que trois défauts successifs ont fini par dessiner. Quand TOUTES
    # les colonnes d'une famille sont manquantes sur un mois entier, « cette famille est
    # absente » vaut exactement « nous sommes en ce mois-là ». LightGBM apprend une direction
    # par défaut pour les NaN, donc il apprend la date — et le protocole cache justement les
    # mois. Ce n'est pas une donnée incomplète, c'est une FUITE.
    #
    # Les trois occurrences, dans l'ordre où elles ont été trouvées :
    #   1. GEOS-CF — vue dès la conception, traitée en restreignant la fenêtre (docstring) ;
    #   2. la spéciation — réintroduite le 17/08 par une jointure `how="left"` qui préservait
    #      le corpus, et repérée par une revue externe : sur les plis de 2023 où la variable
    #      n'existe pas, le modèle produisait quand même +2,64 pt de différence sur PM2,5 ;
    #   3. les membres et les feux — trouvés en cherchant la cause d'une anomalie sur l'ozone.
    #      Membres PM10 : 12 mois sur 24. Membres NO₂/O₃ : juillet 2025 absent, et sur ce
    #      seul pli l'étage « + membres » rend **−126 %** de gain.
    #
    # Le contrôle ne liste plus les familles fautives : il MESURE la couverture de chacune.
    # ⚠️ Le garde mesure par polluant, donc il peut écarter une famille chez trois d'entre
    # eux et la garder chez le quatrième — les membres sont troués sur NO₂, O₃ et PM10 mais
    # complets sur PM2,5. On obtiendrait alors QUATRE piles principales différentes, ce qui
    # rend le tableau final non comparable d'une colonne à l'autre. `--exclure` porte donc
    # l'union des familles trouées, décidée une fois pour les quatre.
    if exclure:
        for nom in exclure:
            if nom in familles:
                del familles[nom]
                print(f"  famille « {nom} » exclue par --exclure (pile commune aux quatre "
                      f"polluants)", flush=True)

    mois_corpus = sorted(d["mois"].unique())
    troues: dict[str, list[str]] = {}
    for nom, cols in list(familles.items()):
        if nom in ("veille", "era5"):        # hors pile PARTOUT — jugées ailleurs
            continue
        # ⚠️ Le critère est un TAUX, pas la totalité — et il a fallu deux versions fausses
        # pour l'apprendre. « Toutes les colonnes absentes » laissait passer les membres
        # NO₂/O₃ de juillet 2025 ; « une colonne entièrement absente » aussi. La cause :
        # le fichier mensuel de juin **déborde d'un jour** sur juillet, donc le mois porte
        # 1 jour sur 31 et n'est jamais « entièrement » vide. Il est pourtant manquant à
        # 97 %, et c'est exactement le pli où l'étage « + membres » rend **−126 %** de gain.
        vides = [m for m, bloc in d.groupby("mois")[cols]
                 if float(bloc.isna().mean(axis=0).max()) > TAUX_MANQUE_MAX]
        if vides:
            troues[nom] = vides
    if troues:
        print(f"\n  🔴 {len(troues)} famille(s) avec au moins un MOIS entièrement absent — "
              f"« absente » y vaut « nous sommes en ce mois-là » :", flush=True)
        for nom, vides in troues.items():
            taux = {m: float(bloc.isna().mean(axis=0).max())
                    for m, bloc in d.groupby("mois")[familles[nom]] if m in vides}
            print(f"     {nom:12s} {len(mois_corpus) - len(vides)}/{len(mois_corpus)} mois · "
                  f"troués : " + ", ".join(f"{m} ({100*taux[m]:.0f} %)" for m in vides[:4])
                  + (" …" if len(vides) > 4 else ""),
                  flush=True)
        if support_complet:
            for nom in troues:
                del familles[nom]
            print(f"  → écartées de la pile (--support-complet) : {', '.join(troues)}",
                  flush=True)
        else:
            print("  ⚠️ CONSERVÉES : la mesure porte un indicateur d'époque implicite. "
                  "Utiliser --support-complet pour une pile auditable.", flush=True)
    else:
        print(f"  ✅ aucune famille n'a de mois entièrement absent "
              f"({len(mois_corpus)} mois)", flush=True)

    # ── Le module MÉTÉO PRÉVUE, sur demande — 24/08/2026 ────────────────────────────
    #
    # L'IFS a tenu au criblage sur les quatre polluants : +0,86 à +1,66 pt appariés,
    # p_PC = 0,0003. Mais ce criblage portait sur la pile à huit familles ; la confirmation
    # se fait ici, en DERNIÈRE position, sur le socle.
    #
    # ⚠️ Il ne peut PAS entrer dans le socle : sa couverture commence en 2024-03 quand la
    # fenêtre canonique commence en 2023-09. C'est un MODULE — son gain se mesure sur son
    # propre support, et la fenêtre est restreinte ici plutôt que ses colonnes écartées
    # comme indicateur d'époque. Sans cette restriction, la règle de couverture en deux
    # passes le retirerait purement et simplement.
    #
    # Huit champs de surface, MOYENNES seules : le criblage a montré que les maxima
    # n'ajoutent rien de démontrable (p_PC 0,0435 contre 0,0003).
    for lot, actif in (("ifs", avec_ifs), ("chimie", avec_chimie)):
        if actif:
            d, mois_ok = joindre_module(d, familles, mois_ok, lot)

    # ── Épingler la fenêtre sur celle d'une RÉFÉRENCE — 25/08/2026 ───────────────────
    #
    # Le défaut que cela lève : retirer une famille **lève sa restriction de support**. Sur
    # le socle, la fenêtre est bornée par `precurseurs` (2023-08 absent à 54 %) ; retirer
    # cette famille rend le mois, et la pile réduite tourne alors sur 34 mois quand sa
    # référence en a 33. `ablation_jointe` refuse à raison — l'écart mélangerait le retrait
    # avec les mois en plus — mais le refus bloque la mesure au lieu de la rendre possible.
    #
    # Épingler ne peut que RESTREINDRE : on prend l'intersection, jamais l'union. Un mois
    # demandé mais absent de la couverture serait un mois sans données, et le réclamer
    # produirait un pli vide plutôt qu'une erreur — d'où le refus explicite ci-dessous.
    if mois_de:
        ref = Path(mois_de) if Path(mois_de).is_absolute() else RACINE / mois_de
        if not ref.exists():
            raise SystemExit(f"⛔ --mois-de : {ref} introuvable. On n'épingle pas sur une "
                             f"référence qui n'existe pas.")
        vises = sorted(pd.read_csv(ref)["mois"].astype(str).unique())
        mois_ok, retires = epingler_fenetre(mois_ok, vises, ref.name)
        if retires:
            d = d[d["mois"].isin(mois_ok)].reset_index(drop=True)

    # ── Les configurations, cumulatives et déclarées ─────────────────────────────────
    configs: list[tuple[str, list[str], str]] = [("base (CAMS, terrain, calendrier)",
                                                  list(base), "PARTOUT")]
    cumul = list(base)
    for nom in ORDRE:
        if nom not in familles:
            continue
        cumul = cumul + familles[nom]
        configs.append((f"+ {nom}", list(cumul), PERIMETRE[nom]))
    partout = list(cumul)
    configs.append(("★ MAXIMALE — PARTOUT", list(partout), "PARTOUT"))

    # ── Ablation : ce que chaque famille apporte VRAIMENT, à la fin ──────────────────
    #
    # Les configurations cumulatives ci-dessus mesurent un apport *sachant les
    # précédents*, dans un ordre fixé une fois pour toutes. C'est une mesure honnête mais
    # elle ne répond pas à la question « faut-il garder cette famille pour CE polluant ? » :
    # un étage arrivé tôt s'attribue ce qu'un étage plus tardif aurait apporté seul, et un
    # étage arrivé dernier hérite de la place la plus dure. L'ablation retire une famille
    # de la pile COMPLÈTE et laisse toutes les autres en place — c'est la seule lecture qui
    # ne dépende pas de l'ordre.
    #
    # ⚠️ C'est une MESURE, pas une sélection. Élaguer ensuite les familles dont l'ablation
    # ne coûte rien, puis publier le score de la pile élaguée sur ces mêmes plis, serait le
    # biais de criblage que ce dépôt a mesuré à ×2 à ×4
    # ([[balayage-des-variables-inexploitees]]). Le score d'une pile choisie ici se
    # re-mesure sur des plis qui n'ont pas servi à la choisir, ou se publie en déclarant
    # qu'il est dans l'échantillon.
    if ablation:
        for nom in ORDRE:
            if nom not in familles:
                continue
            sans = [c for c in partout if c not in set(familles[nom])]
            if len(sans) == len(partout):
                raise SystemExit(f"ablation de {nom} : aucune colonne retirée — "
                                 f"les familles ne partitionnent pas la pile")
            configs.append((f"− {nom} (ablation)", sans, "PARTOUT"))
    if "veille" in familles:
        configs.append(("★ MAXIMALE — AUX STATIONS (+ veille)",
                        partout + familles["veille"], "AUX STATIONS"))
    if "era5" in familles:
        configs.append(("plafond ERA5 (NON déployable)",
                        partout + familles.get("veille", []) + familles["era5"],
                        "— (plafond)"))

    # 🔴 La fenêtre annoncée doit être celle qui a SERVI. `mois_ok` est calculé avant les
    # restrictions de support (core7, familles trouées) : le laisser tel quel faisait
    # annoncer « 2023-08→2025-12 · 29 mois » à des rapports portant 24 plis de 2024-01 à
    # 2025-12. Le « 5 écartés » était exact, la fenêtre mentait — et une revue externe l'a
    # relevé. On recalcule depuis les données effectivement retenues.
    # 🔴 Sous `--fenetre complete`, un mois PARTIELLEMENT couvert est écarté — 23/08/2026.
    #
    # La restriction GEOS-CF masquait le problème en bornant à sa propre fenêtre. Sans
    # elle, le corpus reprend des mois où une famille n'est présente qu'à moitié :
    #
    #     2023-08 : CAMS de base 31 jours · précurseurs 14 · chimie 13
    #
    # Le service a livré la moitié du mois sans le dire, et `OK 89 Mo` s'est lu comme un
    # succès. C'est le même défaut qu'un mois entièrement absent, en version partielle :
    # « les précurseurs sont vides » vaut « nous sommes après le 14 août 2023 ». Un mois
    # entier lève un garde ; une demi-couverture ne levait rien.
    #
    # Le seuil ne coûte rien ici : 2023-09 → 2026-08 fait 36 mois, soit 12 blocs de trois
    # — exactement autant que 37, dont le reliquat serait jeté de toute façon.

    if fenetre == "complete":
        # 🔴 Deux passes, et l'ORDRE décide — corrigé le 23/08/2026, avant tout lancement.
        #
        # La première version prenait le minimum de couverture sur TOUTES les colonnes de
        # famille et écartait le mois s'il tombait sous 80 %. Elle aurait vidé le corpus :
        # `pm2p5_no3_conc` est absent avant 2024-12, donc son minimum vaut zéro sur trente
        # mois, et la règle censée GAGNER des mois en aurait supprimé seize. Un garde-fou
        # qui détruit ce qu'il protège est pire que pas de garde-fou.
        #
        # La bonne lecture distingue deux objets. Une COLONNE absente de mois entiers est
        # elle-même l'indicateur d'époque : elle sort de la pile, et le mois reste. Un MOIS
        # où une colonne conservée n'est qu'à moitié servie est un mois amputé : il sort, et
        # la colonne reste. Traiter les deux par le même seuil confond la cause et l'effet.
        toutes_cols = [c for cols in familles.values() for c in cols if c in d.columns]
        couv = d.groupby("mois")[toutes_cols].apply(lambda b: b.notna().mean())

        epoque, maigres = trier_couverture(couv, familles)
        if epoque:
            # 🔴 Toutes nommées, jamais tronquées. Le premier essai en affichait huit sur
            # trente et deux familles disparaissaient sans qu'on sache lesquelles : un
            # retrait qu'on ne peut pas énumérer ne peut pas être contesté.
            par_famille: dict[str, list[str]] = {}
            for nom, cols in familles.items():
                pris = [c for c in cols if c in set(epoque)]
                if pris:
                    par_famille[nom] = pris
            print(f"  {len(epoque)} colonne(s) retirée(s) — absentes de mois ENTIERS, donc "
                  f"indicateurs d'époque :", flush=True)
            for nom, cols in par_famille.items():
                print(f"    {nom:12s} {len(cols):2d} : {', '.join(cols)}", flush=True)
            garde = set(epoque)
            for nom in list(familles):
                familles[nom] = [c for c in familles[nom] if c not in garde]
                if not familles[nom]:
                    del familles[nom]
                    print(f"    famille « {nom} » vidée par ce retrait", flush=True)
            toutes_cols = [c for c in toutes_cols if c not in garde]

        if toutes_cols:
            if maigres:
                print(f"  mois écartés — une colonne CONSERVÉE y est partielle : "
                      + ", ".join(f"{m} ({100 * couv.loc[m, toutes_cols].min():.0f} %)"
                                  for m in maigres), flush=True)
                mois_ok = [m for m in mois_ok if m not in set(maigres)]
                d = d[d["mois"].isin(mois_ok)].reset_index(drop=True)

    avant_fenetre = len(mois_ok)
    mois_ok = [m for m in mois_ok if m in set(d["mois"])]
    if len(mois_ok) != avant_fenetre:
        print(f"  fenêtre recalculée après restriction de support : {avant_fenetre} → "
              f"{len(mois_ok)} mois ({mois_ok[0]} → {mois_ok[-1]})", flush=True)

    # 🔴 L'EMPREINTE DES ENTRÉES — 24/08/2026, après une comparaison entre deux corpus.
    #
    # Deux exécutions peuvent porter la même fenêtre, le même nombre de mois, le même
    # nombre de colonnes ET le même `n_test` par pli, tout en reposant sur des données
    # différentes : la spéciation se joint en `left`, donc la compléter ne change pas le
    # nombre de lignes du modèle, seulement leurs VALEURS. Aucune statistique de résumé
    # déjà écrite ne le voyait, et une comparaison appariée a été rendue ce soir entre une
    # référence de 21 h 59 et une variante de 16 h 23, sans un mot.
    #
    # L'empreinte compte les cellules RENSEIGNÉES par famille : c'est exactement ce qu'un
    # remplissage déplace, et cela reste stable au bruit d'exécution puisque aucune valeur
    # n'y entre.
    import hashlib  # noqa: PLC0415
    corps = "|".join(
        f"{nom}:{len(cols)}:{int(d[cols].notna().to_numpy().sum())}"
        for nom, cols in sorted(familles.items()) if all(c in d.columns for c in cols))
    empreinte = hashlib.sha256(f"{len(d)}|{corps}".encode()).hexdigest()[:12]
    print(f"  empreinte des entrées : {empreinte} · {len(d):,} lignes · "
          f"{len(familles)} familles", flush=True)


    # ── Le protocole : double aveugle, station ET mois cachés ────────────────────────
    rng = np.random.default_rng(GRAINE)
    ids = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(ids), n_spa)
    plis = []
    for i, mm in enumerate(mois_ok):
        dans = d["station_id"].isin(groupes[i % n_spa])
        plis.append((mm, (d["mois"] == mm) & dans, (d["mois"] != mm) & ~dans))

    print(f"\n{'═' * 100}")
    print(f"MÉTHODE MAXIMALE — {polluant} {libelle_echeance(horizon)} · double aveugle, station ET mois cachés")
    print(f"{'═' * 100}")
    print(f"  {'configuration':38s} {'périmètre':14s} {'col.':>5s} {'gain':>8s} "
          f"{'marginal':>9s} {'σ':>6s} {'plis<0':>7s}")
    # Le fichier `.partiel` est écrit après CHAQUE configuration. Un plantage machine a
    # déjà coûté trois configurations mesurées et perdues (05/08, 01 h 08) : un script qui
    # n'écrit qu'à la fin transforme n'importe quelle interruption en zéro résultat.
    suff = "" if speciation == "brute" else f"_spe-{speciation}"
    suff += "_sc" if support_complet else ""
    suff += ("_sans-" + "-".join(sorted(exclure))) if exclure else ""
    # Le suffixe porte la variante : sans lui, deux piles différentes écriraient le même
    # fichier et la seconde effacerait la première sans que rien ne lève (§ 4).
    suff += "_pre-moyennes" if precurseurs == "moyennes" else ""
    suff += "_fenetre-complete" if fenetre == "complete" else ""
    suff += "_avec-ifs" if avec_ifs else ""
    suff += "_avec-chimie" if avec_chimie else ""
    # L'épinglage ne change PAS le nom par lui-même : une pile réduite épinglée sur sa
    # référence est la mesure qu'on veut lui comparer, et la renommer la rendrait introuvable
    # pour `ablation_jointe`. Ce que l'épinglage change est inscrit dans `n_mois`.
    #
    # 🔴 Mais alors DEUX épinglages différents écrivent le même fichier. C'est « une variante
    # écrase sa jumelle », déjà payé sur ce dépôt. Le nom de la variante ne peut pas se
    # deviner depuis la liste de mois — il appartient à l'appelant, qui seul sait pourquoi il
    # épingle. D'où `--suffixe-extra`, explicite et obligatoire dès qu'on épingle plusieurs
    # fois la même pile.
    suff += suffixe_extra
    partiel = RACINE / f"reports/methode_maximale_{polluant}_h{horizon}{suff}.csv.partiel"

    # ── Le PÉRIMÈTRE EFFECTIF, affiché avant la première mesure ──────────────────
    # `CLAUDE.md` § 2 quater : un pli écarté pour effectif insuffisant change le
    # dénominateur sans rien dire. C'est ainsi que PM10 a tourné sur 24 plis au lieu de
    # 29 — visible seulement parce que `n_plis` finit dans le CSV, et encore : sans le
    # nombre PRÉVU à côté, un compte ne dit pas qu'il en manque. Le rejet ne dépend pas
    # de la configuration (seulement des effectifs), il se calcule donc une seule fois.
    ecartes = [(e, int(d[m_te].shape[0]), int(d[m_tr].shape[0])) for e, m_te, m_tr in plis
               if len(d[m_te]) < 200 or len(d[m_tr]) < 1000]
    n_prevus = len(plis)
    if ecartes:
        print(f"  ⚠️ {len(ecartes)} pli(s) écarté(s) sur {n_prevus} pour effectif "
              f"insuffisant (test < 200 ou train < 1 000) :", flush=True)
        for e, nte, ntr in ecartes:
            print(f"       {e} — test {nte:,} · train {ntr:,}", flush=True)
    print(f"  périmètre effectif : {n_prevus - len(ecartes)} plis exécutés "
          f"sur {n_prevus} prévus", flush=True)

    # ── Reprise sur le `.partiel` (règle 4) ──────────────────────────────────────
    # Le segfault de chargement mesuré le 08/08 est **intermittent** : la même commande
    # tombe environ une fois sur deux, et les données ne sont pas en cause — le fichier
    # d'abord accusé (`..._o3_202406.parquet`) passe cinq fois de suite quand il est lu
    # seul. Sans reprise, chaque tentative rejoue les configurations déjà mesurées et le
    # lot n'aboutit jamais ; avec reprise, il aboutit en quelques tentatives.
    #
    # La reprise porte sur le **nom** des configurations, jamais sur leur nombre : un
    # `.partiel` écrit par une version antérieure n'a pas les mêmes étages, et un compte
    # ne le dirait pas. Et elle est invalidée si la fenêtre du corpus a changé — sinon on
    # recollerait des mesures faites sur deux périmètres différents.
    atomes = RACINE / f"reports/predictions_methode_maximale_{polluant}_h{horizon}{suff}.parquet"
    # La reprise porte sur les COLONNES déjà écrites, jamais sur leur nombre : un partiel
    # d'une version antérieure n'a pas les mêmes étages, et un compte ne le dirait pas.
    atomiques = None
    if atomes.with_suffix(".parquet.partiel").exists():
        atomiques = pd.read_parquet(atomes.with_suffix(".parquet.partiel"))
        print(f"  ↷ prédictions atomiques reprises : "
              f"{len([c for c in atomiques.columns if c.startswith('pred__')])} configuration(s)",
              flush=True)
    lignes, precedent = [], None
    # ⚠️ Le CSV ne portait que l'écart-type inter-plis et le compte de plis négatifs. Deux
    # résumés ne permettent PAS de calculer un intervalle sur la DIFFÉRENCE APPARIÉE entre
    # deux configurations : les plis partagent leurs lignes, leur graine et leur découpage,
    # donc la différence est bien plus serrée que ne le suggère la dispersion de chaque
    # série prise séparément. Sans les plis, on ne peut ni le montrer ni le réfuter.
    par_pli: list[dict] = []
    fenetre_courante = f"{mois_ok[0]}→{mois_ok[-1]}"
    if partiel.exists():
        deja = pd.read_csv(partiel)
        attendues = {nom for nom, _, _ in configs}
        fenetres = set(deja.get("fenetre", pd.Series(dtype=str)).astype(str))
        if fenetres - {fenetre_courante}:
            print(f"  ⚠️ .partiel écarté — fenêtre {fenetres} ≠ {fenetre_courante}",
                  flush=True)
        else:
            for r in deja.to_dict("records"):
                if r["configuration"] not in attendues:
                    print(f"  ⚠️ .partiel : « {r['configuration']} » n'existe plus dans "
                          f"cette version — ligne ignorée", flush=True)
                    continue
                lignes.append(r)
                print(f"  {r['configuration']:38s} {r['perimetre']:14s} "
                      f"{r['n_colonnes']:>5d} {r['gain_pct']:+7.2f}%"
                      f"{'':>10}{'':>7}{'':>8}  ↷ repris du .partiel", flush=True)
                if not str(r["configuration"]).startswith(("★", "plafond")):
                    precedent = float(r["gain_pct"])
    faites = {r["configuration"] for r in lignes}

    for nom, colonnes, per in configs:
        if nom in faites:
            continue
        t0 = time.time()
        obs, cams, pred, gains, cles = [], [], [], [], []
        for mm, m_te, m_tr in plis:
            te, tr = d[m_te], d[m_tr]
            if len(te) < 200 or len(tr) < 1000:
                continue
            if speciation == "anomalie" and any(c in colonnes for c in cols_spe):
                # référence = TOUTES les stations, le mois de test exclu (cf. `anomaliser`)
                tr, te = anomaliser(d[d["mois"] != mm], tr, te, cols_spe)
            p = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
            o, c = te["valeur"].to_numpy(), te["cams_jour"].to_numpy()
            gains.append(gain(o, c, p))
            obs.append(o); cams.append(c); pred.append(p)
            cles.append(te[["station_id", "jour"]])
            par_pli.append({
                "polluant": polluant, "configuration": nom, "mois": mm,
                "n_test": len(te), "n_train": len(tr),
                "n_stations_test": int(te["station_id"].nunique()),
                "rmse_cams": float(np.sqrt(np.mean((c - o) ** 2))),
                "rmse_corrige": float(np.sqrt(np.mean((p - o) ** 2))),
                "gain_pct": gains[-1]})
        g = gain(np.concatenate(obs), np.concatenate(cams), np.concatenate(pred))
        marge = np.nan if precedent is None else g - precedent
        neg = int(np.sum(np.array(gains) < 0))
        print(f"  {nom:38s} {per:14s} {len(colonnes):>5d} {g:+7.2f}% "
              f"{'—' if precedent is None else f'{marge:+8.2f}'} "
              f"{np.std(gains):6.2f} {neg:>4d}/{len(gains)}"
              f"  [{(time.time() - t0) / 60:.1f} min · cumul {(time.time() - depart) / 60:.1f}]",
              flush=True)
        lignes.append({"polluant": polluant, "horizon": horizon, "configuration": nom,
                       "perimetre": per, "n_colonnes": len(colonnes), "gain_pct": g,
                       "apport_marginal_pct": marge, "ecart_type": float(np.std(gains)),
                       "n_plis_negatifs": neg, "n_plis": len(gains),
                       "n_plis_prevus": n_prevus, "n_plis_ecartes": len(ecartes),
                       "fenetre": f"{mois_ok[0]}→{mois_ok[-1]}", "n_mois": len(mois_ok),
                       "empreinte_entrees": empreinte})
        pd.DataFrame(lignes).to_csv(partiel, index=False)   # jamais le nom définitif

        # ── A01 — les pertes appariées LIGNE À LIGNE ────────────────────────────────
        #
        # 🔴 Ce que leur absence coûtait : une RMSE déjà moyennée par pli a **détruit la
        # covariance** entre deux séries de prédictions sur les mêmes lignes — précisément
        # ce que l'appariement exploite. Sans les prédictions atomiques, tout intervalle
        # robuste, toute ablation jointe et toute mesure de redondance entre familles exige
        # de **recalculer** la pile entière : vingt-cinq à cinquante minutes par polluant et
        # par configuration.
        #
        # On écrit donc une colonne par configuration, avec sa clé (station, jour), et on le
        # fait APRÈS CHAQUE configuration — même discipline que le `.partiel` du CSV : un
        # fichier écrit seulement à la fin transforme n'importe quelle interruption en zéro
        # résultat, et cette machine plante une fois sur deux au chargement.
        cle_col = "".join(ch if ch.isalnum() else "_" for ch in nom).strip("_").lower()
        bloc = pd.concat(cles, ignore_index=True)
        bloc["obs"] = np.concatenate(obs)
        bloc["cams_jour"] = np.concatenate(cams)
        bloc[f"pred__{cle_col}"] = np.concatenate(pred)
        if atomiques is None:
            atomiques = bloc
        else:
            avant_at = len(atomiques)
            atomiques = atomiques.merge(
                bloc[["station_id", "jour", f"pred__{cle_col}"]],
                on=["station_id", "jour"], how="outer")
            if len(atomiques) < avant_at:
                raise SystemExit(f"la jointure atomique a PERDU des lignes "
                                 f"({avant_at:,} → {len(atomiques):,})")
        atomiques.to_parquet(atomes.with_suffix(".parquet.partiel"), index=False)
        if not nom.startswith("★") and not nom.startswith("plafond"):
            precedent = g

    # ⚠️ La table se construit APRÈS la dernière mesure (règle 2 ter), et l'on exige
    # nommément les colonnes attendues avant d'écrire.
    t = pd.DataFrame(lignes)
    for c in ("gain_pct", "apport_marginal_pct", "perimetre", "n_mois"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")
    f = RACINE / f"reports/methode_maximale_{polluant}_h{horizon}{suff}.csv"
    t.to_csv(f, index=False)
    if par_pli:   # un pli par ligne : de quoi apparier deux configurations à la main
        fp = RACINE / f"reports/methode_maximale_{polluant}_h{horizon}{suff}_par_pli.csv"
        pd.DataFrame(par_pli).to_csv(fp, index=False)
        print(f"Écrit : {fp.relative_to(RACINE)} · {len(par_pli)} lignes "
              f"({len(set(x['configuration'] for x in par_pli))} configurations)", flush=True)
    if atomiques is not None:
        atomiques.to_parquet(atomes, index=False)
        prov_at = atomes.with_suffix(".parquet.partiel")
        prov_at.unlink(missing_ok=True)
        n_conf = len([c for c in atomiques.columns if c.startswith("pred__")])
        print(f"Écrit : {atomes.relative_to(RACINE)} · {len(atomiques):,} lignes × "
              f"{n_conf} configurations — pertes appariées reconstructibles sans recalcul",
              flush=True)
    partiel.unlink(missing_ok=True)   # le nom définitif ne paraît qu'une fois complet
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--ablation", action="store_true",
                   help="ajouter les 5 configurations « pile complète MOINS une famille » "
                        "— ce que chaque famille apporte pour CE polluant, hors effet d'ordre")
    a.add_argument("--exclure", default="",
                   help="familles à retirer quoi qu'il arrive, séparées par des virgules — "
                        "pour rendre la pile identique sur les quatre polluants")
    a.add_argument("--support-complet", action="store_true",
                   help="écarter toute famille ayant au moins un MOIS entièrement absent — "
                        "sinon le modèle apprend la date par le motif de manque")
    a.add_argument("--suffixe-extra", default="", dest="suffixe_extra", metavar="_MOT",
                   help="suffixe supplémentaire du nom de sortie — obligatoire dès qu'on "
                        "épingle plusieurs variantes de la même pile, sans quoi elles "
                        "s'écrasent")
    a.add_argument("--mois-de", default="", dest="mois_de", metavar="CSV_PAR_PLI",
                   help="restreindre la fenêtre aux mois d'un artefact `_par_pli.csv` de "
                        "référence ; ne peut que restreindre, jamais élargir")
    a.add_argument("--avec-chimie", action="store_true", dest="avec_chimie",
                   help="joint le MODULE chimie (formaldéhyde, glyoxal, NO, CO ; 4 moyennes) "
                        "en dernière position ; la fenêtre est restreinte à son support")
    a.add_argument("--avec-ifs", action="store_true", dest="avec_ifs",
                   help="ajoute le module météo prévue IFS en DERNIÈRE position et "
                        "restreint la fenêtre à son support")
    a.add_argument("--fenetre", default="geoscf", choices=("geoscf", "complete"),
                   help="« geoscf » borne l'évaluation à la couverture de GEOS-CF v1 "
                        "(29 mois) ; « complete » prend tout le corpus apparié et EXIGE "
                        "--exclure geoscf")
    a.add_argument("--precurseurs", default="completes",
                   choices=("completes", "moyennes"),
                   help="« moyennes » retient les 4 moyennes ; « completes » y ajoute les "
                        "4 maxima — la variante en service, non démontrée sur l'axe complet")
    a.add_argument("--speciation", default="brute",
                   choices=("brute", "anomalie", "core7"),
                   help="« anomalie » remplace chaque composante par son écart à la "
                        "climatologie station × mois, ajustée pli par pli. Écrit dans "
                        "un artefact SUFFIXÉ : le chemin publié reste intact.")
    n = a.parse_args()
    # ⚠️ Le paramètre s'appelle `n_spa`, l'option `--plis-spatiaux`. Ce décalage est
    # précisément ce qui rend un appel positionnel fragile — et il m'a fait écrire
    # `plis_spatiaux=` ici, refusé en quatre minutes par le contrôle d'artefact.
    #
    # 🔴 Arguments NOMMÉS, jamais positionnels — 24/08/2026. Un `--lot` présent dans le
    # parseur et absent de l'appel positionnel a fait tourner la chimie sous l'étiquette des
    # précurseurs et ÉCRASER leur fichier. Rien n'a levé : le CSV existait, ses colonnes
    # étaient les bonnes, ses valeurs venaient d'ailleurs.
    raise SystemExit(main(polluant=n.polluant, horizon=n.horizon,
                          n_spa=n.plis_spatiaux, ablation=n.ablation,
                          speciation=n.speciation, support_complet=n.support_complet,
                          exclure=tuple(x for x in n.exclure.split(',') if x),
                          precurseurs=n.precurseurs, fenetre=n.fenetre,
                          avec_ifs=n.avec_ifs, avec_chimie=n.avec_chimie,
                          mois_de=n.mois_de, suffixe_extra=n.suffixe_extra))
