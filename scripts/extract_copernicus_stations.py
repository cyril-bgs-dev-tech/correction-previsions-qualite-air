"""Échantillonne les champs Copernicus téléchargés aux coordonnées des stations.

Usage : python scripts/extract_copernicus_stations.py --service era5 [--scope metropole]
Sortie : data/processed/meteo/{service}_{scope}_AAAAMM.parquet

Le découpage mensuel de la sortie n'est pas un détail : il permet de lancer
l'extraction **pendant** que le téléchargement continue, et de la relancer sans
rien recalculer. Un mois absent est un mois à faire, rien d'autre à retenir.

Pour ERA5, les deux flux d'un même mois — champs instantanés et champs cumulés —
sont rassemblés en une seule table. Ils ont été téléchargés séparément parce que le
service l'impose, pas parce qu'ils décrivent des choses différentes au même instant.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.features import meteo  # noqa: E402
from aq.ingest import stations as st  # noqa: E402

SORTIE = RACINE / "data/processed/meteo"


def selectionner_stations(scope: str) -> pd.DataFrame:
    referentiel = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    if scope == "occitanie":
        return referentiel[
            (referentiel["reseau"] == st.RESEAU_OCCITANIE) & referentiel["active"]
        ]
    return referentiel[referentiel["metropole"] & referentiel["active"]]


def mois_era5(dossier: Path) -> dict[str, list[Path]]:
    """Regroupe les fichiers ERA5 par mois — un flux instantané, un flux cumulé.

    La clé capture **tous** les codes AAAAMM du nom, comme pour CAMS. Les fichiers ERA5
    sont mono-mois aujourd'hui, mais le téléchargement regroupe quatre mois par requête :
    rien ne garantit que cela dure, et une expression qui n'en capturerait que le dernier
    fondrait des mois distincts sous une même clé sans lever d'erreur.
    """
    # Deux conventions coexistent à l'écriture : `_202501.nc`, `_202501_202502.nc`, et la
    # forme **abrégée** `_202501_04.nc` — où le second segment ne porte que le mois. Un motif
    # n'acceptant que des codes à six chiffres ignorait cette dernière **sans lever d'erreur**,
    # et quatre fichiers de 2025 étaient invisibles à l'extraction : 68 mois sur disque, zéro à
    # extraire. Le défaut ne casse rien et fait disparaître des données — le pire des deux.
    motif = re.compile(r"_(\d{6}(?:_(?:\d{6}|\d{2}))*)\.nc$")
    par_mois: dict[str, list[Path]] = {}
    ignores = []
    for fichier in sorted(dossier.glob("era5_*.nc")):
        trouve = motif.search(fichier.name)
        if trouve:
            par_mois.setdefault(trouve.group(1), []).append(fichier)
        else:
            ignores.append(fichier.name)
    if ignores:
        # Un fichier qu'on ne sait pas nommer doit être **dit**, jamais sauté en silence.
        print(f"⚠️ {len(ignores)} fichier(s) ERA5 au nom non reconnu, ignoré(s) : "
              f"{', '.join(ignores[:4])}", flush=True)
    return par_mois


# Espèces nommées explicitement : une expression générique `([a-z0-9]+)` capturait
# « 202402 » plutôt que « o3 » sur un dossier groupé `..._o3_202402_202403`, et les trois
# polluants s'écrasaient mutuellement dans un même fichier de sortie. Le nom de l'espèce
# est une liste fermée : autant l'écrire.
# `pm10` ajouté le 01/08/2026. L'alternation du motif reste sans ambiguïté — `pm25` et
# `pm10` ne se préfixent pas — et la liste doit rester **fermée** : c'est elle qui
# empêche un dossier au nom inattendu de se faire passer pour une espèce connue.
ESPECES_CAMS = ("no2", "o3", "pm25", "pm10")


def mois_cams(dossier: Path) -> dict[str, list[Path]]:
    """Regroupe les membres journaliers CAMS par (espèce, mois ou groupe de mois)."""
    motif = re.compile(
        r"_(" + "|".join(ESPECES_CAMS) + r")_(\d{6}(?:_\d{6})*)$"
    )
    par_mois: dict[str, list[Path]] = {}
    for repertoire in sorted(p for p in dossier.iterdir() if p.is_dir()):
        trouve = motif.search(repertoire.name)
        if trouve:
            cle = f"{trouve.group(1)}_{trouve.group(2)}"
            par_mois[cle] = sorted(repertoire.glob("*.nc"))
    return par_mois


def jours_attendus(service: str, cle: str) -> int:
    """Nombre de fichiers que doit compter un mois complet.

    ERA5 en donne deux — un flux instantané, un flux cumulé. CAMS en donne un par jour
    de prévision, donc autant que le mois a de jours : c'est le calendrier qui fixe la
    valeur, pas une constante, sinon février serait éternellement jugé incomplet.
    """
    # Un groupe porte plusieurs codes AAAAMM : le compte attendu est leur **somme**,
    # sans quoi un groupe de deux mois serait jugé complet à moitié.
    mois = re.findall(r"(\d{4})(\d{2})", cle)
    if service == "era5":
        return 2 * max(len(mois), 1)
    if not mois:
        return 1

    # **Le mois en cours ne peut pas être complet.** Exiger ses 31 jours le 30 le
    # déclarerait éternellement partiel, et l'extraction le reporterait indéfiniment —
    # la garde contre les mois troués se retournerait contre le seul mois qu'on veut
    # rejouer. On n'attend donc que les jours **écoulés**, en gardant la veille comme
    # borne : la prévision du jour même peut n'être pas encore publiée.
    aujourdhui = pd.Timestamp.now(tz="UTC").normalize()
    total = 0
    for annee, m in mois:
        periode = pd.Period(f"{annee}-{m}")
        if periode == pd.Period(aujourdhui, freq="M"):
            total += max(1, aujourdhui.day - 1)
        else:
            total += periode.days_in_month
    return total


def assembler(fichiers: list[Path], stations: pd.DataFrame) -> pd.DataFrame:
    """Extrait puis recolle les fichiers d'un même mois.

    ERA5 : deux flux à fusionner sur (station, instant) — ce sont les mêmes instants
    décrits par des variables différentes, donc une jointure.
    CAMS : des journées de prévision à empiler — ce sont des instants différents,
    donc une concaténation. Confondre les deux produirait soit des colonnes perdues,
    soit des lignes dupliquées.
    """
    tables = [meteo.extraire_aux_stations(str(f), stations) for f in fichiers]
    if len(tables) == 1:
        return tables[0]

    memes_instants = all(
        set(t.columns) - {"maille_lat", "maille_lon"}
        == set(tables[0].columns) - {"maille_lat", "maille_lon"}
        for t in tables
    )
    if memes_instants:
        return pd.concat(tables, ignore_index=True)

    fusion = tables[0]
    for suivante in tables[1:]:
        suivante = suivante.drop(columns=["maille_lat", "maille_lon"], errors="ignore")
        fusion = fusion.merge(suivante, on=["station_id", "timestamp_utc"], how="outer")
    return fusion


def main(service: str, scope: str) -> int:
    dossier = RACINE / "data/raw" / service
    if not dossier.is_dir():
        raise SystemExit(f"{dossier} absent — lancer d'abord download_copernicus.py")

    stations = selectionner_stations(scope)
    SORTIE.mkdir(parents=True, exist_ok=True)

    groupes = mois_era5(dossier) if service == "era5" else mois_cams(dossier)

    # **Ne jamais extraire un mois incomplet.** Un mois ERA5 dont seul le flux
    # instantané est arrivé produirait une table sans précipitation ni rayonnement ;
    # un mois CAMS à 9 jours sur 31 produirait une table qui n'a l'air de rien de
    # spécial. Dans les deux cas elle serait écrite sous un nom définitif, donc sautée
    # à jamais par la reprise, et le trou ne se verrait que dans les métriques — sans
    # jamais s'y annoncer.
    partiels = {cle for cle, fichiers in groupes.items()
                if len(fichiers) < jours_attendus(service, cle)}
    if partiels:
        print(f"{len(partiels)} mois encore incomplet(s), reportés : "
              f"{', '.join(sorted(partiels)[:6])}", flush=True)

    restants = {
        cle: fichiers for cle, fichiers in groupes.items()
        if cle not in partiels
        and not (SORTIE / f"{service}_{scope}_{cle}.parquet").exists()
    }
    print(f"{service} · {len(stations)} stations · {len(groupes)} mois sur disque · "
          f"{len(restants)} à extraire", flush=True)

    debut = time.time()
    lignes_totales = 0
    for n, (cle, fichiers) in enumerate(sorted(restants.items()), start=1):
        cible = SORTIE / f"{service}_{scope}_{cle}.parquet"
        try:
            tableau = assembler(fichiers, stations)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{n}/{len(restants)}] {cle} ECHEC "
                  f"{type(exc).__name__}: {str(exc)[:200]}", flush=True)
            continue
        # Écriture par un nom provisoire : un parquet au nom définitif est réputé
        # complet et sera sauté à la reprise.
        provisoire = cible.with_suffix(".parquet.partiel")
        tableau.to_parquet(provisoire, index=False)
        provisoire.rename(cible)
        lignes_totales += len(tableau)
        print(f"  [{n}/{len(restants)}] {time.time() - debut:5.0f}s  {cle}  "
              f"{len(tableau):,} lignes · {len(fichiers)} fichier(s)", flush=True)

    produits = sorted(SORTIE.glob(f"{service}_{scope}_*.parquet"))
    print(f"\n{len(produits)} mois extraits · {lignes_totales:,} lignes écrites "
          f"cette fois · {SORTIE}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--service", default="era5",
                         choices=["era5", "cams_prevision"])
    parseur.add_argument("--scope", default="metropole",
                         choices=["metropole", "occitanie"])
    args = parseur.parse_args()
    raise SystemExit(main(args.service, args.scope))
