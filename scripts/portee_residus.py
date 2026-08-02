#!/usr/bin/env python3
"""Sur quelle distance les résidus restent-ils corrélés — et donc jusqu'où la fuite porte.

Les deux questions que ce script tranche d'un coup
--------------------------------------------------
**1. Quel rayon de fossé choisir ?** La validation par plis bloqués creuse un fossé de *r*
kilomètres autour des stations de test. Jusqu'ici *r* a été essayé à 25 puis 50 km — donc
choisi **après** avoir vu les scores, ce qui n'est pas un protocole. Le rayon juste se lit
dans la **portée de l'autocorrélation des résidus** : au-delà, une station voisine n'apporte
plus rien, et le fossé devient inutile.

**2. Pourquoi le NO₂ résiste-t-il au blocage et pas l'ozone ?** Le NO₂ perd 2,2 points, l'ozone
10,1. L'explication par la densité du réseau est **réfutée** : le NO₂ a les stations les plus
serrées (4,1 km de médiane, 66 % sous 10 km) et c'est lui qui résiste le mieux ; l'ozone, trois
fois plus dispersé (14,3 km), perd le plus.

L'hypothèse testée ici, écrite **avant** la mesure : ce n'est pas la densité qui compte, c'est
la **portée**. Si les résidus d'ozone restent corrélés sur des dizaines de kilomètres —
photochimie régionale — alors même des voisines lointaines renseignent, et le blocage coûte
cher. Si les résidus de NO₂ décorrèlent en quelques kilomètres — sources linéaires locales —
alors une voisine à 2 km n'apprend rien, et le blocage ne coûte presque rien.

Ce que le script mesure
-----------------------
Pour chaque couple de stations : la **corrélation de leurs séries de résidus** hors pli, sur
leurs jours communs. Puis la moyenne par tranche de distance — c'est un corrélogramme, et sa
**portée pratique** est la distance où la corrélation passe sous un seuil.

⚠️ On corrèle les **résidus**, pas les concentrations. Deux stations voisines ont des
concentrations corrélées de façon triviale ; ce qui décide de la fuite est que leurs *erreurs
de modèle* le soient.

Usage : python3 scripts/portee_residus.py [--polluant O3]
Sortie : reports/portee_residus_{polluant}.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

from aq.ingest.controle import ControleEchec, exiger_colonnes  # noqa: E402

GRAINE = 20260801
# Un couple de stations n'est retenu que s'il partage assez de jours : une corrélation sur
# vingt points est du bruit, et elle pèserait autant qu'une corrélation sur cinq cents.
MIN_JOURS_COMMUNS = 120
TRANCHES = [0, 5, 10, 20, 35, 50, 75, 100, 150, 200, 300, 500, 1000]
# Seuil de portée pratique. 0,1 plutôt que 0,05 : en dessous, la corrélation moyenne est
# noyée dans la dispersion des couples, et la portée lue devient arbitraire.
SEUIL_PORTEE = 0.10


def modele():
    return modele_mos(graine=GRAINE)


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    d = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    d = d.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    stations = np.sort(d["station_id"].unique())
    groupe = d["station_id"].map({s: i % n_plis for i, s in enumerate(stations)}).to_numpy()
    d["pred"] = np.nan
    for p in sorted(set(groupe)):
        test = groupe == p
        m = modele()
        m.fit(d.loc[~test, predicteurs], d.loc[~test, "valeur"] - d.loc[~test, "cams_jour"])
        d.loc[test, "pred"] = np.clip(
            d.loc[test, "cams_jour"].to_numpy() + m.predict(d.loc[test, predicteurs]),
            0, None)
    d["residu"] = d["valeur"] - d["pred"]
    # Le résidu de CAMS brut sert de témoin : si sa portée est longue et celle du résidu
    # corrigé courte, la correction a **absorbé** la structure spatiale — ce qui est
    # précisément ce qu'on lui demande.
    d["residu_cams"] = d["valeur"] - d["cams_jour"]

    meta = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    exiger_colonnes(meta, ["station_id", "x_l93", "y_l93"], "stations")
    meta = meta.drop_duplicates("station_id").set_index("station_id")
    ids = [s for s in stations if s in meta.index]
    if len(ids) < len(stations):
        raise ControleEchec(f"{len(stations) - len(ids)} stations sans coordonnées")
    xy = meta.loc[ids, ["x_l93", "y_l93"]].to_numpy() / 1000.0
    dist = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])

    lignes = []
    for etiquette, colonne in (("résidu corrigé", "residu"), ("résidu CAMS brut", "residu_cams")):
        table = d.pivot_table(index="jour", columns="station_id", values=colonne)
        table = table.reindex(columns=ids)
        # Corrélation par paires sur les jours communs — pandas gère l'appariement ; on
        # invalide ensuite les couples dont l'effectif commun est trop faible.
        c = table.corr(min_periods=MIN_JOURS_COMMUNS).to_numpy()
        haut = np.triu_indices(len(ids), k=1)
        r, dd = c[haut], dist[haut]
        ok = np.isfinite(r)
        print(f"\n{etiquette} · {ok.sum():,} couples exploitables sur {len(r):,} "
              f"(≥ {MIN_JOURS_COMMUNS} jours communs)", flush=True)
        print(f"{'tranche (km)':>16} {'couples':>9} {'r moyen':>9} {'r médian':>9}")
        for a, b in zip(TRANCHES[:-1], TRANCHES[1:]):
            sel = ok & (dd >= a) & (dd < b)
            if sel.sum() < 20:
                continue
            rm, rmed = float(r[sel].mean()), float(np.median(r[sel]))
            print(f"{f'{a}–{b}':>16} {sel.sum():9d} {rm:9.3f} {rmed:9.3f}")
            lignes.append({"polluant": polluant, "serie": etiquette, "borne_bas": a,
                           "borne_haut": b, "n_couples": int(sel.sum()),
                           "r_moyen": rm, "r_median": rmed})

        # Portée pratique : première tranche dont la corrélation moyenne passe sous le seuil.
        courbe = [l for l in lignes if l["serie"] == etiquette]
        portee = next((l["borne_bas"] for l in courbe if l["r_moyen"] < SEUIL_PORTEE), None)
        print(f"  → portée pratique (r < {SEUIL_PORTEE}) : "
              + (f"**{portee} km**" if portee is not None
                 else f"non atteinte à {courbe[-1]['borne_haut']} km"))

    t = pd.DataFrame(lignes)
    sortie = RACINE / f"reports/portee_residus_{polluant}.csv"
    t.to_csv(sortie, index=False)

    corrige = t[t["serie"] == "résidu corrigé"]
    p_corrige = next((int(l.borne_bas) for l in corrige.itertuples()
                      if l.r_moyen < SEUIL_PORTEE), None)
    print(f"\n{'─' * 78}")
    if p_corrige is None:
        print(f"  ⚠️ La corrélation des résidus corrigés ne descend jamais sous "
              f"{SEUIL_PORTEE}\n     sur la plage examinée : **aucun fossé praticable ne "
              f"supprime la fuite**.\n     Le chiffre bloqué reste alors optimiste, et il "
              f"faut le dire.")
    else:
        print(f"  → Rayon de fossé justifié pour {polluant} : **{p_corrige} km**.\n"
              f"    C'est la distance au-delà de laquelle une station voisine n'informe plus\n"
              f"    le résidu — donc le seul rayon choisi par la donnée et non par le score.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.plis))
