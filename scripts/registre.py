#!/usr/bin/env python3
"""Le registre des prédictions — actions A02 et A03.

Pourquoi cet outil, et ce qu'il a déjà valu ici
------------------------------------------------
Deux défauts de protocole ont été trouvés cette semaine, et **aucun des deux n'a levé
d'exception**. L'un et l'autre n'ont été vus que parce qu'une prédiction avait été écrite
AVANT la mesure :

* le jeu d'options qui retirait quatre familles de la base rendait « tient 4/4 » avec des
  apports trois fois plus gros. Ce qui l'a démasqué est le NO₂ **gagnant contre une
  prédiction écrite qu'il ne devait rien gagner** — il mesurait de la substitution ;
* la fuite d'époque introduite en croyant élargir une fenêtre a été repérée parce que le
  nombre de plis annoncé avant le lancement — **32** — ne correspondait pas aux 36
  affichés. Coût mesuré de cette fuite : 15 % de gonflement sur l'ozone, parfaitement
  plausible, invisible sans la prédiction.

Une prédiction formulée APRÈS coup ne réfute rien : elle s'ajuste. Le registre la scelle —
horodatage et empreinte SHA-256 du texte — pour qu'elle ne puisse plus être réécrite en
silence, et il oblige à nommer **ce qui la démentirait** avant de lancer quoi que ce soit.

Ce que le registre mesure en plus des prédictions : moi
--------------------------------------------------------
`etat` rend la part de prédictions tenues. C'est la seule calibration honnête d'une
confiance affichée : si une prédiction sur deux tombe, annoncer « je m'attends à » ne vaut
rien, et le savoir change la façon d'écrire. Un registre qui ne compte que les succès ne
calibre rien — les prédictions démenties comptent au dénominateur.

Usage
-----
  registre.py inscrire --question "..." --prediction "..." --critere "..." [--echeance AAAA-MM-JJ]
  registre.py resoudre --id ab12cd34 --verdict tenu|dementi|indecidable --resultat "..."
  registre.py etat [--ouvertes]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
REGISTRE = RACINE / "reports/registre_predictions.jsonl"
VERDICTS = ("tenu", "dementi", "indecidable")


def lire() -> list[dict]:
    if not REGISTRE.exists():
        return []
    return [json.loads(l) for l in REGISTRE.read_text().splitlines() if l.strip()]


def inscrire(question: str, prediction: str, critere: str, echeance: str | None) -> int:
    if not critere.strip():
        raise SystemExit("--critere est obligatoire : une prédiction dont on ne sait pas "
                         "ce qui la réfuterait n'est pas une prédiction.")
    horodatage = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # L'empreinte couvre l'horodatage : réécrire le texte plus tard change l'identifiant,
    # donc la substitution se voit au lieu de passer.
    corps = f"{horodatage}|{question}|{prediction}|{critere}"
    ident = hashlib.sha256(corps.encode()).hexdigest()[:8]
    if any(e["id"] == ident for e in lire()):
        raise SystemExit(f"identifiant {ident} déjà présent — prédiction en double")
    entree = {"id": ident, "inscrit_le": horodatage, "question": question,
              "prediction": prediction, "critere_de_refutation": critere,
              "echeance": echeance, "verdict": None, "resultat": None, "resolu_le": None}
    REGISTRE.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRE.open("a") as f:
        f.write(json.dumps(entree, ensure_ascii=False) + "\n")
    print(f"✅ inscrite · id {ident} · {horodatage}")
    print(f"   question   : {question}")
    print(f"   prédiction : {prediction}")
    print(f"   réfutée si : {critere}")
    return 0


def resoudre(ident: str, verdict: str, resultat: str) -> int:
    if verdict not in VERDICTS:
        raise SystemExit(f"--verdict doit être l'un de {', '.join(VERDICTS)}")
    entrees = lire()
    cible = [e for e in entrees if e["id"] == ident]
    if not cible:
        raise SystemExit(f"identifiant {ident} absent du registre")
    if cible[0]["verdict"]:
        raise SystemExit(f"{ident} déjà résolue le {cible[0]['resolu_le']} "
                         f"({cible[0]['verdict']}) — une résolution ne se réécrit pas")
    for e in entrees:
        if e["id"] == ident:
            e.update(verdict=verdict, resultat=resultat,
                     resolu_le=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    REGISTRE.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entrees))
    marque = {"tenu": "✅", "dementi": "🔴", "indecidable": "⬜"}[verdict]
    print(f"{marque} {ident} · {verdict} · {resultat}")
    return 0


def etat(ouvertes: bool) -> int:
    entrees = lire()
    if not entrees:
        print("registre vide")
        return 0
    resolues = [e for e in entrees if e["verdict"]]
    en_cours = [e for e in entrees if not e["verdict"]]
    tenues = sum(1 for e in resolues if e["verdict"] == "tenu")
    decidees = [e for e in resolues if e["verdict"] != "indecidable"]

    print(f"REGISTRE DES PRÉDICTIONS · {len(entrees)} inscrites · "
          f"{len(en_cours)} ouvertes · {len(resolues)} résolues")
    if decidees:
        # Les démenties comptent au dénominateur : un registre qui ne compte que les
        # succès ne calibre rien.
        print(f"  calibration : {tenues}/{len(decidees)} tenues "
              f"({tenues / len(decidees):.0%}) — les indécidables sont hors ratio")
    print("═" * 96)
    for e in (en_cours if ouvertes else entrees):
        marque = {"tenu": "✅", "dementi": "🔴", "indecidable": "⬜",
                  None: "⏳"}[e["verdict"]]
        retard = ""
        if not e["verdict"] and e.get("echeance"):
            if date.fromisoformat(e["echeance"]) < date.today():
                retard = f"  ⚠️ échéance dépassée ({e['echeance']})"
        print(f"\n{marque} {e['id']} · {e['inscrit_le'][:10]}{retard}")
        print(f"   Q  {e['question']}")
        print(f"   P  {e['prediction']}")
        print(f"   R  réfutée si {e['critere_de_refutation']}")
        if e["verdict"]:
            print(f"   →  {e['verdict'].upper()} · {e['resultat']}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = a.add_subparsers(dest="commande", required=True)
    i = sub.add_parser("inscrire")
    i.add_argument("--question", required=True)
    i.add_argument("--prediction", required=True)
    i.add_argument("--critere", required=True, help="ce qui REFUTERAIT la prédiction")
    i.add_argument("--echeance", default=None, help="AAAA-MM-JJ")
    r = sub.add_parser("resoudre")
    r.add_argument("--id", required=True, dest="ident")
    r.add_argument("--verdict", required=True, choices=VERDICTS)
    r.add_argument("--resultat", required=True)
    e = sub.add_parser("etat")
    e.add_argument("--ouvertes", action="store_true")
    n = a.parse_args()
    cmd = vars(n).pop("commande")
    sys.exit({"inscrire": inscrire, "resoudre": resoudre, "etat": etat}[cmd](**vars(n)))
