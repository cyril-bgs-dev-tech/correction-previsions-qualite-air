#!/usr/bin/env python3
"""Rend les pages publiées dans les deux thèmes et remonte les erreurs de console.

Le défaut que la version précédente portait
-------------------------------------------
Le chemin des pages était **codé en dur sur un répertoire de session** :
``/tmp/claude-.../f3bcaeaf-.../scratchpad``. Ce répertoire disparaît avec la session, si bien
que le script échouait sur ``ERR_FILE_NOT_FOUND`` — et un contrôle qui ne peut plus s'exécuter
ne protège de rien. Les pages vivent dans ``reports/figures/`` ; c'est de là qu'on les lit, et
les captures vont dans un dossier du dépôt.

Deux contrôles, pas un
----------------------
* les **erreurs de console** — une page qui lève en silence s'affiche quand même ;
* le **débordement horizontal** — invisible sur une capture pleine page, il casse la lecture
  sur mobile. On le mesure explicitement plutôt que de l'espérer absent.

Usage : python3 scripts/render_check.py [page.html ...]
Sortie : reports/figures/rendu/{page}_{clair,sombre}.png
"""

from __future__ import annotations

import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
PAGES = RACINE / "reports/figures"
SORTIE = PAGES / "rendu"

# Par défaut, les deux pages écrites à la main — les seules sans générateur pour les
# revérifier à chaque exécution.
DEFAUT = ["presentation.html", "figures.html"]


def main(noms: list[str]) -> int:
    from playwright.sync_api import sync_playwright

    SORTIE.mkdir(parents=True, exist_ok=True)
    cibles = [PAGES / n for n in (noms or DEFAUT)]
    manquantes = [c for c in cibles if not c.exists()]
    if manquantes:
        print("Pages introuvables : " + ", ".join(m.name for m in manquantes))
        return 1

    total = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for src in cibles:
            for mode, suffixe in (("light", "clair"), ("dark", "sombre")):
                pg = b.new_page(viewport={"width": 1120, "height": 1200}, color_scheme=mode)
                erreurs: list[str] = []
                pg.on("pageerror", lambda e: erreurs.append(str(e)))
                pg.on("console",
                      lambda m: erreurs.append(m.text) if m.type == "error" else None)
                pg.goto(f"file://{src}")
                pg.wait_for_timeout(900)
                pg.screenshot(path=str(SORTIE / f"{src.stem}_{suffixe}.png"), full_page=True)
                hauteur = pg.evaluate("document.documentElement.scrollHeight")
                deborde = pg.evaluate(
                    "document.documentElement.scrollWidth > "
                    "document.documentElement.clientWidth + 2")
                pg.close()
                total += len(erreurs) + int(deborde)
                etat = "OK" if not erreurs and not deborde else "⚠️"
                print(f"{etat} {src.name:24} {suffixe:7} {hauteur:6d} px"
                      + (" · DÉBORDE horizontalement" if deborde else "")
                      + (f" · erreurs : {erreurs}" if erreurs else ""), flush=True)
        b.close()
    print(f"\n{total} anomalie(s) · captures dans {SORTIE.relative_to(RACINE)}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
