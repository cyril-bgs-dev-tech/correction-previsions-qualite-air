"""Surveiller la dérive du modèle amont — la voir le jour où elle se produit.

**Le problème.** Une prévision CAMS ne porte aucun numéro de version : mêmes attributs,
même grille, même producteur d'un bout à l'autre de l'archive. Quand le système change —
et il change une à deux fois par an — rien ne le signale au fichier. L'erreur du modèle
se déplace, et l'on ne s'en aperçoit qu'en recalculant les scores plusieurs mois plus
tard. Sur ce projet : rupture en novembre 2024, découverte en juillet 2026.

C'est un problème pour toute AASQA, et il est double : une correction apprise sur
l'ancien régime devient partiellement fausse, et un prévisionniste qui fait confiance au
modèle continue de lui faire confiance sans raison.

**Le principe.** Comparer en continu l'erreur du modèle amont à sa propre distribution
historique, et déclencher quand l'écart cumulé dépasse ce que le passé rendait plausible.

Trois précautions, dont chacune suffirait à rendre l'indicateur inutilisable :

- **Déssaisonnaliser d'abord.** Le biais de CAMS sur l'ozone suit un cycle annuel de
  grande amplitude. Un seuil posé sur le biais brut se déclencherait chaque printemps, et
  l'alarme serait ignorée dès la deuxième année.
- **Cumuler, ne pas seuiller point par point.** Un changement de système produit un
  décalage **petit et permanent**, pas un pic. Un seuil instantané le rate ; une somme
  cumulée (CUSUM) l'accumule jusqu'à devenir indiscutable. C'est le compromis classique
  entre délai de détection et fausses alertes.
- **Calibrer le seuil sur les données, pas sur la loi normale.** Le biais journalier est
  fortement autocorrélé — les régimes météo durent plusieurs jours — si bien que les
  formules d'ARL sous indépendance sous-estiment largement les fausses alertes.

**Et distinguer un changement de modèle d'un épisode météo.** Les deux déplacent
l'erreur. Deux discriminants, tous deux calculables ici :

- **la concordance spatiale** — un changement de système déplace *toutes* les stations
  dans le même sens ; un épisode est régional ;
- **la persistance** — un épisode se referme, une version ne se referme pas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Deux harmoniques : le cycle annuel et sa première correction. Au-delà, on se met à
# ajuster la météo de l'année de référence plutôt que la saisonnalité du biais.
N_HARMONIQUES = 2

# Décalage à détecter, en écarts-types de la série déssaisonnalisée. 0,5 est la valeur
# usuelle du CUSUM : elle vise un décalage d'environ 1 σ, ce qui correspond ici à
# quelques µg/m³ de biais — l'ordre de grandeur d'un changement de version.
K_CUSUM = 0.5

JOURS_AN = 365.2425


# --------------------------------------------------------------------------- #
# Saisonnalité
# --------------------------------------------------------------------------- #

def matrice_harmoniques(jour_annee: np.ndarray,
                        n_harmoniques: int = N_HARMONIQUES) -> np.ndarray:
    """Constante + sinus/cosinus annuels. Une colonne de plus par harmonique."""
    angle = 2.0 * np.pi * np.asarray(jour_annee, dtype="float64") / JOURS_AN
    colonnes = [np.ones_like(angle)]
    for k in range(1, n_harmoniques + 1):
        colonnes += [np.sin(k * angle), np.cos(k * angle)]
    return np.column_stack(colonnes)


def ajuster_saisonnalite(jour_annee: np.ndarray, valeurs: np.ndarray,
                         n_harmoniques: int = N_HARMONIQUES) -> np.ndarray:
    """Coefficients du cycle annuel du biais, estimés par moindres carrés.

    Ajusté sur la **période de référence seule**. L'ajuster sur toute la série ferait
    absorber la rupture par la saisonnalité — l'indicateur se rendrait aveugle à ce
    qu'il cherche.
    """
    conception = matrice_harmoniques(jour_annee, n_harmoniques)
    coefficients, *_ = np.linalg.lstsq(conception, np.asarray(valeurs, dtype="float64"),
                                       rcond=None)
    return coefficients


def predire_saisonnalite(coefficients: np.ndarray, jour_annee: np.ndarray,
                         n_harmoniques: int = N_HARMONIQUES) -> np.ndarray:
    return matrice_harmoniques(jour_annee, n_harmoniques) @ coefficients


# --------------------------------------------------------------------------- #
# CUSUM
# --------------------------------------------------------------------------- #

@dataclass
class Cusum:
    """Trajectoire du CUSUM bilatéral et instants d'alarme."""

    haut: np.ndarray
    bas: np.ndarray
    alarmes: np.ndarray  # indices, sens = +1 (dérive vers le haut) ou -1
    sens: np.ndarray


def cusum(z: np.ndarray, k: float = K_CUSUM, h: float = 5.0) -> Cusum:
    """CUSUM bilatéral sur une série centrée-réduite.

    `S⁺ = max(0, S⁺ + z − k)` accumule les écarts positifs au-delà de la tolérance `k` ;
    `S⁻` fait de même pour les écarts négatifs. Franchir `h` déclenche, puis la statistique
    est **remise à zéro** — sans quoi une alarme resterait vraie à jamais et masquerait
    tout événement ultérieur.
    """
    z = np.asarray(z, dtype="float64")
    haut = np.zeros(len(z))
    bas = np.zeros(len(z))
    alarmes: list[int] = []
    sens: list[int] = []

    s_haut = s_bas = 0.0
    for i, valeur in enumerate(z):
        if not np.isfinite(valeur):
            haut[i], bas[i] = s_haut, s_bas
            continue
        s_haut = max(0.0, s_haut + valeur - k)
        s_bas = max(0.0, s_bas - valeur - k)
        haut[i], bas[i] = s_haut, s_bas
        if s_haut > h or s_bas > h:
            alarmes.append(i)
            sens.append(1 if s_haut > h else -1)
            s_haut = s_bas = 0.0

    return Cusum(haut=haut, bas=bas,
                 alarmes=np.array(alarmes, dtype="int64"),
                 sens=np.array(sens, dtype="int64"))


def calibrer_seuil(z_reference: np.ndarray, k: float = K_CUSUM,
                   fausses_alertes_tolerees: int = 0,
                   grille: np.ndarray | None = None) -> float:
    """Plus petit `h` dont la période de référence tire au plus le nombre toléré.

    **Calibrer sur les données plutôt que sur la loi normale.** Le biais journalier est
    autocorrélé sur plusieurs jours ; les seuils tabulés, établis sous indépendance,
    donneraient bien plus de fausses alertes qu'annoncé. Ici le seuil est celui qui tient
    sur l'historique observé — et il faut annoncer sur quelle durée il a été calibré,
    puisque c'est cette durée qui définit le taux garanti.
    """
    if grille is None:
        grille = np.arange(2.0, 40.05, 0.5)
    for h in grille:
        if len(cusum(z_reference, k=k, h=float(h)).alarmes) <= fausses_alertes_tolerees:
            return float(h)
    return float(grille[-1])


# --------------------------------------------------------------------------- #
# Concordance spatiale — modèle ou météo ?
# --------------------------------------------------------------------------- #

def grouper_alarmes(dates: pd.Series, ecart_min_jours: int = 30) -> pd.Series:
    """Ne retient que la **première** alarme de chaque épisode.

    Une dérive permanente franchit le seuil, se remet à zéro, et le franchit de nouveau
    le lendemain : tant qu'elle dure, elle déclenche tous les jours. C'est arithmétiquement
    correct et opérationnellement inutilisable — l'information est *quand la dérive a
    commencé*, pas *qu'elle dure encore*.

    **Un épisode se ferme après `ecart_min_jours` sans aucune alarme**, et se mesure
    donc à l'alarme précédente, jamais à l'ouverture de l'épisode. Comparer à l'ouverture
    rouvrirait un épisode à intervalle fixe tant que la dérive dure, ce qui reproduirait
    le défaut qu'on cherche à corriger.
    """
    dates = pd.Series(dates).sort_values().reset_index(drop=True)
    if dates.empty:
        return dates
    gardees = [dates.iloc[0]]
    precedente = dates.iloc[0]
    for date in dates.iloc[1:]:
        if (date - precedente).days >= ecart_min_jours:
            gardees.append(date)
        precedente = date
    return pd.Series(gardees, name=dates.name)


def part_stations_concordantes(ecarts: pd.Series) -> float:
    """Part des stations dont l'écart va dans le sens majoritaire.

    Proche de 1 : le déplacement est **partagé par tout le réseau** — signature d'un
    changement de système. Autour de 0,5-0,7 : le déplacement est régional, donc plutôt
    météorologique. Ce n'est pas une preuve, c'est un discriminant.
    """
    valeurs = pd.Series(ecarts).dropna()
    if valeurs.empty:
        return float("nan")
    signe = np.sign(valeurs.median())
    if signe == 0:
        return float("nan")
    return float((np.sign(valeurs) == signe).mean())


# --------------------------------------------------------------------------- #
# Surveillance de bout en bout
# --------------------------------------------------------------------------- #

@dataclass
class Surveillance:
    journalier: pd.DataFrame          # date, biais, attendu, ecart, z, cusum_haut/bas
    seuil: float
    alarmes: pd.DataFrame             # date, sens, jours_depuis_debut_suivi
    debut_suivi: pd.Timestamp
    ecart_type_reference: float
    meta: dict = field(default_factory=dict)


def biais_journalier(paires: pd.DataFrame, colonne_prevu: str = "cams",
                     colonne_observe: str = "valeur",
                     n_minimum: int = 100) -> pd.DataFrame:
    """Biais moyen du modèle amont, par jour, sur l'ensemble du réseau.

    Les jours à faible effectif sont écartés : leur bruit d'échantillonnage se
    confondrait avec le signal recherché.
    """
    travail = paires[["timestamp_utc", colonne_prevu, colonne_observe]].dropna()
    jours = pd.to_datetime(travail["timestamp_utc"]).dt.tz_convert("UTC").dt.normalize()
    ecarts = travail[colonne_prevu].to_numpy() - travail[colonne_observe].to_numpy()

    table = (pd.DataFrame({"date": jours.to_numpy(), "ecart": ecarts})
             .groupby("date", as_index=False)
             .agg(biais=("ecart", "mean"), n=("ecart", "size")))
    return table[table["n"] >= n_minimum].reset_index(drop=True)


def surveiller(paires: pd.DataFrame, debut_suivi: pd.Timestamp,
               k: float = K_CUSUM, fausses_alertes_tolerees: int = 0,
               n_harmoniques: int = N_HARMONIQUES,
               ecart_min_jours: int = 30,
               **kwargs) -> Surveillance:
    """Ajuste la saisonnalité sur la référence, puis surveille la suite.

    `debut_suivi` sépare strictement les deux rôles : tout ce qui précède sert à
    apprendre le comportement normal, tout ce qui suit est jugé. Aucune information
    postérieure n'entre dans la référence.
    """
    journalier = biais_journalier(paires, **kwargs)
    if journalier.empty:
        raise ValueError("aucun jour ne réunit assez d'observations")

    debut_suivi = pd.Timestamp(debut_suivi)
    if debut_suivi.tzinfo is None:
        debut_suivi = debut_suivi.tz_localize("UTC")

    journalier = journalier.sort_values("date").reset_index(drop=True)
    journalier["jour_annee"] = journalier["date"].dt.dayofyear
    reference = journalier["date"] < debut_suivi
    if reference.sum() < 60:
        raise ValueError(
            f"référence trop courte : {int(reference.sum())} jours, 60 au minimum")

    # **La référence doit couvrir un cycle annuel entier.** Sinon l'ajustement
    # harmonique doit *extrapoler* sur les jours de l'année qu'il n'a jamais vus, et
    # cette extrapolation est arbitraire : elle produit des alarmes qui ne signalent
    # qu'un trou dans la référence. Le défaut est passé inaperçu jusqu'à ce qu'un test
    # sur série synthétique déclenche deux alarmes sans aucune rupture.
    dates_reference = journalier.loc[reference, "date"]
    couverture = (dates_reference.max() - dates_reference.min()).days + 1
    if couverture < 330:
        raise ValueError(
            f"la référence couvre {couverture} jours : moins d'un cycle annuel. "
            "La saisonnalité serait extrapolée sur les jours de l'année non observés, "
            "et l'indicateur signalerait ce trou plutôt qu'une dérive.")

    coefficients = ajuster_saisonnalite(
        journalier.loc[reference, "jour_annee"].to_numpy(),
        journalier.loc[reference, "biais"].to_numpy(), n_harmoniques)
    journalier["attendu"] = predire_saisonnalite(
        coefficients, journalier["jour_annee"].to_numpy(), n_harmoniques)
    journalier["ecart"] = journalier["biais"] - journalier["attendu"]

    sigma = float(journalier.loc[reference, "ecart"].std(ddof=1))
    journalier["z"] = journalier["ecart"] / sigma

    seuil = calibrer_seuil(journalier.loc[reference, "z"].to_numpy(), k=k,
                           fausses_alertes_tolerees=fausses_alertes_tolerees)

    trace = cusum(journalier["z"].to_numpy(), k=k, h=seuil)
    journalier["cusum_haut"] = trace.haut
    journalier["cusum_bas"] = trace.bas

    # Seules comptent les alarmes de la période surveillée : celles de la référence ont
    # servi à fixer le seuil, les compter comme détections serait circulaire.
    brutes = pd.DataFrame(
        [{"date": journalier.loc[i, "date"], "sens": int(s)}
         for i, s in zip(trace.alarmes, trace.sens)
         if journalier.loc[i, "date"] >= debut_suivi],
        columns=["date", "sens"])

    brutes["date"] = pd.to_datetime(brutes["date"], utc=True)
    debuts = set(grouper_alarmes(brutes["date"], ecart_min_jours))
    episodes = brutes[brutes["date"].isin(debuts)].copy()
    episodes["jours_depuis_debut_suivi"] = (
        episodes["date"] - debut_suivi).dt.days.astype("int64")

    return Surveillance(
        journalier=journalier, seuil=seuil,
        alarmes=episodes.reset_index(drop=True),
        debut_suivi=debut_suivi, ecart_type_reference=sigma,
        meta={"n_reference": int(reference.sum()),
              "n_suivi": int((~reference).sum()),
              "k": k, "n_harmoniques": n_harmoniques},
    )


def delai_de_detection(surveillance: Surveillance,
                       date_evenement: pd.Timestamp) -> int | None:
    """Jours écoulés entre un événement connu et la première alarme postérieure.

    Renvoie `None` si l'événement n'est jamais détecté — un résultat, pas une absence.
    """
    date_evenement = pd.Timestamp(date_evenement)
    if date_evenement.tzinfo is None:
        date_evenement = date_evenement.tz_localize("UTC")
    posterieures = surveillance.alarmes[surveillance.alarmes["date"] >= date_evenement]
    if posterieures.empty:
        return None
    return int((posterieures["date"].iloc[0] - date_evenement).days)
