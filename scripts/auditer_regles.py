#!/usr/bin/env python3
"""Audite `CLAUDE.md` — les règles se contredisent-elles, se répètent-elles, grossissent-elles ?

Pourquoi ce script existe
--------------------------
Le § 0 pose une méta-règle : *« une règle violée deux fois devient du code, ou elle
disparaît »*, et son corollaire *« CLAUDE.md doit RÉTRÉCIR à mesure que le code
grossit »*. Le fichier est passé de **440 lignes le 03/08 à 1 181 le 16/08** — dont
+119 dans la seule soirée où j'ai écrit la méta-règle. Une règle que son propre auteur
enfreint le jour où il l'écrit n'est pas une règle, c'est un vœu.

Ce que l'audit contrôle, et pourquoi chacun
--------------------------------------------
1. **Leçons dupliquées.** Trois sections disent « un nom ment » (fichier, axe, colonne) ;
   deux disent « le contrôle porte sur l'artefact » ; deux disent « une mesure ne suffit
   pas ». Une leçon en trois endroits, c'est trois endroits à retrouver au moment
   d'agir — or le § 0 a établi que **le facteur limitant est l'instant d'application**,
   pas la connaissance.
2. **Renvois périmés.** Le § 5 s'intitule « ce qui relie ces **cinq** règles » alors que
   le fichier en compte seize sections et huit lettres. Un renvoi faux est une étiquette
   qui ment (§ 0, règle H) appliquée au document lui-même.
3. **Croissance non soldée.** Toute règle ajoutée doit nommer ce qu'elle remplace, ou
   dire pourquoi rien ne peut l'être.

⚠️ **Ce que cet audit NE fait PAS.** Il est lexical : il repère des formulations proches,
pas des idées contradictoires. Il ne remplace pas une relecture — il dit *où regarder*.
Le prendre pour un juge serait exactement le défaut qu'il traque.

Usage : python3 scripts/auditer_regles.py [--fichier CLAUDE.md]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# Les leçons qui ont déjà essaimé. Chaque entrée : (nom, motifs qui la trahissent).
# Liste FERMÉE : ouverte, elle laisserait passer la prochaine duplication, et un contrôle
# qui ne peut pas échouer ne protège de rien.
LECONS = {
    "un nom ment": (r"n'est pas une source de vérité", r"n'est pas ce que son nom annonce",
                    r"porte un RÔLE, jamais une identité", r"étiquette.{0,20}ment"),
    "contrôler l'artefact, pas le code de sortie": (
        r"porte sur l'\*\*artefact", r"jamais sur le code de sortie",
        r"code de sortie appartient"),
    "une mesure ne fait pas une propriété": (
        r"n'est pas une propriété", r"[Dd]eux essais ne font pas",
        r"deux sous-ensembles indépendants", r"pas d'une passe unitaire"),
    "la concurrence dépend de la ressource": (
        r"concurrence n'est pas la réponse par défaut",
        r"[Uu]ne file par RESSOURCE", r"sérialiser dedans, paralléliser entre"),
    "un seuil dérivé, jamais constant": (
        r"seuil se recalcule", r"cadence \*\*mesurée\*\*", r"jamais sur une intuition"),
}


def sections(texte: str) -> list[tuple[int, str]]:
    return [(i, l) for i, l in enumerate(texte.splitlines(), 1) if l.startswith("## ")]


def main(fichier: str) -> int:
    chemin = RACINE / fichier
    if not chemin.exists():
        raise SystemExit(f"❌ absent : {chemin}")
    texte = chemin.read_text(encoding="utf-8")
    lignes = texte.splitlines()
    secs = sections(texte)
    print(f"{fichier} · {len(lignes)} lignes · {len(secs)} sections\n")

    # ── ① Leçons dispersées ────────────────────────────────────────────────────────────
    print("① LEÇONS DISPERSÉES — une leçon devrait vivre à UN endroit")
    total_disperse = 0
    for lecon, motifs in LECONS.items():
        vus: dict[str, list[int]] = {}
        for i, l in enumerate(lignes, 1):
            for m in motifs:
                if re.search(m, l):
                    sec = next((s for n, s in reversed(secs) if n <= i), "?")
                    vus.setdefault(sec.strip("# ").split(".")[0], []).append(i)
        if len(vus) > 1:
            total_disperse += 1
            print(f"   ⚠️ « {lecon} » dans {len(vus)} sections : "
                  f"{', '.join(f'§ {k} (l.{v[0]})' for k, v in vus.items())}")
    if not total_disperse:
        print("   ✅ aucune leçon dispersée")

    # ── ② Renvois numériques périmés ───────────────────────────────────────────────────
    print("\n② RENVOIS PÉRIMÉS")
    mots = {"deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8}
    n_sec, n_lettres = len(secs), len(re.findall(r"^\| \*\*[A-Z]\*\* \|", texte, re.M))
    faux = []
    for i, l in enumerate(lignes, 1):
        for mot, val in mots.items():
            if re.search(rf"ces {mot} règles", l) and val not in (n_sec, n_lettres):
                faux.append(f"l.{i} « ces {mot} règles » — or {n_sec} sections, "
                            f"{n_lettres} règles lettrées")
    print("   " + ("\n   ".join(faux) if faux else "✅ aucun renvoi numérique faux"))

    # ── ③ Croissance ───────────────────────────────────────────────────────────────────
    print("\n③ CROISSANCE")
    import subprocess
    try:
        anciens = subprocess.run(
            ["git", "log", "--format=%ad|%H", "--date=short", "--", fichier],
            cwd=RACINE, capture_output=True, text=True, timeout=30).stdout.splitlines()
        if anciens:
            d, h = anciens[-1].split("|")
            n0 = len(subprocess.run(["git", "show", f"{h}:{fichier}"], cwd=RACINE,
                                    capture_output=True, text=True).stdout.splitlines())
            croiss = 100 * (len(lignes) - n0) / max(n0, 1)
            print(f"   {n0} lignes le {d} → {len(lignes)} aujourd'hui  ({croiss:+.0f} %)")
            if croiss > 0:
                print("   ⚠️ le fichier GROSSIT. La méta-règle du § 0 demande l'inverse :")
                print("      toute règle ajoutée nomme ce qu'elle remplace, ou dit "
                      "pourquoi rien ne peut l'être.")
    except Exception as e:  # noqa: BLE001
        print(f"   (historique indisponible : {type(e).__name__})")

    print(f"\n{'─' * 78}\n⚠️ Audit LEXICAL : il dit où regarder, il ne juge pas. "
          f"Une duplication\n   peut être un rappel délibéré — mais elle doit alors être "
          f"un RENVOI, pas une\n   réénonciation.")
    return 1 if (total_disperse or faux) else 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--fichier", default="CLAUDE.md")
    n = a.parse_args()
    raise SystemExit(main(n.fichier))
