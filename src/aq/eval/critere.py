"""Le critère de rétention d'une piste — relatif, jamais absolu.

Le défaut que ce module existe pour supprimer
---------------------------------------------
Le projet a longtemps retenu une piste si elle gagnait **0,3 µg/m³**, valeur écrite en dur
dans huit scripts. Ce seuil est en unités absolues, appliqué à des polluants dont le RMSE de
base varie d'un facteur cinq :

===========  =============  ==============================
polluant     RMSE de base   ce que 0,3 µg/m³ représente
===========  =============  ==============================
NO₂          14,4           **2,1 %**
O₃           8,0            3,8 %
PM2,5        2,7            **11,0 %**
===========  =============  ==============================

Franchir le critère sur les PM2,5 demanderait un gain plus grand que **n'importe quel levier
jamais mesuré dans ce projet** — l'observation de la veille, le meilleur de tous, en rend
8,5 %. Le seuil y était donc inatteignable par construction, et complaisant sur le NO₂.

Ce n'est pas un arbitrage scientifique, c'est un artefact d'unité. `VERITE_DOSSIER.md` § 6 le
consignait déjà ; il a continué d'écarter des pistes pendant ce temps, faute d'être corrigé
**dans le code**. Consigner un défaut ne le corrige pas.

Pourquoi 2 %, et pas une autre valeur
-------------------------------------
Le seuil doit être **au-dessus de ce que la mesure sait résoudre**, sinon il retient du bruit ;
et aussi bas que possible au-dessus, sinon il écarte du signal. La demi-largeur des IC95 par
bootstrap de stations, mesurée sur les trois polluants et plusieurs familles de variables,
vaut de façon remarquablement stable **1,0 à 1,5 %** du RMSE de base :

===========  =========================  ====================
polluant     IC95 typique (météo IFS)   demi-largeur / base
===========  =========================  ====================
O₃           [+0,325 ; +0,547]          1,4 %
NO₂          [+0,148 ; +0,430]          1,0 %
PM2,5        [+0,063 ; +0,135]          1,3 %
===========  =========================  ====================

**2 %** se situe donc juste au-dessus du pouvoir de résolution, à la même distance pour les
trois polluants — ce que l'ancien seuil ne faisait pour aucun. Sur l'ozone il vaut 0,16 µg/m³,
soit environ la moitié de l'ancien : le critère devient plus exigeant là où il était laxiste
en relatif, et plus atteignable là où il était impossible.

Ce que le critère ne dit pas
----------------------------
Un gain sous le seuil n'est pas *nul* : il est **sous le seuil de rétention**. Et un gain qui
échoue en RMSE peut réussir en **détection** — la météo prévue IFS gagne +3,5 % de RMSE sur
l'ozone, sous l'ancien seuil absolu, tout en dépassant la réanalyse en CSI. Pour un produit
dont l'usage est le franchissement d'un seuil, c'est la détection qui tranche. Ce module donne
un critère, pas un verdict.
"""

from __future__ import annotations

from dataclasses import dataclass

# Part du RMSE de base à partir de laquelle un gain est retenu. Voir la justification
# ci-dessus : au-dessus du pouvoir de résolution du bootstrap, et à la même distance pour
# tous les polluants.
PART_RETENTION = 0.02

# Ce que l'on tolère de dégradation sur le décile haut avant d'écarter, en part du RMSE du
# décile haut. Un gain moyen payé par la queue ne sert pas un service d'alerte.
PART_QUEUE = 0.02


@dataclass(frozen=True)
class Verdict:
    """Le résultat d'un criblage, avec de quoi le contester."""

    retenu: bool
    seuil: float
    motif: str

    def __str__(self) -> str:
        return f"{'RETENU' if self.retenu else 'écarté'} — {self.motif}"


def seuil(rmse_base: float, part: float = PART_RETENTION) -> float:
    """Le seuil de rétention, en µg/m³, pour une grandeur de RMSE ``rmse_base``."""
    if not rmse_base > 0:
        raise ValueError(f"rmse_base doit être strictement positif, reçu {rmse_base!r}")
    return part * rmse_base


def cribler(rmse_base: float, gain: float, ic_bas: float,
            gain_queue: float | None = None,
            rmse_queue_base: float | None = None,
            ic_haut: float | None = None) -> Verdict:
    """Retient une piste si elle est **significative** et **assez grande**, sans coût de queue.

    Trois conditions, dans cet ordre — la première qui échoue nomme le motif :

    1. ``ic_bas > 0`` — l'intervalle exclut zéro. Un gain non significatif n'est pas un gain.
    2. ``gain >= seuil(rmse_base)`` — assez grand pour valoir la complexité ajoutée.
    3. la queue ne se dégrade pas au-delà de ``PART_QUEUE`` du RMSE du décile haut.

    ``gain_queue`` est **positif quand la queue s'améliore**, comme le gain principal.
    """
    s = seuil(rmse_base)
    if not ic_bas > 0:
        # ⚠️ Distinguer « non significatif » de « significativement PIRE ». L'ancien
        # message annonçait « IC95 contenant zéro » dans les deux cas — donc une
        # dégradation franche, intervalle entièrement négatif, était rapportée comme une
        # absence d'effet. C'est précisément le genre de silence que ce projet traque :
        # le criblage écartait la piste, mais le journal cachait qu'elle NUISAIT.
        if gain < 0 and ic_haut is not None and ic_haut < 0:
            return Verdict(False, s, f"DÉGRADATION significative : {gain:+.3f} µg/m³, "
                                     f"IC95 entièrement négatif")
        return Verdict(False, s, f"IC95 contenant zéro (borne basse {ic_bas:+.3f})")
    if gain < s:
        return Verdict(False, s, f"gain {gain:+.3f} sous le seuil de {s:.3f} µg/m³ "
                                 f"({100 * gain / rmse_base:+.1f} % contre "
                                 f"{100 * PART_RETENTION:.0f} % exigés)")
    if gain_queue is not None and rmse_queue_base is not None:
        cout = -gain_queue
        if cout > PART_QUEUE * rmse_queue_base:
            return Verdict(False, s, f"queue dégradée de {cout:+.3f} µg/m³, au-delà des "
                                     f"{PART_QUEUE * rmse_queue_base:.3f} tolérés")
    return Verdict(True, s, f"gain {gain:+.3f} µg/m³ ({100 * gain / rmse_base:+.1f} %), "
                            f"IC95 strictement positif")
