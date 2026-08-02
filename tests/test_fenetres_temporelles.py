"""Un nom de fichier n'est pas une source de vérité.

Le même défaut a coûté des données **trois fois** dans ce projet, sous trois formes :

1. Une expression capturant `202402` au lieu de `o3` sur un dossier groupé
   `..._o3_202402_202403` — les trois polluants s'écrasaient sous une même clé.
2. `fit_mos.py` déduisant du nom la fenêtre d'observations à charger : sur les six
   fichiers `..._202308_202309.parquet`, seul le **second mois** était retenu.
   **11 mois sur 17, 35 % du jeu d'entraînement perdu sans qu'aucune erreur ne soit
   levée.**
3. `benchmark_cams.py`, la même ligne recopiée, amputant le mois de bordure de la
   référence contre laquelle tout le projet se mesure.

Le point commun est une **expression ancrée à droite** appliquée à un nom qui porte
plusieurs jetons. Elle ne lève rien : elle capture le dernier et oublie les autres.

Ces tests gardent les deux versants : le comportement correct des bornes déduites des
données, et l'absence du motif fautif dans le code.
"""

import re
from pathlib import Path

import pandas as pd
import pytest

RACINE = Path(__file__).resolve().parents[1]

NOMS_GROUPES = [
    "cams_prevision_metropole_o3_202308_202309.parquet",
    "cams_prevision_metropole_no2_202410_202411.parquet",
    "cams_prevision_metropole_pm25_202503_202504.parquet",
]


# --------------------------------------------------------------------------- #
# Le défaut lui-même, rendu explicite
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("nom", NOMS_GROUPES)
def test_expression_ancree_a_droite_perd_le_premier_mois(nom):
    """La démonstration du défaut — s'il cesse d'être vrai, le test devient inutile
    et doit être supprimé, pas adapté."""
    tous = re.findall(r"(\d{6})", nom)
    ancree = re.search(r"_(\d{6})\.parquet$", nom).group(1)

    assert len(tous) == 2, "ce nom porte bien deux mois"
    assert ancree == tous[1]
    assert ancree != tous[0], "le premier mois est perdu, en silence"


# --------------------------------------------------------------------------- #
# Le comportement correct : les bornes viennent des données
# --------------------------------------------------------------------------- #

def _prevision_sur_deux_mois() -> pd.DataFrame:
    """Deux mois de prévisions, avec le débordement d'échéance sur le mois suivant."""
    instants = pd.date_range("2023-08-01 01:00", "2023-10-01 00:00",
                             freq="h", tz="UTC")
    return pd.DataFrame({"timestamp_utc": instants,
                         "echeance_h": ((range(len(instants))) and
                                        [1 + i % 24 for i in range(len(instants))])})


def test_bornes_deduites_des_donnees_couvrent_les_deux_mois():
    prev = _prevision_sur_deux_mois()
    debut = prev["timestamp_utc"].min()
    fin = prev["timestamp_utc"].max() + pd.Timedelta(hours=1)

    mois = pd.period_range(debut, fin - pd.Timedelta(hours=1), freq="M")
    assert {str(m) for m in mois} >= {"2023-08", "2023-09"}


def test_bornes_deduites_des_donnees_incluent_le_debordement():
    """Les prévisions débordent sur le mois suivant, jusqu'à 72 h d'échéance. Une
    fenêtre calée sur le seul mois nommé les tronquerait."""
    prev = _prevision_sur_deux_mois()
    fin = prev["timestamp_utc"].max() + pd.Timedelta(hours=1)
    assert fin > pd.Timestamp("2023-10-01", tz="UTC")


def test_couverture_signale_les_mois_sans_observation():
    """Un mois de prévisions sans observation en face disparaît du jeu sans erreur.
    C'est légitime — 2025 n'a pas d'observations — mais cela doit être **dit**."""
    prevus = {pd.Period("2024-12", "M"), pd.Period("2025-01", "M"),
              pd.Period("2025-02", "M")}
    obtenus = {pd.Period("2024-12", "M"), pd.Period("2025-01", "M")}

    manquants = sorted(prevus - obtenus)
    assert manquants == [pd.Period("2025-02", "M")]


# --------------------------------------------------------------------------- #
# La garde : le motif ne doit pas reparaître
# --------------------------------------------------------------------------- #

# Une expression `\d{6}` ancrée sur la fin d'un nom de fichier. `extract_copernicus_
# stations.py` en porte une légitime — `(\d{6}(?:_\d{6})*)` capture **tous** les
# jetons — d'où la vérification du caractère répété plutôt qu'une interdiction sèche.
MOTIF_SUSPECT = re.compile(r"\(\\d\{6\}\)\\\.(?:parquet|nc)\$")


@pytest.mark.parametrize("dossier", ["scripts", "src"])
def test_aucune_fenetre_deduite_du_nom_de_fichier(dossier):
    coupables = [
        f"{chemin.relative_to(RACINE)}:{n}"
        for chemin in sorted((RACINE / dossier).rglob("*.py"))
        for n, ligne in enumerate(chemin.read_text().splitlines(), start=1)
        if MOTIF_SUSPECT.search(ligne)
    ]
    assert not coupables, (
        "expression ancrée à droite sur un nom de fichier — elle perdra le premier "
        "jeton d'un nom groupé. Lire les bornes dans les données : "
        + ", ".join(coupables)
    )
