"""La correction peut-elle cesser d'écraser les pics ? Test de pertes alternatives.

Usage : python scripts/preserver_la_queue.py [--polluant O3]
Sortie : reports/PRESERVER_LA_QUEUE.md et le CSV associé

**Le problème mesuré.** Sur l'ozone, la correction gagne 28 % de RMSE global mais
**dégrade de 17 %** le décile supérieur hors régime photochimique. La cause est connue :
minimiser une erreur quadratique sur une distribution asymétrique tire les extrêmes vers
la moyenne. Sur NO₂ et PM2.5, l'effet ne se produit pas — les pics y sont plus fréquents
et mieux échantillonnés.

**Les trois remèdes testés**, tous sans changer d'architecture :

- **perte quantile** (pinball) à q = 0,9 — le modèle vise le neuvième décile plutôt que
  la moyenne, donc n'a plus intérêt à raboter les valeurs hautes ;
- **erreur quadratique pondérée** — chaque observation pèse proportionnellement à sa
  concentration, ce qui rend une erreur sur un pic aussi coûteuse que plusieurs erreurs
  sur du fond ;
- **perte de Huber** — moins sensible aux valeurs extrêmes, testée comme témoin négatif :
  elle devrait *aggraver* l'écrasement, et le vérifier valide le protocole.

L'évaluation porte sur ce qui décide : le RMSE global **et** celui du décile supérieur.
Un remède qui sauve la queue en ruinant le cœur ne vaut rien.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402


def modele(objectif: str, graine: int = 0, **extra):
    from lightgbm import LGBMRegressor

    return LGBMRegressor(
        objective=objectif, n_estimators=400, learning_rate=0.05, num_leaves=63,
        min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
        random_state=graine, n_jobs=-1, verbose=-1, **extra,
    )


def main(polluant: str, horizon: int, n_plis: int) -> int:
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"]).reset_index(drop=True)

    seuil_haut = jeu["valeur"].quantile(0.90)
    print(f"{polluant} J+{horizon} · {len(jeu):,} paires · "
          f"décile supérieur au-delà de {seuil_haut:.1f} µg/m³\n", flush=True)

    stations = np.array(sorted(jeu["station_id"].unique()))
    rng = np.random.default_rng(0)
    groupes = np.array_split(rng.permutation(stations), n_plis)

    # Les poids sont normalisés pour que la somme reste comparable : sans cela, la
    # variante pondérée s'entraînerait sur un effectif effectif différent des autres.
    variantes = {
        "erreur quadratique (référence)": ("regression", {}, None),
        "quantile q=0,90 (pinball)": ("quantile", {"alpha": 0.90}, None),
        "quadratique pondérée par la concentration": ("regression", {}, "poids"),
        "Huber (témoin négatif)": ("huber", {}, None),
    }

    morceaux = {nom: [] for nom in variantes}
    for groupe in groupes:
        test_masque = jeu["station_id"].isin(groupe)
        entrainement, test = jeu[~test_masque], jeu[test_masque]
        cible = entrainement["valeur"] - entrainement["cams"]
        poids = (entrainement["valeur"] / entrainement["valeur"].mean()).to_numpy()

        for nom, (objectif, extra, pondere) in variantes.items():
            m = modele(objectif, **extra)
            m.fit(entrainement[colonnes], cible,
                  sample_weight=poids if pondere else None)
            predit = np.clip(
                test["cams"].to_numpy() + m.predict(test[colonnes]), 0, None)
            morceaux[nom].append(test[["station_id", "valeur", "cams"]]
                                 .assign(predit=predit))

    reference = pd.concat(morceaux["erreur quadratique (référence)"], ignore_index=True)
    haut_global = reference["valeur"] >= seuil_haut

    print(f"{'variante':44s} {'RMSE':>7s} {'RMSE décile sup.':>17s} {'vs CAMS':>9s}")
    m_cams = cmp.metriques(reference["valeur"], reference["cams"])
    m_cams_haut = cmp.metriques(reference.loc[haut_global, "valeur"],
                                reference.loc[haut_global, "cams"])
    print(f"{'CAMS brut':44s} {m_cams['rmse']:7.2f} {m_cams_haut['rmse']:17.2f}")

    lignes = []
    for nom in variantes:
        p = pd.concat(morceaux[nom], ignore_index=True)
        haut = p["valeur"] >= seuil_haut
        m = cmp.metriques(p["valeur"], p["predit"])
        m_haut = cmp.metriques(p.loc[haut, "valeur"], p.loc[haut, "predit"])
        gain_haut = 100 * (1 - m_haut["rmse"] / m_cams_haut["rmse"])
        lignes.append({"variante": nom, "rmse": m["rmse"], "rmse_haut": m_haut["rmse"],
                       "gain_global": 100 * (1 - m["rmse"] / m_cams["rmse"]),
                       "gain_haut": gain_haut, "biais_haut": m_haut["biais"]})
        print(f"{nom:44s} {m['rmse']:7.2f} {m_haut['rmse']:17.2f} "
              f"{gain_haut:+8.1f} %", flush=True)

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/queue_{polluant}.csv", index=False)

    # **Garder les prédictions, pas seulement les métriques.** Une variante coûte plusieurs
    # minutes d'ajustement ; sans les prédictions ligne à ligne, toute étude de combinaison
    # entre variantes — front de Pareto entre le RMSE global et celui de la queue — impose
    # de tout réajuster. Avec elles, elle est gratuite et rejouable.
    large = reference[["station_id", "valeur", "cams"]].copy()
    for nom in variantes:
        colonne = (nom.split(" (")[0].replace(" ", "_")
                      .replace(",", "").replace("=", "").lower())
        bloc = pd.concat(morceaux[nom], ignore_index=True)
        # Les variantes partagent les mêmes plis et le même `test` à chaque tour, donc le
        # même ordre de lignes. C'est vrai *par construction* — et c'est exactement le genre
        # d'alignement dont la rupture ne lèverait aucune erreur : on le vérifie.
        if not np.allclose(bloc["valeur"].to_numpy(), large["valeur"].to_numpy()):
            raise RuntimeError(f"désalignement des prédictions pour « {nom} »")
        large[colonne] = bloc["predit"].to_numpy()
    chemin_large = RACINE / f"reports/queue_predictions_{polluant}.csv"
    large.to_csv(chemin_large, index=False)
    print(f"Écrit : {chemin_large.name} · {len(large):,} lignes · "
          f"colonnes {[c for c in large.columns if c not in ('station_id','valeur','cams')]}")
    print(f"\n(« vs CAMS » porte sur le décile supérieur — c'est là que se joue "
          f"l'écrasement)")
    print(f"Écrit : queue_{polluant}.csv")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    parseur.add_argument("--plis", type=int, default=4)
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
