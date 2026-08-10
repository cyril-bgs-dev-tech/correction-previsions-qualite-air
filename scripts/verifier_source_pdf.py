#!/usr/bin/env python3
"""Télécharge une source PDF, prouve qu'elle est complète, et montre où l'affirmation se lit.

C'est la chaîne de vérification des fiches départementales, écrite une fois plutôt que
réinventée à chaque lot. Elle applique trois règles de CLAUDE.md :

  · § 1 ter — « un code 200 n'est pas un résultat » : le volume reçu est comparé au
    `Content-Length` annoncé, et un PDF qui ne commence pas par %PDF est refusé. Une page
    d'erreur HTML de 18 ko ne passera pas pour un bilan de 6 Mo.
  · § 2 bis — compter le reçu contre le demandé : le nombre de pages est affiché, et
    chaque mot-clé demandé est cherché ; les mots-clés SANS correspondance sont nommés,
    parce qu'un zéro de non-lecture ne se distingue pas d'un zéro de non-occurrence.
  · § 4 — écrire sous un nom provisoire, vérifier, puis renommer.

Usage :
    python3 scripts/verifier_source_pdf.py <url> <destination.pdf> [mot-cle ...]
    python3 scripts/verifier_source_pdf.py --local <fichier.pdf> [mot-cle ...]

La recherche des mots-clés est insensible à la casse et aux accents.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

CONTEXTE = 260  # caractères affichés autour d'une correspondance


def sans_accent(texte: str) -> str:
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def telecharger(url: str, destination: Path) -> Path:
    """Télécharge sous un nom provisoire, contrôle, puis renomme (§ 4)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    provisoire = destination.with_suffix(destination.suffix + ".partiel")

    entetes = subprocess.run(
        ["curl", "-sIL", "--max-time", "60", url],
        capture_output=True, text=True, check=False,
    ).stdout
    annonce = 0
    for ligne in entetes.splitlines():
        if ligne.lower().startswith("content-length:"):
            annonce = int(ligne.split(":", 1)[1].strip() or 0)

    subprocess.run(
        ["curl", "-sL", "--max-time", "300", "-o", str(provisoire), url],
        check=True,
    )
    recu = provisoire.stat().st_size

    if annonce and recu != annonce:
        provisoire.unlink()
        raise SystemExit(f"✗ {recu} octets reçus pour {annonce} annoncés — {url}")
    if provisoire.read_bytes()[:4] != b"%PDF":
        debut = provisoire.read_bytes()[:60]
        provisoire.unlink()
        raise SystemExit(f"✗ ce n'est pas un PDF ({recu} octets) : {debut!r} — {url}")

    provisoire.replace(destination)
    print(f"✅ {recu:,} octets · {url}".replace(",", " "))
    return destination


def extraire(pdf: Path) -> dict[int, str]:
    import fitz

    document = fitz.open(pdf)
    pages = {n + 1: page.get_text() for n, page in enumerate(document)}
    document.close()
    sortie = pdf.with_suffix(pdf.suffix + ".txt")
    sortie.write_text(
        "".join(f"\n=== PAGE {n} ===\n{t}" for n, t in pages.items()), encoding="utf-8"
    )
    total = sum(len(t) for t in pages.values())
    print(f"   {len(pages)} pages · {total:,} caractères → {sortie}".replace(",", " "))
    if total < 200 * len(pages):
        print("   ⚠️ très peu de texte par page : PDF probablement scanné (image)")
    return pages


def chercher(pages: dict[int, str], mots: list[str]) -> None:
    muets = []
    for mot in mots:
        cible = sans_accent(mot)
        trouves = 0
        for numero, texte in pages.items():
            plat = sans_accent(" ".join(texte.split()))
            for correspondance in re.finditer(re.escape(cible), plat):
                if trouves == 0:
                    print(f"\n── « {mot} »")
                debut = max(0, correspondance.start() - CONTEXTE // 2)
                print(f"   p{numero} …{plat[debut:correspondance.start() + CONTEXTE]}…")
                trouves += 1
                break
            if trouves >= 4:
                break
        if trouves == 0:
            muets.append(mot)
    if muets:
        print(f"\n⚠️ AUCUNE correspondance pour : {', '.join(muets)}")
        print("   (un zéro de non-lecture ne se distingue pas d'un zéro de non-occurrence)")


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments:
        raise SystemExit(__doc__)

    if arguments[0] == "--local":
        pdf, mots = Path(arguments[1]), arguments[2:]
        if not pdf.exists():
            raise SystemExit(f"✗ absent : {pdf}")
        print(f"✅ local · {pdf.stat().st_size:,} octets · {pdf}".replace(",", " "))
    else:
        url, destination, mots = arguments[0], Path(arguments[1]), arguments[2:]
        pdf = telecharger(url, destination)

    pages = extraire(pdf)
    if mots:
        chercher(pages, mots)
    return 0


if __name__ == "__main__":
    sys.exit(main())
