#!/usr/bin/env python3
"""Le lot des membres d'ensemble CAMS — après passe unitaire validée.

Ce que la passe unitaire a établi (`scripts/passe_unitaire_membres.py`, 30/07)
------------------------------------------------------------------------------
- 6 membres × 24 échéances × 31 jours = **4 464 champs, 89 % du plafond** ADS ;
- le `.nc` livré est une **archive ZIP** de 6 entrées — une par membre ;
- axe `time` de 744 = 31 jours × 24 échéances, et non un axe d'échéances séparé ;
- **394 s par requête** → 51 requêtes (17 mois × 3 espèces) = **5,6 h, ~15 Go**.

Pourquoi ces six membres et ces 24 échéances
--------------------------------------------
Le projet ne télécharge aujourd'hui que la **médiane** de l'ensemble, et jette la dispersion
des 11 modèles. Or ce désaccord est une estimation d'incertitude **native**, disponible avant
l'observation — ce que ni le détecteur d'anomalies ni l'écart entre échéances n'ont su
fabriquer. Elle sert trois questions ouvertes : incertitude, stratification *ex ante* de la
dérive, et signal de coupure.

Onze membres ne tiendraient pas sous le plafond. Six suffisent à estimer une dispersion, et
couvrent des chimies distinctes : CHIMERE (celui de PREV'AIR), MOCAGE (Météo-France), EMEP,
SILAM, LOTOS-EUROS, MATCH.

Les 24 échéances sont exactement la tranche J+1 du projet, `TRANCHES[1] = (1, 24)`. Nous en
téléchargions 73 sans en utiliser plus de 24 : c'est ce gaspillage qui finance les six membres.

Usage : python3 scripts/lot_membres_ensemble.py [--especes ozone,nitrogen_dioxide,particulate_matter_2.5um]
"""

from __future__ import annotations

import argparse
import sys
import time
import zipfile
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import copernicus as cop  # noqa: E402
from download_copernicus import SERVICES, lire_cle  # noqa: E402

DOSSIER = RACINE / "data/raw/cams_membres"
DEBUT, FIN = date(2023, 8, 1), date(2024, 12, 31)
ABREGE = {"ozone": "o3", "nitrogen_dioxide": "no2", "particulate_matter_2.5um": "pm25"}


def complet(chemin: Path, n_membres: int) -> str:
    """Vérifie le **contenu**, jamais la seule existence du fichier.

    Un mois arrivé avec deux membres sur six s'ouvrirait sans erreur, serait écrit sous son nom
    définitif, et sauté à jamais par la reprise. Le trou n'apparaîtrait qu'en fin de chaîne.
    """
    if not zipfile.is_zipfile(chemin):
        return "pas une archive ZIP"
    with zipfile.ZipFile(chemin) as z:
        n = len(z.namelist())
    return "" if n == n_membres else f"{n} membres sur {n_membres}"


def main(especes: list[str]) -> int:
    DOSSIER.mkdir(parents=True, exist_ok=True)
    membres = cop.MEMBRES_DIVERSIFIES
    url, jeu = SERVICES["cams_prevision"]
    identifiants = cop.Identifiants(url=url, cle=lire_cle())

    plan = [(a, m, e) for e in especes for a, m in cop.mois_entre(DEBUT, FIN)]
    reste = [(a, m, e) for a, m, e in plan
             if not (DOSSIER / f"membres_{ABREGE[e]}_{a}{m:02d}.nc").exists()]
    print(f"{len(plan)} requêtes au plan · {len(reste)} à faire · "
          f"{len(membres)} membres · échéances 1-24", flush=True)
    if not reste:
        print("rien à faire")
        return 0
    print(f"extrapolation : {len(reste)} × 394 s ≈ **{len(reste) * 394 / 3600:.1f} h**\n",
          flush=True)

    debut = time.time()
    for n, (annee, mois, espece) in enumerate(reste, start=1):
        cible = DOSSIER / f"membres_{ABREGE[espece]}_{annee}{mois:02d}.nc"
        partiel = cible.with_suffix(".nc.partiel")
        requete = cop.requete_cams_prevision(
            annee, mois, variables=[espece], echeances_h=range(1, 25), modeles=membres)
        t0 = time.time()
        try:
            cop.executer(identifiants, jeu, requete, str(partiel))
        except Exception as exc:  # noqa: BLE001
            print(f"[{n}/{len(reste)}] {cible.name} ÉCHEC "
                  f"{type(exc).__name__}: {str(exc)[:120]}", flush=True)
            partiel.unlink(missing_ok=True)
            continue

        probleme = complet(partiel, len(membres))
        if probleme:
            print(f"[{n}/{len(reste)}] {cible.name} REJETÉ — {probleme}", flush=True)
            partiel.unlink(missing_ok=True)
            continue

        # Renommage seulement après vérification du contenu : un nom définitif vaut marque
        # d'achèvement pour la reprise.
        partiel.rename(cible)
        ecoule = time.time() - debut
        print(f"[{n}/{len(reste)}] {cible.name} · {cible.stat().st_size / 1e6:.0f} Mo · "
              f"{time.time() - t0:.0f}s · écoulé {ecoule / 60:.0f} min · "
              f"reste ~{ecoule / n * (len(reste) - n) / 60:.0f} min", flush=True)

    faits = sorted(DOSSIER.glob("membres_*.nc"))
    print(f"\n{len(faits)} mois-espèce sur disque · "
          f"{sum(f.stat().st_size for f in faits) / 1e9:.1f} Go · "
          f"{(time.time() - debut) / 3600:.1f} h", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--especes", default="ozone")
    args = p.parse_args()
    raise SystemExit(main([e.strip() for e in args.especes.split(",")]))
