#!/usr/bin/env python3
"""Étendre les prévisions CAMS de J+2 à J+3 — échéances 73 à 96 h.

Pourquoi ne pas simplement retélécharger
------------------------------------------
Une requête 0-96 h sur deux mois coûte **120 % du plafond ADS** : elle serait refusée.
Et retélécharger l'existant représenterait 21 Go pour 5 Go d'information nouvelle.

On ne demande donc que la **tranche manquante**, 73-96 h, à 15 % du plafond par mois.

⚠️ Pourquoi mois par mois plutôt que groupé
---------------------------------------------
La règle 1 du projet dit qu'un coût **par requête** impose de regrouper. C'est vrai quand
l'attente en file domine — ce fut le cas sur ERA5, et l'oublier a coûté treize heures.

Mesuré ici, ce n'est **pas** le cas : 49 Mo en 85 s, soit 0,6 Mo/s, contre 0,52 Mo/s pour
les requêtes 0-72 h de 149 Mo. Le débit est le même : c'est le **transfert** qui domine, pas
la file. Grouper ne gagnerait rien et compliquerait le décodage de l'axe aplati.

**La consigne du fournisseur répond à SA question, pas à la tienne** — et la mesure
tranche, pas l'habitude.

⚠️ L'axe temporel est APLATI, et c'est le piège
-------------------------------------------------
La passe unitaire du 03/08 a montré que le service ne renvoie **pas** une archive de
fichiers journaliers pour cette tranche, mais un **netCDF unique** dont l'axe `time` compte
**744 valeurs de 73 à 816** — soit 31 jours × 24 échéances aplatis en une dimension.

C'est exactement le piège que `CLAUDE.md` § 2 bis documente, avec le même nombre : *« un
test exigeait un axe de taille 24 alors que le service aplatit date × échéance en un axe de
744 »*.

Le décodage, vérifié sur les données :

    jour     = (time − 73) // 24     →  31 valeurs distinctes ✓
    échéance = ((time − 73) % 24) + 73  →  exactement 73…96 ✓

Et **validé par la physique** : le PM10 moyen culmine à l'échéance 78 h et creuse à 87 h,
soit 06 h et 15 h UTC — pic matinal sous couche limite basse, creux d'après-midi une fois
l'air brassé. Un décodage faux donnerait un profil plat ou incohérent.

Le raccord avec l'existant
----------------------------
`aq.features.meteo` lit l'échéance dans la coordonnée `time` et la **date de base dans le
nom du fichier** (`\\d{4}-\\d{2}-\\d{2}` n'importe où). On découpe donc le fichier plat en
journées nommées `ENS_FORECAST_J3_AAAA-MM-JJ.nc`, déposées **dans le dossier existant** :
l'extraction les lira à côté des `ENS_FORECAST_AAAA-MM-JJ.nc` de 0 à 72 h, et les
concaténera naturellement.

Usage : python3 scripts/etendre_j3.py [--especes pm10,o3] [--debut 2023-08] [--fin 2026-07]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import copernicus as cop  # noqa: E402
from download_copernicus import SERVICES, lire_cle  # noqa: E402

BRUT = RACINE / "data/raw/cams_prevision"
ECHEANCES = list(range(73, 97))
VARIABLE = {"pm10": "particulate_matter_10um", "pm25": "particulate_matter_2.5um",
            "o3": "ozone", "no2": "nitrogen_dioxide"}
PREFIXE = "ENS_FORECAST_J3_"


def decouper(fichier: Path, destination: Path, annee: int, mois: int) -> int:
    """Découpe le netCDF plat en journées, avec l'échéance restaurée.

    Contrôles avant écriture — un découpage faux produirait des horodatages plausibles
    et faux, ce que rien ne rattraperait ensuite.
    """
    import xarray as xr

    d = xr.open_dataset(fichier)
    t = d["time"].values.astype(int)
    jours = (t - ECHEANCES[0]) // len(ECHEANCES)
    ech = ((t - ECHEANCES[0]) % len(ECHEANCES)) + ECHEANCES[0]

    n_jours = pd.Period(f"{annee}-{mois:02d}").days_in_month
    if set(ech) != set(ECHEANCES):
        raise SystemExit(f"{fichier.name} : échéances décodées {sorted(set(ech))[:5]}… "
                         f"— attendu {ECHEANCES[0]}…{ECHEANCES[-1]}")
    if len(set(jours)) != n_jours:
        raise SystemExit(f"{fichier.name} : {len(set(jours))} jours décodés pour "
                         f"{n_jours} attendus en {annee}-{mois:02d}")

    destination.mkdir(parents=True, exist_ok=True)
    ecrits = 0
    for j in sorted(set(jours)):
        masque = jours == j
        sous = d.isel(time=np.flatnonzero(masque))
        sous = sous.assign_coords(time=("time", ech[masque]))
        jour = pd.Timestamp(f"{annee}-{mois:02d}-01") + pd.Timedelta(days=int(j))
        cible = destination / f"{PREFIXE}{jour:%Y-%m-%d}.nc"
        partiel = cible.with_suffix(".nc.partiel")
        sous.to_netcdf(partiel)
        partiel.replace(cible)          # nom définitif = fichier complet
        ecrits += 1
    return ecrits


def main(especes: list[str], debut: str, fin: str) -> int:
    url, jeu = SERVICES["cams_prevision"]
    ident = cop.Identifiants(url=url, cle=lire_cle())
    mois = pd.period_range(debut, fin, freq="M")
    taches = [(e, p.year, p.month) for e in especes for p in mois]

    print(f"{len(taches)} tâches · {len(especes)} espèces × {len(mois)} mois · "
          f"échéances {ECHEANCES[0]}-{ECHEANCES[-1]} h", flush=True)
    depart, faits, sautes, echecs = time.time(), 0, 0, 0
    tmp = RACINE / "data/raw/.j3_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    for i, (esp, an, mo) in enumerate(taches, 1):
        # Le dossier cible est celui de la tranche 0-72 h — nom simple ou groupé.
        cands = sorted(BRUT.glob(f"cams_prevision_{esp}_*{an}{mo:02d}*"))
        cands = [c for c in cands if c.is_dir()]
        if not cands:
            print(f"  [{i}/{len(taches)}] {esp} {an}-{mo:02d} · dossier 0-72 h absent, "
                  f"sauté", flush=True)
            sautes += 1
            continue
        dest = cands[0]
        n_attendu = pd.Period(f"{an}-{mo:02d}").days_in_month
        # ⚠️ Les dossiers sont GROUPÉS par deux mois (`..._202308_202309`, 61 jours).
        # Compter les fichiers J3 du dossier entier contre le calendrier d'UN mois faisait
        # sauter le second : après août (31 fichiers), septembre voyait 31 ≥ 30 et passait.
        # Onze mois sur trente-six ont été annoncés « déjà faits » sans l'être.
        #
        # C'est la règle 4 encore : le test de reprise porte sur le contenu ATTENDU — ici
        # les journées de CE mois, nommément, pas un total.
        jours = pd.date_range(f"{an}-{mo:02d}-01", periods=n_attendu)
        presents = sum((dest / f"{PREFIXE}{d:%Y-%m-%d}.nc").exists() for d in jours)
        if presents >= n_attendu:
            sautes += 1
            continue
        if presents:
            print(f"  [{i}/{len(taches)}] {esp} {an}-{mo:02d} · {presents}/{n_attendu} "
                  f"jours présents — repris", flush=True)
        try:
            req = cop.requete_cams_prevision(an, mo, variables=[VARIABLE[esp]],
                                             echeances_h=ECHEANCES)
            brut = tmp / f"{esp}_{an}{mo:02d}.nc"
            cop.executer(ident, jeu, req, str(brut))
            n = decouper(brut, dest, an, mo)
            brut.unlink(missing_ok=True)
            faits += 1
            reste = (time.time() - depart) / max(faits, 1) * (len(taches) - i)
            print(f"  [{i}/{len(taches)}] {esp} {an}-{mo:02d} · {n} jours · "
                  f"{time.time() - depart:5.0f}s · fin dans ~{reste / 60:.0f} min",
                  flush=True)
        except Exception as e:  # noqa: BLE001
            # On journalise ET on compte : un échec avalé rendrait un lot « réussi »
            # avec des trous invisibles.
            print(f"  [{i}/{len(taches)}] {esp} {an}-{mo:02d} · ÉCHEC "
                  f"{type(e).__name__}: {str(e)[:90]}", flush=True)
            echecs += 1

    print(f"\n{faits} étendus · {sautes} déjà faits ou sans base · {echecs} échecs · "
          f"{(time.time() - depart) / 60:.0f} min")
    return 1 if echecs else 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--especes", default="pm10,o3,no2,pm25")
    a.add_argument("--debut", default="2023-08")
    a.add_argument("--fin", default="2026-07")
    n = a.parse_args()
    raise SystemExit(main([e.strip() for e in n.especes.split(",")], n.debut, n.fin))
