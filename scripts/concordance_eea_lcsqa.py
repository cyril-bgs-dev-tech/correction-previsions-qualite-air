#!/usr/bin/env python3
"""Les deux sources d'observation concordent-elles ? — le contrôle avant tout raccord.

Pourquoi ce contrôle existe avant la fusion, et non après
----------------------------------------------------------
Le corpus apparié du projet fait **18 mois**, borné par les observations **EEA** qui
s'arrêtent en 2025-01. Le flux **LCSQA** couvre 2024-01 → 2026-07, soit 31 mois. Les recoller
porterait le corpus à **36 mois** et les plis temporels de 17 à 29 — ce dont le double aveugle
a précisément besoin, l'ozone y rendant +3,3 % avec 7 plis négatifs sur 17.

Mais recoller deux sources de mesure, c'est **fabriquer une rupture au milieu du corpus** si
elles ne disent pas la même chose. Et cette rupture-là serait lue par le double aveugle comme
une non-stationnarité de l'atmosphère ou du modèle amont, alors qu'elle serait **de notre
fait**.

Ce n'est pas une précaution théorique : le 02/08/2026, ce projet a mesuré une « marche de
+17,96 % » sur l'ozone et l'a attribuée à un changement d'étalon métrologique. Le témoin NO₂
a montré que c'était faux. **Mesurer une marche est facile ; l'attribuer à la bonne cause ne
l'est pas.** Ici on a treize mois de recouvrement — 2024-01 → 2025-01 — pour trancher avant
de créer le problème plutôt qu'après.

Ce que le contrôle vérifie, dans cet ordre
-------------------------------------------
1. **La convention horaire.** Le flux LCSQA étiquette l'heure par son **début**, la chaîne du
   projet par sa **fin**. C'est déjà traité à l'ingestion, mais on le revérifie ici par
   balayage : on compare aux décalages −1, 0 et +1 h et on exige que **le zéro gagne
   largement**. Si un autre décalage l'emporte, la convention a changé quelque part.
2. **La couverture de stations.** Combien de stations sont communes, combien sont propres à
   chaque source ? Un raccord qui change la population de stations au milieu du corpus
   déplacerait le score sans que rien ne le signale.
3. **L'accord sur les valeurs communes.** Écart moyen, écart absolu médian, corrélation,
   et **part de couples strictement égaux**. Deux flux issus du même réseau devraient être
   quasi identiques ; un écart notable désignerait un traitement différent — arrondi, statut
   de validation, limite de détection.
4. **La stabilité dans le temps.** Le même accord, mois par mois. Un accord parfait sur douze
   mois et dégradé sur le treizième vaut refus.

Le verdict, écrit avant de voir les chiffres
---------------------------------------------
* **écart absolu médian < 0,5 µg/m³ et > 95 % de stations communes** → raccord légitime ;
* **écart médian systématique** → raccord possible **après correction du décalage**, à
  condition de la mesurer et de l'écrire ;
* **écart variable dans le temps ou population de stations différente** → **ne pas raccorder**,
  et se contenter des 18 mois. Un corpus plus court est préférable à un corpus faussé.

Usage : python3 scripts/concordance_eea_lcsqa.py [--polluants O3,NO2,PM25]
Sortie : reports/concordance_eea_lcsqa.csv
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

# La fenêtre où les deux sources coexistent. Bornes lues dans les données, jamais supposées.
RECOUVREMENT = ("2024-01", "2025-01")


def charger_lcsqa(polluant: str, debut: str, fin: str) -> pd.DataFrame:
    fichiers = sorted(glob.glob(str(RACINE / "data/interim/lcsqa/lcsqa_*.parquet")))
    mois_ok = {f for f in fichiers
               if debut.replace("-", "") <= f.split("_")[-1][:6] <= fin.replace("-", "")}
    if not mois_ok:
        raise SystemExit(f"aucun mois LCSQA entre {debut} et {fin}")
    morceaux = []
    for f in sorted(mois_ok):
        t = pd.read_parquet(f, columns=["station_id", "polluant", "timestamp_utc", "valeur"])
        t = t[t["polluant"] == polluant]
        if not t.empty:
            morceaux.append(t)
    d = pd.concat(morceaux, ignore_index=True)
    return d.rename(columns={"valeur": "lcsqa"}).drop(columns="polluant")


def charger_eea(polluant: str, debut: str, fin: str) -> pd.DataFrame:
    t = pd.read_parquet(RACINE / "data/processed/panel_metropole_ds2.parquet",
                        columns=["station_id", "polluant", "timestamp_utc", "valeur"])
    t = t[t["polluant"] == polluant]
    m = t["timestamp_utc"].dt.strftime("%Y-%m")
    t = t[(m >= debut) & (m <= fin)]
    return t.rename(columns={"valeur": "eea"}).drop(columns="polluant")


def accord(d: pd.DataFrame) -> dict:
    e, l = d["eea"].to_numpy(), d["lcsqa"].to_numpy()
    ecart = l - e
    return {"n": len(d), "biais_moyen": float(np.mean(ecart)),
            "ecart_absolu_median": float(np.median(np.abs(ecart))),
            "ecart_absolu_p95": float(np.quantile(np.abs(ecart), 0.95)),
            "correlation": float(np.corrcoef(e, l)[0, 1]) if len(d) > 2 else np.nan,
            "part_identiques": float(np.mean(np.abs(ecart) < 1e-6))}


def main(polluants: list[str]) -> int:
    depart = time.time()
    debut, fin = RECOUVREMENT
    lignes = []

    for polluant in polluants:
        print(f"\n{'═' * 78}\n{polluant} · recouvrement {debut} → {fin}\n{'═' * 78}",
              flush=True)
        lc = charger_lcsqa(polluant, debut, fin)
        ee = charger_eea(polluant, debut, fin)
        print(f"  LCSQA {len(lc):,} lignes · {lc['station_id'].nunique()} stations")
        print(f"  EEA   {len(ee):,} lignes · {ee['station_id'].nunique()} stations",
              flush=True)

        # ── ① La convention horaire, revérifiée par balayage ────────────────────
        # On ne suppose pas qu'elle est bonne parce qu'elle l'était : on la remesure.
        print(f"\n  ① convention horaire — le décalage 0 doit gagner LARGEMENT")
        meilleur, scores = None, {}
        for h in (-1, 0, 1):
            d = lc.copy()
            d["timestamp_utc"] = d["timestamp_utc"] + pd.Timedelta(hours=h)
            f = ee.merge(d, on=["station_id", "timestamp_utc"], how="inner")
            if f.empty:
                scores[h] = np.nan
                continue
            scores[h] = float(np.mean(np.abs(f["lcsqa"] - f["eea"])))
            print(f"     {h:+d} h · {len(f):>9,} couples · écart absolu moyen "
                  f"{scores[h]:8.4f} µg/m³")
        valides = {h: v for h, v in scores.items() if np.isfinite(v)}
        meilleur = min(valides, key=valides.get)
        if meilleur != 0:
            print(f"     ⚠️ Le décalage {meilleur:+d} h l'emporte — la convention n'est PAS "
                  f"celle attendue.\n        Ne pas raccorder avant d'avoir compris "
                  f"pourquoi.")
        else:
            second = min((h for h in valides if h != 0), key=lambda h: valides[h])
            print(f"     → 0 h gagne, {valides[second] / max(valides[0], 1e-9):.0f}× mieux "
                  f"que {second:+d} h ✓")

        # ── ② La population de stations ─────────────────────────────────────────
        s_lc, s_ee = set(lc["station_id"]), set(ee["station_id"])
        communes = s_lc & s_ee
        print(f"\n  ② stations · {len(communes)} communes · "
              f"{len(s_ee - s_lc)} EEA seule · {len(s_lc - s_ee)} LCSQA seule")
        part = len(communes) / max(len(s_ee), 1)
        print(f"     {part:.1%} des stations EEA se retrouvent dans LCSQA"
              f"{' ✓' if part > 0.95 else '  ⚠️ population différente'}")

        # ── ③ L'accord sur les valeurs, au décalage retenu ─────────────────────
        d = lc.copy()
        d["timestamp_utc"] = d["timestamp_utc"] + pd.Timedelta(hours=meilleur)
        f = ee.merge(d, on=["station_id", "timestamp_utc"], how="inner")
        f = f.dropna(subset=["eea", "lcsqa"])
        if f.empty:
            raise SystemExit(f"{polluant} : aucun couple commun — raccord impossible")
        a = accord(f)
        print(f"\n  ③ accord sur {a['n']:,} couples communs")
        print(f"     biais moyen (LCSQA − EEA) : {a['biais_moyen']:+.4f} µg/m³")
        print(f"     écart absolu médian       : {a['ecart_absolu_median']:.4f} µg/m³")
        print(f"     écart absolu p95          : {a['ecart_absolu_p95']:.4f} µg/m³")
        print(f"     corrélation               : {a['correlation']:.6f}")
        print(f"     part strictement identiques : {a['part_identiques']:.1%}")

        # ── ④ La stabilité mois par mois ───────────────────────────────────────
        f["mois"] = f["timestamp_utc"].dt.strftime("%Y-%m")
        par_mois = f.groupby("mois").apply(
            lambda g: pd.Series({"n": len(g),
                                 "biais": float((g["lcsqa"] - g["eea"]).mean()),
                                 "ecart_median": float(
                                     np.median(np.abs(g["lcsqa"] - g["eea"])))}),
            include_groups=False)
        print(f"\n  ④ stabilité — l'accord doit être le MÊME tous les mois")
        print(par_mois.round(4).to_string())
        derive = float(par_mois["ecart_median"].max() - par_mois["ecart_median"].min())
        print(f"     amplitude de l'écart médian entre mois : {derive:.4f} µg/m³"
              f"{' ✓' if derive < 0.5 else '  ⚠️ accord instable dans le temps'}")

        lignes.append({"polluant": polluant, "decalage_h": meilleur,
                       "n_stations_communes": len(communes),
                       "part_stations_eea_retrouvees": part,
                       "derive_mensuelle": derive, **a})

    t = pd.DataFrame(lignes)
    sortie = RACINE / "reports/concordance_eea_lcsqa.csv"
    t.to_csv(sortie, index=False)

    # ── Le verdict, selon les critères écrits AVANT la mesure ──────────────────
    print(f"\n{'═' * 78}\nVERDICT — critères posés avant de regarder les chiffres\n{'═' * 78}")
    for _, r in t.iterrows():
        ok = (r["decalage_h"] == 0 and r["ecart_absolu_median"] < 0.5
              and r["part_stations_eea_retrouvees"] > 0.95 and r["derive_mensuelle"] < 0.5)
        motifs = []
        if r["decalage_h"] != 0:
            motifs.append(f"décalage {r['decalage_h']:+.0f} h")
        if r["ecart_absolu_median"] >= 0.5:
            motifs.append(f"écart médian {r['ecart_absolu_median']:.2f}")
        if r["part_stations_eea_retrouvees"] <= 0.95:
            motifs.append(f"stations {r['part_stations_eea_retrouvees']:.0%}")
        if r["derive_mensuelle"] >= 0.5:
            motifs.append(f"dérive {r['derive_mensuelle']:.2f}")
        print(f"  {r['polluant']:5s} {'RACCORD LÉGITIME' if ok else 'NE PAS RACCORDER'}"
              f"{'' if ok else ' — ' + ', '.join(motifs)}")

    print(f"\n⚠️ Un corpus de 18 mois **juste** vaut mieux qu'un corpus de 36 mois **faussé**.")
    print(f"   Une rupture introduite par le raccord serait lue par le double aveugle comme")
    print(f"   une non-stationnarité de l'atmosphère — et attribuée à la mauvaise cause.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.0f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluants", default="O3,NO2,PM25")
    n = a.parse_args()
    raise SystemExit(main([p.strip() for p in n.polluants.split(",") if p.strip()]))
