#!/usr/bin/env python3
"""Ce que « le meilleur de K » vaut sous l'hypothèse nulle — action A07.

Le problème, et pourquoi le citer ne suffit pas
------------------------------------------------
Ce dépôt écrit que le biais de criblage y vaut « ×2 à ×4 », chiffre venu du balayage des
variables inexploitées. C'est un ordre de grandeur emprunté à une autre expérience : il ne
dit pas ce que vaut le criblage SUR CES configurations-ci, avec ce nombre de blocs-là et
cette corrélation-là entre polluants.

Or la décision se prend sur `p_PC`, la conjonction partielle. Et `p_PC < 0,05` est un
seuil valide pour UNE configuration testée, pas pour la meilleure de quatorze. Retenir le
plus petit `p_PC` d'un lot revient à tirer quatorze fois et à garder le meilleur tirage.

Le protocole — permutation par retournement de signe des blocs
----------------------------------------------------------------
Sous H₀ « la configuration n'apporte rien », l'écart apparié d'un bloc est aussi
plausible en positif qu'en négatif : son signe est **échangeable**. On tire donc un
vecteur de signes par bloc, on l'applique, et on relit tout le lot.

Deux points de conception, et ils décident du résultat :

* **le même vecteur de signes sert à toutes les configurations d'un même lot de mois.**
  Les configurations sont emboîtées et partagent leurs plis ; leur donner des signes
  indépendants casserait cette corrélation et gonflerait artificiellement le maximum ;
* **les lots de mois différents reçoivent des vecteurs indépendants.** C'est une
  hypothèse de corrélation nulle entre lots, donc un maximum légèrement SURESTIMÉ — la
  calibration penche vers l'exigence, pas vers la complaisance.

⚠️ Ce que ce script ne dit pas : il calibre le criblage sur les configurations
effectivement écrites en CSV. Les pistes abandonnées avant d'écrire un fichier ne sont pas
comptées, et elles font partie du criblage réel. Le chiffre rendu est donc un **minorant**
du biais, et c'est écrit ici plutôt que passé sous silence.

Usage  : python3 scripts/calibrer_criblage.py [--axe double] [--tirages 4000]
Sortie : reports/calibration_criblage.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
from verdict_apports import blocs_de, conjonction_partielle  # noqa: E402

POLLUANTS = ("NO2", "O3", "PM10", "PM25")
BLOC = 3


def charger(axe: str, horizon: int) -> dict:
    """Rend {(prefixe, config): {polluant: (blocs, signature_de_mois)}}."""
    series: dict = {}
    for f in sorted((RACINE / "reports").glob(f"apport_*_h{horizon}_{axe}_par_pli.csv")):
        # « apport_<prefixe>_<POLLUANT>_h2_<axe>_par_pli.csv » — on retire les jetons de
        # queue plutôt que d'ancrer une expression à droite, qui capturerait le mauvais
        # groupe sur un nom à plusieurs jetons (§ 4 bis).
        jetons = f.stem.split("_")
        polluant = jetons[-4 - len(axe.split("_")) + 1] if False else None
        for p in POLLUANTS:
            if f"_{p}_h{horizon}_" in f.name:
                polluant = p
                break
        if polluant is None:
            continue
        prefixe = f.name.split(f"_{polluant}_h{horizon}_")[0]
        t = pd.read_csv(f)
        ref = t["rmse_config1"].to_numpy()
        signature = "|".join(map(str, t["mois"].tolist()))
        for c in [c for c in t.columns if c.startswith("rmse_config") and c != "rmse_config1"]:
            v = list(100 * (1 - t[c].to_numpy() / ref))
            b = blocs_de(v, BLOC)
            if len(b) >= 6:
                series.setdefault((prefixe, c), {})[polluant] = (np.array(b), signature)
    return series


def main(axe: str, horizon: int, tirages: int, graine: int) -> int:
    series = charger(axe, horizon)
    complets = {k: v for k, v in series.items() if len(v) == len(POLLUANTS)}
    if not complets:
        raise SystemExit(f"aucune configuration complète sur les {len(POLLUANTS)} polluants")
    cles = sorted(complets)
    K = len(cles)
    rng = np.random.default_rng(graine)

    # Un vecteur de signes par (polluant, signature de mois) et par tirage : les
    # configurations qui partagent leurs mois partagent leurs signes.
    groupes: dict[tuple[str, str], np.ndarray] = {}
    for k in cles:
        for p, (b, sig) in complets[k].items():
            groupes.setdefault((p, sig), b.shape)
    signes = {g: rng.choice([-1.0, 1.0], size=(tirages, forme[0]))
              for g, forme in groupes.items()}

    # Distribution nulle et valeur observée, par configuration et par polluant.
    nul: dict = {}
    obs: dict = {}
    for k in cles:
        for p, (b, sig) in complets[k].items():
            nul[(k, p)] = (signes[(p, sig)] * b).mean(axis=1)
            obs[(k, p)] = float(b.mean())

    def p_unilateral(echantillon: np.ndarray, valeurs: np.ndarray) -> np.ndarray:
        """`p` de permutation : la part de l'échantillon nul au moins aussi extrême."""
        tri = np.sort(echantillon)
        rang = np.searchsorted(tri, valeurs, side="left")
        return (1.0 + (len(tri) - rang)) / (len(tri) + 1.0)

    # p_PC observé par configuration, et p_PC sous H₀ pour chaque tirage.
    pc_obs, pc_nul = {}, np.empty((K, tirages))
    for i, k in enumerate(cles):
        ps_obs, ps_nul = [], []
        for p in POLLUANTS:
            ech = nul[(k, p)]
            ps_obs.append(float(p_unilateral(ech, np.array([obs[(k, p)]]))[0]))
            ps_nul.append(p_unilateral(ech, ech))
        pc_obs[k] = conjonction_partielle(ps_obs)
        # Conjonction partielle vectorisée : le 2ᵉ plus petit `p`, × (n − r + 1).
        m = np.sort(np.vstack(ps_nul), axis=0)
        pc_nul[i] = np.minimum(1.0, (len(POLLUANTS) - 2 + 1) * m[1])

    meilleur_nul = pc_nul.min(axis=0)          # le meilleur des K, tirage par tirage
    seuil = float(np.quantile(meilleur_nul, 0.05))
    # La TAILLE réelle du test pour UNE configuration : la part de tirages nuls dont le
    # p_PC descend sous 0,05. Si elle vaut 0,05, le test est exact ; si elle vaut bien
    # moins, il est conservateur — et c'est cette conservation, pas le criblage, qui
    # décide alors du seuil.
    taille_une = float((pc_nul < 0.05).mean())
    taille_K = float((meilleur_nul < 0.05).mean())
    moyennes_nul = np.vstack([np.abs(np.vstack([nul[(k, p)] for p in POLLUANTS])).mean(axis=0)
                              for k in cles]).max(axis=0)
    ampleur = float(np.quantile(moyennes_nul, 0.95))

    print(f"CALIBRATION DU CRIBLAGE · axe {axe} · {K} configurations complètes · "
          f"{tirages:,} tirages")
    print("═" * 98)
    print(f"  Taille réelle du test pour UNE configuration : P(p_PC < 0,05 | H₀) = "
          f"{taille_une:.4f}")
    print(f"  Taille après criblage des {K} : P(min p_PC < 0,05 | H₀) = {taille_K:.4f}")
    print(f"  Seuil calibré à 5 % d'erreur de famille sur les {K} : p_PC < {seuil:.4f}")
    if seuil >= 0.05:
        print(f"\n  → Le criblage ne consomme PAS le budget : la conjonction partielle est")
        print(f"    conservatrice d'un facteur {0.05 / max(taille_une, 1e-9):.0f}× pour une")
        print(f"    seule configuration, et cribler {K} candidats ne l'épuise pas. Garder")
        print(f"    0,05 comme barre de publication reste défendable — mais un résultat")
        print(f"    entre 0,05 et {seuil:.3f} n'est PAS écarté par le criblage : il est")
        print(f"    écarté par la sévérité du test, ce qui n'est pas la même réserve.")
    else:
        print(f"\n  → Le criblage consomme le budget : un p_PC observé doit descendre sous")
        print(f"    {seuil:.4f} pour valoir 0,05, soit {0.05 / seuil:.1f}× plus strict que")
        print(f"    le seuil naïf.")
    print(f"  Ampleur : sous H₀, le meilleur écart moyen des {K} atteint "
          f"{ampleur:.3f} pt (95ᵉ centile).")
    print("═" * 98)
    # 🔴 Les deux instruments ne s'accordent pas, et il faut le VOIR plutôt que choisir.
    # Le bootstrap par blocs du verdict est asymptotique ; sur 8 à 12 blocs, la
    # permutation par retournement de signe est EXACTE sous échangeabilité. Quand ils
    # divergent, c'est la permutation qui fait foi, et la divergence est un fait sur le
    # corpus, pas un détail d'implémentation.
    boot = {}
    # 🔴 La glob se termine à l'axe EXACT. Avec `_{axe}*.csv`, « double » attrapait aussi
    # « double_sans-geoscf », un AUTRE axe, et l'écrasait sur la même clé — la colonne
    # bootstrap affichait alors les `p` d'une expérience pour les configurations d'une
    # autre. C'est le motif du § 4 bis : un nom à plusieurs jetons dont on n'en capture
    # qu'une partie ne lève jamais, il rend le mauvais fichier.
    for f in (RACINE / "reports").glob(f"verdict_apport_*_{axe}.csv"):
        tv = pd.read_csv(f)
        # Un verdict d'une version antérieure ne porte pas cette colonne : on le saute en
        # le DISANT, plutôt que de le laisser lever ou, pire, de l'avaler en silence.
        if "p_conjonction_partielle" not in tv.columns:
            print(f"  ✘ {f.name} ignoré : sans colonne p_conjonction_partielle "
                  f"(verdict d'une version antérieure)")
            continue
        pref = "apport_" + f.stem.replace("verdict_apport_", "").rsplit(f"_{axe}", 1)[0]
        for _, r in tv.iterrows():
            boot[(pref, str(r["configuration"]))] = float(r["p_conjonction_partielle"])
    libelles = {}
    for f in sorted((RACINE / "reports").glob(f"apport_*_h{horizon}_{axe}.csv")):
        for p_ in POLLUANTS:
            if f"_{p_}_h{horizon}_" in f.name:
                pref = f.name.split(f"_{p_}_h{horizon}_")[0]
                tl = pd.read_csv(f)
                for k_, nom in enumerate(tl["configuration"], start=1):
                    libelles[(pref, f"rmse_config{k_}")] = str(nom)
                break

    print(f"  {'configuration':52s} {'permut.':>9s} {'bootstrap':>10s} {'verdict':>13s}")
    lignes = []
    for k in sorted(cles, key=lambda x: pc_obs[x]):
        tient = ("✅ tient" if pc_obs[k] < min(seuil, 0.05)
                 else "⚠️ zone grise" if pc_obs[k] < max(seuil, 0.05) else "🔴 non")
        nom = libelles.get(k, k[1])
        pb = boot.get((k[0], nom), float("nan"))
        alerte = " 🔴" if (pb == pb and (pb < 0.05) != (pc_obs[k] < 0.05)) else ""
        print(f"  {(k[0].replace('apport_', '') + ' · ' + nom)[:52]:52s} "
              f"{pc_obs[k]:9.4f} {pb:10.4f} {tient:>13s}{alerte}")
        lignes.append({"axe": axe, "prefixe": k[0], "config": k[1],
                       "p_PC_observe": pc_obs[k], "seuil_apres_criblage": seuil,
                       "n_configurations_criblees": K,
                       "taille_reelle_une_config": taille_une,
                       "taille_apres_criblage": taille_K,
                       "libelle": libelles.get(k, k[1]),
                       "p_PC_bootstrap_verdict": boot.get((k[0], libelles.get(k, k[1])),
                                                          float("nan")),
                       "tient_apres_criblage": bool(pc_obs[k] < seuil)})
    t = pd.DataFrame(lignes)
    for c in ("p_PC_observe", "seuil_apres_criblage", "tient_apres_criblage"):
        if c not in t:
            raise SystemExit(f"colonne absente du rapport : {c}")
    sortie = RACINE / "reports/calibration_criblage.csv"
    t.to_csv(sortie, index=False)
    print(f"\n⚠️ Minorant : seules les configurations écrites en CSV sont comptées. Les")
    print(f"   pistes abandonnées avant d'écrire un fichier font partie du criblage réel.")
    print(f"Écrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--axe", default="double")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--tirages", type=int, default=4000)
    a.add_argument("--graine", type=int, default=20260823)
    sys.exit(main(**vars(a.parse_args())))
