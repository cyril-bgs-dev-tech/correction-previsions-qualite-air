#!/usr/bin/env python3
"""Valide les fiches de contexte départemental contre le brief qui les a commandées.

Ce script remplace les trois validateurs ad hoc qui vivaient dans `tmp/`, chacun avec
sa liste de codes recopiée à la main — exactement le motif que CLAUDE.md § 2 bis
interdit (« un contrôle ad hoc à chaque script, qui est justement la façon dont les
trois défauts sont nés »).

Deux principes le gouvernent :

  · **L'attendu vient de la demande** (§ 4). Les 84 codes ne sont pas écrits ici : ils
    sont lus dans `docs/PROMPT_GPT_DEPARTEMENTS.md`, le document envoyé au rédacteur.
    Si le brief change, le contrôle suit ; si quelqu'un recopie mal une liste, le
    contrôle le voit.
  · **On ne compare jamais un compte à un compte** (§ 4). Les codes manquants et les
    codes en trop sont NOMMÉS un par un, jamais résumés par « 82 sur 84 ».

Usage :
    python3 scripts/valider_departements.py            # valide tout ce qui existe
    python3 scripts/valider_departements.py --complet  # exige les 84, échoue sinon
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
BRIEF = RACINE / "docs" / "PROMPT_GPT_DEPARTEMENTS.md"
LOTS = RACINE / "docs" / "departements"

CLES_ATTENDUES = [
    "code", "nom", "region", "resume", "sources_dominantes", "topographie_climat",
    "regime_episodes", "transport_longue_distance", "cadre_decision",
    "pieges_modelisation", "sans_source",
]
POLLUANTS = {"NO2", "O3", "PM10", "PM2.5", "SO2", "NH3", "COV", "benzene"}
EFFETS = {"dispersif", "piegeant", "mixte"}
SAISONS = {"hiver", "printemps", "ete", "automne", "toute_annee"}
CONFIANCES = {"haute", "moyenne", "basse"}

# Structure de chaque champ : (clés exigées, est-ce une liste ?)
FORME = {
    "sources_dominantes": (("libelle", "polluants", "confiance", "source"), True),
    "topographie_climat": (("libelle", "effet", "vents_nommes", "confiance", "source"), False),
    "regime_episodes": (("saison", "polluant", "mecanisme", "confiance", "source"), True),
    "transport_longue_distance": (("origine", "polluant", "regime", "confiance", "source"), True),
    "cadre_decision": (("ppa", "zfe", "contentieux_no2", "confiance", "source"), False),
    "pieges_modelisation": (("libelle", "confiance", "speculatif"), True),
}
# Les champs courts n'ont pas le droit aux accents (contrainte d'ingestion du brief) ;
# `libelle`, `resume` et `mecanisme` sont du texte affiché et y ont droit.
CHAMPS_SANS_ACCENT = {
    "nom", "region", "effet", "saison", "polluant", "origine", "regime",
    "confiance", "ppa", "zfe",
}


def codes_du_brief() -> list[str]:
    """Lit la liste canonique des départements dans la § 7 du brief.

    Les codes y sont dans des lignes de citation (`> `), sous trois formes — gras
    `**30** Gard`, ou nu `01 Ain`. Rien d'autre dans le fichier n'est lu : la liste
    des douze exclus, elle, est en texte courant et ne doit surtout pas être captée.
    """
    texte = BRIEF.read_text(encoding="utf-8")
    section = re.search(r"^## 7\..*?(?=^## 8\.)", texte, re.S | re.M)
    if not section:
        raise SystemExit(f"§ 7 introuvable dans {BRIEF} — le brief a changé de structure")

    codes: list[str] = []
    for ligne in section.group(0).splitlines():
        if not ligne.startswith(">"):
            continue
        for item in ligne.lstrip("> ").replace("**", "").split("·"):
            jeton = item.strip().split(" ")[0]
            if re.fullmatch(r"\d{2}|2[AB]", jeton):
                codes.append(jeton)

    doublons = [c for c in codes if codes.count(c) > 1]
    if doublons:
        raise SystemExit(f"le brief lui-même liste deux fois : {sorted(set(doublons))}")
    return codes


def a_un_accent(valeur: str) -> bool:
    return any(unicodedata.combining(c) for c in unicodedata.normalize("NFD", valeur))


def controler_source(source: object, ou: str, erreurs: list[str]) -> None:
    """Une source doit nommer un document daté et pointer une URL ouvrable."""
    if not isinstance(source, str) or not source.strip():
        erreurs.append(f"{ou} : source absente ou vide")
        return
    if "https://" not in source and "http://" not in source:
        erreurs.append(f"{ou} : source sans URL — {source[:70]}")
    if not re.search(r"\b(?:19|20)\d{2}\b", source):
        erreurs.append(f"{ou} : source sans date — {source[:70]}")


def controler_item(item: object, champ: str, cles: tuple[str, ...], ou: str,
                   erreurs: list[str]) -> None:
    if not isinstance(item, dict):
        erreurs.append(f"{ou} : {champ} n'est pas un bloc de clés")
        return
    if tuple(item.keys()) != cles:
        erreurs.append(f"{ou} : clés de {champ} = {tuple(item.keys())}, attendu {cles}")
        return

    for cle, valeur in item.items():
        if cle in CHAMPS_SANS_ACCENT and isinstance(valeur, str) and a_un_accent(valeur):
            erreurs.append(f"{ou} : accent interdit dans {champ}.{cle} = {valeur!r}")

    if "confiance" in item and item["confiance"] not in CONFIANCES:
        erreurs.append(f"{ou} : confiance invalide {item['confiance']!r} dans {champ}")
    if "source" in item:
        controler_source(item["source"], f"{ou}/{champ}", erreurs)
    if "polluants" in item:
        if not isinstance(item["polluants"], list) or not item["polluants"]:
            erreurs.append(f"{ou} : polluants doit être une liste non vide")
        else:
            for p in item["polluants"]:
                if p not in POLLUANTS:
                    erreurs.append(f"{ou} : polluant invalide {p!r}")
    if "polluant" in item and item["polluant"] not in POLLUANTS:
        erreurs.append(f"{ou} : polluant invalide {item['polluant']!r}")
    if "effet" in item and item["effet"] not in EFFETS:
        erreurs.append(f"{ou} : effet invalide {item['effet']!r}")
    if "saison" in item and item["saison"] not in SAISONS:
        erreurs.append(f"{ou} : saison invalide {item['saison']!r}")
    if "contentieux_no2" in item and not isinstance(item["contentieux_no2"], bool):
        erreurs.append(f"{ou} : contentieux_no2 doit être un booléen")
    if "speculatif" in item and not isinstance(item["speculatif"], bool):
        erreurs.append(f"{ou} : speculatif doit être un booléen")


def controler_bloc(bloc: object, fichier: str, rang: int, erreurs: list[str]) -> str | None:
    ou = f"{fichier}#{rang}"
    if not isinstance(bloc, dict):
        erreurs.append(f"{ou} : le bloc n'est pas un dictionnaire")
        return None
    if list(bloc.keys()) != CLES_ATTENDUES:
        erreurs.append(f"{ou} : clés de tête = {list(bloc.keys())}")
        return None

    code = bloc["code"]
    if not isinstance(code, str) or not re.fullmatch(r"\d{2}|2[AB]", code):
        erreurs.append(f"{ou} : code {code!r} — attendu une chaîne \"01\"…\"95\", \"2A\", \"2B\"")
        return None
    ou = f"{code}"

    for cle in ("nom", "region"):
        if not isinstance(bloc[cle], str) or not bloc[cle].strip():
            erreurs.append(f"{ou} : {cle} vide")
        elif a_un_accent(bloc[cle]):
            erreurs.append(f"{ou} : accent interdit dans {cle} = {bloc[cle]!r}")

    mots = re.findall(r"[\wÀ-ÿ]+(?:['-][\wÀ-ÿ]+)*", bloc["resume"] or "")
    if not mots:
        erreurs.append(f"{ou} : resume vide")
    elif len(mots) > 25:
        erreurs.append(f"{ou} : resume de {len(mots)} mots (25 au plus)")

    for champ, (cles, est_liste) in FORME.items():
        valeur = bloc[champ]
        if valeur is None:
            continue
        if est_liste:
            if not isinstance(valeur, list) or not valeur:
                erreurs.append(f"{ou} : {champ} doit être une liste non vide ou null")
                continue
            for item in valeur:
                controler_item(item, champ, cles, ou, erreurs)
        else:
            controler_item(valeur, champ, cles, ou, erreurs)

    sans_source = bloc["sans_source"]
    if sans_source is not None and not (
        isinstance(sans_source, list) and all(isinstance(s, str) for s in sans_source)
    ):
        erreurs.append(f"{ou} : sans_source doit être null ou une liste de phrases")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complet", action="store_true",
                        help="exiger les 84 départements du brief, pas seulement les lots livrés")
    args = parser.parse_args()

    attendus = codes_du_brief()
    fichiers = sorted(LOTS.glob("lot*.yaml"))
    if not fichiers:
        print(f"aucun lot dans {LOTS}")
        return 1

    erreurs: list[str] = []
    livres: list[str] = []
    par_fichier: dict[str, list[str]] = {}

    for fichier in fichiers:
        brut = fichier.read_text(encoding="utf-8")
        for numero, ligne in enumerate(brut.splitlines(), 1):
            if "[]" in ligne:
                erreurs.append(f"{fichier.name}:{numero} : liste vide `[]` — écrire `null`")
            nu = ligne.rstrip()
            if nu and not nu.lstrip().startswith("#"):
                indentation = len(nu) - len(nu.lstrip(" "))
                if indentation % 2:
                    erreurs.append(f"{fichier.name}:{numero} : indentation impaire")
        try:
            blocs = yaml.safe_load(brut)
        except yaml.YAMLError as erreur:
            erreurs.append(f"{fichier.name} : YAML illisible — {str(erreur)[:120]}")
            continue
        if not isinstance(blocs, list):
            erreurs.append(f"{fichier.name} : le fichier doit contenir une liste de blocs")
            continue

        codes = []
        for rang, bloc in enumerate(blocs, 1):
            code = controler_bloc(bloc, fichier.name, rang, erreurs)
            if code:
                codes.append(code)
        par_fichier[fichier.name] = codes
        livres.extend(codes)

    # ── Couverture : les codes sont nommés, jamais comptés (§ 4) ──────────────
    vus: dict[str, str] = {}
    for nom, codes in par_fichier.items():
        for code in codes:
            if code in vus:
                erreurs.append(f"{code} : livré deux fois — {vus[code]} et {nom}")
            vus[code] = nom
    hors_brief = [c for c in livres if c not in attendus]
    if hors_brief:
        erreurs.append(f"codes absents du brief : {sorted(set(hors_brief))}")
    manquants = [c for c in attendus if c not in vus]

    ordre_attendu = [c for c in attendus if c in vus]
    if livres != ordre_attendu:
        erreurs.append("l'ordre des blocs ne suit pas celui du brief")

    print(f"brief    : {len(attendus)} départements demandés")
    print(f"livrés   : {len(livres)} en {len(par_fichier)} lots")
    for nom, codes in par_fichier.items():
        print(f"  {nom:<12} {' '.join(codes)}")
    if manquants:
        print(f"manquants ({len(manquants)}) : {' '.join(manquants)}")

    if args.complet and manquants:
        erreurs.append(f"{len(manquants)} départements manquants : {' '.join(manquants)}")

    if erreurs:
        print(f"\nÉCHEC — {len(erreurs)} anomalies")
        for erreur in erreurs:
            print(f"  - {erreur}")
        return 1

    print("\nOK — schéma, énumérations, sources datées et sourcées, ordre du brief respecté")
    return 0


if __name__ == "__main__":
    sys.exit(main())
