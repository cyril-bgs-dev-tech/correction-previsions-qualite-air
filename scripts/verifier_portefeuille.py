#!/usr/bin/env python3
"""Les chiffres du portefeuille contre la source unique — le contrôle qui manquait.

Pourquoi ce script existe
---------------------------
Le 20 et le 21/08/2026, cinq défauts de chiffres ont été trouvés dans le portefeuille par des
relectures externes, et aucun par une relecture interne. Ils avaient tous la même signature :
une valeur juste, attachée au mauvais objet ou recopiée depuis un état périmé.

- « 213 M d'enregistrements » — un chiffre qui n'existait dans aucun fichier du projet ;
- « routage par domaine 72,5 » — la valeur de `tuned_dom`, portant le nom du routeur ;
- « 96,2 % » accolé à la promesse « là où personne ne mesure », dont le chiffre est 87,9 % ;
- une figure décomposant sept étages en cinq, sans recalculer les apports ;
- une figure opposant deux protocoles d'évaluation dans la même image.

**La cause n'est pas l'inattention, elle est structurelle**, et elle se mesure :

| cause | mesure du 21/08 |
|---|---|
| les chiffres des figures sont **saisis à la main** | 7 littéraux dans le générateur, **0 lecture d'artefact** |
| **deux pages d'accueil** répètent les mêmes chiffres | chaque chiffre phare vit dans **3 fichiers** |
| le libellé d'échéance est **écrit**, pas dérivé | 10 occurrences à la main dans le seul README |
| **aucun contrôle** ne croise le portefeuille avec la source | 28 contrôles côté dossier, **0** côté portefeuille |

Le dépôt qualité de l'air a `verifier_dossier_candidature.py` et n'a pas connu ce genre de
dérive depuis. Le portefeuille n'avait rien. Ce script comble exactement cet écart.

Ce qu'il vérifie, et ce qu'il ne peut pas vérifier
----------------------------------------------------
Il croise chaque chiffre **déclaré ici** avec `reports/VERITE_DOSSIER.md`, et il contrôle que
les littéraux du générateur de figures y correspondent aussi. Il ne sait pas juger d'un
chiffre qu'on ne lui a pas déclaré : **c'est l'acte de déclarer qui arme le garde-fou**, et il
revient à celui qui écrit — lui seul sait ce qu'il a voulu dire.

Usage : python3 scripts/verifier_portefeuille.py
"""

from __future__ import annotations

import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
PORTEFEUILLE = pathlib.Path.home() / "Portfolio"
VERITE = RACINE / "reports/VERITE_DOSSIER.md"

# Chaque entrée : (le chiffre tel qu'il est publié, ce qu'il désigne, la valeur attendue depuis
# la source, la tolérance). La tolérance absorbe l'arrondi de publication, jamais un écart réel.
ATTENDUS = [
    ("39,6",  "NO₂ · double aveugle J+1 · PARTOUT",              39.61, 0.06),
    ("20,2",  "PM10 · double aveugle J+1 · PARTOUT",             20.23, 0.06),
    ("17,9",  "O₃ · double aveugle J+1 · PARTOUT",               17.90, 0.06),
    ("11,8",  "PM2,5 · double aveugle J+1 · PARTOUT",            11.79, 0.06),
    ("41,4",  "NO₂ · FAIRMODE · CAMS brut",                      41.42, 0.06),
    ("87,9",  "NO₂ · FAIRMODE · corrigé PARTOUT",                87.87, 0.06),
    ("96,2",  "NO₂ · FAIRMODE · corrigé aux stations",           96.15, 0.06),
    ("28,0",  "corpus · millions d'enregistrements",             27.99, 0.06),
    ("438",   "stations effectivement évaluées",               438.00, 0.5),
]

# Les chiffres qui ne se citent JAMAIS seuls. Le défaut du 20/08 n'était pas une proximité
# de mots — c'était une ABSENCE : « 96,2 % » publié sans « 87,9 % », donc le chiffre favorable
# sans celui qui ne franchit pas le seuil.
#
# ⚠️ La première version de ce garde cherchait « 96,2 » à moins de 420 caractères de la phrase
# « là où personne ne mesure ». Éprouvé en réinjectant le défaut réel, il n'a RIEN vu : la
# phrase déclencheuse était plus loin, et un défaut peut s'écrire avec d'autres mots. Un garde
# par proximité de vocabulaire ne tient pas ; un garde par co-présence obligatoire, si.
INSEPARABLES = [
    ("96,2", "87,9",
     "« 96,2 % » est le chiffre AUX STATIONS ; sans « 87,9 % » à côté, la page laisse croire "
     "que le critère est franchi là où rien ne mesure — il ne l'est pas"),
    ("72,8", "source-strict",
     "« 72,8 » n'a de sens qu'avec le nom de son protocole : une autre variante vaut 72,3"),
]

# Les littéraux du générateur de figures, contrôlés contre la même source.
FIGURES_ATTENDUES = {
    "v1_gain_polluants": [39.6, 20.2, 17.9, 11.8],
    "v3_fairmode_no2": [41.4, 87.9, 96.2],
    "v6_pile_no2": [26.6, 35.6, 36.1, 36.4, 38.7, 38.9, 40.2],
}


def _nombres(texte: str) -> set[float]:
    """Décimaux ET entiers de 2 à 4 chiffres.

    La première version ne captait que les décimaux : « 438 stations » était donc porté
    manquant alors qu'il figure bien dans la source. Un contrôle qui ne sait pas lire une
    partie de sa référence rend un faux positif — et un faux positif qu'on prend l'habitude
    d'ignorer vaut un contrôle absent.
    """
    n = {round(float(x.replace(",", ".")), 2)
         for x in re.findall(r"\d{1,3}[.,]\d{1,3}", texte)}
    n |= {float(x) for x in re.findall(r"(?<![\d.,])\d{2,4}(?![\d.,])", texte)}
    return n


def main() -> int:
    if not VERITE.exists():
        print(f"ÉCHEC : {VERITE.relative_to(RACINE)} absent — lancer verite_dossier.py d'abord")
        return 1
    if not PORTEFEUILLE.exists():
        print(f"ÉCHEC : {PORTEFEUILLE} absent")
        return 1

    verite = VERITE.read_text(encoding="utf-8")
    # Le vérificateur du dossier recalcule ses chiffres depuis les artefacts : son rapport est
    # donc une seconde source légitime, et il porte des grandeurs que VERITE_DOSSIER n'expose
    # pas sous forme décimale.
    rapport = RACINE / "reports/VERIFICATION_CANDIDATURE.md"
    ref = _nombres(verite + (rapport.read_text(encoding="utf-8") if rapport.exists() else ""))
    pages = {p: p.read_text(encoding="utf-8")
             for p in sorted(PORTEFEUILLE.rglob("*.md")) + sorted(PORTEFEUILLE.rglob("*.qmd"))
             if ".git" not in p.parts}
    ecarts = 0

    print("── ① Chaque chiffre publié existe-t-il dans la source ? ──")
    for cite, quoi, attendu, tol in ATTENDUS:
        ou = [p.relative_to(PORTEFEUILLE) for p, s in pages.items() if cite in s]
        if not ou:
            continue
        trouve = any(abs(attendu - r) <= tol for r in ref)
        etat = "✓" if trouve else "✗"
        print(f"  {etat} {cite:>6}  {quoi:44s} {len(ou)} page(s)")
        if not trouve:
            print(f"        ⚠️  {attendu} introuvable dans VERITE_DOSSIER")
            ecarts += 1

    print("\n── ② Un chiffre est-il cité sans celui qui le borne ? ──")
    manque_2 = 0
    for cite, compagnon, explication in INSEPARABLES:
        for p, texte in pages.items():
            if cite not in texte:
                continue
            # La SECTION est l'unité de lecture : un lecteur qui parcourt un bloc doit y
            # trouver les deux. Chercher dans la page entière laisserait passer un chiffre
            # borné trois écrans plus bas — ce qui ne borne rien.
            # ⚠️ Le texte alternatif d'une figure contient les mêmes chiffres, et il a fait
            # passer ce garde au vert sur un défaut réel : la borne était dans l'attribut `alt`
            # et non dans la prose. Un lecteur pressé lit la phrase, pas l'attribut — et un
            # lecteur d'écran entend l'alternative SANS la phrase. Les deux doivent porter la
            # borne, donc on contrôle la PROSE, attributs retirés.
            prose = re.sub(r'\b(?:alt|src|srcset|title)="[^"]*"', " ", texte)
            for bloc in re.split(r"\n(?=#{2,4} )", prose):
                if cite in bloc and compagnon.lower() not in bloc.lower():
                    apercu = re.sub(r"\s+", " ", bloc[:90]).strip()
                    print(f"  ✗ {p.relative_to(PORTEFEUILLE)} · « {cite} » sans « {compagnon} »")
                    print(f"        section : {apercu}…")
                    print(f"        ⚠️  {explication}")
                    manque_2 += 1
    ecarts += manque_2
    if not manque_2:
        print("  ✓ chaque chiffre borné est accompagné de sa borne")

    print("\n── ③ Les figures reposent-elles sur les mêmes chiffres que la source ? ──")
    gen = (RACINE / "scripts/figures_portefeuille.py")
    src = gen.read_text(encoding="utf-8") if gen.exists() else ""
    for nom, valeurs in FIGURES_ATTENDUES.items():
        i = src.find(f'"{nom}"')
        bloc = src[i:src.find("))),", i)] if i >= 0 else ""
        dans = _nombres(bloc)
        manquants = [v for v in valeurs if not any(abs(v - d) <= 0.06 for d in dans)]
        hors = [v for v in valeurs if not any(abs(v - r) <= 0.06 for r in ref)]
        etat = "✓" if not manquants and not hors else "✗"
        print(f"  {etat} {nom:24s} {len(valeurs)} valeurs")
        if manquants:
            print(f"        ⚠️  absentes du générateur : {manquants}")
            ecarts += 1
        if hors:
            print(f"        ⚠️  absentes de VERITE_DOSSIER : {hors}")
            ecarts += 1

    print("\n── ④ Un même fait porte-t-il deux valeurs selon la page ? ──")
    for cite, quoi, _, _ in ATTENDUS:
        pages_ou = {p.relative_to(PORTEFEUILLE) for p, s in pages.items() if cite in s}
        if len(pages_ou) > 1:
            print(f"  · {cite:>6} répété sur {len(pages_ou)} pages — {quoi}")
    print("  (répétition ≠ défaut, mais chaque répétition est une occasion de diverger)")

    print("\n" + "─" * 76)
    if ecarts:
        print(f"❌ {ecarts} écart(s) — le portefeuille et la source ne disent pas la même chose.")
        return 1
    print("✅ Portefeuille et source unique concordent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
