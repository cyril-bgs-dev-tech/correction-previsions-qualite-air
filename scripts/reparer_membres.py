#!/usr/bin/env python3
"""Masque les valeurs de remplissage des membres déjà extraits, et recalcule les dérivées.

L'erreur qui a produit ce script — 04/08/2026
-----------------------------------------------
Le membre **CHIMERE de décembre 2025** portait **22 848 valeurs jusqu'à 1,3 × 10¹² µg/m³**,
quand le p99,9 de tous les membres PM10 vaut **110**. Aucun contrôle n'a levé : ni à
l'extraction, ni au chargement, ni à l'ajustement. Le krigeage du biais récent les a
propagées, et la chaîne concurrente est sortie du rapport avec une **RMSE de 4 milliards**.

Découvert seulement parce qu'un tableau affichait `4035579516.230` — c'est-à-dire par
hasard. Un fichier corrompu de 0,06 % de ses lignes ne se voit pas autrement.

Ce que fait ce script
-----------------------
1. masque à `NaN` tout ce qui dépasse le plafond de plausibilité physique de l'espèce ;
2. **recalcule les colonnes dérivées** — médiane, écart-type, min, max, effectif, étendue,
   asymétrie — qui sont contaminées par construction ;
3. écrit sous un nom provisoire, vérifie, puis renomme ;
4. rend le compte, fichier par fichier.

⚠️ Le point 2 est le plus facile à oublier : masquer les six membres sans refaire les
dérivées laisse `membres_max` à 1,3 × 10¹² dans un fichier par ailleurs assaini.

Usage : python3 scripts/reparer_membres.py [--seulement pm10]
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from extraire_membres import PLAFOND  # noqa: E402

MEMBRES = ["chimere", "emep", "mocage", "silam", "lotos", "match"]
DOSSIER = RACINE / "data/processed/meteo"


def derivees(t: pd.DataFrame, presents: list[str]) -> pd.DataFrame:
    v = t[presents]
    t["membres_median"] = v.median(axis=1)
    t["membres_ecart"] = v.std(axis=1)
    t["membres_min"] = v.min(axis=1)
    t["membres_max"] = v.max(axis=1)
    t["membres_n"] = v.notna().sum(axis=1)
    t["membres_etendue"] = t["membres_max"] - t["membres_min"]
    # (max − médiane) − (médiane − min) : distingue un désaccord **orienté** d'un
    # désaccord symétrique. Recalculée, sinon elle garde la trace des valeurs masquées.
    t["membres_asymetrie"] = (t["membres_max"] - t["membres_median"]) - (
        t["membres_median"] - t["membres_min"])
    return t


def main(seulement: str | None) -> int:
    # ⚠️ § 4 bis — l'expression capture TOUS les jetons de mois, pas le dernier. Ancrée à
    # droite sur un seul `(\d{6})`, elle ne matchait pas un nom groupé
    # `..._o3_202308_202309.parquet` : ici elle levait (« nom non conforme »), donc sans
    # perte silencieuse — mais le motif restait celui qui a déjà coûté 35 % d'un jeu
    # d'entraînement ailleurs. On le corrige à la source plutôt que d'attendre le jumeau.
    motif = re.compile(
        r"membres_metropole_([a-z][a-z0-9]*)_(\d{6}(?:_\d{6})*)\.parquet$")
    fichiers = sorted(glob.glob(str(DOSSIER / "membres_metropole_*.parquet")))
    total, touches = 0, 0
    for f in fichiers:
        m = motif.search(f)
        if not m:
            raise SystemExit(f"nom non conforme : {Path(f).name}")
        espece, mois = m.group(1), m.group(2)
        if seulement and espece != seulement:
            continue
        plafond = PLAFOND.get(espece, 5000.0)
        t = pd.read_parquet(f)
        presents = [x for x in MEMBRES if x in t.columns]
        n = int(sum((t[x] > plafond).sum() for x in presents))
        if n == 0:
            continue
        avant = float(np.nanmax(t[presents].to_numpy()))
        for x in presents:
            t.loc[t[x] > plafond, x] = np.nan
        t = derivees(t, presents)
        apres = float(np.nanmax(t[presents].to_numpy()))
        cible = Path(f)
        prov = cible.with_suffix(".parquet.partiel")
        t.to_parquet(prov, index=False)
        # Vérifier AVANT de renommer : un nom définitif vaut marque d'assainissement.
        v = pd.read_parquet(prov, columns=presents + ["membres_max", "membres_asymetrie"])
        if float(np.nanmax(v[presents].to_numpy())) > plafond \
                or float(np.nanmax(v["membres_max"])) > plafond:
            prov.unlink(missing_ok=True)
            raise SystemExit(f"{cible.name} : assainissement incomplet, non écrit")
        prov.replace(cible)
        total += n
        touches += 1
        print(f"  {espece:5s} {mois} · {n:7,d} valeurs masquées · "
              f"max {avant:11.4g} → {apres:8.2f}", flush=True)

    print(f"\n{touches} fichier(s) réparé(s) · {total:,} valeurs masquées")
    if touches:
        print("⚠️ Relancer la production sur les polluants touchés : leurs prédictions "
              "ont été ajustées sur des entrées contaminées.")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--seulement", default=None, help="limiter à une espèce (ex. pm10)")
    n = a.parse_args()
    raise SystemExit(main(n.seulement))
