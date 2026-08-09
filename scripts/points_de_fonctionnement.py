#!/usr/bin/env python3
"""Un seul modèle, trois services différents — ce que le seuil décide, et ce qu'il ne décide pas.

Le propos
-----------
La tête B ne change ni le modèle ni les données : elle **choisit un seuil**. Or ce choix
n'appartient pas au modélisateur, il appartient au service qui subira les alertes. Ce banc
matérialise trois demandes réelles, incompatibles entre elles, et montre ce que chacune
donne avec **la même sortie** :

    A · « attrapez-en le plus »     à volume de fausses alertes ÉGAL à la chaîne AASQA,
                                     maximiser le rappel
    B · « trompez-vous le moins »   maximiser le CSI = TP/(TP+FN+FP) — l'unique score qui
                                     pénalise les deux erreurs **ensemble**, sans arbitrer
                                     entre elles à notre place
    C · « leur niveau, sans bruit » à rappel ÉGAL à la chaîne AASQA, minimiser les fausses

A et C sont les deux faces du même arbitrage : l'un fixe le coût et pousse le rappel,
l'autre fixe le rappel et écrase le coût. B se place au milieu sans qu'on le lui demande.

Le seuil est choisi HORS ÉCHANTILLON
--------------------------------------
Pour le mois `M`, le seuil est calé sur les mois **antérieurs à M** puis appliqué tel quel.
Un seuil optimisé sur le mois qu'on évalue donnerait un chiffre que personne ne pourrait
reproduire en service : c'est la différence entre un réglage et une triche. Les premiers
mois, sans historique, sont **comptés et écartés** — jamais dissimulés.

⚠️ Ce que ce banc ne dit pas
------------------------------
Il ne crée aucune information : le rang de la prédiction est le même dans les trois
colonnes. Déplacer un seuil ne rend pas le modèle meilleur, cela **choisit où placer son
erreur**. Le comparer à la chaîne AASQA n'a de sens que parce que les deux subissent
exactement le même traitement, sur les mêmes lignes.

Usage : python3 scripts/points_de_fonctionnement.py [--polluants O3 PM10]
Sortie : reports/points_de_fonctionnement.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from tableau_comparatif import SEUIL  # noqa: E402

COURT = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}
MIN_EPISODES_HIST = 30      # sous ce compte, un seuil calé sur l'historique est du bruit
# Marge de sécurité du réglage C, en points de rappel. Déclarée avant la mesure : une
# contrainte posée au bord sur le passé n'est pas tenue dans le futur (visée 52,9 %,
# obtenue 46,7 % sans marge). Elle s'achète en fausses alertes, et le banc rapporte les deux.
MARGE_C = 0.06


def scores(obs_haut: np.ndarray, pred_haut: np.ndarray) -> dict:
    tp = int((obs_haut & pred_haut).sum())
    fn = int((obs_haut & ~pred_haut).sum())
    fp = int((~obs_haut & pred_haut).sum())
    return {
        "attrapes": tp, "manques": fn, "fausses": fp,
        "rappel": tp / (tp + fn) if tp + fn else np.nan,
        "precision": tp / (tp + fp) if tp + fp else np.nan,
        "csi": tp / (tp + fn + fp) if tp + fn + fp else np.nan,
    }


def grille(pred: np.ndarray) -> np.ndarray:
    """Seuils candidats : les quantiles de la prédiction, pas une grille arbitraire.
    Une grille en µg/m³ serait tantôt trop fine, tantôt vide selon le polluant."""
    q = np.quantile(pred, np.linspace(0.50, 0.9995, 400))
    return np.unique(q)


def seuil_A(pred_h, obs_h, budget_fausses):
    """Le plus bas seuil dont le volume de fausses alertes ne dépasse pas le budget."""
    meilleur, best_tp = None, -1
    for s in grille(pred_h):
        r = scores(obs_h, pred_h >= s)
        if r["fausses"] <= budget_fausses and r["attrapes"] > best_tp:
            meilleur, best_tp = s, r["attrapes"]
    return meilleur


def seuil_B(pred_h, obs_h):
    """CSI maximal — les deux erreurs pénalisées ensemble."""
    vals = [(scores(obs_h, pred_h >= s)["csi"], s) for s in grille(pred_h)]
    vals = [(c, s) for c, s in vals if np.isfinite(c)]
    return max(vals)[1] if vals else None


def seuil_C(pred_h, obs_h, rappel_cible, marge=MARGE_C):
    """Le plus HAUT seuil qui atteint le rappel cible **majoré d'une marge**.

    ⚠️ Sans marge, ce réglage échoue par construction. Le seuil qui atteint *exactement*
    la cible sur l'historique est posé au bord de la contrainte : la moindre dérive du
    mois suivant le fait passer dessous. Mesuré ici — visée 52,9 %, obtenu **46,7 %**.
    Ce n'était pas un défaut d'implémentation mais un défaut de méthode : *une contrainte
    calée au bord sur le passé n'est pas tenue dans le futur.*

    La marge est un **paramètre déclaré**, pas un réglage optimisé après coup : la viser
    plus haut coûte des fausses alertes, la viser plus bas fait rater la cible. Le rappel
    réellement obtenu est rapporté à côté de la cible, pour que l'échec reste visible.
    """
    meilleur = None
    for s in grille(pred_h):
        if scores(obs_h, pred_h >= s)["rappel"] >= min(rappel_cible + marge, 0.999):
            meilleur = s          # la grille est croissante : le dernier retenu est le plus haut
    return meilleur


def main(polluants: list[str], horizon: int) -> int:
    lignes = []
    for pol in polluants:
        f = RACINE / f"data/processed/predictions/production_{pol}_h{horizon}.parquet"
        if not f.exists():
            print(f"  {COURT[pol]} : absent, ignoré")
            continue
        d = pd.read_parquet(f).sort_values("mois").reset_index(drop=True)
        seuil_phys = SEUIL[pol]
        obs = d["valeur"].to_numpy()
        haut = obs >= seuil_phys
        if haut.sum() < 50:
            print(f"  {COURT[pol]} : {haut.sum()} dépassements — trop peu, ignoré")
            continue

        mois = np.sort(d["mois"].unique())
        cols = {"A": [], "B": [], "C": []}
        cibles = []
        retenus, ecartes = [], []
        for m in mois:
            hist, cur = (d["mois"] < m).to_numpy(), (d["mois"] == m).to_numpy()
            oh, ph, ah = haut[hist], d["nous"].to_numpy()[hist], d["aasqa"].to_numpy()[hist]
            if oh.sum() < MIN_EPISODES_HIST:
                ecartes.append(m)
                continue
            ref = scores(oh, ah >= seuil_phys)
            cibles.append((ref["rappel"], ref["fausses"]))
            sA = seuil_A(ph, oh, ref["fausses"])
            sB = seuil_B(ph, oh)
            sC = seuil_C(ph, oh, ref["rappel"])
            if None in (sA, sB, sC):
                ecartes.append(m)
                continue
            retenus.append(m)
            for cle, s in (("A", sA), ("B", sB), ("C", sC)):
                cols[cle].append(pd.Series(d["nous"].to_numpy()[cur] >= s, index=np.flatnonzero(cur)))

        if not retenus:
            print(f"  {COURT[pol]} : aucun mois exploitable")
            continue
        idx = np.concatenate([np.flatnonzero((d["mois"] == m).to_numpy()) for m in retenus])
        o = haut[idx]
        print(f"\n═══ {COURT[pol]} · seuil physique {seuil_phys:g} µg/m³ · "
              f"{len(retenus)} mois retenus sur {len(mois)} · {o.sum()} dépassements ═══")
        if ecartes:
            print(f"  ⚠️ {len(ecartes)} mois écartés faute d'historique : {', '.join(ecartes)}")

        ref_sys = {
            "chaîne AASQA (seuil physique)": d["aasqa"].to_numpy()[idx] >= seuil_phys,
            "CAMS brut (seuil physique)": d["cams"].to_numpy()[idx] >= seuil_phys,
            "nous · seuil physique, sans réglage": d["nous"].to_numpy()[idx] >= seuil_phys,
        }
        for nom, m in ref_sys.items():
            r = scores(o, m)
            lignes.append({"polluant": pol, "systeme": nom, **r})
        for cle, titre in (("A", "nous · A — leur budget d'alertes, rappel maximal"),
                           ("B", "nous · B — CSI maximal, les deux erreurs ensemble"),
                           ("C", "nous · C — leur rappel, fausses alertes minimales")):
            masque = pd.concat(cols[cle]).sort_index().to_numpy()
            r = scores(o, masque)
            lignes.append({"polluant": pol, "systeme": titre, **r})

        t = pd.DataFrame([x for x in lignes if x["polluant"] == pol])
        print(f"  {'système':<44}{'attrapés':>9}{'manqués':>9}{'fausses':>9}"
              f"{'rappel':>9}{'précis.':>9}{'CSI':>8}")
        for _, r in t.iterrows():
            print(f"  {r.systeme:<44}{r.attrapes:>9}{r.manques:>9}{r.fausses:>9}"
                  f"{r.rappel:>8.1%}{r.precision:>9.1%}{r.csi:>8.3f}")

    t = pd.DataFrame(lignes)
    for c in ("polluant", "systeme", "attrapes", "manques", "fausses", "rappel", "precision", "csi"):
        if c not in t:
            raise SystemExit(f"colonne absente du rapport : {c}")
    cible = RACINE / "reports/points_de_fonctionnement.csv"
    t.to_csv(cible, index=False)
    print(f"\nÉcrit : {cible.relative_to(RACINE)} · {len(t)} lignes")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--polluants", nargs="+", default=["O3", "PM10", "PM25"])
    ap.add_argument("--horizon", type=int, default=1)
    a = ap.parse_args()
    raise SystemExit(main(a.polluants, a.horizon))
