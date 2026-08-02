#!/usr/bin/env python3
"""Archive quotidiennement les prévisions PREV'AIR — la fenêtre publique est glissante.

Pourquoi ce script est urgent, et pas seulement utile
------------------------------------------------------
PREV'AIR publie ses prévisions en NetCDF sur data.gouv.fr, mais **la fenêtre n'est que
d'environ six jours**. Le 02/08/2026, le jeu ne contenait que les dates du 27/07 au 02/08.
L'archive complète existe à l'INERIS depuis 2003 — elle alimente le site — mais elle n'est
pas téléchargeable en masse ; l'ancien chemin `prevair.org/donneesmisadispo/public/` est
mort (404 après refonte du site).

Conséquence pratique : **chaque jour non archivé est perdu définitivement.** Il n'y a pas
de rattrapage possible sans passer par `prevair@ineris.fr`.

Pourquoi ces données valent l'effort
--------------------------------------
C'est le produit contre lequel le projet devrait se mesurer, et non CAMS brut :

* la variable s'appelle `PM10_kriging` — c'est la sortie **déjà corrigée** par krigeage,
  adaptation statistique comprise, telle que PREV'AIR la diffuse ;
* la grille fait 755 × 534 sur la France, soit **≈ 1,7 km** — six fois plus fine que les
  0,1° de CAMS ;
* les échéances vont de `MAXJ0` à `MAXJ3` pour NO₂, O₃, PM10 et PM2,5.

Comparer notre correction d'un ensemble européen à 10 km à ce produit national assimilé
n'est pas une comparaison de méthodes : c'est une comparaison de **chaînes d'ampleur
différente**. Le dire ainsi vaut mieux que de l'ignorer.

Coût mesuré
------------
Passe unitaire du 02/08/2026 : 3,25 Mo par fichier, 2,3 s, débit 1,35 Mo/s.
Le lot complet des six dates — 192 fichiers — a pris **83 s pour 625 Mo**, zéro échec.
Soit environ **104 Mo par jour** archivé.

Usage : python3 scripts/archiver_prevair.py
        (idempotent — ne retélécharge pas ce qui est déjà complet)

Automatisation suggérée, une fois par jour après 07:00 UTC :
        0 8 * * *  cd /mnt/d/Projet_Air_Quality && python3 scripts/archiver_prevair.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DEST = RACINE / "data/raw/prevair"
API = ("https://www.data.gouv.fr/api/1/datasets/?q=prevair&page_size=10")
TAILLE_MIN = 100_000  # un NetCDF valide fait ~3 Mo ; en dessous, c'est une page d'erreur


def ressources() -> list[tuple[str, str]]:
    with urllib.request.urlopen(API, timeout=40) as r:
        d = json.loads(r.read())
    out = []
    for jeu in d.get("data", []):
        for res in jeu.get("resources") or []:
            titre, url = str(res.get("title") or ""), res.get("url")
            if str(res.get("format", "")).lower() == "nc" and url:
                out.append((titre, url))
    return out


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    depart = time.time()
    liste = ressources()
    if not liste:
        # ⚠️ Lever, ne pas sortir en silence : un archivage muet qui ne récupère rien est
        # indiscernable d'un archivage à jour, et le trou n'apparaîtra que des mois plus
        # tard, quand la donnée sera définitivement perdue.
        raise SystemExit("aucune ressource NetCDF listée — l'API a changé ou est en panne")

    ok = deja = ko = 0
    for nom, url in liste:
        cible = DEST / nom
        if cible.exists() and cible.stat().st_size >= TAILLE_MIN:
            deja += 1
            continue
        # Nom provisoire puis renommage : un artefact au nom définitif doit être complet.
        tmp = cible.with_suffix(cible.suffix + ".partiel")
        try:
            urllib.request.urlretrieve(url, tmp)
            if tmp.stat().st_size < TAILLE_MIN:
                raise ValueError(f"{tmp.stat().st_size} octets — trop petit")
            tmp.replace(cible)
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ {nom} : {type(e).__name__} {e}", flush=True)
            tmp.unlink(missing_ok=True)
            ko += 1

    fichiers = sorted(DEST.glob("*.nc"))
    dates = sorted({m for f in fichiers for m in re.findall(r"\.(\d{8})\.", f.name)})
    volume = sum(f.stat().st_size for f in fichiers) / 1e6
    print(f"{ok} nouveaux · {deja} déjà présents · {ko} échecs · "
          f"{time.time() - depart:.0f} s")
    print(f"archive : {len(fichiers)} fichiers · {volume:.0f} Mo · "
          f"{len(dates)} dates · {dates[0]} → {dates[-1]}" if dates else "archive vide")

    # Contrôle de continuité — un trou signale un jour d'exécution manqué, définitif.
    if len(dates) >= 2:
        import datetime as dt
        d0 = dt.date.fromisoformat(f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}")
        d1 = dt.date.fromisoformat(f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}")
        attendues = {(d0 + dt.timedelta(days=i)).strftime("%Y%m%d")
                     for i in range((d1 - d0).days + 1)}
        manquantes = sorted(attendues - set(dates))
        if manquantes:
            print(f"⚠️ {len(manquantes)} jour(s) MANQUANT(S), non rattrapables : "
                  f"{', '.join(manquantes[:10])}")
    if ko:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
