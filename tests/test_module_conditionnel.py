#!/usr/bin/env python3
"""`joindre_module` — le chemin qui a produit la confirmation IFS, donc à ne pas casser.

Le 24/08, le bloc IFS de `methode_maximale.py` a été généralisé pour porter aussi la chimie.
Ce refactor touche exactement le code qui a rendu « IFS +0,75 à +1,22 pt sur les quatre » :
une régression y serait invisible — la pile tournerait, écrirait son CSV et rendrait 0.

Les cinq contrôles portent sur ce qu'un module DOIT faire, et les deux derniers sur ce qu'il
doit REFUSER de faire. Un module sans support n'est pas un module vide : c'est une erreur.
"""
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))


def _faux_lot(lot, doubler=False):
    j = pd.date_range("2024-01-01", periods=90, freq="D")
    t = pd.DataFrame({"station_id": "A", "jour": j,
                      f"{lot}_x_mean": np.arange(90.0), f"{lot}_y_mean": np.arange(90.0),
                      f"{lot}_x_max": np.arange(90.0)})
    t.loc[t["jour"] < "2024-02-01", [f"{lot}_x_mean", f"{lot}_y_mean"]] = np.nan
    if doubler:
        t = pd.concat([t, t], ignore_index=True)
    return t, [f"{lot}_x_mean", f"{lot}_y_mean"], [f"{lot}_x_max"]


def _installer(doubler=False):
    m = types.ModuleType("apport_precurseurs")
    m.charger_lot = lambda lot: _faux_lot(lot, doubler)
    sys.modules["apport_precurseurs"] = m


def _jeu():
    d = pd.DataFrame({"station_id": "A",
                      "jour": pd.date_range("2024-01-01", periods=90, freq="D")})
    d["mois"] = d["jour"].dt.strftime("%Y-%m")
    return d


def test_module_restreint_la_fenetre_a_son_support():
    _installer()
    import methode_maximale as mm
    fam = {}
    d, mois = mm.joindre_module(_jeu(), fam, ["2024-01", "2024-02", "2024-03"], "chimie")
    assert mois == ["2024-02", "2024-03"], mois
    assert fam["chimie"] == ["chimie_x_mean", "chimie_y_mean"], fam["chimie"]
    assert "chimie_x_max" not in d.columns, "les maxima ne doivent pas être joints"
    # Février 2024 compte 29 jours (bissextile) et mars 30 dans cette fenêtre de 90 jours.
    assert len(d) == 59, len(d)
    assert d["chimie_x_mean"].notna().all(), "aucune ligne conservée ne doit être vide"


def test_support_vide_leve_au_lieu_de_rendre_une_pile_vide():
    _installer()
    import methode_maximale as mm
    try:
        mm.joindre_module(_jeu(), {}, ["2023-12"], "chimie")
    except SystemExit as e:
        assert "aucun mois commun" in str(e), str(e)
    else:
        raise AssertionError("un module sans support doit LEVER")


def test_cle_non_unique_leve_en_la_nommant():
    _installer(doubler=True)
    import methode_maximale as mm
    try:
        mm.joindre_module(_jeu(), {}, ["2024-01", "2024-02", "2024-03"], "chimie")
    except SystemExit as e:
        assert "n'est pas unique" in str(e), str(e)
    else:
        raise AssertionError("une clé (station, jour) dupliquée doit LEVER")


if __name__ == "__main__":
    for nom, fn in sorted(globals().items()):
        if nom.startswith("test_"):
            fn()
            print(f"  ✅ {nom}")
    print("TOUT PASSE ✅")
