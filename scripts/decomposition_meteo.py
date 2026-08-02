#!/usr/bin/env python3
"""Laquelle des six variables météo porte le gain — et la pluie en fait-elle partie ?

La question, et pourquoi elle n'est pas résolue
-----------------------------------------------
La météo prévue IFS rend **+5,5 %** sur l'ozone, **+2,2 %** sur le NO₂ et **+4,8 %** sur les
PM2,5. Ces chiffres portent sur le **bloc entier** : six grandeurs agrégées en dix variables
journalières. On ne sait donc pas laquelle travaille.

La question a une portée pratique. Une chaîne opérationnelle qui n'aurait besoin que de la
température et du vent se câble bien plus simplement qu'une qui exige aussi le rayonnement,
la pluie et le point de rosée — et chaque champ supplémentaire est un point de panne.

Et une hypothèse est réfutable d'avance : **CAMS modélise déjà le dépôt humide**. Si la règle
du projet — *une correction n'ajoute que là où le modèle amont est aveugle à lui-même* — vaut
ici, alors la **pluie** devrait apporter peu, tandis que la couche limite (température, vent)
devrait apporter beaucoup, car c'est elle que huit kilomètres de maille lissent.

Le protocole
------------
Deux lectures complémentaires, sur les **mêmes plis** :

* **retrait** (*leave-one-out*) — on retire une grandeur du bloc complet. Mesure son apport
  **marginal**, c'est-à-dire ce qu'aucune autre ne remplace.
* **ajout seul** — on ajoute cette grandeur et elle seule à la base. Mesure son apport
  **total**, redondances comprises.

Les deux ensemble distinguent une variable *inutile* d'une variable *redondante* : la
première est faible sur les deux lectures, la seconde forte en ajout et faible en retrait.
C'est la distinction que la mesure du bloc entier ne permet pas, et c'est elle qui décide.

Usage : python3 scripts/decomposition_meteo.py [--polluant O3]
Sortie : reports/decomposition_meteo_{polluant}.csv
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from apport_ifs import COMMUNES, journalier  # noqa: E402
from apport_meteo import ic_difference  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

from aq.ingest.controle import ControleEchec  # noqa: E402

GRAINE = 20260731

# Chaque grandeur physique et les colonnes journalières qu'elle produit. Le regroupement suit
# le **mécanisme** : retirer `ifs_vent` sans retirer `ifs_sin`/`ifs_cos` laisserait le vent
# dans le modèle sous une autre forme, et la mesure ne voudrait rien dire.
GRANDEURS = {
    "température": ["ifs_temp", "ifs_temp_max"],
    "point de rosée": ["ifs_rosee"],
    "rayonnement": ["ifs_ray", "ifs_ray_max"],
    "précipitation": ["ifs_pluie"],
    "vent": ["ifs_vent", "ifs_vent_max", "ifs_sin", "ifs_cos"],
}


def modele():
    return modele_mos(graine=GRAINE)


def evaluer(d: pd.DataFrame, predicteurs: list[str], groupe: np.ndarray) -> pd.DataFrame:
    pred = np.full(len(d), np.nan)
    for p in sorted(set(groupe)):
        test = groupe == p
        m = modele()
        m.fit(d.loc[~test, predicteurs],
              d.loc[~test, "valeur"] - d.loc[~test, "cams_jour"])
        pred[test] = np.clip(d.loc[test, "cams_jour"].to_numpy()
                             + m.predict(d.loc[test, predicteurs]), 0, None)
    return pd.DataFrame({"station_id": d["station_id"], "obs_jour": d["valeur"],
                         "pred": pred})


def rmse(p: pd.DataFrame) -> float:
    return float(np.sqrt(np.mean((p["pred"] - p["obs_jour"]) ** 2)))


def queue(p: pd.DataFrame) -> float:
    haut = p["obs_jour"] >= p["obs_jour"].quantile(0.9)
    return float(np.sqrt(np.mean((p.loc[haut, "pred"] - p.loc[haut, "obs_jour"]) ** 2)))


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    d = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    d = d.rename(columns={"obs_jour": "valeur"})
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    fichiers = sorted(glob.glob(str(RACINE / "data/processed/meteo/ifs_metropole_*.parquet")))
    retenus = [f for f in fichiers if set(COMMUNES) <= set(pd.read_parquet(f).columns)]
    if len(retenus) < 5:
        raise ControleEchec(f"{len(retenus)} mois IFS exploitables — trop peu pour décomposer")
    ifs = pd.concat([pd.read_parquet(f)[list(COMMUNES) + ["station_id", "timestamp_utc"]]
                     for f in retenus], ignore_index=True)
    ifs_j, noms = journalier(ifs, "ifs")
    d = d.merge(ifs_j, on=["station_id", "jour"], how="inner").reset_index(drop=True)

    # Toute colonne du bloc doit appartenir à exactement une grandeur : une colonne orpheline
    # resterait dans le modèle à chaque retrait et fausserait toutes les mesures.
    classees = [c for v in GRANDEURS.values() for c in v]
    orphelines = sorted(set(noms) - set(classees))
    if orphelines:
        raise ControleEchec(f"colonnes météo non classées : {orphelines}")

    stations = np.sort(d["station_id"].unique())
    groupe = d["station_id"].map({s: i % n_plis for i, s in enumerate(stations)}).to_numpy()
    print(f"{polluant} · {len(d):,} jours-station · {len(stations)} stations · "
          f"{len(retenus)} mois IFS · {len(noms)} colonnes météo", flush=True)

    p_base = evaluer(d, base, groupe)
    p_tout = evaluer(d, base + noms, groupe)
    r_base, r_tout = rmse(p_base), rmse(p_tout)
    print(f"  base {r_base:.3f} · bloc météo complet {r_tout:.3f} "
          f"(gain {r_base - r_tout:+.3f}, {100 * (r_base - r_tout) / r_base:+.1f} %)",
          flush=True)

    lignes = []
    for nom, cols in GRANDEURS.items():
        sans = evaluer(d, base + [c for c in noms if c not in cols], groupe)
        seule = evaluer(d, base + cols, groupe)
        # Apport marginal : ce que le bloc perd quand on retire cette grandeur.
        marginal = rmse(sans) - r_tout
        b_m, h_m = ic_difference(sans, p_tout)
        # Apport total : ce que cette grandeur seule rend contre la base.
        total = r_base - rmse(seule)
        b_t, h_t = ic_difference(p_base, seule)
        lignes.append({"grandeur": nom, "n_colonnes": len(cols),
                       "apport_marginal": marginal, "marg_ic_bas": b_m, "marg_ic_haut": h_m,
                       "apport_total": total, "tot_ic_bas": b_t, "tot_ic_haut": h_t,
                       "queue_seule": queue(seule)})
        print(f"  {nom:16s} marginal {marginal:+.3f} [{b_m:+.3f} ; {h_m:+.3f}] · "
              f"total {total:+.3f} [{b_t:+.3f} ; {h_t:+.3f}] · "
              f"{time.time() - depart:5.0f}s", flush=True)

    t = pd.DataFrame(lignes).sort_values("apport_marginal", ascending=False)
    print(f"\n{'─' * 84}\nClassement par apport **marginal** — ce qu'aucune autre "
          f"variable ne remplace :")
    for _, r in t.iterrows():
        etat = ("porteuse" if r["marg_ic_bas"] > 0
                else ("redondante" if r["tot_ic_bas"] > 0 else "sans effet"))
        print(f"  {r['grandeur']:16s} {r['apport_marginal']:+.3f} µg/m³  → {etat}")

    pluie = t[t["grandeur"] == "précipitation"].iloc[0]
    print(f"\nLa **pluie** : marginal {pluie['apport_marginal']:+.3f} "
          f"[{pluie['marg_ic_bas']:+.3f} ; {pluie['marg_ic_haut']:+.3f}] · "
          f"total {pluie['apport_total']:+.3f} "
          f"[{pluie['tot_ic_bas']:+.3f} ; {pluie['tot_ic_haut']:+.3f}]")
    if pluie["marg_ic_bas"] > 0:
        print("  → Elle porte une information propre. CAMS modélise le dépôt humide, mais "
              "pas assez\n    finement pour que la corriger soit inutile.")
    elif pluie["tot_ic_bas"] > 0:
        print("  → Redondante : seule elle aide, mais une autre variable porte la même "
              "information.\n    Une chaîne opérationnelle peut s'en passer.")
    else:
        print("  → Sans effet mesurable, dans les deux lectures. Conforme à la règle du "
              "projet :\n    CAMS modélise déjà le dépôt humide, et le re-fournir n'ajoute "
              "rien.")

    sortie = RACINE / f"reports/decomposition_meteo_{polluant}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--plis", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.plis))
