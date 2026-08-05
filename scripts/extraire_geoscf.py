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
MOLAIRE = {"o3": 48.0, "no2": 46.0, "co": 28.0, "so2": 64.0}
# Plafonds de **plausibilité physique**, en µg/m³, appliqués APRÈS conversion. Au-delà, la
# valeur n'est pas une concentration : c'est un code de remplissage ou de la mémoire non
# initialisée que le service n'a pas signalé.
#
# ⚠️ Mesuré le 04/08 : `pm10` de juin 2026 atteignait **3,24 × 10³⁸** — la borne du flottant
# simple précision — et `co` de mai 2026 **2,61 × 10¹⁰**, soit une fraction molaire de 22,
# impossible. Le `_FillValue` déclaré vaut 1,0 × 10¹⁵ et `netCDF4` le masque ; ces deux blocs
# lui échappent. Troisième occurrence du même piège en une journée, après les membres CAMS.
PLAFOND_UG = {"o3": 1200.0, "no2": 1500.0, "pm25": 1500.0, "pm10": 2000.0,
              "co": 50000.0, "so2": 5000.0}   # les PM sont déjà en µg/m³
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
        plafond = PLAFOND_UG.get(nom)
        if plafond is not None:
            # ⚠️ Test **des DEUX côtés**. Une première version ne bornait que par le haut :
            # le mois 2026-06 portait 1 232 valeurs à **−3,32 × 10³⁸** — la borne négative
            # du flottant simple précision, donc de la mémoire non initialisée — que le
            # maximum ne voyait pas. La RMSE sortait à 1,7 × 10³⁵ sur des données dont le
            # maximum affichait un rassurant 504. Une concentration est positive : tout ce
            # qui sort de [−1, plafond] est un artefact, jamais une mesure.
            mauvais = (x > plafond) | (x < -1.0)
            n = int(mauvais.sum())
            if n:
                x = np.where(mauvais, np.nan, x)
                part = n / max(x.size, 1)
                print(f"    ⚠️ {nom} : {n:,} valeur(s) au-dessus de {plafond:g} µg/m³ "
                      f"({100 * part:.3f} %) masquée(s)", flush=True)
                if part > 0.05:
                    raise ValueError(f"{nom} : {100 * part:.1f} % de valeurs aberrantes — "
                                     f"sortie suspecte, non écrite")
        out[f"geoscf_{nom}"] = x.astype("float32")
    return out


# Noms de variables dans les fichiers BRUTS du portail : en MAJUSCULES, contrairement au
# serveur OPeNDAP qui les expose en minuscules. Deviner l'un depuis l'autre serait une
# convention supposée de plus.
BRUT_VERS_NOM = {"O3": "o3", "NO2": "no2", "PM25_RH35": "pm25", "PM10_RH35": "pm10",
                 "CO": "co"}
PORTAIL = "https://portal.nccs.nasa.gov/datashare/gmao/geos-cf/v2/fcst"


def extraire_sortie_fichiers(jour: pd.Timestamp, st: pd.DataFrame,
                             fils: int = 6) -> pd.DataFrame:
    """Repli : lire les fichiers BRUTS du portail, quand le serveur OPeNDAP échoue.

    ⚠️ Pourquoi cette seconde voie existe. Sept sorties d'octobre 2025 rendent
    systématiquement `NetCDF: DAP server error` — trois tentatives, reprise incluse — alors
    que **les fichiers existent** : 120 par jour sur le portail. Ce ne sont pas des pannes
    réseau, c'est le service d'agrégation qui est défectueux sur ces dates. Le portail de
    fichiers est un service **distinct** et il répond.

    Coût mesuré : 31,8 s médian et 48,9 s au pire par fichier en séquentiel, **8,6 s à six
    fils** — un gain de 5,7×. Soit ~24 min pour sept jours.
    """
    import subprocess
    import tempfile
    from concurrent.futures import ThreadPoolExecutor

    from netCDF4 import Dataset

    lendemain = (jour + pd.Timedelta(days=1)).normalize()
    base = (f"{PORTAIL}/Y{jour:%Y}/M{jour:%m}/D{jour:%d}/"
            f"GEOS.cf.fcst.aqc_tavg_1hr_glo_L1440x721_slv.{jour:%Y%m%d}_09z")

    def un(h: int):
        u = f"{base}+{lendemain:%Y%m%d}_{h:02d}30z.R0.nc4"
        f = tempfile.NamedTemporaryFile(suffix=".nc4", delete=False)
        try:
            # ⚠️ `curl` et non `urllib` : le second a rendu « Network is unreachable » là
            # où le premier répond HTTP 200 sur les mêmes URL, dans le même processus et
            # sans variable de proxy. Ne pas diagnostiquer une intermittence de
            # bibliothèque quand un outil éprouvé fait le travail — et `--retry` gère les
            # coupures pour nous.
            r = subprocess.run(
                ["curl", "-sS", "-f", "--retry", "3", "--retry-delay", "2",
                 "--max-time", "180", "-o", f.name, u],
                capture_output=True, text=True)
            if r.returncode != 0 or Path(f.name).stat().st_size < 100_000:
                raise OSError(f"curl {r.returncode} sur {u.split('/')[-1]} : "
                              f"{r.stderr.strip()[:90]}")
            d = Dataset(f.name)
            try:
                lat = np.asarray(d.variables["lat"][:])
                lon = np.asarray(d.variables["lon"][:])
                i0, i1 = int(np.searchsorted(lat, 41.0)), int(np.searchsorted(lat, 52.0))
                j0, j1 = int(np.searchsorted(lon, -6.0)), int(np.searchsorted(lon, 10.0))
                il = np.abs(lat[i0:i1, None] - st["lat_wgs84"].values[None, :]).argmin(0)
                jl = np.abs(lon[j0:j1, None] - st["lon_wgs84"].values[None, :]).argmin(0)
                out = {}
                for v, nom in BRUT_VERS_NOM.items():
                    if v not in d.variables:
                        raise ValueError(f"variable {v} absente de {u.split('/')[-1]}")
                    a = np.ma.filled(d.variables[v][0, 0, i0:i1, j0:j1], np.nan)
                    out[nom] = a[il, jl]
                return h, out
            finally:
                d.close()
        finally:
            Path(f.name).unlink(missing_ok=True)

    with ThreadPoolExecutor(fils) as ex:
        res = dict(ex.map(lambda h: un(h)[::-1][::-1], range(24)))
    if len(res) != 24:
        raise ValueError(f"{jour:%Y-%m-%d} : {len(res)} heures sur 24 par le portail")

    # ⚠️ Même calage que la voie OPeNDAP : le pas étiqueté HH:30 couvre [HH:00, HH+1:00)
    # — vérifié dans les attributs `RangeBeginningTime`/`RangeEndingTime` du fichier — et
    # s'attribue donc à l'heure HH+1, convention de fin d'heure du panel d'observations.
    lignes, horo = [], []
    for h in range(24):
        horo.append(lendemain + pd.Timedelta(hours=h + 1))
        lignes.append(res[h])
    n_s = len(st)
    out = pd.DataFrame({"station_id": np.tile(st["station_id"].values, 24),
                        "timestamp_utc": np.repeat(pd.DatetimeIndex(horo), n_s)})
    for nom in set(BRUT_VERS_NOM.values()):
        x = np.concatenate([lignes[h][nom] for h in range(24)]).astype("float64")
        if nom in MOLAIRE:
            x = x * MOLAIRE[nom] * DENSITE_MOLAIRE * 1e6
        pl = PLAFOND_UG.get(nom)
        if pl is not None:
            x = np.where((x > pl) | (x < -1.0), np.nan, x)
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


def main(mois_liste: list[str], etiquette: str, tolerance: float = 0.2) -> int:
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
            # ⚠️ **Réessayer une fois avant d'abandonner une sortie.** Les échecs de ce
            # service sont des pannes d'entrée/sortie transitoires — `NetCDF: I/O failure`,
            # `OSError -68` — qui passent au second essai. Sans reprise, le mois 2025-10 a
            # été rejeté DEUX fois pour 7 sorties perdues sur 31 (22,6 %, juste au-dessus
            # du seuil de 20 %), alors qu'aucune n'était un défaut de données.
            derniere = None
            for essai in (1, 2):
                try:
                    blocs.append(extraire_sortie(j, st))
                    derniere = None
                    break
                except ValueError as exc:      # convention temporelle : ne PAS réessayer
                    derniere = exc
                    break
                except Exception as exc:       # noqa: BLE001 — transitoire
                    derniere = exc
                    if essai == 1:
                        time.sleep(5)
            if derniere is not None and VERSION["courante"] == "v2":
                # Le serveur d'agrégation a renoncé : essayer les fichiers bruts.
                try:
                    blocs.append(extraire_sortie_fichiers(j, st))
                    print(f"[{etiquette}] {mois} · sortie {j:%Y-%m-%d} récupérée par le "
                          f"PORTAIL après échec OPeNDAP", flush=True)
                    derniere = None
                except Exception as exc:  # noqa: BLE001
                    derniere = exc
            if derniere is not None:
                rates += 1
                print(f"[{etiquette}] {mois} · sortie {j:%Y-%m-%d} ÉCHEC "
                      f"{type(derniere).__name__}: {str(derniere)[:110]}", flush=True)
        # ⚠️ La tolérance protège le CORPUS d'un mois estropié. Pour un mois de
        # **diagnostic** — comparer deux versions sur des jours identiques — 24 jours
        # sur 31 suffisent, et la desserrer est légitime À CONDITION de le dire.
        if not blocs or rates > len(jours) * tolerance:
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
    a.add_argument("--tolerance", type=float, default=0.2,
                   help="part de sorties perdues admise avant rejet du mois")
    n = a.parse_args()
    VERSION["courante"] = n.version
    if n.passe_unitaire:
        raise SystemExit(passe_unitaire(n.mois.split(",")[0]))
    raise SystemExit(main([x.strip() for x in n.mois.split(",") if x.strip()],
                          n.etiquette, n.tolerance))
