#!/usr/bin/env python3
"""Les données de la page 04 — « Contre la chaîne réglementaire, année par année ».

Ce que cette page compare, et ce qu'elle ne compare pas
---------------------------------------------------------
Trois systèmes, **sur exactement les mêmes lignes** (`comparatif_<polluant>_h<n>.parquet`) :

| | ce que c'est |
|---|---|
| **CAMS brut** | l'ensemble européen 0,1° — la référence commune, le dénominateur de tout gain |
| **AASQA réglementaire** | leur *famille* de méthode : biais récent interpolé spatialement, **dans son réglage optimisé** — fenêtre 30 j, portée 200 km, donneurs de même typologie |
| **nous** | résidu appris, toutes familles déployables, **double aveugle** (station ET mois cachés) |

⚠️ **Ce que la ligne AASQA n'est pas.** Leur *méthode* est rejouée, et même réglée au mieux :
sur le NO₂ le réglage la fait passer de +3,5 % à +21,4 %. C'est leur **modèle amont** qui
n'est pas reproductible — le CHIMERE dont nous disposons est le membre de l'ensemble CAMS
(Europe, 0,1°, sans assimilation), quand celui de PREV'AIR est national, plus fin et assimilé.
Leur chaîne réelle ferait donc **mieux** que cette simulation : tout écart affiché est un
**majorant** de notre avance. C'est dit sur la page, pas en note de bas de page.

⚠️ **Sur les PM10 la référence réglementaire est CAMS + krigeage**, pas CHIMERE+MOCAGE : les
membres d'ensemble n'existent pas pour ce polluant. Le libellé le porte.

Trois contrôles, écrits avant d'avoir vu le résultat
------------------------------------------------------
1. **Les systèmes sont désignés par leur libellé, jamais par leur rang** — l'ordre des colonnes
   n'est pas le même d'un polluant à l'autre (PM10 n'a que quatre systèmes). Zéro ou deux
   correspondances sont **toutes deux** des erreurs.
2. **Aucune ligne à prédiction manquante n'entre dans un score.** Le double aveugle laisse des
   trous là où un pli était trop petit ; ils sont comptés et retirés, jamais moyennés.
3. **Aucun gain n'est publié sans son effectif.** Les couples polluant × année sous
   `N_MIN_ANNEE` jours-station sont **écartés** et nommés ; ceux sous `N_FAIBLE` sont marqués.
   Sans cela, les 73 jours-station de PM2,5 2025 produiraient un chiffre spectaculaire et vide.

Usage  : python3 scripts/page_comparaison_annuelle.py
Sortie : reports/figures/p4_donnees.json  (+ reports/comparaison_annuelle.csv, lisible)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from controle_fraicheur import annoncer, controle, empreinte  # noqa: E402

HORIZON = 2  # ⚠️ les échéances 25-48 h d'une sortie 00 UTC : c'est J+1, pas J0
N_MIN_ANNEE = 500     # sous ce seuil, l'année n'est pas publiée du tout
N_FAIBLE = 2_000      # sous ce seuil, elle est publiée mais marquée
N_MIN_STATION = 30    # jours minimum pour qu'une station porte un point sur la carte
N_MIN_JOUR = 20       # stations minimum pour qu'un jour entre dans la bande temporelle

# ⚠️ Les PM10 se publient en DEUX variantes, et la longue vient en premier. Un seuil de
# disponibilité codé en dur (`chimere.notna().mean() > 0.3`) faisait basculer tout le
# corpus vers la fenêtre des membres — 31 mois → 19 — sans que personne ne le décide.
# Les deux tables sont légitimes ; c'est de les cacher l'une l'autre qui ne l'est pas.
# Et la longue est le test le PLUS DUR : le substitut ancré sur CAMS (RMSE 7,20) est un
# adversaire plus fort que la chaîne réelle CHIMERE+MOCAGE (7,63).
POLLUANTS = {
    "O3":     ("O3",   "",             "O₃",   "maximum glissant 8 h", "µg/m³"),
    "NO2":    ("NO2",  "",             "NO₂",  "maximum horaire",      "µg/m³"),
    "PM10":   ("PM10", "_sansmembres", "PM10", "moyenne journalière",  "µg/m³"),
    "PM10c":  ("PM10", "",             "PM10 · chaîne nommée",
               "moyenne journalière",  "µg/m³"),
    "PM25":   ("PM25", "",             "PM2,5", "moyenne journalière", "µg/m³"),
}


def rmse(o: np.ndarray, p: np.ndarray) -> float:
    return float(np.sqrt(np.mean((o - p) ** 2)))


def colonne(sys: pd.DataFrame, motif: str, polluant: str) -> str:
    """Un système se désigne par son libellé. Zéro et deux correspondances sont des erreurs."""
    c = sys[sys["systeme"].str.contains(motif, regex=False)]
    if len(c) != 1:
        raise SystemExit(f"{polluant} : {len(c)} correspondance(s) pour « {motif} » "
                         f"parmi {list(sys['systeme'])}")
    return str(c.iloc[0]["code"])


def main() -> int:
    contours = json.loads((RACINE / "reports/carte_stations_contours.json").read_text())
    carte = pd.read_csv(RACINE / "reports/carte_stations.csv")
    sortie: dict = {"contours": contours, "horizon": HORIZON,
                    "seuils": {"annee": N_MIN_ANNEE, "faible": N_FAIBLE,
                               "station": N_MIN_STATION}, "polluants": {}}
    lignes_csv: list[dict] = []
    ecartees: list[str] = []

    for p, (espece, suffixe, nom, grandeur, unite) in POLLUANTS.items():
        sysf = RACINE / f"data/processed/predictions/systemes_{espece}_h{HORIZON}{suffixe}.csv"
        if not sysf.exists():
            sysf = RACINE / f"data/processed/predictions/systemes_{espece}_h{HORIZON}.csv"
        parq = (RACINE / f"data/processed/predictions/comparatif_{espece}_h{HORIZON}{suffixe}.parquet")
        if not (sysf.exists() and parq.exists()):
            raise SystemExit(f"{p} : artefact manquant — {sysf.name} ou {parq.name}")
        # ⚠️ La variante `sansmembres` n'a PAS de table de systèmes livrée. On ne devine
        # pas une correspondance : celle-ci est **vérifiée sur les données** —
        #   · `sys1` est identique bit à bit à CAMS brut de la variante nommée
        #     (56 238 lignes communes, écart max < 1e-9) ;
        #   · `sys2` (RMSE 7,201) et `sys3` (6,483) reproduisent exactement les +4,2 % et
        #     +13,8 % que cette page affichait quand ce même jeu de 31 mois portait encore
        #     le nom `comparatif_PM10_h2` et sa table à quatre systèmes.
        # À remplacer par `systemes_PM10_h2_sansmembres.csv` dès qu'il sera livré.
        if suffixe and not sysf.name.endswith(f"{suffixe}.csv"):
            sys_ = pd.DataFrame([
                ("sys1", "① CAMS brut — ensemble 6 modèles"),
                ("sys2", "④ CAMS + krigeage — réglages usuels"),
                ("sys3", "⑤ CAMS + krigeage — OPTIMISÉ ici"),
                ("sys4", "⑥ notre modèle — toutes familles"),
            ], columns=["code", "systeme"])
            print(f"   ⚠️ table de systèmes absente pour {nom} — correspondance vérifiée "
                  f"sur les données, à remplacer par un fichier livré")
        else:
            sys_ = pd.read_csv(sysf)
        c_ref = colonne(sys_, "CAMS brut", p)
        c_opt = colonne(sys_, "OPTIMISÉ ici", p)
        c_usu = colonne(sys_, "réglages usuels", p)
        c_nous = colonne(sys_, "notre modèle", p)
        libelle_aasqa = sys_.loc[sys_["code"] == c_opt, "systeme"].iloc[0][2:]

        d = pd.read_parquet(parq)
        avant = len(d)
        d = d.dropna(subset=[c_ref, c_opt, c_usu, c_nous, "valeur"])
        perdues = avant - len(d)
        d["an"] = pd.to_datetime(d["jour"]).dt.year.astype(str)
        print(f"\n── {p} · J+{HORIZON} · {len(d):,} lignes complètes "
              f"({perdues:,} retirées faute de prédiction) · {d.station_id.nunique()} stations")

        # ── Stations : coordonnées, prises dans la table de la carte ──────────────
        cs = carte[carte["polluant"] == espece].drop_duplicates("station_id")
        cs = cs.set_index("station_id")
        connues = [s for s in sorted(d["station_id"].unique()) if s in cs.index]
        inconnues = d["station_id"].nunique() - len(connues)
        if inconnues:
            print(f"   ⚠️ {inconnues} station(s) sans coordonnée — absentes des cartes")
        rang = {s: i for i, s in enumerate(connues)}
        st = {"id": connues,
              "x": [round(float(cs.loc[s, "x_km"]), 1) for s in connues],
              "y": [round(float(cs.loc[s, "y_km"]), 1) for s in connues],
              "nom": [str(cs.loc[s, "nom"]) for s in connues],
              "typo": [str(cs.loc[s, "typologie_zone"]) for s in connues]}

        # ── Par année ────────────────────────────────────────────────────────────
        annees = []
        for an, g in list(d.groupby("an")) + [("toutes", d)]:
            if an != "toutes" and len(g) < N_MIN_ANNEE:
                ecartees.append(f"{p} {an} ({len(g)} jours-station)")
                print(f"   ✗ {an} écartée : {len(g)} jours-station < {N_MIN_ANNEE}")
                continue
            o = g["valeur"].to_numpy()
            r = {k: rmse(o, g[c].to_numpy())
                 for k, c in (("cams", c_ref), ("aasqa", c_opt),
                              ("usuel", c_usu), ("nous", c_nous))}
            gains = {k: 100 * (r["cams"] - v) / r["cams"] for k, v in r.items() if k != "cams"}

            pts = {"i": [], "ga": [], "gn": [], "n": []}
            for s, gs in g.groupby("station_id"):
                if s not in rang or len(gs) < N_MIN_STATION:
                    continue
                os_ = gs["valeur"].to_numpy()
                rc = rmse(os_, gs[c_ref].to_numpy())
                if rc <= 0:
                    continue
                pts["i"].append(rang[s])
                pts["ga"].append(round(100 * (rc - rmse(os_, gs[c_opt].to_numpy())) / rc, 1))
                pts["gn"].append(round(100 * (rc - rmse(os_, gs[c_nous].to_numpy())) / rc, 1))
                pts["n"].append(int(len(gs)))

            # « Effectif faible » ne se mesure pas au seul volume : une année peut aligner
            # 2 600 jours-station sur 86 stations quand l'ensemble en compte 270. C'est la
            # **couverture du réseau** qui manque, pas les lignes.
            ns_an = int(g.station_id.nunique())
            mois_an = sorted(g["mois"].unique())
            # ⚠️ Le protocole évalue chaque mois sur un TIERS disjoint du réseau. Une
            # année d'un seul mois ne peut donc jamais montrer plus d'un tiers des
            # stations : ce n'est pas un trou de données, c'est la construction des
            # plis. Ce qui manque réellement à ces années-là, ce sont des MOIS.
            faible = bool(an != "toutes" and (len(mois_an) < 6 or len(g) < N_FAIBLE * 2.5))
            annees.append({"an": an, "n": int(len(g)), "ns": ns_an,
                           "faible": faible, "n_mois": len(mois_an),
                           "mois": [mois_an[0], mois_an[-1]],
                           "part_reseau": round(100 * ns_an / d.station_id.nunique()),
                           "rmse": {k: round(v, 2) for k, v in r.items()},
                           "gain": {k: round(v, 1) for k, v in gains.items()},
                           "st": pts})
            lignes_csv.append({"polluant": nom, "annee": an, "n": len(g),
                               "n_stations": g.station_id.nunique(),
                               **{f"rmse_{k}": round(v, 3) for k, v in r.items()},
                               **{f"gain_{k}_pct": round(v, 2) for k, v in gains.items()},
                               "n_stations_carte": len(pts["i"])})
            print(f"   {an:8s} n={len(g):>7,} · AASQA {gains['aasqa']:+6.1f} % "
                  f"(usuel {gains['usuel']:+6.1f} %) · nous {gains['nous']:+6.1f} % "
                  f"· {len(pts['i'])} stations cartographiées")

        # ── La bande temporelle : moyenne sur les stations présentes ce jour-là ───
        # Les quatre séries partagent EXACTEMENT les mêmes lignes : leur comparaison est
        # donc exacte à chaque date. Seul le niveau absolu dépend de la composition du
        # jour, d'où le retrait des jours à moins de N_MIN_JOUR stations.
        j = d.groupby("jour").agg(ns=("station_id", "nunique"), obs=("valeur", "mean"),
                                  cams=(c_ref, "mean"), aasqa=(c_opt, "mean"),
                                  nous=(c_nous, "mean")).reset_index()
        retires = int((j["ns"] < N_MIN_JOUR).sum())
        j = j[j["ns"] >= N_MIN_JOUR]
        print(f"   bande temporelle : {len(j)} jours retenus, {retires} écartés "
              f"(< {N_MIN_JOUR} stations)")
        serie = {"j": [x.strftime("%Y-%m-%d") for x in pd.to_datetime(j["jour"])],
                 "ns": j["ns"].astype(int).tolist(),
                 **{k: [round(float(v), 2) for v in j[k]]
                    for k in ("obs", "cams", "aasqa", "nous")}}

        # ⚠️ L'artefact n'est pas son propre juge : on compare son corpus à ce que les
        # sources permettraient aujourd'hui, et le manque part DANS LA PAGE.
        fr = controle(espece, sorted(d["mois"].unique()))
        annoncer(nom, fr)

        sortie["polluants"][p] = {"nom": nom, "grandeur": grandeur, "unite": unite,
                                  "aasqa": libelle_aasqa, "stations": st,
                                  "annees": annees, "serie": serie, "fraicheur": fr,
                                  "empreinte": empreinte(espece, suffixe=suffixe),
                                  "variante": suffixe or "chaine_nommee"}

    # ── On exige nommément ce qu'on croit avoir mesuré, avant d'écrire ────────────
    for p, b in sortie["polluants"].items():
        if not b["annees"]:
            raise SystemExit(f"{p} : aucune année retenue")
        for a in b["annees"]:
            for k in ("aasqa", "nous", "usuel"):
                if k not in a["gain"] or not np.isfinite(a["gain"][k]):
                    raise SystemExit(f"{p} {a['an']} : gain « {k} » absent ou non fini")
        if not b["serie"]["j"]:
            raise SystemExit(f"{p} : bande temporelle vide")

    f = RACINE / "reports/figures/p4_donnees.json"
    f.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")),
                 encoding="utf-8")
    t = pd.DataFrame(lignes_csv)
    for c in ("gain_aasqa_pct", "gain_nous_pct", "n"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")
    t.to_csv(RACINE / "reports/comparaison_annuelle.csv", index=False)
    print(f"\nÉcrit : {f.relative_to(RACINE)} ({f.stat().st_size / 1024:.0f} ko)"
          f" · reports/comparaison_annuelle.csv ({len(t)} lignes)")
    if ecartees:
        print("Années écartées faute d'effectif : " + " · ".join(ecartees))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
