#!/usr/bin/env python3
"""GEOS-CF aux stations — un modèle de chimie **indépendant de CAMS**, par OPeNDAP.

Pourquoi cette source
-----------------------
Les six membres de l'ensemble CAMS sont **corrélés entre eux** : leur moyenne ne rend que
+0,03 %. GEOS-CF (NASA GMAO) est un système entièrement distinct — météo GEOS et non IFS,
chimie GEOS-Chem, inventaire et assimilation différents. C'est la seule source identifiée
susceptible d'apporter de l'information de grande ampleur.

Trois conventions **vérifiées dans les données**, pas supposées
----------------------------------------------------------------
1. **La sortie est à 12 UTC**, pas 00 comme CAMS. Le premier pas d'une sortie `AAAAMMJJ_12z`
   est à **12:30 UTC du jour même**, le dernier à 11:30 de J+4.
2. **Ce sont des moyennes horaires centrées sur la demi-heure** (`tavg_1hr`) : le pas
   étiqueté 12:30 couvre [12:00, 13:00).
3. Pour couvrir une journée **D entière**, il faut donc la sortie de **D−1 à 12z**, pas 12
   à 35. Elle est émise **douze heures avant** la sortie CAMS de D : la comparaison est au
   pire équitable, jamais à notre avantage.

Supposer « échéances 1-24 = J0 » aurait été faux en silence — c'est la faute que la
règle 4 ter du projet interdit.

Le coût, mesuré avant de lancer
---------------------------------
Une requête OPeNDAP contrainte — 4 variables × 24 pas × emprise France — pèse ~1,1 Mo et
prend ~10 s. Le serveur GrADS découpe côté serveur : lire les fichiers un à un coûtait
**13 s par champ horaire**, soit 60 fois plus.

La lecture charge **l'emprise entière puis indexe en mémoire** : 476 `sel()` sur un jeu
paresseux dégénèrent en lecture point par point — c'est la règle 2 du projet, qui a déjà
coûté un facteur 400.

Les unités
------------
Les gaz sont en **mol/mol**, les PM2,5 en µg/m³. La conversion applique la convention
européenne (293,15 K, 1013,25 hPa). ⚠️ Elle est **sans enjeu tant que la variable sert de
prédicteur** — un arbre est invariant par changement d'échelle linéaire. Elle ne compterait
que si GEOS-CF était publié comme prévision concurrente.

Usage :
  python3 scripts/extraire_geoscf.py --passe-unitaire --mois 2025-07
  python3 scripts/extraire_geoscf.py --mois 2025-07,2025-08 --etiquette A
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

# Deux flux successifs, **pas compatibles** — et ne pas s'en apercevoir aurait été
# silencieux : v1 a été retiré le **2 janvier 2026**, v2 avait démarré le 5 août 2025.
# Un code figé sur v1 aurait cessé de produire ce jour-là sans lever d'erreur de flux.
#
# v2 change trois choses : l'heure de sortie (09z contre 12z), le nom de la collection,
# et **les noms de variables** — `pm25_rh35_gcc` devient `pm25_rh35`, et surtout v2
# **ajoute `pm10_rh35`**, le polluant qui déclenche 77 % des procédures et le seul sans
# membres d'ensemble CAMS.
VERSIONS = {
    "v1": {"racine": ("https://opendap.nccs.nasa.gov/dods/gmao/geos-cf/fcast/"
                      "aqc_tavg_1hr_g1440x721_v1/aqc_tavg_1hr_g1440x721_v1"),
           "heure": "12z",
           "vars": {"o3": "o3", "no2": "no2", "pm25_rh35_gcc": "pm25", "co": "co"}},
    "v2": {"racine": ("https://opendap.nccs.nasa.gov/dods/gmao/geos-cf/v2/fcst/"
                      "aqc_tavg_1hr_glo_L1440x721_slv/aqc_tavg_1hr_glo_L1440x721_slv"),
           "heure": "09z",
           "vars": {"o3": "o3", "no2": "no2", "pm25_rh35": "pm25",
                    "pm10_rh35": "pm10", "co": "co"}},
}
VERSION = {"courante": "v1"}          # fixée par la ligne de commande
SORTIE = RACINE / "data/processed/meteo"
EMPRISE = dict(lat=slice(41.0, 52.0), lon=slice(-6.0, 10.0))
# masse molaire (g/mol) ; densité molaire à 293,15 K et 1013,25 hPa
MOLAIRE = {"o3": 48.0, "no2": 46.0, "co": 28.0, "so2": 64.0}   # les PM sont déjà en µg/m³
DENSITE_MOLAIRE = 101325.0 / (8.314462618 * 293.15)      # mol/m³



def stations() -> pd.DataFrame:
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "lat_wgs84", "lon_wgs84", "metropole",
                                  "active"])
    st = st[st["metropole"] & st["active"]].drop_duplicates("station_id")
    return st.dropna(subset=["lat_wgs84", "lon_wgs84"]).reset_index(drop=True)


def extraire_sortie(jour: pd.Timestamp, st: pd.DataFrame) -> pd.DataFrame:
    """La sortie de `jour` à 12z, restreinte aux pas couvrant **le lendemain entier**.

    ⚠️ Lecture par `netCDF4` et **non** `xarray` : le client DAP de `xarray` émet une
    multitude de petites requêtes et met plus de 600 s là où le découpage explicite en
    prend 59. C'est la règle 2 du projet sous une autre forme — charger le bloc voulu en
    une fois, puis indexer en mémoire.
    """
    from netCDF4 import Dataset

    cfg = VERSIONS[VERSION["courante"]]
    variables = list(cfg["vars"])
    ds = Dataset(f'{cfg["racine"]}.{jour:%Y%m%d}_{cfg["heure"]}')
    try:
        lat = np.asarray(ds.variables["lat"][:])
        lon = np.asarray(ds.variables["lon"][:])
        i0, i1 = int(np.searchsorted(lat, 41.0)), int(np.searchsorted(lat, 52.0))
        j0, j1 = int(np.searchsorted(lon, -6.0)), int(np.searchsorted(lon, 10.0))

        # ⚠️ L'axe est en « days since 1-1-1 00:00:0.0 » — convention GrADS, référence à
        # l'an **1**. `pd.to_timedelta` déborde dessus (739 433 jours). `num2date` de
        # netCDF4 la décode correctement ; on ne devine jamais un calendrier, on le lit.
        from netCDF4 import num2date  # noqa: PLC0415

        vt = ds.variables["time"]
        brut = np.asarray(vt[:])
        dates = num2date(brut, units=vt.units,
                         calendar=getattr(vt, "calendar", "standard"),
                         only_use_cftime_datetimes=False)
        horo = pd.DatetimeIndex([pd.Timestamp(str(x)) for x in dates]).round("min")
        lendemain = (jour + pd.Timedelta(days=1)).normalize()
        garde = np.flatnonzero((horo >= lendemain)
                               & (horo < lendemain + pd.Timedelta(days=1)))
        # **Compter le reçu contre le demandé** : une journée fait 24 pas, jamais autre
        # chose. Un axe qui n'en rend pas 24 signale une convention différente.
        if len(garde) != 24:
            raise ValueError(f"{jour:%Y-%m-%d} : {len(garde)} pas pour le lendemain, "
                             f"24 attendus — convention temporelle à revérifier")
        k0, k1 = int(garde[0]), int(garde[-1]) + 1
        # ⚠️ Le pas étiqueté 12:30 est la moyenne sur [12:00, 13:00). Le panel
        # d'observations étiquette ses heures par leur **fin** : il faut donc l'attribuer
        # à 13:00, pas à 12:00. Mesuré le 04/08 par balayage de décalage — la corrélation
        # culmine à +1 h sur O₃ (0,5634 contre 0,5460) et sur NO₂ (0,2673 contre 0,2603).
        # Avec ce calage, les 24 pas d'une journée portent les heures 01:00 à 00:00 du
        # lendemain, exactement la convention des échéances 1-24 de CAMS.
        ts = (horo[garde] + pd.Timedelta(minutes=30)).floor("h")

        ilat = np.abs(lat[i0:i1, None] - st["lat_wgs84"].values[None, :]).argmin(0)
        ilon = np.abs(lon[j0:j1, None] - st["lon_wgs84"].values[None, :]).argmin(0)
        blocs = {}
        manquantes = [v for v in variables if v not in ds.variables]
        # **Compter le reçu contre le demandé** : un service qui ignore un nom
        # invalide sert le reste sans lever, et la variable disparaît en silence.
        if manquantes:
            raise ValueError(f"variables absentes du flux : {manquantes}")
        for v in variables:
            a = np.ma.filled(ds.variables[v][k0:k1, 0, i0:i1, j0:j1], np.nan)
            blocs[v] = a[:, ilat, ilon]
    finally:
        ds.close()

    n_t, n_s = blocs[variables[0]].shape
    out = pd.DataFrame({"station_id": np.tile(st["station_id"].values, n_t),
                        "timestamp_utc": np.repeat(ts, n_s)})
    for v, nom in cfg["vars"].items():
        x = blocs[v].reshape(-1).astype("float64")
        if nom in MOLAIRE:                      # mol/mol → µg/m³ (les gaz seulement)
            x = x * MOLAIRE[nom] * DENSITE_MOLAIRE * 1e6
        out[f"geoscf_{nom}"] = x.astype("float32")
    return out


def passe_unitaire(mois: str) -> int:
    """Les deux axes — résultat **et** coût — avant tout lot."""
    st = stations()
    debut = pd.Timestamp(f"{mois}-01")
    jours = pd.date_range(debut - pd.Timedelta(days=1), periods=3, freq="D")
    # ⚠️ Règle § 1 ter : une durée mesurée une fois n'est pas un débit. Ce service a
    # varié d'un facteur 20 en une heure — 3,6 s, 76 s, puis 504. On mesure chaque sortie
    # séparément et l'on extrapole depuis la **pire**, jamais la première ni la meilleure.
    durees, blocs = [], []
    for j in jours:
        t0 = time.time()
        blocs.append(extraire_sortie(j, st))
        durees.append(time.time() - t0)
    d = pd.concat(blocs, ignore_index=True)
    cout = max(durees)
    print(f"durées par sortie : " + " · ".join(f"{x:.0f}s" for x in durees)
          + f"  → médiane {np.median(durees):.0f}s, PIRE {cout:.0f}s", flush=True)
    print(f"{len(d):,} lignes · {d['station_id'].nunique()} stations · "
          f"{d['timestamp_utc'].nunique()} heures")
    print(f"coût : {cout:.1f} s par sortie · extrapolation 885 jours = "
          f"**{cout * 885 / 3600:.1f} h** en série, {cout * 885 / 4 / 3600:.1f} h à 4",
          flush=True)
    for c in [x for x in d.columns if x.startswith("geoscf_")]:
        v = d[c]
        print(f"  {c:14s} médiane {v.median():8.2f} · p95 {v.quantile(.95):8.2f} · "
              f"max {v.max():9.2f} µg/m³ · nuls {100 * v.isna().mean():.1f} %")

    # ── Axe résultat : le décalage horaire, mesuré contre les observations ──────
    from fit_mos import PANEL_UNIFIE  # noqa: PLC0415
    print(f"\n  balayage du décalage horaire — la corrélation doit culminer à 0 h :")
    for polluant, col in (("O3", "geoscf_o3"), ("NO2", "geoscf_no2")):
        # ⚠️ Le panel porte des horodatages **avec fuseau** ; nos bornes sont naïves.
        # Arrow refuse la comparaison sans lever de message lisible — on aligne les deux.
        b0 = (d["timestamp_utc"].min() - pd.Timedelta(hours=3)).tz_localize("UTC")
        b1 = (d["timestamp_utc"].max() + pd.Timedelta(hours=3)).tz_localize("UTC")
        obs = pd.read_parquet(
            RACINE / PANEL_UNIFIE,
            filters=[("polluant", "==", polluant),
                     ("timestamp_utc", ">=", b0),
                     ("timestamp_utc", "<=", b1)],
            columns=["station_id", "timestamp_utc", "valeur"])
        obs["timestamp_utc"] = pd.to_datetime(obs["timestamp_utc"]).dt.tz_localize(None)
        ligne = []
        for dec in (-2, -1, 0, 1, 2):
            g = d[["station_id", "timestamp_utc", col]].copy()
            g["timestamp_utc"] = g["timestamp_utc"] + pd.Timedelta(hours=dec)
            j = g.merge(obs, on=["station_id", "timestamp_utc"]).dropna()
            r = j[col].corr(j["valeur"]) if len(j) > 500 else np.nan
            ligne.append(f"{dec:+d} h : {r:.4f}" + ("  ←" if dec == 0 else ""))
        print(f"    {polluant:4s} " + " · ".join(ligne))
    print(f"\n  ⚠️ Si la corrélation culmine ailleurs qu'à 0 h, la convention est fausse")
    print(f"     et le lot ne doit PAS être lancé.")
    return 0


def main(mois_liste: list[str], etiquette: str) -> int:
    st = stations()
    SORTIE.mkdir(parents=True, exist_ok=True)
    depart, faits, echecs = time.time(), 0, []
    for mois in mois_liste:
        cible = SORTIE / (f"geoscf_metropole_{mois.replace('-', '')}"
                      + ("" if VERSION["courante"] == "v1" else "_v2") + ".parquet")
        # ⚠️ **La reprise porte sur le CONTENU, jamais sur l'existence du fichier.**
        # Le 04/08, le mois 2025-11 est sorti avec 29 jours sur 30 sous un nom définitif :
        # il n'aurait plus jamais été repris, et le trou ne serait apparu qu'en aval. On
        # nomme donc les jours attendus un par un et l'on compare — règle 4 du projet.
        cal = pd.date_range(f"{mois}-01", periods=pd.Period(mois).days_in_month, freq="D")
        if cible.exists():
            vus = set(pd.to_datetime(
                pd.read_parquet(cible, columns=["timestamp_utc"])["timestamp_utc"]
            ).dt.floor("D").dt.date)
            absents = [d for d in cal.date if d not in vus]
            if not absents:
                print(f"[{etiquette}] {mois} complet ({len(cal)} jours)", flush=True)
                continue
            print(f"[{etiquette}] {mois} INCOMPLET — {len(absents)} jour(s) manquant(s) : "
                  f"{', '.join(str(d) for d in absents[:5])} — mois refait", flush=True)
        debut = pd.Timestamp(f"{mois}-01")
        fin = debut + pd.offsets.MonthEnd(0)
        # sortie de D−1 pour couvrir D : on part de la veille du 1er
        jours = pd.date_range(debut - pd.Timedelta(days=1), fin - pd.Timedelta(days=1),
                              freq="D")
        blocs, rates = [], 0
        for j in jours:
            try:
                blocs.append(extraire_sortie(j, st))
            except Exception as exc:  # noqa: BLE001
                rates += 1
                print(f"[{etiquette}] {mois} · sortie {j:%Y-%m-%d} ÉCHEC "
                      f"{type(exc).__name__}: {str(exc)[:110]}", flush=True)
        if not blocs or rates > len(jours) * 0.2:
            echecs.append(mois)
            print(f"[{etiquette}] {mois} REJETÉ — {rates}/{len(jours)} sorties perdues",
                  flush=True)
            continue
        d = pd.concat(blocs, ignore_index=True)
        prov = cible.with_suffix(".parquet.partiel")
        d.to_parquet(prov, index=False)
        prov.replace(cible)          # nom définitif = contenu vérifié
        faits += 1
        ecoule = time.time() - depart
        print(f"[{etiquette}] {mois} · {len(d):,} lignes · {len(jours) - rates}/"
              f"{len(jours)} sorties · {ecoule / 60:.0f} min écoulées", flush=True)
    print(f"[{etiquette}] TERMINÉ · {faits} mois · {len(echecs)} échec(s)"
          + (" : " + ", ".join(echecs) if echecs else ""), flush=True)
    return 0 if not echecs else 1


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--passe-unitaire", action="store_true")
    a.add_argument("--mois", default="2025-07")
    a.add_argument("--etiquette", default="geoscf")
    a.add_argument("--version", default="v1", choices=("v1", "v2"))
    n = a.parse_args()
    VERSION["courante"] = n.version
    if n.passe_unitaire:
        raise SystemExit(passe_unitaire(n.mois.split(",")[0]))
    raise SystemExit(main([x.strip() for x in n.mois.split(",") if x.strip()],
                          n.etiquette))
