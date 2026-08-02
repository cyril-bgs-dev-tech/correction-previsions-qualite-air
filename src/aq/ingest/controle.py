"""Contrôles d'intégrité au chargement — vérifier ce qu'on a **demandé**, pas ce qui est plausible.

Le motif commun de trois défauts commis le 31/07/2026
------------------------------------------------------
Trois bogues distincts, une seule cause : *j'ai vérifié que le résultat était plausible, jamais
qu'il correspondait à la demande.* Dans les trois cas, l'échec a produit un objet d'allure
normale au lieu de lever une erreur.

| défaut | ce qui a été produit | ce qui manquait |
|---|---|---|
| colonne prise **par position** (« la première qui n'est ni une clé ni une maille ») | la coordonnée `level`, constante à 0 → dispersion de 0,00 sur six membres | nommer la colonne attendue |
| `xarray.open_datasets` — **fonction inexistante**, erreur avalée par `except: continue` | 0 ligne, 0 colonne, aucun message | ne jamais taire une exception de chargement |
| deux variables demandées à GFAS, **une seule reçue** | un fichier valide, un contrôle au vert | comparer le reçu au demandé |

Un quatrième, du même jour, est l'image en miroir : un contrôle exigeait « un axe de taille 24 »
alors que le service aplatit date × échéance en 744. **Le contrôle était faux, pas la donnée** —
et un test de conformité mal posé fait rejeter du bon, ce qui coûte autant qu'une absence de test.

La règle
--------
> Tout chargement se termine par une assertion **sur la demande**, jamais sur la vraisemblance
> du résultat. Et une assertion qui échoue **lève** ; elle ne journalise pas.

Les fonctions ci-dessous sont volontairement brutales : elles lèvent `ControleEchec` avec un
message qui nomme l'écart. Une donnée absente qui s'annonce coûte quelques minutes ; une donnée
absente qui se tait coûte des heures et se découvre dans les métriques finales.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


class ControleEchec(AssertionError):
    """Un chargement n'a pas rendu ce qui était demandé."""


def exiger_colonnes(tableau: pd.DataFrame, attendues: Iterable[str],
                    quoi: str = "tableau") -> pd.DataFrame:
    """Toutes les colonnes attendues sont présentes — sinon on lève en les nommant."""
    manquantes = [c for c in attendues if c not in tableau.columns]
    if manquantes:
        raise ControleEchec(
            f"{quoi} : colonnes absentes {manquantes} · présentes {list(tableau.columns)}")
    return tableau


def colonne_unique(tableau: pd.DataFrame, motif: str, quoi: str = "tableau") -> str:
    """Nom de **l'unique** colonne correspondant au motif.

    Remplace l'heuristique positionnelle qui a produit la dispersion nulle. Zéro correspondance
    est une erreur ; plusieurs aussi — dans les deux cas on ne sait pas quoi lire, et deviner
    est précisément ce qu'il faut refuser.
    """
    candidates = [c for c in tableau.columns if motif in c]
    if len(candidates) != 1:
        raise ControleEchec(
            f"{quoi} : {len(candidates)} colonne(s) contenant « {motif} » "
            f"{candidates} · toutes : {list(tableau.columns)}")
    return candidates[0]


def exiger_variables(jeu, demandees: Iterable[str], quoi: str = "jeu") -> None:
    """Le jeu porte **autant** de variables que demandé.

    Le service peut ignorer un nom invalide et servir le reste sans lever : la requête paraît
    réussie, le fichier s'ouvre, et il manque une grandeur. C'est le cas GFAS.
    """
    demandees = list(demandees)
    obtenues = list(getattr(jeu, "data_vars", jeu))
    if len(obtenues) != len(demandees):
        raise ControleEchec(
            f"{quoi} : {len(obtenues)} variable(s) reçue(s) pour {len(demandees)} demandée(s) · "
            f"reçues {obtenues} · demandées {demandees} — un nom est probablement invalide")


def exiger_axe(jeu, nom: str, taille: int, quoi: str = "jeu") -> None:
    """Un axe a exactement la taille attendue.

    **Calculer la taille attendue depuis la demande**, jamais depuis une intuition de forme :
    un service peut aplatir date × échéance en un seul axe, et un contrôle qui cherche « un axe
    de 24 » rejetterait alors une donnée parfaitement complète.
    """
    obtenue = dict(getattr(jeu, "sizes", {})).get(nom)
    if obtenue != taille:
        raise ControleEchec(
            f"{quoi} : axe « {nom} » de taille {obtenue} au lieu de {taille} · "
            f"axes {dict(getattr(jeu, 'sizes', {}))}")


def exiger_variation(tableau: pd.DataFrame, colonnes: Iterable[str],
                     quoi: str = "tableau") -> None:
    """Aucune colonne n'est constante.

    Une colonne constante est presque toujours le signe qu'on a lu autre chose que ce qu'on
    croyait — une coordonnée dégénérée, un niveau, un indicateur. C'est le contrôle qui aurait
    attrapé la dispersion nulle **avant** de l'écrire sur disque.
    """
    plates = [c for c in colonnes
              if c in tableau.columns and tableau[c].nunique(dropna=True) <= 1]
    if plates:
        raise ControleEchec(
            f"{quoi} : colonne(s) constante(s) {plates} — lecture probablement erronée")


def exiger_lignes(tableau: pd.DataFrame, minimum: int = 1,
                  quoi: str = "tableau") -> pd.DataFrame:
    """Le tableau n'est pas vide. Un chargement muet rend souvent zéro ligne."""
    if len(tableau) < minimum:
        raise ControleEchec(f"{quoi} : {len(tableau)} ligne(s), minimum attendu {minimum}")
    return tableau


def exiger_couverture(tableau: pd.DataFrame, colonne: str, part_min: float = 0.5,
                      quoi: str = "tableau") -> None:
    """Une part suffisante de valeurs renseignées.

    Distingue « la jointure a réussi » de « la jointure a rendu des lignes vides » : le panneau
    occitan porte des lignes horaires dont la valeur est nulle, et une jointure y réussit
    parfaitement en ne ramenant rien d'exploitable.
    """
    part = float(tableau[colonne].notna().mean()) if len(tableau) else 0.0
    if part < part_min:
        raise ControleEchec(
            f"{quoi} : « {colonne} » renseignée sur {100 * part:.1f} % des lignes, "
            f"minimum {100 * part_min:.0f} %")


def resume_chargement(tableau: pd.DataFrame, quoi: str, cles: Iterable[str] = ()) -> str:
    """Ligne de journal normalisée — un lot muet ne se corrige qu'une fois terminé."""
    details = [f"{len(tableau):,} lignes"]
    for c in cles:
        if c in tableau.columns:
            details.append(f"{tableau[c].nunique():,} {c}")
    numeriques = tableau.select_dtypes(include=[np.number]).columns
    constantes = [c for c in numeriques if tableau[c].nunique(dropna=True) <= 1]
    if constantes:
        details.append(f"⚠️ constantes : {constantes[:4]}")
    return f"{quoi} · " + " · ".join(details)
