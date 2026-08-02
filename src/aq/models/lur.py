"""Modèle *Land-Use Regression* — concentration moyenne annuelle ~ paysage.

La LUR explique la variance **spatiale** des concentrations par la structure du
paysage autour du point de mesure. Elle ne prédit pas une heure : elle prédit un
niveau moyen, et permet ensuite de cartographier en tout point du territoire.

**Le régime statistique est celui des très petits échantillons.** L'effectif utile est
le nombre de STATIONS — 23 de fond en Occitanie, 312 en métropole — face à plusieurs
dizaines de variables candidates fortement corrélées entre elles (les λ successifs
d'une même couche mesurent presque la même chose). Sans discipline, un ajustement
parfait est garanti et entièrement fallacieux.

D'où le protocole de la littérature ESCAPE, repris ici :

1. **Sélection ascendante** : on ajoute une variable à la fois, celle qui améliore le
   plus le R² ajusté, et l'on s'arrête tôt (5 prédicteurs par défaut).
2. **Contrainte de signe** : une variable dont le coefficient contredit le mécanisme
   physique attendu est **rejetée**, même si elle améliore le score. C'est ce qui
   distingue un modèle explicatif d'un ajustement de courbe.
3. **Une seule variable par famille** : retenir deux λ de la même couche revient à
   compter deux fois le même effet, avec des coefficients instables et de signes
   opposés.
4. **Validation par station exclue** (*leave-one-station-out*) : la seule qui teste ce
   qui nous intéresse — prédire là où l'on n'a pas mesuré. Une validation croisée
   ordinaire laisserait la station dans l'apprentissage et surestimerait massivement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Signe attendu du coefficient, par mécanisme physique. Une variable dont le signe
# estimé contredit cette attente est écartée.
#   +1 : la variable augmente la concentration
#   -1 : elle la diminue
#    0 : signe non contraint (mécanisme ambivalent)
SIGNES_ATTENDUS = {
    # Le trafic est une source directe de NO₂ et de particules primaires.
    "route": +1,
    # Les forêts émettent des précurseurs d'ozone (isoprène pour les chênes) mais
    # constituent aussi un puits par dépôt sec : l'effet net dépend du polluant.
    # On laisse libre plutôt que d'imposer une hypothèse fausse la moitié du temps.
    "chene": 0,
    "feuillu_autre": 0,
    "conifere": 0,
    "foret_tot": 0,
    # Une distance grande à une source éloigne de la source, donc réduit l'exposition.
    "dist_min": -1,
}


def famille(colonne: str) -> str:
    """Famille d'une variable : tous les λ d'une même couche partagent la leur.

    Sert à interdire la sélection de deux variables redondantes — deux λ de la même
    couche mesurent presque la même chose, et les retenir ensemble produit des
    coefficients instables aux signes opposés.
    """
    if "_dist_min" in colonne:
        return f"{colonne.split('_dist_min')[0]}_dist"
    return re.split(r"_(lambda|buffer|surface|longueur)", colonne)[0]


def signe_attendu(colonne: str) -> int:
    if "_dist_min" in colonne:
        return SIGNES_ATTENDUS["dist_min"]
    for prefixe, signe in SIGNES_ATTENDUS.items():
        if colonne.startswith(prefixe):
            return signe
    return 0


@dataclass
class ModeleLUR:
    """Modèle ajusté : les variables retenues, dans l'ordre de sélection."""

    variables: list[str] = field(default_factory=list)
    coefficients: np.ndarray | None = None
    intercept: float = 0.0
    r2_ajuste: float = float("nan")
    historique: list[tuple[str, float]] = field(default_factory=list)

    def predire(self, X: pd.DataFrame) -> np.ndarray:
        if self.coefficients is None:
            raise RuntimeError("Modèle non ajusté")
        return X[self.variables].to_numpy() @ self.coefficients + self.intercept


def _r2_ajuste(y: np.ndarray, prediction: np.ndarray, n_variables: int) -> float:
    n = len(y)
    if n - n_variables - 1 <= 0:
        return -np.inf
    residuel = float(((y - prediction) ** 2).sum())
    total = float(((y - y.mean()) ** 2).sum())
    if total == 0:
        return -np.inf
    return 1 - (residuel / (n - n_variables - 1)) / (total / (n - 1))


def ajuster(
    X: pd.DataFrame,
    y: np.ndarray,
    max_variables: int = 5,
    gain_min: float = 0.01,
    respecter_signes: bool = True,
) -> ModeleLUR:
    """Sélection ascendante sous contrainte de signe et d'unicité par famille."""
    y = np.asarray(y, dtype="float64")
    retenues: list[str] = []
    familles_prises: set[str] = set()
    historique: list[tuple[str, float]] = []
    meilleur_score = -np.inf
    modele = ModeleLUR()

    candidates_initiales = [c for c in X.columns if X[c].std() > 0]

    while len(retenues) < max_variables:
        meilleure, meilleur_gain, ajustement = None, gain_min, None

        for colonne in candidates_initiales:
            if colonne in retenues or famille(colonne) in familles_prises:
                continue

            essai = retenues + [colonne]
            regression = LinearRegression().fit(X[essai], y)
            score = _r2_ajuste(y, regression.predict(X[essai]), len(essai))

            if respecter_signes:
                attendu = signe_attendu(colonne)
                obtenu = np.sign(regression.coef_[-1])
                # Un coefficient contraire au mécanisme physique disqualifie la
                # variable, même si elle améliore le score.
                if attendu != 0 and obtenu != attendu:
                    continue

            gain = score - meilleur_score
            if gain > meilleur_gain:
                meilleure, meilleur_gain, ajustement = colonne, gain, (regression, score)

        if meilleure is None:
            break

        regression, score = ajustement
        retenues.append(meilleure)
        familles_prises.add(famille(meilleure))
        historique.append((meilleure, score))
        meilleur_score = score
        modele = ModeleLUR(
            variables=list(retenues),
            coefficients=regression.coef_.copy(),
            intercept=float(regression.intercept_),
            r2_ajuste=score,
            historique=list(historique),
        )

    return modele


def valider_station_exclue(
    X: pd.DataFrame,
    y: np.ndarray,
    stations: pd.Series,
    **kwargs,
) -> pd.DataFrame:
    """Validation *leave-one-station-out*.

    **La sélection de variables est refaite à chaque pli.** La conserver d'un pli à
    l'autre laisserait fuiter la station exclue dans le choix des variables, ce qui
    est la forme la plus courante — et la plus invisible — de fuite en LUR.
    """
    y = np.asarray(y, dtype="float64")
    stations = pd.Series(stations).reset_index(drop=True)
    X = X.reset_index(drop=True)

    lignes = []
    for station in stations.unique():
        test = (stations == station).to_numpy()
        if test.all():
            continue
        modele = ajuster(X[~test], y[~test], **kwargs)
        if not modele.variables:
            prediction = np.full(int(test.sum()), y[~test].mean())
        else:
            prediction = modele.predire(X[test])
        for observe, predit in zip(y[test], prediction):
            lignes.append(
                {
                    "station_id": station,
                    "observe": float(observe),
                    "predit": float(predit),
                    "n_variables": len(modele.variables),
                }
            )
    return pd.DataFrame(lignes)


def metriques(observe, predit) -> dict[str, float]:
    """RMSE, MAE, biais et R² — plus la comparaison à la baseline de la moyenne.

    Le R² se calcule contre la moyenne des OBSERVATIONS, ce qui le rend négatif
    quand le modèle fait pire que de prédire la moyenne partout. C'est le seul
    repère honnête : sur 23 stations, un R² de 0,3 peut n'être que du bruit.
    """
    observe = np.asarray(observe, dtype="float64")
    predit = np.asarray(predit, dtype="float64")
    residus = observe - predit
    total = float(((observe - observe.mean()) ** 2).sum())
    return {
        "n": len(observe),
        "rmse": float(np.sqrt((residus**2).mean())),
        "mae": float(np.abs(residus).mean()),
        "biais": float(residus.mean()),
        "r2": float(1 - (residus**2).sum() / total) if total > 0 else float("nan"),
        "rmse_baseline_moyenne": float(np.sqrt(((observe - observe.mean()) ** 2).mean())),
    }
