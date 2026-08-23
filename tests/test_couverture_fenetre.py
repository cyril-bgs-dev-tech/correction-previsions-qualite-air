"""Une colonne d'époque sort ; un mois amputé sort — et l'ORDRE décide.

Le défaut, mesuré le 23/08/2026 avant tout lancement
------------------------------------------------------
La première version de cette règle prenait le minimum de couverture sur TOUTES les
colonnes de famille et écartait le mois s'il tombait sous 80 %. Elle aurait vidé le
corpus : `pm2p5_no3_conc` est absent avant 2024-12, son minimum vaut donc zéro sur trente
mois, et la règle censée faire passer la fenêtre de 29 à 36 mois l'aurait ramenée à 21.

**Un garde-fou qui détruit ce qu'il protège est pire que pas de garde-fou.**

La bonne lecture distingue deux objets que le seuil unique confondait :

* une COLONNE absente de mois ENTIERS est elle-même l'indicateur d'époque — « le nitrate
  est vide » vaut « nous sommes avant décembre 2024 ». Elle sort, le mois reste ;
* un MOIS où une colonne conservée n'est qu'à moitié servie est amputé — 2023-08 et ses
  précurseurs à 54 %. Il sort, la colonne reste.

Ces tests figent les deux passes et, surtout, leur ORDRE.
"""

import pandas as pd
import pytest

from methode_maximale import trier_couverture

MOIS = ["2023-08", "2023-09", "2023-12", "2024-06", "2024-12", "2025-06"]


def table(**colonnes):
    return pd.DataFrame(colonnes, index=MOIS)


def test_une_colonne_absente_de_mois_entiers_sort_et_le_mois_reste():
    """Le cas réel du nitrate : vide avant 2024-12, pleine ensuite."""
    couv = table(sia_conc=[1.0] * 6, pm2p5_no3_conc=[0.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    epoque, amputes = trier_couverture(couv, {"spe": ["sia_conc", "pm2p5_no3_conc"]})
    assert epoque == ["pm2p5_no3_conc"]
    assert amputes == [], "les mois doivent SURVIVRE au retrait de la colonne d'époque"


def test_un_mois_amputé_sort_et_la_colonne_reste():
    """Le cas réel de 2023-08 : précurseurs servis à 54 % du mois."""
    couv = table(nh3_conc=[0.54, 1.0, 1.0, 1.0, 1.0, 1.0])
    epoque, amputes = trier_couverture(couv, {"pre": ["nh3_conc"]})
    assert epoque == [] and amputes == ["2023-08"]


def test_l_ORDRE_des_deux_passes_decide():
    """Le défaut du 23/08 : juger les mois AVANT d'avoir retiré la colonne d'époque
    supprime tous les mois où elle manque. Ici, quatre sur six."""
    couv = table(sia_conc=[1.0] * 6, pm2p5_no3_conc=[0.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    _, amputes = trier_couverture(couv, {"spe": ["sia_conc", "pm2p5_no3_conc"]})
    assert amputes == []
    # La passe naïve, pour mémoire : elle aurait rendu quatre mois amputés sur six.
    naif = sorted(m for m in couv.index if couv.loc[m].min() < 0.8)
    assert len(naif) == 4, "le témoin du défaut doit rester visible dans le test"


def test_les_deux_defauts_a_la_fois():
    couv = table(sia_conc=[0.54, 1.0, 1.0, 1.0, 1.0, 1.0],
                 pm2p5_no3_conc=[0.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    epoque, amputes = trier_couverture(couv, {"spe": ["sia_conc", "pm2p5_no3_conc"]})
    assert epoque == ["pm2p5_no3_conc"] and amputes == ["2023-08"]


def test_une_famille_entierement_d_epoque_ne_laisse_aucun_mois_amputé():
    """Si tout sort en passe 1, il ne reste rien à juger — et surtout pas TOUT à jeter."""
    couv = table(a=[0.0, 0.0, 1.0, 1.0, 1.0, 1.0], b=[0.0, 0.0, 1.0, 1.0, 1.0, 1.0])
    epoque, amputes = trier_couverture(couv, {"f": ["a", "b"]})
    assert set(epoque) == {"a", "b"} and amputes == []


def test_une_couverture_pleine_ne_retire_rien():
    couv = table(a=[1.0] * 6, b=[0.95] * 6)
    assert trier_couverture(couv, {"f": ["a", "b"]}) == ([], [])


def test_une_colonne_absente_de_la_table_est_ignoree_sans_lever():
    couv = table(a=[1.0] * 6)
    epoque, amputes = trier_couverture(couv, {"f": ["a", "jamais_jointe"]})
    assert epoque == [] and amputes == []


def test_le_seuil_de_colonne_distingue_le_vide_du_tres_creux():
    """3 % de couverture — les membres en 2023-11 — n'est PAS un mois entièrement vide :
    la colonne reste, et c'est le mois qui sort."""
    couv = table(membres=[1.0, 0.03, 1.0, 1.0, 1.0, 1.0])
    epoque, amputes = trier_couverture(couv, {"mem": ["membres"]})
    assert epoque == [] and amputes == ["2023-09"]
