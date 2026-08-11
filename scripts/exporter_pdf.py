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

Et le contrôle que ce plancher NE PEUT PAS faire — mesuré le 11/08/2026
------------------------------------------------------------------------
Ajouter la page 07 a fait passer le PDF de **54 à 49 pages**. Rien n'a été perdu : le
document entier a été rendu à l'échelle **0,90**, corps de texte de 9,75 pt tombé à
8,75 pt. Cause : la 8ᵉ entrée du sommaire portait la largeur de mise en page à **772 px**
pour **718 px** imprimables (A4 moins les marges), et Chromium **réduit tout le document**
plutôt que de couper. Un plancher de pages ne verra jamais cela — il compte des pages,
et le défaut en produit **moins**, donc plus loin du plancher, tout en s'aggravant.

Le contrôle qui l'attrape est en amont du PDF : mesurer la largeur de mise en page **à la
largeur imprimable** et refuser tout débordement, en NOMMANT l'élément qui déborde (une
mesure qui dit « ça déborde » sans dire « où » envoie chercher au hasard).

Usage : python3 scripts/exporter_pdf.py [page.html] [--pages-min 40]
"""

from __future__ import annotations

import argparse
import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
FIG = RACINE / "reports/figures"

# A4 (210 mm) moins les marges gauche+droite de 10 mm, à 96 px CSS par pouce.
# C'est la largeur que Chromium donne à la mise en page en impression — pas le viewport.
LARGEUR_IMPRIMABLE = round((210 - 2 * 10) / 25.4 * 96)   # 718 px

# Cacher un élément et regarder si le débordement retombe : ça attrape ce qu'une lecture de
# rectangles rate — pseudo-éléments, conteneurs à `overflow`, débordements indirects.
_JS_COUPABLES = """() => {
  const large = () => document.documentElement.scrollWidth;
  const base = large(), trouves = [];
  let noeuds = [...document.querySelectorAll('body > *')], prof = 0;
  while (noeuds.length && prof < 8) {
    const suivants = [];
    for (const e of noeuds) {
      const memo = e.style.display;
      e.style.display = 'none';
      const sans = large();
      e.style.display = memo;
      if (sans < base) {
        trouves.push({prof, tag: e.tagName.toLowerCase(), id: e.id || '',
                      cls: ((e.className?.baseVal ?? e.className) || '').toString().slice(0, 44),
                      sans, txt: (e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 60)});
        suivants.push(...e.children);
      }
    }
    noeuds = suivants; prof++;
  }
  return {base, trouves};
}"""


def largeur_de_mise_en_page(pg) -> tuple[int, list[dict]]:
    """La largeur réellement occupée en impression, et qui la pousse au-delà du papier."""
    pg.set_viewport_size({"width": LARGEUR_IMPRIMABLE, "height": 1400})
    pg.wait_for_timeout(400)
    r = pg.evaluate(_JS_COUPABLES)
    pg.set_viewport_size({"width": 1120, "height": 1400})
    pg.wait_for_timeout(200)
    return r["base"], r["trouves"]


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
        largeur, coupables = largeur_de_mise_en_page(pg)
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
    nom = cible.relative_to(RACINE) if cible.is_relative_to(RACINE) else cible
    print(f"Écrit : {nom} · {len(brut) / 1024:.0f} ko · "
          f"{pages} pages" + (f" · erreurs de console : {erreurs}" if erreurs else ""))

    if largeur > LARGEUR_IMPRIMABLE:
        print(f"ÉCHEC : mise en page {largeur} px pour {LARGEUR_IMPRIMABLE} px imprimables — "
              f"Chromium a réduit TOUT le document à {LARGEUR_IMPRIMABLE / largeur:.0%}, "
              f"ces {pages} pages sont en plus petit. Ce qui déborde :")
        for c in coupables[-6:]:
            print(f"   {'  ' * c['prof']}{c['tag']}"
                  f"{'#' + c['id'] if c['id'] else ''}"
                  f"{'.' + c['cls'] if c['cls'] else ''}   « {c['txt']} »")
        if not coupables:
            print("   (aucun élément isolé — le débordement vient du corps lui-même)")
        return 1
    print(f"Mise en page : {largeur} px ≤ {LARGEUR_IMPRIMABLE} px imprimables — échelle 1:1")

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
