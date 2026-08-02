#!/usr/bin/env python3
"""Prédire la probabilité de dépassement, plutôt que seuiller une concentration prédite.

Le raisonnement
---------------
Le projet prédit une concentration puis la compare à un seuil. Or une régression minimise
une erreur quadratique **moyenne** : elle est optimisée pour le gros de la distribution, et
c'est mesuré ici — sur le décile supérieur d'ozone, la correction est pire que CAMS brut, et
le biais de fréquence des dépassements vaut 0,43, c'est-à-dire une sous-annonce d'un facteur
deux.

Une classification, elle, optimise directement la séparation entre « dépasse » et « ne
dépasse pas ». Elle ne rend pas de concentration — donc elle ne remplace pas la régression,
elle répond à une autre question, qui est celle du service : *faut-il regarder ce jour-là ?*

Ce que le script compare, sur les **mêmes** jours-station et le **même** seuil :

1. **seuillage de la régression** — la pratique actuelle ;
2. **classification directe** — probabilité de dépassement, seuillée à son tour.

Et il mesure la **calibration**, que la régression ne fournit pas : une probabilité de 0,3
doit correspondre à trois dépassements sur dix. Sans calibration, une probabilité n'est
qu'un score, inutilisable pour arbitrer entre alerte manquée et fausse alerte.

Le **score de Brier** et son *skill score* face à la fréquence de base tranchent : un skill
négatif signifie qu'annoncer toujours la fréquence climatologique ferait mieux.

Usage : python3 scripts/classification_depassement.py [--polluant O3] [--plis 3]
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

from aq.models import mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from scores_episodes import scores  # noqa: E402

# Seuils par grandeur réglementaire, en µg/m³ — les mêmes que `scores_episodes.py`.
SEUILS = {"O3": [120.0, 130.0], "NO2": [120.0], "PM25": [25.0]}


class ProbabiliteDeDepassement:
    """Classifieur exposé comme un régresseur, pour réutiliser le protocole de validation.

    `ajuster_par_stations_exclues` appelle `predict`. On y renvoie la **probabilité** de la
    classe positive plutôt qu'une étiquette : c'est elle qui porte l'information, et la
    seuiller ensuite permet de choisir le point de fonctionnement après coup, sans
    réajuster.
    """

    def __init__(self, graine: int):
        from lightgbm import LGBMClassifier

        self._modele = LGBMClassifier(
            n_estimators=400, learning_rate=0.05, num_leaves=63,
            min_child_samples=200, subsample=0.8, subsample_freq=1,
            colsample_bytree=0.8, random_state=graine, n_jobs=-1, verbose=-1,
        )

    def fit(self, X, y, **kwargs):
        self._modele.fit(X, y, **kwargs)
        return self

    def predict(self, X):
        return self._modele.predict_proba(X)[:, 1]

    @property
    def feature_importances_(self):
        return self._modele.feature_importances_


def brier(observe: np.ndarray, probabilite: np.ndarray) -> dict:
    """Score de Brier et *skill score* face à la fréquence de base.

    Le skill score rapporte l'erreur à celle d'une prévision constante égale à la fréquence
    climatologique. **Négatif, il condamne le modèle** : mieux valait annoncer la fréquence.
    """
    base = float(observe.mean())
    bs = float(np.mean((probabilite - observe) ** 2))
    bs_ref = float(np.mean((base - observe) ** 2))
    return {"brier": bs, "brier_reference": bs_ref,
            "brier_skill": 1 - bs / bs_ref if bs_ref > 0 else np.nan,
            "frequence_base": base}


def fiabilite(observe: np.ndarray, probabilite: np.ndarray, n_paniers: int = 10) -> str:
    """Courbe de fiabilité en texte : probabilité annoncée contre fréquence constatée."""
    bornes = np.linspace(0, 1, n_paniers + 1)
    lignes = []
    for i in range(n_paniers):
        dans = (probabilite >= bornes[i]) & (probabilite < bornes[i + 1] + (i == n_paniers - 1))
        if dans.sum() < 50:
            continue
        lignes.append(f"    [{bornes[i]:.1f};{bornes[i+1]:.1f}[ "
                      f"annoncé {probabilite[dans].mean():.3f} · "
                      f"constaté {observe[dans].mean():.3f} · n={int(dans.sum()):,}")
    return "\n".join(lignes) or "    (aucun panier suffisamment peuplé)"


def main(polluant: str, horizon: int, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    journalier = agreger_journalier(jeu, colonnes, grandeur)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    print(f"{polluant} · {grandeur} · {len(journalier):,} jours-station · "
          f"{journalier['station_id'].nunique()} stations\n", flush=True)

    # ── Voie 1 : régression sur la grandeur du jour, puis seuillage ────────────
    entree = journalier.rename(columns={"obs_jour": "valeur", "jour": "timestamp_utc"})
    regression = mos.ajuster_par_stations_exclues(
        entree, predicteurs, colonne_cams="cams_jour", n_plis=n_plis, verbeux=False,
    ).predictions.dropna(subset=["observe"])

    lignes = []
    for seuil in SEUILS.get(polluant, []):
        depasse = (regression["observe"] >= seuil).to_numpy()
        if depasse.sum() < 100:
            print(f"seuil {seuil:.0f} : {int(depasse.sum())} dépassements, trop peu — ignoré")
            continue

        print(f"=== seuil {seuil:.0f} µg/m³ · {int(depasse.sum()):,} dépassements observés "
              f"({100 * depasse.mean():.2f} %) ===", flush=True)

        s_reg = scores(depasse, (regression["corrige"] >= seuil).to_numpy())
        print(f"  régression seuillée      POD {s_reg['POD']:.3f} · FAR {s_reg['FAR']:.3f} "
              f"· CSI {s_reg['CSI']:.3f} · FB {s_reg['FB']:.3f}", flush=True)
        lignes.append({"seuil": seuil, "voie": "régression seuillée", **s_reg})

        # ── Voie 2 : classification directe de l'événement ─────────────────────
        cible = entree.copy()
        cible["valeur"] = (cible["valeur"] >= seuil).astype(int)
        # `cible_residu=False` : on apprend l'événement lui-même, pas un écart à CAMS.
        proba = mos.ajuster_par_stations_exclues(
            cible, predicteurs, colonne_cams="cams_jour", n_plis=n_plis,
            cible_residu=False, verbeux=False,
            fabrique_modele=ProbabiliteDeDepassement,
        ).predictions.dropna(subset=["observe"])

        p = np.clip(proba["corrige"].to_numpy(), 0.0, 1.0)
        vrai = proba["observe"].to_numpy().astype(bool)
        b = brier(vrai.astype(float), p)
        print(f"  Brier {b['brier']:.5f} · référence {b['brier_reference']:.5f} · "
              f"**skill {b['brier_skill']:+.3f}** · fréquence de base {b['frequence_base']:.4f}")
        print("  fiabilité (annoncé contre constaté) :")
        print(fiabilite(vrai.astype(float), p), flush=True)

        # ── Le point de fonctionnement ────────────────────────────────────────
        # **Le modèle n'est pas réajusté, mais le seuil est un paramètre appris.** Retenir le
        # meilleur CSI parmi sept seuils balayés sur les données qui l'évaluent fabrique un
        # score : c'est le même défaut que seuiller une régression sur son propre test, corrigé
        # ailleurs dans ce projet et resté ici. On mesure donc les deux, et l'écart entre eux
        # **est** l'optimisme de sélection.
        grille = (0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50)
        for pr in grille:
            s = scores(vrai, p >= pr)
            lignes.append({"seuil": seuil, "voie": f"classification p≥{pr:.2f}",
                           "brier_skill": b["brier_skill"], **s})
            print(f"  classification p≥{pr:.2f}   POD {s['POD']:.3f} · FAR {s['FAR']:.3f} "
                  f"· CSI {s['CSI']:.3f} · FB {s['FB']:.3f}", flush=True)

        oracle_pr = max(grille, key=lambda x: scores(vrai, p >= x).get("CSI") or 0)
        s_oracle = scores(vrai, p >= oracle_pr)

        # Choix honnête : le seuil est fixé sur d'**autres stations** que celles où il est
        # appliqué. Les probabilités sont déjà hors échantillon vis-à-vis du modèle ; ce
        # découpage-ci ne protège que le choix du seuil.
        stations = np.sort(proba["station_id"].unique())
        groupe = proba["station_id"].map({s_: i % n_plis for i, s_ in enumerate(stations)})
        annonce = np.zeros(len(p), dtype=bool)
        seuils_retenus = []
        for g in range(n_plis):
            test = (groupe == g).to_numpy()
            if test.sum() == 0 or (~test).sum() == 0:
                continue
            choisi = max(grille,
                         key=lambda x: scores(vrai[~test], p[~test] >= x).get("CSI") or 0)
            seuils_retenus.append(choisi)
            annonce[test] = p[test] >= choisi
        s_honnete = scores(vrai, annonce)
        lignes.append({"seuil": seuil, "voie": "classification, seuil hors échantillon",
                       "brier_skill": b["brier_skill"], **s_honnete})

        print(f"\n  seuil choisi sur les données évaluées (optimiste) : p≥{oracle_pr:.2f} · "
              f"CSI {s_oracle['CSI']:.3f} · POD {s_oracle['POD']:.3f}")
        print(f"  seuil choisi sur d'autres stations (honnête)      : "
              f"p≥{'/'.join(f'{x:.2f}' for x in sorted(set(seuils_retenus)))} · "
              f"CSI {s_honnete['CSI']:.3f} · POD {s_honnete['POD']:.3f}")
        print(f"  optimisme de sélection : {s_oracle['CSI'] - s_honnete['CSI']:+.3f} de CSI")

        gain_csi = s_honnete["CSI"] - s_reg["CSI"]
        verdict = ("CONCLUANT" if gain_csi >= 0.02 else "NON CONCLUANT (< +0,02 de CSI)")
        print(f"  → contre la régression seuillée ({s_reg['CSI']:.3f}) : {gain_csi:+.3f} "
              f"→ {verdict}\n", flush=True)

    if lignes:
        sortie = RACINE / f"reports/classification_depassement_{polluant}.csv"
        pd.DataFrame(lignes).to_csv(sortie, index=False)
        print(f"Écrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
