"""Correction apprise des sorties CAMS (Model Output Statistics).

**Ce que ce module fait, et pourquoi c'est la bonne cible.** Le benchmark montre que
l'erreur de CAMS ne croît quasiment pas avec l'échéance (+1,2 % du RMSE entre J+1 et
J+3 sur le NO₂). Une erreur qui n'augmente pas avec l'horizon n'est pas produite par la
divergence chaotique de l'atmosphère : elle est **structurelle**, liée au modèle —
inventaire d'émissions, résolution de maille, paramétrisations. C'est exactement le type
d'erreur qu'une correction apprise sait capter.

**La contrainte qui gouverne toute la conception : n'utiliser que ce qui est disponible
à l'heure de la prévision.** Un modèle qui consommerait de la météo réanalysée (ERA5)
verrait un futur que CAMS n'avait pas, et le battrait sans que cela signifie quoi que ce
soit d'exploitable. Les variables admises ici sont donc :

- la **prévision CAMS** elle-même, publiée avant l'échéance ;
- les variables **géographiques et topographiques**, statiques ;
- des variables **calendaires**, connues d'avance.

Toute variable météo ajoutée par la suite devra provenir d'une *prévision*, pas d'une
réanalyse — c'est la même faute que ci-dessus, et elle est silencieuse.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from aq.models.moteur import N_JOBS  # une seule source pour la borne de fils

# Le cycle diurne et le cycle annuel sont **circulaires** : coder l'heure par un entier
# de 0 à 23 place minuit et 23 h aux extrémités opposées de l'échelle, alors qu'ils se
# suivent. Un arbre de décision doit alors dépenser plusieurs coupures pour reconstituer
# une continuité que l'encodage a détruite.
CYCLES = {"heure": 24.0, "jour_annee": 365.25}


def variables_calendaires(horodatages: pd.Series) -> pd.DataFrame:
    """Encodage cyclique du temps, plus le jour de semaine.

    Le jour de semaine reste catégoriel : il porte le rythme des émissions (trafic
    ouvré contre week-end), qui n'a rien de circulaire au sens des heures — samedi et
    dimanche se ressemblent, lundi et dimanche non.
    """
    horodatages = pd.to_datetime(horodatages)
    brut = pd.DataFrame({
        "heure": horodatages.dt.hour.to_numpy(dtype="float64"),
        "jour_annee": horodatages.dt.dayofyear.to_numpy(dtype="float64"),
    })
    sortie = pd.DataFrame(index=brut.index)
    for nom, periode in CYCLES.items():
        angle = 2 * np.pi * brut[nom] / periode
        sortie[f"{nom}_cos"] = np.cos(angle)
        sortie[f"{nom}_sin"] = np.sin(angle)
    sortie["jour_semaine"] = horodatages.dt.dayofweek.to_numpy()
    sortie["weekend"] = (sortie["jour_semaine"] >= 5).astype("int8")
    return sortie


@dataclass
class ResultatMos:
    """Sorties d'un ajustement, avec de quoi le juger honnêtement."""

    predictions: pd.DataFrame       # station_id, timestamp_utc, observe, cams, corrige
    importances: pd.DataFrame
    n_entrainement: int
    n_test: int


def _modele(graine: int):
    """Gradient boosting, réglé pour un jeu large et bruité.

    Les hyperparamètres sont volontairement prudents : sur des observations horaires,
    un modèle trop profond mémorise le bruit de mesure — qui n'a rien de reproductible
    d'une station à l'autre.
    """
    from lightgbm import LGBMRegressor

    return LGBMRegressor(
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=63,
        min_child_samples=200,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        random_state=graine,
        # ⚠️ **Jamais `n_jobs=-1`.** LightGBM prend alors les 32 cœurs, et deux ajustements
        # lancés ensemble en demandent 64 : ce n'est pas un ralentissement de 2×, c'est un
        # effondrement — la contention porte sur la **bande passante mémoire**, pas sur les
        # cœurs (`CLAUDE.md` règle 1). Mesuré le 05/08/2026 sur `fit_mos.py`, corpus
        # identique de 7,05 M de paires : **114 s le premier pli en solo, 1 473 s à deux
        # en parallèle — ×12,9**. La valeur 8 est celle que `aq.models.moteur` retient
        # déjà ; ce fichier était le seul à ne pas la suivre.
        n_jobs=N_JOBS,
        verbose=-1,
    )


def ajuster_par_stations_exclues(
    jeu: pd.DataFrame,
    colonnes: list[str],
    colonne_cams: str,
    colonne_observe: str = "valeur",
    n_plis: int = 5,
    graine: int = 0,
    cible_residu: bool = True,
    verbeux: bool = True,
    fabrique_modele=None,
) -> ResultatMos:
    """Entraîne et évalue par groupes de **stations** entièrement exclues.

    C'est la seule évaluation qui réponde à la question du projet. Découper au hasard
    dans les lignes laisserait, pour chaque station de test, des milliers d'heures de
    cette même station dans l'entraînement : le modèle apprendrait le niveau moyen de
    chaque station par cœur, et afficherait un score qui ne dit rien de sa capacité à
    prédire là où l'on ne mesure pas — c'est-à-dire l'objet même d'une spatialisation.

    **`cible_residu` n'est pas une option de confort — c'est la différence entre une
    correction et un remplacement.** Apprendre l'observation directement fait du modèle
    un prédicteur autonome : sur une distribution fortement asymétrique comme celle de
    l'ozone, où 83 % des points sont sous 80 µg/m³, minimiser l'erreur quadratique le
    pousse à bien traiter le gros de la masse et à **écraser la queue**. Mesuré sur ce
    projet : le RMSE global s'améliorait de 13 %, mais la détection des dépassements du
    seuil d'information passait de 5 sur 15 à **0 sur 15**. Le modèle était meilleur
    partout sauf là où il sert.

    Apprendre le **résidu** `observation − CAMS` change la nature du problème : la
    prédiction reste ancrée à la physique du modèle, et l'amortissement caractéristique
    du gradient boosting tire vers « pas de correction » plutôt que vers la moyenne.
    """
    stations = np.array(sorted(jeu["station_id"].unique()))
    rng = np.random.default_rng(graine)
    plis = np.array_split(rng.permutation(stations), n_plis)

    morceaux = []
    importances = []
    n_entrainement = 0

    # **Un pli terminé se dit.** Sans trace, l'ajustement est muet pendant des dizaines
    # de minutes : impossible de savoir s'il progresse, et impossible d'extrapoler sa
    # fin. Deux runs de 90 minutes ont été tués par un `timeout` sans qu'on puisse le
    # voir venir, faute de ce seul `print`.
    depart = time.time()

    for n, pli in enumerate(plis, start=1):
        test = jeu["station_id"].isin(pli)
        # **Écarter les cibles manquantes de l'entraînement.** Le panneau conserve des
        # lignes horaires sans mesure valide — 11 % ici, et 49 couples
        # (station, polluant) entièrement vides. Le gradient boosting ne s'en plaint
        # pas : il les absorbe, et la correction apprise s'en trouve amortie. Mesuré
        # sur l'ozone : RMSE 12,605 → 12,312 et biais +1,05 → +0,38 en les retirant.
        # L'erreur va donc dans le sens pessimiste, ce qui la rend d'autant plus
        # facile à ne pas voir.
        entrainement = jeu[~test].dropna(subset=[colonne_observe, colonne_cams])
        if entrainement.empty or test.sum() == 0:
            continue

        cible = (
            entrainement[colonne_observe] - entrainement[colonne_cams]
            if cible_residu
            else entrainement[colonne_observe]
        )
        # `fabrique_modele` permet de comparer des algorithmes **à protocole identique** :
        # mêmes plis, même cible résiduelle, même écrêtage. Sans elle, toute comparaison
        # d'algorithmes réimplémenterait la boucle et n'en serait plus une.
        modele = (fabrique_modele or _modele)(graine)
        modele.fit(entrainement[colonnes], cible)
        n_entrainement += len(entrainement)

        bloc = jeu.loc[test, ["station_id", "timestamp_utc"]].copy()
        bloc["observe"] = jeu.loc[test, colonne_observe].to_numpy()
        bloc["cams"] = jeu.loc[test, colonne_cams].to_numpy()
        sortie = modele.predict(jeu.loc[test, colonnes])
        bloc["corrige"] = bloc["cams"] + sortie if cible_residu else sortie
        # Une concentration négative n'existe pas. La correction peut en produire là
        # où CAMS est déjà bas : on écrête, faute de quoi le modèle serait pénalisé
        # pour une valeur qu'aucune mesure ne peut prendre.
        bloc["corrige"] = bloc["corrige"].clip(lower=0.0)
        morceaux.append(bloc)

        # Un modèle linéaire expose `coef_` et non `feature_importances_` ; un pipeline
        # n'expose ni l'un ni l'autre. L'importance est un agrément, pas une exigence :
        # ne pas faire échouer un ajustement valide pour son absence.
        poids = getattr(modele, "feature_importances_", None)
        if poids is None:
            coefficients = getattr(modele, "coef_", None)
            poids = np.abs(coefficients) if coefficients is not None else None
        if poids is not None and len(poids) == len(colonnes):
            importances.append(pd.Series(poids, index=colonnes))

        if verbeux:
            ecoule = time.time() - depart
            print(f"  pli {n}/{len(plis)} · {ecoule:5.0f}s · "
                  f"reste ~{ecoule / n * (len(plis) - n):5.0f}s", flush=True)

    predictions = pd.concat(morceaux, ignore_index=True)
    if importances:
        moyennes = pd.concat(importances, axis=1).mean(axis=1)
        table = (moyennes / moyennes.sum()).sort_values(ascending=False)
        table = pd.DataFrame({"variable": table.index, "importance": table.to_numpy()})
    else:
        # Aucun modèle n'a exposé de poids : rendre une table vide plutôt que d'échouer
        # après un ajustement qui, lui, a réussi.
        table = pd.DataFrame({"variable": [], "importance": []})

    return ResultatMos(
        predictions=predictions,
        importances=table,
        n_entrainement=n_entrainement // max(1, len(plis)),
        n_test=len(predictions),
    )
