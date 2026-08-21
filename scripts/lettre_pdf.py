#!/usr/bin/env python3
"""Compose la lettre de motivation en PDF — pièce jointe du mail de candidature.

Pourquoi un script et pas un export manuel
-------------------------------------------
La lettre a changé six fois en une journée. Un PDF exporté à la main se désynchronise du
`.md` au premier remaniement, et **rien ne le signale** : le fichier existe, il s'ouvre, il
porte l'ancienne version. Le PDF se régénère donc depuis le Markdown, à la commande.

Ce que le contrôle vérifie
---------------------------
Une page (au-delà, une lettre de motivation se lit moins), le texte réellement présent dans
le PDF produit, et l'absence des formulations écartées lors des relectures. Le verdict porte
sur l'artefact ouvert, jamais sur le code de retour de WeasyPrint.

Usage : python3 scripts/lettre_pdf.py
"""
from __future__ import annotations

import html
import re
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SOURCE = RACINE / "docs/LETTRE_ATMO_VARIANTE_SANS_GITHUB.md"
SORTIE = Path("/mnt/c/Users/Cyril/Desktop/Cyril_Bourgeois_lettre.pdf")

DESTINATAIRE = ["ATMO Occitanie", "Pôle Partenariats", "Toulouse"]
LIEU = "Clermont-Ferrand"
MOIS = ("janvier février mars avril mai juin juillet "
        "août septembre octobre novembre décembre").split()

# Formulations retirées au fil des relectures : le PDF ne doit en porter aucune.
ECARTEES = ("là où aucune station", "là où il n'y en a pas", "plusieurs mois",
            "approfondi depuis", "vos publications", "rencontré",
            "[Formule de politesse]")


def paragraphes() -> list[str]:
    t = SOURCE.read_text(encoding="utf-8")
    corps = t[t.index("Madame, Monsieur,"):t.index("**Cyril Bourgeois**")]
    out = []
    for p in (x.strip() for x in corps.split("\n\n")):
        if not p:
            continue
        x = html.escape(" ".join(p.split()))
        x = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", x)
        out.append(x)
    return out


def document(paras: list[str]) -> str:
    d = date.today()
    ouverture, corps, cloture = paras[0], paras[1:-1], paras[-1]
    dest = "<br>".join(html.escape(x) for x in DESTINATAIRE)
    blocs = "\n".join(f"<p>{p}</p>" for p in corps)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 16mm 21mm 15mm; }}
* {{ box-sizing: border-box; }}
body {{
  font-family: "DejaVu Serif", Georgia, serif; font-size: 9.2pt; line-height: 1.45;
  color: #1A1D21; margin: 0; hyphens: auto;
}}
.entete {{ display: flex; justify-content: space-between; align-items: flex-start;
  border-bottom: 1.6pt solid #1F3864; padding-bottom: 3.2mm; margin-bottom: 6mm; }}
.moi {{ font-family: "DejaVu Sans", sans-serif; }}
.moi .nom {{ font-size: 15pt; font-weight: bold; color: #1F3864; letter-spacing: .2pt; }}
.moi .role {{ font-size: 8.4pt; color: #5D666F; letter-spacing: .9pt;
  text-transform: uppercase; margin-top: 1.4mm; }}
.coord {{ font-family: "DejaVu Sans", sans-serif; font-size: 8.2pt;
  text-align: right; line-height: 1.62; padding-top: .6mm; }}
.coord a {{ color: #1F3864; text-decoration: none; }}
.coord .sec {{ font-size: 7.5pt; color: #5D666F; }}
.adresse {{ display: flex; justify-content: space-between;
  align-items: flex-start; margin-bottom: 6mm; }}
.dest {{ font-family: "DejaVu Sans", sans-serif; font-size: 9pt; line-height: 1.5; }}
.dest .a {{ font-size: 7.4pt; color: #8A939C; letter-spacing: 1pt;
  text-transform: uppercase; display: block; margin-bottom: 1.6mm; }}
.date {{ font-family: "DejaVu Sans", sans-serif; font-size: 8.6pt;
  color: #5D666F; text-align: right; padding-top: 5mm; }}
.objet {{ font-family: "DejaVu Sans", sans-serif; font-size: 9pt; color: #1F3864;
  font-weight: bold; margin-bottom: 4.4mm; }}
.ouverture {{ margin: 0 0 2.6mm; }}
p {{ margin: 0 0 2.6mm; text-align: justify; }}
strong {{ color: #1F3864; }}
.cloture {{ margin: 4mm 0 0; text-align: left; }}
.signature {{ font-family: "DejaVu Sans", sans-serif; margin-top: 5.5mm;
  font-size: 9.6pt; font-weight: bold; color: #1F3864; }}
</style></head><body>

<div class="entete">
  <div class="moi">
    <div class="nom">Cyril Bourgeois</div>
    <div class="role">Data Scientist</div>
  </div>
  <div class="coord">
    <a href="https://gitlab.com/cyril.bgs.dev"><strong>gitlab.com/cyril.bgs.dev</strong></a><br>
    <a href="https://www.linkedin.com/in/cyril-bourgeois-65a739150/"><strong>linkedin.com/in/cyril-bourgeois-65a739150</strong></a><br>
    <span class="sec">cyril.bgs.dev@gmail.com &middot; 06 89 44 81 36</span>
  </div>
</div>

<div class="adresse">
  <div class="dest"><span class="a">À l'attention de</span>{dest}</div>
  <div class="date">{LIEU}, le {d.day} {MOIS[d.month - 1]} {d.year}</div>
</div>

<p class="objet">Objet — Candidature au CDD du Pôle Partenariats</p>

<p class="ouverture">{ouverture}</p>
{blocs}
<p class="cloture">{cloture}</p>
<div class="signature">Cyril Bourgeois</div>

</body></html>"""


def main() -> int:
    from weasyprint import HTML

    paras = paragraphes()
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=document(paras)).write_pdf(str(SORTIE))

    # ── Le verdict porte sur l'artefact ouvert, pas sur l'absence d'exception ──
    import fitz
    d = fitz.open(SORTIE)
    texte = "\n".join(p.get_text() for p in d)
    n = len(d)
    d.close()

    if n != 1:
        raise SystemExit(f"❌ {n} pages — une lettre de motivation tient sur une page")
    for m in ECARTEES:
        if m in texte:
            raise SystemExit(f"❌ formulation écartée présente dans le PDF : « {m} »")
    for attendu in ("Madame, Monsieur", "41 %", "96 %", "88 %", "2,5 points",
                    "3 dépassements sur 32", "salutations distinguées"):
        if attendu not in texte:
            raise SystemExit(f"❌ « {attendu} » absent du PDF produit")

    print(f"Écrit : {SORTIE} · {SORTIE.stat().st_size / 1024:.0f} ko · {n} page")
    print(f"  {len(' '.join(texte.split()).split())} mots dans le PDF · "
          f"{len(paras)} paragraphes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
