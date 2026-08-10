#!/usr/bin/env python3
"""Exporte une page du dossier en PDF — la pièce jointe qui ne dépend d'aucun service.

Pourquoi ce script existe
---------------------------
`presentation_atmo.pdf` était produit **à la main**, hors dépôt. Conséquence mesurée le
10/08/2026 : la page HTML a été régénérée trois fois dans la soirée, le PDF datait de la
veille, et rien ne le signalait — un artefact périmé ne se distingue pas d'un artefact
complet (`CLAUDE.md` § 4, et [[regenerer-peut-degrader]]). Une étape de livraison qui n'est
pas un script est une étape qu'on oubliera.

Le contrôle de fin porte sur l'artefact, jamais sur le code de sortie : le PDF est rouvert,
son nombre de pages est compté et comparé au plancher attendu. Un PDF d'une page est un
échec de rendu, pas une livraison.

Usage : python3 scripts/exporter_pdf.py [page.html] [--pages-min 40]
"""

from __future__ import annotations

import argparse
import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
FIG = RACINE / "reports/figures"


def exporter(source: pathlib.Path, cible: pathlib.Path, pages_min: int) -> int:
    from playwright.sync_api import sync_playwright

    erreurs: list[str] = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1120, "height": 1400}, color_scheme="light")
        pg.on("pageerror", lambda e: erreurs.append(str(e)))
        pg.goto(f"file://{source}")
        pg.wait_for_timeout(1800)          # laisser les <details> et les scripts se poser
        pg.emulate_media(media="print")
        pg.pdf(path=str(cible), format="A4", print_background=True,
               margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"})
        pg.close()
        b.close()

    if not cible.exists():
        print(f"AUCUN fichier écrit : {cible}")
        return 1
    # Compter les pages sans dépendance : le nombre d'objets /Type /Page du PDF.
    brut = cible.read_bytes()
    pages = brut.count(b"/Type /Page") - brut.count(b"/Type /Pages")
    print(f"Écrit : {cible.relative_to(RACINE)} · {len(brut) / 1024:.0f} ko · "
          f"{pages} pages" + (f" · erreurs de console : {erreurs}" if erreurs else ""))
    if pages < pages_min:
        print(f"ÉCHEC : {pages} pages pour un plancher de {pages_min} — rendu incomplet")
        return 1
    return 1 if erreurs else 0


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("page", nargs="?", default="presentation_atmo.html")
    a.add_argument("--pages-min", type=int, default=40,
                   help="plancher de pages attendu ; le dossier en faisait 53 le 09/08")
    n = a.parse_args()
    source = FIG / n.page
    if not source.exists():
        print(f"introuvable : {source}")
        return 1
    return exporter(source, source.with_suffix(".pdf"), n.pages_min)


if __name__ == "__main__":
    sys.exit(main())
