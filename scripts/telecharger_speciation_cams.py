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

# ── Le second lot, ouvert le 23/08/2026 — six variables, six mécanismes déclarés ──────
#
# Le catalogue expose 28 variables ; nous en tirions 12 (les 4 masses totales + les 8 de
# spéciation). Les six ci-dessous sont choisies pour un mécanisme nommé AVANT la mesure,
# jamais pour compléter une liste. ⚠️ `nitric_acid` figurait dans la première sélection :
# le catalogue interrogé le 23/08 ne l'expose pas. Les noms sont vérifiés contre
# `catalogue/v1/collections/.../form.json`, pas devinés — un service qui reçoit un nom
# invalide sert le reste sans lever (§ 2 bis).
PRECURSEURS = [
    # l'épandage agricole, et le précurseur du nitrate d'ammonium qui fait les épisodes
    # de particules du printemps
    "ammonia",
    # l'autre moitié du SIA : sulfate et nitrate n'ont ni la même chimie ni la même
    # saisonnalité, et le total les confond
    "pm2.5_sulphate",
    # ferme le triplet SIA — le rapport ammonium/nitrate dit quel précurseur limite
    "pm2.5_ammonium",
    # le précurseur gazeux du sulfate : industrie, maritime
    "sulphur_dioxide",
    # réservoir d'azote transporté : sépare l'ozone importé de l'ozone produit sur place
    "peroxyacyl_nitrates",
    # le second précurseur de l'ozone — le régime COV-limité contre NOx-limité est la
    # question centrale de la photochimie urbaine, et rien dans nos variables ne le dit
    "non_methane_vocs",
]
# ── Le troisième lot, ouvert le 23/08/2026 sous CONTRAINTE D'ARCHIVE ─────────────────
#
# 🔴 Le catalogue CAMS Europe est une **archive glissante de trois ans** — signalé par une
# revue externe, et corroboré par nos propres fichiers : les précurseurs téléchargés cette
# nuit commencent le **18 août 2023**, soit exactement trois ans avant le jour du
# téléchargement. Ce n'était pas un démarrage de flux, c'était **le bord de la fenêtre**.
#
# Conséquence, et elle inverse la discipline habituelle : chaque mois écoulé rend un mois de
# plus **définitivement** inaccessible. On acquiert donc AVANT de tester, contrairement à la
# règle 1 qui veut qu'on mesure avant d'engager le volume — parce qu'ici le coût d'attendre
# n'est pas du temps, c'est de la donnée perdue.
CHIMIE = [
    # produits d'oxydation des COV : plus près de la production d'ozone et d'aérosol
    # organique secondaire que la masse de COV elle-même
    "formaldehyde",
    "glyoxal",
    # la titration locale de l'ozone par le monoxyde d'azote, que le NO₂ seul ne dit pas
    "nitrogen_monoxide",
    # traceur de combustion fraîche, longue durée de vie — sépare l'apport local du transporté
    "carbon_monoxide",
    # ⚠️ Les deux suivants sont pris comme ASSURANCE, pas comme piste : le pollen EST de la
    # matière particulaire, il pèse sur les PM10 au printemps, et l'archive se referme. Ils
    # ne coûtent aucune requête de plus (6 espèces = 89 % du plafond, 4 en coûteraient 60 %)
    # et ne seront pas testés en priorité.
    "birch_pollen",
    "grass_pollen",
]

# Les quatre polluants cibles, en ALTITUDE. Le contraste vertical dit le confinement près du
# sol, que la valeur de surface et sa forme horaire ne peuvent pas reconstruire.
# ⚠️ Un niveau est une dimension du coût : 4 espèces × 2 niveaux = 5 952 champs, au-dessus du
# plafond de 5 000. D'où un lot par niveau, à 60 % du plafond — la granularité est imposée
# par la structure, pas choisie.
CIBLES = ["ozone", "nitrogen_dioxide", "particulate_matter_10um", "particulate_matter_2.5um"]

# {nom du lot : (espèces, niveaux)} — le nom du lot entre dans le nom du fichier, donc dans
# la reprise : deux jeux d'espèces ne peuvent pas se confondre.
LOTS = {
    "speciation": (ESPECES, ["0"]),
    "precurseurs": (PRECURSEURS, ["0"]),
    "chimie": (CHIMIE, ["0"]),
    "vertical100": (CIBLES, ["100"]),
    "vertical500": (CIBLES, ["500"]),
}

# ── Échéances J+1 : les 24 heures du lendemain d'une sortie à 00 UTC ─────────────────
# ⚠️ **`horizon=2` du dépôt vaut J+1, et `horizon=1` vaut J0** (§ « J+1 désignait du J0 »).
# Les échéances 25-48 h couvrent donc bien le jour J+1 d'une sortie à 00 UTC, qui est
# l'échéance du duel PREV'AIR et des bancs LCSQA publiés.
ECHEANCES_J1 = list(range(25, 49))

TAILLE_MIN = 200_000  # un NetCDF de six espèces sur 24 échéances fait plusieurs Mo


def telecharger_mois(ident: cop.Identifiants, an: int, mo: int,
                     lot: str = "speciation") -> tuple[str, str]:
    # ⚠️ Le nom du fichier porte le LOT, donc les espèces qu'il contient. Réutiliser
    # `speciation_*.nc` pour un autre jeu de variables ferait mentir le nom, et la reprise
    # sauterait des mois qui ne contiennent pas ce qu'on croit (§ 4 bis).
    especes, niveaux = LOTS[lot]
    nom = f"{lot}_{an}{mo:02d}.nc"
    final = DEST / nom
    # Reprise sur le CONTENU, jamais sur la seule existence (§ 4) : un fichier tronqué
    # par une coupure s'ouvre parfois sans erreur et livre des champs partiels.
    if final.exists() and final.stat().st_size >= TAILLE_MIN:
        return nom, "déjà présent"
    partiel = DEST / f"{nom}.partiel"
    requete = cop.requete_cams_prevision(an, mo, variables=especes,
                                         echeances_h=ECHEANCES_J1,
                                         niveaux=niveaux)
    t0 = time.time()
    cop.executer(ident, cop.JEU_CAMS_PREVISION, requete, str(partiel))
    if not partiel.exists() or partiel.stat().st_size < TAILLE_MIN:
        taille = partiel.stat().st_size if partiel.exists() else 0
        return nom, f"❌ {taille} octets reçus (< {TAILLE_MIN}) — page d'erreur probable"
    partiel.rename(final)
    return nom, f"OK {partiel_mo(final)} Mo · {time.time() - t0:.0f}s"


def partiel_mo(p: Path) -> int:
    return round(p.stat().st_size / 1e6)


def main(debut: str, fin: str, paralleles: int, lot: str = "speciation") -> int:
    especes, niveaux = LOTS[lot]
    DEST.mkdir(parents=True, exist_ok=True)
    d0 = date(int(debut[:4]), int(debut[5:7]), 1)
    d1 = date(int(fin[:4]), int(fin[5:7]), 1)
    mois = list(cop.mois_entre(d0, d1))

    cout = cop.cout_champs(len(especes) * len(niveaux), len(ECHEANCES_J1))
    print(f"lot « {lot} » : {', '.join(especes)} · niveau(x) {', '.join(niveaux)} m\n"
          f"{len(especes)} espèces · {len(ECHEANCES_J1)} échéances (J+1) · "
          f"{cout} champs/requête = {100 * cout / cop.PLAFOND_CHAMPS_ADS:.0f} % du plafond\n"
          f"{len(mois)} mois demandés · {paralleles} requêtes simultanées "
          f"(3 passent, 6 sont rejetées — mesuré)", flush=True)

    ident = cop.Identifiants(url=cop.URL_ADS, cle=lire_cle())
    cop.accepter_licence(ident)

    t0, faits, echecs = time.time(), 0, []
    with ThreadPoolExecutor(max_workers=paralleles) as pool:
        futurs = [pool.submit(telecharger_mois, ident, a, m, lot) for a, m in mois]
        for n, f in enumerate(futurs, start=1):
            nom, etat = f.result()
            print(f"  [{n}/{len(mois)}] {int(time.time() - t0):5d}s  {nom}  {etat}",
                  flush=True)
            faits += 1
            if etat.startswith("❌"):
                echecs.append(nom)

    # Le contrôle de fin porte sur l'ARTEFACT, jamais sur le code de sortie (§ 1 bis).
    sur_disque = sorted(DEST.glob(f"{lot}_*.nc"))
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
    a.add_argument("--lot", default="speciation", choices=sorted(LOTS),
                   help="quel jeu d'espèces — le nom du fichier le porte")
    a.add_argument("--paralleles", type=int, default=3,
                   help="3 passent, 6 sont rejetées puis le client échoue en HTTP 400")
    n = a.parse_args()
    raise SystemExit(main(n.debut, n.fin, n.paralleles, n.lot))
