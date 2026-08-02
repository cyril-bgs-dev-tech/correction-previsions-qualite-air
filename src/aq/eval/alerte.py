"""Métriques de détection pour un usage d'alerte — le rappel avant tout.

**Pourquoi ce module existe séparément.** Un RMSE, un R², même un taux d'accord de
classe, traitent les erreurs symétriquement. Le métier d'une AASQA ne l'est pas : ne pas
annoncer un épisode qui survient expose la population et engage la responsabilité de
l'organisme ; annoncer un épisode qui ne survient pas coûte de la crédibilité. Les deux
sont des fautes, elles ne pèsent pas le même poids, et **aucune métrique agrégée ne
distingue les deux**.

Le texte lui-même consacre cette asymétrie : l'arrêté du 07/04/2016 autorise le
déclenchement des procédures **sur prévision**, sans attendre le constat — précisément
pour ne pas manquer d'épisode.

Conséquence pratique : un modèle qui réduit les fausses alertes tout en manquant
davantage d'épisodes est **une régression**, quelle que soit l'amélioration de ses
métriques moyennes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Pondération du F-bêta. β > 1 accorde plus de poids au rappel qu'à la précision ;
# β = 2 signifie « manquer un épisode coûte quatre fois une fausse alerte », ordre de
# grandeur usuel dans les usages d'alerte sanitaire. Le choix est discutable et doit
# être discuté — mais il doit être explicite, ce qu'un F1 muet ne fait pas.
BETA_ALERTE = 2.0


def matrice_detection(observe_positif, predit_positif) -> dict[str, int]:
    """Effectifs des quatre cas, sur les paires complètes."""
    observe = np.asarray(observe_positif, dtype=bool)
    predit = np.asarray(predit_positif, dtype=bool)
    return {
        "vrais_positifs": int((observe & predit).sum()),
        "faux_negatifs": int((observe & ~predit).sum()),
        "faux_positifs": int((~observe & predit).sum()),
        "vrais_negatifs": int((~observe & ~predit).sum()),
    }


def metriques_alerte(observe_positif, predit_positif) -> dict[str, float]:
    """Rappel, précision, F-bêta et taux de fausse alerte.

    Le **rappel** est la part des épisodes réels que le modèle annonce : c'est la
    grandeur déterminante. La précision vient ensuite, et le F-bêta les combine avec un
    poids explicite.
    """
    m = matrice_detection(observe_positif, predit_positif)
    vp, fn, fp, vn = (m["vrais_positifs"], m["faux_negatifs"],
                      m["faux_positifs"], m["vrais_negatifs"])

    rappel = vp / (vp + fn) if (vp + fn) else np.nan
    precision = vp / (vp + fp) if (vp + fp) else np.nan
    # Taux de fausse alerte rapporté aux NON-événements : c'est la grandeur qui dit
    # combien de fois on a dérangé pour rien, indépendamment de la rareté de l'épisode.
    taux_fausse_alerte = fp / (fp + vn) if (fp + vn) else np.nan

    if np.isnan(rappel) or np.isnan(precision) or (rappel + precision) == 0:
        f_beta = np.nan
    else:
        b2 = BETA_ALERTE**2
        f_beta = (1 + b2) * precision * rappel / (b2 * precision + rappel)

    return {
        **m,
        "n_evenements": vp + fn,
        "rappel": float(rappel) if not np.isnan(rappel) else np.nan,
        "precision": float(precision) if not np.isnan(precision) else np.nan,
        f"f{BETA_ALERTE:.0f}": float(f_beta) if not np.isnan(f_beta) else np.nan,
        "taux_fausse_alerte": float(taux_fausse_alerte)
        if not np.isnan(taux_fausse_alerte) else np.nan,
    }


def par_seuil_de_classe(
    observe: pd.Series, predit: pd.Series, classes=(2, 3, 4, 5)
) -> pd.DataFrame:
    """Détection « classe ≥ s » pour une série de seuils.

    On évalue des **seuils cumulés** et non des classes isolées, parce que c'est ainsi
    que la décision se prend : ce qui déclenche une communication, c'est « l'air sera
    dégradé *ou pire* », jamais « l'air sera exactement dégradé ».
    """
    lignes = []
    for seuil in classes:
        resultat = metriques_alerte(observe >= seuil, predit >= seuil)
        lignes.append({"seuil_classe": seuil, **resultat})
    return pd.DataFrame(lignes)


def comparer_modeles(
    observe: pd.Series, predictions: dict[str, pd.Series], classes=(2, 3, 4, 5)
) -> pd.DataFrame:
    """Compare plusieurs modèles sur les mêmes seuils, rappel en tête."""
    blocs = []
    for nom, predit in predictions.items():
        bloc = par_seuil_de_classe(observe, predit, classes)
        bloc.insert(0, "modele", nom)
        blocs.append(bloc)
    return pd.concat(blocs, ignore_index=True)
