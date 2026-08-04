#!/usr/bin/env python3
"""Compléter les membres d'ensemble manquants — liste explicite, ouvriers disjoints.

Pourquoi ce script alors que `lot_membres_ensemble.py` existe
---------------------------------------------------------------
Celui-là parcourt une **plage** de mois et reprend par existence de fichier. C'est ce qui a
produit, le 31/07, deux processus jumeaux écrivant le même `.partiel` — deux mois perdus en
silence. Ici la reprise ne décide de rien : chaque ouvrier reçoit une **liste nommée** de
tâches, et deux listes disjointes ne peuvent pas se croiser.

Ce que la passe unitaire du 30/07 a établi, et qui reste valable
------------------------------------------------------------------
* 6 membres × 24 échéances × 31 jours = **4 464 champs, 89 % du plafond ADS de 5 000** ;
* le `.nc` livré est une **archive ZIP** de six entrées, une par membre ;
* **394 s par requête**, dont l'essentiel en file d'attente ;
* **3 requêtes simultanées passent, 6 sont rejetées** — la concurrence est donc bornée à
  trois ouvriers, jamais davantage.

⚠️ **PM10 n'a jamais été demandé sur ce jeu.** Sa passe unitaire est obligatoire avant de
l'inclure dans un lot : un nom de variable invalide se voit servir le reste sans lever, et
c'est exactement ainsi que le flux PM2,5 de GFAS avait été perdu.

La reprise porte sur le **contenu**
-------------------------------------
Écriture sous `.partiel`, vérification des six membres, **puis** renommage. Un nom
définitif vaut donc marque d'achèvement, et jamais l'inverse.

Usage :
  python3 scripts/lot_membres_complement.py --taches "o3:2025-08,o3:2025-09,no2:2025-08"
  python3 scripts/lot_membres_complement.py --taches-fichier lot_a.txt
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import copernicus as cop  # noqa: E402
from download_copernicus import SERVICES, lire_cle  # noqa: E402
from lot_membres_ensemble import complet  # noqa: E402

DOSSIER = RACINE / "data/raw/cams_membres"
ESPECE_LONGUE = {"o3": "ozone", "no2": "nitrogen_dioxide",
                 "pm25": "particulate_matter_2.5um", "pm10": "particulate_matter_10um"}


def lire_taches(texte: str) -> list[tuple[str, int, int]]:
    """« o3:2025-08,no2:2025-09 » → [('o3', 2025, 8), ('no2', 2025, 9)]."""
    out = []
    for jeton in (x.strip() for x in texte.replace("\n", ",").split(",") if x.strip()):
        espece, _, mois = jeton.partition(":")
        if espece not in ESPECE_LONGUE:
            raise SystemExit(f"espèce inconnue : « {espece} » — attendu "
                             f"{', '.join(ESPECE_LONGUE)}")
        annee, _, m = mois.partition("-")
        out.append((espece, int(annee), int(m)))
    if not out:
        raise SystemExit("aucune tâche")
    return out


def main(taches: list[tuple[str, int, int]], etiquette: str) -> int:
    membres = cop.MEMBRES_DIVERSIFIES
    url, jeu = SERVICES["cams_prevision"]
    identifiants = cop.Identifiants(url=url, cle=lire_cle())
    DOSSIER.mkdir(parents=True, exist_ok=True)

    reste = [t for t in taches
             if not (DOSSIER / f"membres_{t[0]}_{t[1]}{t[2]:02d}.nc").exists()]
    print(f"[{etiquette}] {len(taches)} tâches · {len(reste)} à faire · "
          f"{len(membres)} membres · échéances 1-24 · "
          f"extrapolation {len(reste) * 394 / 3600:.1f} h", flush=True)
    if not reste:
        print(f"[{etiquette}] rien à faire")
        return 0

    depart, faits, echecs = time.time(), 0, []
    for n, (espece, annee, mois) in enumerate(reste, start=1):
        cible = DOSSIER / f"membres_{espece}_{annee}{mois:02d}.nc"
        partiel = cible.with_suffix(".nc.partiel")
        requete = cop.requete_cams_prevision(
            annee, mois, variables=[ESPECE_LONGUE[espece]],
            echeances_h=range(1, 25), modeles=membres)
        t0 = time.time()
        try:
            cop.executer(identifiants, jeu, requete, str(partiel))
        except Exception as exc:  # noqa: BLE001
            # ⚠️ Jamais silencieux : une exception avalée transforme un plantage en
            # fichier absent, indiscernable d'un mois sans données.
            print(f"[{etiquette}] [{n}/{len(reste)}] {cible.name} ÉCHEC "
                  f"{type(exc).__name__}: {str(exc)[:160]}", flush=True)
            partiel.unlink(missing_ok=True)
            echecs.append(cible.name)
            continue

        probleme = complet(partiel, len(membres))
        if probleme:
            print(f"[{etiquette}] [{n}/{len(reste)}] {cible.name} REJETÉ — {probleme}",
                  flush=True)
            partiel.unlink(missing_ok=True)
            echecs.append(cible.name)
            continue

        partiel.rename(cible)          # nom définitif = contenu vérifié, jamais l'inverse
        faits += 1
        ecoule = time.time() - depart
        print(f"[{etiquette}] [{n}/{len(reste)}] {cible.name} · "
              f"{cible.stat().st_size / 1e6:.0f} Mo · {time.time() - t0:.0f}s · "
              f"écoulé {ecoule / 60:.0f} min · "
              f"reste ~{ecoule / n * (len(reste) - n) / 60:.0f} min", flush=True)

    print(f"[{etiquette}] TERMINÉ · {faits} écrits · {len(echecs)} échec(s)"
          + (" : " + ", ".join(echecs) if echecs else ""), flush=True)
    return 0 if not echecs else 1


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--taches", default="", help="« o3:2025-08,no2:2025-09 »")
    a.add_argument("--taches-fichier", default="")
    a.add_argument("--etiquette", default="lot")
    n = a.parse_args()
    texte = (Path(n.taches_fichier).read_text() if n.taches_fichier else n.taches)
    raise SystemExit(main(lire_taches(texte), n.etiquette))
