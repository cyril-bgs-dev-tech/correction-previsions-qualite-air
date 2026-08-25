#!/usr/bin/env python3
"""La table d'échelle de `Découverte_ATMO.html`, DÉRIVÉE du socle plutôt que recopiée.

Pourquoi ce générateur existe
------------------------------
Cette table portait l'échelle de la pile du 17/08 — dont un barreau était **GEOS-CF**, devenu
un module conditionnel. Ses six chiffres de tête étaient périmés, et l'audit
`auditer_chiffres_publies.py` les signalait à chaque exécution.

Corriger seulement les dernières lignes aurait produit un tableau dont le total ne découle
plus de ses barreaux : **incohérent est pire que cohérent et daté**. Et la corriger à la main
en entier la laisserait périmer une fois de plus.

Elle n'avait pas de générateur — la pièce est écrite à la main. Elle en a un maintenant, et
il remplace le `<tbody>` **entre sentinelles**, sans toucher à la prose autour.

Usage : python3 scripts/table_decouverte.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
CIBLE = RACINE / "reports/figures/Découverte_ATMO.html"
V = "_sans-feux-geoscf_fenetre-complete"
POLLUANTS = ("NO2", "O3", "PM10", "PM25")

# Les barreaux du socle, dans l'ordre d'empilement, avec leur nom lisible. Les noms techniques
# n'ont pas leur place dans une pièce grand public ; les correspondances sont écrites ici pour
# qu'on puisse les vérifier d'un coup d'œil contre les CSV.
BARREAUX = [
    ("base (CAMS, terrain, calendrier)", "modèle de base", ""),
    ("+ typologie", "+ typologie de station", "trafic, fond, urbain"),
    ("+ membres", "+ accord des modèles européens", "9 modèles de CAMS"),
    ("+ tendance", "+ tendance récente du modèle", "sans lire une observation"),
    ("+ speciation", "+ composition du champ CAMS", "de quoi la masse est faite"),
    ("+ profil", "+ forme de la journée", ""),
    ("+ fourier", "+ cycles saisonniers", ""),
    ("+ precurseurs", "+ précurseurs gazeux", "NH₃, SO₂, PAN, COV"),
    ("★ MAXIMALE — PARTOUT", "<b>Maximum atteint — partout</b>", "aucune observation"),
    ("★ MAXIMALE — AUX STATIONS (+ veille)", "<b>Maximum aux stations instrumentées</b>",
     "avec l'observation de la veille"),
]
DEBUT = "<!-- ══ TABLE SOCLE · générée par scripts/table_decouverte.py ══ -->"
FIN_ = "<!-- ══ FIN TABLE SOCLE ══ -->"


def cellule(gain: float, marge: float | None) -> str:
    """Une case : la valeur, sa jauge, et l'écart au barreau précédent."""
    largeur = max(2, round(2 * gain))
    if marge is None:
        em = ""
    else:
        classe = "plus" if marge >= 0 else "moins"
        em = f'<em class="{classe}">{marge:+.2f}</em>'.replace(".", ",")
    val = f"{gain:+.2f} %".replace(".", ",")
    return (f'<td><span class="jauge-cell"><b>{val}</b>'
            f'<i style="width:{largeur}px"></i>{em}</span></td>')


def main() -> int:
    tables = {}
    for p in POLLUANTS:
        f = RACINE / f"reports/methode_maximale_{p}_h2{V}.csv"
        if not f.exists():
            raise SystemExit(f"⛔ {f.name} absent — le socle n'est pas mesuré pour {p}.")
        tables[p] = pd.read_csv(f).set_index("configuration")["gain_pct"]

    # Chaque barreau doit exister dans les QUATRE piles : une ligne partiellement remplie
    # afficherait un tableau d'apparence normale avec un trou muet.
    manquants = [(c, p) for c, _, _ in BARREAUX for p in POLLUANTS if c not in tables[p].index]
    if manquants:
        raise SystemExit(f"⛔ barreau(x) absent(s) de la pile : {manquants[:4]}")

    lignes, precedent = [], {p: None for p in POLLUANTS}
    for cle, libelle, note in BARREAUX:
        n = (f' <span style="font-size:12px;color:var(--encre-3)">({note})</span>'
             if note else "")
        cases = []
        for p in POLLUANTS:
            g = float(tables[p][cle])
            marge = None if precedent[p] is None or "MAXIMALE" in cle else g - precedent[p]
            cases.append(cellule(g, marge))
            if "MAXIMALE" not in cle:
                precedent[p] = g
        lignes.append(f"          <tr>\n            <td>{libelle}{n}</td>\n            "
                      + "\n            ".join(cases) + "\n          </tr>")

    bloc = DEBUT + "\n" + "\n".join(lignes) + "\n          " + FIN_
    texte = CIBLE.read_text(encoding="utf-8")
    if DEBUT in texte:
        texte = re.sub(re.escape(DEBUT) + r".*?" + re.escape(FIN_), bloc, texte, flags=re.S)
    else:
        # Première pose : on remplace le <tbody> de la table qui porte l'échelle.
        i = texte.find("composition du champ CAMS")
        if i < 0:
            raise SystemExit("⛔ table d'échelle introuvable — la pièce a-t-elle changé ?")
        d = texte.rfind("<tbody>", 0, i)
        f = texte.find("</tbody>", i)
        if d < 0 or f < 0:
            raise SystemExit("⛔ bornes <tbody> introuvables autour de la table d'échelle.")
        texte = texte[:d + len("<tbody>")] + "\n" + bloc + "\n        " + texte[f:]
    CIBLE.write_text(texte, encoding="utf-8")
    print(f"  {len(BARREAUX)} barreaux × {len(POLLUANTS)} polluants écrits dans {CIBLE.name}")
    for p in POLLUANTS:
        print(f"    {p:5s} {tables[p]['base (CAMS, terrain, calendrier)']:+6.2f} % → "
              f"{tables[p]['★ MAXIMALE — PARTOUT']:+6.2f} % partout · "
              f"{tables[p]['★ MAXIMALE — AUX STATIONS (+ veille)']:+6.2f} % aux stations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
