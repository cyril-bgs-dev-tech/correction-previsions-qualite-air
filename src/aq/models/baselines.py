"""Baselines de prévision — la barre que tout modèle doit franchir.

Un modèle de qualité de l'air ne se juge pas contre zéro. Les concentrations sont
fortement autocorrélées : la persistance seule (« demain comme aujourd'hui ») atteint
des scores élevés, et un modèle sophistiqué qui ne la bat pas ne sert à rien.

Trois références, de la plus naïve à la plus exigeante :

1. **Persistance** — la dernière valeur observée. Redoutable à court terme, elle
   s'effondre aux horizons longs et rate systématiquement les retournements, donc
   les débuts d'épisode, qui sont précisément ce qui compte.
2. **Climatologie horaire** — la moyenne historique pour cette station, ce mois et
   cette heure locale. Capture le cycle diurne et la saisonnalité, ignore la météo
   du jour. Ne s'effondre pas avec l'horizon.
3. **CAMS brut** — la vraie référence métier, à ajouter dès que l'accès existe.

**Anti-fuite :** la climatologie s'estime sur la période d'APPRENTISSAGE seule. La
calculer sur l'ensemble des données ferait entrer de l'information future dans une
prévision — erreur classique, invisible dans les métriques, et qui flatte le score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FUSEAU_LOCAL = "Europe/Paris"


def _cles_temporelles(horodatages: pd.Series) -> pd.DataFrame:
    """Mois et heure LOCALE — le cycle diurne suit l'heure sociale, pas UTC."""
    local = horodatages.dt.tz_convert(FUSEAU_LOCAL)
    return pd.DataFrame(
        {"mois": local.dt.month, "heure_locale": local.dt.hour},
        index=horodatages.index,
    )


def persistance(panneau: pd.DataFrame, horizon_h: int = 24) -> pd.DataFrame:
    """Prévision = valeur observée `horizon_h` heures plus tôt.

    Le décalage se fait sur une grille horaire **continue**, non sur les lignes : sur
    un index troué, décaler de 24 positions ne remonte pas de 24 heures, et le
    baseline paraîtrait meilleur qu'il n'est.
    """
    out = panneau.sort_values(["station_id", "polluant", "timestamp_utc"]).copy()
    out["prevision"] = (
        out.groupby(["station_id", "polluant"], observed=True)["valeur"].shift(horizon_h)
    )
    return out


def ajuster_climatologie(panneau_train: pd.DataFrame) -> pd.DataFrame:
    """Moyenne par station, polluant, mois et heure locale — sur le TRAIN seul."""
    df = panneau_train.copy()
    df[["mois", "heure_locale"]] = _cles_temporelles(df["timestamp_utc"])
    return (
        df.groupby(["station_id", "polluant", "mois", "heure_locale"], observed=True)[
            "valeur"
        ]
        .mean()
        .rename("prevision")
        .reset_index()
    )


def appliquer_climatologie(
    panneau: pd.DataFrame, climatologie: pd.DataFrame
) -> pd.DataFrame:
    """Applique une climatologie ajustée à un jeu de test."""
    out = panneau.copy()
    out[["mois", "heure_locale"]] = _cles_temporelles(out["timestamp_utc"])
    return out.merge(
        climatologie, on=["station_id", "polluant", "mois", "heure_locale"], how="left"
    )


def evaluer(observe, prevision, par: pd.Series | None = None) -> pd.DataFrame:
    """Métriques d'erreur, éventuellement ventilées par groupe.

    Les couples dont l'un des deux termes manque sont écartés — et leur nombre est
    rapporté : un baseline qui ne prédit que la moitié des heures n'est pas
    comparable à un modèle qui les prédit toutes.
    """
    cadre = pd.DataFrame({"observe": np.asarray(observe, dtype="float64"),
                          "prevision": np.asarray(prevision, dtype="float64")})
    if par is not None:
        cadre["groupe"] = np.asarray(par)

    def _metriques(bloc: pd.DataFrame) -> pd.Series:
        valide = bloc.dropna(subset=["observe", "prevision"])
        if valide.empty:
            return pd.Series({"n": 0, "rmse": np.nan, "mae": np.nan,
                              "biais": np.nan, "r2": np.nan, "taux_couvert": 0.0})
        residus = valide["observe"] - valide["prevision"]
        total = float(((valide["observe"] - valide["observe"].mean()) ** 2).sum())
        return pd.Series(
            {
                "n": len(valide),
                "rmse": float(np.sqrt((residus**2).mean())),
                "mae": float(residus.abs().mean()),
                "biais": float(residus.mean()),
                "r2": float(1 - (residus**2).sum() / total) if total > 0 else np.nan,
                "taux_couvert": len(valide) / len(bloc),
            }
        )

    if par is None:
        return _metriques(cadre).to_frame().T
    return cadre.groupby("groupe").apply(_metriques, include_groups=False).reset_index()


def scinder_temporellement(
    panneau: pd.DataFrame, date_bascule: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Découpage strictement temporel : apprentissage avant, test après.

    Un découpage aléatoire placerait des heures futures dans l'apprentissage, entre
    deux heures de test séparées de 120 minutes — le modèle interpolerait au lieu de
    prévoir, et le score n'aurait plus aucun rapport avec l'usage opérationnel.
    """
    bascule = pd.Timestamp(date_bascule, tz="UTC")
    return (
        panneau[panneau["timestamp_utc"] < bascule].copy(),
        panneau[panneau["timestamp_utc"] >= bascule].copy(),
    )
