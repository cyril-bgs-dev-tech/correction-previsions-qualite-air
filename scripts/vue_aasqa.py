#!/usr/bin/env python3
"""Le dossier lu dans les conventions d'une AASQA, et non dans les nôtres.

Pourquoi cette vue existe
-------------------------
Un audit externe du 31/07/2026 a nommé le défaut : nos scores sont des **RMSE groupées sur
tous les couples station–temps réunis**. C'est une perte d'apprentissage nationale, pertinente
pour comparer trois produits, mais **ce n'est pas ce que calcule un rapport AASQA**.

Le référentiel national — arrêté du 16 avril 2021 article 13, guide LCSQA applicable depuis le
1ᵉʳ janvier 2022 — et la pratique de PREV'AIR imposent quatre choses que notre vue ne fait pas :

1. **stations de fond uniquement** — urbaines, périurbaines et rurales ; les stations trafic et
   industrielles sont écartées ;
2. **disponibilité ≥ 75 %** des données valides sur la période — le référentiel écrit
   `sum(idx) >= 0,75 * nb_times`, un opérateur large ; la page PREV'AIR résume « plus de
   75 % » mais ce résumé ne remplace pas le pseudo-code du RTN ;
3. **score temporel par station, puis moyenne non pondérée des stations** — une station à
   8 000 heures ne pèse pas plus qu'une à 6 500, alors que notre RMSE groupée le fait ;
4. **échéances séparées** (J+1, J+2, J+3), et pour l'ozone la **saison avril–septembre**.

L'écart entre les deux vues n'est pas supposé petit : il est **mesuré ici**, produit à côté de
la vue ML, jamais à sa place. Les deux répondent à des questions différentes.

Ce que la vue ne peut pas faire, et pourquoi c'est dit
------------------------------------------------------
Le franchissement réglementaire français se juge sur l'ozone à **180 µg/m³ en maximum horaire**
(seuil d'information) et sur les **PM10 à 50 µg/m³ en moyenne journalière**. Le projet n'a
**jamais ingéré les PM10** — ni observations ni prévisions. Or 40 des 52 vigilances réellement
déclarées par ATMO Occitanie entre janvier 2025 et mars 2026 portent sur les PM10. Cette vue
calcule donc l'ozone à 180 et **déclare la lacune** plutôt que de la remplacer par les PM2,5
à 25 µg/m³, qui répondent à une autre question.

Usage : python3 scripts/vue_aasqa.py [--polluant O3] [--horizons 1 2 3]
Sortie : reports/vue_aasqa_{polluant}.csv
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

from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

from aq.ingest.controle import ControleEchec, exiger_colonnes, exiger_lignes  # noqa: E402

GRAINE = 20260731
DISPONIBILITE_MIN = 0.75
# Seuil d'information de la procédure française, en maximum **horaire**. Ce n'est pas notre
# 120 µg/m³ en maximum glissant 8 h, qui est la valeur cible européenne.
# Seuils d'**information et de recommandation** de la procédure française, en maximum
# horaire (code de l'environnement, art. R. 221-1 ; arrêté du 7 avril 2016). Ce ne sont pas
# nos grains de dossier.
#
# ⚠️ **Un seuil se cite avec sa durée.** Les seuils d'ALERTE, non évalués ici, exigent une
# persistance : ozone **240 µg/m³ pendant trois heures consécutives**, NO₂ **400 µg/m³
# pendant trois heures consécutives** (200 µg/m³ pour le NO₂ n'est que l'information).
# Et le **120 µg/m³ en maximum glissant 8 h** du dossier est une **valeur cible
# européenne**, appréciée sur un nombre annuel de dépassements moyenné sur trois ans —
# ce n'est ni un seuil d'information ni, jour par jour, un déclencheur préfectoral.
#
# Enfin le déclenchement effectif dépend aussi de critères de superficie, de population et
# de la procédure préfectorale applicable : **une valeur à une station ne suffit pas**.
# **Les PM2,5 n'ont pas de seuil de procédure** : la procédure particules porte sur les PM10 à
# 50 µg/m³ en moyenne journalière, polluant que le projet n'a jamais ingéré. On n'invente donc
# pas un seuil PM2,5 pour avoir une ligne à afficher.
SEUIL_INFORMATION = {"O3": 180.0, "NO2": 200.0}
SAISON = {"O3": (4, 9)}  # fenêtre d'évaluation de l'ozone au référentiel LCSQA


def modele():
    return modele_mos(graine=GRAINE)


def stations_de_fond() -> pd.DataFrame:
    """Fond urbain, périurbain et rural — la population du référentiel AASQA."""
    s = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    exiger_colonnes(s, ["station_id", "type_station", "typologie_zone"], "stations")
    s = s.drop_duplicates("station_id")
    fond = s[s["type_station"] == "background"].copy()
    if fond.empty:
        raise ControleEchec(
            "aucune station de type 'background' — le libellé de typologie a changé, "
            f"valeurs vues : {sorted(s['type_station'].dropna().unique())}")
    # Les rurales portent plusieurs libellés (regional, nearcity, remote) : on les regroupe
    # par **préfixe**, jamais par une liste figée qui laisserait tomber un libellé nouveau.
    zone = fond["typologie_zone"].fillna("")
    fond["zone_aasqa"] = np.select(
        [zone.eq("urban"), zone.eq("suburban"), zone.str.startswith("rural")],
        ["urbaine", "périurbaine", "rurale"], default="autre")
    inconnues = fond[fond["zone_aasqa"] == "autre"]["typologie_zone"].unique()
    if len(inconnues):
        raise ControleEchec(f"typologies de zone non classées : {list(inconnues)}")
    return fond[["station_id", "zone_aasqa"]]


def scores_station(g: pd.DataFrame, colonne: str) -> dict:
    """Les trois indicateurs de PREV'AIR : biais, RMSE, corrélation — pour une station."""
    o, p = g["valeur"].to_numpy(), g[colonne].to_numpy()
    r = float(np.corrcoef(o, p)[0, 1]) if len(o) > 2 and o.std() > 0 and p.std() > 0 else np.nan
    return {"biais": float(np.mean(p - o)),
            "rmse": float(np.sqrt(np.mean((p - o) ** 2))), "correlation": r}


def main(polluant: str, horizons: list[int]) -> int:
    depart = time.time()
    fond = stations_de_fond()
    lignes, contingences = [], []

    for horizon in horizons:
        jeu = charger(polluant, horizon)
        colonnes = colonnes_admises(jeu)
        jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
        jeu = jeu.dropna(subset=["valeur"])
        d = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
        d = d.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
        if polluant in SEUIL_INFORMATION:
            # Même jeu, agrégé au grain de la **procédure** : maximum horaire. On ne garde
            # que la colonne d'observation et celle de CAMS, jointes par clé — jamais par
            # position, et en vérifiant que la jointure ne perd rien.
            proc = agreger_journalier(jeu, colonnes, "max_horaire")
            proc = proc[["station_id", "jour", "obs_jour", "cams_jour"]].rename(
                columns={"obs_jour": "obs_max_horaire", "cams_jour": "cams_max_horaire"})
            avant = len(d)
            d = d.merge(proc, on=["station_id", "jour"], how="left")
            if len(d) != avant:
                raise ControleEchec(
                    f"la jointure du grain horaire a changé le nombre de lignes "
                    f"({avant:,} → {len(d):,})")
            couv = float(d["obs_max_horaire"].notna().mean())
            if couv < 0.95:
                raise ControleEchec(
                    f"maximum horaire renseigné sur {couv:.1%} des lignes seulement")
        predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
        d["jour"] = pd.to_datetime(d["jour"])

        avant_stations = d["station_id"].nunique()
        d = d.merge(fond, on="station_id", how="inner")
        exiger_lignes(d, 1000, f"{polluant} J+{horizon} sur stations de fond")

        # Saison d'évaluation, **avant** le filtre de disponibilité : la règle des 75 % porte
        # sur la période évaluée, pas sur l'année entière.
        if polluant in SAISON:
            m0, m1 = SAISON[polluant]
            d = d[d["jour"].dt.month.between(m0, m1)]

        # Disponibilité : part des journées de la période effectivement mesurées.
        etendue = (d["jour"].max() - d["jour"].min()).days + 1
        if polluant in SAISON:
            # Sur une fenêtre saisonnière, le dénominateur est le nombre de jours de saison,
            # pas l'étendue calendaire — sinon aucune station ne passerait jamais les 75 %.
            attendus = int(d.groupby(d["jour"].dt.year)["jour"].nunique().sum())
        else:
            attendus = etendue
        dispo = d.groupby("station_id")["jour"].nunique() / max(attendus, 1)
        gardees = dispo[dispo >= DISPONIBILITE_MIN].index
        d = d[d["station_id"].isin(gardees)]
        print(f"{polluant} J+{horizon} · {avant_stations} stations → "
              f"{len(fond)} de fond → {d['station_id'].nunique()} à plus de "
              f"{DISPONIBILITE_MIN:.0%} de disponibilité · {len(d):,} jours-station",
              flush=True)
        if d["station_id"].nunique() < 20:
            raise ControleEchec(
                f"{d['station_id'].nunique()} stations retenues — trop peu pour une moyenne "
                "de stations ; vérifier le calcul de disponibilité avant de conclure")

        # La correction, en validation par stations exclues sur cette population.
        stations = np.sort(d["station_id"].unique())
        groupe = d["station_id"].map({s: i % 3 for i, s in enumerate(stations)}).to_numpy()
        d["nous"] = np.nan
        for p in sorted(set(groupe)):
            test = groupe == p
            m = modele()
            m.fit(d.loc[~test, predicteurs],
                  d.loc[~test, "valeur"] - d.loc[~test, "cams_jour"])
            d.loc[test, "nous"] = np.clip(
                d.loc[test, "cams_jour"].to_numpy() + m.predict(d.loc[test, predicteurs]),
                0, None)

        for nom, colonne in (("CAMS brut", "cams_jour"), ("notre correction", "nous")):
            par_station = pd.DataFrame(
                [scores_station(g, colonne) | {"station_id": s, "zone": g["zone_aasqa"].iloc[0]}
                 for s, g in d.groupby("station_id")])
            # **Moyenne non pondérée des stations** — c'est là toute la différence avec la
            # vue ML, qui pondère implicitement par le nombre d'heures valides.
            groupee = float(np.sqrt(np.mean((d[colonne] - d["valeur"]) ** 2)))
            lignes.append({
                "polluant": polluant, "horizon": f"J+{horizon}", "produit": nom,
                "n_stations": len(par_station), "n_jours_station": len(d),
                "rmse_aasqa": float(par_station["rmse"].mean()),
                "rmse_groupee_ml": groupee,
                "biais_aasqa": float(par_station["biais"].mean()),
                "correlation_aasqa": float(par_station["correlation"].mean()),
                "rmse_pire_station": float(par_station["rmse"].max()),
            })
            for zone, gz in par_station.groupby("zone"):
                lignes.append({
                    "polluant": polluant, "horizon": f"J+{horizon}",
                    "produit": f"{nom} · {zone}", "n_stations": len(gz),
                    "n_jours_station": np.nan,
                    "rmse_aasqa": float(gz["rmse"].mean()), "rmse_groupee_ml": np.nan,
                    "biais_aasqa": float(gz["biais"].mean()),
                    "correlation_aasqa": float(gz["correlation"].mean()),
                    "rmse_pire_station": float(gz["rmse"].max())})

        # ── Franchissement du seuil d'information, s'il est défini pour ce polluant ──
        if polluant in SEUIL_INFORMATION:
            s = SEUIL_INFORMATION[polluant]
            if "obs_max_horaire" not in d.columns:
                print(f"  ⚠️ seuil {s:.0f} µg/m³ non évalué : maximum horaire indisponible.",
                      flush=True)
            else:
                # Notre correction est apprise sur le max 8 h ; pour juger un seuil en max
                # horaire, on lui applique le **rapport** observé entre les deux grains chez
                # CAMS. C'est une transposition, pas une prédiction directe — et elle est
                # nommée comme telle dans la sortie.
                rapport = (d["cams_max_horaire"] / d["cams_jour"].clip(lower=1.0)).clip(1.0, 2.0)
                d["nous_max_horaire"] = d["nous"] * rapport

                # **Et un modèle entraîné directement sur le grain de la procédure.** La
                # transposition ci-dessus est un bricolage : elle applique à notre correction
                # un rapport mesuré chez CAMS. Si le seuil de 180 µg/m³ n'est pas détecté, il
                # faut savoir si c'est le mécanisme qui manque ou seulement ce bricolage.
                # Mêmes plis, mêmes prédicteurs, seule la cible change.
                d["nous_direct"] = np.nan
                for pli in sorted(set(groupe)):
                    test = groupe == pli
                    m = modele()
                    m.fit(d.loc[~test, predicteurs],
                          d.loc[~test, "obs_max_horaire"] - d.loc[~test, "cams_max_horaire"])
                    d.loc[test, "nous_direct"] = np.clip(
                        d.loc[test, "cams_max_horaire"].to_numpy()
                        + m.predict(d.loc[test, predicteurs]), 0, None)

                # Les scores sur le grain de la PROCÉDURE — c'est celui qu'évalue
                # PREV'AIR (« seul le maximum journalier d'ozone est considéré »), donc le
                # seul sur lequel une comparaison à la chaîne nationale soit légitime.
                print(f"  RMSE sur le maximum horaire journalier — grain PREV'AIR :",
                      flush=True)
                for nom, colonne in (("CAMS brut", "cams_max_horaire"),
                                     ("notre correction (apprise sur ce grain)", "nous_direct")):
                    e = d[colonne] - d["obs_max_horaire"]
                    par_st = d.assign(e=e).groupby("station_id")["e"].agg(
                        rmse=lambda x: float(np.sqrt(np.mean(x ** 2))), biais="mean")
                    corr = d.groupby("station_id").apply(
                        lambda g: g["obs_max_horaire"].corr(g[colonne]),
                        include_groups=False)
                    print(f"    {nom:42s} RMSE {par_st['rmse'].mean():6.2f} · "
                          f"biais {par_st['biais'].mean():+6.2f} · "
                          f"corrélation {corr.mean():.3f} · "
                          f"{len(par_st)} stations", flush=True)

                for nom, colonne in (("CAMS brut", "cams_max_horaire"),
                                     ("notre correction (transposée)", "nous_max_horaire"),
                                     ("notre correction (apprise sur ce grain)", "nous_direct")):
                    vrai, predit = d["obs_max_horaire"] > s, d[colonne] > s
                    contingences.append({
                        "horizon": f"J+{horizon}", "produit": nom, "seuil": s,
                        "TP": int((vrai & predit).sum()), "FP": int((~vrai & predit).sum()),
                        "FN": int((vrai & ~predit).sum()), "TN": int((~vrai & ~predit).sum())})

    t = pd.DataFrame(lignes)
    print(f"\n{'─' * 96}")
    print(f"{'horizon':8} {'produit':34} {'n st.':>6} {'RMSE AASQA':>11} "
          f"{'RMSE groupée':>13} {'biais':>8} {'r':>7} {'pire st.':>9}")
    for _, r in t.iterrows():
        gr = f"{r['rmse_groupee_ml']:13.3f}" if np.isfinite(r["rmse_groupee_ml"]) else " " * 13
        print(f"{r['horizon']:8} {r['produit']:34} {r['n_stations']:6d} "
              f"{r['rmse_aasqa']:11.3f} {gr} {r['biais_aasqa']:+8.3f} "
              f"{r['correlation_aasqa']:7.3f} {r['rmse_pire_station']:9.3f}")

    # L'écart entre les deux conventions — le chiffre que l'audit réclamait.
    print(f"\n{'─' * 96}\nÉcart entre les deux conventions, par horizon :")
    for h, g in t[t["rmse_groupee_ml"].notna()].groupby("horizon"):
        for _, r in g.iterrows():
            ecart = r["rmse_aasqa"] - r["rmse_groupee_ml"]
            print(f"  {h} · {r['produit']:20s} AASQA {r['rmse_aasqa']:6.3f} contre groupée "
                  f"{r['rmse_groupee_ml']:6.3f} → {ecart:+.3f} µg/m³ "
                  f"({100 * ecart / r['rmse_groupee_ml']:+.1f} %)")

    if contingences:
        c = pd.DataFrame(contingences)
        print(f"\n{'─' * 96}\nFranchissement du seuil d'information "
              f"{SEUIL_INFORMATION[polluant]:.0f} µg/m³ (maximum horaire) :")
        print(c.to_string(index=False))
        if int(c["TP"].sum() + c["FN"].sum()) == 0:
            print("\n  ⚠️ **Aucun franchissement observé** sur cette population et cette "
                  "fenêtre.\n     Le seuil d'information français n'est pas évaluable ici — "
                  "à dire, et non\n     à remplacer par un seuil plus bas choisi pour qu'il "
                  "y ait des événements.")
        c.to_csv(RACINE / f"reports/vue_aasqa_{polluant}_contingence.csv", index=False)

    # Les PM10 ont été ajoutées le 01/08/2026 (flux LCSQA + prévisions ADS). L'avertissement
    # qui annonçait leur absence est donc devenu faux ; le laisser serait aussi trompeur que
    # de l'avoir omis quand il était vrai.
    if polluant == "PM10":
        print("\n  Rappel du poids de ce polluant : **40 des 52 vigilances** réellement "
              "déclarées\n  par Atmo Occitanie entre 01/2025 et 03/2026 portent sur les "
              "PM10, contre 12 sur l'ozone.\n  Le seuil d'information est de 50 µg/m³ en "
              "moyenne journalière.")
    else:
        print("\n  Note : les PM2,5 n'ont **pas** de seuil de procédure — la procédure "
              "particules porte\n  sur les PM10 à 50 µg/m³ en moyenne journalière, "
              "polluant désormais traité.")

    sortie = RACINE / f"reports/vue_aasqa_{polluant}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizons", type=int, nargs="+", default=[1, 2, 3])
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizons))
