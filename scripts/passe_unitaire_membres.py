#!/usr/bin/env python3
"""Passe unitaire avant le lot des membres d'ensemble CAMS — les deux axes, puis extrapoler.

La règle 1 du projet, appliquée intégralement
---------------------------------------------
1. **Interroger les limites** : plafond 5 000 champs, vérifié dans `cout_champs`.
2. **Dimensionner à 70-90 %** : 6 membres × 24 échéances × 31 jours = **4 464 champs, 89 %**.
3. **Tester cette requête-là**, sur les deux axes — et c'est l'oubli du second qui avait coûté
   treize heures la première fois.
4. Lancer le lot seulement ensuite.

Axe **résultat** — trois pièges déjà rencontrés sur ce service :
- un `.nc` peut être une **archive ZIP** ;
- un mois peut arriver **amputé** d'une partie de ses membres sans qu'aucune erreur ne soit
  levée, puis être écrit sous son nom définitif et sauté à jamais par la reprise ;
- les six membres doivent tous être **présents et distincts** : si le service renvoie six fois
  la médiane, la dispersion serait nulle et le projet mesurerait du vide.

Axe **coût** — chronométrer, ventiler l'attente en file, le calcul serveur et le transfert,
puis extrapoler `t_unitaire × N` **avant** de lancer.

Usage : python3 scripts/passe_unitaire_membres.py [--annee 2024] [--mois 7]
"""

from __future__ import annotations

import argparse
import sys
import time
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.ingest import copernicus as cop  # noqa: E402

DOSSIER = RACINE / "data/raw/cams_membres"
N_MOIS_LOT = 17 * 3  # 17 mois appariés × 3 espèces


def inspecter(chemin: Path) -> dict:
    """Ce que le fichier contient réellement — jamais ce que son nom promet."""
    import xarray as xr

    infos = {"zip": zipfile.is_zipfile(chemin),
             "taille_mo": chemin.stat().st_size / 1e6}
    ouvrir = chemin
    if infos["zip"]:
        # Le piège du ZIP déguisé : extraire avant d'ouvrir, sinon xarray échoue sur un
        # message qui n'évoque pas l'archive.
        with zipfile.ZipFile(chemin) as z:
            noms = z.namelist()
            infos["membres_zip"] = len(noms)
            cible = DOSSIER / "_unitaire"
            cible.mkdir(parents=True, exist_ok=True)
            z.extractall(cible)
            ouvrir = cible / noms[0]
    jeu = xr.open_dataset(ouvrir)
    infos["variables"] = list(jeu.data_vars)
    infos["dimensions"] = {k: int(v) for k, v in jeu.sizes.items()}
    return infos


def main(annee: int, mois: int, espece: str) -> int:
    DOSSIER.mkdir(parents=True, exist_ok=True)
    membres = cop.MEMBRES_DIVERSIFIES
    requete = cop.requete_cams_prevision(
        annee, mois, variables=[espece], echeances_h=range(1, 25), modeles=membres)
    cout = cop.cout_champs(1, 24) * len(membres)
    print(f"Requête : {espece} · {annee}-{mois:02d} · {len(membres)} membres "
          f"({', '.join(membres)}) · échéances 1-24")
    print(f"Coût : {cout} champs = {100 * cout / cop.PLAFOND_CHAMPS_ADS:.0f} % du plafond\n",
          flush=True)

    sys.path.insert(0, str(RACINE / "scripts"))
    from download_copernicus import SERVICES, lire_cle

    url, _ = SERVICES["cams_prevision"]
    identifiants = cop.Identifiants(url=url, cle=lire_cle())
    cible = DOSSIER / f"membres_{espece[:4]}_{annee}{mois:02d}.nc"
    partiel = cible.with_suffix(".nc.partiel")

    debut = time.time()
    try:
        cop.executer(identifiants, cop.JEU_CAMS_PREVISION, requete, str(partiel))
    except Exception as exc:  # noqa: BLE001
        print(f"ÉCHEC {type(exc).__name__}: {str(exc)[:300]}")
        partiel.unlink(missing_ok=True)
        return 1
    duree = time.time() - debut

    # ── Axe résultat ──────────────────────────────────────────────────────────
    infos = inspecter(partiel)
    print("AXE RÉSULTAT")
    print(f"  taille {infos['taille_mo']:.1f} Mo · archive ZIP : {infos['zip']}"
          + (f" ({infos.get('membres_zip')} entrées)" if infos["zip"] else ""))
    print(f"  variables : {infos['variables']}")
    print(f"  dimensions : {infos['dimensions']}")

    # **Le service aplatit date × échéance en un seul axe `time`.** Une première version de ce
    # contrôle cherchait un axe de taille 24 et déclarait la structure fautive : c'était le
    # contrôle qui était faux, pas la donnée. Un test de conformité mal posé coûte autant qu'une
    # absence de test — il fait rejeter du bon.
    jours = 31 if mois in (1, 3, 5, 7, 8, 10, 12) else (29 if mois == 2 and annee % 4 == 0
                                                        else 28 if mois == 2 else 30)
    attendu_time = jours * 24
    manques = []
    dims = infos["dimensions"]
    if dims.get("time") != attendu_time:
        manques.append(f"axe time = {dims.get('time')} au lieu de {attendu_time} "
                       f"({jours} jours × 24 échéances)")
    # Un membre par entrée de l'archive : c'est la garantie que le service n'a pas servi
    # six fois la médiane, auquel cas la dispersion serait nulle et le projet mesurerait du vide.
    if infos.get("membres_zip") != len(membres):
        manques.append(f"{infos.get('membres_zip')} entrées dans l'archive pour "
                       f"{len(membres)} membres demandés")
    print(f"  → {'⚠️ ' + ' · '.join(manques) if manques else '✅ structure conforme'}\n",
          flush=True)

    # ── Axe coût ──────────────────────────────────────────────────────────────
    debit = infos["taille_mo"] / duree
    print("AXE COÛT")
    print(f"  durée totale {duree:.0f}s · débit apparent {debit:.2f} Mo/s")
    print(f"  extrapolation lot : {duree:.0f}s × {N_MOIS_LOT} = "
          f"**{duree * N_MOIS_LOT / 3600:.1f} h**")
    print(f"  volume estimé : {infos['taille_mo'] * N_MOIS_LOT / 1000:.1f} Go", flush=True)

    if manques:
        print("\nLot NON lancé : corriger la structure d'abord.")
        partiel.unlink(missing_ok=True)
        return 1
    partiel.rename(cible)
    print(f"\nÉcrit : {cible.relative_to(RACINE)}")
    print("Décider du lot au vu de l'extrapolation ci-dessus, pas de l'envie de le lancer.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--annee", type=int, default=2024)
    p.add_argument("--mois", type=int, default=7)
    p.add_argument("--espece", default="ozone")
    args = p.parse_args()
    raise SystemExit(main(args.annee, args.mois, args.espece))
