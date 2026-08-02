#!/usr/bin/env python3
"""Extrait les six membres de l'ensemble CAMS aux stations, et en tire la dispersion.

Ce que le projet jetait
-----------------------
Nous ne téléchargions que `model=["ensemble"]`, c'est-à-dire la **médiane** de neuf à onze
modèles de chimie-transport. Leur **désaccord** — une estimation d'incertitude native,
disponible avant toute observation — partait à la poubelle. Le projet a passé des jours à lui
fabriquer des substituts : écart entre échéances, détecteur d'anomalies. La grandeur existait
en amont.

Ce que ce script produit
------------------------
Pour chaque station et chaque heure, les six valeurs des membres, puis leurs résumés :

| variable | ce qu'elle porte |
|---|---|
| `membres_median` | la valeur centrale, comparable à l'`ensemble` déjà utilisé |
| `membres_ecart` | l'écart-type entre modèles — la dispersion proprement dite |
| `membres_etendue` | max − min, plus robuste au petit effectif que l'écart-type |
| `membres_min`, `membres_max` | les bornes, utiles si le désaccord est asymétrique |
| `membres_asymetrie` | (max − médiane) − (médiane − min) : distingue un désaccord **orienté** d'un désaccord aléatoire |

**Six membres, pas onze** : le plafond ADS de 5 000 champs l'impose. La dispersion en est
sous-estimée, et il faut le dire plutôt que de laisser croire à l'ensemble complet.

Usage : python3 scripts/extraire_membres.py [--scope metropole]
Sortie : data/processed/meteo/membres_{scope}_AAAAMM.parquet
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.features import meteo  # noqa: E402
from aq.ingest import stations as st  # noqa: E402

SOURCE = RACINE / "data/raw/cams_membres"
SORTIE = RACINE / "data/processed/meteo"
TEMPORAIRE = RACINE / "data/raw/cams_membres/_extraction"


def selectionner_stations(scope: str) -> pd.DataFrame:
    ref = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    if scope == "occitanie":
        return ref[(ref["reseau"] == st.RESEAU_OCCITANIE) & ref["active"]]
    return ref[ref["metropole"] & ref["active"]]


def extraire_un_mois(archive: Path, stations: pd.DataFrame, mois: str) -> pd.DataFrame:
    """Décompresse les six membres, les échantillonne aux stations, et les recolle en large.

    Le nom du membre vient du **nom de fichier dans l'archive** (`CHIMERE_FORECAST.nc`), pas
    d'un attribut : c'est la seule information dont la présence est garantie pour les six.

    **La date de base doit être réinjectée dans le nom du fichier extrait.** À l'intérieur, la
    coordonnée `time` ne porte que des heures — 1 à 744 pour un mois de 31 jours, chaque
    journée contribuant ses échéances 1 à 24. L'attribut le confirme : *« FORECAST time from
    20240701 »*. Le module d'extraction lit cette date dans le **nom** au format `AAAA-MM-JJ` ;
    décompresser sous le nom d'origine la perd, et il refuse alors de deviner — refus légitime,
    car un horodatage inventé se propagerait en silence dans toute la chaîne.
    """
    TEMPORAIRE.mkdir(parents=True, exist_ok=True)
    base = f"{mois[:4]}-{mois[4:]}-01"
    colonnes = {}
    with zipfile.ZipFile(archive) as z:
        noms = z.namelist()
        for nom in noms:
            modele = nom.split("_")[0].lower()
            chemin = TEMPORAIRE / f"{Path(nom).stem}_{base}.nc"
            if not chemin.exists():
                with z.open(nom) as source, open(chemin, "wb") as sortie:
                    sortie.write(source.read())
            t = meteo.extraire_aux_stations(str(chemin), stations)
            # **Nommer la colonne, jamais la deviner.** Une première version prenait « la
            # première colonne qui n'est ni une clé ni une maille » : le tableau porte aussi la
            # coordonnée `level`, constante à 0, et c'est elle qui était extraite — six fois,
            # donnant une dispersion nulle parfaitement cohérente et parfaitement fausse.
            # Une heuristique positionnelle sur des colonnes qu'on ne contrôle pas ne signale
            # jamais qu'elle s'est trompée.
            conc = [c for c in t.columns if c.endswith("_conc")]
            if len(conc) != 1:
                raise ValueError(f"{nom} : {len(conc)} colonne(s) de concentration "
                                 f"trouvée(s) parmi {list(t.columns)}")
            colonnes[modele] = t.set_index(["station_id", "timestamp_utc"])[conc[0]]
            chemin.unlink(missing_ok=True)

    large = pd.DataFrame(colonnes)
    valeurs = large.to_numpy(dtype="float64")
    # `nan*` partout : un membre absent sur une maille ne doit pas annuler la dispersion des
    # cinq autres, mais il doit être compté.
    resume = pd.DataFrame({
        "membres_median": np.nanmedian(valeurs, axis=1),
        "membres_ecart": np.nanstd(valeurs, axis=1, ddof=1),
        "membres_min": np.nanmin(valeurs, axis=1),
        "membres_max": np.nanmax(valeurs, axis=1),
        "membres_n": np.isfinite(valeurs).sum(axis=1),
    }, index=large.index)
    resume["membres_etendue"] = resume["membres_max"] - resume["membres_min"]
    # Asymétrie du désaccord : positive si un ou plusieurs membres tirent vers le haut. Un
    # désaccord orienté n'a pas le même sens qu'un désaccord symétrique — le premier suggère
    # un modèle divergent, le second une situation intrinsèquement incertaine.
    resume["membres_asymetrie"] = ((resume["membres_max"] - resume["membres_median"])
                                   - (resume["membres_median"] - resume["membres_min"]))
    return pd.concat([large, resume], axis=1).reset_index()


def main(scope: str) -> int:
    archives = sorted(SOURCE.glob("membres_*.nc"))
    if not archives:
        raise SystemExit(f"aucune archive dans {SOURCE}")
    stations = selectionner_stations(scope)
    SORTIE.mkdir(parents=True, exist_ok=True)

    # ⚠️ **Capture TOUS les jetons du nom — espèce ET chaque mois.**
    #
    # Une expression qui ne capture qu'un seul groupe de six chiffres, ancrée sur la fin du
    # nom, a **déjà fait cette faute dans ce projet** : sur un dossier groupé elle prenait le
    # second mois pour l'espèce, et les trois polluants s'écrasaient sous une même clé. La
    # même ligne recopiée dans `fit_mos.py` a ensuite coûté **35 % du jeu d'entraînement**.
    motif = re.compile(r"^membres_([a-z]+[a-z0-9]*)_(\d{6}(?:_\d{6})*)\.nc$")
    restants, mois_par_archive = [], {}
    for a in archives:
        trouve = motif.match(a.name)
        if not trouve:
            raise SystemExit(
                f"nom d'archive non conforme : {a.name}\n"
                f"Attendu `membres_ESPECE_AAAAMM.nc`. L'espèce doit commencer par une "
                f"lettre —\nsans quoi un mois pourrait être lu comme une espèce, ce qui "
                f"s'est déjà produit ici.")
        espece, jetons = trouve.group(1), trouve.group(2).split("_")
        if len(jetons) > 1:
            raise SystemExit(
                f"{a.name} porte {len(jetons)} mois : {', '.join(jetons)}.\n"
                f"Ce script ne sait traiter qu'un mois par archive. Il le DIT plutôt que "
                f"d'en garder un seul.")
        mois = jetons[0]
        cible = SORTIE / f"membres_{scope}_{espece}_{mois}.parquet"
        mois_par_archive[a] = mois
        if not cible.exists():
            restants.append((a, cible))

    print(f"{len(archives)} archives · {len(stations)} stations · "
          f"{len(restants)} à extraire", flush=True)
    debut = time.time()
    for n, (archive, cible) in enumerate(restants, start=1):
        try:
            t = extraire_un_mois(archive, stations, mois_par_archive[archive])
        except Exception as exc:  # noqa: BLE001
            print(f"  [{n}/{len(restants)}] {archive.name} ÉCHEC "
                  f"{type(exc).__name__}: {str(exc)[:150]}", flush=True)
            continue
        provisoire = cible.with_suffix(".parquet.partiel")
        t.to_parquet(provisoire, index=False)
        provisoire.rename(cible)
        print(f"  [{n}/{len(restants)}] {cible.name} · {len(t):,} lignes · "
              f"écart médian {t['membres_ecart'].median():.2f} µg/m³ · "
              f"{time.time() - debut:.0f}s", flush=True)

    produits = sorted(SORTIE.glob(f"membres_{scope}_*.parquet"))
    print(f"\n{len(produits)} mois extraits · {time.time() - debut:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scope", default="metropole", choices=["metropole", "occitanie"])
    args = p.parse_args()
    raise SystemExit(main(args.scope))
