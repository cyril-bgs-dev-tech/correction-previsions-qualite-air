#!/usr/bin/env python3
"""Les données de la page 00 — la porte d'entrée du dossier.

Pourquoi cette page existe
----------------------------
Un lecteur arrivait sur « dix-sept sources de données », c'est-à-dire l'argument le plus
faible en premier, et devait traverser 25 000 pixels avant de savoir ce que ce travail
démontre. La thèse était enterrée en page 03.

Cette page ne mesure **rien de neuf**. Elle lit les JSON des pages 04 et 06 et n'en extrait
que les chiffres de tête. C'est délibéré : deux pages qui affichent le même gain avec deux
décimales différentes détruisent la confiance dans les deux. Un seul chemin de données, un
seul chiffre.

⚠️ Le périmètre affiché est **PARTOUT** — aucune observation passée de la station n'entre
dans le modèle, donc le chiffre vaut *là où rien ne mesure*. Le périmètre « aux stations »
afficherait davantage ; il ne vaut que là où un capteur existe déjà. Les deux ne se
confondent jamais, et c'est le plus bas des deux qui est mis en avant : c'est le seul que
CAMS ne sait pas faire.

Usage  : python3 scripts/page_synthese.py
Sortie : reports/figures/p0_donnees.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from aq.rapport import libelle_echeance  # noqa: E402
FIG = RACINE / "reports/figures"

ORDRE = ["NO2", "O3", "PM10", "PM25"]

# ⚠️ Les chiffres de tête viennent de la PILE COMPLÈTE (VERITE_DOSSIER § 12), pas des
# tableaux de la page 04. Ce ne sont pas les mêmes familles et elles ne s'interchangent
# pas : la pile empile TOUS les leviers, GEOS-CF compris, à J+2, sur la fenêtre du flux
# GEOS-CF v1. La page 04 mesure la même architecture SANS GEOS-CF, à J+1, sur 36 mois.
# Les deux sont justes ; c'est de les confondre qui serait faux.
# 🔴 La passe la plus CONTRÔLÉE, jamais la plus ancienne — et depuis le 25/08 c'est le SOCLE.
#
# `_h2.csv` (29 mois) porte un défaut de support reproduit : des familles absentes sur un mois
# entier donnaient au modèle un indicateur d'époque, alors que le protocole cache les mois.
#
# Et sa fenêtre était bornée par GEOS-CF v1 — un **candidat** qui définissait ainsi le banc
# d'essai sur lequel on le jugeait, en faisant perdre huit mois à toutes les autres familles.
# Le contrat de produit (`reports/CONTRAT_PRODUIT.md`) fixe la fenêtre par la DISPONIBILITÉ,
# avant tout candidat : c'est le socle, et c'est lui qu'on publie.
SUFFIXES_PILE = ("_sans-feux-geoscf_fenetre-complete",
                 "_spe-core7_sc_sans-feux-membres", "_spe-core7_sc", "")


def chemin_pile(p: str) -> Path:
    for suf in SUFFIXES_PILE:
        f = RACINE / f"reports/methode_maximale_{p}_h2{suf}.csv"
        if f.exists():
            return f
    raise SystemExit(f"aucune passe maximale pour {p}")


PILE = RACINE / "reports/methode_maximale_{p}_h2.csv"
HORIZON = 2

# 🔴 L'échéance se DÉRIVE, elle ne s'écrit pas — 25/08/2026.
#
# Cette signature annonçait « J+2 » pour `horizon=2`. Or `TRANCHES = {1: (1,24), 2: (25,48)}`
# porte des heures depuis la sortie de 00 UTC : les heures 1 à 24 sont celles du JOUR DE LA
# SORTIE, donc `horizon=1` est J0 et `horizon=2` est **J+1**. Vérifié sur les données le
# 17/08 — premier jour couvert 2023-08-01 pour horizon 1, 2023-08-02 pour horizon 2.
#
# `libelle_echeance` existe exactement pour cela, et la page de garde du dossier l'ignorait au
# profit d'une chaîne écrite à la main. C'est la § 4 ter — *un nom d'axe n'est pas ce qu'il
# annonce* — sur la première page que lit un recruteur d'AASQA.
SIGNATURE = {"perimetre": "PARTOUT", "epreuve": "double aveugle — station ET mois cachés",
             "echeance": libelle_echeance(HORIZON),
             "source": "socle du contrat de produit — fenêtre fixée par la disponibilité, "
                       "hors GEOS-CF et feux (modules conditionnels)"}


def main() -> int:
    for f in ("p4_donnees.json", "p6_donnees.json"):
        if not (FIG / f).exists():
            raise SystemExit(f"{f} absent — lancer d'abord son générateur")
    p4 = json.loads((FIG / "p4_donnees.json").read_text(encoding="utf-8"))
    p6 = json.loads((FIG / "p6_donnees.json").read_text(encoding="utf-8"))

    gains = []
    for p in ORDRE:
        fp = chemin_pile(p)
        if not fp.exists():
            raise SystemExit(f"{fp.name} absent — la pile complète n'est pas mesurée")
        import pandas as pd  # noqa: PLC0415
        t = pd.read_csv(fp)
        ligne = t[t["configuration"].str.contains("MAXIMALE — PARTOUT", regex=False)]
        if len(ligne) != 1:
            raise SystemExit(f"{fp.name} : {len(ligne)} ligne(s) « MAXIMALE — PARTOUT »")
        r = ligne.iloc[0]
        b = p4["polluants"].get("PM10" if p == "PM10" else p)
        gains.append({
            "code": p, "nom": (b or {}).get("nom", p),
            "gain": round(float(r["gain_pct"]), 2),
            "n_mois": int(r["n_mois"]), "fenetre": str(r["fenetre"]).split("→"),
            # La fenêtre diffère d'un polluant à l'autre : seuls les ÉCARTS ENTRE ÉTAGES
            # se comparent, jamais les niveaux. C'est écrit sur la page.
        })

    pm10 = p6["polluants"].get("PM10")
    if pm10 is None:
        raise SystemExit("PM10 absent de p6_donnees.json")
    par = {s["nom"]: s for s in pm10["systemes"]}
    for attendu in ("observation", "notre modèle", "chaîne AASQA"):
        if attendu not in par:
            raise SystemExit(f"système « {attendu} » absent de p6")

    sortie = {
        "signature": SIGNATURE,
        "gains": gains,
        "contrepoids": {
            "episodes": pm10["episodes"],
            "declares": p6["inevaluables"]["total_declares"],
            "nous": par["notre modèle"]["attrapes"],
            "aasqa": par["chaîne AASQA"]["attrapes"],
            "plafond": par["observation"]["attrapes"],
        },
        "corpus": {"mois_min": min(g["n_mois"] for g in gains),
                   "mois_max": max(g["n_mois"] for g in gains)},
    }
    f = FIG / "p0_donnees.json"
    f.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")),
                 encoding="utf-8")
    for g in gains:
        print(f"  {g['nom']:6s} {g['gain']:+6.2f} % · {g['n_mois']:>2} mois · "
              f"{'→'.join(g['fenetre'])}")
    c = sortie["contrepoids"]
    print(f"  contrepoids : {c['nous']}/{c['episodes']} épisodes réels attrapés "
          f"(plafond {c['plafond']}, chaîne AASQA {c['aasqa']})")
    print(f"Écrit : {f.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
