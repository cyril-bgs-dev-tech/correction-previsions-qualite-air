#!/usr/bin/env python3
"""Aurions-nous annoncé les épisodes **réellement déclenchés** en Occitanie ?

Pourquoi ce script change la nature de l'évaluation
-----------------------------------------------------
Tout le dossier compte des « épisodes » au sens d'une **journée-station** en classe ATMO
≥ 3 — des milliers d'occurrences. Ce n'est **pas** ce qu'Atmo Occitanie appelle un épisode :
un déclenchement réel est une **zone-jour** faisant l'objet d'une procédure préfectorale,
et il y en a **52 en quatorze mois**.

Les deux comptes sont cohérents chacun dans son ordre, mais les confondre serait faux. Ce
script évalue sur le **second** : la vérité terrain publiée par l'AASQA elle-même
(`data/raw/atmo_occitanie/episodes_occitanie.parquet`, service ArcGIS `epipol_occitanie`).

Répartition mesurée : **PM10 40 · ozone 12 · NO₂ 0**. Le NO₂, où notre modèle gagne le plus
(+44 %), **ne déclenche jamais** de procédure en Occitanie.

Le protocole
--------------
Une zone est un **département**. Pour chaque (département, jour) déclaré en épisode, on
demande : au moins une station du département dépassait-elle le seuil de procédure, selon
chaque système ?

* **PM10** — seuil d'information **50 µg/m³ en moyenne journalière**. C'est exactement la
  grandeur que le projet prédit, et la borne de la classe ATMO « mauvais ».
* **O₃** — la procédure française se déclenche sur le **maximum horaire à 180 µg/m³**, que
  nous ne prédisons pas : notre grandeur est le maximum journalier de la moyenne 8 h. Le
  projet a déjà mesuré qu'il y est **aveugle** (3 détections sur 32). L'ozone est donc
  rapporté à titre indicatif, sur la borne de classe 3 (120 µg/m³), et **la comparaison
  n'est pas au seuil réglementaire** — c'est dit, pas contourné.

⚠️ Les fausses alertes se comptent sur les **mêmes zones-jours** : tout couple
(département, jour) de la période où aucun épisode n'a été déclaré.

Usage  : python3 scripts/episodes_reels.py
Sortie : reports/episodes_reels_occitanie.csv
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from appariement import presence  # noqa: E402
from pages_soutenance import charger, classe, recaler  # noqa: E402

EPISODES = RACINE / "data/raw/atmo_occitanie/episodes_occitanie.parquet"
# Seuil de déclenchement retenu par polluant, et sa nature.
SEUILS = {"PM10": (50.0, "information, moyenne journalière — seuil réglementaire"),
          "O3": (120.0, "borne de classe « mauvais » — PAS le seuil réglementaire de "
                        "180 µg/m³ en maximum horaire, que nous ne prédisons pas")}
POLLUANT_DE = {"Particules PM10": "PM10", "Ozone": "O3"}


def sans_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s))
                   if not unicodedata.combining(c)).upper().replace("-", " ").strip()


def stations_par_departement() -> dict[str, set]:
    """Rattache les stations aux départements par point-dans-polygone, jamais par nom."""
    from matplotlib.path import Path as Chemin  # noqa: PLC0415

    from pages_regions import SOURCE_DEPARTEMENTS, charger_territoires  # noqa: PLC0415

    deps = charger_territoires(SOURCE_DEPARTEMENTS, 900.0)
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "x_l93", "y_l93"]).dropna()
    xy = st[["x_l93", "y_l93"]].to_numpy()
    out: dict[str, set] = {}
    for d in deps:
        dedans = np.zeros(len(st), bool)
        for c in d["chemins_fins"]:
            dedans |= Chemin(c).contains_points(xy)
        if dedans.any():
            out[sans_accent(d["nom"])] = set(st["station_id"].to_numpy()[dedans])
    return out


def main(horizon: int) -> int:
    if not EPISODES.exists():
        raise SystemExit(f"absent : {EPISODES.relative_to(RACINE)}")
    ep = pd.read_parquet(EPISODES)
    ep["jour"] = pd.to_datetime(ep["date_ech"]).dt.normalize()
    ep["dep"] = ep["lib_zone"].map(sans_accent)
    ep["polluant"] = ep["lib_pol"].map(POLLUANT_DE)
    ep = ep.dropna(subset=["polluant"])

    par_dep = stations_par_departement()
    # **Nommer ce qui n'est pas évaluable**, jamais l'ignorer : une zone perdue en silence
    # enlève des épisodes du dénominateur et flatte le rappel.
    #
    # ⚠️ Mesuré le 04/08 : **AUDE et LOT ne portent AUCUNE station** dans
    # `stations.parquet` — ni Carcassonne, ni Narbonne, ni Cahors. Ce n'est pas un défaut de
    # rattachement, c'est une lacune du réseau national extrait (476 stations actives), qui
    # laisse deux départements d'Occitanie sans aucun point de mesure. Les épisodes qui s'y
    # produisent sont **inévaluables**, et il faut le dire au lieu de les compter comme
    # ratés — ce qui accuserait le modèle d'un trou de données.
    inconnus = sorted(set(ep["dep"]) - set(par_dep))
    if inconnus:
        perdus = ep[ep["dep"].isin(inconnus)]
        print(f"⚠️ {len(perdus)} épisode(s) sur {len(ep)} INÉVALUABLES — aucune station "
              f"dans : {', '.join(inconnus)}", flush=True)
        print("   " + perdus.groupby(["dep", "polluant"]).size().to_string().replace(
            "\n", "\n   "), flush=True)
        ep = ep[~ep["dep"].isin(inconnus)]

    lignes = []
    for polluant, (seuil, nature) in SEUILS.items():
        vrais = ep[ep["polluant"] == polluant]
        if vrais.empty:
            continue
        d = charger(polluant, horizon)
        if d is None:
            print(f"  {polluant} : aucune prédiction", flush=True)
            continue
        d = recaler(d, ["nous", "aasqa"])
        d["jour"] = pd.to_datetime(d["jour"]).dt.normalize()
        # ne garder que les stations d'Occitanie, département par département
        appartenance = {s: dep for dep, ss in par_dep.items() for s in ss}
        d["dep"] = d["station_id"].map(appartenance)
        d = d[d["dep"].isin(set(ep["dep"]))]
        if d.empty:
            continue

        # ⚠️ **Second contrôle d'inévaluabilité, par polluant.** Le contrôle ci-dessus teste
        # « ce département porte-t-il UNE station » ; il ne dit rien de « porte-t-il des
        # prédictions POUR CE POLLUANT ». L'ARIÈGE a une station dans `stations.parquet` —
        # elle passe donc le premier filtre — et **aucune station prédite**, pour aucun
        # polluant. Ses **3 épisodes PM10** disparaissaient du dénominateur en silence :
        # rappel publié 2/33 = 6,1 % au lieu de 2/36 = 5,6 %. Le compte manquant gonfle
        # toujours le rappel. Trouvé au contrôle du 05/08 ; c'est `CLAUDE.md` § 4 —
        # l'attendu venait d'ailleurs que de la demande.
        muets = sorted(set(vrais["dep"]) - set(d["dep"]))
        if muets:
            perdus = vrais[vrais["dep"].isin(muets)]
            print(f"\n⚠️ {polluant} : {len(perdus)} épisode(s) INÉVALUABLES — départements "
                  f"sans aucune station prédite : {', '.join(muets)}", flush=True)
            vrais = vrais[~vrais["dep"].isin(muets)]
            if vrais.empty:
                continue

        systemes = {"CAMS brut": "cams", "chaîne AASQA": "aasqa_r",
                    "notre modèle": "nous_r"}
        # Le **maximum par (département, jour)** : une procédure se déclenche dès qu'un
        # point du territoire dépasse, jamais sur une moyenne spatiale.
        g = d.groupby(["dep", "jour"]).agg(
            obs=("valeur", "max"), **{k: (c, "max") for k, c in systemes.items()}
        ).reset_index()
        g["reel"] = presence(g, vrais, ("dep", "jour"))

        n_couvert = int(g["reel"].sum())
        # Le dénominateur affiché est **le nombre d'épisodes évaluables**, et l'on exige
        # qu'il n'en manque aucun : après le filtre par polluant ci-dessus, tout écart
        # restant est un défaut d'appariement, pas une lacune de réseau.
        if n_couvert != len(vrais):
            raise SystemExit(
                f"{polluant} : {len(vrais)} épisodes évaluables mais {n_couvert} retrouvés "
                f"dans la grille — appariement (département, jour) à vérifier")
        print(f"\n{'═' * 84}\n{polluant} · {len(vrais)} épisodes évaluables, "
              f"{n_couvert} retrouvés dans nos zones-jours prédites\n"
              f"seuil {seuil:.0f} µg/m³ — {nature}\n{'═' * 84}")
        print(f"  {len(g):,} zones-jours évaluées sur {g['dep'].nunique()} départements")
        print(f"\n  {'système':16s} {'annoncés':>9s} {'ratés':>7s} {'fausses':>9s} "
              f"{'rappel':>8s} {'précision':>10s}")
        # ⚠️ L'agrégation ci-dessus nomme ses colonnes par le **libellé** du système
        # (« CAMS brut »), pas par le nom de la colonne source (« cams ») : c'est le libellé
        # qu'il faut relire ici.
        for nom in ["observation"] + list(systemes):
            vu = g["obs" if nom == "observation" else nom].to_numpy() >= seuil
            att = int((vu & g["reel"]).sum())
            rate = int((~vu & g["reel"]).sum())
            faux = int((vu & ~g["reel"]).sum())
            rap = att / max(n_couvert, 1)
            pre = att / max(att + faux, 1)
            print(f"  {nom:16s} {att:9d} {rate:7d} {faux:9d} {100 * rap:7.1f}% "
                  f"{100 * pre:9.1f}%")
            lignes.append({"polluant": polluant, "systeme": nom, "seuil": seuil,
                           "episodes": n_couvert, "attrapes": att, "rates": rate,
                           "fausses": faux, "rappel_pct": 100 * rap,
                           "precision_pct": 100 * pre, "zones_jours": len(g)})
        print(f"\n  La ligne « observation » est le plafond : ce qu'un système parfait,")
        print(f"  connaissant la mesure, aurait annoncé avec ce seuil et ces stations.")

    if not lignes:
        raise SystemExit("rien à évaluer")
    t = pd.DataFrame(lignes)
    f = RACINE / "reports/episodes_reels_occitanie.csv"
    t.to_csv(f, index=False)
    print(f"\n⚠️ Un épisode réel est une **zone-jour sous procédure préfectorale**, pas une")
    print(f"   journée-station en classe ≥ 3. Les deux comptes du dossier ne se comparent")
    print(f"   pas : celui-ci porte sur 52 événements, l'autre sur des milliers.")
    print(f"\nÉcrit : {f.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--horizon", type=int, default=1)
    n = a.parse_args()
    raise SystemExit(main(n.horizon))
