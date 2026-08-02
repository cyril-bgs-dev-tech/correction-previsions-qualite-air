#!/usr/bin/env python3
"""TROPOMI aux 476 stations — la colonne de NO₂ et l'indice d'aérosols, par lecture partielle.

Pourquoi cette source
---------------------
Le levier le plus fort du projet est **l'observation de la veille : +8,9 %**, davantage que
toute la météo. Sa limite est écrite dans le dossier : elle n'existe **qu'aux stations
instrumentées**. C'est précisément l'écart entre le chiffre « aux stations » et la
revendication « partout ».

TROPOMI observe **partout**, tous les jours, à 0,035° ≈ 3,9 km — deux fois plus fin que la
maille CAMS. Deux produits de nature différente en sortent :

* **la colonne du jour** — l'observation de la veille, étendue au territoire. Couverture
  mesurée à **86 % en moyenne annuelle**, mais **34 % au pire jour d'hiver** ;
* **la colonne moyennée sur un mois** — complète, elle, puisque moyenner trente passages à
  86 % ne laisse pas de trou. C'est une carte de l'environnement d'émission local, disponible
  en tout point, et surtout **transportable** : contrairement à `lat/lon`, elle décrit un
  lieu sans le nommer. C'est le substitut recherché depuis que la validation bloquée s'est
  effondrée à −9 % sur PM2,5.

L'indice d'aérosols UV est extrait dans la même passe : c'est le traceur classique des
intrusions sahariennes, qui dominent les pics de PM10 en Occitanie — le polluant qui porte
40 des 52 vigilances réellement déclarées.

Accès — vérifié avant d'écrire une ligne de lot
-----------------------------------------------
Seau ``s3://meeo-s5p`` (MEEO / AWS Open Data), **sans authentification**. Le préfixe
``COGT/`` porte les produits reprojetés en EPSG:4326 au format Cloud Optimized GeoTIFF :
grille mondiale 10 285 × 4 837, tuilée 512×512, cinq niveaux d'aperçus, ``Accept-Ranges:
bytes`` et **HTTP 206** confirmé. On ne lit donc que la fenêtre France — **zéro octet
stocké**, comme pour le MNT GLO-30.

Sur les 14 orbites quotidiennes, **une seule couvre la France** : celle qui démarre vers
11 h 46 UTC, pour un passage au-dessus des stations vers 12 h 30 UTC. Pour une prévision
émise à 3 h du matin, la donnée de la veille est acquise depuis quinze heures — la source
est **opérationnellement propre**.

⚠️ Les deux pièges du ``qa_value``, tous deux silencieux
--------------------------------------------------------
1. **Il est stocké en entier 0-100, pas en fraction 0-1.** Recopier le seuil de l'ESA tel
   qu'il est publié — « qa > 0.75 » — laisse passer **tout**, minimum à 33 compris. La
   couverture annoncée valait alors 99 % en plein janvier : plausible, et faux.
2. **La valeur est quantifiée, et le ciel clair tombe sur 74, pas 75.** Un ``>= 75``
   appliqué à la lettre jetterait 235 pixels valides sur 476 un 8 janvier. Le seuil qui
   sépare réellement les régimes est **50** — il rejette le 33 « couvert par un nuage » au
   sens de l'ESA et retient le reste. Seuil lu dans les données, pas recopié d'une note.

Usage :
  python3 scripts/extraire_tropomi.py --passe-unitaire --debut 2024-01-15
  python3 scripts/extraire_tropomi.py --debut 2024-01-01 --fin 2026-07-31
Sortie : data/processed/tropomi/tropomi_metropole_{AAAAMM}.parquet
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")

SEAU = "https://meeo-s5p.s3.amazonaws.com"
SORTIE = RACINE / "data/processed/tropomi"
FRANCE = (-5.5, 41.0, 10.0, 51.5)
QA_MIN, QA_ABSENT = 50, 255
NODATA = -9999.0

# Les deux produits, avec la couche utile de chacun. La clé du dictionnaire devient le
# préfixe des colonnes écrites.
PRODUITS = {
    "no2": ("COGT/OFFL/L2__NO2___",
            "_PRODUCT_nitrogendioxide_tropospheric_column_4326.tif"),
    "aai": ("COGT/OFFL/L2__AER_AI",
            "_PRODUCT_aerosol_index_340_380_4326.tif"),
}
QA_SUFFIXE = "_PRODUCT_qa_value_4326.tif"

# Rayons des couronnes, en kilomètres. Le plus petit vaut deux fois et demie la maille de
# 3,9 km — en dessous, la couronne ne contiendrait que le pixel central et ses voisins
# immédiats, donc rien de plus que le point.
RAYONS_KM = (10.0, 25.0, 50.0, 100.0)

# L'orbite qui couvre la France démarre vers 11 h 46 UTC ; ses deux voisines la frôlent.
# Sonder cette plage au lieu des 14 orbites divise le temps par ~4. La borne est large
# exprès : elle est là pour écarter les orbites de nuit, pas pour choisir à la place de la
# mesure de couverture qui suit.
HEURES_CANDIDATES = range(10, 15)

# ⚠️ Le nom porte **plusieurs** jetons datés — début, fin, et un horodatage de traitement.
# Une expression ancrée à droite en capturerait le mauvais (règle 4 bis). On les capture
# tous, nommément, et on n'utilise que ceux qu'on a nommés.
MOTIF = re.compile(
    r"S5P_(?P<mode>\w{4})_L2_+(?P<produit>[A-Z0-9_]+?)_+"
    r"(?P<debut>\d{8}T\d{6})_(?P<fin>\d{8}T\d{6})_(?P<orbite>\d{5})_"
    r"(?P<collection>\d{2})_(?P<version>\d{6})_(?P<traitement>\d{8}T\d{6})")


def avec_reprise(action, quoi: str, tentatives: int = 4, attente: float = 3.0):
    """Réessaie une action réseau, puis **lève** — jamais de valeur de repli silencieuse.

    Une coupure passagère — ``Connection reset by peer`` — a coûté un jour au premier lot :
    l'exception remontait au niveau de la journée, qui la comptait comme « sans orbite ».
    Un incident de transport devenait un trou de données, indiscernable d'une absence réelle.
    """
    derniere = None
    for essai in range(1, tentatives + 1):
        try:
            return action()
        except Exception as e:  # noqa: BLE001 — on relaie la cause après épuisement
            derniere = e
            if essai < tentatives:
                time.sleep(attente * essai)
    raise RuntimeError(f"{quoi} : {tentatives} tentatives échouées · "
                       f"{type(derniere).__name__}: {derniere}") from derniere


def lister(prefixe: str) -> list[str]:
    """Clés d'un préfixe S3, sans authentification."""
    url = f"{SEAU}/?list-type=2&prefix={prefixe}&max-keys=1000"

    def _lire():
        with urllib.request.urlopen(url, timeout=90) as r:
            return r.read()

    arbre = ET.fromstring(avec_reprise(_lire, f"listage {prefixe}"))
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    return [e.text for e in arbre.findall(".//s3:Contents/s3:Key", ns)]


def candidats(jour: date, produit: str, suffixe: str) -> dict[int, str]:
    """Granules du jour dont l'orbite peut voir la France, indexés par numéro d'orbite."""
    prefixe = f"{produit}/{jour:%Y/%m/%d}/"
    cles = [k for k in lister(prefixe) if k.endswith(suffixe)]
    retenus = {}
    for k in cles:
        m = MOTIF.search(k.rsplit("/", 1)[-1])
        if not m:
            continue
        heure = int(m.group("debut")[9:11])
        if heure in HEURES_CANDIDATES:
            retenus[int(m.group("orbite"))] = k
    return retenus


def fenetre(src):
    from rasterio.windows import from_bounds

    o, s, e, n = FRANCE
    return from_bounds(o, s, e, n, transform=src.transform).round_offsets().round_lengths()


def lire(cle: str) -> tuple[np.ndarray, object]:
    """Charge la fenêtre France **en entier** puis on indexe en mémoire (règle 2)."""
    import rasterio

    def _lire():
        with rasterio.open(f"/vsicurl/{SEAU}/{cle}") as src:
            f = fenetre(src)
            return src.read(1, window=f), src.window_transform(f)

    return avec_reprise(_lire, f"lecture {cle.rsplit('/', 1)[-1][:50]}")


def indices(transform, stations: pd.DataFrame, forme) -> tuple[np.ndarray, np.ndarray]:
    from rasterio.transform import rowcol

    li, co = rowcol(transform, stations["lon_wgs84"].to_numpy(),
                    stations["lat_wgs84"].to_numpy())
    li, co = np.asarray(li), np.asarray(co)
    return np.clip(li, 0, forme[0] - 1), np.clip(co, 0, forme[1] - 1)


def preparer_couronnes(transform, forme, stations: pd.DataFrame) -> dict:
    """Indices des pixels autour de chaque station, à plusieurs rayons — calculés **une fois**.

    Pourquoi des couronnes plutôt que le seul pixel de la station
    -------------------------------------------------------------
    Réduire une image à un point jette ce que l'image a de particulier : le panache en amont,
    le gradient ville-campagne, l'étendue de l'épisode. Le projet a déjà cet idiome — les
    prédicteurs de forêt sont des couronnes concentriques de 100 m à 30 km. On l'applique
    au champ satellitaire, à des rayons adaptés à sa maille de 3,9 km.

    C'est aussi l'étape qui **rend falsifiable** l'idée d'un réseau convolutif : si les
    couronnes n'ajoutent rien au pixel central, la structure spatiale ne porte pas
    d'information et une architecture profonde n'en trouvera pas davantage.

    Coût réseau : **nul.** La fenêtre France est déjà chargée entière en mémoire pour lire le
    pixel de la station — les couronnes ne sont que de l'indexation sur ces mêmes octets.

    La distance est équirectangulaire, centrée sur la latitude moyenne des stations : sur
    l'emprise française et pour des rayons de 100 km, l'écart au géodésique reste sous 1 %,
    bien en deçà de la maille de 3,9 km.
    """
    from scipy.spatial import cKDTree

    ny, nx = forme
    lon = transform.c + (np.arange(nx) + 0.5) * transform.a
    lat = transform.f + (np.arange(ny) + 0.5) * transform.e
    grille_lon, grille_lat = np.meshgrid(lon, lat)

    lat0 = np.deg2rad(float(stations["lat_wgs84"].mean()))
    r_terre = 6371.0

    def en_km(lo, la):
        return (np.deg2rad(lo) * r_terre * np.cos(lat0), np.deg2rad(la) * r_terre)

    px, py = en_km(grille_lon.ravel(), grille_lat.ravel())
    sx, sy = en_km(stations["lon_wgs84"].to_numpy(), stations["lat_wgs84"].to_numpy())
    arbre = cKDTree(np.column_stack([px, py]))

    plan = {}
    for rayon in RAYONS_KM:
        paquets = arbre.query_ball_point(np.column_stack([sx, sy]), r=rayon)
        idx = np.concatenate([np.asarray(p, dtype="int64") for p in paquets])
        lab = np.repeat(np.arange(len(paquets)), [len(p) for p in paquets])
        plan[rayon] = (idx, lab)
        print(f"   couronne {rayon:3.0f} km · {len(idx) / len(paquets):.0f} pixels par "
              f"station en moyenne", flush=True)
    return plan


def moyennes_couronnes(masque: np.ndarray, plan: dict, n_stations: int) -> dict:
    """Moyenne des pixels valides par station et par rayon, sur un bloc **déjà masqué**."""
    plat = masque.ravel()
    sortie = {}
    for rayon, (idx, lab) in plan.items():
        v = plat[idx]
        ok = np.isfinite(v)
        somme = np.bincount(lab[ok], weights=v[ok], minlength=n_stations)
        compte = np.bincount(lab[ok], minlength=n_stations).astype("float64")
        moyenne = np.divide(somme, compte, out=np.full(n_stations, np.nan),
                            where=compte > 0)
        sortie[rayon] = (moyenne, compte)
    return sortie


_PLAN: dict = {}


def plan_couronnes(transform, forme, stations: pd.DataFrame) -> dict:
    """Le plan d'indexation, calculé une seule fois par géométrie rencontrée."""
    cle = (forme, tuple(np.round(np.asarray(transform)[:6], 9)))
    if cle not in _PLAN:
        print(f"  géométrie {forme} — calcul du plan de couronnes", flush=True)
        _PLAN[cle] = preparer_couronnes(transform, forme, stations)
    return _PLAN[cle]


def extraire_jour(jour: date, stations: pd.DataFrame) -> pd.DataFrame | None:
    """Une ligne par station pour ce jour, ou None si aucune orbite ne couvre la France."""
    lignes = pd.DataFrame({"station_id": stations["station_id"].to_numpy(),
                           "jour": pd.Timestamp(jour)})
    n = len(stations)
    trouve = False

    for nom, (prefixe, suffixe) in PRODUITS.items():
        cles = candidats(jour, prefixe, suffixe)
        meilleur, meilleure_couv = None, -1
        for orbite, cle in sorted(cles.items()):
            bloc, transform = lire(cle)
            couv = int((bloc != NODATA).sum())
            if couv > meilleure_couv:
                meilleur, meilleure_couv = (orbite, bloc, transform, cle), couv
        if meilleur is None or meilleure_couv <= 0:
            lignes[f"{nom}_col"] = np.nan
            for r in RAYONS_KM:
                lignes[f"{nom}_r{r:.0f}"] = np.nan
                lignes[f"{nom}_n{r:.0f}"] = 0.0
            continue

        orbite, bloc, transform, cle = meilleur

        # ── Masquer le bloc ENTIER, pas seulement les pixels de station ──────────────
        # Les couronnes moyennent des voisins : un pixel nuageux qui entre dans la moyenne
        # la fausse aussi sûrement qu'au point central.
        qa_bloc, _ = lire(cle.replace(suffixe, QA_SUFFIXE))
        if qa_bloc.shape != bloc.shape:
            raise SystemExit(f"{jour} · {nom} : qa {qa_bloc.shape} ≠ couche {bloc.shape} — "
                             f"ne PAS masquer avec un tableau d'une autre forme")
        masque = bloc.astype("float64")
        masque[bloc == NODATA] = np.nan
        masque[(qa_bloc < QA_MIN) | (qa_bloc == QA_ABSENT)] = np.nan

        li, co = indices(transform, stations, bloc.shape)
        lignes[f"{nom}_col"] = masque[li, co]
        lignes[f"{nom}_qa"] = qa_bloc[li, co].astype("float64")
        lignes[f"{nom}_orbite"] = orbite

        for rayon, (moyenne, compte) in moyennes_couronnes(
                masque, plan_couronnes(transform, bloc.shape, stations), n).items():
            lignes[f"{nom}_r{rayon:.0f}"] = moyenne
            # Le nombre de pixels valides dans la couronne est une variable, pas un détail :
            # une moyenne sur 3 pixels et une moyenne sur 2 000 ne se valent pas.
            lignes[f"{nom}_n{rayon:.0f}"] = compte
        trouve = True

    return lignes if trouve else None


def controler_mois(t: pd.DataFrame, cle: str, jours_demandes: int, echecs: int) -> None:
    """Le contrôle porte sur la **demande**, pas sur la vraisemblance (règle 2 bis).

    ⚠️ La première version de cette fonction comparait le nombre de jours extraits au nombre
    de jours extraits — `jours < n_jours * 0.8` où `n_jours` était lui-même compté sur les
    morceaux reçus. **Elle passait donc toujours au vert**, et aurait laissé écrire sous son
    nom définitif un mois amputé de la moitié de ses jours. C'est le défaut que la règle 2 bis
    nomme « le contrôle mal posé coûte autant que l'absence de contrôle » : la valeur attendue
    se calcule **depuis la demande** — ici le calendrier — jamais depuis ce qu'on a reçu.

    Un jour sans orbite couvrante est **légitime** et ne bloque rien. Un jour perdu sur un
    incident réseau ne l'est pas : c'est un trou technique, et il doit empêcher le renommage.
    """
    jours = t["jour"].nunique()
    if echecs:
        raise SystemExit(f"{cle} : {echecs} jour(s) perdus sur incident technique — "
                         f"mois NON écrit sous son nom définitif, relancer ce mois")
    if jours < jours_demandes:
        manquants = jours_demandes - jours
        if manquants > jours_demandes * 0.1:
            raise SystemExit(f"{cle} : {jours} jours sur {jours_demandes} demandés, "
                             f"{manquants} sans orbite couvrante — au-delà des 10 % tolérés")
        print(f"   {cle} · {manquants} jour(s) sans orbite couvrante, toléré", flush=True)
    for colonne in ("no2_col", "aai_col"):
        if colonne not in t.columns:
            raise SystemExit(f"{cle} : colonne {colonne} absente")
        v = t[colonne].dropna()
        if v.empty:
            raise SystemExit(f"{cle} : {colonne} entièrement vide")
        if v.nunique() < 100:
            raise SystemExit(f"{cle} : {colonne} ne prend que {v.nunique()} valeurs "
                             f"distinctes — on ne lit pas ce qu'on croit")


def main(debut: str, fin: str, passe_unitaire: bool) -> int:
    depart = time.time()
    SORTIE.mkdir(parents=True, exist_ok=True)

    stations = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                               columns=["station_id", "lat_wgs84", "lon_wgs84",
                                        "metropole", "active"])
    stations = (stations[stations["metropole"] & stations["active"]]
                .dropna(subset=["lat_wgs84", "lon_wgs84"])
                .reset_index(drop=True))

    if passe_unitaire:
        # Règle 1 : l'unité mesurée doit être **l'unité du lot** — ici une journée, les deux
        # produits compris, pas une lecture de raster isolée.
        d = date.fromisoformat(debut)
        t0 = time.time()
        t = extraire_jour(d, stations)
        duree = time.time() - t0
        if t is None:
            raise SystemExit(f"{d} : aucune orbite couvrante — journée inexploitable")
        print(f"{d} · {len(t)} stations · {duree:.1f} s\n")
        print("AXE RÉSULTAT")
        for c in ("no2_col", "aai_col"):
            v = t[c].dropna()
            print(f"  {c:8s} · {len(v):3d}/{len(t)} valides ({len(v) / len(t):.0%}) · "
                  f"{v.nunique()} valeurs distinctes · "
                  f"médiane {v.median():.3e}" if len(v) else f"  {c} · VIDE")
        n = (date.fromisoformat(fin) - d).days + 1
        print(f"\nAXE COÛT")
        print(f"  {n} jours × {duree:.1f} s = **{n * duree / 60:.0f} min**")
        print(f"  volume : {n * len(t) / 1e6:.2f} M lignes")
        print("\nRelancer sans --passe-unitaire si ces deux axes conviennent.")
        return 0

    d, dfin = date.fromisoformat(debut), date.fromisoformat(fin)
    n_total = (dfin - d).days + 1
    faits, sans_orbite, echecs = 0, [], []
    par_mois: dict[str, list] = {}
    # Compté **depuis la demande**, jamais depuis ce qui revient.
    demandes: dict[str, int] = {}
    echecs_mois: dict[str, int] = {}
    mois_refuses = []

    while d <= dfin:
        cle = d.strftime("%Y%m")
        cible = SORTIE / f"tropomi_metropole_{cle}.parquet"
        if cible.exists() and d.day == 1:
            saut = (pd.Timestamp(d) + pd.offsets.MonthBegin(1)).date()
            print(f"── {cle} déjà écrit, sauté", flush=True)
            d = saut
            continue
        demandes[cle] = demandes.get(cle, 0) + 1
        try:
            t = extraire_jour(d, stations)
            if t is None:
                sans_orbite.append(d.isoformat())
            else:
                par_mois.setdefault(cle, []).append(t)
        except Exception as e:  # noqa: BLE001 — jamais avaler : on veut le jour ET la cause
            print(f"  ⚠️ {d} · {type(e).__name__}: {e}", flush=True)
            echecs.append(d.isoformat())
            echecs_mois[cle] = echecs_mois.get(cle, 0) + 1

        faits += 1
        lendemain = d + timedelta(days=1)
        if lendemain.month != d.month or lendemain > dfin:
            morceaux = par_mois.pop(cle, [])
            if morceaux:
                m = pd.concat(morceaux, ignore_index=True)
                try:
                    controler_mois(m, cle, demandes[cle], echecs_mois.get(cle, 0))
                except SystemExit as refus:
                    print(f"  ⚠️ {refus}", flush=True)
                    mois_refuses.append(cle)
                    d = lendemain
                    continue
                # Règle 4 : nom provisoire, contrôle, puis renommage.
                prov = cible.with_suffix(".parquet.partiel")
                m.to_parquet(prov, index=False)
                prov.replace(cible)
                valides = m["no2_col"].notna().mean()
                aai_val = m["aai_col"].notna().mean()
                ecoule = time.time() - depart
                reste = ecoule / max(faits, 1) * (n_total - faits)
                print(f"── {cle} · {len(m):,} lignes · {m['jour'].nunique()}/"
                      f"{demandes[cle]} jours · NO₂ valide {valides:.0%} · "
                      f"AAI {aai_val:.0%} · {ecoule / 60:.0f} min écoulées · "
                      f"fin estimée dans {reste / 60:.0f} min", flush=True)
        d = lendemain

    print(f"\n{faits} jours traités · {len(sans_orbite)} sans orbite couvrante "
          f"· {len(echecs)} échecs techniques · {len(mois_refuses)} mois refusés "
          f"· {(time.time() - depart) / 60:.0f} min")
    for j in echecs[:15]:
        print(f"  échec · {j}")
    for c in mois_refuses:
        print(f"  mois refusé · {c} — relancer : --debut {c[:4]}-{c[4:]}-01")
    ecrits = sorted(SORTIE.glob("tropomi_metropole_*.parquet"))
    print(f"Écrit : {len(ecrits)} fichiers dans {SORTIE.relative_to(RACINE)}")
    if not ecrits:
        print("AUCUN fichier écrit")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--debut", default="2024-01-01")
    p.add_argument("--fin", default="2026-07-31")
    p.add_argument("--passe-unitaire", action="store_true")
    a = p.parse_args()
    raise SystemExit(main(a.debut, a.fin, a.passe_unitaire))
