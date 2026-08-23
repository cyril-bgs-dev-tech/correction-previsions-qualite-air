#!/usr/bin/env python3
"""Le prétraitement a-t-il changé sans qu'on le veuille ? — action A10.

Pourquoi ce contrôle existe
----------------------------
Deux défauts de prétraitement ont été trouvés le 22/08 par un audit, pas par la chaîne :

* la fenêtre « 8 h » se comptait en **lignes** et non en heures — 7,96 % des jours-station
  d'ozone portaient une cible fausse, et 98,6 % de janvier 2024 ;
* la clé d'appariement n'était pas unique — 5 à 6 % de doublons entraient dans le modèle.

Aucun des deux n'a jamais levé. Les deux produisaient des tables complètes, d'allure
normale, avec le bon nombre de colonnes. Ce sont les défauts que `CLAUDE.md` § 5 décrit :
*si ce traitement produisait un résultat incomplet, est-ce que je m'en apercevrais ?*

Les tests unitaires figent le **comportement des fonctions** sur des cas construits. Ils
ne voient rien d'une dérive du **corpus** : un mois réingéré autrement, un panel régénéré
avec un filtre différent, une écriture perdue sur `/mnt/d` — tous laissent les tests au
vert. Ce script comble exactement cet écart : il mesure des invariants sur les **données
réelles** et les compare à une empreinte figée.

Ce qu'il compare, et pourquoi ces grandeurs
--------------------------------------------
Chacune est choisie parce qu'un défaut connu la déplace, et dans un sens su :

* **lignes par polluant et par mois** — une réingestion qui perd un code de validité les
  fait chuter ; c'est ainsi que treize mois d'ozone avaient disparu ;
* **unicité de la clé (station, horodatage, polluant)** — le doublon d'appariement ;
* **couverture horaire médiane par jour-station** — la fenêtre 8 h et le filtre à 75 % ;
* **moments de la valeur** (médiane, écart-type) — une unité qui change, une sentinelle
  qui repasse, un étalon qui bouge.

🔴 Le seuil ne regarde pas seulement à la baisse. Un plancher « au moins N lignes » ne
voit rien d'un corpus qui GONFLE — et le doublon d'appariement gonflait. La comparaison
porte donc sur l'écart RELATIF en valeur absolue, dans les deux sens (§ 2 quinquies).

Usage  : python3 scripts/controle_pretraitement.py [--figer] [--tolerance 0.005]
Sortie : reports/pretraitement_empreinte.json ; code 1 si un invariant a dérivé.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
PANEL = RACINE / "data/processed/panel_unifie_lcsqa.parquet"
EMPREINTE = RACINE / "reports/pretraitement_empreinte.json"
POLLUANTS = ("NO2", "O3", "PM10", "PM25")


def mesurer() -> dict:
    if not PANEL.exists():
        raise SystemExit(f"panel absent : {PANEL.relative_to(RACINE)}")
    t = pd.read_parquet(PANEL, columns=["station_id", "timestamp_utc", "polluant",
                                        "valeur"])
    t = t[t["polluant"].isin(POLLUANTS)]
    t["mois"] = t["timestamp_utc"].dt.strftime("%Y-%m")
    t["jour"] = t["timestamp_utc"].dt.strftime("%Y-%m-%d")

    mesures: dict[str, float] = {}
    for p, g in t.groupby("polluant", observed=True):
        mesures[f"{p}.n_lignes"] = float(len(g))
        mesures[f"{p}.n_stations"] = float(g["station_id"].nunique())
        mesures[f"{p}.n_mois"] = float(g["mois"].nunique())
        # Unicité de la clé : la mesure est le NOMBRE de doublons, dont l'attendu est 0.
        mesures[f"{p}.n_doublons_cle"] = float(
            len(g) - len(g.drop_duplicates(subset=["station_id", "timestamp_utc"])))
        # Couverture horaire par jour-station : la fenêtre 8 h et le filtre à 75 % s'y
        # lisent directement. La médiane, pas la moyenne — une queue de jours creux la
        # tirerait sans qu'aucun jour ne change.
        h = g.dropna(subset=["valeur"]).groupby(["station_id", "jour"]).size()
        mesures[f"{p}.heures_par_jour_mediane"] = float(h.median()) if len(h) else np.nan
        mesures[f"{p}.part_jours_au_moins_18h"] = float((h >= 18).mean()) if len(h) else np.nan
        v = g["valeur"].dropna()
        mesures[f"{p}.valeur_mediane"] = float(v.median()) if len(v) else np.nan
        mesures[f"{p}.valeur_ecart_type"] = float(v.std()) if len(v) else np.nan
        mesures[f"{p}.valeur_min"] = float(v.min()) if len(v) else np.nan
    mesures["corpus.premier_mois"] = float(t["mois"].min().replace("-", ""))
    mesures["corpus.dernier_mois"] = float(t["mois"].max().replace("-", ""))
    return mesures


def comparer(ref: dict, mesures: dict, tolerance: float) -> tuple[list, list, list]:
    """La comparaison, isolée de toute entrée-sortie pour être testable.

    Rend `(derives, nouveaux, disparus)` ; chaque dérive est `(clé, référence, mesuré,
    écart_relatif)`. Un garde-fou non testé est une croyance, et il se testera tout seul
    le jour où il aura échoué (§ 1 quater).
    """
    nouveaux = sorted(set(mesures) - set(ref))
    disparus = sorted(set(ref) - set(mesures))
    derives = []
    for k in sorted(set(ref) & set(mesures)):
        a, b = ref[k], mesures[k]
        if a != a and b != b:            # deux NaN : identiques
            continue
        if a != a or b != b:             # un seul NaN : dérive, écart indéfini
            derives.append((k, a, b, float("nan")))
            continue
        # Écart RELATIF en valeur absolue : un invariant qui GONFLE dérive autant qu'un
        # invariant qui chute, et un plancher ne verrait que la seconde moitié (§ 2
        # quinquies). Le doublon d'appariement gonflait le corpus de 5 à 6 %.
        if abs(b - a) / max(abs(a), 1e-12) > tolerance:
            derives.append((k, a, b, abs(b - a) / max(abs(a), 1e-12)))
    return derives, nouveaux, disparus


def main(figer: bool, tolerance: float) -> int:
    mesures = mesurer()
    if figer or not EMPREINTE.exists():
        EMPREINTE.write_text(json.dumps(mesures, indent=2, sort_keys=True) + "\n")
        print(f"empreinte {'refigée' if figer else 'créée'} · {len(mesures)} invariants")
        print(f"Écrit : {EMPREINTE.relative_to(RACINE)}")
        for k in sorted(mesures):
            print(f"  {k:38s} {mesures[k]:>18,.4f}")
        return 0

    ref = json.loads(EMPREINTE.read_text())
    derives, nouveaux, disparus = comparer(ref, mesures, tolerance)

    print(f"CONTRÔLE DE PRÉTRAITEMENT · {len(mesures)} invariants · "
          f"tolérance {tolerance:.2%}")
    print("═" * 92)
    if nouveaux:
        print(f"  ➕ {len(nouveaux)} invariant(s) nouveau(x) : {', '.join(nouveaux)}")
    if disparus:
        print(f"  ➖ {len(disparus)} invariant(s) disparu(s) : {', '.join(disparus)}")
    if not derives:
        print("  ✅ aucun invariant n'a dérivé au-delà de la tolérance.")
        return 1 if disparus else 0
    print(f"  🔴 {len(derives)} invariant(s) ont dérivé :\n")
    print(f"  {'invariant':38s} {'référence':>16s} {'mesuré':>16s} {'écart':>9s}")
    for k, a, b, e in derives:
        print(f"  {k:38s} {a:>16,.4f} {b:>16,.4f} {e:>8.2%}")
    print("\n  Une dérive n'est pas une erreur : c'est une CHANGEMENT non déclaré. Si elle")
    print("  est voulue — réingestion, nouveau mois, filtre corrigé — refiger l'empreinte")
    print("  avec --figer, et dire dans le message de commit ce qui a bougé et pourquoi.")
    return 1


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--figer", action="store_true",
                   help="réécrire l'empreinte depuis les données actuelles")
    a.add_argument("--tolerance", type=float, default=0.005,
                   help="écart relatif toléré, dans les DEUX sens (défaut 0,5 %%)")
    sys.exit(main(**vars(a.parse_args())))
