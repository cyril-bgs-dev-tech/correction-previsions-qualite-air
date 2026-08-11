#!/usr/bin/env python3
"""Injecte les pages 00, 04, 05 et 06 dans `presentation_atmo.html`, entre sentinelles.

Pourquoi un injecteur plutôt qu'une édition à la main
--------------------------------------------------------
`presentation_atmo.html` est écrite à la main — il n'y a pas de générateur pour la page
entière, et il n'en faut pas : sa valeur est dans sa rédaction. Mais la page 04 porte
**281 ko de données mesurées** qui doivent pouvoir être régénérées sans retoucher une
ligne de prose. D'où ce découpage : la prose et le style vivent dans des fragments, les
données dans un JSON, et cet injecteur recolle le tout **entre deux sentinelles**.

Relancer l'injection est donc sans effet de bord : le contenu entre sentinelles est
remplacé, jamais empilé. C'est ce qui permet de régénérer après une nouvelle mesure.

Usage : python3 scripts/injecter_pages.py   (toutes les pages, à chaque fois)
"""

from __future__ import annotations

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PAGE = RACINE / "reports/figures/presentation_atmo.html"
FIG = RACINE / "reports/figures"

# Chaque page déclare où elle se pose : la 00 est une porte d'entrée, elle passe donc
# AVANT la page 01 — dans le corps comme dans le sommaire. Les autres s'ajoutent à la fin.
PAGES_INJECTEES = [
    {"prefixe": "p0", "ident": "synthese", "libelle": "00 · Synthèse",
     "ancre_section": '<section class="page" id="sources">',
     "ancre_nav": '<a href="#sources">01 · Sources</a>', "avant": True},
    {"prefixe": "p4", "ident": "resultats", "libelle": "04 · Résultats",
     "ancre_section": "</main>",
     "ancre_nav": '<a href="#architecture">03 · Architecture</a>', "avant": False},
    {"prefixe": "p5", "ident": "seuils", "libelle": "05 · Déclenchement",
     "ancre_section": "</main>",
     "ancre_nav": '<a href="#resultats">04 · Résultats</a>', "avant": False},
    {"prefixe": "p6", "ident": "decision", "libelle": "06 · Décision réelle",
     "ancre_section": "</main>",
     "ancre_nav": '<a href="#seuils">05 · Déclenchement</a>', "avant": False},
    {"prefixe": "p7", "ident": "prevair", "libelle": "07 · Barre réelle",
     "ancre_section": "</main>",
     "ancre_nav": '<a href="#decision">06 · Décision réelle</a>', "avant": False},
    {"prefixe": "p8", "ident": "degradees", "libelle": "08 · La limite",
     "ancre_section": "</main>",
     "ancre_nav": '<a href="#prevair">07 · Barre réelle</a>', "avant": False},
]


def poser(page: str, nom: str, contenu: str, ancre: str | None) -> str:
    """Remplace le bloc entre sentinelles, ou le crée à l'ancre. Jamais d'empilement."""
    debut, fin = f"<!-- {nom}:DEBUT -->", f"<!-- {nom}:FIN -->"
    bloc = f"{debut}\n{contenu}\n{fin}"
    if debut in page and fin in page:
        i, j = page.index(debut), page.index(fin) + len(fin)
        return page[:i] + bloc + page[j:]
    if ancre is None:
        return page.rstrip() + "\n\n" + bloc + "\n"
    if ancre not in page:
        raise SystemExit(f"ancre « {ancre} » introuvable — injection annulée")
    i = page.index(ancre)
    return page[:i] + bloc + "\n" + page[i:]


def coherence() -> None:
    """Les deux pages doivent décrire le MÊME état des artefacts.

    Sinon on publie une page 04 sur un ozone à 25 mois et une page 05 sur le même ozone
    à 35 mois — chacune juste, les deux incohérentes. C'est arrivé le 05/08, parce qu'un
    lot de régénération tournait pendant la génération des pages.
    """
    import json
    emp = {}
    for pg in PAGES_INJECTEES:
        f = FIG / f"{pg['prefixe']}_donnees.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for p, b in d.get("polluants", {}).items():
            if "empreinte" in b:
                emp.setdefault(p, {})[pg["prefixe"]] = b["empreinte"]
    divergents = {p: v for p, v in emp.items() if len({tuple(sorted(x.items()))
                                                       for x in v.values()}) > 1}
    if divergents:
        raise SystemExit(
            "ARTEFACTS DIVERGENTS entre les pages — régénérer les deux d'un coup :\n  "
            + "\n  ".join(f"{p} : " + " · ".join(f"{k}={v['octets']}o"
                                                 for k, v in sorted(d.items()))
                          for p, d in divergents.items()))
    if emp:
        print(f"cohérence : {len(emp)} polluants, même artefact dans toutes les pages")


def main() -> int:
    coherence()
    page = PAGE.read_text(encoding="utf-8")
    avant = len(page)

    for pg in PAGES_INJECTEES:
        prefixe, ident = pg["prefixe"], pg["ident"]
        frags = {k: FIG / f"_{prefixe}_{k}" for k in ("section.html", "style.css", "script.js")}
        frags["donnees"] = FIG / f"{prefixe}_donnees.json"
        manquants = [f.name for f in frags.values() if not f.exists()]
        if manquants:
            raise SystemExit(f"fragments manquants pour {prefixe} : {manquants} — "
                             f"lancer d'abord le script de données correspondant")
        maj = prefixe.upper()
        page = poser(page, f"{maj}-STYLE",
                     "<style>\n" + frags["style.css"].read_text(encoding="utf-8") + "</style>",
                     "</main>")
        page = poser(page, f"{maj}-SECTION",
                     frags["section.html"].read_text(encoding="utf-8"), pg["ancre_section"])
        page = poser(page, f"{maj}-SCRIPT",
                     f'<script id="{prefixe}-data" type="application/json">'
                     + frags["donnees"].read_text(encoding="utf-8") + "</script>\n"
                     + "<script>\n" + frags["script.js"].read_text(encoding="utf-8")
                     + "</script>", None)

        # Le sommaire : une entrée, une seule, même après plusieurs injections
        lien = f'<a href="#{ident}">{pg["libelle"]}</a>'
        if lien not in page:
            a = pg["ancre_nav"]
            if a not in page:
                raise SystemExit(f"entrée « {a} » introuvable dans le sommaire")
            page = page.replace(a, (lien + "\n      " + a) if pg["avant"]
                                else (a + "\n      " + lien), 1)

    PAGE.write_text(page, encoding="utf-8")

    # Contrôle : chaque sentinelle exactement une fois, chaque section exactement une fois
    for pg in PAGES_INJECTEES:
        prefixe, ident = pg["prefixe"], pg["ident"]
        for suffixe in ("STYLE", "SECTION", "SCRIPT"):
            nom = f"{prefixe.upper()}-{suffixe}"
            n = page.count(f"<!-- {nom}:DEBUT -->")
            if n != 1:
                raise SystemExit(f"sentinelle {nom} présente {n} fois — page à vérifier")
        if page.count(f'id="{ident}"') != 1:
            raise SystemExit(f"section « {ident} » présente {page.count(chr(34))} fois")
    print(f"Injecté dans {PAGE.relative_to(RACINE)} : "
          f"{avant / 1024:.0f} ko → {len(page) / 1024:.0f} ko · "
          f"{page.count('<section class=' + chr(34) + 'page')} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
