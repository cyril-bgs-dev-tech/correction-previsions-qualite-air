"""La fenêtre « 8 h » se compte en HEURES, jamais en lignes — le test qui le fige.

Le défaut, mesuré le 22/08/2026
--------------------------------
`max_glissant_8h` faisait `rolling(8, min_periods=6)` sur une série non réindexée sur une
grille horaire continue. La grandeur produite n'était donc plus celle du texte réglementaire
— valeur cible européenne de l'ozone, MQI FAIRMODE, sous-indice ATMO — dès qu'une heure
manquait ou qu'une ligne était en double.

Coût mesuré sur l'ozone du corpus : **7,96 % des jours-station** portaient une cible fausse,
écart médian 2,17 µg/m³ sur ces jours et biais moyen +1,99 ; et **98,6 % de 2024-01, 99,9 %
de 2024-02** — les deux mois où le panel portait chaque observation en double, ce qui
resserrait la fenêtre à 4 heures réelles.

Ces tests figent les trois propriétés qui comptent, dans l'ordre où elles ont manqué :
identité sur une grille propre, sensibilité au trou, insensibilité au doublon.
"""

import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from cible_journaliere import max_glissant_8h, moyenne_glissante_8h  # noqa: E402


def _table(heures, valeurs, station="A"):
    return pd.DataFrame({
        "station_id": station,
        "timestamp_utc": pd.to_datetime("2024-06-01") + pd.to_timedelta(heures, "h"),
        "x": np.asarray(valeurs, dtype="float64"),
    })


def test_grille_continue_le_correctif_ne_deplace_rien():
    """Sur 24 heures pleines, la fenêtre temporelle rend EXACTEMENT l'ancienne.

    C'est la propriété qui autorise le correctif : il ne change que ce qui était faux.
    """
    d = _table(range(24), np.arange(24.0))
    attendu = d["x"].rolling(8, min_periods=6).mean()
    obtenu = moyenne_glissante_8h(d, "x")
    pd.testing.assert_series_equal(obtenu, attendu, check_names=False)


def test_un_trou_horaire_change_la_reponse_et_la_nouvelle_est_la_bonne():
    """Six heures présentes, un trou de 5 h, puis la suite : la fenêtre ne doit pas
    enjamber le trou pour aller chercher des valeurs vieilles de treize heures."""
    heures = [0, 1, 2, 3, 4, 5, 11, 12, 13, 14]
    d = _table(heures, [10, 10, 10, 10, 10, 10, 100, 100, 100, 100])
    en_heures = moyenne_glissante_8h(d, "x")
    en_lignes = d["x"].rolling(8, min_periods=6).mean()

    # À l'heure 14, la fenêtre d'horloge couvre (6 h, 14 h] : seules les quatre valeurs à
    # 100 y sont — mais elles sont quatre, donc sous le minimum de six : la moyenne n'est
    # pas définie, et c'est le comportement réglementaire (règle des 75 %).
    assert np.isnan(en_heures.iloc[-1])
    # La version en lignes, elle, moyenne huit LIGNES qui s'étalent sur quinze heures.
    assert not np.isnan(en_lignes.iloc[-1])
    assert en_lignes.iloc[-1] == pytest.approx((10 * 4 + 100 * 4) / 8)


def test_les_doublons_ne_resserrent_plus_la_fenetre():
    """Chaque heure en double — le cas réel de 2024-01/02 — ne doit rien changer.

    En lignes, huit lignes ne couvraient plus que quatre heures : la « moyenne 8 h »
    devenait une moyenne 4 h, systématiquement plus haute sur un profil qui monte.
    """
    simple = _table(range(12), np.arange(12.0))
    double = pd.concat([simple, simple]).sort_values(
        ["station_id", "timestamp_utc"]).reset_index(drop=True)

    ref = moyenne_glissante_8h(simple, "x").iloc[-1]
    avec_doublons = moyenne_glissante_8h(double, "x").iloc[-1]
    assert avec_doublons == pytest.approx(ref)

    en_lignes = double["x"].rolling(8, min_periods=6).mean().iloc[-1]
    assert en_lignes > ref                      # la fenêtre resserrée surestime
    assert en_lignes == pytest.approx(np.mean([8, 9, 10, 11]))


def test_deux_stations_ne_se_contaminent_pas():
    a = _table(range(12), np.zeros(12), station="A")
    b = _table(range(12), np.full(12, 100.0), station="B")
    d = pd.concat([a, b]).sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)
    r = moyenne_glissante_8h(d, "x")
    assert r[d["station_id"] == "A"].dropna().eq(0.0).all()
    assert r[d["station_id"] == "B"].dropna().eq(100.0).all()


def test_une_table_non_triee_leve_au_lieu_de_decaler():
    """Un garde-fou non testé est une croyance (§ 1 quater) : celui-ci l'est."""
    d = _table(range(12), np.arange(12.0)).sample(frac=1.0, random_state=0)
    with pytest.raises(SystemExit, match="ordre du glissement"):
        moyenne_glissante_8h(d, "x")


def test_l_ancienne_fonction_leve_au_lieu_de_retomber_en_silence():
    with pytest.raises(SystemExit, match="8 lignes, pas 8 heures"):
        max_glissant_8h(pd.Series([1.0, 2.0, 3.0]))
