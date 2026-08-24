#!/usr/bin/env python3
"""Le registre EXHAUSTIF des configurations criblées — chantier ④, action P0.5.

Le défaut qu'il corrige
------------------------
La calibration du criblage ne compte que les configurations **ayant laissé un CSV**. Or une
configuration abandonnée après un résultat partiel a déjà influencé la sélection : elle
consomme un degré de liberté que rien n'enregistre. Le seuil de 0,0950 calculé sur douze
configurations n'est donc défendable que si douze est le vrai compte — et il ne l'est pas.

    « Un registre défini par les seuls fichiers qui ont survécu n'est pas un registre. »

Le moment d'entrée
-------------------
Un candidat reçoit un identifiant **avant le premier calcul dépendant de la cible ou du
score** : entraînement même partiel, calcul sur un seul polluant, ablation partielle,
graphique de résidus servant à décider, ou tout proxy de performance pouvant conduire à
abandonner.

Une vérification de licence, de schéma, de coût ou de disponibilité reste une **étude de
faisabilité** : elle est tracée, mais ne consomme pas le lot d'hypothèses tant qu'aucune
information de résultat n'a été consultée.

Les états
----------
    PROPOSÉ
    ├── INÉLIGIBLE AVANT RÉSULTAT   → tracé, ne compte PAS dans la famille de tests
    ├── ÉCHEC TECHNIQUE             → reste au registre, compte
    ├── EXÉCUTÉ / REJETÉ            → compte
    ├── EXÉCUTÉ / RÉSERVE           → compte
    └── EXÉCUTÉ / PROMU             → compte

Usage
-----
  registre_configs.py inscrire --lot ifs-2026-08 --config "IFS surface, 8 champs" \
      --polluants NO2,O3,PM10,PM25 --effet-utile 0.5
  registre_configs.py etat --id ab12cd34 --statut execute/reserve --resultat "…"
  registre_configs.py compte          # le nombre de degrés de liberté consommés
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
REGISTRE = RACINE / "reports/registre_configurations.jsonl"
STATUTS = ("propose", "ineligible-avant-resultat", "echec-technique",
           "execute/rejete", "execute/reserve", "execute/promu")
# Seuls ces états consomment un degré de liberté : ils ont vu un résultat.
COMPTENT = {"echec-technique", "execute/rejete", "execute/reserve", "execute/promu"}


def lire() -> list[dict]:
    if not REGISTRE.exists():
        return []
    return [json.loads(l) for l in REGISTRE.read_text().splitlines() if l.strip()]


def inscrire(lot: str, config: str, polluants: str, effet_utile: float,
             note: str | None) -> int:
    h = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ident = hashlib.sha256(f"{h}|{lot}|{config}".encode()).hexdigest()[:8]
    REGISTRE.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRE.open("a") as f:
        f.write(json.dumps({"id": ident, "inscrit_le": h, "lot": lot, "config": config,
                            "polluants": polluants, "effet_utile_pt": effet_utile,
                            "statut": "propose", "resultat": None, "clos_le": None,
                            "note": note}, ensure_ascii=False) + "\n")
    print(f"✅ {ident} · lot {lot} · {config}")
    print(f"   ⚠️ inscrit AVANT tout calcul dépendant du score. S'il en dépend déjà, "
          f"le compte est faux.")
    return 0


def etat(ident: str, statut: str, resultat: str) -> int:
    if statut not in STATUTS:
        raise SystemExit(f"--statut doit être l'un de {', '.join(STATUTS)}")
    e = lire()
    if not any(x["id"] == ident for x in e):
        raise SystemExit(f"identifiant {ident} absent")
    for x in e:
        if x["id"] == ident:
            if x["statut"] != "propose":
                raise SystemExit(f"{ident} déjà clos ({x['statut']}) — un état ne se "
                                 f"réécrit pas ; inscrire une nouvelle configuration.")
            x.update(statut=statut, resultat=resultat,
                     clos_le=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    REGISTRE.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in e))
    print(f"{'✅' if statut in COMPTENT else '⬜'} {ident} · {statut} · {resultat}")
    return 0


def compte() -> int:
    e = lire()
    if not e:
        print("registre vide — aucun degré de liberté enregistré.")
        print("⚠️ Cela ne veut pas dire qu'aucun n'a été consommé : le registre commence "
              "le 24/08/2026,\n   et la campagne qui précède doit être qualifiée "
              "d'exploratoire.")
        return 0
    par_statut: dict[str, int] = {}
    for x in e:
        par_statut[x["statut"]] = par_statut.get(x["statut"], 0) + 1
    consommes = sum(n for s, n in par_statut.items() if s in COMPTENT)
    ouverts = par_statut.get("propose", 0)
    print(f"REGISTRE DES CONFIGURATIONS · {len(e)} inscrites")
    print("═" * 80)
    for s in STATUTS:
        if s in par_statut:
            marque = "compte" if s in COMPTENT else "ne compte pas"
            print(f"  {s:28s} {par_statut[s]:3d}   {marque}")
    print("═" * 80)
    print(f"  degrés de liberté CONSOMMÉS : {consommes}"
          + (f" · {ouverts} encore ouverte(s)" if ouverts else ""))
    print(f"  → c'est ce nombre, et non celui des CSV survivants, qui doit alimenter")
    print(f"    la correction de criblage de `calibrer_decision.py`.")
    for x in e:
        if x["statut"] == "propose":
            print(f"\n⏳ {x['id']} · {x['lot']} · {x['config']}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = a.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("inscrire")
    i.add_argument("--lot", required=True)
    i.add_argument("--config", required=True)
    i.add_argument("--polluants", default="NO2,O3,PM10,PM25")
    i.add_argument("--effet-utile", type=float, default=0.5, dest="effet_utile")
    i.add_argument("--note", default=None)
    e = sub.add_parser("etat")
    e.add_argument("--id", required=True, dest="ident")
    e.add_argument("--statut", required=True, choices=STATUTS)
    e.add_argument("--resultat", required=True)
    sub.add_parser("compte")
    n = a.parse_args()
    cmd = vars(n).pop("cmd")
    sys.exit({"inscrire": inscrire, "etat": etat, "compte": compte}[cmd](**vars(n)))
