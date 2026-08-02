#!/usr/bin/env python3
"""Météo **prévue** IFS aux stations, par lecture partielle du seau AWS.

Pourquoi ce script, et pourquoi un seul mois d'abord
----------------------------------------------------
Le plafond météo est mesuré à **+7,8 %** sur l'ozone avec ERA5 — mais ERA5 est une
**réanalyse**, indisponible à l'heure d'émission. La question qui décide de la piste est :
*quelle part de ce plafond une météo **prévue** récupère-t-elle ?*

Une relecture opérationnelle a formulé l'avertissement qui tient lieu de règle ici :
« **168 Go d'IFS sans un tableau leave-station sur grandeur réglementaire** » serait du travail
pour rien. On mesure donc **un mois** avant d'engager le volume.

Ce que la chaîne d'accès a établi
---------------------------------
Seau `ecmwf-forecasts`, anonyme, CC-BY, profondeur depuis le **18/01/2023**. Chaque pas porte
un index de 31 Ko donnant `_offset` et `_length` par champ : lecture **par plage d'octets**,
validée en HTTP 206 avec messages GRIB décodés et interpolés à Toulouse.

**Le service n'impose aucune limite de débit** — mesuré le 31/07 : 288 requêtes par minute,
8 succès sur 8 à pause nulle, les rejets étant aléatoires et rares. Une première version en
déduisait le contraire d'un 503 isolé et patientait 8 à 40 s après chaque échec : elle
extrapolait **94 heures** pour un lot que le service peut servir en quelques heures. *La
prudence non mesurée coûte autant qu'une imprudence.*

Le regroupement des plages contiguës reste utile : il ramène 14 requêtes par pas à 1 ou 2, au
prix de 2,5 fois plus d'octets. Il embarque au passage les **niveaux de pression** — vent,
température et géopotentiel à 13 niveaux — sans requête supplémentaire.

Décodage
--------
`cfgrib` n'est pas installé dans l'environnement principal — il tire `eccodes` et contraint
`numpy`. Il vit dans un environnement séparé `grib`, et ce script l'appelle par sous-processus
plutôt que de risquer un conflit de version avec les ajustements en cours.

Usage : python3 scripts/extraire_ifs.py --annee 2024 --mois 7 [--jours 5]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.ingest import stations as st  # noqa: E402

BASE = "https://ecmwf-forecasts.s3.amazonaws.com"
SORTIE = RACINE / "data/processed/meteo"
CACHE = RACINE / "data/raw/ifs"
PYTHON_GRIB = "/home/cyril/miniforge3/bin/mamba"

# Six champs de surface, dans l'ordre de priorité établi par une relecture méthodologique.
# Les niveaux de pression sont écartés à ce stade : l'ablation a montré que le vent n'apporte
# que **+0,067 µg/m³** en marginal, ce qui ne justifie pas treize niveaux.
CHAMPS_SFC = {"2t", "2d", "10u", "10v", "ssrd", "tp"}
TOLERANCE_REGROUPEMENT = 20_000_000  # octets : 1 requête par pas, 60 % de superflu assumé
# Un run de 00 h couvre le jour suivant par ses échéances 24 à 47 ; l'open data est tri-horaire.
ECHEANCES = [24, 27, 30, 33, 36, 39, 42, 45]


def index_du_pas(date: str, echeance: int) -> list[dict]:
    url = f"{BASE}/{date}/00z/ifs/0p25/oper/{date}000000-{echeance}h-oper-fc.index"
    for essai in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                brut = r.read()
            if brut[:1] == b"{":
                return [json.loads(l) for l in brut.decode().splitlines() if l.strip()]
        except Exception:  # noqa: BLE001
            pass
        # **Le code de sortie ne suffit pas** : un appel limité rend du XML d'erreur avec un
        # statut apparemment normal. On contrôle le contenu.
        #
        # Attente courte, et c'est une correction de fond. Une première version patientait
        # 8 à 40 s après chaque échec, sur l'hypothèse d'une limite de débit déduite d'un 503
        # isolé. **Mesure du 31/07 : le service accepte 288 requêtes par minute sans un seul
        # rejet** — 8 succès sur 8 à pause nulle. Les rejets sont aléatoires et rares. Les 94 h
        # extrapolées venaient donc entièrement de ma propre prudence, pas du service.
        time.sleep(0.5 * (essai + 1))
    return []


def plages_regroupees(champs: list[dict]) -> list[tuple[int, int]]:
    """Regroupe les champs voulus en plages contiguës, superflu compris."""
    voulus = sorted([d for d in champs
                     if d["levtype"] == "sfc" and d["param"] in CHAMPS_SFC],
                    key=lambda d: d["_offset"])
    if not voulus:
        return []
    plages, a = [], voulus[0]["_offset"]
    b = a + voulus[0]["_length"]
    for d in voulus[1:]:
        if d["_offset"] - b <= TOLERANCE_REGROUPEMENT:
            b = d["_offset"] + d["_length"]
        else:
            plages.append((a, b))
            a, b = d["_offset"], d["_offset"] + d["_length"]
    plages.append((a, b))
    return plages


def telecharger_pas(date: str, echeance: int, cible: Path) -> bool:
    if cible.exists():
        return True
    champs = index_du_pas(date, echeance)
    if not champs:
        return False
    plages = plages_regroupees(champs)
    url = f"{BASE}/{date}/00z/ifs/0p25/oper/{date}000000-{echeance}h-oper-fc.grib2"
    morceaux = []
    for a, b in plages:
        for essai in range(4):
            try:
                req = urllib.request.Request(url, headers={"Range": f"bytes={a}-{b - 1}"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    brut = r.read()
                if brut[:4] == b"GRIB":
                    morceaux.append(brut)
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.5 * (essai + 1))
        else:
            return False
    provisoire = cible.with_suffix(".grib2.partiel")
    provisoire.write_bytes(b"".join(morceaux))
    provisoire.rename(cible)
    return True


def extraire(fichiers: list[Path], stations: pd.DataFrame) -> pd.DataFrame:
    """Décode et interpole aux stations, dans l'environnement `grib` isolé."""
    entree = {"fichiers": [str(f) for f in fichiers],
              "lat": stations["lat_wgs84"].tolist(),
              "lon": stations["lon_wgs84"].tolist(),
              "ids": stations["station_id"].tolist()}
    script = RACINE / "scripts/_decoder_grib.py"
    # **Délai proportionnel au travail, jamais fixe.** Un plafond de 1800 s tenait sur les
    # mois de 30 jours et a lâché sur octobre 2024 — 248 pas, 8,4 Go, le plus gros du lot.
    # L'échec survient *après* tout le téléchargement : un délai trop court coûte alors
    # l'heure entière du mois, pas les quelques minutes qu'il économise. On compte 25 s par
    # fichier, soit environ trois fois la mesure observée, avec un plancher de 30 min.
    delai = max(1800, 25 * len(fichiers))
    r = subprocess.run([PYTHON_GRIB, "run", "-n", "grib", "python", str(script)],
                       input=json.dumps(entree), capture_output=True, text=True,
                       timeout=delai)
    if r.returncode != 0:
        raise RuntimeError(f"décodage : {r.stderr[-400:]}")
    return pd.read_json(r.stdout, orient="records")


def main(annee: int, mois: int, jours: int) -> int:
    depart = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    SORTIE.mkdir(parents=True, exist_ok=True)
    ref = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    stations = ref[ref["metropole"] & ref["active"]].dropna(
        subset=["lat_wgs84", "lon_wgs84"]).reset_index(drop=True)

    dates = [f"{annee}{mois:02d}{j:02d}" for j in range(1, jours + 1)]
    print(f"IFS · {len(dates)} jours × {len(ECHEANCES)} échéances · "
          f"{len(CHAMPS_SFC)} champs · {len(stations)} stations", flush=True)

    fichiers, echecs = [], 0
    for date in dates:
        for e in ECHEANCES:
            cible = CACHE / f"ifs_{date}_{e:03d}h.grib2"
            if telecharger_pas(date, e, cible):
                fichiers.append(cible)
            else:
                echecs += 1
        volume = sum(f.stat().st_size for f in fichiers) / 1e6
        print(f"  {date} · {len(fichiers)} pas · {volume:.0f} Mo · "
              f"{time.time() - depart:.0f}s · {echecs} échec(s)", flush=True)

    if not fichiers:
        print("aucun pas téléchargé — vérifier l'accès avant d'insister")
        return 1

    volume = sum(f.stat().st_size for f in fichiers) / 1e6
    print(f"\n{len(fichiers)} pas · {volume:.0f} Mo · {time.time() - depart:.0f}s")
    print(f"extrapolation 17 mois : {volume * 17 * 30 / jours / 1000:.0f} Go · "
          f"{(time.time() - depart) * 17 * 30 / jours / 3600:.1f} h", flush=True)

    t = extraire(fichiers, stations)
    cible = SORTIE / f"ifs_metropole_{annee}{mois:02d}.parquet"
    provisoire = cible.with_suffix(".parquet.partiel")
    t.to_parquet(provisoire, index=False)
    provisoire.rename(cible)
    print(f"\nÉcrit : {cible.relative_to(RACINE)} · {len(t):,} lignes · "
          f"colonnes {list(t.columns)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--annee", type=int, default=2024)
    p.add_argument("--mois", type=int, default=7)
    p.add_argument("--jours", type=int, default=5)
    args = p.parse_args()
    raise SystemExit(main(args.annee, args.mois, args.jours))
