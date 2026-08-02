#!/usr/bin/env python3
"""Observations du flux national LCSQA — celui qui alimente Geod'Air, sans authentification.

Pourquoi cette source, alors que le projet en a déjà une
--------------------------------------------------------
Le projet ingère les observations depuis le service de téléchargement de l'**Agence
européenne pour l'environnement**. Geod'Air, la référence nationale, avait été cataloguée
5/5 mais écartée : inscription avec validation manuelle, quota de 15 requêtes par heure,
délai d'approbation inconnu.

Or le **même flux national** est publié sur `data.gouv.fr` par le LCSQA, **sans
authentification**, archivé jour par jour de **2021 à 2026**. Il lève les deux lacunes que
le dossier déclarait définitives :

* **PM10** — jamais ingérées, alors que **40 des 52 vigilances réellement déclarées** en
  Occitanie entre janvier 2025 et mars 2026 portent sur ce polluant. Ici : 328 à 335 sites
  par jour ;
* **l'ozone après le 1ᵉʳ juillet 2025** — rompu dans notre flux, **continu** dans celui-ci
  (277 sites en août 2025, 279 en mai 2026).

Ce ne sont donc pas des limites de la donnée française, mais du flux choisi au départ.

Ce que le fichier contient
--------------------------
Un CSV par jour, séparateur ``;``, encodage UTF-8 avec BOM, ~12 Mo, ~48 000 lignes,
487 sites. Colonnes utiles : ``code site``, ``Polluant``, ``Date de début``, ``valeur``,
``validité``, ``type d'implantation``, ``type d'influence``, ``Zas``, ``taux de saisie``.

⚠️ **``validité`` prend trois valeurs** — 1, 4 et −1 — et non deux. Le sens de 4 a été
vérifié le 01/08/2026 dans le vocabulaire EIONET auquel renvoie la note explicative du
LCSQA (`dd.eionet.europa.eu/vocabulary/aq/observationvalidity`) :

| code | libellé | valide ? |
|---|---|---|
| −99 | *Not valid due to station maintenance or calibration* | non |
| −1 | *Not valid* | non |
| 1 | *Valid* | oui |
| 2 | *Valid, but below detection limit* | oui |
| 3 | *Valid, but below detection limit and number replaced* | oui |
| 4 | *Valid (Ozone only) using CCQM.O3.2019* | **oui** |

**Le code 4 est une donnée valide**, pas une donnée non validée : il signale seulement que
la mesure d'ozone se rattache à l'étalon métrologique CCQM.O3.2019, ajouté au vocabulaire
en juillet 2024. La France y a basculé le 01/07/2025 — d'où le passage de **tout** l'ozone
en code 4 à cette date.

Le filtre `validite == 1` qui régnait ici jusqu'au 01/08/2026 **jetait donc 13 mois d'ozone
valide, en silence et avant écriture** : les fichiers de `data/interim/` n'en portaient
aucune trace. Le filtre retient désormais tous les codes positifs.

Réserve à mesurer, pas à supposer : un changement d'étalon peut déplacer le niveau des
concentrations. Vérifier la continuité de part et d'autre du 01/07/2025 avant d'agréger
les deux périodes.

Usage :
  python3 scripts/ingerer_lcsqa.py --passe-unitaire
  python3 scripts/ingerer_lcsqa.py --debut 2024-01-01 --fin 2024-12-31
Sortie : data/interim/lcsqa/lcsqa_{AAAAMM}.parquet
"""

from __future__ import annotations

import argparse
import io
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.ingest.controle import ControleEchec, exiger_colonnes, exiger_lignes  # noqa: E402

BASE = ("https://files.data.gouv.fr/ineris/lcsqa/"
        "concentrations-de-polluants-atmospheriques-reglementes/temps-reel")
SORTIE = RACINE / "data/interim/lcsqa"
# Les quatre polluants du dossier plus les PM10, qui sont la raison d'être de cette source.
POLLUANTS = {"O3": "O3", "NO2": "NO2", "PM10": "PM10", "PM2.5": "PM25"}
COLONNES = ["code site", "Polluant", "Date de début", "Date de fin", "valeur", "validité",
            "type d'implantation", "type d'influence", "Zas", "taux de saisie"]


def jour(d: date) -> pd.DataFrame:
    """Un jour du flux national, filtré aux polluants utiles."""
    url = f"{BASE}/{d.year}/FR_E2_{d.isoformat()}.csv"
    with urllib.request.urlopen(url, timeout=120) as r:
        brut = r.read()
    # Le service répond parfois une page de redirection en HTTP 200 : un CSV de 4 Ko n'est
    # pas un CSV de 12 Mo, et le laisser passer produirait un fichier vide plausible.
    if len(brut) < 100_000:
        raise ControleEchec(
            f"{d} : réponse de {len(brut)} octets, au moins 100 000 attendus — "
            f"probablement une page de redirection et non le fichier")
    t = pd.read_csv(io.BytesIO(brut), sep=";", encoding="utf-8-sig", low_memory=False)
    exiger_colonnes(t, COLONNES, f"flux LCSQA {d}")
    t = t[t["Polluant"].isin(POLLUANTS)].copy()
    exiger_lignes(t, 5000, f"flux LCSQA {d} après filtre polluants")
    t["polluant"] = t["Polluant"].map(POLLUANTS)
    # **« Date de fin », jamais « Date de début ».** Le flux LCSQA nomme l'heure par son
    # DÉBUT ; la chaîne du projet, comme le flux EEA, la nomme par sa FIN. Les deux sont en
    # UTC — ce n'est pas une affaire de fuseau mais d'étiquetage.
    #
    # Vérifié plutôt que supposé : sur 39 stations communes et une semaine de NO₂, l'écart
    # absolu moyen entre les deux sources vaut 2,99 µg/m³ sans décalage, 4,83 à −1 h, et
    # **0,0001 à +1 h**. La concordance est donc exacte une fois l'heure de fin retenue.
    #
    # Sans ce contrôle, chaque observation aurait été appariée à la mauvaise heure de
    # prévision, en silence et sans qu'aucune métrique ne le signale.
    t["timestamp_utc"] = pd.to_datetime(
        t["Date de fin"], format="%Y/%m/%d %H:%M:%S").dt.tz_localize("UTC")
    return t.rename(columns={"code site": "station_id", "validité": "validite",
                             "type d'implantation": "implantation",
                             "type d'influence": "influence",
                             "taux de saisie": "taux_saisie"})[
        ["station_id", "polluant", "timestamp_utc", "valeur", "validite",
         "implantation", "influence", "Zas", "taux_saisie"]]


def main(debut: str, fin: str, passe_unitaire: bool) -> int:
    depart = time.time()
    SORTIE.mkdir(parents=True, exist_ok=True)

    if passe_unitaire:
        # Règle 1 : mesurer l'unité définitive, sur les deux axes, avant tout lot.
        d = date.fromisoformat(debut)
        t0 = time.time()
        t = jour(d)
        duree = time.time() - t0
        print(f"{d} · {len(t):,} lignes · {t['station_id'].nunique()} sites · "
              f"{duree:.1f} s")
        print("\nAXE RÉSULTAT — ce que je reçois est-il ce que je crois ?")
        print(t.groupby("polluant").agg(
            n=("valeur", "size"), sites=("station_id", "nunique"),
            nulles=("valeur", lambda s: s.isna().sum()),
            mediane=("valeur", "median")).round(2).to_string())
        print(f"\n  validité : {dict(t['validite'].value_counts())}")
        print(f"  part validité == 1 : {(t['validite'] == 1).mean():.1%}")
        print(f"  heures couvertes : {t['timestamp_utc'].dt.hour.nunique()} sur 24")
        n_jours = (date.fromisoformat(fin) - d).days + 1
        print(f"\nAXE COÛT — le lot entier est-il tenable ?")
        print(f"  {n_jours} jours × {duree:.1f} s = **{n_jours * duree / 60:.0f} min**")
        print(f"  volume estimé : {n_jours * len(t) / 1e6:.1f} M lignes retenues")
        print("\nRelancer sans --passe-unitaire si ces deux axes conviennent.")
        return 0

    d, dfin = date.fromisoformat(debut), date.fromisoformat(fin)
    par_mois: dict[str, list] = {}
    manques, ecartes = [], 0
    while d <= dfin:
        cle = d.strftime("%Y%m")
        cible = SORTIE / f"lcsqa_{cle}.parquet"
        if cible.exists() and d.day == 1:
            # Reprise au mois : on saute, mais seulement si le mois est déjà **écrit**
            # sous son nom définitif — règle 4.
            saut = pd.Timestamp(d) + pd.offsets.MonthBegin(1)
            print(f"── {cle} déjà écrit, sauté", flush=True)
            d = saut.date()
            continue
        try:
            par_mois.setdefault(cle, []).append(jour(d))
        except Exception as e:  # noqa: BLE001 — on veut le nom du jour et la cause
            manques.append((d.isoformat(), f"{type(e).__name__}: {e}"))
            print(f"  ⚠️ {d} : {type(e).__name__}", flush=True)
        lendemain = d + timedelta(days=1)
        if lendemain.month != d.month or lendemain > dfin:
            morceaux = par_mois.pop(cle, [])
            if morceaux:
                m = pd.concat(morceaux, ignore_index=True)
                avant = len(m)
                # Codes positifs = valides (vocabulaire EIONET, voir l'en-tête). Le 4
                # est l'ozone à l'étalon CCQM.O3.2019 : le filtrer coûtait 13 mois.
                m = m[m["validite"] > 0]
                ecartes += avant - len(m)
                prov = (SORTIE / f"lcsqa_{cle}.parquet").with_suffix(".parquet.partiel")
                m.to_parquet(prov, index=False)
                prov.replace(SORTIE / f"lcsqa_{cle}.parquet")
                print(f"── {cle} · {len(m):,} lignes valides sur {avant:,} · "
                      f"{m['station_id'].nunique()} sites · {time.time() - depart:.0f}s",
                      flush=True)
        d = lendemain

    print(f"\n{len(manques)} jour(s) manquant(s) · {ecartes:,} lignes écartées "
          f"(validité ≠ 1)")
    for j, cause in manques[:10]:
        print(f"  {j} · {cause[:90]}")
    print(f"Écrit dans {SORTIE.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--debut", default="2024-01-01")
    a.add_argument("--fin", default="2024-12-31")
    a.add_argument("--passe-unitaire", action="store_true")
    n = a.parse_args()
    raise SystemExit(main(n.debut, n.fin, n.passe_unitaire))
