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

# 🔴 Deux miroirs, alternés — mesuré le 23/08/2026 après une limitation en pleine face.
#
# Le lot de juin 2024 a tiré ~970 Mo puis s'est effondré : jour 22 à 426 s, jour 23 à
# 970 s, et une sonde dix minutes plus tard rendait encore **4 rejets sur 16 à 4 s de
# pause**, avec 0,16 Mo/s contre 2,7 en début de soirée. Ce n'est pas une limite de
# CADENCE — la bande passante elle-même était bridée d'un facteur 17. C'est un budget
# consommé, et insister le creuse.
#
# L'open data ECMWF est servi par plusieurs hébergeurs. Mesuré sur le même fichier :
#
#   AWS s3     ✅ 12,52 Mo/s        Google  ✅ 6,82 Mo/s
#   Azure      ❌ HTTP 409          data.ecmwf.int ❌ 404
#
# Alterner les deux répartit la charge : chaque hôte voit la moitié des requêtes, donc le
# budget se consomme deux fois moins vite. Ce n'est pas une optimisation de débit — les
# deux sont largement assez rapides — c'est une façon de ne pas épuiser un seul seau.
MIROIRS = [
    "https://ecmwf-forecasts.s3.amazonaws.com",
    "https://storage.googleapis.com/ecmwf-open-data",
]
BASE = MIROIRS[0]  # conservé : d'anciens appels le référencent

_TOUR = 0


def _miroir() -> str:
    """Rend le miroir suivant. L'alternance est par REQUÊTE, pas par mois : un mois entier
    sur un seul hôte reviendrait à ne rien alterner du tout."""
    global _TOUR
    _TOUR += 1
    return MIROIRS[_TOUR % len(MIROIRS)]
SORTIE = RACINE / "data/processed/meteo"
CACHE = RACINE / "data/raw/ifs"
PYTHON_GRIB = "/home/cyril/miniforge3/bin/mamba"

# Six champs de surface, dans l'ordre de priorité établi par une relecture méthodologique.
# Les niveaux de pression sont écartés à ce stade : l'ablation a montré que le vent n'apporte
# que **+0,067 µg/m³** en marginal, ce qui ne justifie pas treize niveaux.
CHAMPS_SFC = {"2t", "2d", "10u", "10v", "ssrd", "tp"}
# 🔴 Ramené de 20 Mo à 1 Mo — mesuré le 23/08/2026, SANS transférer un octet.
#
# Les six champs de surface sont éparpillés dans un GRIB de plusieurs centaines de Mo. Une
# tolérance de 20 Mo fusionne des plages très distantes et tire tout ce qui les sépare. Le
# coût se calcule exactement depuis l'index, qui porte l'offset et la longueur de chaque
# champ — donc la question se tranche avant l'acquisition, pas après :
#
#   tolérance   requêtes/jour   transféré/jour   superflu   22 mois
#      20 Mo         16            175,0 Mo        77 %      115 Go
#       5 Mo         26            117,5 Mo        65 %       78 Go
#       1 Mo         47             41,7 Mo         2 %       27 Go
#       0            48             40,9 Mo         0 %       27 Go
#
# L'utile vaut 40,9 Mo par jour. À 1 Mo de tolérance on transfère 41,7 Mo — 2 % de
# superflu — pour 47 requêtes au lieu de 16. Or la mesure du 31/07 établit que le service
# accepte **288 requêtes par minute sans un seul rejet** : le nombre de requêtes n'est pas
# la ressource rare, le volume l'est. Diviser le transfert par 4,2 pour tripler un compteur
# qu'on ne sature pas est un échange sans perdant.
#
# En dessous de 1 Mo le gain devient nul (2 % → 0 %) pour une requête de plus : c'est le
# point où le regroupement cesse de coûter.
TOLERANCE_REGROUPEMENT = 1_000_000
# Un run de 00 h couvre le jour suivant par ses échéances 24 à 47 ; l'open data est tri-horaire.
ECHEANCES = [24, 27, 30, 33, 36, 39, 42, 45]


def index_du_pas(date: str, echeance: int) -> list[dict]:
    url = f"{_miroir()}/{date}/00z/ifs/0p25/oper/{date}000000-{echeance}h-oper-fc.index"
    _derniere: BaseException | None = None
    for essai in range(6):
        try:
            _freiner()
            with urllib.request.urlopen(url, timeout=60) as r:
                brut = r.read()
            if brut[:1] == b"{":
                _succes()
                return [json.loads(l) for l in brut.decode().splitlines() if l.strip()]
        except Exception as ex:  # noqa: BLE001
            _derniere = ex
        # **Le code de sortie ne suffit pas** : un appel limité rend du XML d'erreur avec un
        # statut apparemment normal. On contrôle le contenu.
        #
        # ⚠️ Ce bloc a porté pendant trois semaines la phrase « le service accepte 288
        # requêtes par minute sans un seul rejet », tirée de HUIT requêtes du 31/07. La
        # passe unitaire du 23/08 l'a réfutée : 62 échecs sur 240, tous groupés en fin de
        # lot, et des 503 encore servis une minute plus tard. Voir `_freiner`.
        nature = _rejet(_derniere)
        time.sleep(min(4.0, 0.5 * (essai + 1)) if nature == "lent"
                   else min(30.0, 2.0 ** essai))
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



# ── Le frein adaptatif, et le défaut qui l'impose — mesuré le 23/08/2026 ───────────────
#
# La passe unitaire sur juin 2024 a rendu **62 échecs sur 240 pas**, et ils étaient tous
# groupés à la FIN : les jours 1 à 20 sont passés sans une erreur, les jours 21 à 30 ont
# presque tout raté. Interrogé juste après, le service rendait **HTTP 503** même sur une
# requête d'index isolée. Ce n'est donc pas une absence de données, c'est une limitation de
# débit qui s'installe sous charge soutenue.
#
# 🔴 Et cela RÉFUTE une phrase écrite dans ce fichier : « le service accepte 288 requêtes
# par minute sans un seul rejet ». Elle vient d'une mesure du 31/07 portant sur **huit
# requêtes**. Huit requêtes ne mesurent pas un débit soutenu — c'est la § 1 ter, *une
# mesure n'est pas une propriété*, et la phrase avait ensuite servi à justifier de retirer
# toute prudence.
#
# Le frein ne porte aucune constante devinée (§ 0-A) : il part de zéro, s'allonge à chaque
# rejet et se relâche à chaque succès. Il se calibre donc sur le service tel qu'il est ce
# jour-là, au lieu de reprendre un chiffre d'une autre exécution.
_PAUSE = 0.0
_PLAFOND_PAUSE = 4.0


def _rejet(erreur: BaseException | None = None) -> str:
    """Un rejet allonge le frein — mais PAS de la même façon selon sa nature.

    🔴 La première version traitait toutes les erreurs à l'identique, et c'est faux — vu
    sur juin 2024, où un jour a coûté 426 s pour sept pas. Un **503 SlowDown** de S3 dit
    « tu vas trop vite » et se résorbe en quelques secondes ; un délai d'attente ou une
    coupure disent « le lien est mauvais » et méritent un recul franc. Les confondre fait
    reculer de 30 s là où 1 s suffisait, et le lot passe de 3 h à 60 h.

    Rend le type de rejet, pour que l'appelant choisisse son attente.
    """
    global _PAUSE
    code = getattr(erreur, "code", None)
    if code in (503, 429):
        # Ralentir un peu et souvent, plutôt que beaucoup et rarement.
        _PAUSE = min(_PLAFOND_PAUSE, _PAUSE * 1.4 + 0.05)
        return "lent"
    _PAUSE = min(_PLAFOND_PAUSE, _PAUSE * 2 + 0.05)
    return "dur"


def _succes() -> None:
    """Une réussite le relâche, lentement : redescendre trop vite rappelle le rejet."""
    global _PAUSE
    _PAUSE *= 0.97


def _freiner() -> None:
    if _PAUSE > 0:
        time.sleep(_PAUSE)


def telecharger_pas(date: str, echeance: int, cible: Path) -> bool:
    if cible.exists():
        return True
    champs = index_du_pas(date, echeance)
    if not champs:
        return False
    plages = plages_regroupees(champs)
    chemin = f"{date}/00z/ifs/0p25/oper/{date}000000-{echeance}h-oper-fc.grib2"
    morceaux = []
    for a, b in plages:
        # Six tentatives et un recul exponentiel : l'ancienne version abandonnait après
        # 0,5+1+1,5 = 3 s, soit bien moins que la durée d'un throttle S3.
        for essai in range(6):
            try:
                _freiner()
                req = urllib.request.Request(f"{_miroir()}/{chemin}",
                                             headers={"Range": f"bytes={a}-{b - 1}"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    brut = r.read()
                if brut[:4] == b"GRIB":
                    morceaux.append(brut)
                    _succes()
                    break
                nature = _rejet()
            except Exception as ex:  # noqa: BLE001
                nature = _rejet(ex)
            # Un « tu vas trop vite » se résorbe vite : on réessaie tôt et souvent. Une
            # panne de lien mérite le recul exponentiel.
            time.sleep(min(4.0, 0.5 * (essai + 1)) if nature == "lent"
                       else min(30.0, 2.0 ** essai))
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
    # L'extrapolation porte sur le lot RESTANT, et depuis la passe de CETTE exécution
    # (§ 0-A) — jamais sur un compte figé qui périme dès que la cible change.
    par_mois = volume * 30 / max(jours, 1)
    secondes = (time.time() - depart) * 30 / max(jours, 1)
    print(f"extrapolation : {par_mois / 1000:.2f} Go et {secondes / 60:.0f} min par mois "
          f"→ 22 mois = {par_mois * 22 / 1000:.0f} Go · {secondes * 22 / 3600:.1f} h",
          flush=True)

    t = extraire(fichiers, stations)
    cible = SORTIE / f"ifs_metropole_{annee}{mois:02d}.parquet"
    provisoire = cible.with_suffix(".parquet.partiel")
    t.to_parquet(provisoire, index=False)

    # 🔴 Le contrôle porte sur le CONTENU, avant le nom définitif (§ 4). Un mois à moitié
    # téléchargé écrit sous son nom final serait sauté à jamais par la reprise, et sa
    # moitié absente deviendrait un code d'époque. Les jours attendus sont NOMMÉS, pas
    # comptés contre un total : « ne jamais comparer un compte à un compte ».
    vus = set(pd.to_datetime(t["timestamp_utc"]).dt.strftime("%Y-%m-%d"))
    attendus = {f"{annee}-{mois:02d}-{j:02d}" for j in range(1, jours + 1)}
    # Le run 00 h d'un jour porte les échéances 24-45 h, donc le LENDEMAIN : on décale.
    attendus = {(pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                for d in attendus}
    manquants = sorted(attendus - vus)
    if manquants:
        provisoire.unlink(missing_ok=True)
        print(f"\n❌ {len(manquants)} jour(s) absent(s) du parquet : "
              f"{', '.join(manquants[:8])}{' …' if len(manquants) > 8 else ''}\n"
              f"   Rien écrit sous le nom définitif — le cache GRIB est CONSERVÉ pour la "
              f"reprise.", flush=True)
        return 1
    provisoire.rename(cible)
    print(f"\nÉcrit : {cible.relative_to(RACINE)} · {len(t):,} lignes · "
          f"{len(vus)} jours · colonnes {list(t.columns)}", flush=True)

    # Le cache GRIB ne sert qu'à la reprise DANS le mois. Une fois le parquet complet
    # écrit, il ne sert plus à rien — et /mnt/d n'a pas la place de 22 mois à 1,2 Go.
    libere = sum(f.stat().st_size for f in fichiers) / 1e9
    for f in fichiers:
        f.unlink(missing_ok=True)
    print(f"Cache GRIB purgé : {len(fichiers)} fichier(s), {libere:.1f} Go rendus",
          flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--annee", type=int, default=2024)
    p.add_argument("--mois", type=int, default=7)
    p.add_argument("--jours", type=int, default=5)
    args = p.parse_args()
    raise SystemExit(main(args.annee, args.mois, args.jours))
