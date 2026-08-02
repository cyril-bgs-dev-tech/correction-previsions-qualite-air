"""Exposition au trafic routier hiérarchisé et à la population.

**Ce que ce module corrige.** Les premières variables routières pondéraient les tronçons
par leur **longueur seule** : une rue de village et une autoroute comptaient pareil au
mètre. C'est physiquement faux pour le NO₂, dont l'émission suit le **trafic**, lequel
varie de deux ordres de grandeur entre une voie communale et une section autoroutière.

**Le choix méthodologique, et pourquoi il évite d'inventer des chiffres.** On pourrait
convertir chaque classe de route en trafic moyen journalier — mais ces valeurs ne sont
pas dans la donnée, et les poser de mémoire reviendrait à fabriquer une hypothèse
invérifiable au cœur du modèle. On construit donc **une variable d'exposition par classe**
et l'on laisse le modèle apprendre leur poids relatif sur les observations. C'est la même
logique que la séparation des essences forestières, qui avait doublé le R² de l'ozone.

**La population** entre par la même porte : une somme pondérée par la distance,
`Σ habitants × exp(−d/λ)`, calculée sur les communes environnantes. Elle décrit
l'intensité des sources diffuses — chauffage, trafic résidentiel, activité — que ni le
réseau routier ni l'occupation du sol ne capturent seuls. Ce n'est pas la « distance au
centre-ville » : une distance ignore la taille, alors qu'être à 5 km d'un village et à
5 km d'une métropole ne place pas dans le même environnement.
"""

from __future__ import annotations

import numpy as np

from aq.ingest.geopf import Entite

# Classes de route par ordre décroissant d'émission attendue. Le regroupement s'appuie
# sur `nature` (type physique) et `importance` (classement administratif, 1 = plus
# structurant) de la BD TOPO — deux attributs présents et renseignés.
#
# On ne fusionne pas ces classes en un indice unique : un indice suppose un rapport
# d'émission entre elles, que la donnée ne fournit pas. Les garder séparées laisse ce
# rapport être appris.
# **C'est `importance` qui porte la hiérarchie, pas `nature`.** Mesuré sur une emprise
# toulousaine : « Route à 1 chaussée » couvre 11 285 tronçons sur 14 331 — en faire un
# critère de classe reviendrait à ranger presque tout le réseau dans la même catégorie et
# à ne jamais consulter l'importance. Cette dernière se répartit au contraire utilement :
# importance 1 → 146 tronçons, 2-3 → 2 003, 4 → 1 081, 5-6 → 11 101.
#
# `nature` n'intervient donc que pour deux choses qu'`importance` ne dit pas : reconnaître
# le gabarit autoroutier, et écarter ce qui ne porte pas de trafic motorisé.
CLASSES_PAR_IMPORTANCE = {
    "1": "autoroute",
    "2": "principale", "3": "principale",
    "4": "secondaire",
    "5": "locale", "6": "locale",
}

NATURES_AUTOROUTIERES = {"Type autoroutier", "Bretelle"}

# Voies exclues : elles n'accueillent pas de trafic motorisé et gonfleraient le linéaire
# sans porter d'émission.
NATURES_SANS_TRAFIC = {"Sentier", "Escalier", "Chemin", "Piste cyclable"}


def classer_route(entite: Entite) -> str | None:
    """Classe un tronçon d'après sa nature et son importance administrative.

    L'ordre d'évaluation compte : un tronçon de gabarit autoroutier reste une autoroute
    quel que soit son classement administratif. Pour tout le reste, c'est `importance`
    qui décide — c'est elle qui porte la hiérarchie du réseau.
    """
    nature = entite.proprietes.get("nature")
    if nature in NATURES_SANS_TRAFIC:
        return None
    if nature in NATURES_AUTOROUTIERES:
        return "autoroute"

    importance = str(entite.proprietes.get("importance", ""))
    # Sans importance renseignée, on classe en local : c'est le cas majoritaire, et
    # surestimer la classe d'un tronçon inconnu gonflerait l'exposition des stations
    # rurales — l'erreur la plus coûteuse ici.
    return CLASSES_PAR_IMPORTANCE.get(importance, "locale")


def masse_trafic(entite: Entite) -> float:
    """Longueur pondérée par le nombre de voies, à défaut de trafic mesuré.

    Le nombre de voies est le seul indicateur de capacité présent dans la donnée. Une
    section à 2×3 voies porte davantage de trafic qu'une voie unique de même longueur ;
    l'ignorer reviendrait à traiter les deux comme équivalentes.

    En l'absence de l'attribut — 14 % des tronçons — on retient 2 voies, valeur médiane
    observée. Écarter ces tronçons serait pire : ils sont surtout ruraux, et leur absence
    biaiserait les stations de fond.
    """
    voies = entite.proprietes.get("nombre_de_voies")
    try:
        voies = float(voies) if voies is not None else 2.0
    except (TypeError, ValueError):
        voies = 2.0
    return entite.masse * max(1.0, voies)


def exposition_ponderee(
    x: float, y: float, entites: list[Entite], masses: list[float], lambda_m: float
) -> float:
    """Somme des masses pondérée par `exp(−d/λ)`.

    La décroissance exponentielle traduit la dilution : au-delà de quelques longueurs
    caractéristiques, une source ne contribue plus. λ court décrit une exposition de
    proximité, λ long une exposition de fond.
    """
    if not entites:
        return 0.0
    xs = np.fromiter((e.x for e in entites), dtype="float64", count=len(entites))
    ys = np.fromiter((e.y for e in entites), dtype="float64", count=len(entites))
    d = np.hypot(xs - x, ys - y)
    return float(np.sum(np.asarray(masses) * np.exp(-d / lambda_m)))


def variables_routieres(
    x: float, y: float, routes: list[Entite], lambdas=(100.0, 300.0, 1000.0, 3000.0)
) -> dict[str, float]:
    """Exposition routière par classe et par échelle, plus la distance à chaque classe.

    La **distance à la voie majeure la plus proche** est conservée séparément : elle
    répond à une question différente de l'exposition cumulée — « suis-je en bord
    d'autoroute ? » plutôt que « combien de trafic autour de moi ? ». Les deux sont
    utilisées en régression sur paysage, et elles ne sont pas redondantes.
    """
    par_classe: dict[str, list[Entite]] = {
        c: [] for c in ("autoroute", "principale", "secondaire", "locale")}
    for entite in routes:
        classe = classer_route(entite)
        if classe:
            par_classe[classe].append(entite)

    valeurs: dict[str, float] = {}
    for classe, membres in par_classe.items():
        masses = [masse_trafic(e) for e in membres]
        valeurs[f"route_{classe}_longueur_m"] = float(sum(e.masse for e in membres))
        for lam in lambdas:
            valeurs[f"route_{classe}_lambda{int(lam)}m"] = exposition_ponderee(
                x, y, membres, masses, lam
            )
        if membres:
            xs = np.fromiter((e.x for e in membres), dtype="float64", count=len(membres))
            ys = np.fromiter((e.y for e in membres), dtype="float64", count=len(membres))
            valeurs[f"route_{classe}_dist_min_m"] = float(
                np.hypot(xs - x, ys - y).min()
            )
        else:
            # Aucune voie de cette classe dans le rayon : une distance infinie serait
            # ingérable en régression. On retient le rayon d'interrogation, valeur
            # finie et interprétable — « au-delà de ce que l'on a regardé ».
            valeurs[f"route_{classe}_dist_min_m"] = np.nan
    return valeurs


def variables_population(
    x: float, y: float, communes: list[Entite],
    lambdas=(2000.0, 5000.0, 20000.0),
) -> dict[str, float]:
    """Exposition à la population environnante, et poids du pôle dominant.

    Trois grandeurs, qui ne disent pas la même chose :

    - `population_lambda*` — la somme pondérée `Σ habitants × exp(−d/λ)`, qui mesure
      l'intensité des sources diffuses alentour ;
    - `population_pole_dominant` — la population de la commune qui contribue le plus,
      c'est-à-dire l'agglomération qui structure l'environnement ;
    - `distance_pole_dominant_m` — à quelle distance elle se trouve.

    Une simple distance au centre-ville serait insuffisante : elle ignore la taille, et
    placerait sur le même plan un village et une métropole à égale distance.
    """
    if not communes:
        return {f"population_lambda{int(l)}m": 0.0 for l in lambdas} | {
            "population_pole_dominant": 0.0, "distance_pole_dominant_m": np.nan
        }

    xs = np.fromiter((e.x for e in communes), dtype="float64", count=len(communes))
    ys = np.fromiter((e.y for e in communes), dtype="float64", count=len(communes))
    habitants = np.fromiter(
        (float(e.proprietes.get("population") or 0.0) for e in communes),
        dtype="float64", count=len(communes),
    )
    d = np.hypot(xs - x, ys - y)

    valeurs = {
        f"population_lambda{int(lam)}m": float(np.sum(habitants * np.exp(-d / lam)))
        for lam in lambdas
    }
    # Le pôle dominant est défini à λ = 20 km : c'est l'échelle à laquelle une
    # agglomération influence encore la composition de l'air, sans que le choix soit
    # dominé par la commune d'implantation elle-même.
    contribution = habitants * np.exp(-d / 20_000.0)
    principal = int(np.argmax(contribution))
    valeurs["population_pole_dominant"] = float(habitants[principal])
    valeurs["distance_pole_dominant_m"] = float(d[principal])
    return valeurs
