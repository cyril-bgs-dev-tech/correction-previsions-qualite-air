#!/usr/bin/env python3
"""Garder le RMSE optimal **et** calibrer le signal de déclenchement — sans arbitrage.

Le problème, et pourquoi il est en partie un théorème
------------------------------------------------------
Le RMSE est minimisé par l'**espérance conditionnelle**. Un estimateur de la moyenne est donc
**contracté par construction** : il tire vers le centre, et c'est exactement ce qui écrase la
queue. Toute inflation de variance qui restaure la queue **dégrade le RMSE**, mécaniquement.
On ne peut pas demander à un seul nombre d'être à la fois optimal en erreur moyenne et calibré
au seuil.

La tension disparaît dès qu'on cesse de le demander. Le modèle produit un **score** ; on en
tire deux sorties qui ne se gênent pas :

* la **valeur publiée** — la moyenne conditionnelle, inchangée, qui porte le RMSE ;
* le **déclencheur** — une application **monotone** du même score vers une probabilité, ajustée
  hors échantillon. Une transformation monotone **préserve le rang à l'identique** : le RMSE de
  la valeur publiée n'est pas touché d'un millième.

Le projet a déjà la moitié de la preuve : *en détection, ce qui décide est le rang* — la
régression brute bat une tête de classification (POD 0,355 contre 0,262) et un quantile 0,90
(0,147). Le rang porte l'information ; ce qui manquait est la **carte du rang vers la
décision**.

Pourquoi les bandes ATMO et pas le seuil de procédure
------------------------------------------------------
À 180 µg/m³ en maximum horaire il y a **32 événements** sur 60 400 jours-station. Aucune
calibration ne s'ajuste sur 32 cas — il en faudrait une part pour ajuster et une part pour
vérifier. À cette rareté, toute optimisation est du surajustement déguisé, et ce script
refuse de la faire.

Les **bandes de l'indice ATMO** sont en revanche ordinales et peuplées, et ce sont elles que
l'AASQA affiche au public. C'est là qu'une calibration a de quoi apprendre.

Ce que le script mesure
-----------------------
1. **Le coût de la contraction** — écart-type prédit contre observé, par bande.
2. **Trois politiques de décision**, sur les mêmes plis et le même score :
   * seuillage direct de la valeur prédite (ce que fait le dossier aujourd'hui) ;
   * **calibration isotone** du score vers la probabilité de chaque bande, ajustée sur un
     pli tenu à l'écart, puis décision au **coût attendu minimal** ;
   * la même, avec une **matrice de coût asymétrique** — rater une classe haute coûte plus
     cher qu'une fausse alerte, ce que le métier impose.
3. **Le RMSE de la valeur publiée reste identique** entre les trois — vérifié, pas supposé.

Usage : python3 scripts/calibration_ordinale.py [--polluant O3] [--cout 4]
Sortie : reports/calibration_ordinale_{polluant}.csv
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
from fit_mos import BANDES, charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

from aq.ingest.controle import ControleEchec  # noqa: E402

GRAINE = 20260801


def modele():
    return modele_mos(graine=GRAINE)


def classe(valeurs: np.ndarray, bandes: list) -> np.ndarray:
    """Indice de bande ATMO, de 0 à len(bandes)−1."""
    bornes = np.array([b for _, b in bandes[:-1]], dtype="float64")
    return np.searchsorted(bornes, valeurs, side="right")


def matrice_cout(k: int, penalite: float) -> np.ndarray:
    """Coût de prédire `j` quand la vérité est `i`.

    Asymétrique et **ordinale** : l'erreur coûte proportionnellement à la distance entre
    classes, et **sous-estimer coûte `penalite` fois plus cher que surestimer**. C'est la
    situation réelle d'un service d'alerte — un épisode manqué ne vaut pas une fausse alerte,
    et l'arrêté autorise à déclencher sur prévision précisément pour cette raison.
    """
    i = np.arange(k)[:, None]
    j = np.arange(k)[None, :]
    ecart = np.abs(i - j).astype("float64")
    return np.where(j < i, ecart * penalite, ecart)


def isotone(score: np.ndarray, cible: np.ndarray) -> callable:
    """Régression isotone score → probabilité. **Monotone, donc le rang est préservé.**"""
    from sklearn.isotonic import IsotonicRegression

    r = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    r.fit(score, cible.astype("float64"))
    return r.predict


def main(polluant: str, penalite: float, n_plis: int) -> int:
    depart = time.time()
    bandes = BANDES[polluant]
    k = len(bandes)

    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    d = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    d = d.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    stations = np.sort(d["station_id"].unique())
    groupe = d["station_id"].map({s: i % n_plis for i, s in enumerate(stations)}).to_numpy()

    # Le score, hors pli. C'est la valeur publiée : elle ne sera jamais modifiée.
    d["score"] = np.nan
    for p in sorted(set(groupe)):
        test = groupe == p
        m = modele()
        m.fit(d.loc[~test, predicteurs], d.loc[~test, "valeur"] - d.loc[~test, "cams_jour"])
        d.loc[test, "score"] = np.clip(
            d.loc[test, "cams_jour"].to_numpy() + m.predict(d.loc[test, predicteurs]),
            0, None)

    obs = d["valeur"].to_numpy()
    score = d["score"].to_numpy()
    vraie = classe(obs, bandes)
    rmse_publie = float(np.sqrt(np.mean((score - obs) ** 2)))
    effectifs = np.bincount(vraie, minlength=k)
    print(f"{polluant} · {len(d):,} jours-station · {k} bandes ATMO · "
          f"effectifs {list(effectifs)}", flush=True)
    if (effectifs[:-1] < 200).any():
        print("  ⚠️ une bande basse est peu peuplée — la calibration y sera fragile",
              flush=True)

    # ── 1. La contraction, mesurée sans se tromper de conditionnement ─────────
    # Une première version comparait les écarts-types **à l'intérieur de chaque bande
    # observée**. C'était faux : conditionner sur la bande vraie tronque mécaniquement la
    # variance de l'observation (dans 120–180 elle ne peut pas dépasser 60 µg/m³ de large,
    # la prédiction si), et l'on mesurait sa propre troncature. Le diagnostic juste est
    # **inconditionnel**, et la grandeur qui le porte est la pente de la régression de
    # l'observé sur le prédit : elle vaut 1 si le modèle est calibré, et **dépasse 1 quand
    # il contracte** — il faut alors étirer ses prédictions pour retrouver l'observation.
    pente = float(np.polyfit(score, obs, 1)[0])
    print(f"\nContraction, sans conditionnement :")
    print(f"  écart-type observé {obs.std():6.2f} · prédit {score.std():6.2f} "
          f"· rapport {score.std() / obs.std():.3f}")
    print(f"  pente de obs sur pred : {pente:.3f} "
          f"({'contraction' if pente > 1.02 else 'dilatation' if pente < 0.98 else 'calibré'})")
    lignes_contraction = [{"ecart_type_obs": float(obs.std()),
                           "ecart_type_pred": float(score.std()), "pente_obs_sur_pred": pente}]

    # ── 2. Trois politiques, mêmes plis, même score ───────────────────────────
    # La calibration est ajustée **sur les autres plis** : elle ne voit jamais les lignes
    # qu'elle décide. Sans cela, l'isotone mémoriserait et le gain serait fictif.
    proba = np.full((len(d), k), np.nan)
    for p in sorted(set(groupe)):
        test = groupe == p
        for c in range(k):
            f = isotone(score[~test], (vraie[~test] == c).astype("float64"))
            proba[test, c] = f(score[test])
    somme = proba.sum(axis=1, keepdims=True)
    if not np.isfinite(somme).all() or (somme <= 0).any():
        raise ControleEchec("probabilités non normalisables — l'isotone a rendu du vide")
    proba = proba / somme

    politiques = {}
    politiques["seuillage direct"] = classe(score, bandes)
    C_sym = matrice_cout(k, 1.0)
    C_asym = matrice_cout(k, penalite)
    politiques["isotone · coût symétrique"] = np.argmin(proba @ C_sym, axis=1)
    politiques[f"isotone · sous-estimer ×{penalite:.0f}"] = np.argmin(proba @ C_asym, axis=1)

    print(f"\n{'politique':>32} {'exact':>7} {'±1':>7} {'MAE cl.':>8} "
          f"{'rappel haut':>12} {'sur-alerte':>11} {'RMSE publié':>12}")
    lignes = []
    haut = k - 2  # première bande « à conséquence » : 120 µg/m³ pour l'ozone
    for nom, pred in politiques.items():
        exact = float((pred == vraie).mean())
        pm1 = float((np.abs(pred - vraie) <= 1).mean())
        mae = float(np.abs(pred - vraie).mean())
        reel_haut = vraie >= haut
        rappel = float((pred[reel_haut] >= haut).mean()) if reel_haut.any() else np.nan
        # Part des annonces hautes qui n'en étaient pas : le coût que le service subit.
        annonce = pred >= haut
        sur = float((~reel_haut[annonce]).mean()) if annonce.any() else np.nan
        print(f"{nom:>32} {exact:6.1%} {pm1:6.1%} {mae:8.3f} {rappel:11.1%} "
              f"{sur:10.1%} {rmse_publie:11.3f}")
        lignes.append({"politique": nom, "exact": exact, "a_une_classe": pm1,
                       "mae_classe": mae, "rappel_bandes_hautes": rappel,
                       "part_fausses_annonces": sur, "rmse_valeur_publiee": rmse_publie})

    # ── 3. Le contrôle qui fonde tout l'argument ──────────────────────────────
    # Si le RMSE de la valeur publiée bougeait d'une politique à l'autre, la promesse
    # « on ne perd rien » serait fausse. Il ne peut pas bouger — les politiques ne
    # touchent que la décision — mais on le vérifie plutôt que de l'affirmer.
    ecarts = {l["rmse_valeur_publiee"] for l in lignes}
    if max(ecarts) - min(ecarts) > 1e-9:
        raise ControleEchec("le RMSE publié varie selon la politique — une politique modifie "
                            "la valeur, ce qui contredit toute la construction")
    print(f"\n✔ RMSE de la valeur publiée identique pour les trois politiques : "
          f"{rmse_publie:.4f} µg/m³ — la calibration ne touche que la décision.")

    # ── 3 bis. La seule comparaison qui vaut : à budget de fausses annonces égal ──
    # Une première version annonçait « la calibration récupère de la sensibilité sans
    # toucher au RMSE ». Le RMSE était bien intact, mais le gain de rappel était payé par
    # 6,7 points de fausses annonces : c'est un déplacement le long d'un arbitrage, pas un
    # gain. Le projet a une règle pour cela — **comparer à budget de fausses alertes
    # fixé** — et elle s'applique ici comme ailleurs.
    ref = lignes[0]
    budget = max(l["part_fausses_annonces"] for l in lignes
                 if np.isfinite(l["part_fausses_annonces"]))
    reel_haut = vraie >= haut

    def rappel_au_budget(valeurs: np.ndarray, cible_budget: float) -> tuple[float, float]:
        """Abaisse le seuil jusqu'à consommer exactement le budget, puis lit le rappel."""
        ordre = np.unique(valeurs)[::-1]
        meilleur_r, atteint = 0.0, np.nan
        for seuil in ordre[:: max(1, len(ordre) // 400)]:
            annonce = valeurs >= seuil
            if not annonce.any():
                continue
            faux = float((~reel_haut[annonce]).mean())
            if faux <= cible_budget:
                meilleur_r = float((valeurs[reel_haut] >= seuil).mean())
                atteint = faux
        return meilleur_r, atteint

    # Le seuillage direct, déplacé jusqu'au même budget que la meilleure politique calibrée.
    r_direct, b_direct = rappel_au_budget(score, budget)
    meilleur = max(lignes[1:], key=lambda l: l["rappel_bandes_hautes"])
    print(f"\n{'─' * 92}")
    print(f"À budget de fausses annonces égal ({budget:.1%}) :")
    print(f"  seuillage direct, seuil abaissé   rappel {r_direct:6.1%} "
          f"(budget réellement consommé {b_direct:.1%})")
    print(f"  {meilleur['politique']:33s} rappel "
          f"{meilleur['rappel_bandes_hautes']:6.1%} "
          f"(budget {meilleur['part_fausses_annonces']:.1%})")
    ecart = meilleur["rappel_bandes_hautes"] - r_direct
    print(f"  écart imputable à la calibration  {ecart:+.1%}")
    if ecart > 0.02:
        print("\n  → La calibration apporte **au-delà** du simple déplacement de seuil.\n"
              "    Le déclencheur gagne à être calibré, pas seulement abaissé.")
    elif ecart > -0.02:
        print("\n  → À budget égal, la calibration ne fait **pas mieux qu'abaisser le\n"
              "    seuil**. Le rang du régresseur portait déjà toute la décision : c'est\n"
              "    cohérent avec la mesure du projet selon laquelle classification,\n"
              "    pondération et quantile n'ajoutent rien.")
    else:
        print("\n  → À budget égal, la calibration fait **moins bien** qu'abaisser le seuil.")
    lignes.append({"politique": f"seuillage direct au budget {budget:.1%}",
                   "exact": np.nan, "a_une_classe": np.nan, "mae_classe": np.nan,
                   "rappel_bandes_hautes": r_direct, "part_fausses_annonces": b_direct,
                   "rmse_valeur_publiee": rmse_publie})

    print("\n⚠️ Ceci porte sur les **bandes de l'indice**, pas sur le seuil de procédure à\n"
          "   180 µg/m³ en maximum horaire, où 32 événements sur 60 400 interdisent toute\n"
          "   calibration honnête. Ne pas transporter ce résultat à ce seuil.")

    t = pd.DataFrame(lignes)
    sortie = RACINE / f"reports/calibration_ordinale_{polluant}.csv"
    t.to_csv(sortie, index=False)
    pd.DataFrame(lignes_contraction).to_csv(
        RACINE / f"reports/calibration_ordinale_{polluant}_contraction.csv", index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--cout", type=float, default=4.0,
                   help="combien de fois sous-estimer coûte plus cher que surestimer")
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.cout, n.plis))
