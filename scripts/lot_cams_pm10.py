#!/usr/bin/env python3
"""Prévisions CAMS PM10 seules — sans re-télécharger ce qui est déjà extrait.

Pourquoi un script dédié plutôt que le lot général
--------------------------------------------------
`download_copernicus.py --service cams_prevision` planifie **les quatre espèces**. Or les
bruts d'O₃, NO₂ et PM2,5 ont été purgés après extraction en parquet : le lot général les
redemanderait tous. Mesuré : **30 fichiers à télécharger dont 18 inutiles**, soit environ
deux heures perdues à 7 minutes la requête.

Ce script ne demande que les PM10, et ne redemande pas ce qui est déjà sur le disque.

Coût mesuré (règle 1, passe unitaire du 01/08/2026)
---------------------------------------------------
* **425 s** pour une requête de deux mois — 289 Mo, 60 fichiers journaliers ;
* **2263 champs sur 5000** par mois, donc 91 % du plafond ADS pour une paire : le
  groupement par deux est déjà optimal, en demander trois serait refusé ;
* axe résultat vérifié : variable ``pm10_conc``, **73 échéances** par jour, grille
  110 × 150, valeurs de 0,42 à 147 µg/m³ pour une moyenne de 10,10 — cohérent avec la
  médiane de 9,5 observée dans le flux LCSQA.

Extrapolation : **12 paires × 425 s ≈ 85 min** pour la fenêtre 2023-08 → 2025-06.

Pourquoi les PM10 maintenant
----------------------------
Sur les **52 vigilances réellement déclarées** par Atmo Occitanie entre janvier 2025 et mars
2026, **40 portent sur les PM10** et 12 sur l'ozone. Le projet optimisait le polluant qui
décide de l'indice ATMO ; l'AASQA déclenche sur celui des particules.

Usage : python3 scripts/lot_cams_pm10.py [--debut 2023-08] [--fin 2025-06]
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import copernicus as cop  # noqa: E402
# On réutilise la machinerie du lot général — reprise, reprise sur erreur, dépaquetage,
# vérification de structure. La dupliquer ferait diverger deux chemins de code sur la
# même tâche, et c'est ainsi que naissent les défauts silencieux.
from download_copernicus import SERVICES, lire_cle, telecharger  # noqa: E402


def acheve(dossier: Path, nom: str) -> bool:
    """Un mois est fait s'il a laissé **tous** ses jours, pas seulement son dossier."""
    if (dossier / nom).exists():
        return True
    membres = dossier / Path(nom).stem
    if not membres.is_dir():
        return False
    jetons = re.findall(r"_(\d{4})(\d{2})(?=_|$)", membres.name)
    if not jetons:
        return True
    attendus = sum(pd.Period(f"{a}-{m}").days_in_month for a, m in jetons)
    presents = len(list(membres.glob("*.nc")))
    if presents < attendus:
        print(f"  ↻ {membres.name} incomplet : {presents}/{attendus} jours", flush=True)
    return presents >= attendus


def main(debut: str, fin: str, especes: list[str]) -> int:
    a0, m0 = (int(x) for x in debut.split("-"))
    a1, m1 = (int(x) for x in fin.split("-"))
    plan = cop.plan_telechargement(date(a0, m0, 1), date(a1, m1, 28),
                                   service="cams_prevision")
    # Filtrer par le nom que **le planificateur** construit, jamais par un motif inventé
    # ici : si la convention change, on veut ne rien trouver plutôt qu'attraper autre chose.
    retenues = [(n, r) for n, r in plan
                if any(f"_{e}_" in n for e in especes)]
    if not retenues:
        raise SystemExit(f"aucune entrée {especes} dans le plan — ces espèces ne sont pas "
                         f"dans VARIABLES_CAMS, ou la convention de nommage a changé")

    dossier = RACINE / "data/raw/cams_prevision"
    dossier.mkdir(parents=True, exist_ok=True)
    reste = [(n, r) for n, r in retenues if not acheve(dossier, n)]
    print(f"{len(retenues)} paires planifiées ({', '.join(especes)}) · "
          f"{len(reste)} à télécharger · "
          f"extrapolation {len(reste) * 425 / 60:.0f} min", flush=True)
    if not reste:
        print("rien à faire")
        return 0

    url, _ = SERVICES["cams_prevision"]
    identifiants = cop.Identifiants(url=url, cle=lire_cle())
    cop.accepter_licence(identifiants)

    depart = time.time()
    echecs = 0
    for i, (nom, requete) in enumerate(reste, 1):
        t0 = time.time()
        _, statut = telecharger("cams_prevision", identifiants, dossier, nom, requete)
        echecs += not statut.startswith(("OK", "déjà"))
        print(f"  [{i}/{len(reste)}] {time.time() - t0:5.0f}s  {nom}  {statut} · "
              f"total {(time.time() - depart) / 60:.0f} min", flush=True)

    faits = sum(1 for n, _ in retenues if acheve(dossier, n))
    print(f"\n{faits}/{len(retenues)} paires complètes · {echecs} échec(s) · "
          f"{(time.time() - depart) / 60:.0f} min")
    if faits < len(retenues):
        print("⚠️ Paires incomplètes — relancer la MÊME commande : la reprise porte sur le "
              "contenu (tous les jours présents), pas sur l'existence du dossier.")
    return 0 if faits == len(retenues) else 1


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--debut", default="2023-08")
    a.add_argument("--fin", default="2025-06")
    # ⚠️ Défaut inchangé — `pm10` seul — pour que les appels existants gardent leur sens.
    # Le lot général `download_copernicus.py --service cams_prevision` reste à proscrire :
    # il replanifie les quatre espèces et redemande les bruts déjà purgés après extraction.
    a.add_argument("--especes", default="pm10",
                   help="liste séparée par des virgules, ex. o3,no2,pm25,pm10")
    n = a.parse_args()
    raise SystemExit(main(n.debut, n.fin, [e.strip() for e in n.especes.split(",") if e.strip()]))
