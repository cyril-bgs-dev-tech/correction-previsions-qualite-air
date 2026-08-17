#!/usr/bin/env python3
"""La SPÉCIATION des particules par CAMS — six variables qu'on ne téléchargeait pas.

Le constat qui a produit ce script — 16/08/2026
------------------------------------------------
Le catalogue ADS expose **28 variables** pour `cams-europe-air-quality-forecasts`. Ce
dépôt en télécharge **quatre** : NO₂, O₃, PM2,5, PM10 — des masses totales, sans aucune
décomposition. Or notre modèle corrige un **résidu** : lui donner la composition du champ,
c'est lui dire *pourquoi* CAMS prédit ce qu'il prédit, et lui permettre d'apprendre des
biais **par source** plutôt qu'un biais moyen.

C'est le levier le plus plausible pour l'écart mesuré sur les particules face à AS-CHI
(+52,5 % et +60,1 % pour eux contre +33,3 % et +29,6 % pour nous, convention AASQA) :
leur CHIMERE tourne sur l'inventaire d'émissions français, le nôtre est un ensemble
européen dont on n'utilisait que la somme.

Les six retenues, et le mécanisme de chacune
----------------------------------------------
* `residential_elementary_carbon` — le traceur du **chauffage au bois**, première source
  française de PM2,5 en hiver (7,4 M de logements équipés) ;
* `secondary_inorganic_aerosol` — la fraction NH₃ → nitrate/ammonium/sulfate, qui domine
  les **épisodes de printemps** liés aux épandages ;
* `pm2.5_nitrate` — sa composante la plus variable, séparée pour que le modèle puisse la
  distinguer du sulfate, dont la chimie et la saisonnalité diffèrent ;
* `dust` — les poussières sahariennes, qui font les pics de PM10 méditerranéens et donc
  **occitans** ;
* `pm10_wildfires` — les feux, **à jour dans ce flux** alors que notre GFAS a quinze mois
  de retard ;
* `pm2.5_total_organic_matter` — l'organique secondaire, mal contraint par les inventaires.

⚠️ **Réserve à porter avec tout résultat** : Copernicus ne valide contre observations que
NO, NO₂, SO₂, O₃, PM2,5, PM10 et `dust`. Les cinq autres sont **expérimentales**. Comme
prédicteurs d'un résidu — et non comme vérité — c'est acceptable ; le dire ne l'est pas
moins.

Le dimensionnement, et le défaut qu'il corrige
------------------------------------------------
`copernicus.py` télécharge **une espèce par requête** : 31 j × 73 échéances = 2 263 champs,
soit **45 % du plafond de 5 000**. Le commentaire d'origine explique qu'à trois espèces on
dépassait (6 789) — mais on est passé de trois à **une** au lieu de **deux**. C'est la
règle 1 de `CLAUDE.md` appliquée à l'envers, dans le fichier même qui l'a fait naître.

Ici on vise 70-90 % comme la règle l'exige. En restreignant aux échéances **J+1**
(25-48 h), une espèce-mois ne coûte que 744 champs : **six espèces par requête = 4 464,
soit 89 % du plafond**, et un mois par requête au lieu de six.

Usage : python3 scripts/telecharger_speciation_cams.py --debut 2025-01 --fin 2025-01
        python3 scripts/telecharger_speciation_cams.py --debut 2024-01 --fin 2026-08
Sortie : data/raw/cams_speciation/speciation_AAAAMM.nc
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import copernicus as cop  # noqa: E402
from download_copernicus import lire_cle  # noqa: E402

DEST = RACINE / "data/raw/cams_speciation"

ESPECES = [
    "residential_elementary_carbon",
    "secondary_inorganic_aerosol",
    "pm2.5_nitrate",
    "dust",
    "pm10_wildfires",
    "pm2.5_total_organic_matter",
]

# ── Échéances J+1 : les 24 heures du lendemain d'une sortie à 00 UTC ─────────────────
# ⚠️ **`horizon=2` du dépôt vaut J+1, et `horizon=1` vaut J0** (§ « J+1 désignait du J0 »).
# Les échéances 25-48 h couvrent donc bien le jour J+1 d'une sortie à 00 UTC, qui est
# l'échéance du duel PREV'AIR et des bancs LCSQA publiés.
ECHEANCES_J1 = list(range(25, 49))

TAILLE_MIN = 200_000  # un NetCDF de six espèces sur 24 échéances fait plusieurs Mo


def telecharger_mois(ident: cop.Identifiants, an: int, mo: int) -> tuple[str, str]:
    nom = f"speciation_{an}{mo:02d}.nc"
    final = DEST / nom
    # Reprise sur le CONTENU, jamais sur la seule existence (§ 4) : un fichier tronqué
    # par une coupure s'ouvre parfois sans erreur et livre des champs partiels.
    if final.exists() and final.stat().st_size >= TAILLE_MIN:
        return nom, "déjà présent"
    partiel = DEST / f"{nom}.partiel"
    requete = cop.requete_cams_prevision(an, mo, variables=ESPECES,
                                         echeances_h=ECHEANCES_J1)
    t0 = time.time()
    cop.executer(ident, cop.JEU_CAMS_PREVISION, requete, str(partiel))
    if not partiel.exists() or partiel.stat().st_size < TAILLE_MIN:
        taille = partiel.stat().st_size if partiel.exists() else 0
        return nom, f"❌ {taille} octets reçus (< {TAILLE_MIN}) — page d'erreur probable"
    partiel.rename(final)
    return nom, f"OK {partiel_mo(final)} Mo · {time.time() - t0:.0f}s"


def partiel_mo(p: Path) -> int:
    return round(p.stat().st_size / 1e6)


def main(debut: str, fin: str, paralleles: int) -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    d0 = date(int(debut[:4]), int(debut[5:7]), 1)
    d1 = date(int(fin[:4]), int(fin[5:7]), 1)
    mois = list(cop.mois_entre(d0, d1))

    cout = cop.cout_champs(len(ESPECES), len(ECHEANCES_J1))
    print(f"{len(ESPECES)} espèces · {len(ECHEANCES_J1)} échéances (J+1) · "
          f"{cout} champs/requête = {100 * cout / cop.PLAFOND_CHAMPS_ADS:.0f} % du plafond\n"
          f"{len(mois)} mois demandés · {paralleles} requêtes simultanées "
          f"(3 passent, 6 sont rejetées — mesuré)", flush=True)

    ident = cop.Identifiants(url=cop.URL_ADS, cle=lire_cle())
    cop.accepter_licence(ident)

    t0, faits, echecs = time.time(), 0, []
    with ThreadPoolExecutor(max_workers=paralleles) as pool:
        futurs = [pool.submit(telecharger_mois, ident, a, m) for a, m in mois]
        for n, f in enumerate(futurs, start=1):
            nom, etat = f.result()
            print(f"  [{n}/{len(mois)}] {int(time.time() - t0):5d}s  {nom}  {etat}",
                  flush=True)
            faits += 1
            if etat.startswith("❌"):
                echecs.append(nom)

    # Le contrôle de fin porte sur l'ARTEFACT, jamais sur le code de sortie (§ 1 bis).
    sur_disque = sorted(DEST.glob("speciation_*.nc"))
    print(f"\n{len(sur_disque)} fichier(s) sur disque · "
          f"{sum(p.stat().st_size for p in sur_disque) / 1e9:.2f} Go · "
          f"{len(echecs)} échec(s) · {(time.time() - t0) / 60:.1f} min", flush=True)
    if echecs:
        print(f"❌ échecs : {', '.join(echecs[:8])}", flush=True)
        return 1
    if not sur_disque:
        print("❌ AUCUN fichier écrit", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--debut", default="2025-01", help="AAAA-MM")
    a.add_argument("--fin", default="2025-01", help="AAAA-MM")
    a.add_argument("--paralleles", type=int, default=3,
                   help="3 passent, 6 sont rejetées puis le client échoue en HTTP 400")
    n = a.parse_args()
    raise SystemExit(main(n.debut, n.fin, n.paralleles))
