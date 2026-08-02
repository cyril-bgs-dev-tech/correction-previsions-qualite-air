"""Assemblage des séries station × polluant sur la grille horaire canonique.

Sortie : un panneau long `(station_id, polluant, timestamp_utc) → valeur`, réindexé
sur une grille horaire continue et complète.

Le réindexage n'est pas cosmétique. Une heure ABSENTE et une heure PRÉSENTE MAIS
VIDE sont deux choses différentes pour un modèle de série temporelle et pour un
calcul de couverture réglementaire : la première est invisible, la seconde est un
fait mesurable. On rend donc tous les trous explicites.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

import pandas as pd

from aq.harmonize import timegrid
from aq.ingest import eea


def telecharger_series(
    urls: Iterable[str], max_parallele: int = 6, sur_erreur: str = "signaler"
) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """Télécharge et harmonise plusieurs séries en parallèle.

    Les échecs sont collectés et retournés plutôt que levés : sur plusieurs dizaines
    de fichiers, un point de prélèvement indisponible ne doit pas faire échouer toute
    l'ingestion — mais il doit être visible, jamais avalé en silence.
    """
    urls = list(urls)
    echecs: list[tuple[str, str]] = []

    def _un(url: str) -> pd.DataFrame | None:
        try:
            return eea.lire_fichier(url)
        except Exception as exc:  # noqa: BLE001 - on veut le message, pas le type
            echecs.append((url, f"{type(exc).__name__}: {exc}"))
            return None

    with ThreadPoolExecutor(max_workers=max_parallele) as pool:
        morceaux = [df for df in pool.map(_un, urls) if df is not None]

    if sur_erreur == "lever" and echecs:
        raise RuntimeError(f"{len(echecs)} téléchargements en échec : {echecs[:3]}")

    if not morceaux:
        return pd.DataFrame(), echecs

    return pd.concat(morceaux, ignore_index=True), echecs


def construire_panneau(brut: pd.DataFrame) -> pd.DataFrame:
    """Passe des fichiers concaténés au panneau long canonique."""
    if brut.empty:
        return brut

    df = brut.copy()
    df["station_id"] = df["point_prelevement"].map(eea.code_station)

    # Une même station peut exposer plusieurs points de prélèvement pour un même
    # polluant (remplacement d'analyseur, doublon métrologique). Les empiler sans
    # dédoublonner créerait des horodatages en double et fausserait toute moyenne.
    doublons = df.duplicated(["station_id", "polluant", "timestamp_utc"], keep=False)
    if doublons.any():
        df = (
            df.sort_values("valeur")
            .groupby(["station_id", "polluant", "timestamp_utc"], as_index=False)
            .agg(
                valeur=("valeur", "mean"),
                flag_qualite=("flag_qualite", "first"),
                n_points=("point_prelevement", "nunique"),
            )
        )
    else:
        df = df.assign(n_points=1)[
            ["station_id", "polluant", "timestamp_utc", "valeur", "flag_qualite", "n_points"]
        ]

    return df.sort_values(["station_id", "polluant", "timestamp_utc"]).reset_index(drop=True)


def reindexer_grille(
    panneau: pd.DataFrame, debut=None, fin=None
) -> pd.DataFrame:
    """Réindexe chaque série sur une grille horaire continue commune.

    La grille est commune à toutes les séries : sans cela, une station dont la
    mesure démarre tard paraîtrait complète sur sa propre période, et son défaut de
    couverture disparaîtrait de l'analyse.
    """
    if panneau.empty:
        return panneau

    debut = debut or panneau["timestamp_utc"].min()
    fin = fin or panneau["timestamp_utc"].max()
    grille = timegrid.grille_complete(debut, fin)

    cles = panneau[["station_id", "polluant"]].drop_duplicates()
    plein = cles.merge(
        pd.DataFrame({"timestamp_utc": grille}), how="cross"
    )

    return (
        plein.merge(panneau, on=["station_id", "polluant", "timestamp_utc"], how="left")
        .sort_values(["station_id", "polluant", "timestamp_utc"])
        .reset_index(drop=True)
    )


def rapport_qualite(panneau: pd.DataFrame) -> pd.DataFrame:
    """Indicateurs de qualité par série.

    **Une couverture rapportée à la grille globale est trompeuse** : elle confond
    trois situations de nature complètement différente.

    1. *Censure à gauche* — l'instrument n'était pas encore installé. « Montpellier
       Antigone » affiche 8 % de couverture sur douze ans simplement parce qu'elle
       a ouvert en 2024 ; sur sa propre durée de vie elle est quasi complète. Ce
       n'est pas un défaut de qualité.
    2. *Censure à droite* — mesure arrêtée alors que la station reste active.
       « Perpignan bd Pyrénées » a mesuré les PM2.5 quinze mois puis s'est arrêtée.
       Cela, en revanche, est un fait à documenter.
    3. *Trous internes* — les seuls véritables défauts de couverture, et les seuls
       qui relèvent du critère réglementaire.

    On rapporte donc les deux dénominateurs : `couverture_grille` (position dans le
    corpus, utile au dimensionnement) et `couverture_active` (qualité réelle de la
    mesure, entre la première et la dernière observation).
    """
    if panneau.empty:
        return pd.DataFrame()

    def _serie(groupe: pd.DataFrame) -> pd.Series:
        groupe = groupe.sort_values("timestamp_utc")
        valeurs = groupe["valeur"]
        presentes = valeurs.notna()
        n_valides = int(presentes.sum())

        if not n_valides:
            return pd.Series(
                {
                    "n_heures_grille": len(groupe),
                    "n_valides": 0,
                    "couverture_grille": 0.0,
                    "couverture_active": float("nan"),
                    "debut_mesure": pd.NaT,
                    "fin_mesure": pd.NaT,
                    "plus_long_trou_interne_h": 0,
                    "repetition_max_h": 0,
                    "median": float("nan"),
                    "max": float("nan"),
                    "n_negatives": 0,
                }
            )

        indices = presentes.to_numpy().nonzero()[0]
        premier, dernier = indices[0], indices[-1]
        interne = presentes.iloc[premier : dernier + 1]

        # Plus long trou strictement à l'intérieur de la période de mesure.
        manquantes = ~interne
        plus_long_trou = int(manquantes.groupby(interne.cumsum()).sum().max())

        # Une valeur répétée à l'identique pendant des heures signale un capteur
        # gelé, pas une atmosphère stable : défaut classique et invisible.
        valides = valeurs[presentes]
        bloc = (valides != valides.shift()).cumsum()
        repetition_max = int(valides.groupby(bloc).size().max())

        return pd.Series(
            {
                "n_heures_grille": len(groupe),
                "n_valides": n_valides,
                "couverture_grille": float(presentes.mean()),
                "couverture_active": float(interne.mean()),
                "debut_mesure": groupe["timestamp_utc"].iloc[premier],
                "fin_mesure": groupe["timestamp_utc"].iloc[dernier],
                "plus_long_trou_interne_h": plus_long_trou,
                "repetition_max_h": repetition_max,
                "median": float(valides.median()),
                "max": float(valides.max()),
                "n_negatives": int((valides < 0).sum()),
            }
        )

    return (
        panneau.groupby(["station_id", "polluant"])
        .apply(_serie, include_groups=False)
        .reset_index()
        .sort_values("couverture_active")
        .reset_index(drop=True)
    )
