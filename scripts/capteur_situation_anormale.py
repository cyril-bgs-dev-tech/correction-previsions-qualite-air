#!/usr/bin/env python3
"""Un score d'anomalie sur l'état d'entrée sert-il de capteur de situation à risque ?

L'idée testée
-------------
Notre faiblesse mesurée est la généralisation **temporelle** : sept plis négatifs sur dix-sept
en double aveugle, le pire à −41 %. Nous savons que la correction échoue parfois ; nous ne
savons pas le **prévoir**. La règle d'abstention actuelle est écrite à la main — « ne pas
corriger à la baisse quand le forçage annonce déjà un dépassement ».

L'hypothèse : un détecteur d'anomalies appliqué à l'**état d'entrée** (les 53 prédicteurs,
sans jamais voir l'observation) donnerait la version *apprise* de cette règle, et servirait de
capteur de situation anormale — utilisable avant la prévision, donc opérationnel.

Trois questions, trois réfutations possibles
-------------------------------------------
**Q1 — dérive.** Le score monte-t-il sur les deux ruptures documentées de la chaîne CAMS
(13/11 et 03/12/2024) ? Les dates sont **fixées d'avance**, jamais choisies après lecture.
*Réfuté si* le score ne se distingue pas du reste de la période : le détecteur ne voit pas un
changement du modèle amont, et l'usage « surveillance de dérive » tombe.

**Q2 — performance conditionnelle.** Le gain de la correction est-il moindre quand le score est
haut ? Et surtout — **le contrôle qui décide de tout** — le score apporte-t-il quelque chose
**au-delà de la valeur de CAMS elle-même** ? Les prédicteurs contiennent `cams` : un score
d'anomalie fera feu sur les journées à forte concentration, qui sont précisément celles où le
modèle se comporte autrement. Sans ce contrôle, on mesurerait un détecteur de fortes valeurs
rebaptisé capteur d'anomalie.
*Réfuté si* le score ne stratifie plus le gain **à valeur de CAMS fixée**.

**Q3 — modes fonctionnels.** Sur les journées anormales, une autre action gagne-t-elle ?
On compare trois politiques sur le même sous-ensemble : corriger toujours, s'abstenir (garder
CAMS brut), et corriger avec un modèle **entraîné sur les seules journées anormales**.
*Réfuté si* aucune ne bat « corriger toujours » de plus de 0,3 µg/m³ — le critère d'arrêt du
projet.

Ce que le script ne fait pas
----------------------------
Il n'importe pas le routeur de `Bencher_AD` : celui-ci **choisit un algorithme** par
méta-features, ce qui n'a de sens qu'avec plusieurs jeux de données. Sur un corpus unique, on
compare directement deux détecteurs éprouvés par ce benchmark — IForest (0,762 de VUS-PR moyen
sur ADBench) et ECOD (0,742). Si le signal n'existe avec aucun des deux, un détecteur plus
sophistiqué ne le fera pas apparaître ; s'il existe, alors le routeur devient pertinent.

Usage : python3 scripts/capteur_situation_anormale.py [--polluant O3]
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

from aq.eval.critere import seuil  # noqa: E402
from aq.eval import comparaison as cmp  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

# Dates **fixées avant toute lecture des scores** — ce sont les ruptures opérationnelles de la
# chaîne CAMS déjà documentées par le projet. Les choisir après coup transformerait le test en
# description.
RUPTURES = [pd.Timestamp("2024-11-13"), pd.Timestamp("2024-12-03")]
FENETRE_RUPTURE = 7  # jours de part et d'autre
# Le critère de rétention vit dans `aq.eval.critere` : **relatif au RMSE de base**,
# donc comparable entre polluants. L'ancien 0,3 µg/m³ absolu valait 2 % sur le NO₂
# et 11 % sur les PM2,5 — il écartait ces dernières par artefact d'unité.


def scores_anomalie(x: pd.DataFrame, groupes: pd.Series, methode: str) -> np.ndarray:
    """Score d'anomalie hors échantillon, par groupes de stations.

    Le détecteur est ajusté sur les stations d'entraînement et applique son score aux stations
    tenues à l'écart : aucun point n'est scoré par un modèle qui l'a vu. Il ne reçoit **que des
    prédicteurs** — jamais l'observation, jamais le résidu.
    """
    from pyod.models.ecod import ECOD
    from pyod.models.iforest import IForest

    fabrique = {"iforest": lambda: IForest(n_estimators=200, random_state=0, n_jobs=8),
                "ecod": lambda: ECOD(n_jobs=8)}[methode]

    score = np.full(len(x), np.nan)
    for g in sorted(groupes.unique()):
        test = (groupes == g).to_numpy()
        det = fabrique()
        det.fit(x[~test])
        score[test] = det.decision_function(x[test])
    return score


def q1_derive(j: pd.DataFrame, colonne: str) -> dict:
    """Le score monte-t-il sur les ruptures **déclarées d'avance** ?"""
    quotidien = j.groupby("jour")[colonne].mean()
    quotidien.index = pd.to_datetime(quotidien.index).tz_localize(None)

    proche = pd.Series(False, index=quotidien.index)
    for date in RUPTURES:
        proche |= (quotidien.index >= date) & (
            quotidien.index <= date + pd.Timedelta(days=FENETRE_RUPTURE))

    # Rang du score moyen des jours post-rupture dans la distribution des jours ordinaires :
    # une mesure sans hypothèse de forme, contrairement à un écart-type.
    dedans, dehors = quotidien[proche], quotidien[~proche]
    if dedans.empty:
        return {}
    percentile = float((dehors < dedans.mean()).mean() * 100)
    return {"n_jours_rupture": int(proche.sum()), "score_rupture": float(dedans.mean()),
            "score_ordinaire": float(dehors.mean()), "percentile": percentile}


def q2_conditionnel(j: pd.DataFrame, colonne: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Le gain baisse-t-il quand le score monte — et **au-delà de la valeur de CAMS** ?"""
    d = j.copy()
    d["gain"] = (d["obs_jour"] - d["cams_jour"]) ** 2 - (d["obs_jour"] - d["corrige"]) ** 2
    d["decile_score"] = pd.qcut(d[colonne], 10, labels=False, duplicates="drop")
    d["decile_cams"] = pd.qcut(d["cams_jour"], 10, labels=False, duplicates="drop")

    marginal = (d.groupby("decile_score")
                 .agg(n=("gain", "size"), gain_mse=("gain", "mean"),
                      cams_moyen=("cams_jour", "mean"), obs_moyen=("obs_jour", "mean"))
                 .reset_index())

    # **Le contrôle.** À décile de CAMS fixé, le score sépare-t-il encore ? On compare le gain
    # du tiers le plus anormal à celui du tiers le plus normal, *dans chaque bande de CAMS*.
    lignes = []
    for bande, g in d.groupby("decile_cams"):
        if len(g) < 200:
            continue
        bas, haut = g[colonne].quantile([1 / 3, 2 / 3])
        normal, anormal = g[g[colonne] <= bas], g[g[colonne] >= haut]
        if len(normal) < 50 or len(anormal) < 50:
            continue
        lignes.append({"decile_cams": int(bande), "cams_moyen": float(g["cams_jour"].mean()),
                       "n_normal": len(normal), "n_anormal": len(anormal),
                       "gain_normal": float(normal["gain"].mean()),
                       "gain_anormal": float(anormal["gain"].mean()),
                       "ecart": float(anormal["gain"].mean() - normal["gain"].mean())})
    return marginal, pd.DataFrame(lignes)


def q3_modes(j: pd.DataFrame, colonne: str, predicteurs: list[str]) -> pd.DataFrame:
    """Sur les journées anormales, une autre action gagne-t-elle ?"""

    seuil = j[colonne].quantile(0.90)
    anormal = j[j[colonne] >= seuil].copy()
    normal = j[j[colonne] < seuil]
    if len(anormal) < 500:
        return pd.DataFrame()

    # Politique 3 : un modèle **dédié aux journées anormales**, entraîné et évalué par plis de
    # stations pour rester hors échantillon — sans quoi il se noterait sur ses propres données.
    anormal["dedie"] = np.nan
    for g in sorted(anormal["groupe"].unique()):
        test = anormal["groupe"] == g
        entrainement = anormal[~test]
        if len(entrainement) < 300:
            continue
        # Capteur d'anomalie, pas le MOS : profondeur volontairement réduite pour un
        # détecteur entraîné sur un décile. Variante NOMMÉE du moteur unique, plutôt qu'un
        # modèle parallèle invisible à toute recherche.
        m = modele_mos(graine=0, num_leaves=31,
                       min_child_samples=REGLE["min_child_samples"],
                       reg_lambda=REGLE["reg_lambda"])
        m.fit(entrainement[predicteurs],
              entrainement["obs_jour"] - entrainement["cams_jour"])
        anormal.loc[test, "dedie"] = np.clip(
            anormal.loc[test, "cams_jour"] + m.predict(anormal.loc[test, predicteurs]), 0, None)

    politiques = [("corriger toujours", "corrige"), ("s'abstenir (CAMS brut)", "cams_jour"),
                  ("modèle dédié aux anormales", "dedie")]
    lignes = []
    for nom, col in politiques:
        sous = anormal.dropna(subset=[col])
        if sous.empty:
            continue
        m = cmp.metriques(sous["obs_jour"], sous[col])
        lignes.append({"politique": nom, "n": len(sous), **m})
    lignes.append({"politique": "— rappel : journées normales, corrigées", "n": len(normal),
                   **cmp.metriques(normal["obs_jour"], normal["corrige"])})
    return pd.DataFrame(lignes)


def main(polluant: str, methode: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    # Les prédictions corrigées existent déjà : on les reprend plutôt que de réapprendre.
    ref = pd.read_csv(RACINE / f"reports/mos_{polluant}_J1.csv",
                      parse_dates=["timestamp_utc"]).dropna(subset=["observe", "corrige"])
    ref["jour"] = ref["timestamp_utc"].dt.floor("D")
    ref = ref.sort_values(["station_id", "timestamp_utc"])
    ref["c8"] = ref.groupby("station_id")["corrige"].transform(
        lambda s: s.rolling(8, min_periods=6).mean())
    corrige = (ref.groupby(["station_id", "jour"])
                  .agg(corrige=("c8", "max"), n=("timestamp_utc", "size")).reset_index())
    corrige = corrige[corrige["n"] >= 18].drop(columns="n")
    j["jour"] = pd.to_datetime(j["jour"], utc=True)
    corrige["jour"] = pd.to_datetime(corrige["jour"], utc=True)
    j = j.merge(corrige, on=["station_id", "jour"], how="inner").dropna(subset=["corrige"])

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map(
        {s: i % n_plis for i, s in enumerate(stations)})

    print(f"{polluant} · {len(j):,} jours-station · {len(stations)} stations · "
          f"{len(predicteurs)} prédicteurs · détecteur **{methode}**", flush=True)

    colonne = f"score_{methode}"
    j[colonne] = scores_anomalie(j[predicteurs], j["groupe"], methode)
    print(f"  score calculé hors échantillon en {time.time() - depart:.0f}s\n", flush=True)

    # ── Q1 ────────────────────────────────────────────────────────────────────
    r1 = q1_derive(j, colonne)
    print("Q1 · DÉRIVE — le score monte-t-il sur les ruptures CAMS déclarées d'avance ?")
    if r1:
        print(f"  {r1['n_jours_rupture']} jours post-rupture · score moyen "
              f"{r1['score_rupture']:.4f} contre {r1['score_ordinaire']:.4f} en ordinaire")
        print(f"  → le score post-rupture se situe au **{r1['percentile']:.0f}ᵉ percentile** "
              f"des jours ordinaires")
        print(f"  verdict : {'signal net' if r1['percentile'] >= 80 else 'aucun signal exploitable'}",
              flush=True)

    # ── Q2 ────────────────────────────────────────────────────────────────────
    marginal, conditionnel = q2_conditionnel(j, colonne)
    print(f"\nQ2 · PERFORMANCE CONDITIONNELLE — gain (MSE évitée) par décile de score")
    print(f"{'décile':>7s} {'n':>8s} {'gain MSE':>10s} {'CAMS moyen':>11s} {'obs moyen':>10s}")
    for _, r in marginal.iterrows():
        print(f"{int(r['decile_score']):7d} {int(r['n']):8,} {r['gain_mse']:10.1f} "
              f"{r['cams_moyen']:11.1f} {r['obs_moyen']:10.1f}", flush=True)

    print(f"\n  LE CONTRÔLE — à décile de CAMS fixé, le score sépare-t-il encore ?")
    if conditionnel.empty:
        print("  (effectifs insuffisants)")
    else:
        print(f"{'décile CAMS':>12s} {'CAMS moy':>9s} {'gain normal':>12s} "
              f"{'gain anormal':>13s} {'écart':>9s}")
        for _, r in conditionnel.iterrows():
            print(f"{int(r['decile_cams']):12d} {r['cams_moyen']:9.1f} "
                  f"{r['gain_normal']:12.1f} {r['gain_anormal']:13.1f} {r['ecart']:+9.1f}",
                  flush=True)
        # **Le signal se juge sur la constance du signe, pas sur son sens.** Un écart
        # systématiquement positif informe autant qu'un écart négatif : dans les deux cas le
        # score dit quelque chose que la valeur de CAMS ne dit pas. Ne compter que les écarts
        # défavorables reviendrait à ne chercher que l'hypothèse de départ.
        part_neg = float((conditionnel["ecart"] < 0).mean())
        part_pos = float((conditionnel["ecart"] > 0).mean())
        constance = max(part_neg, part_pos)
        sens = "PLUS" if part_pos > part_neg else "MOINS"
        print(f"\n  À valeur de CAMS comparable, la correction rend **{sens}** sur les "
              f"journées anormales,\n  dans {constance * 100:.0f} % des bandes "
              f"(écart médian {conditionnel['ecart'].median():+.1f} de MSE).")
        if constance >= 0.7:
            print(f"  verdict : **le score porte une information que CAMS ne porte pas** — "
                  f"le contrôle de circularité est passé.")
            if sens == "PLUS":
                print(f"  ⚠️ Mais le sens contredit l'hypothèse de départ : les états "
                      f"d'entrée inhabituels\n     sont ceux où la correction est la plus "
                      f"utile, pas les plus risqués. Rien à couper.")
        else:
            print(f"  verdict : pas de signal propre — le score est un proxy de la "
                  f"concentration.")

    # ── Q3 ────────────────────────────────────────────────────────────────────
    modes = q3_modes(j, colonne, predicteurs)
    print(f"\nQ3 · MODES FONCTIONNELS — décile le plus anormal, trois politiques")
    if modes.empty:
        print("  (effectif insuffisant)")
    else:
        print(f"{'politique':36s} {'n':>8s} {'RMSE':>7s} {'biais':>7s} {'R²':>8s}")
        for _, r in modes.iterrows():
            print(f"{r['politique']:36s} {int(r['n']):8,} {r['rmse']:7.2f} "
                  f"{r['biais']:+7.2f} {r['r2']:+8.3f}", flush=True)
        actives = modes[~modes["politique"].str.startswith("—")]
        base = float(actives[actives["politique"] == "corriger toujours"]["rmse"].iloc[0])
        # La marge se mesure contre la **meilleure alternative**, pas contre le minimum global
        # — sinon la politique de référence se compare à elle-même et rend toujours 0,00.
        autres = actives[actives["politique"] != "corriger toujours"]
        meilleure = autres.loc[autres["rmse"].idxmin()]
        marge = base - float(meilleure["rmse"])
        print(f"\n  meilleure alternative : **{meilleure['politique']}** — "
              f"{float(meilleure['rmse']):.2f} contre {base:.2f} µg/m³, soit {marge:+.2f}")
        if marge >= seuil(base):
            print("  verdict : CONCLUANT — une action spécifique aux journées anormales gagne.")
        else:
            abstention = actives[actives["politique"].str.contains("abstenir")]
            cout = (float(abstention["rmse"].iloc[0]) - base if not abstention.empty
                    else float("nan"))
            print(f"  verdict : **aucun mode fonctionnel spécifique**. Corriger reste la "
                  f"meilleure action\n     même sur le décile le plus anormal ; s'abstenir y "
                  f"coûte {cout:+.2f} µg/m³.")

    sortie = RACINE / f"reports/capteur_anomalie_{polluant}_{methode}"
    marginal.to_csv(f"{sortie}_deciles.csv", index=False)
    conditionnel.to_csv(f"{sortie}_conditionnel.csv", index=False)
    modes.to_csv(f"{sortie}_politiques.csv", index=False)
    pd.DataFrame([r1]).to_csv(f"{sortie}_derive.csv", index=False)
    print(f"\nÉcrit : {sortie.name}_*.csv · {time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--methode", default="iforest", choices=("iforest", "ecod"))
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.methode, args.plis))
