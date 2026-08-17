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


@dataclass(frozen=True)
class VerdictMecanisme:
    """Un mécanisme tient-il ailleurs que là où on l'a vu ?"""

    tient: bool
    motif: str
    par_groupe: dict

    def __str__(self) -> str:
        return f"{'TIENT' if self.tient else 'NON ÉTABLI'} — {self.motif}"


def tient_sur_sous_ensembles(valeurs_par_groupe: dict, alpha: float = 0.05,
                             minimum: int = 2) -> VerdictMecanisme:
    """Un effet n'est un **mécanisme** que s'il tient sur ``minimum`` groupes INDÉPENDANTS.

    Le défaut que cette fonction existe pour supprimer
    --------------------------------------------------
    Le 15/08, j'ai lu trois plis de NO₂, vu le gain du réglage croître avec la part de
    stations trafic, et écrit que le motif était « confirmé sur le tiers de test ». Deux
    contrôles l'ont réfuté le lendemain : à niveau de pollution comparable l'effet trafic
    tombe à p = 0,42, et sur les quatre polluants le sens **s'inverse** — NO₂ décroche en
    bas de gamme, PM10 en haut, O₃ et PM2,5 sont plats. Trois plis ne font pas une loi, et
    un polluant ne fait pas un mécanisme.

    Ce que la fonction teste, et pourquoi c'est un test de SIGNE
    ------------------------------------------------------------
    Pour chaque groupe : l'effet est-il discernable d'un pile ou face ? On ne suppose ni
    normalité ni variance commune — sur des gains par station, les deux sont fausses. Le
    mécanisme « tient » si **au moins ``minimum`` groupes sont individuellement
    significatifs ET portent le même signe**. Un groupe significatif dans l'autre sens
    n'est pas un silence : il **réfute**, et le motif le nomme.

    ``valeurs_par_groupe`` : ``{nom_du_groupe: séquence de valeurs signées}`` — un gain par
    station, par pli, par mois. Les groupes doivent être **disjoints** ; c'est à l'appelant
    de le garantir, aucune fonction ne peut le vérifier à sa place.
    """
    from scipy import stats  # local : ce module est importé par des scripts sans scipy

    detail = {}
    for nom, v in valeurs_par_groupe.items():
        vals = [x for x in v if x == x]  # écarte les NaN, sans dépendre de numpy
        n = len(vals)
        if n < 6:
            # Sous six points, le test de signe ne peut pas descendre sous 0,05 même
            # parfait (2⁻⁶ = 0,031 bilatéral ≈ 0,03) : annoncer « non significatif » y
            # serait un artefact de taille, pas un résultat.
            detail[nom] = {"n": n, "part_positive": None, "p": None, "verdict": "trop peu"}
            continue
        k = sum(1 for x in vals if x > 0)
        p = stats.binomtest(k, n, 0.5).pvalue
        sens = 0 if p > alpha else (1 if k > n / 2 else -1)
        detail[nom] = {"n": n, "part_positive": k / n, "p": p,
                       "verdict": {0: "hasard", 1: "positif", -1: "négatif"}[sens]}

    positifs = [g for g, d in detail.items() if d["verdict"] == "positif"]
    negatifs = [g for g, d in detail.items() if d["verdict"] == "négatif"]
    if positifs and negatifs:
        return VerdictMecanisme(
            False, f"RÉFUTÉ — sens opposés : {', '.join(positifs)} positifs contre "
                   f"{', '.join(negatifs)} négatifs. Ce n'est pas un mécanisme unique.",
            detail)
    porteurs = positifs or negatifs
    if len(porteurs) >= minimum:
        return VerdictMecanisme(
            True, f"tient sur {len(porteurs)} groupes ({', '.join(porteurs)}) "
                  f"sur {len(detail)}, même sens", detail)
    return VerdictMecanisme(
        False, f"{len(porteurs)} groupe(s) significatif(s) sur {len(detail)}, il en faut "
               f"{minimum}. Un effet vu une fois n'est pas publiable.", detail)


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


# ─────────────────────────────────────────────────────────────────────────────────────────
# Règle L — une statistique ajustée sur un pli doit être DÉFINIE sur l'autre
# ─────────────────────────────────────────────────────────────────────────────────────────

def exiger_couverture_de_reference(cle_reference, cle_bloc, bloc: str,
                                   part_max: float = 0.5) -> float:
    """Refuse une transformation dont le bloc visé n'est pas couvert par sa référence.

    Le défaut qu'elle attrape, mesuré le 17/08/2026
    ------------------------------------------------
    Une climatologie station × mois ajustée sur le **pli d'apprentissage** a été appliquée au
    pli de test. Mais le protocole du dossier cache la station *et* le mois : **les stations
    de test sont absentes de l'apprentissage par construction**. Leur climatologie n'existait
    donc pas, chaque ligne repliait sur la moyenne globale, et le modèle apprenait sur des
    anomalies centrées pour prédire sur des valeurs brutes décalées d'une constante.

    **Deux échelles de part et d'autre du modèle, et rien ne lève** : le résultat est un
    nombre plausible. C'est § 2 quater (compter le repli) appliqué non plus au périmètre des
    lignes mais à l'**échelle des variables**.

    La règle générale : quand un protocole cache une dimension, toute statistique ajustée le
    long de cette dimension est introuvable de l'autre côté. La référence doit venir d'un
    découpage qui **croise** la dimension cachée, jamais du pli lui-même.

    Paramètres
    ----------
    cle_reference : les clés couvertes par la référence (index, Series ou itérable)
    cle_bloc      : les clés du bloc à transformer, une par ligne
    bloc          : son nom, pour que le message dise LEQUEL a manqué
    part_max      : part de repli au-delà de laquelle on refuse

    Retourne la part effectivement repliée — à journaliser même quand elle passe.
    """
    connues = set(cle_reference)
    manquantes = [k for k in cle_bloc if k not in connues]
    part = len(manquantes) / max(len(list(cle_bloc)), 1) if not hasattr(cle_bloc, "__len__") \
        else len(manquantes) / max(len(cle_bloc), 1)
    if part > part_max:
        exemples = ", ".join(str(k) for k in manquantes[:3])
        raise ValueError(
            f"{100 * part:.0f} % du bloc « {bloc} » est absent de la référence "
            f"(ex. {exemples}) : la statistique ajustée n'y est pas définie et repliera. "
            f"Les deux blocs seraient alors sur des échelles différentes, sans qu'aucune "
            f"exception ne le dise. Élargir la référence à une partition qui CROISE la "
            f"dimension cachée par le protocole.")
    return part
