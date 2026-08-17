"""Une étiquette qui ment est pire qu'une étiquette absente — le contrôle qui l'empêche.

Le défaut qui a produit ce module — 16/08/2026
-----------------------------------------------
`optuna_realmlp.py` a été généralisé pour régler aussi LightGBM, par un paramètre
`--modele`. La **valeur** est devenue paramétrique ; l'**étiquette** est restée écrite en
dur. Résultat : `reports/optuna_lgbm_PM10_temporel.csv` porte une colonne nommée
`rmse_realmlp` qui contient… le LightGBM réglé.

Personne ne l'a vu, parce que rien ne pouvait le voir : le fichier s'ouvre, la colonne
existe, la valeur est plausible. J'en ai tiré « RealMLP bat LightGBM de 9 % sur PM10 »,
je l'ai écrit dans un brief, et un relecteur externe a relu le fichier — correctement —
pour trouver **2,65 %**. Un tiers a corrigé un chiffre que mon propre nommage rendait
infalsifiable.

La règle, et pourquoi elle est structurelle
---------------------------------------------
> **Une colonne ne porte JAMAIS une identité en dur. Elle porte un RÔLE ; l'identité vit
> dans sa propre colonne.**

`rmse_realmlp` affirme deux choses à la fois — « c'est une RMSE » et « c'est RealMLP » —
et seule la première survit à une généralisation. `rmse_candidat` + une colonne `modele`
ne peuvent pas mentir : le jour où le candidat change, la colonne `modele` change avec lui,
parce qu'elle **est** la donnée.

C'est la même famille que les § 4 bis (un nom de fichier n'est pas une source de vérité) et
§ 4 ter (un nom d'axe n'est pas ce qu'il annonce). Le point commun : **un nom est une
promesse que rien ne vérifie**, et une promesse non vérifiée se périme au premier
refactoring.

Ce que ce module fournit
-------------------------
`exiger_etiquettes_vraies` — refuse d'écrire une table dont une colonne porte un jeton
d'identité que le contexte contredit. À appeler juste avant `to_csv`, comme
`exiger_colonnes` l'est avant un chargement.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# Les jetons qui désignent une IDENTITÉ, par famille. Une colonne qui en porte un affirme
# quelque chose de vérifiable — donc de réfutable. La liste est **fermée** à dessein :
# ouverte, elle laisserait passer le prochain nom inventé, et un contrôle qui ne peut pas
# échouer ne protège de rien.
JETONS = {
    "modele": ("realmlp", "lgbm", "xgb", "mlp", "ridge", "krigeage", "cams", "prevair",
               "chimere", "mocage", "geoscf"),
    "polluant": ("o3", "no2", "pm10", "pm25"),
    "axe": ("spatial", "temporel", "spatiale", "temporelle"),
    "echeance": ("h1", "h2", "h3", "j0", "j1", "j2", "j3"),
}


def _jetons_du_nom(nom: str) -> dict[str, str]:
    """Les identités qu'un nom de colonne affirme, par famille."""
    morceaux = set(re.split(r"[^a-z0-9]+", nom.lower()))
    trouves = {}
    for famille, valeurs in JETONS.items():
        for v in valeurs:
            if v in morceaux:
                trouves[famille] = v
                break
    return trouves


def exiger_etiquettes_vraies(tableau: pd.DataFrame, contexte: dict,
                             quoi: str = "rapport") -> pd.DataFrame:
    """Lève si une colonne affirme une identité que `contexte` contredit.

    `contexte` déclare ce que la table décrit réellement — par exemple
    ``{"modele": "lgbm", "polluant": "PM10", "axe": "temporel"}``.

    ⚠️ **Le contrôle ne porte que sur les familles déclarées.** Une colonne
    `rmse_realmlp` dans une table dont le contexte ne dit rien du modèle passe : on ne peut
    pas réfuter ce qui n'est pas affirmé. Déclarer le contexte est donc l'acte qui arme le
    garde-fou — et c'est volontairement à l'appelant de le faire, parce que lui seul sait
    ce qu'il a calculé.

    Les colonnes qui PORTENT l'identité (``modele``, ``polluant``…) sont exemptées : leur
    nom est le champ, pas une affirmation sur le contenu.
    """
    # ⚠️ **Le contexte se lit par FAMILLE, pas par clé exacte** — trou trouvé en testant le
    # garde sur son propre correctif, dix minutes après l'avoir écrit. Le contexte réel
    # déclarait `modele_candidat` et `modele_reference` ; la version initiale cherchait la
    # clé `modele` tout court, ne la trouvait pas, et **laissait passer l'étiquette
    # mensongère qu'elle existait pour attraper**. Un garde-fou non testé est une croyance
    # (§ 1 quater) — celui-ci l'a été, et il avait tort.
    declare: dict[str, set[str]] = {}
    for cle, valeur in contexte.items():
        for famille in JETONS:
            if famille in cle.lower():
                declare.setdefault(famille, set()).add(str(valeur).lower())

    fautes = []
    for col in tableau.columns:
        if any(f in col.lower() for f in JETONS):
            # La colonne qui PORTE l'identité (`modele`, `modele_candidat`, `polluant`…)
            # n'affirme rien sur son contenu : son nom est le champ.
            if col.lower() in declare or any(col.lower().startswith(f) for f in JETONS):
                continue
        for famille, affirme in _jetons_du_nom(col).items():
            attendus = declare.get(famille)
            if not attendus:
                continue
            if affirme not in attendus:
                fautes.append(
                    f"colonne « {col} » affirme {famille}={affirme}, "
                    f"or le contexte déclare {famille} ∈ {sorted(attendus)}")
    if fautes:
        raise SystemExit(
            f"❌ {quoi} : étiquette(s) mensongère(s) — refus d'écrire.\n   "
            + "\n   ".join(fautes)
            + "\n   Une colonne porte un RÔLE (`rmse_candidat`), jamais une identité "
              "(`rmse_realmlp`) ; l'identité vit dans sa propre colonne.")
    return tableau


def ecrire_rapport(tableau: pd.DataFrame, chemin: str | Path, contexte: dict,
                   attendues: list[str] | None = None) -> Path:
    """Écrit un rapport après avoir vérifié ses étiquettes ET ses colonnes attendues.

    Réunit les deux contrôles que ce dépôt a payés séparément : § 2 ter (exiger nommément
    les colonnes avant d'écrire, après qu'un rapport eut été publié sans les six mesures
    qui décidaient de tout) et celui-ci. Le contexte est **écrit dans le fichier**, pour
    qu'un lecteur ultérieur n'ait pas à le deviner du nom de fichier — lequel ment aussi
    (§ 4 bis).
    """
    chemin = Path(chemin)
    exiger_etiquettes_vraies(tableau, contexte, quoi=chemin.name)
    if attendues and (manque := [c for c in attendues if c not in tableau.columns]):
        raise SystemExit(f"❌ {chemin.name} : colonnes absentes du rapport : {manque}")
    t = tableau.copy()
    for cle, valeur in contexte.items():
        t[cle] = valeur
    prov = chemin.with_suffix(chemin.suffix + ".partiel")
    t.to_csv(prov, index=False)
    prov.rename(chemin)
    return chemin


# ─────────────────────────────────────────────────────────────────────────────────────────
# L'échéance : une seule fonction, parce que le calcul à la main s'est trompé deux fois
# ─────────────────────────────────────────────────────────────────────────────────────────

def libelle_echeance(horizon: int) -> str:
    """Le libellé J+n d'une tranche d'échéances CAMS, dérivé — jamais écrit à la main.

    La convention, lue dans les données et non dans un nom
    ------------------------------------------------------
    `TRANCHES = {1: (1, 24), 2: (25, 48), 3: (49, 72)}` porte des **heures depuis la sortie
    de 00 UTC**. Les heures 1 à 24 sont donc celles du **jour de la sortie** : `horizon=1`
    est **J0**, pas J+1. Vérifié sur les données le 17/08/2026 : le premier jour couvert est
    2023-08-01 pour `horizon=1` et 2023-08-**02** pour `horizon=2`. Un jour d'écart.

    D'où : **J+(horizon − 1)**.

    Pourquoi cette fonction existe
    -------------------------------
    Ce défaut s'est produit **deux fois**, et la méta-règle du dépôt dit qu'une règle violée
    deux fois devient du code ou disparaît :

    1. le 02/08/2026, `horizon=1` a été appelé « J+1 » pendant des semaines. Corrigé — mais
       seulement pour `horizon=1` ;
    2. le 17/08/2026, une revue externe relève que `methode_maximale.py` imprime
       `f"J+{horizon}"`, donc **« J+2 » pour la tranche 25-48 h qui est J+1**, et que
       `VERITE_DOSSIER` le publie sept fois. Une revue antérieure (R16) l'avait déjà classé
       P0 et déclaré corrigé : le libellé était revenu.

    Le défaut a une signature qui le rend coûteux : **il flatte**. Annoncer une échéance plus
    lointaine que celle mesurée fait paraître le résultat meilleur, et rien dans les données
    ne contredit un libellé.
    """
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError(f"horizon doit être un entier ≥ 1, reçu {horizon!r}")
    return f"J+{horizon - 1}" if horizon > 1 else "J0"
