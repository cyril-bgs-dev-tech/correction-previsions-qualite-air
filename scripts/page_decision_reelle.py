#!/usr/bin/env python3
"""Les données de la page 06 — les épisodes **réellement déclenchés**, et le cadrage partenaires.

Pourquoi cette page existe
----------------------------
Tout le reste du dossier compte des « épisodes » au sens **journée-station en classe ATMO
≥ 3** — des milliers d'occurrences, une métrique que le projet a lui-même définie. Ce n'est
pas ce qu'une AASQA appelle un épisode : un déclenchement réel est une **zone-jour sous
procédure préfectorale**, et il y en a **52 en quatorze mois** en Occitanie.

C'est la seule mesure du dossier qui confronte le modèle à la **décision réelle** plutôt
qu'à une métrique choisie par lui. C'est aussi la seule où nos chiffres sont mauvais. La
sortir soi-même, avant qu'on la demande, est la seule posture tenable.

Ce que la page ne fait pas
----------------------------
Elle ne compare pas l'ozone au seuil réglementaire. La procédure française se déclenche sur
le **maximum horaire à 180 µg/m³**, que ce projet ne prédit pas — sa grandeur est le maximum
journalier de la moyenne glissante 8 h. L'ozone est donc rapporté sur la borne de classe 3
(120 µg/m³), **à titre indicatif**, et c'est écrit sur la page.

⚠️ L'échéance est **J0** (`production_*_h1`), pas J+1 : c'est le jour même. Les tranches
1-24 h d'une sortie CAMS de 00 UTC couvrent le jour de la sortie — le projet a déjà appelé
« J+1 » du J0 pendant des semaines.

Usage  : python3 scripts/page_decision_reelle.py
Sortie : reports/figures/p6_donnees.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

SOURCE = RACINE / "reports/episodes_reels_occitanie.csv"
EPISODES = RACINE / "data/raw/atmo_occitanie/episodes_occitanie.parquet"
HORIZON = 1  # ⚠️ tranche 1-24 h = J0, le jour même

ATTENDUES = ["polluant", "systeme", "seuil", "episodes", "attrapes", "rates",
             "fausses", "rappel_pct", "precision_pct", "zones_jours"]

# L'ordre d'affichage est déclaré ici : l'observation d'abord, parce qu'elle est le
# **plafond** et non un concurrent — ce qu'un système parfait, connaissant la mesure,
# aurait annoncé avec ce seuil et ces stations.
ORDRE = ["observation", "CAMS brut", "chaîne AASQA", "notre modèle"]

# La signature en trois mots. Elle diffère de celle des pages 04 et 05 sur les TROIS
# termes — région et non France, procédures préfectorales et non bandes ATMO, J0 et non
# J+1 — et c'est précisément pourquoi elle doit être écrite sur la page. Un lecteur qui
# reporte le « 2 sur 33 » d'ici sur le tableau de la page 04 compare deux mesures qui
# n'ont aucun terme en commun.
SIGNATURE = {"perimetre": "Occitanie — 9 départements portant au moins une station",
             "epreuve": "procédures préfectorales réelles · seuil physique fixe, sans réglage",
             "echeance": "J0 — tranche 1-24 h d'une sortie 00 UTC"}


def inevaluables() -> dict:
    """Les épisodes qu'on ne peut pas évaluer — nommés, jamais comptés comme ratés.

    Un épisode perdu en silence sort du dénominateur et **flatte le rappel**. Deux causes
    distinctes, mesurées séparément :
      * le département ne porte **aucune station** dans le réseau national extrait ;
      * il en porte une, mais **aucune prédiction** pour ce polluant.
    """
    # ⚠️ La normalisation (accents, libellés de polluants) vient du script d'origine et
    # n'est pas réécrite ici : deux normalisations divergentes produiraient deux vérités.
    from episodes_reels import POLLUANT_DE, sans_accent, stations_par_departement  # noqa: PLC0415
    from pages_soutenance import charger  # noqa: PLC0415

    ep = pd.read_parquet(EPISODES)
    ep["dep"] = ep["lib_zone"].map(sans_accent)
    ep["polluant"] = ep["lib_pol"].map(POLLUANT_DE)
    ep = ep.dropna(subset=["polluant"])
    par_dep = stations_par_departement()
    sans_station = sorted(set(ep["dep"]) - set(par_dep))
    bloc1 = ep[ep["dep"].isin(sans_station)]

    appartenance = {s: dep for dep, ss in par_dep.items() for s in ss}
    reste = ep[~ep["dep"].isin(sans_station)]
    bloc2 = []
    for p in sorted(reste["polluant"].unique()):
        d = charger(p, HORIZON)
        if d is None:
            continue
        deps_predits = set(d["station_id"].map(appartenance).dropna())
        muets = sorted(set(reste.loc[reste["polluant"] == p, "dep"]) - deps_predits)
        for m in muets:
            n = int(((reste["dep"] == m) & (reste["polluant"] == p)).sum())
            bloc2.append({"dep": m, "polluant": p, "n": n})

    return {
        "total_declares": int(len(ep)),
        "par_polluant": {str(k): int(v) for k, v in ep["polluant"].value_counts().items()},
        "sans_station": [{"dep": d, "polluant": str(p), "n": int(n)}
                         for (d, p), n in bloc1.groupby(["dep", "polluant"]).size().items()],
        "sans_prediction": bloc2,
    }


def main() -> int:
    if not SOURCE.exists():
        raise SystemExit(f"{SOURCE.name} absent — lancer d'abord episodes_reels.py")
    t = pd.read_csv(SOURCE)
    manque = [c for c in ATTENDUES if c not in t.columns]
    if manque:
        raise SystemExit(f"colonnes absentes de {SOURCE.name} : {manque}")

    polluants = {}
    for p, g in t.groupby("polluant"):
        vus = list(g["systeme"])
        if set(vus) != set(ORDRE):
            raise SystemExit(f"{p} : systèmes {vus} au lieu de {ORDRE}")
        g = g.set_index("systeme").loc[ORDRE].reset_index()
        polluants[str(p)] = {
            "seuil": float(g["seuil"].iloc[0]),
            "episodes": int(g["episodes"].iloc[0]),
            "zones_jours": int(g["zones_jours"].iloc[0]),
            "systemes": [{"nom": r.systeme, "attrapes": int(r.attrapes),
                          "rates": int(r.rates), "fausses": int(r.fausses),
                          "rappel": round(float(r.rappel_pct), 1),
                          "precision": round(float(r.precision_pct), 1)}
                         for r in g.itertuples()],
        }

    st = (RACINE / f"data/processed/predictions/production_PM10_h{HORIZON}.parquet").stat()
    sortie = {"horizon": HORIZON, "signature": SIGNATURE,
              "polluants": polluants, "inevaluables": inevaluables(),
              # Clé distincte de « empreinte » : cette page ne lit pas les mêmes artefacts
              # que les pages 04 et 05, et le contrôle de cohérence ne doit pas les confondre.
              "empreinte_production": {"octets": st.st_size, "horodatage": int(st.st_mtime)}}

    for p, b in sortie["polluants"].items():
        obs = [s for s in b["systemes"] if s["nom"] == "observation"]
        if not obs:
            raise SystemExit(f"{p} : ligne « observation » absente — c'est le plafond")
        if any(s["attrapes"] > obs[0]["attrapes"] for s in b["systemes"]):
            raise SystemExit(f"{p} : un système dépasse le plafond de l'observation")

    f = RACINE / "reports/figures/p6_donnees.json"
    f.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")),
                 encoding="utf-8")
    inv = sortie["inevaluables"]
    print(f"{inv['total_declares']} épisodes déclarés · "
          + " · ".join(f"{k} {v}" for k, v in inv["par_polluant"].items()))
    print(f"  inévaluables : {sum(x['n'] for x in inv['sans_station'])} sans station "
          f"({', '.join(sorted({x['dep'] for x in inv['sans_station']}))}) · "
          f"{sum(x['n'] for x in inv['sans_prediction'])} sans prédiction "
          f"({', '.join(sorted({x['dep'] for x in inv['sans_prediction']}))})")
    for p, b in sortie["polluants"].items():
        print(f"  {p:5s} {b['episodes']} épisodes évaluables · "
              + " · ".join(f"{s['nom']} {s['attrapes']}" for s in b["systemes"]))
    print(f"Écrit : {f.relative_to(RACINE)} ({f.stat().st_size / 1024:.1f} ko)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
