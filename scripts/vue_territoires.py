#!/usr/bin/env python3
"""Les données de la vue navigable France → région → département.

Pourquoi un JSON et non 106 pages empilées
-------------------------------------------
Le dépôt porte déjà 84 pages départementales et 13 régionales, à ~143 Ko pièce. Les
empiler donnerait ~12 Mo, au ras du plafond de 16 Mo d'un artefact, **et** ne
produirait aucune navigation : ce serait un classeur, pas une vue.

Ce script extrait la **matière** — métriques et contexte — dans un JSON compact que la
page recompose côté client. Le même jeu sert les trois échelles, donc les trois échelles
ne peuvent pas diverger.

Ce qu'il assemble, et d'où ça vient
------------------------------------
| bloc | source | nature |
|---|---|---|
| gain par territoire | `production_<P>_h1.parquet` via `pages_soutenance.stats_stations` | **mesuré** |
| dépassement au seuil 2030 | `reports/seuils_2030.csv` | **mesuré** |
| émissions, relief, saisonnalité, cadre de décision, pièges | `docs/departements/lot*.yaml` | **sourcé** (chaque item porte son lien) |
| contours | `data/raw/geo/*.geojson` | référentiel |

⚠️ Les gains sont calculés par **les mêmes fonctions** que les pages publiées
(`stats_stations`, colonne `nous`, référence `aasqa`). Réécrire le calcul ici ferait
diverger deux chiffres qui doivent être identiques — c'est la faute que ce dépôt a déjà
payée en publiant deux variantes d'un même score.

⚠️ **Un territoire sans station n'est pas un territoire à zéro.** Les deux se
distinguent dans le JSON (`null` contre `0`) et la page doit les afficher différemment :
c'est le « zéro de non-lecture indiscernable d'un zéro de non-occurrence » de § 4 bis.

Usage : python3 scripts/vue_territoires.py
Sortie : reports/figures/territoires.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from pages_regions import (SOURCE_DEPARTEMENTS, charger_regions,  # noqa: E402
                           charger_territoires, rattacher)
from pages_soutenance import charger, stats_stations  # noqa: E402

POLLUANTS = ("O3", "NO2", "PM10", "PM25")
NOM = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}
HORIZON = 1
LARGEUR = 1000.0        # unités du viewBox SVG


def chemins_svg(territoires: list[dict], bornes: tuple) -> dict[str, str]:
    """Contours L93 → chemins SVG dans un viewBox partagé, Y inversé."""
    x0, y0, x1, y1 = bornes
    ech = LARGEUR / (x1 - x0)
    out = {}
    for t in territoires:
        morceaux = []
        for c in t["chemins"]:
            px = (c[:, 0] - x0) * ech
            py = (y1 - c[:, 1]) * ech
            pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(px, py))
            morceaux.append("M" + pts.replace(" ", "L", 1).replace(" ", " L") + "Z")
        out[t["code"]] = "".join(morceaux)
    return out


def bornes_communes(*groupes: list[dict]) -> tuple:
    tous = np.vstack([c for g in groupes for t in g for c in t["chemins"]])
    return (tous[:, 0].min(), tous[:, 1].min(), tous[:, 0].max(), tous[:, 1].max())


def region_par_departement(departements: list[dict], regions: list[dict]) -> dict:
    """Département → CODE de région, par géométrie.

    ⚠️ Surtout pas par le champ `region` des blocs YAML : il porte le **nom**
    (« Occitanie ») quand la carte manipule le **code** (« 76 »). La page comparait donc
    « Occitanie » à « 76 », aucun département n'était reconnu, et la carte affichait un
    niveau départemental entièrement grisé — sans lever la moindre erreur.
    Deux référentiels qui se ressemblent ne se joignent jamais sur le libellé.
    """
    lignes = []
    for d in departements:
        grand = max(d["chemins"], key=len)          # l'anneau principal, pas les îles
        lignes.append({"station_id": d["code"], "commune": d["nom"],
                       "x_l93": float(grand[:, 0].mean()),
                       "y_l93": float(grand[:, 1].mean())})
    r = rattacher(pd.DataFrame(lignes), regions)
    out = {c: reg for c, reg in zip(r["station_id"], r["region"]) if reg}
    orphelins = sorted({d["code"] for d in departements} - set(out))
    if orphelins:
        print(f"  ⚠️ {len(orphelins)} département(s) non rattaché(s) à une région : "
              f"{', '.join(orphelins)}")
    return out


def stations_situees() -> pd.DataFrame:
    """Chaque station avec sa région et son département — un seul rattachement."""
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "nom", "commune", "x_l93", "y_l93"])
    st = st.drop_duplicates("station_id").dropna(subset=["x_l93", "y_l93"])
    reg = rattacher(st, charger_regions())[["station_id", "nom", "commune", "region"]]
    dep = rattacher(st, charger_territoires(SOURCE_DEPARTEMENTS))[["station_id", "region"]]
    return reg.merge(dep.rename(columns={"region": "departement"}), on="station_id")


def metriques(d: pd.DataFrame, situe: pd.DataFrame) -> dict:
    """Gain par territoire, calculé par la fonction des pages publiées."""
    ss = stats_stations(d, "nous").merge(situe, on="station_id", how="left")
    out = {}

    def agrege(sous: pd.DataFrame) -> dict | None:
        if sous.empty:
            return None
        # RMSE agrégée pondérée par le nombre de jours — jamais une moyenne de RMSE,
        # qui donnerait le même poids à une station de 30 jours et à une de 500.
        n = sous["n"].to_numpy()
        rn = float(np.sqrt(np.sum(n * sous["rmse_nous"] ** 2) / n.sum()))
        ra = float(np.sqrt(np.sum(n * sous["rmse_aasqa"] ** 2) / n.sum()))
        return {"stations": int(len(sous)), "jours_station": int(n.sum()),
                "rmse_nous": round(rn, 3), "rmse_aasqa": round(ra, 3),
                "gain": round(100 * (1 - rn / ra), 2),
                "part_ameliorees": round(100 * float((sous["gain"] > 0).mean()), 1)}

    out["FR"] = agrege(ss)
    for code, sous in ss.groupby("region"):
        if code:
            out[f"R{code}"] = agrege(sous)
    for code, sous in ss.groupby("departement"):
        if code:
            out[f"D{code}"] = agrege(sous)
    return out


def seuils_par_territoire() -> dict:
    f = RACINE / "reports/seuils_2030.csv"
    if not f.exists():
        return {}
    g = pd.read_csv(f)
    out = {}

    def compte(d: pd.DataFrame) -> dict:
        return {"stations": int(d["station_id"].nunique()),
                "sur_actuel": int(d.loc[d["depasse_actuel"], "station_id"].nunique()),
                "sur_2030": int(d.loc[d["depasse_2030"], "station_id"].nunique())}

    # ⚠️ Les codes de département ne sont PAS des entiers : la Corse porte `2A` et `2B`.
    # `int(code)` levait dessus — et un `except` l'aurait fait disparaître en silence,
    # laissant deux départements sans chiffre dans une page qui aurait l'air complète.
    def code2(x) -> str:
        s = str(x).strip()
        if s.endswith(".0"):
            s = s[:-2]
        return s.zfill(2) if s.isdigit() else s

    out["FR"] = compte(g)
    for code, s in g.dropna(subset=["region"]).groupby("region"):
        out[f"R{code2(code)}"] = compte(s)
    for code, s in g.dropna(subset=["departement"]).groupby("departement"):
        out[f"D{code2(code)}"] = compte(s)
    return out


def contexte_departements() -> dict:
    """Les 84 blocs sourcés — émissions, relief, saisonnalité, cadre, pièges."""
    blocs = {}
    for f in sorted((RACINE / "docs/departements").glob("lot*.yaml")):
        for d in yaml.safe_load(f.read_text(encoding="utf-8")) or []:
            blocs[f"D{d['code']}"] = {
                k: d.get(k) for k in
                ("nom", "region", "resume", "sources_dominantes", "topographie_climat",
                 "regime_episodes", "transport_longue_distance", "cadre_decision",
                 "pieges_modelisation", "sans_source")}
    return blocs


def main() -> int:
    print("Vue territoires — assemblage des données\n" + "─" * 70)
    regions = charger_regions()
    departements = charger_territoires(SOURCE_DEPARTEMENTS)
    bornes = bornes_communes(regions, departements)
    print(f"  {len(regions)} régions · {len(departements)} départements tracés")

    situe = stations_situees()
    print(f"  {len(situe)} stations situées")

    par_polluant, couverture = {}, {}
    for p in POLLUANTS:
        d = charger(p, HORIZON)
        if d is None:
            print(f"  ⚠️ {NOM[p]:6s} absent — production_{p}_h{HORIZON}.parquet")
            continue
        par_polluant[p] = metriques(d, situe)
        couverture[p] = {"debut": str(d["mois"].min()), "fin": str(d["mois"].max()),
                         "jours_station": int(len(d))}
        fr = par_polluant[p]["FR"]
        print(f"  {NOM[p]:6s} {fr['stations']:3d} stations · gain France "
              f"{fr['gain']:+6.2f} % · {couverture[p]['debut']} → {couverture[p]['fin']}")

    seuils = seuils_par_territoire()
    ctx = contexte_departements()
    print(f"  seuils 2030 : {len(seuils)} territoires · contexte : {len(ctx)} départements")

    # ⚠️ Un département tracé SANS bloc de contexte doit être nommé, pas oublié.
    sans_ctx = sorted({f"D{d['code']}" for d in departements} - set(ctx))
    if sans_ctx:
        print(f"  ⚠️ {len(sans_ctx)} département(s) tracé(s) sans bloc de contexte : "
              f"{', '.join(c[1:] for c in sans_ctx[:8])}")

    sortie = {
        "genere": datetime.now().isoformat(timespec="seconds"),
        "polluants": [p for p in POLLUANTS if p in par_polluant],
        "nom_polluant": NOM,
        "couverture": couverture,
        "viewbox": f"0 0 {LARGEUR:.0f} {(bornes[3] - bornes[1]) * LARGEUR / (bornes[2] - bornes[0]):.0f}",
        "geo": {
            "regions": [{"code": r["code"], "nom": r["nom"]} for r in regions],
            "departements": [{"code": d["code"], "nom": d["nom"]} for d in departements],
            "chemins_regions": chemins_svg(regions, bornes),
            "chemins_departements": chemins_svg(departements, bornes),
            "region_de_departement": region_par_departement(departements, regions),
        },
        "metriques": par_polluant,
        "seuils_2030": seuils,
        "contexte": ctx,
    }
    f = RACINE / "reports/figures/territoires.json"
    f.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")),
                 encoding="utf-8")
    print(f"\nÉcrit : {f.relative_to(RACINE)} · {f.stat().st_size / 1e6:.2f} Mo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
