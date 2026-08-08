#!/usr/bin/env python3
"""Le panel d'évaluation officiel de PREV'AIR, extrait de l'annexe 7 du rapport LCSQA.

Pourquoi cette table vaut le détour
-------------------------------------
Le rapport annuel de performances PREV'AIR (LCSQA/Ineris) ne publie ses **scores** que
sous forme de figures matricielles — donc non extractibles. Son **annexe 7**, en revanche,
est un vrai tableau : la liste nominative des stations retenues pour l'évaluation, polluant
par polluant, avec la **zone administrative réglementaire** (ZAG / ZAR / ZR), l'AASQA
exploitante, les coordonnées, l'altitude et la typologie.

C'est exactement ce qui manquait pour comparer à armes égales :

* le projet évalue sur **476 stations** choisies par lui ; PREV'AIR évalue sur les stations
  **de fond** ayant plus de 75 % de mesures valides. Comparer nos scores aux leurs sans
  aligner les panels compare deux choses différentes ;
* la **zone administrative** est la maille de décision des procédures préfectorales, celle
  de l'arrêté AMU. Le projet l'approchait par le département, faute de mieux.

⚠️ Ce que cette table n'est PAS : elle ne contient **aucune prévision ni aucune mesure**.
L'archive PREV'AIR reste limitée à six jours glissants ; ces rapports ne la remplacent pas.

Usage  : python3 scripts/extraire_panel_prevair.py --pdf data/raw/lcsqa_rapports/prevair_2024.pdf
Sortie : data/processed/panel_prevair_2024.csv
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

RACINE = Path(__file__).resolve().parents[1]

# La typologie est le dernier champ de chaque ligne : elle sert d'ancre de fin.
TYPOLOGIE = r"(Urbaine|P[ée]riurbaine|Rurale(?:\s+(?:r[ée]gionale|nationale|proche))?)"
# Une ligne = code station … latitude longitude [altitude] typologie.
# Les cellules de texte sont coupées par le rendu PDF ; on n'analyse donc QUE les champs
# numériques et la typologie, jamais les libellés — un nom coupé en deux ne doit pas
# décaler la lecture (règle 4 bis : ne jamais déduire d'une mise en forme).
#
# ⚠️ Deux gardes, et chacune vient d'un défaut constaté sur ce PDF :
#
# 1. **Le milieu ne peut pas franchir un autre code station** — `(?!FR\d{5})`. Sans cela,
#    une ligne mal formée ne se contentait pas d'échouer : son `.*?` courait jusqu'aux
#    chiffres de la ligne SUIVANTE et lui **volait ses coordonnées**. FR41072 sortait
#    ainsi avec la latitude de FR42010, et FR42010 disparaissait. Une ligne fausse et
#    plausible, exactement ce que `CLAUDE.md` § 2 bis interdit.
# 2. **L'altitude est facultative** — la colonne est vide pour au moins une station
#    (FR41072, Ajaccio P. Marconajo). Une donnée absente doit sortir absente, pas faire
#    échouer la ligne ni décaler la lecture.
LIGNE = re.compile(
    r"\b(FR\d{5})\b((?:(?!FR\d{5}).)*?)"
    r"(-?\d{1,2}[,.]\d+)\s+(-?\d{1,3}[,.]\d+)\s+(?:(\d{1,4})\s+)?" + TYPOLOGIE,
    re.S,
)
# Chaque sous-table d'annexe 7 est introduite par un titre de section numéroté — « 7.1 O3 »,
# « 7.2 PM10 ». Le premier motif essayé cherchait « stations validées … <polluant> » et ne
# reconnaissait que le titre de l'annexe : 939 lignes sont sorties sans polluant, et le
# contrôle de comptage a refusé d'écrire. C'est le contrôle qui l'a vu, pas la relecture.
ENTETE = re.compile(r"^\s*7\.\d+\s+(O\s?3|PM\s?10|PM\s?2[,.]5|NO\s?2)\s*$", re.M | re.I)


def normaliser(p: str) -> str:
    p = p.upper().replace(" ", "").replace(".", ",")
    return {"O3": "O3", "PM10": "PM10", "PM2,5": "PM25", "NO2": "NO2"}.get(p, p)


def extraire(pdf: Path) -> pd.DataFrame:
    """L'annexe est lue **en continu**, jamais page par page.

    Une première version analysait chaque page isolément et perdait **2 stations sur les
    288** que le rapport annonce pour l'ozone : les lignes coupées par un saut de page,
    dont le code est en bas d'une page et les coordonnées en haut de la suivante. Deux
    sur 288 est exactement le genre d'écart qu'on ne voit pas sans compter — et c'est le
    contrôle contre le chiffre annoncé qui l'a montré, pas la relecture du code.
    """
    lecteur = PdfReader(str(pdf))
    morceaux, bornes, illisibles, position = [], [], [], 0
    for numero, page in enumerate(lecteur.pages, start=1):
        try:
            texte = page.extract_text() or ""
        except Exception as e:                       # noqa: BLE001
            # `CLAUDE.md` § 2 bis : une exception de chargement ne se tait jamais. pypdf
            # meurt sur certaines pages de ce PDF (`SystemError` dans `NumberObject`) ;
            # on continue, mais la page est NOMMÉE et comptée dans le rapport final.
            illisibles.append((numero, type(e).__name__))
            texte = ""
        morceaux.append(texte)
        bornes.append((position, numero))
        position += len(texte) + 1
    entier = "\n".join(morceaux)

    def page_de(offset: int) -> int:
        return max((n for d, n in bornes if d <= offset), default=0)

    # Les sections « 7.1 O3 », « 7.2 PM10 »… découpent le texte continu. On borne chaque
    # section par le début de la suivante ; hors section, aucune ligne n'est retenue.
    entetes = [(m.start(), normaliser(m.group(1))) for m in ENTETE.finditer(entier)]
    if not entetes:
        raise SystemExit("aucune section « 7.x <polluant> » trouvée dans l'annexe")
    entetes.append((len(entier), None))

    lignes, perdues = [], 0
    for (debut, polluant), (fin, _) in zip(entetes, entetes[1:], strict=False):
        if polluant is None:
            continue
        bloc = entier[debut:fin]
        avant = len(lignes)
        for m in LIGNE.finditer(bloc):
            code, milieu, lat, lon, alt, typo = m.groups()
            zone = re.search(r"\b(ZAG|ZAR|ZR)\b", milieu)
            lignes.append({
                "station_id": code,
                "polluant": polluant,
                "type_zone": zone.group(1) if zone else None,
                "lat": float(lat.replace(",", ".")),
                "lon": float(lon.replace(",", ".")),
                "altitude_m": int(alt) if alt else None,
                "typologie": typo.strip().capitalize(),
                "page": page_de(debut + m.start()),
            })
        # Compter le reçu contre le demandé : les codes présents contre les lignes lues.
        perdues += len(re.findall(r"\bFR\d{5}\b", bloc)) - (len(lignes) - avant)

    if illisibles:
        print(f"  ⚠️ {len(illisibles)} page(s) illisible(s) : {illisibles[:6]}")
    if perdues:
        print(f"  ⚠️ {perdues} ligne(s) portant un code station n'ont pas pu être lues")
    return pd.DataFrame(lignes)


def main(pdf: Path, annee: int) -> int:
    if not pdf.exists():
        raise SystemExit(f"PDF absent : {pdf}")
    t = extraire(pdf)
    if t.empty:
        raise SystemExit("aucune ligne extraite — l'annexe a-t-elle changé de forme ?")
    if t["polluant"].isna().any():
        n = int(t["polluant"].isna().sum())
        print(f"  ⚠️ {n} ligne(s) sans polluant identifié — en-tête de sous-table manquée")

    print(f"\n{len(t)} lignes extraites de {pdf.name}\n")
    print(t.groupby(["polluant", "typologie"], dropna=False).size()
          .unstack(fill_value=0).to_string())

    # ── Compter le reçu contre le DEMANDÉ (règle 2 bis) ───────────────────────────
    # Le rapport 2024 annonce lui-même son panel ozone : « 288 stations de fond, 54
    # rurales, 88 périurbaines, 146 urbaines ». C'est la seule vérification externe
    # disponible ; sans elle, une expression régulière qui perd des lignes le ferait en
    # silence. 288 = 54 + 88 + 146 ne couvre que la métropole : les 10 stations des
    # Caraïbes et les 7 de l'océan Indien s'y ajoutent, d'où un total attendu > 288.
    if annee == 2024:
        o3 = t[t["polluant"] == "O3"]
        compte = o3["typologie"].str[:4].value_counts().to_dict()
        attendu = {"Rura": 54, "Péri": 88, "Urba": 146}
        print("\n  contrôle ozone — le rapport annonce lui-même « un panel de 288 stations "
              "de fond,\n  réparties en 54 rurales, 88 périurbaines et 146 urbaines » (§ 2.1)")
        print(f"  extrait : {len(o3)} lignes · {compte}")
        ecarts = {k: compte.get(k, 0) - v for k, v in attendu.items()
                  if compte.get(k, 0) != v}
        if ecarts or len(o3) != 288:
            raise SystemExit(
                f"panel ozone en écart avec le chiffre publié : {len(o3)} lignes "
                f"au lieu de 288, écarts par typologie {ecarts}")
        print("  ✓ les trois typologies et le total concordent avec le rapport")

    attendues = {"station_id", "polluant", "type_zone", "lat", "lon", "typologie"}
    if manque := attendues - set(t.columns):
        raise SystemExit(f"colonnes absentes : {sorted(manque)}")

    cible = RACINE / f"data/processed/panel_prevair_{annee}.csv"
    prov = cible.with_suffix(".csv.partiel")
    t.to_csv(prov, index=False)
    prov.replace(cible)
    print(f"\nÉcrit : {cible.relative_to(RACINE)} · {len(t)} lignes · "
          f"{t['station_id'].nunique()} stations distinctes")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--pdf", default="data/raw/lcsqa_rapports/prevair_2024.pdf")
    a.add_argument("--annee", type=int, default=2024)
    n = a.parse_args()
    chemin = Path(n.pdf)
    raise SystemExit(main(chemin if chemin.is_absolute() else RACINE / chemin, n.annee))
