#!/usr/bin/env python3
"""Ce que TROPOMI apporte — et la question précise à laquelle il est censé répondre.

La question
-----------
Le levier le plus fort du projet est **l'observation de la veille : +8,9 %**, davantage que
toute la météo. Sa limite est écrite dans le dossier : elle n'existe **qu'aux stations
instrumentées**. C'est exactement l'écart entre le chiffre « aux stations » et la
revendication propre du projet — *prédire là où rien ne mesure*.

Et cette revendication vient de prendre un coup. Sous validation bloquée spatialement, avec
un fossé fixé **a priori** par le variogramme des résidus, le gain tombe de +28,60 % à
**+10,46 %** sur l'ozone et de +28,47 % à **−9,04 %** sur les PM2,5. Le témoin à retrait
aléatoire sépare les causes : sur PM2,5, 21,2 points de famine et 16,3 de fuite spatiale.

Or les 53 prédicteurs actuels contiennent ``lat_wgs84`` et ``lon_wgs84``. Un arbre s'en sert
pour **mémoriser un lieu** — et une mémorisation de lieu est précisément ce que le fossé
détruit. Il manque un descripteur qui dise *quel genre d'endroit c'est* sans le nommer.

Deux produits de nature différente, tirés de la même donnée
-----------------------------------------------------------
**① La colonne du jour.** L'observation de la veille, étendue au territoire. Couverture
mesurée sur 24 jours de 2024 : **86 % en moyenne annuelle**, mais **34 % au pire jour
d'hiver**. La couverture est donc la plus faible quand le NO₂ est le plus fort — biais
d'échantillonnage à mesurer, jamais à moyenner avec l'été.

**② La climatologie mensuelle.** Moyenner trente passages à 86 % ne laisse pas de trou : on
obtient une carte **complète**, à 3,9 km, de l'environnement d'émission de chaque station.
C'est le descripteur transportable qui manque — disponible en tout point de France, y compris
là où aucune station ne mesure, et jamais absent.

**Aucune observation au sol n'entre dans l'une ou l'autre.** La climatologie est une carte
satellitaire, au même titre que le modèle numérique de terrain : elle ne peut pas fuir la
cible, puisqu'elle ne la voit pas.

Les huit jeux comparés — ils forment trois questions, pas une liste
--------------------------------------------------------------------
**Question A — le champ satellitaire apporte-t-il quelque chose ?**

1. **base** — les 53 prédicteurs actuels ;
2. **+ pixel J−3** — la seule valeur au point de la station ;
3. **+ pixel + couronnes** — plus les moyennes à 10, 25, 50 et 100 km et les gradients.

*L'écart entre 2 et 3 **est** l'information que porte la structure spatiale.* C'est la mesure
qui rend falsifiable l'idée d'une architecture convolutive : si elle est nulle, aucun réseau
profond ne trouvera dans ces imagettes ce qui ne s'y trouve pas, et on l'aura établi pour le
prix d'un ``bincount``.

**Question B — la carte climatologique apporte-t-elle quelque chose ?**

4. **+ climatologie** ;
5. **+ tout**.

**Question C — peut-elle remplacer la mémorisation de lieu ?** La seule qui réponde à
l'effondrement de la validation bloquée.

6. **sans lat/lon (nu)** — ce que la position portait réellement ;
7. **sans lat/lon + typologie** — le **témoin gratuit**, déjà sur le disque : urbain /
   périurbain / rural × fond / trafic / industriel ;
8. **sans lat/lon + typologie + climatologie**.

*Sans le jeu 7, un gain du jeu 8 serait porté au crédit de TROPOMI alors qu'une variable
catégorielle gratuite ferait peut-être le même travail.* La question n'est pas « un substitut
à la position aide » mais « **celui-ci** aide au-delà de celui qu'on avait déjà ».

Deux protocoles, parce que le verdict dépend de la question
-------------------------------------------------------------
* ``i % n`` — le protocole historique, celui qui rend les chiffres comparables à tous les
  autres apports mesurés dans ce projet ;
* **blocs + fossé** au rayon du variogramme — 150 km pour O₃ et PM2,5, 75 km pour NO₂ — le
  seul qui pose la question à laquelle TROPOMI prétend répondre.

Un gain sur le premier et pas sur le second serait un résultat **négatif** pour la thèse, et
il se publierait comme les autres.

Critère de rétention : ``aq.eval.critere`` — relatif au RMSE de base, IC95 par bootstrap de
stations, sans dégradation du décile haut.

Usage : python3 scripts/apport_tropomi.py [--polluant NO2] [--plis 3]
Sortie : reports/apport_tropomi_{polluant}.csv
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval.critere import cribler  # noqa: E402
from aq.ingest import controle as ctl  # noqa: E402
from apport_meteo import ic_difference, resume  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402
from validation_bloquee import coordonnees, plis_alternes, plis_spatiaux  # noqa: E402

# ⚠️ **Trois jours, pas deux** — et ce n'est pas un choix de prudence, c'est une mesure.
#
# Le flux OFFL porte dans son nom l'horodatage de traitement. Latence mesurée sur 70 granules
# répartis de 2024 à 2026 : **médiane 40,4 h, p90 58,0 h, maximum 61,4 h**.
#
# Une prévision émise à 3 h du matin pour le jour J dispose du passage de J−2 avec 38,5 h de
# recul — **moins que la latence médiane**. Retenir J−2 aurait donc mesuré un gain avec une
# variable qui n'existe pas encore à l'heure d'émission : exactement la fuite que ce projet
# traque partout ailleurs, et qui ne lève aucune erreur.
#
# J−3 laisse 62,5 h, au-dessus du maximum observé. C'est le décalage **soutenable**.
#
# Le flux NRTI, lui, a une latence médiane de 0,9 h et autoriserait J−1 — mais son archive
# est trouée (0 granule certains jours contre 33 d'autres). Une chaîne réelle l'emploierait
# et ferait donc **mieux** que ce qui est mesuré ici. Contrairement à la météo ERA5, qui
# donne un *plafond* inatteignable, ce chiffre est un **plancher**.
DECALAGE = 3
GRAINE = 0
# Rayons du variogramme des résidus, fixés **a priori** avant tout score.
RAYON = {"O3": 150.0, "PM25": 150.0, "NO2": 75.0, "PM10": 150.0}
POSITION = ["lat_wgs84", "lon_wgs84"]


def tropomi(bornes: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Les extractions TROPOMI, restreintes à la fenêtre du panel évalué.

    Pourquoi borner, et pourquoi le borner **ici**
    ----------------------------------------------
    Deux raisons, dont une seule est évidente.

    1. **Reproductibilité.** L'extraction couvre 2023-08 → 2026-07 tandis que le panel de
       modélisation s'arrête à 2025-01. Sans borne, la climatologie serait calculée sur le
       nombre de mois **présents sur le disque à l'instant du lancement** — donc un résultat
       différent selon qu'on lance pendant ou après l'extraction. Un chiffre qui dépend de
       l'heure à laquelle on l'a produit n'est pas un chiffre.
    2. **Honnêteté temporelle.** La climatologie ne contient aucune observation au sol et ne
       peut donc pas fuir la cible. Mais la calculer sur des mois **postérieurs** à la période
       évaluée resterait difficile à défendre en entretien, pour un gain nul. On s'en prive.
    """
    fichiers = sorted(glob.glob(str(RACINE / "data/processed/tropomi/"
                                    "tropomi_metropole_*.parquet")))
    if not fichiers:
        raise SystemExit("aucune extraction TROPOMI — lancer scripts/extraire_tropomi.py")
    t = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    t["jour"] = pd.to_datetime(t["jour"])
    if t["jour"].dt.tz is not None:
        t["jour"] = t["jour"].dt.tz_localize(None)
    debut, fin = (pd.Timestamp(b).tz_localize(None) if pd.Timestamp(b).tz is not None
                  else pd.Timestamp(b) for b in bornes)
    # Marge amont : les variables retardées de J−3 et les moyennes à 7 jours ont besoin des
    # jours qui précèdent le premier jour évalué.
    t = t[(t["jour"] >= debut - pd.Timedelta(days=10)) & (t["jour"] <= fin)]
    mois_couverts = t["jour"].dt.to_period("M").nunique()
    attendus = (fin.to_period("M") - debut.to_period("M")).n + 1
    if mois_couverts < attendus:
        raise SystemExit(f"TROPOMI ne couvre que {mois_couverts} mois sur {attendus} "
                         f"demandés ({debut:%Y-%m} → {fin:%Y-%m}) — attendre la fin de "
                         f"l'extraction plutôt que d'évaluer sur un corpus amputé")
    ctl.exiger_colonnes(t, ["station_id", "jour", "no2_col", "aai_col"], "TROPOMI")
    ctl.exiger_variation(t, ["no2_col", "aai_col"], "TROPOMI")
    print(f"TROPOMI · {len(t):,} lignes · {t['station_id'].nunique()} stations · "
          f"{t['jour'].nunique()} jours · {t['jour'].min():%Y-%m} → {t['jour'].max():%Y-%m}")
    print(f"  couverture NO₂ {t['no2_col'].notna().mean():.0%} · "
          f"AAI {t['aai_col'].notna().mean():.0%}")
    return t


RAYONS = (10, 25, 50, 100)


def variables_retardees(t: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Champ satellitaire antérieur, décalé de ``DECALAGE`` jours.

    Rend **deux** listes de noms, et la séparation est le cœur de l'expérience :

    * ``point`` — le seul pixel de la station, ce qu'une extraction naïve donnerait ;
    * ``couronnes`` — les moyennes à 10, 25, 50 et 100 km, plus le gradient.

    L'écart entre un jeu qui contient le premier et un jeu qui contient les deux **est**
    l'information que porte la structure spatiale. C'est la mesure qui rend falsifiable
    l'idée d'un réseau convolutif : si elle est nulle, aucune architecture profonde ne
    trouvera dans ces imagettes ce qui n'y est pas.

    Le décalage est appliqué **par station sur un calendrier réindexé**, jamais par ``shift``
    sur des lignes trouées : avec 34 % de couverture en février, « la ligne trois plus haut »
    peut dater de la semaine précédente. On lit la donnée, pas sa position.
    """
    base_point = ["no2_col", "aai_col"]
    base_anneaux = [f"{p}_r{r}" for p in ("no2", "aai") for r in RAYONS]
    comptes = [f"no2_n{r}" for r in RAYONS]
    presentes = [c for c in base_point + base_anneaux + comptes if c in t.columns]
    manquantes = set(base_point + base_anneaux) - set(presentes)
    if manquantes:
        raise SystemExit(f"colonnes TROPOMI absentes : {sorted(manquantes)} — "
                         f"l'extraction date-t-elle d'avant les couronnes ?")

    morceaux = []
    for station, g in t.groupby("station_id", sort=False):
        g = g.set_index("jour").sort_index()
        complet = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="D"))
        passe = complet[presentes].shift(DECALAGE)
        s = pd.DataFrame(index=complet.index)

        s["tropomi_no2_j"] = passe["no2_col"]
        s["tropomi_aai_j"] = passe["aai_col"]
        for n in (3, 7):
            s[f"tropomi_no2_moy_{n}j"] = passe["no2_col"].rolling(n, min_periods=1).mean()
            s[f"tropomi_aai_moy_{n}j"] = passe["aai_col"].rolling(n, min_periods=1).mean()
        # **La fraîcheur est une variable, pas un détail** — et ici plus qu'ailleurs : avec
        # 34 % de pixels valides au cœur de l'hiver, le dernier passage exploitable peut
        # dater de plusieurs jours. Le modèle doit pouvoir en tenir compte plutôt que de
        # traiter une colonne vieille d'une semaine comme celle d'avant-hier.
        age = pd.Series(np.arange(len(complet)), index=complet.index)
        dernier = age.where(complet["no2_col"].notna()).ffill()
        s["tropomi_fraicheur_j"] = (age - dernier + DECALAGE).clip(upper=30)

        for c in base_anneaux + comptes:
            s[f"tropomi_{c}"] = passe[c]
        # Le gradient centre-périphérie : ce que le point a de plus que sa région. C'est la
        # grandeur qui distingue une station dans un panache d'une station dans un fond
        # régional élevé — et le pixel seul ne peut pas la porter.
        for r in RAYONS:
            s[f"tropomi_grad_no2_{r}"] = passe["no2_col"] - passe[f"no2_r{r}"]
        s["station_id"] = station
        morceaux.append(s.reset_index(names="jour"))

    r = pd.concat(morceaux, ignore_index=True)
    point = ["tropomi_no2_j", "tropomi_aai_j", "tropomi_fraicheur_j",
             "tropomi_no2_moy_3j", "tropomi_no2_moy_7j",
             "tropomi_aai_moy_3j", "tropomi_aai_moy_7j"]
    couronnes = [c for c in r.columns
                 if c not in point + ["station_id", "jour"]]
    return r, point, couronnes


def climatologie(t: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Carte satellitaire par station et mois calendaire — complète et transportable.

    Aucune observation au sol n'y entre : c'est un descripteur de lieu au même titre que
    l'altitude, et il ne peut donc pas fuir la cible. Il est en revanche **disponible
    partout**, ce que ``lat/lon`` ne remplace qu'en mémorisant.
    """
    d = t.copy()
    d["mois"] = d["jour"].dt.month
    agregats = {
        "tropomi_no2_clim": ("no2_col", "mean"),
        "tropomi_aai_clim": ("aai_col", "mean"),
        "tropomi_no2_clim_p90": ("no2_col", lambda s: s.quantile(0.9)),
        "tropomi_couverture": ("no2_col", lambda s: s.notna().mean()),
    }
    # La climatologie des couronnes décrit l'environnement **régional** d'émission — un fond
    # urbain dans une plaine peuplée n'a pas la même signature qu'un fond urbain isolé, et
    # c'est précisément la distinction que `lat/lon` ne fait qu'en mémorisant.
    for r in RAYONS:
        for p in ("no2", "aai"):
            if f"{p}_r{r}" in d.columns:
                agregats[f"tropomi_{p}_clim_r{r}"] = (f"{p}_r{r}", "mean")
    clim = d.groupby(["station_id", "mois"]).agg(**agregats).reset_index()
    # Une station dont aucun mois n'est renseigné trahirait une jointure ratée.
    vides = clim.groupby("station_id")["tropomi_no2_clim"].apply(lambda s: s.isna().all())
    if vides.any():
        raise SystemExit(f"{int(vides.sum())} stations sans aucune climatologie — "
                         f"jointure ou extraction incomplète, ne pas poursuivre")
    noms = [c for c in clim.columns if c not in ("station_id", "mois")]
    print(f"  climatologie · {len(clim):,} couples station×mois · "
          f"couverture médiane {clim['tropomi_couverture'].median():.0%}")
    return clim, noms


def typologie(ids: np.ndarray) -> tuple[pd.DataFrame, list[str]]:
    """Le témoin gratuit : la typologie de station, déjà sur le disque.

    Sans ce témoin, tout gain observé en retirant ``lat/lon`` au profit de la climatologie
    satellitaire serait attribué à TROPOMI — alors qu'un descripteur de lieu **catégoriel et
    gratuit** ferait peut-être le même travail. Ce que le jeu ⑤ doit établir n'est pas
    « un substitut à la position aide », mais « **ce** substitut-là aide au-delà de celui
    qu'on avait déjà ».

    ``typologie_zone`` est encodée en ordinal : de l'urbain au rural isolé, c'est un gradient
    de densité réel, et lui imposer un ordre est plus juste que de l'éclater. ``type_station``
    est éclatée : fond, trafic et industriel ne s'ordonnent pas.
    """
    s = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                        columns=["station_id", "typologie_zone", "type_station"])
    s = s.drop_duplicates("station_id").set_index("station_id")
    manquantes = [i for i in ids if i not in s.index]
    if manquantes:
        raise SystemExit(f"{len(manquantes)} stations sans typologie ({manquantes[:4]})")
    s = s.loc[ids]
    if s[["typologie_zone", "type_station"]].isna().any().any():
        raise SystemExit("typologie manquante après jointure — ne pas imputer en silence")

    ordre = {"urban": 0, "suburban": 1, "rural-nearcity": 2,
             "rural-regional": 3, "rural-remote": 4}
    inconnues = set(s["typologie_zone"]) - set(ordre)
    if inconnues:
        raise SystemExit(f"typologie_zone inconnue : {inconnues} — compléter l'ordre "
                         f"plutôt que de la laisser tomber sur une valeur par défaut")
    d = pd.DataFrame(index=s.index)
    d["typo_densite"] = s["typologie_zone"].map(ordre).astype("int8")
    for valeur in sorted(s["type_station"].unique()):
        d[f"typo_{valeur}"] = (s["type_station"] == valeur).astype("int8")
    return d.reset_index(), [c for c in d.columns]


def modele():
    return modele_mos(graine=GRAINE)


def evaluer(j: pd.DataFrame, predicteurs: list[str], groupe: np.ndarray,
            c: pd.DataFrame | None = None, rayon_km: float = 0.0) -> pd.DataFrame:
    """Prédictions hors échantillon, pli par pli, avec fossé optionnel autour du test."""
    sortie = j[["station_id", "jour", "obs_jour", "cams_jour"]].copy()
    sortie["pred"] = np.nan
    stations = np.sort(j["station_id"].unique())
    pli_de_station = dict(zip(stations, groupe))
    pli = j["station_id"].map(pli_de_station).to_numpy()

    for g in np.unique(groupe):
        test = pli == g
        entraine = ~test
        if rayon_km > 0 and c is not None:
            stations_test = stations[groupe == g]
            d = np.sqrt(((c.loc[stations].to_numpy()[:, None, :]
                          - c.loc[stations_test].to_numpy()[None, :, :]) ** 2).sum(-1))
            proches = set(stations[d.min(axis=1) < rayon_km]) - set(stations_test)
            entraine &= ~j["station_id"].isin(proches).to_numpy()
        m = modele()
        m.fit(j.loc[entraine, predicteurs],
              j.loc[entraine, "obs_jour"] - j.loc[entraine, "cams_jour"])
        sortie.loc[test, "pred"] = np.clip(
            j.loc[test, "cams_jour"] + m.predict(j.loc[test, predicteurs]), 0, None)
    return sortie


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()

    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    # ⚠️ Le panel horodate **avec** fuseau (UTC), l'extraction TROPOMI **sans**. Deux
    # conséquences si on l'ignore : la comparaison de bornes lève, et — bien pire — la
    # jointure sur `jour` ne rapproche **aucune** ligne sans rien signaler. On ramène tout
    # au naïf ici, une fois, plutôt qu'au cas par cas dans chaque jointure.
    j["jour"] = pd.to_datetime(j["jour"])
    if j["jour"].dt.tz is not None:
        j["jour"] = j["jour"].dt.tz_localize(None)

    # La fenêtre du panel commande : TROPOMI couvre plus large, mais évaluer hors du panel
    # n'a pas de sens et rendrait la climatologie dépendante de l'avancement du lot.
    bornes = (j["jour"].min(), j["jour"].max())
    print(f"fenêtre évaluée · {bornes[0]:%Y-%m-%d} → {bornes[1]:%Y-%m-%d}")
    t = tropomi(bornes)
    retardees, cols_point, cols_couronnes = variables_retardees(t)
    clim, cols_clim = climatologie(t)

    avant = len(j)
    j = j.merge(retardees, on=["station_id", "jour"], how="inner")
    j["mois"] = j["jour"].dt.month
    j = j.merge(clim, on=["station_id", "mois"], how="left")
    # Compter le reçu contre le demandé (règle 2 bis) : une jointure qui perd 90 % des
    # lignes est un défaut, pas un filtre.
    print(f"\n{polluant} · {avant:,} jours-station → {len(j):,} après jointure TROPOMI "
          f"({100 * len(j) / avant:.0f} % conservés) · {j['station_id'].nunique()} stations")
    if len(j) < avant * 0.5:
        raise SystemExit(f"jointure TROPOMI ne conserve que {100 * len(j) / avant:.0f} % "
                         f"des lignes — vérifier la fenêtre avant d'interpréter un score")
    ctl.exiger_lignes(j, 10_000, "jeu apparié TROPOMI")

    typo, cols_typo = typologie(np.sort(j["station_id"].unique()))
    j = j.merge(typo, on="station_id", how="left")
    if j[cols_typo].isna().any().any():
        raise SystemExit("typologie perdue à la jointure")

    sans_pos = [c for c in base if c not in POSITION]
    jeux = {
        "base": base,
        # ① et ② se lisent ensemble : leur écart EST l'information spatiale, et c'est ce
        #    qui rend falsifiable l'idée d'une architecture convolutive.
        "+ pixel J−3": base + cols_point,
        "+ pixel + couronnes": base + cols_point + cols_couronnes,
        "+ climatologie": base + cols_clim,
        "+ tout": base + cols_point + cols_couronnes + cols_clim,
        # Les trois suivants isolent ce que la position portait, et par quoi la remplacer.
        # Le bras qui manquait : la typologie AVEC la position. Sans lui, on ne sait pas si
        # le gain vient d'ajouter la typologie ou de retirer lat/lon en sa présence.
        "base + typo": base + cols_typo,
        "sans lat/lon (nu)": sans_pos,
        "sans lat/lon + typo": sans_pos + cols_typo,
        "sans lat/lon + typo + clim": sans_pos + cols_typo + cols_clim,
    }
    for nom, p in jeux.items():
        manquants = [c for c in p if c not in j.columns]
        if manquants:
            raise SystemExit(f"jeu « {nom} » : colonnes absentes {manquants[:5]}")

    stations = np.sort(j["station_id"].unique())
    c = coordonnees(stations)
    protocoles = {
        "i % n": (plis_alternes(stations, n_plis), 0.0),
        f"blocs + fossé {RAYON[polluant]:.0f} km": (plis_spatiaux(c, n_plis),
                                                    RAYON[polluant]),
    }

    lignes, predictions = [], {}
    for nom_proto, (groupe, rayon) in protocoles.items():
        print(f"\n{'═' * 74}\n{nom_proto}\n{'═' * 74}", flush=True)
        for nom_jeu, predicteurs in jeux.items():
            t0 = time.time()
            p = evaluer(j, predicteurs, groupe, c, rayon)
            r = resume(p, polluant)
            rmse_cams = float(np.sqrt(((p["obs_jour"] - p["cams_jour"]) ** 2).mean()))
            gain_pct = 100 * (1 - r["rmse"] / rmse_cams)
            predictions[(nom_proto, nom_jeu)] = p
            lignes.append({"protocole": nom_proto, "jeu": nom_jeu,
                           "n_predicteurs": len(predicteurs), "rmse_cams": rmse_cams,
                           **r, "gain_pct": gain_pct})
            print(f"  {nom_jeu:22s} {len(predicteurs):3d} var · RMSE {r['rmse']:6.3f} · "
                  f"gain {gain_pct:+6.2f} % · décile haut "
                  f"{r['rmse_decile_haut']:6.3f} · {time.time() - t0:4.0f}s", flush=True)

        # ── Criblage contre la base, dans ce protocole ────────────────────────────
        ref = predictions[(nom_proto, "base")]
        r_ref = resume(ref, polluant)
        print(f"\n  Contre la base, IC95 par bootstrap de stations :")
        for nom_jeu in jeux:
            if nom_jeu == "base":
                continue
            p = predictions[(nom_proto, nom_jeu)]
            bas, haut = ic_difference(ref, p)
            r = resume(p, polluant)
            gain = r_ref["rmse"] - r["rmse"]
            gain_queue = r_ref["rmse_decile_haut"] - r["rmse_decile_haut"]
            v = cribler(r_ref["rmse"], gain, bas, gain_queue,
                        r_ref["rmse_decile_haut"], ic_haut=haut)
            print(f"    {nom_jeu:22s} {gain:+.3f} µg/m³  IC95 [{bas:+.3f} ; {haut:+.3f}]"
                  f"  {v}")
            for ligne in lignes:
                if ligne["protocole"] == nom_proto and ligne["jeu"] == nom_jeu:
                    ligne |= {"gain_vs_base": gain, "ic_bas": bas, "ic_haut": haut,
                              "retenu": v.retenu, "motif": v.motif}

    sortie = RACINE / f"reports/apport_tropomi_{polluant}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.0f} min")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="NO2")
    p.add_argument("--plis", type=int, default=3)
    a = p.parse_args()
    raise SystemExit(main(a.polluant, a.plis))
