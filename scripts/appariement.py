#!/usr/bin/env python3
"""Apparier deux tables sur des clés dont l'une est une date — sans itérer en Python.

Pourquoi ce module existe
---------------------------
Le motif `set(zip(t["dep"], t["jour"]))`, puis un test d'appartenance ligne à ligne, se
lisait dans **quatre** scripts de ce dépôt. Il a deux défauts, et le second n'est apparu
que le 10/08/2026 :

1. **Il est lent** — chaque valeur d'une colonne de dates est matérialisée en objet
   `Timestamp` par `DatetimeArray.__iter__`, pour être ensuite hachée dans un tuple.
2. **Sur cette machine, il ne fonctionne pas.** Le 10/08, `couverture_membres()` a échoué
   **six fois sur six** à cette ligne précise : segfault, ou
   `TypeError: 'iterator' object cannot be interpreted as an integer`, toujours dans
   `pandas/core/arrays/datetimes.py → __iter__ → ints_to_pydatetime`. Ce n'est pas l'aléa
   à une chance sur deux que `CLAUDE.md` § 1 quater décrit ailleurs : **ce site-là tombe
   à chaque tentative**, alors que le même lot passe en changeant de chemin de code.

La jointure de pandas fait le même appariement dans son code C, sans construire un seul
objet Python. C'est donc à la fois le correctif et l'optimisation — et il n'existe qu'ici,
plutôt qu'en quatre copies qui divergeront au premier ajustement (`CLAUDE.md` § 4 bis).

Ce que ces fonctions garantissent en plus du `set`
---------------------------------------------------
* **Le compte est conservé** : un doublon dans la table de référence dupliquerait des
  lignes en silence et fausserait tout dénominateur en aval. Elles lèvent (§ 2 bis).
* **Un désaccord de fuseau LÈVE** au lieu de rendre « zéro correspondance ». La comparaison
  de tuples, elle, rendait 0 % de couverture sans un mot — un zéro de non-lecture
  indiscernable d'un zéro de non-occurrence (§ 4 bis).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _table(source: pd.DataFrame, cles: tuple[str, ...], dates: tuple[str, ...],
           decalage: pd.Timedelta | None = None) -> pd.DataFrame:
    colonnes = {}
    for cle in cles:
        valeurs = source[cle].reset_index(drop=True)
        if cle in dates:
            valeurs = pd.to_datetime(valeurs)
            if decalage is not None:
                valeurs = valeurs + decalage
        colonnes[cle] = valeurs
    return pd.DataFrame(colonnes)


def presence(gauche: pd.DataFrame, reference: pd.DataFrame, cles: tuple[str, ...],
             dates: tuple[str, ...] = ("jour",),
             decalage: pd.Timedelta | None = None) -> np.ndarray:
    """Pour chaque ligne de `gauche`, la clé existe-t-elle dans `reference` ?

    `decalage` s'ajoute aux colonnes de date **de `gauche`** : c'est ainsi qu'on demande
    « la veille » sans supposer l'ordre des lignes, ce qu'un `shift()` supposerait.

    Rend un tableau booléen de la longueur de `gauche`, dans son ordre.
    """
    g = _table(gauche, cles, dates, decalage)
    r = _table(reference, cles, dates).drop_duplicates()
    r["_présent"] = np.int8(1)
    fusion = g.merge(r, on=list(cles), how="left")
    if len(fusion) != len(g):
        raise SystemExit(f"appariement sur {cles} : {len(fusion)} lignes rendues pour "
                         f"{len(g)} demandées — la référence porte des doublons")
    return fusion["_présent"].notna().to_numpy()


def valeur_associee(gauche: pd.DataFrame, reference: pd.DataFrame,
                    cles: tuple[str, ...], valeurs: np.ndarray,
                    dates: tuple[str, ...] = ("jour",),
                    decalage: pd.Timedelta | None = None,
                    defaut: bool = False) -> np.ndarray:
    """Comme `presence`, mais rapporte un booléen porté par `reference`, pas sa seule existence.

    Sert la règle de persistance : « la règle tenait-elle la veille, dans la même zone ? »
    demande la *valeur* de la veille, et `defaut` dit ce que vaut une veille absente —
    jamais `nan`, qui se propagerait en `True` dans un `&`.
    """
    if len(valeurs) != len(reference):
        raise SystemExit(f"appariement sur {cles} : {len(valeurs)} valeurs pour "
                         f"{len(reference)} lignes de référence")
    g = _table(gauche, cles, dates, decalage)
    r = _table(reference, cles, dates)
    r["_valeur"] = np.asarray(valeurs, dtype=bool).astype(np.int8)
    if r.duplicated(list(cles)).any():
        raise SystemExit(f"appariement sur {cles} : la référence porte des doublons — "
                         f"la valeur associée serait ambiguë")
    fusion = g.merge(r, on=list(cles), how="left")
    return (fusion["_valeur"].fillna(int(defaut)).to_numpy() > 0)
