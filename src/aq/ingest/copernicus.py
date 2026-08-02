"""Ingestion Copernicus — ERA5 (météo, via CDS) et CAMS (qualité de l'air, via ADS).

Format de requête vérifié le 2026-07-28 contre les formulaires JSON publics du
catalogue (`form_*.json`), accessibles sans authentification. Le catalogue est un
STAC public : on peut lister les jeux, lire les contraintes et valider des noms de
variables sans compte — seule l'exécution d'une requête exige une clé (HTTP 401).

**Deux points qui piègent après la migration de l'infrastructure :**

- Un **compte ECMWF unique** dessert CDS et ADS, mais les deux services ont des
  **URL d'API distinctes**. Comme `~/.cdsapirc` ne porte qu'une seule URL, un projet
  qui utilise les deux doit instancier le client explicitement plutôt que de s'en
  remettre au fichier de configuration.
- L'ancien format d'identifiant `UID:API-KEY` ne fonctionne plus : la clé est
  désormais un unique *personal access token*.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Iterator

URL_CDS = "https://cds.climate.copernicus.eu/api"
URL_ADS = "https://ads.atmosphere.copernicus.eu/api"

JEU_ERA5 = "reanalysis-era5-single-levels"
JEU_CAMS_REANALYSE = "cams-europe-air-quality-reanalyses"
JEU_CAMS_PREVISION = "cams-europe-air-quality-forecasts"

# Licence exigée par les deux services, vérifiée le 2026-07-28 : c'est `cc-by` v1, et
# non la `licence-to-use-copernicus-products` v12 que l'ancienne infrastructure
# demandait. Accepter la seconde ne débloque rien — l'API renvoie le même HTTP 403,
# avec un message qui ne nomme pas la licence manquante.
LICENCE_REQUISE = ("cc-by", 1)

# Emprise France métropolitaine, dans l'ordre attendu par l'API : [N, O, S, E].
# Cet ordre n'est pas celui d'une bbox géographique usuelle (souvent O, S, E, N) :
# l'intervertir renverrait silencieusement une zone vide ou l'hémisphère opposé.
EMPRISE_FRANCE = [52, -5, 41, 10]

# Variables ERA5 retenues, séparées selon leur nature temporelle.
#
# **Cette séparation n'est pas un contournement technique, c'est la physique.** Les
# champs instantanés valent à l'heure estampillée ; les champs cumulés sont des totaux
# sur l'heure écoulée. Les lire de la même façon décale les seconds d'une heure et les
# rend faux d'un facteur qui dépend du pas de temps — sans qu'aucune métrique le signale.
#
# Le service impose d'ailleurs la séparation : une requête mêlant les deux natures est
# livrée en **archive ZIP** de deux fichiers, sous une extension `.nc`, et ce malgré
# `download_format="unarchived"` (vérifié par téléchargement réel le 2026-07-28).
#
# `boundary_layer_height` est la variable déterminante des épisodes hivernaux : elle
# fixe le volume dans lequel les émissions se diluent.
VARIABLES_ERA5_INSTANTANEES = [
    "boundary_layer_height",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_temperature",
    "2m_dewpoint_temperature",
    "surface_pressure",
]

VARIABLES_ERA5_CUMULEES = [
    "total_precipitation",
    "surface_solar_radiation_downwards",
]

FLUX_ERA5 = {
    "instantane": VARIABLES_ERA5_INSTANTANEES,
    "cumule": VARIABLES_ERA5_CUMULEES,
}

VARIABLES_ERA5 = VARIABLES_ERA5_INSTANTANEES + VARIABLES_ERA5_CUMULEES

VARIABLES_CAMS = [
    "nitrogen_dioxide",
    "ozone",
    "particulate_matter_2.5um",
    # **Les PM10 ajoutées le 01/08/2026.** Elles manquaient depuis le début du projet, et
    # la mesure qui l'a rendu intenable : sur les 52 vigilances réellement déclarées par
    # Atmo Occitanie entre janvier 2025 et mars 2026, **40 portent sur les PM10** et 12 sur
    # l'ozone. Le projet optimisait le polluant qui décide de l'indice ; l'AASQA déclenche
    # sur celui des particules.
    "particulate_matter_10um",
]

# Plafond du service ADS, mesuré via `estimate_costs` : 5000 **champs** par requête,
# un champ valant un couple (date, échéance, espèce). Un mois de prévisions pour les
# trois espèces sur 73 échéances en demande 6789 — la requête part et échoue en HTTP
# 403, avec un message tronqué qui ne dit pas de combien on dépasse. On découpe donc
# par espèce, ce qui ramène à 2263.
PLAFOND_CHAMPS_ADS = 5000

# Mois par requête ERA5. Mesuré via `estimate_costs` : 1 mois = 22 % du plafond,
# 4 mois = 86 %, 6 mois = 129 % (refusé). Quatre est le maximum utile.
MOIS_PAR_REQUETE_ERA5 = 4


@dataclass(frozen=True)
class Identifiants:
    """Paramètres de connexion à l'un des deux services."""

    url: str
    cle: str


def mois_entre(debut: date, fin: date) -> Iterator[tuple[int, int]]:
    """Itère sur les couples (année, mois) inclus dans l'intervalle.

    Le découpage mensuel n'est pas un détail d'implémentation : c'est la
    recommandation explicite du fournisseur (« submit small requests… download one
    month at a time rather than requesting entire years »). Les limites sont
    exprimées en nombre de champs, et une requête pluriannuelle est mise en file
    d'attente derrière des requêtes plus modestes.
    """
    annee, mois = debut.year, debut.month
    while (annee, mois) <= (fin.year, fin.month):
        yield annee, mois
        annee, mois = (annee + 1, 1) if mois == 12 else (annee, mois + 1)


def requete_era5(
    annee: int,
    mois: int,
    variables: list[str] | None = None,
    emprise: list[float] | None = None,
    flux: str = "instantane",
) -> dict:
    """Construit une requête ERA5 mensuelle horaire, pour un seul flux temporel.

    Les jours 29 à 31 sont demandés systématiquement : l'API ignore les dates
    inexistantes. Filtrer soi-même par longueur de mois n'apporterait rien et
    ajouterait une source d'erreur (années bissextiles).

    `flux` vaut `"instantane"` ou `"cumule"` — mélanger les deux fait livrer une
    archive ZIP au lieu d'un netCDF, et confondrait deux natures de grandeur.
    """
    if not 1 <= mois <= 12:
        raise ValueError(f"Mois hors bornes : {mois}")
    if flux not in FLUX_ERA5:
        raise ValueError(f"Flux inconnu : {flux} (attendu {sorted(FLUX_ERA5)})")

    return {
        "product_type": ["reanalysis"],
        "variable": list(variables or FLUX_ERA5[flux]),
        "year": [str(annee)],
        "month": [f"{mois:02d}"],
        "day": [f"{j:02d}" for j in range(1, 32)],
        "time": [f"{h:02d}:00" for h in range(24)],
        "area": list(emprise or EMPRISE_FRANCE),
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def requete_cams(
    annee: int,
    mois: int,
    variables: list[str] | None = None,
    type_reanalyse: str = "validated_reanalysis",
) -> dict:
    """Construit une requête CAMS de réanalyse régionale européenne.

    Ce jeu n'accepte **ni découpage géographique ni sélection horaire** : le domaine
    européen entier est livré, mois par mois. Le recadrage sur la France se fait en
    post-traitement local.

    `model="ensemble"` désigne la médiane des 9 à 11 modèles de chimie-transport,
    plus robuste qu'un modèle isolé.

    ⚠️ Cette réanalyse **assimile les observations de surface EEA** — donc les mesures
    que le projet cherche à prédire. L'employer comme variable d'entrée d'un modèle
    de correction de biais est partiellement circulaire, et gonflerait les scores sans
    qu'aucune métrique ne le signale. Préférer les *prévisions* CAMS, ou mesurer
    explicitement l'écart entre les deux régimes.
    """
    if type_reanalyse not in {"validated_reanalysis", "interim_reanalysis"}:
        raise ValueError(f"Type de réanalyse inconnu : {type_reanalyse}")

    return {
        "variable": list(variables or VARIABLES_CAMS),
        "model": ["ensemble"],
        "level": ["0"],  # niveau sol
        "type": [type_reanalyse],
        "year": [str(annee)],
        "month": [f"{mois:02d}"],
    }


ABREGE_ESPECE = {
    "nitrogen_dioxide": "no2",
    "ozone": "o3",
    "particulate_matter_2.5um": "pm25",
    "particulate_matter_10um": "pm10",
}


def _abrege(espece: str) -> str:
    """Nom court d'une espèce, pour les noms de fichiers."""
    return ABREGE_ESPECE.get(espece, espece.replace(".", "").replace("_", ""))


def cout_champs(n_especes: int, n_echeances: int, n_jours: int = 31) -> int:
    """Nombre de champs d'une requête CAMS, tel que le service le facture.

    Vérifié contre `estimate_costs` : un mois de 31 jours, 3 espèces et 73 échéances
    donne bien 6789 = 31 × 73 × 3. Savoir le calculer évite d'apprendre le dépassement
    par un HTTP 403 dont le message est tronqué.
    """
    return n_jours * n_echeances * n_especes


# Les modèles de chimie-transport de l'ensemble CAMS. `ensemble` en est la **médiane** ; les
# autres sont les membres individuels. Leur **désaccord** est une estimation d'incertitude
# native, que le projet a longtemps remplacée par des substituts — l'écart entre échéances,
# un détecteur d'anomalies — alors que la grandeur existe en amont.
#
# Six membres diversifiés couvrent des chimies, des inventaires et des schémas de transport
# différents : CHIMERE est celui de PREV'AIR, MOCAGE celui de Météo-France, les quatre autres
# viennent d'équipes norvégienne, finlandaise, néerlandaise et suédoise.
MEMBRES_DIVERSIFIES = ["chimere", "emep", "mocage", "silam", "lotos", "match"]


def requete_cams_prevision(
    annee: int,
    mois: int,
    variables: list[str] | None = None,
    emprise: list[float] | None = None,
    echeances_h: range | list[int] | None = None,
    modeles: list[str] | None = None,
) -> dict:
    """Construit une requête de **prévisions** CAMS Europe, une journée par jour du mois.

    C'est ce jeu-ci, et non la réanalyse, qui constitue la barre à battre. La réanalyse
    assimile les observations EEA — celles que le projet prédit — donc la comparer à ces
    mêmes observations flatte le modèle d'un avantage qu'il n'aurait pas en exploitation.
    La prévision, elle, n'a rien vu du futur qu'elle annonce : c'est la seule référence
    honnête pour les échéances réglementaires J+1 à J+3.

    Contrairement à la réanalyse, ce jeu **accepte** `area` et `leadtime_hour`
    (vérifié par téléchargement réel le 2026-07-28).
    """
    if not 1 <= mois <= 12:
        raise ValueError(f"Mois hors bornes : {mois}")

    echeances = list(echeances_h if echeances_h is not None else range(0, 73))
    if any(h < 0 or h > 96 for h in echeances):
        raise ValueError("Les échéances CAMS Europe vont de 0 à 96 h")

    # Une seule espèce par défaut, et c'est l'ozone : demander les trois dépasse le
    # plafond, et l'ozone pilote l'indice ATMO occitan dans 87,8 % des cas. Un défaut
    # qui échoue systématiquement serait pire qu'un défaut choisi.
    especes = list(variables or ["ozone"])
    # **Le modèle est une dimension du coût, au même titre que l'espèce et l'échéance.**
    # L'oublier ferait passer une requête à six membres pour une requête à un seul, et le
    # service la refuserait en HTTP 403 sans dire de combien.
    membres = list(modeles or ["ensemble"])
    cout = cout_champs(len(especes), len(echeances)) * len(membres)
    if cout > PLAFOND_CHAMPS_ADS:
        raise ValueError(
            f"{cout} champs demandés, plafond {PLAFOND_CHAMPS_ADS}. Découper par "
            "espèce ou réduire les échéances — le service refuserait la requête en "
            "HTTP 403 sans dire de combien on dépasse."
        )

    return {
        "variable": especes,
        "model": membres,
        "level": ["0"],
        "type": ["forecast"],
        # **Le dernier jour du mois, jamais 31 en dur.** Une plage « 2024-02-01/
        # 2024-02-31 » désigne une date inexistante : le service la refuse en HTTP 500,
        # sans dire laquelle des deux bornes est fautive. Le piège est vicieux parce
        # qu'il ne se manifeste que sur les mois de moins de 31 jours — janvier,
        # juillet et décembre passaient, février et avril non.
        "date": [f"{annee}-{mois:02d}-01/{annee}-{mois:02d}-"
                 f"{calendar.monthrange(annee, mois)[1]:02d}"],
        "time": ["00:00"],
        "leadtime_hour": [str(h) for h in echeances],
        "area": list(emprise or EMPRISE_FRANCE),
        "data_format": "netcdf",
    }


def normaliser_longitudes(jeu, trier: bool = True):
    """Ramène un champ Copernicus à des axes croissants en longitude [-180, 180].

    **Le piège, mesuré sur fichier réel.** Les deux services ne partagent pas la même
    convention : ERA5 renvoie des longitudes en [-180, 180], CAMS Europe en [0, 360].
    Pire, sur une emprise à cheval sur le méridien de Greenwich, l'axe CAMS livré est
    **non monotone** — observé `358,05 … 359,95` puis `0,05 … 4,95` dans le même
    fichier.

    Conséquence : `sel(longitude=-1.5, method="nearest")` ne trouve rien de correct.
    Selon la version de la bibliothèque, l'appel lève une erreur ou renvoie la cellule
    de bord — c'est-à-dire une valeur plausible, prise à des centaines de kilomètres.
    Toute station à l'ouest de Greenwich est concernée, ce qui inclut l'ouest de
    l'Occitanie (jusqu'à −0,33° dans le Gers et les Hautes-Pyrénées).

    On normalise donc systématiquement à l'ouverture, plutôt que de se fier au service.
    Les latitudes sont également remises en ordre croissant : les deux jeux les livrent
    décroissantes, ce que l'interpolation n'accepte pas non plus.

    `trier=False` se contente de convertir les longitudes, sans réordonner le champ.
    Le tri déplace physiquement toutes les données — mesuré à 52 s pour une journée de
    prévisions CAMS — et n'est utile qu'aux opérations qui exigent un axe monotone,
    comme `sel(method="nearest")` ou l'interpolation. Un rattachement par indices
    entiers n'en a pas besoin.
    """
    lon = "longitude" if "longitude" in jeu.coords else "lon"
    lat = "latitude" if "latitude" in jeu.coords else "lat"

    jeu = jeu.assign_coords({lon: (((jeu[lon] + 180) % 360) - 180)})
    return jeu.sortby([lon, lat]) if trier else jeu


def plan_telechargement(
    debut: date, fin: date, service: str = "era5"
) -> list[tuple[str, dict]]:
    """Liste des (nom de fichier, requête) à exécuter, un par mois.

    Produire le plan sans l'exécuter permet de le chiffrer, de le reprendre après
    interruption et de le tester sans compte.
    """
    constructeurs = {
        "era5": requete_era5,
        "cams": requete_cams,
        "cams_prevision": requete_cams_prevision,
    }
    if service not in constructeurs:
        raise ValueError(f"Service inconnu : {service}")

    construire = constructeurs[service]

    # ERA5 donne deux fichiers par mois — un par flux temporel. Les demander ensemble
    # ferait livrer une archive ZIP sous une extension `.nc`.
    # ERA5 : **quatre mois par requête**, et c'est la granularité qui décide du temps
    # total. Un mois seul n'utilise que 22 % du plafond (26 784 champs sur 121 000) ;
    # quatre montent à 86 %. Comme le coût du service est *par requête* — l'attente en
    # file représentant 84 % du temps, mesuré —, un découpage mensuel paie quatre fois
    # le prix pour la même charge. Voir la règle 1 de `CLAUDE.md`.
    if service == "era5":
        entrees = []
        for flux in FLUX_ERA5:
            tous = list(mois_entre(debut, fin))
            for i in range(0, len(tous), MOIS_PAR_REQUETE_ERA5):
                groupe = tous[i:i + MOIS_PAR_REQUETE_ERA5]
                requete = construire(*groupe[0], flux=flux)
                # Un groupe ne doit pas chevaucher deux années : `year` et `month` sont
                # des listes croisées, si bien que [2019,2020]×[11,12] demanderait aussi
                # 2019-12 et 2020-11. On scinde donc par année.
                annees = sorted({a for a, _ in groupe})
                for annee in annees:
                    mois_annee = [m for a, m in groupe if a == annee]
                    sous = dict(requete)
                    sous["year"] = [str(annee)]
                    sous["month"] = [f"{m:02d}" for m in mois_annee]
                    etiquette = (f"{annee}{mois_annee[0]:02d}"
                                 if len(mois_annee) == 1
                                 else f"{annee}{mois_annee[0]:02d}_{mois_annee[-1]:02d}")
                    entrees.append((f"era5_{flux}_{etiquette}.nc", sous))
        return entrees

    # CAMS prévisions : une requête par espèce, sans quoi le mois dépasse le plafond
    # de 5000 champs du service.
    #
    # **Un mois par requête n'utilise que 44 % du plafond** (2190 champs sur 5000). Le
    # coût du service étant *par requête* — attente en file comprise, largement
    # dominante —, cette granularité paie deux fois le prix pour la même charge.
    # Regrouper deux mois monte à 89 % du plafond et divise le nombre de requêtes par
    # deux. Voir la règle 1 de `CLAUDE.md`.
    if service == "cams_prevision":
        mois_tous = list(mois_entre(debut, fin))
        paires = [mois_tous[i:i + 2] for i in range(0, len(mois_tous), 2)]
        entrees = []
        for paire in paires:
            for espece in VARIABLES_CAMS:
                requete = construire(*paire[0], variables=[espece])
                requete["date"] = [
                    f"{a}-{m:02d}-01/{a}-{m:02d}-{calendar.monthrange(a, m)[1]:02d}"
                    for a, m in paire
                ]
                etiquette = "_".join(f"{a}{m:02d}" for a, m in paire)
                entrees.append(
                    (f"cams_prevision_{_abrege(espece)}_{etiquette}.nc", requete)
                )
        return entrees

    return [
        (f"{service}_{annee}{mois:02d}.nc", construire(annee, mois))
        for annee, mois in mois_entre(debut, fin)
    ]


def _client(identifiants: Identifiants):
    """Client bas niveau, instancié explicitement plutôt que via `~/.cdsapirc`.

    Le fichier de configuration ne porte qu'une seule URL, or le projet interroge deux
    services aux endpoints distincts avec le même jeton.
    """
    from ecmwf.datastores import Client

    return Client(url=identifiants.url, key=identifiants.cle)


def accepter_licence(identifiants: Identifiants) -> None:
    """Accepte la licence exigée, si elle ne l'est pas déjà.

    Sans elle, toute requête échoue en HTTP 403 avec un message qui **ne nomme pas**
    la licence manquante — il renvoie vers une page web. Le nom se lit en revanche
    dans le lien `rel="license"` de la collection STAC, d'où la constante figée ici.
    """
    client = _client(identifiants)
    nom, revision = LICENCE_REQUISE
    if nom not in {licence.get("id") for licence in client.get_accepted_licences()}:
        client.accept_licence(nom, revision=revision)


def executer(
    identifiants: Identifiants,
    jeu: str,
    requete: dict,
    destination: str,
) -> str:
    """Exécute une requête et télécharge le résultat."""
    _client(identifiants).retrieve(jeu, requete, target=destination)
    return destination
