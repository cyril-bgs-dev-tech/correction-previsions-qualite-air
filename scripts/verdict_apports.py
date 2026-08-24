#!/usr/bin/env python3
"""Le verdict d'un apport — un polluant ne fait pas un mécanisme.

Ce script ne mesure rien : il **juge** ce que `apport_ratios_echelle.py` et
`apport_leviers_gratuits.py` ont écrit pli par pli. La question qu'il pose est celle de la
règle 0-E : *l'effet tient-il sur au moins deux sous-ensembles indépendants ?*

Les quatre polluants sont les groupes. Pour chacun, la série jugée est l'écart **apparié**
pli à pli entre la configuration candidate et la base — appariée parce que les deux
configurations partagent exactement les mêmes lignes, la même graine et le même découpage,
donc le déplacement commun causé par une partition se soustrait.

Le test est un **bootstrap par blocs** sur ces écarts : ni normalité ni variance commune
ne sont supposées, et il lit l'AMPLITUDE que le test de signe jetait. Un polluant
significatif dans l'autre sens ne se tait pas — il réfute, et le verdict le nomme.

🔴 Deux corrections du 23/08/2026 — elles ont fait basculer deux verdicts déjà rendus
--------------------------------------------------------------------------------------
**① Les plis ne sont pas des réplications indépendantes.** Deux plis voisins partagent
~93 % de leur bloc d'apprentissage, et le test de signe sur les plis bruts les traite
comme indépendants : ses `p` sont donc optimistes, d'un facteur qui n'est PAS constant —
mesuré ici, la forme du profil passe de 3,1·10⁻⁴ à 3,9·10⁻² sur le NO₂, et de 1,9·10⁻⁶ à
6,3·10⁻³ sur l'ozone. Aucune correction de variance à facteur fixe ne peut réparer cela.

On agrège donc par **blocs de trois mois consécutifs non chevauchants**, et l'argument
est structurel, pas confortable : le protocole fait tourner les groupes de stations sur
les mois consécutifs (`groupes[i % 3]`), donc **un bloc de trois mois voit les trois
groupes**. C'est l'unité de réplication du plan, et elle n'est pas choisie après lecture
des scores. Deux et quatre mois l'encadrent en sensibilité.

**② « Tenir sur deux polluants » n'était pas testé, il était compté.** Compter deux
`p < 0,05` n'est pas un test de l'assertion globale « l'effet est présent dans au moins
deux groupes ». Le test de **conjonction partielle** de Benjamini & Heller (2008) l'est,
et sa forme de Bonferroni — `p_PC = (n − r + 1) × p_(r)` — reste valide sous dépendance
arbitraire entre polluants, ce qui est exactement notre cas.

Ce que ces deux corrections ont coûté, appliquées aux verdicts de la nuit du 22 au 23 :
la **climatologie du point** passe de TIENT à non confirmé (`p_PC = 0,116`), et les
**précurseurs en moyennes seules** aussi (`p_PC = 0,065`). Les familles réellement
promues dans la pile — forme du profil, harmoniques, précurseurs en moyennes ET maxima —
survivent au test strict.

Usage : python3 scripts/verdict_apports.py --prefixe apport_ratios_echelle --axe double
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))


POLLUANTS = ("NO2", "O3", "PM10", "PM25")


def blocs_de(valeurs: list[float], longueur: int) -> list[float]:
    """Moyennes de blocs consécutifs NON chevauchants — l'unité de réplication du plan."""
    v = np.asarray([x for x in valeurs if x == x], dtype="float64")
    n = len(v) // longueur * longueur
    return list(v[:n].reshape(-1, longueur).mean(axis=1)) if n else []


def bootstrap_blocs(valeurs: list[float], longueur: int, tirages: int = 9999,
                    graine: int = 20260823) -> tuple[float, float, float, float]:
    """Bootstrap par blocs sur l'écart apparié — l'instrument de décision.

    🔴 Pourquoi il remplace le test de signe, et le chiffre qui l'impose
    ---------------------------------------------------------------------
    Un test de signe **jette l'amplitude** : il ne retient que le sens de chaque bloc.
    C'est ce qui le rend robuste, et c'est ce qui lui coûte sa puissance. Mesuré par
    `scripts/puissance_blocs.py`, au seuil effectif qu'impose la conjonction partielle sur
    quatre polluants (p ≤ 0,0167) :

        12 blocs → il faut 11 blocs positifs sur 12 · puissance à q=0,85 : **44 %**
        10 blocs → il faut 10 sur 10           · puissance à q=0,85 : **20 %**
        sous 7 blocs → aucun verdict possible, quel que soit l'effet

    Autrement dit, le test de signe **manquait un effet réel plus d'une fois sur deux**, et
    ses « non confirmés » ne valaient pas réfutation. Atteindre 80 % de puissance aurait
    demandé vingt blocs, soit soixante mois de corpus ; nous en avons trente-sept.

    Le bootstrap garde les magnitudes tout en respectant la dépendance : il rééchantillonne
    des **blocs entiers** de trois mois — l'unité de réplication du plan, puisque la
    rotation des groupes de stations y boucle — et non des plis individuels, dont
    l'apprentissage se recouvre à ~93 %.

    Rend : moyenne, IC95, puis les DEUX `p` unilatéraux — positif et négatif.
    """
    b = np.asarray(blocs_de(valeurs, longueur), dtype="float64")
    if len(b) < 5:
        return (float(np.mean(b)) if len(b) else np.nan), np.nan, np.nan, 1.0, 1.0
    rng = np.random.default_rng(graine)
    idx = rng.integers(0, len(b), size=(tirages, len(b)))
    moyennes = b[idx].mean(axis=1)
    bas, haut = np.percentile(moyennes, [2.5, 97.5])
    # `p` bilatéral du bootstrap, plancher à 2/(B+1) : on ne prétend pas mesurer plus fin
    # que le nombre de tirages ne le permet.
    #
    # 🔴 UNILATÉRAL, et le défaut qui l'impose — trouvé le 23/08 en relisant un verdict
    # ------------------------------------------------------------------------------
    # Avec un `p` BILATÉRAL, un effet fortement NÉGATIF rend un petit `p` et compte donc
    # comme une confirmation dans la conjonction partielle. Mesuré : les 28 ratios
    # d'échelle donnent NO₂ +1,21 % (p=0,0002) et PM10 −0,66 % (p=0,0002), et la
    # configuration ressortait « TIENT sur deux groupes » — de signes opposés.
    #
    # La règle du dépôt dit l'inverse depuis toujours : « un groupe significatif dans
    # l'autre sens n'est pas un silence, il RÉFUTE ». On rend donc les deux `p`
    # unilatéraux : `p_plus` teste un effet positif, `p_moins` un effet négatif. La
    # conjonction se calcule sur `p_plus` ; `p_moins` sert à réfuter.
    plancher = 1.0 / (tirages + 1)
    p_plus = max(plancher, float(np.mean(moyennes <= 0.0)))
    p_moins = max(plancher, float(np.mean(moyennes >= 0.0)))
    return float(np.mean(b)), float(bas), float(haut), float(p_plus), float(p_moins)


def permutation_blocs(valeurs: list[float], longueur: int, tirages: int = 9999,
                      graine: int = 20260823) -> tuple[float, float]:
    """Test de permutation par RETOURNEMENT DE SIGNE des blocs. Rend `(p_plus, p_moins)`.

    Pourquoi il remplace le bootstrap comme porteur du `p` — mesuré le 23/08/2026
    ----------------------------------------------------------------------------
    Le `p` bootstrap est la part de rééchantillons dont la moyenne passe de l'autre côté
    de zéro. Avec 8 à 12 blocs et un effet régulier, **aucun** rééchantillon ne traverse :
    le `p` tombe à son plancher `1/(B+1)` et y reste. Mesuré sur les dix configurations
    criblées, cinq rendaient exactement 0,0003 après conjonction — le bootstrap ne les
    classait plus, il les saturait.

    Sous H₀ « cette configuration n'apporte rien », l'écart d'un bloc est aussi plausible
    en positif qu'en négatif : son signe est **échangeable**. Le test exact consiste donc
    à retourner ces signes au hasard et à regarder où tombe la moyenne observée. Il est
    exact sous cette seule hypothèse, là où le bootstrap est asymptotique — et sur neuf
    blocs, « asymptotique » ne veut pas dire grand-chose.

    ⚠️ Il ne rend PAS d'intervalle : la permutation teste une hypothèse, elle n'estime pas
    une amplitude. L'IC95 reste au bootstrap, qui est bon à cela. Chacun ce qu'il sait
    faire, et le désaccord entre les deux est une information, pas un défaut à cacher.

    ⚠️ Son plancher est `max(1/2ⁿ, 1/(tirages+1))` : sur huit blocs, aucun `p` ne peut
    descendre sous 1/256 = 0,0039, soit 0,0117 après conjonction partielle. Un effet réel
    mais modeste ne PEUT donc pas y être déclaré significatif — c'est une limite du plan,
    pas du test.
    """
    b = np.asarray(blocs_de(valeurs, longueur), dtype=float)
    if len(b) < 2:
        return 1.0, 1.0
    rng = np.random.default_rng(graine)
    tires = rng.choice([-1.0, 1.0], size=(tirages, len(b))) @ b / len(b)
    obs = float(b.mean())
    # `(1 + #{au moins aussi extrême}) / (tirages + 1)` : la forme qui n'atteint jamais
    # zéro, et qui reste valide quand l'observé est lui-même l'un des tirages possibles.
    p_plus = float((1 + np.sum(tires >= obs)) / (tirages + 1))
    p_moins = float((1 + np.sum(tires <= obs)) / (tirages + 1))
    return p_plus, p_moins


def signe(k: int, n: int) -> float:
    """Test de signe bilatéral. Rend 1,0 sous six points : `p` ne peut pas y descendre
    sous 0,05 même parfait, donc annoncer « non significatif » y serait un artefact de
    taille et non un résultat."""
    from scipy import stats  # noqa: PLC0415
    return 1.0 if n < 6 else float(stats.binomtest(k, n, 0.5).pvalue)


def conjonction_partielle(ps: list[float], r: int = 2) -> float:
    """Benjamini & Heller (2008), forme de Bonferroni : `p_PC = (n − r + 1) × p_(r)`.

    Teste l'assertion « l'effet est présent dans au moins `r` groupes » — ce que compter
    des `p < 0,05` ne fait pas. Cette forme reste **valide sous dépendance arbitraire**
    entre les groupes, ce qui est notre cas : les quatre polluants partagent leurs
    stations, leurs jours et leur situation météorologique.
    """
    v = sorted(x for x in ps if x == x)
    if len(v) < r:
        return 1.0
    return min(1.0, (len(v) - r + 1) * v[r - 1])

# 🔴 L'effet UTILE, absent de la décision jusqu'au 24/08/2026 — action P1.7.
#
# Le verdict ne regardait que le `p`. Une famille à +0,05 pt avec p_PC = 0,001 était donc
# déclarée TIENT : statistiquement démontrée, et sans valeur. `fourier` a été promue à
# +0,28 pt sur ce critère.
#
# La décision porte désormais sur TROIS choses — effet, incertitude, utilité — et rend
# trois issues au lieu de deux :
#
#   TIENT    effet ≥ utile sur au moins deux groupes, ET p sous le seuil, ET IC compatible
#   SAUTE    la borne HAUTE est sous l'utile sur tous les groupes : on peut exclure un
#            bénéfice, ce qui est une information, pas un silence
#   RÉSERVE  tout le reste — notamment quatre signes positifs sans résolution suffisante
#
# Le seuil de 0,5 pt n'est pas une constante scientifique : il est aligné sur la résolution
# mesurée (±0,36 à ±0,48). Un seuil de 0,25 serait plus précis que l'instrument.
EFFET_UTILE_PT = 0.5


def rendre_verdict(detail: dict, pcs: dict, signes: dict, alpha: float = 0.05,
                   effet_utile: float = EFFET_UTILE_PT):
    """La décision, isolée de toute entrée-sortie pour être testable.

    `detail` : {polluant: (moy, bas, haut, p_plus, p_moins, k, n_blocs)} au bloc primaire.
    `pcs`    : {longueur_de_bloc: p_conjonction_partielle}.
    `signes` : {longueur_de_bloc: {polluant: signe de l'écart moyen}}.

    Rend `(verdict, porteurs)`.

    🔴 L'ORDRE des trois tests n'est pas cosmétique — c'est le défaut du 23/08/2026.
    La réfutation passe AVANT la conjonction, parce qu'un `p` bilatéral rend un groupe
    fortement négatif indiscernable d'un groupe fortement positif : les 28 ratios
    d'échelle donnaient NO₂ +1,21 % (p=0,0002) et PM10 −0,66 % (p=0,0002), et la
    configuration ressortait « TIENT sur deux groupes ». Deux groupes, oui — de signes
    opposés. La conjonction se calcule donc sur des `p` UNILATÉRAUX, et un groupe
    significatif dans l'autre sens réfute au lieu de se taire.

    Le seuil de réfutation n'est pas corrigé pour la multiplicité, et c'est délibéré :
    avec quatre groupes, la probabilité d'une réfutation à tort avoisine 10 % sous
    l'hypothèse nulle globale — un cas où l'on ne publie pas de toute façon. L'erreur
    penche donc du côté qui coûte le moins : ne pas promouvoir une famille utile est
    réparable par une mesure de plus, publier une famille qui nuit ne l'est pas.
    """
    refute = {p_: d for p_, d in detail.items() if d[4] < alpha}
    porteurs = [p_ for p_, _ in sorted(detail.items(), key=lambda x: x[1][3])[:2]]
    stable = all(len({signes[L][p_] for L in signes}) == 1 for p_ in porteurs)
    if refute:
        noms = ", ".join(f"{p_} ({d[0]:+.2f} %)" for p_, d in sorted(refute.items()))
        return (f"🔴 RÉFUTÉ — effet significativement NÉGATIF sur {noms}. "
                f"Un groupe en sens inverse n'est pas un silence."), porteurs
    # SAUTE — la borne haute exclut un bénéfice utile PARTOUT. C'est une information,
    # pas un silence : on sait que la famille ne paiera pas.
    if all(d[2] < effet_utile for d in detail.values()):
        pire = max(d[2] for d in detail.values())
        return (f"🔴 SAUTE — la borne haute de l'IC95 reste sous {effet_utile} pt sur les "
                f"{len(detail)} groupes (au mieux {pire:+.2f}). Un bénéfice utile est "
                f"EXCLU, pas seulement non démontré."), porteurs
    if pcs[3] >= alpha:
        # 🔴 « Non confirmé » recouvre deux situations que rien ne distinguait, et elles
        # appellent des décisions opposées. Mesuré le 23/08 : la spéciation rend
        # p_PC=0,0648 avec les QUATRE polluants positifs et deux significatifs, tandis que
        # les feux rendent p_PC=1,0 avec trois polluants sur quatre négatifs. Le premier
        # est un défaut de PUISSANCE — le plan a 8 à 9 blocs, la réponse est d'en gagner ;
        # le second est une absence d'effet, et la réponse est de retirer la famille.
        #
        # Le plancher atteignable le dit sans ambiguïté : sur huit blocs, aucun `p_PC` de
        # permutation ne peut descendre sous 0,0117, quel que soit l'effet.
        # 🔴 « Tous positifs » ne suffit pas — corrigé le 24/08/2026 sur un cas réel.
        #
        # La chimie en moyennes et maxima rendait p_PC = 0,86 avec les quatre estimations
        # au-dessus de zéro, dont trois à +0,007, +0,117 et +0,197 pt. Le verdict annonçait
        # « défaut de PUISSANCE, gagner des mois » — ce qui aurait envoyé chercher des mois
        # pour un effet inexistant sur trois polluants. À 0,86, aucun nombre de blocs ne
        # rapproche de 0,05.
        #
        # Un manque de puissance se reconnaît à ce que PLUSIEURS groupes penchent déjà :
        # la conjonction partielle teste « présent dans au moins deux », donc il faut au
        # moins deux `p⁺` qui s'en approchent. Le seuil de 0,25 n'est pas un seuil de
        # décision — c'est la frontière entre « penche » et « ne dit rien ».
        tous_positifs = (all(d[0] > 0 for d in detail.values())
                         and sum(1 for d in detail.values() if d[3] < 0.25) >= 2)
        plancher = min(1.0, (len(detail) - 1) * sorted(
            2.0 ** -max(d[6], 1) for d in detail.values())[1]) if len(detail) >= 2 else 1.0
        if tous_positifs:
            return (f"🟠 NON CONFIRMÉ, mais par PUISSANCE — p_PC={pcs[3]:.4f} et les "
                    f"{len(detail)} groupes vont TOUS dans le même sens. Plancher "
                    f"atteignable à ce nombre de blocs : {plancher:.4f}. Gagner des mois, "
                    f"pas retirer la famille."), porteurs
        return f"🔴 NON CONFIRMÉ — p_PC={pcs[3]:.4f}, il faut < 0,05", porteurs
    if not stable:
        inv = ", ".join(f"{p_} : " + "/".join(f"{signes[L][p_]:+.0f}" for L in sorted(signes))
                        for p_ in porteurs)
        return f"🔴 SIGNE INSTABLE chez un porteur ({inv}) — le découpage décide", porteurs
    # Le `p` est franchi ; reste l'UTILITÉ. Combien de groupes atteignent l'effet utile ?
    utiles = [p_ for p_, d in detail.items() if d[0] >= effet_utile]
    if len(utiles) >= 2:
        return (f"✅ TIENT — p_PC={pcs[3]:.4f}, signe stable chez les porteurs "
                f"({', '.join(porteurs)}), et l'effet dépasse {effet_utile} pt sur "
                f"{len(utiles)} groupe(s) : {', '.join(sorted(utiles))}"), porteurs
    return (f"🟡 RÉSERVE — p_PC={pcs[3]:.4f} franchi, mais l'effet n'atteint "
            f"{effet_utile} pt que sur {len(utiles)} groupe(s)"
            + (f" ({', '.join(sorted(utiles))})" if utiles else "")
            + ". Démontré n'est pas utile."), porteurs


def main(prefixe: str, horizon: int, axe: str) -> int:
    series: dict[str, dict[str, list[float]]] = {}
    libelles: dict[str, str] = {}
    empreintes: dict[str, str] = {}
    for p in POLLUANTS:
        f = RACINE / f"reports/{prefixe}_{p}_h{horizon}_{axe}_par_pli.csv"
        if not f.exists():
            print(f"  ✘ absent : {f.name} — ce polluant ne peut pas voter", flush=True)
            continue
        tp = pd.read_csv(f)
        ref = tp["rmse_config1"].to_numpy()
        for c in [c for c in tp.columns if c.startswith("rmse_config") and c != "rmse_config1"]:
            series.setdefault(c, {})[p] = list(100 * (1 - tp[c].to_numpy() / ref))
        r = RACINE / f"reports/{prefixe}_{p}_h{horizon}_{axe}.csv"
        if r.exists():
            t = pd.read_csv(r)
            # 🔴 Quatre polluants, un seul corpus. Sans ce contrôle, le verdict combine
            # sans broncher trois fichiers régénérés et un qui date d'avant une correction
            # de données — c'est arrivé ce soir, la spéciation ayant été complétée en
            # cours de route.
            empreintes[p] = (str(t["empreinte_corpus"].iloc[0])
                             if "empreinte_corpus" in t.columns else "")
            for k, nom in enumerate(t["configuration"], start=1):
                libelles[f"rmse_config{k}"] = str(nom)
    if not series:
        raise SystemExit(f"aucun fichier « {prefixe}_*_h{horizon}_{axe}_par_pli.csv »")

    connues = {e for e in empreintes.values() if e}
    if len(connues) > 1:
        raise SystemExit(
            "❌ CORPUS DIFFÉRENTS entre polluants : "
            + " · ".join(f"{p_}={e or '—'}" for p_, e in sorted(empreintes.items()))
            + "\n   Un verdict qui combine deux corpus n'est pas un verdict. "
              "Régénérer les apports en retard.")
    if empreintes and not connues:
        print("  ⚠️ aucun fichier ne porte d'empreinte de corpus (antérieurs au 24/08) : "
              "l'identité des entrées n'est PAS vérifiée.", flush=True)
    elif len(empreintes) != len(connues) and connues:
        sans = sorted(p_ for p_, e in empreintes.items() if not e)
        print(f"  ⚠️ empreinte absente pour {', '.join(sans)} — non vérifiés contre "
              f"{connues.pop()}.", flush=True)

    print(f"\n{'═' * 96}")
    print(f"VERDICT · {prefixe} · axe {axe} · bootstrap par blocs de 3 mois · conjonction partielle r=2")
    print(f"{'═' * 96}")
    lignes = []
    for conf, par_polluant in series.items():
        print(f"\n  {libelles.get(conf, conf)}")
        pcs, detail_primaire, controle_signe = {}, {}, {}
        for L in (2, 3, 4):
            ps = {}
            for p, v in par_polluant.items():
                # Le bootstrap porte l'INTERVALLE, la permutation porte le `p`.
                moy, bas, haut, _, _ = bootstrap_blocs(v, L)
                p_plus, p_moins = permutation_blocs(v, L)
                b = blocs_de(v, L)
                k = int(sum(1 for x in b if x > 0))
                ps[p] = (moy, bas, haut, p_plus, p_moins, k, len(b))
            pcs[L] = conjonction_partielle([x[3] for x in ps.values()])
            if L == 3:
                detail_primaire = ps
                # Le test de signe reste calculé, en CONTRÔLE : s'il conclut dans l'autre
                # sens, c'est que l'amplitude est portée par peu de blocs, et ça se dit.
                controle_signe = conjonction_partielle(
                    [signe(k, nb) for _, _, _, _, _, k, nb in ps.values()])
        for p, (moy, bas, haut, p_plus, p_moins, k, n_b) in detail_primaire.items():
            marque = "  🔴 NUIT" if p_moins < 0.05 else ""
            print(f"    {p:5s} {moy:+6.3f} % · IC95 [{bas:+6.3f} ; {haut:+6.3f}] · "
                  f"p⁺={p_plus:.4f} · ({k}/{n_b} blocs positifs){marque}")
            lignes.append({"prefixe": prefixe, "axe": axe,
                           "configuration": libelles.get(conf, conf), "polluant": p,
                           "n_plis": len(par_polluant[p]), "n_blocs_3mois": n_b,
                           "blocs_positifs": k, "ecart_apparie_moyen_pct": moy,
                           "ic95_bas": bas, "ic95_haut": haut,
                           "p_permutation_positif": p_plus,
                           "p_permutation_negatif": p_moins, "p_conjonction_partielle": pcs[3],
                           "p_PC_2mois": pcs[2], "p_PC_4mois": pcs[4],
                           "p_conjonction_test_de_signe": controle_signe})
        # ── Ce que la sensibilité doit vérifier : le SIGNE, pas la significativité ──
        #
        # 🔴 Première version de ce garde, écrite le 23/08 puis corrigée le jour même :
        # elle exigeait `p_PC < 0,05` aux TROIS longueurs. C'est faux, et les données le
        # montrent. Les deux bornes échouent pour des raisons opposées, toutes deux
        # artefactuelles :
        #   · à 2 mois, chaque bloc moyenne moins de plis, donc il est plus bruité ;
        #   · à 4 mois, il ne reste que 8 à 9 blocs, et le p minimal ATTEIGNABLE y vaut
        #     déjà 0,0039 — 0,0117 après conjonction partielle. Un effet réel mais modeste
        #     ne PEUT PAS y être déclaré significatif, quel qu'il soit.
        # Exiger la significativité aux trois longueurs revient donc à exiger qu'un effet
        # survive à deux handicaps que l'analyse de sensibilité fabrique elle-même.
        #
        # Ce qui doit rester stable est le SIGNE de l'écart estimé : s'il s'inverse avec la
        # longueur de bloc, la mesure dépend du découpage et ne dit rien. La décision se
        # prend à la longueur PRIMAIRE, dont l'argument est structurel.
        signes = {L: {p_: np.sign(np.mean(blocs_de(v, L)))
                      for p_, v in par_polluant.items()} for L in (2, 3, 4)}
        sens = " · ".join(f"{L} mois p_PC={v:.4f}" for L, v in pcs.items())
        verdit, porteurs = rendre_verdict(detail_primaire, pcs, signes)
        # Le test de signe en contrôle : quand il diverge, c'est une information sur la
        # FORME de l'effet — quelques blocs qui portent tout, contre un effet diffus.
        if (controle_signe < 0.05) != (pcs[3] < 0.05):
            verdit += (f"\n    ⚠️ le test de signe conclut différemment "
                       f"(p_PC={controle_signe:.4f}) : l'effet est porté par l'amplitude de "
                       f"quelques blocs plutôt que par leur nombre")
        print(f"    sensibilité : {sens}")
        print(f"    → {verdit}")
    t = pd.DataFrame(lignes)
    sortie = RACINE / f"reports/verdict_{prefixe}_{axe}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--prefixe", default="apport_ratios_echelle")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--axe", default="double")
    n = a.parse_args()
    raise SystemExit(main(n.prefixe, n.horizon, n.axe))
