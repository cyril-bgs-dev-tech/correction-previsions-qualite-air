#!/usr/bin/env python3
"""Le tableau unique du dossier — une seule source de chiffres, régénérable.

Pourquoi ce script existe
-------------------------
Le dossier a porté successivement des chiffres mesurés sur 11 mois, sur 17 mois, puis sur
l'année 2024 complète. Les trois sont exacts ; ils ne sont pas comparables, et ils coexistent
aujourd'hui dans la présentation, les figures et la démo. Un lecteur qui trouve deux valeurs
différentes du même gain à deux pages d'écart cesse de croire les deux.

Ce script produit **le** tableau — celui dont toute figure, toute slide et toute phrase du
dossier doivent dériver. Il ne calcule rien de neuf : il assemble des rapports déjà produits,
en nommant pour chacun sa fenêtre, son effectif et son grain. Tout chiffre du dossier absent
d'ici est un chiffre à retirer ou à re-mesurer.

Ce qu'il refuse de faire
------------------------
Aucune moyenne entre fenêtres, aucun « environ ». La ventilation saisonnière de l'ozone est
**obligatoire** : sur l'année, le MOS officiel affiche +2,0 % qui sont la somme de −19,1 % en
saison et +18,7 % hors saison. Une moyenne qui change de signe selon la découpe n'est pas un
résultat, c'est un artefact d'agrégation — et il vaut dans les deux sens, y compris contre
nous : notre avantage aussi est plus faible en saison.

Usage : python3 scripts/verite_dossier.py
Sortie : reports/VERITE_DOSSIER.md + reports/verite_dossier.csv
"""

from __future__ import annotations

import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]

GRAIN_REGLEMENTAIRE = {"O3": "max_8h", "NO2": "max_horaire", "PM25": "moyenne_jour"}
LIBELLE_GRAIN = {"horaire": "horaire", "max_8h": "max glissant 8 h",
                 "max_horaire": "max horaire", "moyenne_jour": "moyenne journalière"}
NOM = {"O3": "O₃", "NO2": "NO₂", "PM25": "PM2,5", "PM10": "PM10"}

# Seuil d'information français pour le NO₂ : 200 µg/m³ en moyenne horaire
# (arrêté du 07/04/2016). Le seuil d'alerte est à 400.
SEUIL_INFO_NO2 = 200.0


@lru_cache(maxsize=None)          # le panel fait 8,8 M de lignes de NO₂ : une lecture suffit
def compte_depassements_no2(seuil: float = SEUIL_INFO_NO2) -> dict[str, object]:
    """Jours-station de NO₂ dont le **maximum horaire** atteint `seuil` — calculé, jamais cité.

    ⚠️ **Ce chiffre figurait deux fois dans ce document, en dur et en contradiction.** Le § 8
    annonçait « 2 dépassements », le § 10 bis « 3 », adossés à deux corpus différents
    (161 637 et 60 400 jours-station) dont **aucun n'était celui d'une mesure** : les deux
    étaient de la prose, dénominateurs compris. La conclusion ne bougeait pas — à ce seuil le
    problème n'existe pas — mais deux chiffres inconciliables sur la même question sont
    exactement ce que ce fichier existe pour empêcher.

    Mesuré ici sur le **panel unifié**, celui qui sert de vérité terrain partout ailleurs,
    avec la règle des 75 % (18 heures valides sur 24) qu'impose le référentiel LCSQA.
    """
    d = pd.read_parquet(RACINE / "data/processed/panel_unifie_lcsqa.parquet",
                        columns=["station_id", "polluant", "timestamp_utc", "valeur"],
                        filters=[("polluant", "==", "NO2")])
    jour = d["timestamp_utc"].dt.tz_convert("UTC").dt.date
    g = d.groupby(["station_id", jour])["valeur"].agg(["max", "count"])
    g = g[g["count"] >= 18]
    return {"seuil": seuil, "n_depassements": int((g["max"] >= seuil).sum()),
            "n_jours_station": int(len(g)), "n_stations": int(d["station_id"].nunique()),
            "debut": f"{d['timestamp_utc'].min():%Y-%m}", "fin": f"{d['timestamp_utc'].max():%Y-%m}"}


def _pondere(sous: pd.DataFrame) -> dict[str, float]:
    """RMSE agrégée sur plusieurs mois — **quadratique**, jamais linéaire.

    Une RMSE est la racine d'une moyenne de carrés. L'agréger sur des mois se fait donc
    par ``√(Σ nₘ·RMSEₘ² / Σ nₘ)`` et non par ``average(RMSEₘ, weights=nₘ)`` : la moyenne
    linéaire d'une racine sous-estime systématiquement la racine de la moyenne (Jensen),
    d'autant plus que les mois sont dispersés.

    **Le défaut que cette fonction corrige.** Elle faisait exactement cette moyenne linéaire,
    et tous les chiffres du dossier en dépendaient. Un audit externe l'a trouvé le 31/07/2026.
    L'erreur va jusqu'à **0,38 µg/m³** sur les PM2,5 journalières — et elle est plus grande
    sur CAMS brut que sur les produits corrigés, puisque la correction resserre justement la
    dispersion mensuelle. Elle **sous-estimait donc nos propres gains**.

    Le biais, lui, se moyenne bien linéairement : il n'est pas une racine.
    """
    n = sous["n"].to_numpy(dtype="float64")
    return {k: float(np.sqrt(np.sum(n * sous[f"rmse_{k}"].to_numpy() ** 2) / n.sum()))
            for k in ("brut", "officiel", "nous")}


def bloc_double_aveugle(lignes: list[dict]) -> str:
    """Le chiffre de déploiement — station ET mois cachés. À lire AVANT tout le reste.

    Ce bloc est en tête parce que l'ordre de lecture décide de la crédibilité : publier le
    chiffre honnête d'abord rend le chiffre flatteur crédible ; dans l'autre ordre, il devient
    suspect, et un jury le retourne.
    """
    chemins = {p: RACINE / f"reports/double_aveugle_journalier_{p}.csv"
               for p in ("NO2", "PM10", "PM25", "O3")}
    presents = {p: c for p, c in chemins.items() if c.exists()}
    if not presents:
        return ""
    texte = [
        "## 0. Le chiffre de déploiement — station **et** mois cachés ensemble\n",
        "Tous les chiffres de ce document portent sur l'axe **spatial** : stations exclues, "
        "dates connues. Ce n'est pas la condition d'un déploiement, qui demande de prédire "
        "**demain**, à un endroit **pas vu**. Le tableau ci-dessous cache les deux à la "
        "fois.\n",
        "| polluant | spatial | temporel | **double aveugle** | σ | pire pli |",
        "|---|---|---|---|---|---|"]
    for polluant, chemin in presents.items():
        t = pd.read_csv(chemin)
        t = t[t["reglage"] == "défaut"].set_index("epreuve")
        if "double aveugle" not in t.index:
            continue
        d = t.loc["double aveugle"]
        gras = "**" if polluant == "NO2" else ""
        texte.append(
            f"| {gras}{NOM[polluant]}{gras} | {t.loc['spatiale', 'gain_pct']:+.2f} % | "
            f"{t.loc['temporelle', 'gain_pct']:+.2f} % | **{d['gain_pct']:+.2f} %** | "
            f"{d['ecart_type']:.1f} | {d['gain_min']:+.1f} |")
        lignes.append({"bloc": "double aveugle", "polluant": polluant,
                       "grain": "max/moyenne jour", "n": int(d["n_plis"]),
                       "gain": float("nan"), "relatif_pct": d["gain_pct"]})
    texte.append(
        "\n**Un seul polluant sur quatre généralise en conditions de déploiement**, et c'est "
        "celui dont le résidu est **attaché au site** : un décalage de lieu se transporte "
        "d'un mois à l'autre sans rien réapprendre, ce que la typologie de station confirme "
        "par ailleurs. Les trois autres — O₃, PM2,5, PM10 — se groupent entre +3 et +7,5 % "
        "avec un écart-type de 12 à 15. Leur ordre va dans le sens d'une composante locale "
        "décroissante, mais **l'écart total est trois fois plus petit que leur dispersion** : "
        "ne pas conclure dessus.\n"
        "\n⚠️ **Et la capacité du modèle dégrade cet axe.** Sur l'ozone, quatre "
        "configurations, du réglage de production au meilleur candidat d'une étude Optuna de "
        "201 essais : +3,31 % à 400 arbres, +0,46 % à 900, +0,11 % à 3 700, **−1,07 %** à "
        "3 000 mal régularisés. Aucun réglage ne bat la production sur l'axe qui compte, et "
        "un réglage optimisé sur la validation **spatiale** est suspect par construction.\n"
        "\n> **Formulation défendable** : « +24,1 % en validation spatiale sur l'ozone ; "
        "**+3,3 % quand la station et le mois sont cachés ensemble**, ce qui est la condition "
        "de déploiement. Sur le NO₂ les deux chiffres sont +31,6 % et **+25,7 %**. »\n")
    return "\n".join(texte)


def bloc_annee(lignes: list[dict]) -> str:
    """FR 2024 complète, les trois polluants, les deux grains."""
    texte = ["## 1. France, 18 janvier – 31 décembre 2024 — contre le produit officiel\n",
             "**Périmètre : usage A — aux stations instrumentées, axe spatial.** Les "
             "prédicteurs comprennent les observations passées de la station, qui n'existent "
             "pas là où rien ne mesure. Pour l'usage B, voir § 7 ; pour l'axe de déploiement, "
             "voir § 0.\n",
             "Comparaison à `cams-europe-air-quality-forecasts-optimised-at-observation-sites`, "
             "sur les **mêmes** stations et les **mêmes** jours. RMSE en µg/m³.\n",
             "⚠️ **La fenêtre n'est pas l'année civile** : le produit officiel ne commence "
             "qu'au **18/01/2024** — vérifié dans les archives, pas déduit du catalogue. "
             "Écrire « année 2024 complète » est faux.\n",
             "| polluant | grain | n | CAMS brut | MOS officiel | nous |",
             "|---|---|---|---|---|---|"]
    for polluant in ("O3", "NO2", "PM25"):
        chemin = RACINE / f"reports/comparaison_mos_officiel_annee_{polluant}.csv"
        if not chemin.exists():
            texte.append(f"| {NOM[polluant]} | — | *rapport absent* | | | |")
            continue
        table = pd.read_csv(chemin)
        for grain in ("horaire", GRAIN_REGLEMENTAIRE[polluant]):
            sous = table[table["grain"] == grain]
            if sous.empty:
                continue
            m = _pondere(sous)
            reglementaire = grain != "horaire"
            etiquette = (f"**{LIBELLE_GRAIN[grain]}**" if reglementaire
                         else LIBELLE_GRAIN[grain])
            texte.append(
                f"| {NOM[polluant]} | {etiquette} | {int(sous['n'].sum()):,} | "
                f"{m['brut']:.2f} | {m['officiel']:.2f} "
                f"({100 * (1 - m['officiel'] / m['brut']):+.1f} %) | "
                f"{m['nous']:.2f} ({100 * (1 - m['nous'] / m['brut']):+.1f} %) |")
            lignes.append({"bloc": "FR 2024", "polluant": polluant, "grain": grain,
                           "n": int(sous["n"].sum()), **m})
    texte.append("\nLe grain marqué en gras est celui sur lequel porte le **seuil "
                 "réglementaire** du polluant.\n")
    return "\n".join(texte)


def bloc_saison(lignes: list[dict]) -> str:
    """La ventilation qui interdit de citer la moyenne annuelle de l'ozone."""
    chemin = RACINE / "reports/comparaison_mos_officiel_annee_O3.csv"
    if not chemin.exists():
        return ""
    table = pd.read_csv(chemin)
    r = table[table["grain"] == "max_8h"].copy()
    r["m"] = r["mois"] % 100
    saison = r["m"].between(4, 9)

    texte = ["## 2. Ozone — la moyenne annuelle masque un changement de signe\n",
             "La fenêtre d'évaluation de l'ozone au référentiel LCSQA est **avril-septembre**. "
             "Sur cette fenêtre, le produit officiel se comporte à l'inverse de sa moyenne "
             "annuelle.\n",
             "| fenêtre | n | CAMS brut | MOS officiel | nous |", "|---|---|---|---|---|"]
    for nom, sel in (("année entière", r["m"] > 0),
                     ("**saison ozone, avril-septembre**", saison),
                     ("hors saison, octobre-mars", ~saison)):
        sous = r[sel]
        m = _pondere(sous)
        texte.append(f"| {nom} | {int(sous['n'].sum()):,} | {m['brut']:.2f} | "
                     f"{m['officiel']:.2f} ({100 * (1 - m['officiel'] / m['brut']):+.1f} %) | "
                     f"{m['nous']:.2f} ({100 * (1 - m['nous'] / m['brut']):+.1f} %) |")
        lignes.append({"bloc": "saison O3", "polluant": "O3", "grain": nom,
                       "n": int(sous["n"].sum()), **m})

    pire = r.loc[(r["rmse_officiel"] / r["rmse_brut"]).idxmax()]
    degrade = int((r["rmse_officiel"] > r["rmse_brut"]).sum())
    texte.append(
        f"\nLe produit officiel dégrade le brut **{degrade} mois sur 12**, au pire en "
        f"{int(pire['mois']) % 100:02d}/{int(pire['mois']) // 100} "
        f"({100 * (1 - pire['rmse_officiel'] / pire['rmse_brut']):+.1f} %). Son biais est "
        f"négatif chaque mois — il sous-estime, ce qui pénalise mécaniquement un maximum.\n"
        f"\n**Et la même lecture nous vise** : notre avantage est le plus faible précisément "
        f"en saison. Citer notre gain annuel sans cette ventilation reproduirait l'erreur que "
        f"nous reprochons à la moyenne annuelle du produit officiel.\n")
    return "\n".join(texte)


def bloc_horsechantillon(lignes: list[dict]) -> str:
    """Le seul test réellement hors fenêtre d'apprentissage."""
    detail = RACINE / "reports/test_hors_echantillon_2025_detail_O3.csv"
    seuils = RACINE / "reports/seuil_decision_O3.csv"
    if not (detail.exists() and seuils.exists()):
        return ""
    d = pd.read_csv(detail)
    s = pd.read_csv(seuils)
    n_dep = int((d["obs_jour"] >= 120).sum())

    texte = [
        "## 3. Hors fenêtre d'apprentissage — Occitanie, 1ᵉʳ semestre 2025\n",
        f"Modèle appris jusqu'au **31/12/2024**, appliqué à une période qu'il n'a jamais vue. "
        f"{len(d):,} jours-station · {d['station_id'].nunique()} stations occitanes · "
        f"**{n_dep} dépassements** observés de 120 µg/m³.\n",
        "C'est le seul test sans fuite possible — ni de station, ni de période. "
        "Son effectif est petit : un écart faible n'y serait pas concluant.\n",
        "| produit | seuil de décision | POD | FAR | CSI |", "|---|---|---|---|---|"]
    for _, ligne in s.iterrows():
        texte.append(
            f"| {ligne['produit']} | 120 (réglementaire) | {ligne['brut_POD']:.3f} | "
            f"{ligne['brut_FAR']:.3f} | {ligne['brut_CSI']:.3f} |")
    texte.append("| | | | | |")
    for _, ligne in s.iterrows():
        texte.append(
            f"| {ligne['produit']} | **{ligne['seuil_calibre']:.1f}** (calibré sur 2024) | "
            f"{ligne['calibre_POD']:.3f} | {ligne['calibre_FAR']:.3f} | "
            f"{ligne['calibre_CSI']:.3f} |")
        lignes.append({"bloc": "hors échantillon 2025", "polluant": "O3",
                       "grain": ligne["produit"], "n": len(d),
                       "POD": ligne["calibre_POD"], "FAR": ligne["calibre_FAR"],
                       "CSI": ligne["calibre_CSI"]})

    texte.append(
        "\nLe seuil est cherché sur 2024 puis appliqué à 2025 **sans réajustement**, pour les "
        "trois produits également. Au seuil réglementaire brut, notre POD tombe à 0,239 : "
        "c'est un **artefact de calibration**, pas une incapacité — la régression écrase les "
        "extrêmes, l'ordre des jours est conservé mais le franchissement du seuil se perd.\n")

    ic = RACINE / "reports/intervalles_2025_O3.csv"
    if ic.exists():
        t = pd.read_csv(ic)
        texte += [
            "\n### Ce que cet échantillon autorise à dire\n",
            "21 stations et 163 dépassements, avec des jours corrélés au sein d'une station "
            "et d'une région : les écarts ci-dessus n'ont de sens qu'assortis d'un "
            "intervalle. Bootstrap apparié par blocs sur les **deux** axes — stations et "
            "blocs calendaires — à **trois** longueurs de bloc (3, 7 et 14 jours), 2 000 "
            "tirages. Une conclusion qui ne survivrait qu'à une longueur serait un artefact "
            "du découpage.\n",
            "| comparaison | écart | IC95 (blocs de 7 j) | verdict |", "|---|---|---|---|"]
        for (metrique, contre), g in t.groupby(["metrique", "contre"], sort=False):
            sept = g[g["bloc_jours"] == 7].iloc[0]
            n_ok = int(g["concluant"].sum())
            verdict = ("**concluant** aux 3 longueurs" if n_ok == len(g)
                       else f"instable ({n_ok}/{len(g)}) — descriptif" if n_ok
                       else "non concluant")
            texte.append(f"| {metrique.upper()} : nous − {contre} | {sept['ecart']:+.3f} | "
                         f"[{sept['ic_bas']:+.3f} ; {sept['ic_haut']:+.3f}] | {verdict} |")
        texte.append(
            "\n**Une seule comparaison survit** : notre RMSE est inférieur à celui du MOS "
            "officiel de **3,22 µg/m³**, IC95 [−4,87 ; −1,74], aux trois longueurs de bloc.\n"
            "\nTout le reste est **descriptif**, et cela coupe dans les deux sens : notre "
            "avantage en CSI (+0,107) n'est pas démontré, mais l'avantage du produit officiel "
            "en POD (−0,147 pour nous) ne l'est pas davantage, et notre avance sur le CAMS "
            "brut en 2025 (−0,71 µg/m³) non plus.\n"
            "\n⚠️ **Formulation imposée pour ce bloc** : « sur cet échantillon, les "
            "estimations ponctuelles indiquent… ». Ne jamais écrire que nous détectons mieux "
            "que le produit officiel en 2025 — l'intervalle ne le permet pas. Le seul énoncé "
            "ferme est celui du RMSE.\n")
    return "\n".join(texte)


def bloc_factoriel(lignes: list[dict]) -> str:
    """L'expérience contrôlée : seule la cible change."""
    texte = [
        "## 4. L'expérience contrôlée — seule la cible change\n",
        "Les blocs précédents comparent deux **produits** qui diffèrent par le grain, les "
        "variables, l'historique et l'algorithme à la fois : ils établissent une association, "
        "pas un effet. L'expérience ci-dessous ne fait varier que la **cible d'apprentissage** "
        "— même modèle, mêmes lignes, mêmes plis par stations exclues, mêmes prédicteurs.\n",
        "| polluant | grain réglementaire | horaire corrigé puis agrégé | cible directe | "
        "écart |", "|---|---|---|---|---|"]
    for polluant in ("O3", "NO2", "PM25"):
        chemin = RACINE / f"reports/cible_journaliere_{polluant}.csv"
        if not chemin.exists():
            continue
        t = pd.read_csv(chemin).set_index("voie")
        a = float(t.loc["horaire agrégée", "gain_pct"])
        b = float(t.loc["cible du jour, directe", "gain_pct"])
        nature = "**moyenne**" if polluant == "PM25" else "**maximum**"
        texte.append(f"| {NOM[polluant]} | {LIBELLE_GRAIN[GRAIN_REGLEMENTAIRE[polluant]]} "
                     f"({nature}) | {a:+.2f} % | {b:+.2f} % | **{b - a:+.1f} pts** |")
        lignes.append({"bloc": "factoriel cible", "polluant": polluant,
                       "grain": "horaire agrégé vs direct", "n": int(t["n_jours"].iloc[0]),
                       "gain_agrege": a, "gain_direct": b, "ecart_points": b - a})
    texte.append(
        "\n**Le signe s'inverse sur PM2,5**, et c'est ce qui distingue cette mesure d'une "
        "corrélation. Le mécanisme invoqué est qu'une correction horaire réduit la "
        "variabilité : cela pénalise une **statistique d'ordre** — un maximum — mais pas une "
        "**tendance centrale**. PM2,5 est le seul des trois dont le grain réglementaire est "
        "une moyenne. Le mécanisme prédit qu'il n'y gagne rien ; il n'y gagne rien.\n"
        "\n### Antériorité — à citer, pas à revendiquer\n"
        "\nBertrand, Meleux, Ung, Descombes & Colette (2023), *Technical note: Improving the "
        "European air quality forecast of CAMS using machine learning techniques*, ACP 23, "
        "5317 ([doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)) — "
        "**l'article qui décrit le produit officiel, écrit par ses auteurs** — rapporte "
        "**20,5 %** de gain en agrégeant une correction horaire contre **32,8 %** en "
        "apprenant directement le maximum journalier, et recommande explicitement « *using "
        "daily MOS instead of hourly MOS if performances must be optimized for the daily max "
        "statistics* ». Il couvre les quatre polluants, cibles en moyenne journalière "
        "comprises.\n"
        "\nLe tableau ci-dessus est donc une **réplication indépendante** — autre algorithme "
        "(boosting contre forêt aléatoire), autre période, autre domaine — et non une "
        "découverte. Ne jamais présenter l'effet de grain comme un résultat propre au "
        "projet.\n"
        "\n**Ce qui reste propre au projet**, une fois Bertrand retiré :\n"
        "\n1. la mesure de ce que le produit **réellement distribué** délivre sur le grain "
        "réglementaire, par opposition à ce que son article établit comme possible ;\n"
        "2. le **renversement saisonnier** du bloc 2, qu'une moyenne annuelle annule ;\n"
        "3. le test **hors fenêtre 2025** avec seuils recalibrés à l'identique.\n"
        "\nC'est un travail de vérification et de caractérisation opérationnelle. C'est moins "
        "qu'une découverte, et c'est exactement le geste attendu d'un service : mesurer ce "
        "qu'un produit rend sur le grain qui décide, et dire s'il faut le brancher.\n")
    return "\n".join(texte)


def bloc_mqi(lignes: list[dict]) -> str:
    """La conformité FAIRMODE, au temps d'agrégation que le référentiel impose."""
    chemin = RACINE / "reports/mqi_bon_grain.csv"
    if not chemin.exists():
        return ""
    t = pd.read_csv(chemin)
    libelles = {"max_8h": "max journalier 8 h", "horaire": "horaire",
                "moyenne_jour": "moyenne journalière"}
    texte = [
        "## 5. Conformité FAIRMODE\n",
        "MQI au sens de JRC120649 v3.2 (DOI 10.2760/30226), formule `RMSE / (β · RMS_U)`, "
        "β = 2, conformité à **MQI ≤ 1**. Le temps d'agrégation est celui que le tableau 6 "
        "impose **par polluant** — et non l'horaire pour les trois, comme le dossier le "
        "faisait auparavant.\n",
        "| polluant | grain imposé | n | MQI CAMS brut | MQI correction | *(MQI horaire, "
        "hors cadre)* |", "|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        texte.append(
            f"| {NOM[r['polluant']]} | {libelles[r['grain_fairmode']]} | {int(r['n']):,} | "
            f"{r['mqi_cams']:.3f} | **{r['mqi_nous']:.3f}** | "
            f"{r['mqi_horaire_cams']:.3f} / {r['mqi_horaire_nous']:.3f} |")
        lignes.append({"bloc": "MQI FAIRMODE", "polluant": r["polluant"],
                       "grain": r["grain_fairmode"], "n": int(r["n"]),
                       "mqi_cams": r["mqi_cams"], "mqi_nous": r["mqi_nous"]})
    texte.append(
        "\nLes six valeurs agrégées sont conformes, avec une marge large. **Aucun produit ne "
        "change de côté du seuil** entre les deux grains : l'énoncé de conformité déjà publié "
        "tenait, seul le chiffre cité était le mauvais.\n"
        "\n⚠️ **Mais l'agrégat masque une non-conformité sur le NO₂.** Station par station "
        "(842 couples mesurés) : **100 %** des stations conformes en O₃ et en PM2,5, mais "
        "**98,5 %** seulement en NO₂ — pire MQI **1,24**, et 95 % de conformité sur les "
        "stations **trafic**. Le MQI national ne doit donc pas être cité comme une conformité "
        "station par station pour le NO₂ ; c'est exactement la compensation entre cas faciles "
        "et difficiles qu'un agrégat peut cacher.\n"
        "\nLe MQI horaire était **pessimiste** — l'agrégation journalière réduit la variance "
        "de l'erreur davantage que celle de l'incertitude de mesure, qui dépend surtout du "
        "niveau observé. L'erreur jouait donc contre nous, ce qui explique qu'elle n'ait rien "
        "déclenché. Elle rendait néanmoins l'énoncé infondé, et un jury FAIRMODE l'aurait "
        "vue.\n"
        "\n**Deux paramètres à connaître si la question vient** : l'α de PM2,5 vaut **0,30** "
        "et celui de PM10 **0,13** — les intervertir sur-estime le MQI de PM2,5 de 2 à 20 %, "
        "et c'est une erreur qui a été commise dans ce projet puis corrigée. La v4.0 du "
        "référentiel (mai 2026) refond les β par polluant ; les chiffres ci-dessus sont en "
        "**v3.2**, et le dossier le dit plutôt que de laisser deviner.\n")
    return "\n".join(texte)


def bloc_duel_prevair(lignes: list[dict]) -> str:
    """Le duel DIRECT — nos sorties contre les leurs, mêmes stations, mêmes jours.

    La § 10 ter compare via le rapport LCSQA : deux publications, deux protocoles, et il
    faut neutraliser le confondant d'amont. Ici, rien à neutraliser — les trois systèmes
    sont évalués sur **exactement les mêmes lignes**.

    ⚠️ Et c'est payé d'une fenêtre minuscule. PREV'AIR n'expose que ~6 jours glissants ;
    l'archivage quotidien n'a démarré que fin juillet 2026, donc **le passé n'est pas
    récupérable**. Dix jours ne concluent rien : c'est un ordre de grandeur, et toute
    citation qui omet la fenêtre est fausse.

    Régénéré par `scripts/duel_prevair.py --polluant <P>`.
    """
    fs = {p: RACINE / f"reports/duel_prevair_{p}.csv" for p in ("O3", "NO2", "PM10", "PM25")}
    tables = {p: pd.read_csv(f) for p, f in fs.items() if f.exists()}
    if not tables:
        return ""

    texte = [
        "## 10 quater. Le duel DIRECT — nos sorties contre PREV'AIR, mêmes stations, "
        "mêmes jours\n",
        "Aucun confondant d'amont à neutraliser ici : les trois systèmes sont évalués sur "
        "**exactement les mêmes lignes**. Grain aligné sur le produit PREV'AIR "
        "(`MAXJ1` pour O₃ et NO₂, `MOYJ1` pour les particules), échéance **J+1**.\n",
        "| polluant | fenêtre | lignes | CAMS brut | **nous** | PREV'AIR | écart PREV'AIR / nous |",
        "|---|---|---|---|---|---|---|",
    ]
    for p, t in tables.items():
        r = {str(x["systeme"]): x for _, x in t.iterrows()}
        nous = next((v for k, v in r.items() if k.startswith("notre")), None)
        pv = next((v for k, v in r.items() if k.startswith("PREV")), None)
        brut = next((v for k, v in r.items() if k.startswith("CAMS")), None)
        if nous is None or pv is None or brut is None:
            continue
        ecart = 100 * (float(pv["rmse"]) / float(nous["rmse"]) - 1)
        # L'espace des milliers s'applique au NOMBRE seul : un `.replace(",", " ")` sur la
        # ligne entière avalait aussi la virgule de « PM2,5 », qui devenait « PM2 5 ».
        n_fmt = f"{int(nous['n']):,}".replace(",", " ")
        texte.append(
            f"| {NOM.get(p, p)} | {int(nous['jours'])} j · {nous['debut']}→{nous['fin']} "
            f"| {n_fmt} | {float(brut['rmse']):.2f} | "
            f"**{float(nous['rmse']):.2f}** | {float(pv['rmse']):.2f} | "
            f"**+{ecart:.1f} %** |")
        lignes.append({"bloc": "duel PREV'AIR", "polluant": p,
                       "grain": str(nous["grain"]), "n": int(nous["n"]),
                       "gain": round(ecart, 2), "relatif_pct": float(nous["rmse"])})

    jmax = max(int(t["jours"].iloc[0]) for t in tables.values())
    texte.append(
        f"\n🔴 **{jmax} jours NE CONCLUENT RIEN.** C'est un ordre de grandeur, et le script "
        f"le réaffirme à chaque exécution. PREV'AIR n'expose qu'une fenêtre glissante "
        f"d'environ six jours et notre archivage quotidien n'a démarré que fin juillet "
        f"2026 : **le passé n'est pas récupérable**, cette fenêtre ne grandira que d'un "
        f"jour par jour.\n")
    texte.append(
        "⚠️ **Deux réserves qui jouent dans des sens opposés, et il faut les dire ensemble.** "
        "*Contre nous* : PREV'AIR tourne à 1,7 km **avec assimilation et krigeage**, nous "
        "corrigeons un ensemble à 10 km. *Pour nous* : nos stations sont connues de notre "
        "modèle — mais les leurs le sont aussi de leur krigeage, donc l'avantage n'est pas "
        "unilatéral.\n")
    texte.append(
        "⚠️ **Ce duel n'utilise PAS la pile complète** — seulement `base + tendance + "
        "typologie`. GEOS-CF, les membres d'ensemble et les feux sont **hors d'atteinte sur "
        "cette fenêtre** : leurs flux s'arrêtent au 01/08/2026 pour les deux premiers et à "
        "juin 2025 pour les feux. C'est une limite de **fraîcheur**, pas de conception — et "
        "elle rend ces écarts **minorants**.\n")
    return "\n".join(texte)


def bloc_seuils_2030(lignes: list[dict]) -> str:
    """Le mur réglementaire, chiffré localement — et le calcul que personne n'avait fait.

    La directive (UE) 2024/2881 rend la modélisation obligatoire là où un seuil est dépassé,
    ET divise les valeurs limites annuelles par deux au 1ᵉʳ janvier 2030. Le produit des deux
    n'est écrit nulle part : abaisser le seuil **multiplie mécaniquement** le nombre de zones
    où modéliser devient une obligation légale.

    Régénéré par `scripts/seuils_2030.py`.
    """
    f = RACINE / "reports/seuils_2030.csv"
    if not f.exists():
        return ""
    g = pd.read_csv(f)
    VL = {"NO2": (40, 20), "PM10": (40, 20), "PM25": (25, 10)}

    def u(d, col):
        return int(d.loc[d[col], "station_id"].nunique())

    texte = [
        "## 5 bis. Le seuil 2030 — combien de stations basculent sans qu'un gramme "
        "de plus soit émis\n",
        "Valeurs limites en **moyenne annuelle**, année **2025** (dernière année pleine), "
        "taux de saisie recalculé ≥ 75 %. L'**ozone est exclu** : il n'a pas de valeur "
        "limite annuelle mais une valeur cible sur le maximum 8 h — l'y comparer n'aurait "
        "aucun sens réglementaire.\n",
        "| polluant | VL actuelle | VL **2030** | stations évaluées | > actuelle | "
        "> **2030** | **basculent** |",
        "|---|---|---|---|---|---|---|",
    ]
    for p, (va, v30) in VL.items():
        s = g[g["polluant"] == p]
        if s.empty:
            continue
        texte.append(f"| {NOM.get(p, p)} | {va} µg/m³ | **{v30} µg/m³** | {len(s)} | "
                     f"{int(s['depasse_actuel'].sum())} | **{int(s['depasse_2030'].sum())}** "
                     f"| {int(s['bascule'].sum())} |")
        lignes.append({"bloc": "seuil 2030", "polluant": p, "grain": "moyenne annuelle",
                       "n": len(s), "gain": float(s["depasse_2030"].sum()),
                       "relatif_pct": float(s["depasse_actuel"].sum())})

    a, b, tot = u(g, "depasse_actuel"), u(g, "depasse_2030"), int(g["station_id"].nunique())
    texte.append(
        f"\n**En union sur les trois polluants : {a} station(s) en dépassement aujourd'hui, "
        f"{b} en 2030** — un facteur **{b / max(a, 1):.1f}**, sur {tot} stations évaluées "
        f"({b / tot:.0%} du parc). **Aucune émission n'a changé : seul le seuil a bougé.**\n")

    occ = g[g["region"] == 76]
    if not occ.empty:
        ao, bo = u(occ, "depasse_actuel"), u(occ, "depasse_2030")
        deps = set(occ["departement"].dropna().astype(int))
        sans = sorted({9, 11, 12, 30, 31, 32, 34, 46, 48, 65, 66, 81, 82} - deps)
        texte.append(
            f"**Occitanie** : {ao} → **{bo}** stations, sur {int(occ['station_id'].nunique())} "
            f"évaluées. Et **{len(sans)} des 13 départements n'ont aucune station retenue** "
            f"({', '.join(f'{d:02d}' for d in sans)}) : pour eux, la conformité 2030 **ne peut "
            f"pas être posée depuis la mesure**. C'est exactement le cas que la directive "
            f"confie à la modélisation.\n")
        lignes.append({"bloc": "seuil 2030", "polluant": "Occitanie", "grain": "union",
                       "n": int(occ["station_id"].nunique()), "gain": float(bo),
                       "relatif_pct": float(ao)})

    texte.append(
        "⚠️ **Ce que ce tableau ne dit pas** : les moyennes de 2025 ne sont pas une "
        "prévision de 2030. Les émissions baisseront d'ici là. Il mesure une chose et une "
        "seule — **l'effet du changement de seuil, à air constant** — ce qui est exactement "
        "la question qu'une collectivité doit se poser aujourd'hui pour préparer sa feuille "
        "de route.\n")
    return "\n".join(texte)


def bloc_meteo(lignes: list[dict]) -> str:
    """Ce que le modèle se refuse — mesuré, et à ne jamais citer comme un gain."""
    presents = [p for p in ("O3", "NO2", "PM25")
                if (RACINE / f"reports/apport_meteo_{p}.csv").exists()]
    if not presents:
        return ""
    texte = [
        "## 6. Le plafond de la météo — ce que le modèle se refuse\n",
        "Le modèle évalué dans tout ce document n'utilise **aucune variable "
        "météorologique** : ses 53 prédicteurs sont tous disponibles à l'heure d'émission. "
        "Le tableau ci-dessous mesure ce que coûte ce choix, en ajoutant les variables ERA5 "
        "au même protocole — mêmes plis par stations exclues, mêmes hyperparamètres.\n",
        "| polluant | RMSE base | gain | relatif | IC95 (bootstrap de stations) | décile "
        "haut |", "|---|---|---|---|---|---|"]
    for polluant in presents:
        t = pd.read_csv(RACINE / f"reports/apport_meteo_{polluant}.csv", index_col=0)
        ic = pd.read_csv(RACINE / f"reports/apport_meteo_{polluant}_ic.csv")
        r = ic[ic["jeu"].str.contains("enrichie")].iloc[0]
        base = float(t.loc["base (actuel)", "rmse"])
        texte.append(
            f"| {NOM[polluant]} | {base:.3f} | **+{r['gain']:.3f}** | "
            f"**+{100 * r['gain'] / base:.1f} %** | [{r['ic_bas']:+.3f} ; "
            f"{r['ic_haut']:+.3f}] | {r['cout_queue']:+.2f} *(meilleur)* |")
        lignes.append({"bloc": "plafond météo", "polluant": polluant, "grain": "max_8h",
                       "n": 0, "gain": r["gain"], "relatif_pct": 100 * r["gain"] / base})
    texte.append(
        "\nLes trois intervalles sont strictement positifs et **le décile haut s'améliore "
        "partout** : il n'y a pas d'arbitrage entre erreur moyenne et épisodes, ce qui est "
        "rare dans ce projet.\n"
        "\n⚠️ **C'est un plafond, jamais un gain.** ERA5 est une **réanalyse** : elle n'existe "
        "pas à l'heure d'émission. Une chaîne opérationnelle emploierait les prévisions IFS et "
        "en récupérerait une part inconnue, décroissante avec l'échéance. Ne jamais citer ces "
        "chiffres comme une performance du modèle — ils mesurent ce dont il se prive pour "
        "rester opérationnellement propre.\n"
        "\n### Un défaut de notre propre critère d'arrêt\n"
        "\nLe critère du projet — « retenir si le gain atteint **0,3 µg/m³** » — est en unités "
        "**absolues**, appliqué à des polluants dont le RMSE varie d'un facteur 5. Pour PM2,5 "
        "(RMSE ≈ 3) ce seuil vaut 10 % ; pour NO₂ (RMSE ≈ 15) il vaut 2 %. Il **écarte** donc "
        "PM2,5 à +6,7 % relatifs tout en **retenant** NO₂ à +2,7 %.\n"
        "\nCe n'est pas un arbitrage scientifique, c'est un artefact d'unité. Le critère doit "
        "devenir relatif, ou être fixé par polluant. Le défaut n'est apparu que parce que la "
        "mesure a porté sur les trois polluants à la fois.\n")
    return "\n".join(texte)


def bloc_perimetres(lignes: list[dict]) -> str:
    """Les deux usages, qui n'ont ni les mêmes entrées ni la même revendication."""
    presents = [p for p in ("O3", "NO2", "PM25")
                if (RACINE / f"reports/apport_observation_veille_{p}_ic.csv").exists()]
    if not presents:
        return ""
    texte = [
        "## 7. Deux périmètres, et il ne faut jamais citer l'un pour l'autre\n",
        "Une observation passée n'existe **qu'aux stations instrumentées**. L'ajouter aux "
        "prédicteurs scinde le projet en deux usages qui n'ont ni les mêmes entrées ni la même "
        "revendication.\n",
        "| usage | entrées | ce qu'on peut prétendre |",
        "|---|---|---|",
        "| **A — corriger aux stations** | + observations à J−2 | comparable au MOS officiel "
        "**sur son terrain**, qui les utilise aussi |",
        "| **B — prédire là où rien ne mesure** | sans | **la seule revendication propre du "
        "projet** |\n",
        "Règle de disponibilité retenue, volontairement conservatrice : **rien de plus récent "
        "que la fin de J−2**, soit au moins 24 h de marge sur l'heure d'émission. Plus strict "
        "que le produit officiel ; si le gain existe sous cette contrainte, il existe *a "
        "fortiori* sous une règle plus permissive. Couverture **97,7 à 98,5 %**, fraîcheur "
        "médiane 2 jours.\n",
        "| polluant | usage B (sans) | usage A (avec) | gain | relatif | IC95 | décile haut |",
        "|---|---|---|---|---|---|---|"]
    for polluant in presents:
        t = pd.read_csv(RACINE / f"reports/apport_observation_veille_{polluant}.csv",
                        index_col=0)
        ic = pd.read_csv(RACINE / f"reports/apport_observation_veille_{polluant}_ic.csv").iloc[0]
        b = t.loc["B — sans observation"]
        a = t.loc["A — avec observations passées"]
        texte.append(
            f"| {NOM[polluant]} | {b['rmse']:.3f} | **{a['rmse']:.3f}** | "
            f"+{ic['gain']:.3f} | **+{ic['relatif_pct']:.1f} %** | "
            f"[{ic['ic_bas']:+.3f} ; {ic['ic_haut']:+.3f}] | "
            f"{a['rmse_decile_haut'] - b['rmse_decile_haut']:+.2f} |")
        lignes.append({"bloc": "périmètres", "polluant": polluant, "grain": "max/moyenne jour",
                       "n": 0, "gain": ic["gain"], "relatif_pct": ic["relatif_pct"]})
    texte.append(
        "\nLes trois intervalles sont strictement positifs et **le décile haut s'améliore "
        "partout**. Sur le NO₂ le gain atteint **+21,9 %**, et la queue s'améliore de "
        "5,5 µg/m³ — cohérent avec un polluant dominé par des sources très locales que CAMS "
        "résout mal à 8 × 11 km.\n"
        "\n**C'est le plus fort levier mesuré du projet, et le seul qui soit déployable** : il "
        "ne demande aucune réanalyse, aucun téléchargement, et le MOS officiel de Copernicus "
        "s'en sert déjà — sa documentation le dit.\n"
        "\n### L'erreur de raisonnement que cela corrige\n"
        "\nLe projet excluait les observations récentes **au même titre** que la météo de "
        "réanalyse. Ce n'est pas le même argument : ERA5 décrit le présent depuis le futur, la "
        "mesure d'avant-hier est publiée. Une prudence appliquée par **analogie** plutôt que "
        "par examen a coûté ce levier pendant tout le projet — et elle ne levait aucune erreur, "
        "une entrée exclue à tort étant invisible.\n"
        "\n### Ce que cela répare dans la comparaison au produit officiel\n"
        "\nElle était **asymétrique dans les deux sens** : à notre avantage sur le grain — nous "
        "apprenons la grandeur réglementaire, eux l'horaire — et à notre désavantage sur les "
        "entrées, puisqu'ils avaient les observations récentes et nous pas. L'usage A permet "
        "enfin la comparaison à armes égales.\n")
    return "\n".join(texte)


def _col(t: pd.DataFrame, nom: str, chemin) -> pd.Series:
    """Désigner une colonne par son nom, et lever si elle manque (`CLAUDE.md` § 2 bis § 1)."""
    if nom not in t.columns:
        raise SystemExit(f"{chemin} : colonne '{nom}' absente — colonnes lues : {list(t.columns)}")
    return t[nom]


def _ligne_unique(t: pd.DataFrame, colonne: str, motif: str, chemin) -> pd.Series:
    """Une ligne désignée par un motif qui n'en sélectionne QU'UNE.

    Zéro correspondance et deux correspondances sont **toutes deux** des erreurs — c'est
    précisément la faute que `CLAUDE.md` § 2 bis interdit (« la première colonne qui n'est
    ni… ni… » avait sélectionné `level`, constante à 0).
    """
    r = t[_col(t, colonne, chemin).astype(str).str.startswith(motif)]
    if len(r) != 1:
        raise SystemExit(f"{chemin} : {len(r)} ligne(s) pour '{motif}' dans '{colonne}' — "
                         f"il en faut exactement 1. Valeurs : {list(t[colonne])}")
    return r.iloc[0]


def bloc_reconciliation(lignes: list[dict]) -> str:
    """Les cinq familles de gains, rapprochées — le risque n° 1 en entretien.

    Le projet produit cinq familles de scores qui portent des noms voisins et mesurent des
    choses différentes. Sur l'ozone elles valaient, **au 08/08/2026**, +22,43 %, +22,47 %,
    +15,83 %, +9,24 % et +3,31 % : **toutes justes, aucune interchangeable.** Jusqu'ici
    elles ne se croisaient dans aucun document — seulement dans une fiche de mémoire, ce
    qui est exactement le statut que ce fichier existe pour refuser.

    ⚠️ Ces cinq valeurs sont **datées à dessein** : elles illustrent l'écart, elles ne le
    définissent pas. La table publiée est recalculée depuis les CSV à chaque exécution, et
    l'ajout de l'étage `tendance` le 08/08 a déplacé deux d'entre elles (② +21,66 → +22,47,
    ③ +13,75 → +15,83) — assez pour que ② passe devant ①a. Un chiffre d'illustration non
    daté devient un chiffre faux sans prévenir.

    ⚠️ Tout est **recalculé depuis les CSV**. Une version antérieure de la table de
    réconciliation portait « +27,09 % O₃ » recopié d'une fiche de tableau de bord et non
    d'une mesure : ces valeurs étaient périmées et ne correspondaient à aucune colonne des
    fichiers. *Un chiffre recopié d'une fiche n'est pas un chiffre vérifié.*
    """
    POLLUANTS = ("O3", "NO2", "PM10", "PM25")

    def prod(p: str) -> tuple[float, float, str] | None:
        f = RACINE / f"reports/production_reelle_{p}_h1.csv"
        if not f.exists():
            return None
        t = pd.read_csv(f)
        r = _ligne_unique(t, "systeme", "notre modèle — moyenne des sept pertes", f)
        return (float(r["gain_vs_aasqa_pct"]), float(r["gain_vs_cams_pct"]),
                f"{r['mois_debut']}→{r['mois_fin']}")

    def maxi(p: str) -> tuple[float, float, int, str] | None:
        f = RACINE / f"reports/methode_maximale_{p}_h2.csv"
        if not f.exists():
            return None
        t = pd.read_csv(f)
        aux = _ligne_unique(t, "configuration", "★ MAXIMALE — AUX STATIONS", f)
        par = _ligne_unique(t, "configuration", "★ MAXIMALE — PARTOUT", f)
        return (float(aux["gain_pct"]), float(par["gain_pct"]),
                int(par["n_mois"]), str(par["fenetre"]))

    def aveugle(p: str) -> tuple[float, int] | None:
        f = RACINE / f"reports/double_aveugle_journalier_{p}.csv"
        if not f.exists():
            return None
        t = pd.read_csv(f)
        r = t[(_col(t, "epreuve", f) == "double aveugle")
              & (_col(t, "reglage", f) == "défaut")]
        if len(r) != 1:
            raise SystemExit(f"{f} : {len(r)} ligne(s) « double aveugle / défaut », il en faut 1")
        return float(r.iloc[0]["gain_pct"]), int(r.iloc[0]["n_plis"])

    def veille(p: str) -> float | None:
        f = RACINE / f"reports/apport_observation_veille_{p}_ic.csv"
        return float(pd.read_csv(f).iloc[0]["relatif_pct"]) if f.exists() else None

    src = {p: (prod(p), maxi(p), aveugle(p), veille(p)) for p in POLLUANTS}
    src = {p: v for p, v in src.items() if any(x is not None for x in v)}
    if not src:
        return ""

    def c(x, fmt="{:+.2f} %") -> str:
        # Virgule décimale : c'est LA section destinée à être recopiée telle quelle dans une
        # diapositive ou une phrase d'entretien. Le reste du document est mixte.
        return "—" if x is None else fmt.format(x).replace(".", ",")

    # La fourchette de l'ozone était ÉCRITE EN DUR — « +3,31 % à +22,43 % ». L'étage
    # `tendance`, ajouté le 08/08, l'a rendue fausse sans que rien ne lève : ② est passé de
    # +21,66 à +22,47 %, donc AU-DESSUS de ①a, et la borne haute citée n'était plus la
    # bonne famille. Un chiffre recopié dans la prose d'un générateur est exactement ce que
    # le docstring de cette fonction interdit — on le dérive donc des mêmes valeurs que le
    # tableau. ①b est exclu : c'est une variante de dénominateur d'①a, pas une 6ᵉ famille.
    o = src.get("O3")
    familles_o3 = [x for x in ((o[0][0] if o and o[0] else None),   # ①a production
                               (o[1][0] if o and o[1] else None),   # ②  maximale + veille
                               (o[1][1] if o and o[1] else None),   # ③  maximale PARTOUT
                               (o[3] if o else None),               # ④  veille seule
                               (o[2][0] if o and o[2] else None))   # ⑤  base sans levier
                   if x is not None]
    fourchette = (f"de **{c(min(familles_o3))} à {c(max(familles_o3))}** selon l'épreuve"
                  if len(familles_o3) >= 2 else "beaucoup selon l'épreuve")

    texte = [
        "## 7 ter. Les cinq familles de gains — laquelle citer, et jamais l'une pour l'autre\n",
        "Ce projet produit **cinq familles de scores** qui portent des noms voisins et "
        "répondent à des questions différentes. Elles sont **toutes justes et aucune n'est "
        f"interchangeable** : sur l'ozone, la même correction vaut {fourchette}. "
        "Confondre deux lignes de ce tableau discrédite le dossier entier "
        "plus sûrement qu'un chiffre faux — un chiffre faux se corrige, une confusion de "
        "périmètre jette le doute sur tout le reste.\n",
        "**Tout pourcentage cité hors de ce document doit venir avec trois mots : "
        "périmètre · épreuve · échéance.**\n",
        "| # | famille | épreuve | échéance | "
        + " | ".join(NOM[p] for p in src) + " |",
        "|---|---|---|---|" + "---|" * len(src)]

    def ligne(num, nom, epreuve, ech, get, gras=False) -> None:
        cells = []
        for p, v in src.items():
            x = get(v)
            s = c(x)
            cells.append(f"**{s}**" if (gras and x is not None) else s)
            if x is not None:
                lignes.append({"bloc": "réconciliation", "polluant": p, "grain": nom,
                               "n": 0, "gain": float("nan"), "relatif_pct": x})
        texte.append(f"| {num} | {nom} | {epreuve} | {ech} | " + " | ".join(cells) + " |")

    ligne("①a", "**production, contre la chaîne en service** ⭐", "origine glissante, "
          "station **connue**", "**J0**", lambda v: v[0][0] if v[0] else None, gras=True)
    ligne("①b", "production, contre CAMS brut", "idem", "J0",
          lambda v: v[0][1] if v[0] else None)
    ligne("②", "**maximale — AUX STATIONS**", "double aveugle, pile complète **+ veille**",
          "J+2", lambda v: v[1][0] if v[1] else None)
    ligne("③", "**maximale — PARTOUT** ⭐", "double aveugle, **sans** la veille",
          "J+2", lambda v: v[1][1] if v[1] else None, gras=True)
    ligne("④", "apport de la seule observation de la veille (§ 7)", "usage A contre usage B",
          "J+2", lambda v: v[3])
    ligne("⑤", "double aveugle de référence", "base seule, **aucun levier**", "J+2",
          lambda v: v[2][0] if v[2] else None)

    corpus = []
    for p, v in src.items():
        bouts = []
        if v[0]:
            bouts.append(f"① {v[0][2]}")
        if v[1]:
            bouts.append(f"②③ {v[1][3]} ({v[1][2]} mois)")
        if v[2]:
            bouts.append(f"⑤ {v[2][1]} plis")
        corpus.append(f"**{NOM[p]}** : " + ", ".join(bouts))
    texte.append("\n**Les corpus ne coïncident pas** — " + " · ".join(corpus)
                 + ". Les niveaux ne se comparent donc pas d'une ligne à l'autre ; seuls les "
                   "écarts **internes à une même ligne** le peuvent.\n")
    texte.append(
        "### Comment les lire sans se tromper\n"
        "\n- **① n'est comparable à aucune des autres.** Il est mesuré à **J0** et la station "
        "évaluée est **connue du modèle**. C'est l'usage « exploitation sur un réseau "
        "existant », pas une mesure de généralisation. Ne jamais l'opposer à un double aveugle.\n"
        "- **③ est la seule revendication propre du projet** — prédire là où rien ne mesure. "
        "C'est le chiffre à mettre en avant, et **c'est le plus bas** : c'est précisément ce "
        "qui le rend crédible.\n"
        "- **② − ③ mesure l'apport de la veille**, et ce faisant **change de périmètre**. ④ "
        "mesure la même chose sur un autre corpus : les deux se recoupent, ils ne "
        "s'additionnent pas.\n"
        "- **⑤ → ③ est la démonstration de la méthode** : ce que la pile complète ajoute à "
        "une base sans levier, à protocole d'épreuve identique. La comparaison est "
        "**indicative, pas rigoureuse** — les deux lignes n'ont ni le même corpus ni le même "
        "nombre de plis. La comparaison **rigoureuse** est interne à ③ : la ligne « base » de "
        "`methode_maximale_<P>_h2.csv`, mesurée sur exactement les mêmes plis que le total.\n"
        "\n### Les échéances ne sont pas les mêmes partout\n"
        "\n`methode_maximale` est à **J+2** ; `detection_maximale`, `episodes_reels` et "
        "`agregation_zone` sont à **J0** (`horizon=1`) ; les bancs FAIRMODE et LCSQA à "
        "**J+1** ; les pages HTML de production à **J0**. Un jury demandera « à quelle "
        "échéance ? » et la réponse **change selon le tableau montré**. Le rassurant est "
        "mesuré — moins d'un point d'écart entre J0, J+1 et J+2 — mais cela **se dit**, "
        "jamais ne se laisse découvrir.\n")
    return "\n".join(texte)


def bloc_comparaison_annuelle(lignes: list[dict]) -> str:
    """Le tableau de la page 04 — année par année, contre DEUX dénominateurs.

    Pourquoi cette section a dû être écrite
    ---------------------------------------
    Elle manquait. La page 04 de la présentation est le plus gros tableau du dossier et
    citait +13,26 %, +3,65 %, +21,32 %, +16,75 %, +22,64 %, +37,64 % — **aucun de ces
    chiffres n'existait ici**, et `verite_dossier.py` ne lisait même pas
    `comparaison_annuelle.csv`. Par la règle que ce fichier énonce lui-même en tête, ils
    étaient donc « à retirer ou à re-mesurer ». C'est la récidive exacte du défaut trouvé à
    l'audit du 05/08 sur les cinq résultats du 04-05/08.

    Les deux dénominateurs, et pourquoi les deux
    --------------------------------------------
    **Contre CAMS brut** — dénominateur commun aux trois systèmes, donc le seul qui permette
    de les *ordonner*. Mais personne n'exploite CAMS brut en l'état : le citer flatterait
    tout le monde, nous compris.

    **Contre la chaîne en service** — le krigeage du biais récent dans ses *réglages usuels*,
    ce qu'une AASQA fait réellement tourner. C'est le chiffre qui se *cite*. Et à côté, le
    gain contre la **même méthode réglée au mieux**, adversaire plus dur partout sauf sur
    l'ozone, où le krigeage dégrade CAMS.

    ⚠️ Cette inversion de l'ozone est exactement pourquoi un pourcentage exige ses trois
    mots : notre +11,88 % contre CAMS devient +22,64 % contre la chaîne, **sans qu'aucun
    modèle ait changé**. C'est la référence qui a bougé.
    """
    chemin = RACINE / "reports/comparaison_annuelle.csv"
    if not chemin.exists():
        return ""
    t = pd.read_csv(chemin)
    # Exiger nommément les colonnes avant d'écrire (`CLAUDE.md` § 2 ter § 2) : une colonne
    # absente s'imprimerait `nan %` sans que rien ne s'en émeuve.
    ATTENDUES = ("polluant", "annee", "n", "rmse_cams", "rmse_usuel", "rmse_aasqa",
                 "rmse_nous", "gain_nous_pct", "gain_service_pct", "gain_service_opt_pct")
    if manque := [c for c in ATTENDUES if c not in t.columns]:
        raise SystemExit(f"{chemin.name} : colonnes absentes {manque} — "
                         f"relancer scripts/page_comparaison_annuelle.py")
    texte = [
        "## 7 quater. Année par année, contre **deux dénominateurs** — la table de la page 04\n",
        "**Périmètre : PARTOUT** — aucune observation passée de la station n'entre dans le "
        "modèle, donc ces chiffres valent *là où rien ne mesure*. Épreuve : **double "
        "aveugle**, station et mois cachés ensemble. Échéance **J+1** (tranche 25-48 h "
        "d'une sortie 00 UTC). Ces trois mots ne s'omettent pas : ils ne sont **pas** ceux "
        "du § 12 ni ceux du § 14.\n",
        "Deux références, parce qu'elles répondent à deux questions. **Contre CAMS brut** "
        "pour *ordonner* les systèmes — dénominateur commun, mais personne n'exploite CAMS "
        "brut en l'état. **Contre la chaîne en service** pour *citer* un chiffre — le "
        "krigeage du biais récent dans ses **réglages usuels**, ce qu'une AASQA fait "
        "tourner. La dernière colonne oppose la **même méthode réglée au mieux**, "
        "adversaire plus dur.\n",
        "| polluant | fenêtre | n | CAMS brut | chaîne en service | nous | /CAMS | "
        "**/service** | /service réglé |",
        "|---|---|---|---|---|---|---|---|---|"]
    for p, sous in t.groupby("polluant", sort=False):
        for _, r in sous.iterrows():
            an = str(r["annee"])
            total = an == "toutes"
            g = "**" if total else ""
            texte.append(
                f"| {g}{p}{g} | {g}{an}{g} | {int(r['n']):,} | {r['rmse_cams']:.2f} | "
                f"{r['rmse_usuel']:.2f} | {r['rmse_nous']:.2f} | "
                f"{r['gain_nous_pct']:+.2f} % | {g}{r['gain_service_pct']:+.2f} %{g} | "
                f"{r['gain_service_opt_pct']:+.2f} % |")
            if total:
                lignes.append({"bloc": "comparaison annuelle", "polluant": p,
                               "grain": "toutes années", "n": int(r["n"]),
                               "rmse_brut": r["rmse_cams"], "rmse_service": r["rmse_usuel"],
                               "rmse_nous": r["rmse_nous"],
                               "gain_vs_brut": r["gain_nous_pct"],
                               "gain_vs_service": r["gain_service_pct"],
                               "gain_vs_service_regle": r["gain_service_opt_pct"]})
    texte.append(
        "\n⚠️ **Les deux blocs de colonnes ne se lisent pas ensemble.** Sur l'ozone, la "
        "chaîne AASQA **dégrade** CAMS brut : notre gain passe de **+11,88 %** contre CAMS "
        "à **+22,64 %** contre elle, *sans qu'aucun modèle ait changé*. C'est la référence "
        "qui a bougé — et c'est exactement pourquoi un pourcentage se cite avec ses trois "
        "mots (§ 7 ter).\n")
    texte.append(
        "⚠️ **Les PM10 sont publiés en deux variantes, et les deux sont légitimes.** Les "
        "membres d'ensemble n'existent pour ce polluant que depuis 2025-01, d'où deux "
        "tables. « PM10 » est la variante **longue — 31 mois**, chaîne réglementaire "
        "**ancrée sur CAMS** faute de membres ; « PM10 · chaîne nommée » est la variante "
        "**courte — 19 mois**, CHIMERE+MOCAGE réel. La longue est à la fois le plus grand "
        "corpus **et** le test le plus dur : son substitut atteint une RMSE de **7,20** "
        "contre **7,63** pour la chaîne nommée. **Le même modèle, sur les mêmes 19 mois, "
        "rend le même +20,2 % contre CAMS brut dans les deux tables** — seule la référence "
        "change. Ne jamais publier l'une en taisant l'autre.\n")
    texte.append(
        "⚠️ **La réserve porte sur les deux dénominateurs.** Les lignes AASQA s'ancrent sur "
        "des modèles en configuration **européenne 0,1° sans assimilation**. La chaîne "
        "réelle tourne en version nationale, plus fine et assimilée : elle est donc "
        "**meilleure** que cette simulation, et tout écart affiché ici est un **majorant** "
        "de notre avance. Le § 10 ter chiffre cet écart sur les journées de PREV'AIR réel "
        "captées.\n")
    return "\n".join(texte)


def bloc_detection(lignes: list[dict]) -> str:
    """Le rappel à budget de fausses alertes imposé — la comparaison qu'un service utilise."""
    chemin = RACINE / "reports/detection_maximale_O3.csv"
    hors = RACINE / "reports/detection_2025_O3.csv"
    if not chemin.exists():
        return ""
    t = pd.read_csv(chemin)
    no2 = compte_depassements_no2()
    texte = [
        "## 8. Détection — à budget de fausses alertes égal\n",
        "Un service ne choisit pas un seuil pour maximiser un score : il subit un **budget de "
        "fausses alertes**, au-delà duquel une alerte cesse d'être écoutée. La comparaison "
        "utile est donc *à taux de fausse alerte fixé, qui rappelle le plus ?* — et non « qui "
        "a le meilleur score à son propre seuil optimal ».\n",
        "Le point de fonctionnement est choisi **hors échantillon**, sur d'autres stations que "
        "celles évaluées.\n",
        "| budget | CAMS brut | correction | **correction + obs. passées** |",
        "|---|---|---|---|"]
    for budget in sorted(t["budget"].unique()):
        s = t[t["budget"] == budget].set_index("produit")["POD"]
        def _v(k):
            v = s.get(k)
            return f"{v:.3f}" if pd.notna(v) else "*inatteignable*"
        texte.append(f"| ≤ {budget:.0%} | {_v('CAMS brut')} | {_v('régression')} | "
                     f"**{_v('régression + obs')}** |")
        lignes.append({"bloc": "détection", "polluant": "O3", "grain": f"FAR<={budget}",
                       "n": 0, "pod_brut": s.get("CAMS brut"),
                       "pod_corrige": s.get("régression + obs")})
    texte.append(
        "\n**À 30 % de fausses alertes : 0,656 contre 0,184 — 3,6 fois plus de dépassements "
        "réels détectés.** À 20 %, 6,6 fois. Et CAMS brut n'atteint jamais 10 % : quel que "
        "soit son seuil, son taux de fausse alerte reste au-dessus.\n")

    if hors.exists():
        texte += [
            "### Le facteur se reproduit hors fenêtre d'apprentissage\n",
            "Modèle appris jusqu'au 31/12/2024, **seuils calibrés sur 2024**, appliqués en "
            "aveugle au 1ᵉʳ semestre 2025.\n",
            "| budget | 17 mois appris | 2025, jamais vu |", "|---|---|---|",
            "| ≤ 20 % | 6,6× | **6,8×** |", "| ≤ 30 % | 3,6× | **3,5×** |",
            "| ≤ 40 % | 2,0× | **1,9×** |",
            "\nLes taux de fausse alerte **constatés** sur 2025 (0,030 à 0,165) restent sous "
            "les budgets visés : les seuils calibrés sur 2024 sont conservateurs.\n"
            "\n**La distinction que cela établit** : la précision ponctuelle généralise mal "
            "dans le temps — +1,1 % en saison ozone, prospectif strict — mais le **classement "
            "des jours par risque** généralise bien. *Le modèle sait ordonner ce qu'il ne sait "
            "pas chiffrer*, et c'est l'ordre qui décide d'une alerte.\n"
            "\n⚠️ L'échantillon 2025 reste petit — 21 stations, ~160 dépassements. La "
            "**reproduction des facteurs** est plus informative que leur valeur.\n"]

    complet = RACINE / "reports/detection_complete_O3.csv"
    if complet.exists():
        t = pd.read_csv(complet)
        s = t[t["budget"] == 0.30].set_index("produit")["POD"]
        t25 = pd.read_csv(RACINE / "reports/detection_complete_PM25.csv")
        s25 = t25[t25["budget"] == 0.30].set_index("produit")["POD"]
        texte += [
            "### Les leviers s'additionnent — et aucun ne se noie dans le précédent\n",
            "Rappel à **30 % de fausses alertes**, point de fonctionnement choisi hors "
            "échantillon.\n",
            "| produit | O₃ | PM2,5 |", "|---|---|---|"]
        for nom in ("CAMS brut", "correction", "+ observations J−2",
                    "+ membres d'ensemble", "+ feux"):
            def _v(serie):
                v = serie.get(nom)
                return f"{v:.3f}" if pd.notna(v) else "*budget inatteignable*"
            gras = "**" if nom == "+ feux" else ""
            texte.append(f"| {gras}{nom}{gras} | {gras}{_v(s)}{gras} | {gras}{_v(s25)}{gras} |")
            lignes.append({"bloc": "détection empilée", "polluant": "O3+PM25",
                           "grain": nom, "n": 0, "pod_o3": s.get(nom),
                           "pod_pm25": s25.get(nom)})
        texte.append(
            "\nSur l'ozone, **3,5 fois le CAMS brut** à 30 % de budget, **5,6 fois** à 20 %. "
            "Sur PM2,5, le brut n'atteint aucun de ces budgets.\n"
            "\n**Un résultat qui contredit le RMSE** : les six membres d'ensemble sont **nuls "
            "en RMSE sur l'ozone** — gain négatif, IC contenant zéro — et valent pourtant ici "
            "autant que les observations passées sur PM2,5 (+0,067 de rappel). *Une variable "
            "peut n'apporter rien à la précision ponctuelle et beaucoup au classement des jours "
            "à risque.* Tester en détection ce qui a été écarté sur le RMSE, et réciproquement.\n")

    texte.append(
        "### Les trois polluants ne sont pas dans la même situation\n"
        "\n| polluant | seuil | dépassements | meilleur rappel à 30 % de fausses alertes |\n"
        "|---|---|---|---|\n"
        "| **O₃** | 120 µg/m³ (max 8 h) | 2 293 sur 134 423 (1,71 %) | **0,656** — 3,6× le brut |\n"
        "| **PM2,5** | 25 µg/m³ (moyenne jour) | 1 844 sur 105 744 (1,74 %) | **0,485** — le brut n'atteint pas ce budget |\n"
        "| **NO₂** | 120 µg/m³ (max horaire) | **270 sur 161 637 (0,17 %)** | **aucun budget ≤ 40 % atteignable** ; 0,044 à 40 % |\n"
        f"\n**Le NO₂ n'est pas détectable à ce grain**, et ce n'est pas un défaut de méthode : "
        f"l'événement est dix fois plus rare que pour les deux autres. Au seuil d'information "
        f"horaire de {no2['seuil']:.0f} µg/m³, le panel unifié ne compte que "
        f"**{no2['n_depassements']} dépassements** sur {no2['n_jours_station']:,} jours-station "
        f"({no2['debut']} → {no2['fin']}, {no2['n_stations']} stations, règle des 75 %) — le "
        f"problème n'existe pas. Ce constat confirme, avec un protocole plus net, ce que le "
        f"projet avait déjà mesuré (POD 0,084, Brier skill +0,017).\n"
        "\n*Un seuil sans événements ne mesure pas une incapacité à détecter : il mesure "
        "l'absence de ce qu'on cherche. Compter les positifs avant de conclure.*\n"
        "\n**Une différence entre polluants** : sur PM2,5 la perte pondérée **aide** (0,485 "
        "contre 0,437 pour la régression simple), alors qu'elle est neutre sur l'ozone. Le "
        "choix de la perte dépend donc du polluant, ce qu'une mesure sur l'ozone seul aurait "
        "laissé croire universel.\n"
        "\n### Trois techniques qui n'apportent rien, une fois le seuil libre\n"
        "\n| technique | avantage annoncé | d'où il venait |\n|---|---|---|\n"
        "| classification | POD 0,483 → 0,641 | la régression était seuillée à **120 µg/m³**, "
        "valeur qu'un moindre carré n'atteint presque jamais |\n"
        "| perte pondérée | queue −3,1 % → +3,1 % | mesuré **à seuil fixe** |\n"
        "| quantile 0,90 | écarté sur RMSE 20,90 | RMSE est un critère de prédiction "
        "**ponctuelle**, pas de détection |\n"
        "\nMesurées à budget de fausses alertes égal et seuil choisi hors échantillon, les "
        "trois s'effacent : 0,656 pour la régression pondérée contre 0,656 pour la régression "
        "simple, 0,573 pour le quantile, 0,622 pour la classification. **Ce qui décide est "
        "l'ordre des jours par risque, pas la fonction de perte.**\n"
        "\n*Note* : maximiser le F1 ≡ maximiser le CSI, puisque `F1 = 2·CSI/(1+CSI)` est "
        "strictement croissante. La précision seule est un objectif dégénéré.\n")
    return "\n".join(texte)


def bloc_signalements(lignes: list[dict]) -> str:
    """Le décompte des signalements — ce qu'un service aurait publié, jour par jour."""
    chemin = RACINE / "reports/heatmap_annuelle_O3.csv"
    if not chemin.exists():
        return ""
    import sys as _sys
    _sys.path.insert(0, str(RACINE / "scripts"))
    from calendrier_signalements import selectionner  # noqa: E402

    d = pd.read_csv(chemin, parse_dates=["jour"])
    texte = [
        "## 9. Les signalements, comptés — France et Occitanie\n",
        "Les blocs précédents mesurent des erreurs. Celui-ci compte ce qu'un service aurait "
        "**publié** : le nombre de jours-station dépassant 120 µg/m³ en maximum journalier 8 h, "
        "sur 2024. C'est la traduction du RMSE en unité de décision.\n",
        "| périmètre | produit | jours-station | jours avec ≥1 signalement | pic (stations le "
        "même jour) |", "|---|---|---|---|---|"]
    for perimetre, libelle in (("france", "France (270 stations)"),
                               ("occitanie", "Occitanie (21 stations)")):
        sous = selectionner(d, perimetre)
        for colonne, nom in (("obs_jour", "**la vérité**"),
                             ("officiel_mos", "MOS officiel"),
                             ("nous", "notre correction complète")):
            if colonne not in sous:
                continue
            s = sous[sous[colonne] >= 120.0].groupby("jour").size()
            total, jours, pic = int(s.sum()), int(len(s)), int(s.max()) if len(s) else 0
            reference = int((sous["obs_jour"] >= 120.0).sum())
            part = f" ({100 * total / reference:.0f} %)" if colonne != "obs_jour" else ""
            texte.append(f"| {libelle} | {nom} | {total:,}{part} | {jours} | {pic} |")
            lignes.append({"bloc": "signalements", "polluant": "O3", "grain": perimetre,
                           "n": total, "produit": nom, "jours": jours, "pic": pic})
    texte.append(
        "\n**Le produit officiel annonce 21 % des jours-station en France, et 7 % en "
        "Occitanie.** L'écart régional est cohérent avec la ventilation saisonnière du bloc 2 : "
        "il est en défaut sur la fenêtre ozone, et l'Occitanie est une région où l'ozone estival "
        "domine.\n"
        "\n**Le pic est le chiffre le plus parlant.** La vérité monte à 106 stations le même "
        "jour en France ; le produit officiel plafonne à 26. Il ne rate pas seulement des jours, "
        "il rate l'**ampleur** de ceux qu'il détecte. Notre correction atteint 91 — elle "
        "retrouve la forme des grands épisodes.\n"
        "\n⚠️ **La comparaison lui est favorable sur un point** : nos prédictions sont hors "
        "échantillon, chaque station prédite par un modèle qui ne l'a jamais vue, tandis que le "
        "produit officiel utilise les observations récentes de ces mêmes stations.\n"
        "\nFigures : `reports/figures/calendrier_france.html` et `calendrier_occitanie.html`.\n")
    return "\n".join(texte)


def bloc_front(lignes: list[dict]) -> str:
    """Le front précision–rappel — la seule comparaison qui ne dépende pas d'un seuil."""
    fichiers = {a: RACINE / f"reports/front_precision_rappel_O3_{a}.csv"
                for a in (2024, 2025)}
    if not all(f.exists() for f in fichiers.values()):
        return ""
    texte = [
        "## 10. Le front précision–rappel — à qualité d'annonce identique\n",
        "Comparer deux détecteurs par leur **nombre d'annonces** ne dit rien : un produit "
        "bruyant en émet davantage et paraît meilleur. La comparaison qui vaut est à "
        "**précision fixée**, ou à **rappel fixé**.\n",
        "| | précision | rappel | fausses alertes |", "|---|---|---|---|",
        "| **2025 — Occitanie, hors échantillon** (3 183 jours-station, 160 dépassements) | "
        "| | |",
        "| MOS officiel, seuil réglementaire | 68,5 % | 46,2 % | 34 |",
        "| nous, seuil réglementaire | **97,1 %** | 42,5 % | **2** |",
        "| **nous, à sa précision** | 68,7 % | **76,9 %** | 56 |",
        "| nous, à son rappel | **94,0 %** | 49,4 % | **5** |",
        "| **2024 — France, stations exclues** (72 372 jours-station, 918 dépassements) | "
        "| | |",
        "| MOS officiel | 61,2 % | 15,8 % | 92 |",
        "| nous, seuil réglementaire | 76,9 % | 47,1 % | 130 |",
        "| **nous, à sa précision** | 61,9 % | **64,1 %** | 362 |",
        "| nous, à son rappel | **96,7 %** | 16,1 % | **5** |",
        "\n> À **qualité d'annonce identique**, nous détectons **1,7 fois plus** de "
        "dépassements hors échantillon et **4,1 fois plus** sur la France. À **rappel "
        "identique**, nous produisons **5 fausses alertes contre 92**.\n",
        "Le front **domine** : à tout point de fonctionnement du produit officiel, nous sommes "
        "strictement meilleurs sur l'autre axe. C'est le seul résultat du projet qui se dise "
        "sans réserve d'axe.\n",
        "**Traduction pour un service** : à 68,5 % de précision — la sienne aujourd'hui — il "
        "passerait de **46 % à 77 % des épisodes détectés**, sans dégrader la qualité de ses "
        "annonces.\n",
        "⚠️ **Deux réserves.** Le seuil est balayé sur les données évaluées : c'est un front, "
        "pas un point de fonctionnement validé — la version calibrée hors échantillon figure au "
        "bloc 8. Et le produit officiel utilise les observations récentes de ces stations, ce "
        "que notre variante « usage B » ne fait pas.\n",
        "\n### Le réentraînement continu ne comble pas l'écart\n",
        "Le produit officiel est réentraîné en continu, notre modèle est figé au 31/12/2024. "
        "Réentraîné mensuellement avec tout l'historique jusqu'à J−2, le gain est de "
        "**−0,02 µg/m³** — nul. L'Occitanie n'ajoute que 2 903 jours-station à un socle de "
        "131 097, soit 2 %. Le levier est réel en principe, **vide faute de volume** — et il le "
        "serait aussi pour une AASQA, dont le réseau régional est petit.\n"]
    lignes.append({"bloc": "front", "polluant": "O3", "grain": "précision égale",
                   "n": 3183, "rappel_nous": 0.769, "rappel_officiel": 0.462})
    return "\n".join(texte)


def bloc_generalisation() -> str:
    """Ce qui est démontré, et ce qui ne l'est pas — sans arrondir."""
    return (
        "## 10 ter. La barre réelle — PREV'AIR, et non CAMS brut\n\n"
        "Tout ce document compare à **CAMS brut**, que les AASQA ne consomment pas : elles "
        "reçoivent **PREV'AIR**. Le rapport *Performances Prev'air en 2024* (J. Salles "
        "Loustau, INERIS/LCSQA, publié le 08/04/2026) donne enfin cette barre.\n\n"
        "⚠️ **Le grain n'est pas le nôtre.** Le rapport précise p. 17 : « seul le **maximum "
        "journalier** d'ozone est ainsi considéré », donc le maximum horaire et non le "
        "maximum glissant 8 h. Nos 9,53 µg/m³ ne s'y comparent pas. Il a fallu recalculer "
        "sur leur grain. Le reste des conventions concorde : stations de **fond** (288 chez "
        "eux, 254 chez nous), filtre à 75 %, fenêtre avril–septembre.\n\n"
        "| | RMSE | biais | corrélation |\n|---|---|---|---|\n"
        "| MOCAGE (J0, 288 stations) | 14,6 | +0,14 | 0,70 |\n"
        "| CHIMERE brut (J0) | 13,9 | +4,2 | 0,67 |\n"
        "| **AS-CHI** — adaptation statistique en production | **13,3** | +3,1 | **0,74** |\n"
        "| CAMS brut (J+1, 254 stations) | 11,08 | −2,02 | 0,822 |\n"
        "| **notre correction** | **8,84** | **+0,05** | **0,880** |\n\n"
        "⚠️ **Ne jamais citer 8,84 contre 13,3.** CAMS brut est déjà à 11,08 contre 13,9 pour "
        "CHIMERE brut : une part de l'écart vient de l'**amont**, et c'est attendu — CAMS "
        "Europe est une médiane d'ensemble de neuf à onze modèles dont CHIMERE lui-même.\n\n"
        "**La seule comparaison défendable oppose chaque correction à son propre brut :**\n\n"
        "| | brut | corrigé | gain de la correction |\n|---|---|---|---|\n"
        "| PREV'AIR (CHIMERE → AS-CHI), **ozone** | 13,9 | 13,3 | **+4,3 %** |\n"
        "| ce projet (CAMS → nous), **ozone** | 11,08 | 8,84 | **+20,2 %** |\n\n"
        "Cette lecture neutralise le confondant d'amont **et** celui des DROM, inclus dans "
        "leur moyenne France avec une RMSE avoisinant 20 mais affectant les deux lignes "
        "également. Deux écarts jouent **contre** nous, donc ne fragilisent pas la "
        "conclusion : leurs scores sont à **J0** et les nôtres à **J+1** ; et notre 8,84 "
        "vient de plis `i % 3`, optimistes — au protocole bloqué le gain descendrait vers "
        "13-14 %.\n\n"
        "### 🔴 « +4,3 % » est un chiffre d'OZONE, et le lire comme leur performance "
        "générale est faux\n\n"
        "Le même rapport donne les trois autres polluants. Extraits de sa prose, pas de ses "
        "figures — p. 19, 29, 39 et 45, à J0, France :\n\n"
        "| polluant | MOCAGE | CHIMERE brut | **AS-CHI** | **gain de LEUR adaptation** |\n"
        "|---|---|---|---|---|\n"
        "| O₃ *(avril–septembre)* | 14,6 | 13,9 | 13,3 | **+4,3 %** |\n"
        "| NO₂ | 17,5 | 16,7 | 11,2 | **+32,9 %** |\n"
        "| PM10 | 7,8 | 9,9 | 4,7 | **+52,5 %** |\n"
        "| PM2,5 | 5,80 | 7,65 | 3,05 | **+60,1 %** |\n\n"
        "**Sur les trois autres polluants, leur adaptation gagne davantage que la nôtre sur "
        "l'ozone.** Le résultat n'est donc pas « nous faisons cinq fois mieux » : c'est que "
        "**l'ozone est le polluant où l'adaptation statistique paie le moins — pour eux "
        "comme pour nous**. Citer +4,3 % sans dire « sur l'ozone » est la faute que le "
        "§ 7 ter interdit, commise contre un tiers.\n\n"
        "### Ce qu'est AS-CHI, et pourquoi ça explique tout le reste\n\n"
        "**AS-CHI est un krigeage, pas un apprentissage.** L'hypothèse est que la "
        "concentration vaut CHIMERE **plus un résidu aléatoire, décorrélé du modèle mais "
        "spatialement structuré**. Ce résidu — l'« innovation » — est calculé **aux "
        "stations** comme mesure moins modèle, puis interpolé : krigeage ordinaire à "
        "l'origine, **krigeage à dérive externe depuis 2010**, qui ajuste localement une "
        "relation linéaire entre observations et CHIMERE.\n\n"
        "Ce mécanisme rend cohérents trois faits mesurés qui paraissaient sans lien :\n\n"
        "1. **Leur avantage s'effondre avec l'échéance** — jusqu'à devenir négatif dès J2 "
        "sur la RMSE. Un champ d'innovations est un instantané&nbsp;: plus la prévision est "
        "lointaine, moins il s'applique. **Nos leviers, eux, ne se dégradent pas avec "
        "l'horizon** (moins d'un point entre J0, J+1 et J+2), parce que le biais corrigé est "
        "une propriété du **site**, pas de l'échéance.\n"
        "2. **Ils gagnent énormément sur les particules** (+52 %, +60 %) : le résidu des PM "
        "est fortement structuré dans l'espace, donc très krigeable à courte portée.\n"
        "3. **Ils gagnent peu sur l'ozone** (+4,3 %) : l'ozone est régionalement homogène — "
        "il y a peu de structure spatiale résiduelle à interpoler.\n\n"
        "> **La différence de nature compte plus que l'écart de score.** Le krigeage exige "
        "des **observations au moment de la correction** : il fonctionne près des stations "
        "et se dégrade là où le réseau est lâche. Notre correction apprend le résidu à "
        "partir de variables **disponibles à l'heure d'émission** — terrain, calendrier, "
        "typologie, autres modèles — donc elle existe **là où aucune station n'existe**. "
        "C'est précisément le cas des **43 EPCI sans station à moins de 30 km** et des "
        "**4 départements d'Occitanie sans station retenue** (§ 5 bis).\n\n"
        "⚠️ **Et c'est aussi pourquoi le duel aux stations leur est favorable** : leur "
        "krigeage *utilise* les observations des stations sur lesquelles on l'évalue. "
        "L'avantage n'est pas unilatéral — le nôtre les connaît par apprentissage — mais il "
        "n'est pas symétrique non plus.\n\n"
        "### 🔴 Pourquoi ce dossier ne rejoue PAS sa correction sur leur fenêtre 2024\n\n"
        "La tentation est forte : leur rapport porte sur une **année entière**, nos duels "
        "directs sur **onze jours**. Mesuré le 11/08/2026, c'est impossible sans fausser la "
        "comparaison **contre nous** :\n\n"
        "| polluant | notre corpus démarre | mois d'entraînement AVANT 2024-01 |\n"
        "|---|---|---|\n"
        "| O₃ · NO₂ · PM2,5 | 2023-06 | **7** *(10 avant avril)* |\n"
        "| **PM10** | **2024-01** | **0** |\n\n"
        "Sur PM10 le corpus **commence** quand leur fenêtre commence — et ses membres "
        "d'ensemble n'existent qu'à partir de **2025-01**. Sur l'ozone, les dix mois "
        "disponibles ne contiennent qu'**un seul été partiel**. Une évaluation 2024 "
        "opposerait **notre année la plus mal entraînée** à **leur système de production en "
        "régime normal**.\n\n"
        "> *S'infliger un protocole plus dur que celui de la référence n'est pas de la "
        "prudence : c'est fausser la comparaison contre soi, ce qui est aussi peu "
        "informatif que la fausser en sa faveur.* Le duel direct de la § 10 quater, malgré "
        "ses onze jours, a l'avantage décisif que 2024 n'aurait pas : **les deux systèmes y "
        "tournent dans leur régime normal**.\n\n"
        "✅ Les autres « capteurs » sont en revanche **disculpés** : GEOS-CF, feux, météo et "
        "TROPOMI couvrent bien les douze mois de 2024, comme les membres d'ensemble d'O₃, "
        "NO₂ et PM2,5. Seul PM10 est privé des siens.\n\n"
        "### Le motif qui se répète, et c'est le vrai résultat\n\n"
        "> « l'amélioration apportée par l'adaptation statistique diminue au fur et à mesure "
        "des échéances, jusqu'à une légère **dégradation** des performances pour l'AS par "
        "rapport au modèle brut à partir de J2 pour la RMSE » — *Performances Prev'air en "
        "2024*, p. 22\n\n"
        "C'est **exactement** ce que ce dossier mesure sur le MOS de Copernicus : dégradation "
        "huit mois sur douze, −19,6 % en saison ozone. Deux post-traitements officiels, deux "
        "chaînes différentes — CHIMERE et CAMS —, le **même retournement**. Ce n'est plus "
        "l'anomalie d'un produit, c'est un motif de la famille de méthodes.\n\n"
        "## 10 bis. Le dossier lu dans les conventions d'une AASQA\n\n"
        "Nos scores sont des **RMSE groupées** sur tous les couples station–temps réunis. Un "
        "rapport AASQA conforme au référentiel LCSQA calcule autre chose : **stations de fond "
        "seules**, disponibilité **≥ 75 %** (opérateur large, comme le pseudo-code du "
        "référentiel technique national), score temporel **par station puis moyenne non "
        "pondérée des stations**, échéances séparées, ozone limité à **avril–septembre**. "
        "Comparer nos chiffres à un rapport d'AASQA sans ce recalcul serait comparer deux "
        "grandeurs différentes.\n\n"
        "Recalculé sur les stations de fond passant le seuil de disponibilité, échéance "
        "J+1 :\n\n"
        "| polluant | n stations | CAMS brut | notre correction | gain **AASQA** | gain ML "
        "groupé | écart |\n|---|---|---|---|---|---|---|\n"
        "| O₃ | 254 | 10,062 | **7,879** | **+21,7 %** | +21,9 % | −0,2 pt |\n"
        "| NO₂ | 217 | 15,458 | **10,101** | **+34,7 %** | +36,3 % | −1,6 pt |\n"
        "| PM2,5 | 156 | 3,936 | **2,772** | **+29,6 %** | +26,4 % | **+3,2 pt** |\n"
        "| **PM10** | 191 | 6,349 | **4,236** | **+33,3 %** | +32,7 % | +0,6 pt |\n\n"
        "⚠️ **Les PM10 n'apparaissent pas au tableau principal** (§ 1) : celui-ci "
        "compare au post-traitement officiel de Copernicus, que le projet n'a pas "
        "téléchargé pour ce polluant. Le chiffre ci-dessus est donc une comparaison à "
        "**CAMS brut seul**, sur 19 mois appariés (2024-01 → 2026-08) et non sur la "
        "fenêtre 2024 des trois autres — à ne pas aligner sans le dire.\n\n"
        "Le biais y est le plus parlant : CAMS **sous-estime les PM10 de 2,08 µg/m³** "
        "en moyenne sur les stations de fond ; la correction ramène ce biais à "
        "**+0,04** et la corrélation de 0,689 à **0,866**. C'est le polluant qui porte "
        "**40 des 52 vigilances** réellement déclarées en Occitanie.\n\n"
        "**Le changement de convention joue dans les deux sens.** L'audit supposait que la "
        "RMSE groupée nous flattait : c'est vrai pour le NO₂ (−1,6 point), **faux pour les "
        "PM2,5** où la convention AASQA nous est plus favorable de 3,2 points, et négligeable "
        "pour l'ozone. Ce n'est pas un biais systématique mais une dépendance au polluant — "
        "et elle n'était pas prévisible sans la calculer.\n\n"
        "Le résultat le plus démonstratif du dossier apparaît dans cette convention : sur les "
        "**150 stations urbaines de fond**, CAMS sous-estime le NO₂ de **−11,6 µg/m³** en "
        "biais moyen ; notre correction ramène ce biais à **−0,5** et la RMSE de 17,7 à "
        "**11,0**.\n\n"
        "Ventilation par zone, O₃ puis NO₂ — RMSE (biais) :\n\n"
        "| zone | O₃ CAMS | O₃ nous | NO₂ CAMS | NO₂ nous |\n|---|---|---|---|---|\n"
        "| urbaine | 9,790 (+0,62) | **7,670** (+0,41) | 17,674 (**−11,59**) | "
        "**10,975** (−0,51) |\n"
        "| périurbaine | 9,736 (+0,29) | **7,701** (−0,25) | 13,692 (−7,52) | "
        "**9,934** (+0,88) |\n"
        "| rurale | **11,192 (−2,54)** | **8,650** (−0,43) | 5,130 (+0,45) | "
        "5,142 (+1,22) |\n\n"
        "Deux lectures opposées, et les deux comptent. Sur l'**ozone**, le rural est la zone "
        "la moins bien traitée — CAMS y sous-estime de 2,5 µg/m³ et la correction, qui efface "
        "ce biais, y reste la moins performante ; ce sont les stations les plus isolées, donc "
        "celles où le voisinage n'aide pas, ce que la validation par plis bloqués (§ 11) "
        "mesure par ailleurs. Sur le **NO₂ en rural**, à l'inverse, **la correction n'apporte "
        "rien** (5,142 contre 5,130) et dégrade légèrement le biais : là où CAMS est déjà "
        "juste — niveau bas, aucune source locale —, il n'y a rien à corriger.\n\n"
        "⚠️ **Les seuils d'information français ne sont pas évaluables sur cette fenêtre.** "
        "À 180 µg/m³ en maximum horaire, l'ozone compte **32 dépassements sur 60 400 "
        "jours-station** : CAMS en détecte 3, notre correction 2 à J+1, et **aucun des deux "
        f"à J+3**. Le NO₂ à 200 µg/m³ en compte **{compte_depassements_no2()['n_depassements']} "
        f"sur {compte_depassements_no2()['n_jours_station']:,}** — mesurés sur le panel unifié, "
        "et non sur la fenêtre de cette section —, aucun détecté. Un modèle entraîné "
        "**directement** sur le maximum horaire donne le même résultat qu'une transposition "
        "depuis le grain 8 h : l'échec est mécanique, pas méthodologique. **Et il n'est pas une affaire de calibration** : mesurée, la pente de régression de l'observé sur le prédit vaut **1,007** — le modèle n'est pas contracté, son échelle est juste. Une calibration isotone du score vers les bandes de l'indice, décidée au coût attendu minimal avec pénalité asymétrique, n'apporte que **+1,2 point** de rappel contre un simple abaissement de seuil à budget de fausses annonces égal — sous la barre de bruit de ±2 points. Le rang du régresseur porte déjà toute la décision disponible. Ce qui manque est de l'**information** : 53 prédicteurs qui ne contiennent rien distinguant un jour à 175 µg/m³ d'un jour à 185, et 32 événements pour l'apprendre. **Notre facteur 3,6× porte sur la valeur cible européenne (120 µg/m³, "
        "max 8 h), jamais sur le seuil de procédure.**\n\n"
        "⚠️ **PM10 : lacune de périmètre, pas de donnée.** Le projet n'a jamais ingéré les "
        "PM10, ni en observation ni en prévision. Or sur les **52 vigilances réellement "
        "déclarées** par ATMO Occitanie entre janvier 2025 et mars 2026, **40 portent sur les "
        "PM10** et 12 sur l'ozone. Le déclenchement opérationnel se fait donc aux trois "
        "quarts sur un polluant hors de notre périmètre. Les PM2,5 à 25 µg/m³ répondent à une "
        "autre question et ne les remplacent pas.\n\n"
        "⚠️ **Les vigilances déclarées sont une cible, jamais un prédicteur.** Mesuré : "
        "l'historique est diffusé vers 9h40 **le matin de la journée qu'il concerne** "
        "(médiane +10,0 h après l'échéance, **aucune** ligne disponible avant). L'utiliser en "
        "entrée d'une prévision J+1 serait la faute reprochée à ERA5.\n\n"
        "## 11. Ce que la validation démontre, et ce qu'elle ne démontre pas\n\n"
        "| propriété | mesure | verdict |\n|---|---|---|\n"
        "| Généralisation **spatiale** (stations exclues) | **+29,7 %**, σ 1,2, aucun pli "
        "négatif | ✅ démontrée |\n"
        "| Généralisation **temporelle** (mois caché) | +6,7 %, pire pli **−35,5 %**, "
        "5 négatifs sur 17 | ❌ non démontrée |\n"
        "| **Blocage conjoint** station × mois | **+1,5 %**, pire **−41,4 %**, "
        "**8 négatifs sur 17** | ⚠️ marginale |\n"
        "| **Prospectif strict** (rolling-origin) | **+6,3 %**, pire **−7,3 %**, "
        "4 négatifs sur 16 | ⚠️ voir ci-dessous |\n"
        "| Détection de dépassement, hors échantillon | CSI 0,495 (officiel 0,387) | "
        "✅ à seuil calibré |\n\n"
        "| Généralisation spatiale, **plis bloqués** (≥ 50 km) | **+18,5 %** contre "
        "+28,6 % non bloqué | ⚠️ chiffrée ci-dessous |\n\n"
        "### Le blocage spatial des plis — l'optimisme, mesuré\n\n"
        "Le protocole du projet construit ses plis par `i % n` sur l'identifiant de station. "
        "C'est arbitraire, et surtout **non bloqué spatialement**. **Les distances dépendent du polluant, et il faut donner celle de la "
        "population évaluée.** Sur les 813 stations de métropole toutes espèces confondues, "
        "le plus proche voisin est à 2,4 km en médiane ; mais la population qui mesure "
        "l'ozone n'en compte que 270, plus dispersées "
        "(**médiane 14,3 km**, 39 % sous 10 km). Pour le NO₂ : 340 stations, **4,1 km**, "
        "66 % sous 10 km. Pour les PM2,5 : 227 stations, 12,3 km, 45 %.\n\n"
        "En regroupant les stations par k-moyennes et en sortant des **grappes entières** — "
        "la fuite tombe de 79 % à **3 %** — puis en creusant un fossé de 50 km autour du "
        "test :\n\n"
        "| polluant | plis `i % n` | blocs seuls | fossé 50 km | voisin médian |\n|---|---|---|---|---|\n"
        "| O₃ | +28,60 % | +19,21 % | **+18,47 %** | 14,3 km |\n"
        "| PM2,5 | +28,37 % | — | **+20,64 %** | 12,3 km |\n"
        "| NO₂ | +33,14 % | — | **+30,96 %** | 4,1 km |\n\n"
        "### Le rayon du fossé, choisi par la donnée et non par le score\n\n"
        "Les rayons de 25 puis 50 km avaient été **essayés**, donc choisis après avoir "
        "vu les résultats — ce qui n'est pas un protocole. Le rayon juste se lit dans "
        "la **portée de l'autocorrélation des résidus** : au-delà, une station voisine "
        "n'informe plus. Mesurée sur les couples de stations partageant au moins "
        "120 jours :\n\n"
        "| polluant | corrélation des résidus à 0–5 km | portée (r < 0,1) | perte au blocage |\n|---|---|---|---|\n"
        "| O₃ | **0,647** | **150 km** | −10,1 pts |\n"
        "| PM2,5 | 0,499 | 150 km | −7,7 pts |\n"
        "| NO₂ | **0,262** | 75 km | −2,2 pts |\n\n"
        "**La perte au blocage est monotone dans cette corrélation.** L'explication "
        "n'est donc pas la densité du réseau mais la **portée** : une voisine de NO₂ "
        "à 2 km ne renseigne presque rien sur le résidu (0,26), une voisine d'ozone à "
        "50 km en renseigne encore un tiers (0,32). Les résidus de **CAMS brut** sont "
        "bien plus corrélés (0,85 sur l'ozone) que ceux de la correction : celle-ci "
        "**absorbe** une part de la structure spatiale, ce qu'on lui demande.\n\n"
        "### La décomposition, avec son témoin\n\n"
        "Au rayon justifié de **150 km**, le gain ozone tombe à **+10,46 %**. Mais un "
        "fossé de 150 km retire **127 stations d'entraînement par pli sur 180** : une "
        "part de la chute est de la **famine de données**, pas de la fuite supprimée. "
        "Le témoin — retirer autant de stations **au hasard**, sans blocage — le "
        "sépare :\n\n"
        "| protocole (O₃) | gain | ce que l'écart isole |\n|---|---|---|\n"
        "| `i % 3` | +28,60 % | — |\n"
        "| blocs spatiaux, jeu complet | +19,21 % | **−9,4 pts de fuite** |\n"
        "| blocs + retrait **aléatoire** de 127 stations | +16,20 % | **−3,0 pts de volume** |\n"
        "| blocs + fossé 150 km | +10,46 % | −8,8 pts, dont 3,0 de volume |\n\n"
        "**Corrigé du confondant de volume, le gain à indépendance spatiale réelle vaut "
        "environ +13,5 %.** Ni +18,5 % — fossé trop court — ni +10,5 % — confondu par la "
        "perte de données. C'est le premier chiffre de ce dossier qui soit décomposé.\n\n"
        "⚠️ **L'explication par la proximité ne tient pas.** Le NO₂ a les stations les "
        "**plus serrées** (4,1 km) et c'est lui qui **résiste le mieux** au blocage ; l'ozone, "
        "trois fois plus dispersé, perd le plus. C'est l'inverse de ce qu'une explication par "
        "le voisinage prédit. Une première version du dossier affirmait ce mécanisme : il est "
        "retiré, et l'écart reste **mesuré mais inexpliqué**.\n\n"
        "⚠️ **Cela n'invalide aucune comparaison.** Tous les produits — CAMS, MOS officiel, "
        "nos variantes — sont évalués sur les mêmes plis ; le front précision–rappel, les "
        "mesures d'apport et les ablations gardent leur valeur. Ce qui bouge est le chiffre "
        "**absolu**, et seulement pour l'usage *prédire là où rien ne mesure*. Publier les "
        "deux, en nommant l'usage de chacun.\n\n"
        "**« Station inconnue » signifie *autre station du même réseau*, pas *lieu "
        "quelconque*.** Deux stations d'une même maille reçoivent la **même** valeur CAMS ; "
        "l'écart de leurs résidus est donc exactement l'écart de leurs observations — vérifié "
        "à l'identique dans les données. Cette divergence intra-maille vaut **3,61 µg/m³** en "
        "**médiane des écarts-types horaires par maille**, et **6,1 µg/m³** en moyenne sur "
        "paires journalières (IC95 par bootstrap de maille [5,0 ; 7,6]). La distribution est "
        "très asymétrique, d'où l'écart entre les deux résumés : **citer lequel des deux, "
        "toujours.**\n\n"
        "⚠️ **Ce n'est pas un « plancher », et le mot a été retiré du dossier.** Trois raisons, "
        "chacune vérifiée :\n"
        "\n1. la divergence mélange différence de support, gradients urbains réels, bruit "
        "instrumental et sélection du réseau — rien n'établit qu'aucune méthode ne descende "
        "sous cette valeur ;\n"
        "2. la décomposition par strates ne trouve **qu'une seule typologie exploitable** "
        "(fond) : le réseau ne fournit presque aucune paire trafic ou industrielle dans une "
        "même maille, et l'IC reste large (~40 % de la moyenne) ;\n"
        "3. l'ancienne formule « 26 % du RMSE » comparait une **médiane d'écarts-types** à un "
        "**RMSE** — deux grandeurs non commensurables. Elle est retirée.\n\n"
        "*Nuance mesurée au passage : l'écart-type intra-maille du résidu **corrigé** dépasse "
        "souvent celui du résidu brut. C'est attendu — la correction donne des valeurs "
        "différentes à des stations que CAMS traite à l'identique — mais cela signifie aussi "
        "qu'elle peut sur-différencier.*\n\n"
        "**Une part du gain accompagne le défaut du forçage.** En partageant les jours à la "
        "médiane du RMSE de CAMS, la correction rend **+14,0 %** quand le forçage est bon "
        "contre **+23,6 %** quand il dérive.\n\n"
        "⚠️ **Cet écart est en partie arithmétique, et il faut le dire.** Avec `e = Y − CAMS` "
        "et `m` la correction prédite, `ΔMSE = e² − (e − m)² = 2em − m²`. Stratifier les jours "
        "par l'erreur **réalisée** de CAMS sélectionne donc directement le premier terme : un "
        "gain plus grand là où l'erreur brute est grande est en partie mécanique, puisqu'il y "
        "a davantage de perte réductible. La corrélation de **+0,953** en ΔMSE partage sa "
        "variable explicative avec le gain qu'elle explique.\n\n"
        "L'énoncé défendable est donc : *la correction retire davantage de perte sur les cas "
        "où CAMS s'avère mauvais ; nous n'avons pas montré qu'elle **anticipe** une dérive.* "
        "Trancher exigerait une stratification **ex ante** — version de la chaîne, dispersion "
        "inter-membres, contrôle de processus — ne contenant pas l'observation.\n\n"
        "⚠️ **Ne pas citer le +0,913** mesuré sur les deux ruptures des 13/11 et 03/12/2024 : "
        "il repose sur 5 paires de mois et son leave-one-out descend à **+0,135**. Le +0,953 "
        "en ΔMSE le remplace.\n\n"
        "Ce que cela ne dit **pas** : que la correction nuit quand le forçage est juste. Elle "
        "gagne encore +14,0 % — elle gagne moins, elle ne nuit pas, sauf ponctuellement.\n")



def bloc_pile_complete(lignes: list[dict]) -> str:
    """L'empilement cumulatif de tous les leviers — le seul chiffre de synthèse honnête.

    La somme des apports isolés donnerait un total très supérieur, et faux : deux leviers
    qui captent la même information ne s'additionnent pas.
    """
    fs = {p: RACINE / f"reports/methode_maximale_{p}_h2.csv"
          for p in ("NO2", "O3", "PM10", "PM25")}
    presents = {p: f for p, f in fs.items() if f.exists()}
    if not presents:
        return ""
    tables = {p: pd.read_csv(f) for p, f in presents.items()}
    texte = [
        "## 12. La pile complète — ce que valent tous les leviers ensemble\n",
        "Double aveugle **station ET mois cachés**, J+2, fenêtre du flux GEOS-CF v1. "
        "L'ordre des étages est **déclaré avant la mesure** : le réordonner après coup "
        "flatterait un étage choisi. Deux périmètres qui ne se confondent jamais — "
        "**PARTOUT** (utilisable là où aucune station n'existe) et **AUX STATIONS** "
        "(exige l'historique du point). ERA5 figure **hors méthode** : c'est une réanalyse, "
        "elle n'existe pas quand la prévision est émise, son gain est un **plafond**.\n",
        "| étage | " + " | ".join(NOM[p] for p in tables) + " |",
        "|---" * (len(tables) + 1) + "|"]
    etages = list(next(iter(tables.values()))["configuration"])
    for e in etages:
        cells = []
        for p, tb in tables.items():
            r = tb[tb["configuration"] == e]
            if r.empty:
                cells.append("—"); continue
            r = r.iloc[0]
            m = r["apport_marginal_pct"]
            gras = "**" if str(e).startswith("★") else ""
            # Sur une ligne d'ablation, `apport_marginal_pct` est l'écart à la ligne
            # PRÉCÉDENTE, donc à une autre ablation : il ne veut rien dire. L'afficher
            # publierait un chiffre faux. L'apport réel — MAXIMALE − ablation — est
            # recalculé en § 12 bis, et c'est le seul à citer.
            if "(ablation)" in str(e):
                cells.append(f"{r['gain_pct']:+.2f} %")
            else:
                cells.append(f"{gras}{r['gain_pct']:+.2f} %{gras}"
                             + ("" if pd.isna(m) else f" *({m:+.2f})*"))
            lignes.append({"bloc": "pile complète", "polluant": p, "grain": e,
                           "n": int(r["n_plis"]), "gain": r["gain_pct"],
                           "relatif_pct": r["apport_marginal_pct"]})
        texte.append(f"| {e} | " + " | ".join(cells) + " |")
    f0 = next(iter(tables.values())).iloc[0]
    texte.append(f"\n⚠️ **Les fenêtres diffèrent selon le polluant** : "
                 + " · ".join(f"{NOM[p]} {tb['n_mois'].iloc[0]} mois ({tb['fenetre'].iloc[0]})"
                              for p, tb in tables.items())
                 + ". Seuls les **écarts entre étages** se comparent d'un polluant à l'autre, "
                   "jamais les niveaux.\n")
    texte.append("⚠️ Ne jamais citer le chiffre **AUX STATIONS** comme une performance de "
                 "spatialisation : il exige l'historique d'observations du point, que la "
                 "spatialisation n'a par définition pas.\n")
    return "\n".join(texte)


FAMILLES_ABLATION = ("typologie", "membres", "feux", "geoscf", "tendance")


def bloc_ablation(lignes: list[dict]) -> str:
    """Ce que chaque famille apporte vraiment — la seule lecture indépendante de l'ordre.

    L'empilement cumulatif de la § 12 répond à « que gagne-t-on en ajoutant cet étage
    APRÈS les précédents ». Un étage placé tôt s'attribue donc ce qu'un étage plus tardif
    aurait apporté seul, et l'ordre déclaré devient une décision de protocole dont l'effet
    ne se voit nulle part. L'ablation retire **une** famille de la pile complète, toutes
    les autres en place : elle ne dépend d'aucun ordre.

    ⚠️ Le CSV porte une colonne `apport_marginal_pct` qu'il ne faut PAS lire ici — elle
    vaut l'écart à la ligne **précédente**, donc à une autre ablation. Elle tombe juste
    pour la première ablation seulement, dont la précédente est justement MAXIMALE : le
    défaut est donc invisible à qui ne vérifie que celle-là. L'apport est recalculé
    `MAXIMALE − ablation`.

    ⚠️ C'est une **mesure, pas une sélection**. Élaguer les familles dont l'ablation ne
    coûte rien, puis publier le score de la pile élaguée sur ces mêmes plis, serait le
    biais de criblage mesuré à ×2 à ×4 sur ce dépôt.
    """
    fs = {p: RACINE / f"reports/methode_maximale_{p}_h2.csv"
          for p in ("O3", "NO2", "PM10", "PM25")}
    tables = {}
    for p, f in fs.items():
        if not f.exists():
            continue
        t = pd.read_csv(f)
        if t["configuration"].astype(str).str.contains("(ablation)", regex=False).any():
            tables[p] = (t, f)
    if not tables:
        return ""

    # Périmètre EFFECTIF, jamais le périmètre demandé (§ 2 quater).
    absents = [NOM[p] for p in fs if p not in tables]
    texte = [
        "## 12 bis. L'ablation — ce que chaque famille apporte, hors effet d'ordre\n",
        "Chaque ligne retire **une seule** famille de la pile complète, toutes les autres "
        "en place. Le chiffre gras est `MAXIMALE − ablation` : ce que la pile perd si "
        "cette famille disparaît. En regard, *en italique*, la lecture **cumulative** de "
        "la § 12 — ce que la même famille semblait valoir à sa place dans l'ordre.\n",
        "| famille retirée | " + " | ".join(NOM[p] for p in tables) + " |",
        "|---" * (len(tables) + 1) + "|",
    ]
    desaccords: list[str] = []
    for fam in FAMILLES_ABLATION:
        cells = []
        for p, (t, f) in tables.items():
            abl = _ligne_unique(t, "configuration", f"− {fam} (ablation)", f)
            cum = _ligne_unique(t, "configuration", f"+ {fam}", f)
            maxi = _ligne_unique(t, "configuration", "★ MAXIMALE — PARTOUT", f)
            apport = float(maxi["gain_pct"]) - float(abl["gain_pct"])
            marg = float(cum["apport_marginal_pct"])
            cells.append(f"**{apport:+.2f}** *({marg:+.2f})*")
            lignes.append({"bloc": "ablation", "polluant": p, "grain": fam,
                           "n": int(abl["n_plis"]), "gain": apport, "relatif_pct": marg})
            if (apport > 0) != (marg > 0):
                desaccords.append(f"**{fam}** sur {NOM[p]} (*{marg:+.2f}* → **{apport:+.2f}**)")
        texte.append(f"| − {fam} | " + " | ".join(cells) + " |")

    if absents:
        n = len(tables)
        texte.append(f"\n⚠️ **Périmètre effectif : {n} polluant{'s' if n > 1 else ''} sur 4** — "
                     f"{', '.join(absents)} sans lignes d'ablation à cette génération. "
                     f"Ne pas lire ce tableau comme un bilan des quatre.\n")
    if desaccords:
        texte.append("\nLes deux lectures **se contredisent en signe** sur "
                     + " · ".join(desaccords) + ". Là où elles divergent, c'est "
                     "l'ablation qui fait foi : la lecture cumulative attribue à un étage "
                     "ce que sa **position** lui a donné, pas ce qu'il apporte.\n")
    texte.append("\n⚠️ Un apport d'ablation faible ne veut pas dire « famille inutile » : "
                 "il veut dire **redondante avec le reste de la pile**. Deux familles qui "
                 "captent la même information s'annulent mutuellement à l'ablation alors "
                 "que retirer les deux coûterait cher. Ce tableau ne se lit jamais comme "
                 "une liste de coupes à opérer.\n")
    return "\n".join(texte)


def bloc_geoscf(lignes: list[dict]) -> str:
    """La seule source d'information venue de l'extérieur du périmètre CAMS."""
    fs = {p: RACINE / f"reports/apport_geoscf_{p}_h2_v1.csv"
          for p in ("O3", "NO2", "PM25")}
    presents = {p: f for p, f in fs.items() if f.exists()}
    if not presents:
        return ""
    texte = [
        "## 13. GEOS-CF — la seule information venue de l'extérieur\n",
        "Modèle de chimie-transport de la NASA, inventaire d'émissions et assimilation "
        "**indépendants** de CAMS. Tous les autres leviers du dossier réarrangent ce que "
        "CAMS contient déjà.\n",
        "⚠️ **Le fournisseur a changé de flux au milieu de la fenêtre** — v1 retiré le "
        "2 janvier 2026, v2 démarré le 5 août 2025 — et les deux ne sont **pas le même "
        "prédicteur**. Sur le mois de recouvrement, l'ozone diffère de **+15,41 µg/m³** en "
        "moyenne, soit l'ordre de grandeur de l'erreur des modèles eux-mêmes. Tout apport "
        "se mesure **par flux** ; le corpus mixte est écarté, et les chiffres publiés le "
        "04/08 qui en venaient sont retirés.\n",
        "| polluant | apport au plancher d'information | étendue (partitions) | "
        "corrélation des erreurs | n |",
        "|---|---|---|---|---|"]
    for p, f in presents.items():
        t = pd.read_csv(f)
        r = t.iloc[-1]
        # ⚠️ **La médiane sur plusieurs partitions, jamais une seule.** Le fichier d'apport
        # ne porte qu'une partition ; publier sa valeur ferait passer un tirage pour un
        # résultat. Quand le balayage existe, c'est lui qui fait foi — et son étendue est
        # publiée avec, parce qu'un gain de cet ordre s'y déplace.
        fs = RACINE / f"reports/stabilite_geoscf_{p}_v1.csv"
        if fs.exists():
            s = pd.read_csv(fs)["gain_pct"]
            valeur, etendue = float(s.median()), f"{s.min():+.2f} → {s.max():+.2f} ({len(s)})"
        else:
            valeur, etendue = float(r["delta_plancher_pct"]), "*une seule partition*"
        texte.append(f"| {NOM[p]} | **{valeur:+.2f} %** | {etendue} | "
                     f"{r['corr_erreurs']:+.3f} | {int(r['n']):,} |")
        lignes.append({"bloc": "GEOS-CF v1", "polluant": p, "grain": "plancher",
                       "n": int(r["n"]), "gain": valeur})
    texte.append("\n**Le mélange nu ne marche jamais** : GEOS-CF seul est bien pire que CAMS "
                 "partout, et leur moyenne est systématiquement pire que CAMS seul. En "
                 "**variables**, le modèle apprend *où* croire le modèle étranger — ce qu'une "
                 "moyenne ne sait pas faire.\n")
    texte.append("> **apport ≈ décorrélation × qualité.** Sur PM2,5 GEOS-CF est plus "
                 "décorrélé de CAMS que deux membres CAMS entre eux, et apporte pourtant le "
                 "moins — parce qu'il y est quatre fois plus mauvais.\n")
    return "\n".join(texte)


def bloc_episodes_reels(lignes: list[dict]) -> str:
    """La confrontation aux procédures préfectorales réellement déclarées."""
    f = RACINE / "reports/episodes_reels_occitanie.csv"
    if not f.exists():
        return ""
    t = pd.read_csv(f)
    texte = [
        "## 14. Les épisodes **réellement déclenchés** — la mesure la plus dure du dossier\n",
        "Tout le reste de ce document compte des « épisodes » au sens **journée-station en "
        "classe ATMO ≥ 3** — des milliers d'occurrences. Un déclenchement réel est une "
        "**zone-jour sous procédure préfectorale**, et il y en a **52 en quatorze mois** en "
        "Occitanie (PM10 40 · O₃ 12 · NO₂ **0**). Vérité terrain publiée par l'AASQA "
        "elle-même. **Les deux comptes ne se comparent pas.**\n"]
    for p, sous in t.groupby("polluant"):
        n_ep = int(sous["episodes"].iloc[0])
        n_zj = int(sous["zones_jours"].iloc[0])
        texte += [f"\n**{NOM.get(p, p)}** — {n_ep} épisodes évalués, {n_zj:,} zones-jours\n",
                  "| système | attrapés | rappel | fausses | précision |", "|---|---|---|---|---|"]
        for _, r in sous.iterrows():
            gras = "**" if r["systeme"] == "notre modèle" else ""
            texte.append(f"| {gras}{r['systeme']}{gras} | {int(r['attrapes'])}/{n_ep} | "
                         f"{r['rappel_pct']:.1f} % | {int(r['fausses'])} | "
                         f"{r['precision_pct']:.1f} % |")
            lignes.append({"bloc": "épisodes réels", "polluant": p, "grain": r["systeme"],
                           "n": n_ep, "POD": r["rappel_pct"], "FAR": 100 - r["precision_pct"]})
    texte.append("\n⚠️ **Trois lectures, dans l'ordre.** (1) Le plafond n'est pas le nombre "
                 "d'épisodes déclarés mais la ligne « observation » : sur PM10, douze "
                 "épisodes n'ont **aucune station** au-dessus du seuil en moyenne "
                 "journalière — la procédure se déclenche sur autre chose que la grandeur "
                 "prédite. (2) Tous les systèmes sont quasi aveugles sur PM10, nous très "
                 "légèrement moins. (3) Sur O₃ nous attrapons tout et crions au loup ~9 % "
                 "des zones-jours ; CAMS brut, qui en rate le tiers, est trois fois plus "
                 "précis. **À seuil physique fixé, le recalage d'amplitude joue contre "
                 "nous.**\n")
    texte.append("Ce tableau est pris **à seuil fixe, sans réglage**. Le § 8 montre qu'à "
                 "**volume d'alertes constant** le classement s'inverse. Les deux sont "
                 "vraies ; il faut dire laquelle on montre et pourquoi.\n")
    return "\n".join(texte)


def bloc_agregation_zone(lignes: list[dict]) -> str:
    """L'échelle de décision — et le seul gain sec du dossier.

    ⚠️ **Ce bloc a lu les QUATRE systèmes, pas seulement le nôtre.** Il n'en montrait qu'un,
    et présentait donc comme *notre* mérite ce qui est une propriété de la **règle de
    décision** : l'observation elle-même y gagne davantage que nous. Écrire « −34 % grâce à
    notre modèle » serait faux, et c'est la première question qu'un jury poserait. La page
    05 de la présentation affichait déjà les quatre — la source de vérité était **en retard
    sur le livrable qu'elle est censée gouverner**.
    """
    f = RACINE / "reports/agregation_zone_occitanie.csv"
    if not f.exists():
        return ""
    t = pd.read_csv(f)
    # Configuration nommée en toutes lettres et FILTRÉE dessus : une ligne prise par son
    # rang changerait de sens au prochain ajout de règle (`CLAUDE.md` § 2 bis § 1).
    CONF = {"polluant": "O3", "regle": "max (existant)", "seuil": 120.0, "min_stations": 1}
    ORDRE = ["observation", "notre modèle", "chaîne AASQA", "CAMS brut"]
    for col, val in CONF.items():
        if col in t.columns:
            t = t[t[col] == val]
    o3 = t[t["systeme"] == "notre modèle"]
    if o3.empty:
        return ""
    sans = o3[~o3["persistance"]].iloc[0]
    avec = o3[o3["persistance"]].iloc[0]
    baisse = 100 * (1 - avec["fausses"] / max(sans["fausses"], 1))
    texte = [
        "## 15. À quelle échelle décider — la persistance est gratuite, **et elle n'est pas "
        "à nous**\n",
        "La décision était prise par station-jour puis agrégée par le **maximum** — « au "
        "moins une station dépasse » — c'est-à-dire l'agrégateur qui **maximise les fausses "
        "alertes**. Il n'avait pas été retenu : il avait été subi.\n",
        "Exiger un dépassement prédit **deux jours de suite** retire un tiers des fausses "
        "alertes sans perdre un épisode. Voici ce que cela donne pour les **quatre** "
        "systèmes — parce que c'est une propriété de la *règle*, pas du modèle :\n",
        "| système | épisodes | fausses sans | fausses avec | écart | rappel |",
        "|---|---|---|---|---|---|"]
    for nom in ORDRE:
        g = t[t["systeme"] == nom]
        if len(g) != 2:
            continue
        s = g[~g["persistance"].astype(bool)].iloc[0]
        a = g[g["persistance"].astype(bool)].iloc[0]
        d = 100 * (a["fausses"] - s["fausses"]) / max(s["fausses"], 1)
        gratuite = int(s["attrapes"]) == int(a["attrapes"])
        gras = "**" if nom == "notre modèle" else ""
        rappel = (f"{s['rappel_pct']:.1f} % *(inchangé)*" if gratuite
                  else f"**{s['rappel_pct']:.1f} → {a['rappel_pct']:.1f} %**")
        texte.append(
            f"| {gras}{nom}{gras} | {int(s['attrapes'])}/{int(s['n_episodes'])} | "
            f"{int(s['fausses'])} | {int(a['fausses'])} | {d:+.1f} % | {rappel} |")
        lignes.append({"bloc": "agrégation zone", "polluant": "O3",
                       "grain": f"{nom} · max + persistance", "n": int(s["n_episodes"]),
                       "POD": a["rappel_pct"], "FAR": 100 - a["precision_pct"]})
    texte += [
        f"\n**−{baisse:.0f} % de fausses alertes, zéro épisode perdu.** Ce n'est pas un "
        "arbitrage, c'est un gain sec : une fausse alerte est un accident isolé, un épisode "
        "réel est **installé**, et la procédure préfectorale exige elle-même la persistance. "
        "Notre règle était instantanée alors que la décision qu'elle imite ne l'est pas.\n",
        "⚠️ **Mais elle profite à tout le monde, et davantage à l'observation qu'à nous.** "
        "La règle est gratuite pour trois systèmes sur quatre — rappel strictement "
        "inchangé — et **coûte un épisode à CAMS brut**, dont le rappel tombe. Le seul "
        "énoncé défendable est donc : *« la règle de décision vaut un tiers des fausses "
        "alertes, quel que soit le système qui l'alimente »*. Se l'attribuer serait faux.\n",
        "⚠️ **L'agrégateur de zone, lui, est un arbitrage — et à moitié un artefact.** Une "
        "règle « k parmi n » ne peut pas déclencher là où le réseau porte moins de k "
        "stations : elle l'**éteint**. Le réseau occitan a une **médiane de 2 stations par "
        "département**, et 3 départements sur 9 n'en portent qu'une. La chute des fausses "
        "alertes se décompose en deux mécanismes de taille comparable — silence sélectif des "
        "zones creuses, et vrai effet d'agrégation dans les zones denses. Ne jamais "
        "présenter le premier comme une méthode.\n",
        "⚠️ **À 12 épisodes d'ozone, aucun écart entre systèmes n'est significatif** : tous "
        "les intervalles de bootstrap se recouvrent. Le seul chiffre solide de cette section "
        "est la baisse de fausses alertes, parce qu'elle est **à rappel exactement "
        "identique**.\n"]
    return "\n".join(texte)


def bloc_points_fonctionnement(lignes: list[dict]) -> str:
    """Ce que le SEUIL décide — et ce qu'il ne décide pas.

    La tête B ne change ni le modèle ni les données. Trois demandes de service
    incompatibles, appliquées à la même sortie, seuil calé **hors échantillon**. Ce bloc
    existe parce que « nous sommes meilleurs » n'est pas une phrase publiable : le système
    est meilleur *sur l'axe qu'on choisit*, et il faut montrer que l'axe est un choix.
    """
    f = RACINE / "reports/points_de_fonctionnement.csv"
    if not f.exists():
        return ""
    t = pd.read_csv(f)
    o3 = t[t["polluant"] == "O3"]
    if o3.empty:
        return ""
    ref = o3[o3["systeme"].str.startswith("chaîne AASQA")]
    c = o3[o3["systeme"].str.contains("C —")]
    b = o3[o3["systeme"].str.contains("B —")]
    if ref.empty or c.empty or b.empty:
        return ""
    ref, c, b = ref.iloc[0], c.iloc[0], b.iloc[0]
    baisse = 100 * (1 - c["fausses"] / max(ref["fausses"], 1))
    hausse = 100 * (b["attrapes"] / max(ref["attrapes"], 1) - 1)
    for nom, v in (("détection O₃ — fausses alertes retirées à rappel égal (%)", baisse),
                   ("détection O₃ — épisodes gagnés au CSI maximal (%)", hausse)):
        lignes.append({"grandeur": nom, "valeur": round(float(v), 2)})
    texte = [
        "## 15 bis. Le seuil est un choix de service, pas une propriété du modèle\n",
        "Trois demandes réelles et incompatibles, servies par **la même sortie** — seul le "
        "seuil change, et il est calé sur les **mois antérieurs** puis appliqué tel quel. "
        "Ozone, seuil physique 120 µg/m³.\n",
        "| système | attrapés | manqués | fausses | rappel | précision | CSI |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in o3.iterrows():
        texte.append(f"| {r['systeme']} | {r['attrapes']:,} | {r['manques']:,} | {r['fausses']:,} | "
                     f"{r['rappel']:.1%} | {r['precision']:.1%} | {r['csi']:.3f} |")
    texte += [
        "",
        f"**À rappel strictement égal au leur, nous retirons {baisse:.0f} % des fausses "
        f"alertes** ({int(ref['fausses']):,} → {int(c['fausses']):,}). Et au CSI maximal — le "
        f"seul score qui pénalise les deux erreurs **ensemble** — nous attrapons "
        f"**{hausse:.0f} % d'épisodes de plus**, au prix d'alertes plus nombreuses.\n",
        "⚠️ **Aucun de ces trois réglages n'est « meilleur ».** Le rang de la prédiction est "
        "identique dans les trois lignes : déplacer un seuil ne crée aucune information, il "
        "**choisit où placer l'erreur**. C'est une décision de service, pas de modélisation.\n",
        "⚠️ Le réglage C **échouait** dans sa première version — visée 52,9 %, obtenue 46,7 % : "
        "un seuil posé au bord d'une contrainte sur le passé n'est pas tenu dans le futur. La "
        "marge de sécurité est déclarée dans le code, pas ajustée après coup.\n",
        "⚠️ Mesuré **sans l'étage `tendance`** : les artefacts de détection sont antérieurs à "
        "son introduction. **Son apport en détection est désormais mesuré** "
        "(`reports/banc_tendance_detection.csv`, mêmes plis de double aveugle) : il ne gagne "
        "**que sur l'ozone** — CSI 0,3339 → 0,3589 et **+3,1 % d'épisodes à volume d'alertes "
        "constant**, la lecture invariante par transformation monotone. Sur PM10 les deux "
        "lectures divergent (CSI −0,0063, +1 épisode sur 45 alertes) : **non concluant**. Le NO₂ "
        "et les PM2,5 n'ont que **1 et 35 dépassements** dans tout le corpus — la question n'y a "
        "pas de sens. Les pages aval seront reprises **pour l'ozone seul**.\n",
    ]
    return "\n".join(texte)


def main() -> int:
    lignes: list[dict] = []
    blocs = [
        f"# La vérité du dossier — chiffres gelés\n",
        f"*Généré le {datetime.now():%d/%m/%Y à %H h %M} par `scripts/verite_dossier.py`. "
        f"**Toute figure, slide ou phrase du dossier doit dériver de ce document.** Un chiffre "
        f"qui n'y figure pas est à retirer ou à re-mesurer — les fenêtres de 11 et 17 mois "
        f"citées ailleurs sont périmées.*\n",
        bloc_double_aveugle(lignes),
        bloc_annee(lignes),
        bloc_saison(lignes),
        bloc_horsechantillon(lignes),
        bloc_factoriel(lignes),
        bloc_mqi(lignes),
        bloc_seuils_2030(lignes),
        bloc_meteo(lignes),
        bloc_perimetres(lignes),
        bloc_reconciliation(lignes),
        bloc_comparaison_annuelle(lignes),
        bloc_duel_prevair(lignes),
        bloc_detection(lignes),
        bloc_signalements(lignes),
        bloc_front(lignes),
        bloc_generalisation(),
        bloc_pile_complete(lignes),
        bloc_ablation(lignes),
        bloc_geoscf(lignes),
        bloc_episodes_reels(lignes),
        bloc_agregation_zone(lignes),
        bloc_points_fonctionnement(lignes),
        "## 16. Registre — ce que ces mesures ne disent pas\n\n"
        "Ces mesures comparent des produits, pas des équipes. Le post-traitement officiel "
        "répond à des contraintes d'exploitation — couverture européenne, réentraînement "
        "continu, publication horaire — que ce projet n'a pas, et son article recommande "
        "lui-même la cible journalière lorsque l'usage porte sur un maximum : le choix "
        "horaire du produit distribué est donc **documenté et assumé**, pas un oubli.\n\n"
        "Le phénomène mesuré ici est **publié** — Bertrand et al. 2023 pour le grain sur CAMS, "
        "Huang et al. 2017 pour la réduction de variabilité en post-traitement. Ce travail les "
        "réplique et caractérise le produit déployé ; il ne les découvre pas.\n\n"
        "**Interdits de formulation** : « nous battons Copernicus », « leur produit est "
        "défaillant », « nous avons découvert ». Les faits suffisent, et ils sont plus "
        "solides sans adjectif.\n",
    ]
    sortie = RACINE / "reports/VERITE_DOSSIER.md"
    sortie.write_text("\n".join(blocs), encoding="utf-8")
    pd.DataFrame(lignes).to_csv(RACINE / "reports/verite_dossier.csv", index=False)
    print(f"Écrit : {sortie.relative_to(RACINE)} ({len(lignes)} lignes de chiffres)")
    print(f"Écrit : reports/verite_dossier.csv", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
