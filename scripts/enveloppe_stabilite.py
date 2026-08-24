#!/usr/bin/env python3
"""De combien le chiffre publié bouge sous des choix d'évaluation également légitimes.

La question à laquelle ce script répond — chantier ① du contrat de produit
---------------------------------------------------------------------------
Le socle publie « NO₂ +41,09 % ». Ce nombre n'est pas une propriété du modèle : c'est une
propriété du modèle **et** d'une trentaine de décisions d'évaluation qu'un autre analyste
aurait pu prendre autrement — commencer un mois plus tard, exclure les stations qui
n'ouvrent qu'à mi-parcours, écarter un mois d'épisode. Aucune n'est fautive. Tant que
l'amplitude qu'elles produisent n'est pas mesurée, **le chiffre publié n'a pas d'échelle**,
et le lecteur ne peut pas savoir si un écart de 0,4 pt entre deux piles veut dire quelque
chose.

Ce que ce script mesure, et ce qu'il ne mesure pas
---------------------------------------------------
Il perturbe **ce qui est noté**, jamais **ce qui est appris**. Les prédictions hors
échantillon du socle sont enregistrées pli par pli : re-noter un sous-ensemble est donc
EXACT et gratuit. Mais retirer un mois de l'évaluation n'est pas le retirer de
l'apprentissage — le modèle reste celui qui l'a vu.

> **C'est donc un MINORANT de l'enveloppe**, jamais l'enveloppe entière. L'axe
> apprentissage demande un réajustement par perturbation ; il est traité séparément, et son
> coût est ce qui a fait commencer par ici.

Le contrôle qui décide de tout
-------------------------------
Avant de perturber quoi que ce soit, le script **recalcule le chiffre publié depuis les
prédictions** et REFUSE de continuer s'il ne le retrouve pas. Une enveloppe bâtie sur une
reconstruction fausse serait plausible, cohérente et sans rapport — exactement la famille de
défauts que `CLAUDE.md` traque (§ 2 ter).

Usage : python3 scripts/enveloppe_stabilite.py [--polluants NO2,O3,PM10,PM25]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
VARIANTE = "_sans-feux-geoscf_fenetre-complete"
COL_PRED = "pred__maximale___partout"
GRAINE = 20260824  # fixée AVANT exécution — le tirage des stations doit être rejouable


def gain(t: pd.DataFrame) -> float:
    """Le gain poolé, dans la définition EXACTE de la pile : 1 − RMSE(corrigé)/RMSE(CAMS).

    Poolé, pas moyenné par pli : la RMSE n'est pas linéaire, et moyenner des gains de plis
    rend un autre nombre (16,68 % contre 19,44 % mesurés le 24/08).
    """
    e_cams = t["obs"] - t["cams_jour"]
    e_corr = t["obs"] - t[COL_PRED]
    r_cams = float(np.sqrt(np.mean(e_cams ** 2)))
    r_corr = float(np.sqrt(np.mean(e_corr ** 2)))
    return 100.0 * (1.0 - r_corr / r_cams)


def perturbations(t: pd.DataFrame, rng: np.random.Generator) -> list[tuple[str, pd.Series]]:
    """Les masques, INSCRITS ICI AVANT EXÉCUTION. Chacun est un choix qu'un analyste
    raisonnable aurait pu faire — aucun n'est fautif, et c'est ce qui les rend comparables.
    """
    mois = np.sort(t["mois"].unique())
    par_mois_obs = t.groupby("mois")["obs"].mean()
    par_mois_sta = t.groupby("mois")["station_id"].nunique()
    # 🔴 « présentes sur TOUS les mois » rend ZÉRO station, et « sur 80 % » aussi. C'est
    # STRUCTUREL : le protocole cache une rotation de trois groupes, donc une station ne
    # peut apparaître au test que dans UN MOIS SUR TROIS. Mesuré ici : maximum exactement
    # 0,333, et 298 stations sur 344 l'atteignent.
    #
    # Écrite en absolu, la perturbation rendait `nan`, et `nan` traversait `min`/`max` sans
    # lever — toute comparaison avec lui est fausse, en silence (§ 2 ter).
    #
    # Le seuil se dérive donc de CETTE exécution et non d'une constante (règle A). Premier
    # essai — « présentes tous les mois où elles POUVAIENT l'être » — tenait sur NO₂
    # (298/344) et dégénérait sur PM2,5 : 63 stations sur 236, 30 % des lignes, 12 mois. Le
    # réseau PM2,5 est bien plus intermittent, et un critère qui vaut sur un polluant et pas
    # sur l'autre ne rend pas deux enveloppes comparables.
    #
    # La MÉDIANE de présence est définie partout et retient toujours la moitié la mieux
    # observée du réseau, quelle que soit son intermittence.
    presence = t.groupby("station_id")["mois"].nunique()
    stations_assidues = set(presence[presence >= presence.median()].index)
    p: list[tuple[str, pd.Series]] = []
    p.append(("bord — sans le premier mois", t["mois"] != mois[0]))
    p.append(("bord — sans le dernier mois", t["mois"] != mois[-1]))
    p.append(("bord — sans les deux bords", ~t["mois"].isin([mois[0], mois[-1]])))
    p.append((f"sans le mois le PLUS chargé ({par_mois_obs.idxmax()})",
              t["mois"] != par_mois_obs.idxmax()))
    p.append((f"sans le mois le MOINS chargé ({par_mois_obs.idxmin()})",
              t["mois"] != par_mois_obs.idxmin()))
    p.append((f"sans le mois le plus troué ({par_mois_sta.idxmin()})",
              t["mois"] != par_mois_sta.idxmin()))
    p.append((f"moitié la mieux observée du réseau ({len(stations_assidues)} sur "
               f"{t['station_id'].nunique()})",
              t["station_id"].isin(stations_assidues)))
    # Cinq tirages de 95 % des stations : une seule réalisation ne ferait pas une amplitude
    # (§ 1 ter — une mesure n'est pas une propriété).
    sta = np.sort(t["station_id"].unique())
    for k in range(5):
        garde = set(rng.choice(sta, size=int(round(0.95 * len(sta))), replace=False))
        p.append((f"95 % des stations · tirage {k + 1}", t["station_id"].isin(garde)))
    return p


# Les perturbations SAISONNIÈRES sont tenues à part, et ce n'est pas un détail de
# présentation : retirer une saison ne rééchantillonne pas le corpus, cela CHANGE LA
# QUESTION — « que vaut la correction sur l'année » devient « que vaut-elle hors été ». Sur
# PM10 l'écart atteint 4,57 pt, six fois l'amplitude de tout le reste ; le mêler aux autres
# donnerait une enveloppe qui ne mesure plus la stabilité mais le contraste des saisons.
def perturbations_saison(t: pd.DataFrame) -> list[tuple[str, pd.Series]]:
    return [("sans l'été (juin-août)", ~t["jour"].dt.month.isin([6, 7, 8])),
            ("sans l'hiver (déc-févr)", ~t["jour"].dt.month.isin([12, 1, 2]))]


def verifier_masque(nom: str, m: pd.Series, t: pd.DataFrame) -> None:
    """Un masque qui ne retient presque rien n'est pas une perturbation, c'est un défaut.

    Sans ce garde, une perturbation dégénérée rend `nan`, et `nan` traverse `min`/`max` sans
    lever : l'enveloppe publiée serait bâtie sur une valeur qui n'existe pas.
    """
    sous = t[m]
    if len(sous) < 0.4 * len(t) or sous["station_id"].nunique() < 5 or sous["mois"].nunique() < 3:
        raise SystemExit(
            f"⛔ perturbation dégénérée « {nom} » : {len(sous):,} lignes "
            f"({100 * len(sous) / len(t):.0f} %), {sous['station_id'].nunique()} stations, "
            f"{sous['mois'].nunique()} mois. Une perturbation qui ne retient presque rien "
            f"ne mesure pas la stabilité — corriger sa définition, jamais l'ignorer.")


def enveloppe_appariee(pol: str) -> dict | None:
    """L'amplitude du chiffre ABSOLU contre celle de l'écart APPARIÉ, sur les mêmes lignes.

    La question que ce mode tranche
    --------------------------------
    Si retirer un seul mois déplace le chiffre publié de 1,6 à 2,5 pt, un module qui gagne
    0,75 pt est-il du bruit ? La réponse ne s'affirme pas, elle se mesure — et les deux
    grandeurs ne se comparent que sur les MÊMES lignes.

    🔴 Le piège, mesuré le 24/08 : comparer la pile socle et la pile module entre DEUX
    exécutions ne mesure rien. Le protocole cache une rotation `groupes[i % 3]` indexée sur
    le rang du mois ; les deux exécutions ne commençant pas au même mois, leurs partitions
    de test sont DISJOINTES par construction — 16 055 lignes communes sur 90 000 pour NO₂,
    et **zéro pour O₃**. Le premier calcul rendait « +1,77 à +3,33 pt » là où l'appariement
    correct rend +0,78, et rien n'aurait signalé l'erreur : les deux nombres sont plausibles.

    L'appariement juste est INTERNE au fichier module : la pile complète contre la même pile
    dont on retire l'IFS, mêmes plis, mêmes lignes, même graine.
    """
    f = RACINE / f"reports/predictions_methode_maximale_{pol}_h2{VARIANTE}_avec-ifs.parquet"
    if not f.exists():
        return None
    t = pd.read_parquet(f)
    t["mois"] = pd.to_datetime(t["jour"]).dt.strftime("%Y-%m")
    if "pred__ifs__ablation" not in t.columns:
        raise SystemExit(f"⛔ {pol} : colonne d'ablation IFS absente — l'appariement interne "
                         f"est impossible, et le faire entre exécutions serait faux.")
    mois = np.sort(t["mois"].unique())
    abso = [gain(t[t["mois"] != m]) for m in mois]
    ecart = [gain(t[t["mois"] != m]) - gain(t[t["mois"] != m].rename(
        columns={COL_PRED: "_x", "pred__ifs__ablation": COL_PRED})) for m in mois]
    return {"polluant": pol,
            "absolu_bas": min(abso), "absolu_haut": max(abso),
            "absolu_amplitude_pt": max(abso) - min(abso),
            "apparie_bas": min(ecart), "apparie_haut": max(ecart),
            "apparie_amplitude_pt": max(ecart) - min(ecart),
            "apparie_plein": gain(t) - gain(t.rename(
                columns={COL_PRED: "_x", "pred__ifs__ablation": COL_PRED})),
            "rapport_stabilite": (max(abso) - min(abso)) / (max(ecart) - min(ecart))}


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--polluants", default="NO2,O3,PM10,PM25")
    a.add_argument("--apparie", action="store_true",
                   help="compare l'amplitude du chiffre absolu à celle de l'écart apparié")
    o = a.parse_args()

    if o.apparie:
        rs = [r for pol in o.polluants.split(",") if (r := enveloppe_appariee(pol))]
        r = pd.DataFrame(rs)
        sortie = RACINE / "reports/enveloppe_stabilite_appariee.csv"
        r.to_csv(sortie, index=False)
        print("JACKKNIFE PAR MOIS · chiffre ABSOLU contre écart APPARIÉ (mêmes lignes)")
        print("═" * 94)
        print(f"{'':6s} {'absolu (socle + module)':>26s} {'apparié : retrait du module':>31s}"
              f" {'rapport':>9s}")
        for _, x in r.iterrows():
            print(f"{x['polluant']:6s} {x['absolu_bas']:8.2f}–{x['absolu_haut']:5.2f} "
                  f"({x['absolu_amplitude_pt']:4.2f} pt)     "
                  f"{x['apparie_bas']:+7.3f}–{x['apparie_haut']:+6.3f} "
                  f"({x['apparie_amplitude_pt']:5.3f} pt) plein {x['apparie_plein']:+.3f}"
                  f"  {x['rapport_stabilite']:6.1f} ×")
        print(f"\nL'écart apparié est {r['rapport_stabilite'].min():.1f} à "
              f"{r['rapport_stabilite'].max():.1f} × plus stable que le chiffre absolu.")
        print(f"Écrit : {sortie.relative_to(RACINE)}")
        return 0

    lignes = []
    for pol in o.polluants.split(","):
        f = RACINE / f"reports/predictions_methode_maximale_{pol}_h2{VARIANTE}.parquet"
        ref = RACINE / f"reports/methode_maximale_{pol}_h2{VARIANTE}.csv"
        if not f.exists() or not ref.exists():
            print(f"⛔ {pol} : artefact absent — {f.name if not f.exists() else ref.name}")
            return 2
        t = pd.read_parquet(f)
        t["jour"] = pd.to_datetime(t["jour"])
        t["mois"] = t["jour"].dt.strftime("%Y-%m")

        # ── Le contrôle qui autorise la suite ────────────────────────────────────────────
        publie = float(pd.read_csv(ref).set_index("configuration")
                       ["gain_pct"]["★ MAXIMALE — PARTOUT"])
        recalcule = gain(t)
        if abs(recalcule - publie) > 0.02:
            print(f"⛔ {pol} : le gain recalculé ({recalcule:.3f} %) ne retrouve pas le "
                  f"publié ({publie:.3f} %). Une enveloppe bâtie sur une reconstruction "
                  f"fausse serait plausible et sans rapport — on s'arrête.")
            return 3

        rng = np.random.default_rng(GRAINE)
        vals = []
        print(f"\n{pol} · publié {publie:.2f} % · recalculé {recalcule:.2f} % ✅ "
              f"({len(t):,} lignes, {t['mois'].nunique()} mois)")
        for nom, masque in perturbations(t, rng):
            verifier_masque(nom, masque, t)
            g = gain(t[masque])
            vals.append(g)
            print(f"    {g:+7.2f} %  ({g - publie:+5.2f})  {nom} · "
                  f"{100 * masque.mean():.0f} % des lignes")
        saison = []
        for nom, masque in perturbations_saison(t):
            verifier_masque(nom, masque, t)
            g = gain(t[masque])
            saison.append(g)
            print(f"    {g:+7.2f} %  ({g - publie:+5.2f})  ⚠️ {nom} — CHANGE LA QUESTION, "
                  f"hors enveloppe")
        # Le jackknife par mois : quel mois PORTE le chiffre ?
        jack = {m: gain(t[t["mois"] != m]) for m in np.sort(t["mois"].unique())}
        pire = min(jack.items(), key=lambda kv: kv[1])
        meilleur = max(jack.items(), key=lambda kv: kv[1])
        print(f"    ── jackknife par mois : {min(jack.values()):+.2f} à "
              f"{max(jack.values()):+.2f} %"
              f"  (retirer {pire[0]} coûte {pire[1] - publie:+.2f}, "
              f"{meilleur[0]} rapporte {meilleur[1] - publie:+.2f})")
        lignes.append({
            "polluant": pol, "publie_pct": publie,
            "enveloppe_bas": min(vals), "enveloppe_haut": max(vals),
            "amplitude_pt": max(vals) - min(vals),
            "jack_bas": min(jack.values()), "jack_haut": max(jack.values()),
            "jack_amplitude_pt": max(jack.values()) - min(jack.values()),
            "mois_le_plus_porteur": pire[0], "n_perturbations": len(vals),
            "saison_bas": min(saison), "saison_haut": max(saison),
        })

    r = pd.DataFrame(lignes)
    for c in ("publie_pct", "enveloppe_bas", "enveloppe_haut", "amplitude_pt",
              "jack_bas", "jack_haut", "jack_amplitude_pt", "saison_bas", "saison_haut"):
        if c not in r:  # pragma: no cover — un garde, pas une branche
            raise SystemExit(f"colonne absente du rapport : {c}")
    sortie = RACINE / "reports/enveloppe_stabilite_evaluation.csv"
    r.to_csv(sortie, index=False)
    print("\n" + "═" * 92)
    print("ENVELOPPE DE STABILITÉ · axe ÉVALUATION seul (minorant)")
    print(f"{'':6s} {'publié':>9s} {'enveloppe':>18s} {'amplitude':>10s} "
          f"{'jackknife mois':>18s} {'ampl.':>7s}  {'saison ↓/↑':>12s}")
    for _, x in r.iterrows():
        print(f"{x['polluant']:6s} {x['publie_pct']:8.2f}% "
              f"[{x['enveloppe_bas']:6.2f} ; {x['enveloppe_haut']:6.2f}] "
              f"{x['amplitude_pt']:9.2f} pt "
              f"[{x['jack_bas']:6.2f} ; {x['jack_haut']:6.2f}] {x['jack_amplitude_pt']:6.2f}"
              f"   {x['saison_bas']:6.2f}/{x['saison_haut']:.2f}")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
