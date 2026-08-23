"""Ingestion des mesures de qualité de l'air — EEA Air Quality Download Service.

Source retenue comme point d'entrée : accès sans authentification, format Parquet,
et surtout colonnes `Validity` / `Verification` qui distinguent nativement données
provisoires et validées.

Conventions établies EMPIRIQUEMENT le 2026-07-28 sur des fichiers réels (elles ne
sont pas documentées dans les métadonnées du service) :

- **Horodatage en UTC.** Vérifié par continuité au changement d'heure : sur 13 762
  pas consécutifs d'une série, tous les écarts valent exactement 1 h, aucun doublon,
  et l'heure 02:00 du 30 mars 2025 est présente — or elle n'existe pas en heure
  locale française. Le test du cycle diurne, lui, n'est pas concluant : en été la
  couche limite se rompt tôt et décale le pic matinal indépendamment du fuseau.
- **`Start` et `End` sont explicites** : la valeur datée t couvre [t, t+1h).
  C'est la convention canonique du projet, aucun décalage n'est nécessaire.
- **`Validity == 1` ↔ valeur réelle ; `Validity == -1` ↔ sentinelle `-999`.**
  Correspondance parfaite sur l'échantillon. Le filtrage se fait sur le flag, jamais
  sur un seuil de valeur : certaines stations sont invalides à 100 % et une moyenne
  naïve renverrait -999.
"""

from __future__ import annotations

import io
from typing import Iterable

import pandas as pd
import requests

API_BASE = "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
URLS_ENDPOINT = f"{API_BASE}/ParquetFile/urls"

# Jeux de données du service. Le choix est structurant : le jeu 1 (UTD) est
# provisoire et couvre une fenêtre glissante ; le jeu 2 (E1a) est validé mais
# n'est publié que le 30 septembre de l'année N+1, soit ~9 mois de décalage.
DATASET_UTD = 1        # non vérifié, transmis en continu (~1-2 h de latence)
DATASET_VERIFIED = 2   # validé E1a
DATASET_AIRBASE = 3    # historique 2002-2012

# Codes du vocabulaire Eionet (`/Pollutant`), restreints au périmètre du projet.
CODES_POLLUANTS = {
    "SO2": 1,
    "PM10": 5,
    "O3": 7,
    "NO2": 8,
    "NOX": 9,      # « NOX as NO2 » — nécessaire au rapport NO2/NOx
    "CO": 10,
    "PM25": 6001,
}
CODE_VERS_POLLUANT = {v: k for k, v in CODES_POLLUANTS.items()}

# Le libellé attendu par l'API n'est pas toujours le nom canonique interne. Un
# point dans un nom de polluant deviendrait un point dans un nom de colonne :
# on garde `PM25` en interne et on traduit à la frontière du service.
NOTATION_API = {
    "PM25": "PM2.5",
    "NOX": "NOX as NO2",
}

# Sentinelle numérique du producteur. Elle survit aux agrégations et contamine
# silencieusement toute statistique : neutralisée dès l'ingestion.
SENTINELLE = -999.0

# 🔴 Le vocabulaire EIONET compte CINQ codes valides, pas un — et le filtrer à 1 a déjà
# coûté treize mois d'ozone dans la chaîne LCSQA, corrigés le 01/08/2026.
#
#   dd.eionet.europa.eu/vocabulary/aq/observationvalidity
#     −99  Not valid due to station maintenance or calibration   → invalide
#      −1  Not valid                                             → invalide
#       1  Valid                                                 → valide
#     2, 3  Valid, but below detection limit (et sa variante)     → valide
#       4  Valid (Ozone only) using CCQM.O3.2019                  → valide
#
# Le code 4 est entré au vocabulaire en juillet 2024 et la France y a basculé le
# 01/07/2025 : TOUT l'ozone français porte 4 depuis cette date. Un filtre `== 1` le jette
# intégralement, sans lever et avant écriture — le fichier produit ne porte alors aucune
# trace de ce qu'il a perdu.
#
# Ce module alimente les panels EEA, aujourd'hui remplacés par `panel_unifie_lcsqa` : le
# défaut y est donc DORMANT, pas actif. Il est corrigé quand même, parce qu'un jumeau
# dormant est exactement ce qu'une régénération réveille (§ 4 bis).
#
# La règle générale, et elle vaut au-delà de ce fichier : **un code de qualité inconnu se
# résout dans le vocabulaire normatif, jamais par l'exclusion prudente.** L'exclusion
# prudente est ce qui a coûté les treize mois.
# Conservée pour la lisibilité du commentaire ci-dessus ; le filtre porte sur le
# SIGNE, pas sur cette valeur.
VALIDITE_VALIDE = 1


def lister_fichiers(
    polluants: Iterable[str],
    pays: str = "FR",
    dataset: int = DATASET_UTD,
    villes: Iterable[str] | None = None,
    timeout: int = 120,
) -> list[str]:
    """Retourne les URL Parquet, une par point de prélèvement."""
    polluants = list(polluants)
    inconnus = set(polluants) - set(CODES_POLLUANTS)
    if inconnus:
        raise ValueError(f"Polluants hors périmètre : {sorted(inconnus)}")

    reponse = requests.post(
        URLS_ENDPOINT,
        json={
            "countries": [pays],
            "cities": list(villes or []),
            "pollutants": [NOTATION_API.get(p, p) for p in polluants],
            "dataset": dataset,
            "source": "API",
        },
        timeout=timeout,
    )
    reponse.raise_for_status()

    lignes = reponse.text.lstrip("﻿").splitlines()
    return [ligne.strip() for ligne in lignes[1:] if ligne.strip().endswith(".parquet")]


def lire_fichier(url: str, timeout: int = 120) -> pd.DataFrame:
    """Télécharge un Parquet et le convertit au schéma canonique du projet.

    Les lignes invalides sont conservées avec une valeur NaN plutôt que supprimées :
    un trou explicite est une information (panne, maintenance), une ligne absente
    n'en est pas une. Le calcul de couverture temporelle réglementaire en dépend.
    """
    reponse = requests.get(url, timeout=timeout)
    reponse.raise_for_status()
    brut = pd.read_parquet(io.BytesIO(reponse.content))

    df = pd.DataFrame(
        {
            "point_prelevement": brut["Samplingpoint"].astype("string"),
            # decimal128 en natif : sans conversion, les opérations numériques
            # ultérieures échouent ou dégradent silencieusement la précision.
            "valeur": brut["Value"].astype("float64"),
            "unite": brut["Unit"].astype("string"),
            "agregation": brut["AggType"].astype("string"),
            # Entiers NULLABLES : le jeu Airbase historique laisse ces colonnes
            # vides sur certaines lignes, et un int32 classique refuse les NA.
            "validite": brut["Validity"].astype("Int32"),
            "verification": brut["Verification"].astype("Int32"),
        }
    )

    df["polluant"] = (
        brut["Pollutant"].map(CODE_VERS_POLLUANT).astype("string")
    )

    # Horodatage naïf en UTC (cf. docstring du module) ; Start est déjà le début
    # de l'intervalle, conformément au contrat de données.
    df["timestamp_utc"] = pd.to_datetime(brut["Start"]).dt.tz_localize("UTC")

    # Neutralisation conjointe du flag et de la sentinelle. Les deux critères sont
    # appliqués : ils coïncident sur l'échantillon observé, mais s'appuyer sur une
    # coïncidence non documentée serait imprudent.
    # Le test porte sur le SIGNE — tout code positif est valide au vocabulaire EIONET,
    # voir le commentaire de `VALIDITE_VALIDE`. Un `!= 1` jetterait 2, 3 et 4.
    # `fillna(True)` : une validité absente n'est pas une validité acquise.
    # Sans cela, la comparaison sur un Int32 nullable produit <NA>, que le masque
    # traiterait comme faux — donc comme une donnée valide.
    invalide = (
        (df["validite"] <= 0).fillna(True)
        | (df["valeur"] <= SENTINELLE)
    )
    df.loc[invalide, "valeur"] = pd.NA
    df["flag_qualite"] = pd.Series(
        pd.Categorical(
            ["valide"] * len(df), categories=["valide", "provisoire", "invalide", "manquant"]
        )
    )
    df.loc[invalide, "flag_qualite"] = "invalide"
    # `Verification == 1` désigne les données vérifiées ; tout le reste est
    # provisoire et sera potentiellement corrigé lors de la validation N+1.
    df.loc[~invalide & (df["verification"] != 1), "flag_qualite"] = "provisoire"

    return df.sort_values("timestamp_utc").reset_index(drop=True)


def code_station(point_prelevement: str) -> str:
    """Extrait le code station d'un identifiant de point de prélèvement.

    Format observé : `FR/SPO-FR34051_8` — pays, préfixe SPO, code station, puis
    code polluant. Une même station porte donc plusieurs points de prélèvement,
    un par polluant mesuré : les joindre sans retirer le suffixe démultiplierait
    artificiellement le nombre de stations.
    """
    dernier = point_prelevement.rsplit("/", 1)[-1]
    sans_prefixe = dernier.removeprefix("SPO-")
    return sans_prefixe.rsplit("_", 1)[0]


def resume_qualite(df: pd.DataFrame) -> pd.Series:
    """Indicateurs de qualité d'une série, à journaliser à chaque ingestion."""
    n = len(df)
    if n == 0:
        return pd.Series(dtype="object")
    ecarts = df["timestamp_utc"].diff().dropna()
    return pd.Series(
        {
            "n_lignes": n,
            "debut": df["timestamp_utc"].min(),
            "fin": df["timestamp_utc"].max(),
            "taux_valide": float(df["valeur"].notna().mean()),
            "taux_provisoire": float((df["flag_qualite"] == "provisoire").mean()),
            "horodatages_dupliques": int(df["timestamp_utc"].duplicated().sum()),
            "pas_non_horaires": int((ecarts != pd.Timedelta(hours=1)).sum()),
        }
    )
