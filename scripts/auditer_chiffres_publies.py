#!/usr/bin/env python3
"""Les chiffres de TÊTE publiés sont-ils ceux du contrat de produit ?

Ce que ce script vérifie, et pourquoi si étroitement
-----------------------------------------------------
Premier essai, 25/08 : comparer **tout** pourcentage publié à **toute** valeur numérique de
`verite_dossier.csv`. Inutilisable, et faux dans les DEUX sens —

* « 0,00 % » d'une heatmap ressortait *dépassé* parce qu'une colonne d'ablation valait zéro ;
* et « +39,61 % », qui EST un chiffre de tête périmé, ressortait *appuyé* parce que 39,61
  figurait une fois dans une colonne `relatif_pct` sans rapport.

> **Apparier des nombres nus contre un large tableau produit des coïncidences dans les deux
> sens.** Un contrôle mal posé coûte autant que l'absence de contrôle (§ 2 bis).

Ce script ne regarde donc qu'une chose, nommément : **les valeurs qui ont été, à un moment,
« le » chiffre du dossier.** Elles sont peu nombreuses, elles portent deux décimales, et leur
présence dans une pièce publiée est un fait, pas une coïncidence.

Usage : python3 scripts/auditer_chiffres_publies.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]

# ── Les chiffres de tête PÉRIMÉS, nommés un par un ──────────────────────────────────────
# Chacun a été « le » gain du dossier à une date. Aucun n'est faux : chacun est exact sur sa
# pile et sa fenêtre. Ils ne sont plus publiables **seuls**, parce que le lecteur les prend
# pour le chiffre du produit.
PERIMES = {
    "39,61": "NO₂ PARTOUT · pile du 17/08, avant correction du prétraitement et du corpus",
    "45,71": "NO₂ AUX STATIONS · idem",
    "17,90": "O₃ PARTOUT · idem",
    "24,05": "O₃ AUX STATIONS · idem",
    "41,52": "NO₂ PARTOUT · pile bornée par GEOS-CF, 29 mois",
    "20,51": "O₃ PARTOUT · idem",
    "21,36": "PM10 PARTOUT · idem, 24 mois",
    "13,96": "PM2,5 PARTOUT · idem",
}
ENTITES = {"&#8239;": " ", "&#160;": " ", "&nbsp;": " ", "&#x202f;": " ",
           " ": " ", " ": " "}
BALISE = re.compile(r"<[^>]+>")


def pieces() -> list[Path]:
    """Les pièces publiées, lues sur le DISQUE — jamais via git ni le `grep` de session :
    `reports/figures/*.html` est dans `.gitignore`, et une recherche qui les saute rend un
    zéro indiscernable d'un zéro de non-occurrence (§ 4 bis)."""
    fs = sorted((RACINE / "reports/figures").glob("*.html"))
    # 🔴 Le périmètre ne couvrait que `reports/figures` — 25/08/2026.
    #
    # Il rendait « zéro chiffre périmé » pendant que `README.md`, la première page que voit
    # quiconque ouvre le dépôt, publiait encore +39,6 %. Un contrôle dont la CIBLE n'est pas
    # ce qu'on publie rend un zéro de non-lecture (§ 4 bis) — le même défaut que
    # `render_check.py` visant un fichier du 02/08 pendant qu'on en modifiait un autre.
    #
    # Toute pièce lue par un tiers entre ici. La liste est explicite plutôt que globale : un
    # glob attraperait les brouillons et noierait le verdict.
    for n in ("README.md", "LIVRABLE.md", "presentation_atmo.html",
              "NOTE_ATMO_OCCITANIE.md", "docs/BESOINS_ATMO_OCCITANIE_2025.md",
              "reports/matrice_predictions_2026/README.md",
              "reports/CONTRAT_PRODUIT.md", "reports/VERITE_DOSSIER.md"):
        if (RACINE / n).exists():
            fs.append(RACINE / n)
    return fs


def actuels() -> dict[str, str]:
    """Les chiffres de tête d'AUJOURD'HUI, lus dans la source unique — jamais recopiés."""
    f = RACINE / "reports/verite_dossier.csv"
    if not f.exists():
        raise SystemExit("⛔ reports/verite_dossier.csv absent — lancer verite_dossier.py")
    t = pd.read_csv(f)
    m = t[(t["bloc"].astype(str).str.startswith("socle"))
          & (t["grain"].astype(str).str.contains("MAXIMALE"))]
    if m.empty:
        raise SystemExit("⛔ aucune ligne « socle » dans la source — le bloc 0 bis manque-t-il ?")
    return {f"{r['gain']:.2f}".replace(".", ","): f"{r['bloc']} · {r['polluant']}"
            for _, r in m.iterrows()}


def main() -> int:
    courants, trouves, pistes, ok = actuels(), [], [], []
    fs = pieces()
    for f in fs:
        texte = f.read_text(errors="ignore")
        for a, b in ENTITES.items():
            texte = texte.replace(a, b)
        for val, origine in PERIMES.items():
            # 🔴 Le même chiffre périmé s'écrit aussi ARRONDI — 25/08/2026.
            # `README.md`, première page du dépôt, publie « +39,6 % » quand le motif exigeait
            # deux décimales. Un chiffre de tête reste un chiffre de tête quand on lui retire
            # une décimale : on cherche les deux formes.
            # ⚠️ La forme ARRONDIE élargit le filet — et elle coïncide. « +14,0 % » de
            # `LIVRABLE.md` est le résultat d'un partage des jours à la médiane, sans rapport
            # avec le 13,96 de la pile dépassée. Les deux formes sont donc rapportées
            # SÉPARÉMENT : l'exacte est un fait, l'arrondie est une piste à regarder.
            # Les mêler produirait un contrôle qui crie au loup, et on cesserait de le lire.
            arrondi = f"{round(float(val.replace(',', '.')), 1):.1f}".replace(".", ",")
            for motif, sur in ((re.escape(val), True), (re.escape(arrondi), False)):
                for m in re.finditer(motif + r"\s*%", texte):
                    brut = BALISE.sub(" ", texte[max(0, m.start() - 70):m.start() + 30])
                    ctx = re.sub(r"\s+", " ", brut).strip()
                    (trouves if sur else pistes).append((f, val, origine, ctx))
        for val, quoi in courants.items():
            if re.search(re.escape(val) + r"\s*%", texte):
                ok.append((f.name, val, quoi))

    print(f"CHIFFRES DE TÊTE · {len(fs)} pièce(s) publiée(s)")
    print("═" * 100)
    print("\nLe contrat de produit publie : "
          + " · ".join(f"{v} % ({q.split('·')[-1].strip()})" for v, q in courants.items()))
    if trouves:
        print(f"\n🔴 {len(trouves)} occurrence(s) d'un chiffre de tête PÉRIMÉ :\n")
        for f, val, origine, ctx in trouves:
            print(f"  {val} %  ·  {f.relative_to(RACINE)}")
            print(f"      {origine}")
            print(f"      « …{ctx}… »")
    else:
        print("\n✅ aucun chiffre de tête périmé dans les pièces publiées")
    if pistes:
        print(f"\n🟠 {len(pistes)} forme(s) ARRONDIE(S) d'un chiffre périmé — à regarder, "
              f"pas à corriger d'office :\n")
        for f, val, _o, ctx in pistes:
            print(f"  ~{val} %  ·  {f.relative_to(RACINE)}")
            print(f"      « …{ctx[-88:]}… »")
    if ok:
        print(f"\n✅ {len(ok)} présence(s) d'un chiffre COURANT : "
              + ", ".join(f"{v} % dans {n}" for n, v, _ in ok[:6]))
    else:
        print("\n🟠 aucun chiffre du contrat de produit n'apparaît dans les pièces — "
              "elles n'ont pas encore été régénérées.")
    return 1 if trouves else 0


if __name__ == "__main__":
    sys.exit(main())
