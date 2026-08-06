#!/usr/bin/env python3
"""Les données de la page 05 — l'erreur de **classe** ATMO, et non l'erreur en µg/m³.

La question, qui n'est pas celle de la RMSE
---------------------------------------------
Un service ne publie pas une concentration, il publie une **bande** : bon, moyen, dégradé,
mauvais, très mauvais. Deux systèmes de RMSE identique peuvent se tromper très
différemment **de bande**, et c'est la bande qui déclenche une communication. On mesure
donc ici la **distance signée** entre la classe prédite et la classe observée :

    distance = classe(prédiction) − classe(observation)      ∈ [−4, +4]

* **négative — sous-classée** : l'épisode est annoncé plus bénin qu'il n'est. C'est le
  manqué, la faute qui coûte.
* **zéro** : bande exacte.
* **positive — sur-classée** : fausse alerte. Coûteuse aussi, mais pas de la même façon.

Les cinq systèmes comparés, et pourquoi le cinquième existe
--------------------------------------------------------------
| | ce que c'est |
|---|---|
| **CAMS brut** | l'ensemble européen — la référence |
| **AASQA réglée** | leur famille de méthode, dans son meilleur réglage |
| **tête A** | notre modèle à l'optimum quadratique — la RMSE la plus basse |
| **tête B** | la **même sortie**, recalibrée en amplitude (cartographie de quantiles) |
| **AASQA + recalibrage** | leur méthode, avec **exactement le même** traitement post-hoc |

⚠️ Le cinquième n'est pas une coquetterie. Sans lui, l'écart entre « tête B » et « AASQA
réglée » mélangerait deux choses : ce que vaut notre modèle, et ce que vaut le fait d'avoir
recalibré. Comparer une méthode traitée à une méthode non traitée, c'est fausser la
comparaison en sa faveur — ce que ce projet s'interdit explicitement.

La recalibration, et pourquoi elle ne fuit pas
------------------------------------------------
`F_obs⁻¹(F_préd(ŷ))` — la prédiction est transportée sur la loi des observations. Le
**rang est préservé exactement**, donc rien ne change à budget d'alerte constant ; seuls
les franchissements de bande bougent. Les deux lois sont estimées **sur les mois
antérieurs uniquement** : sans fuite, et c'est ce qu'on ferait en déploiement.

Le premier mois n'a pas d'historique. Il est **retiré pour les cinq systèmes à la fois**,
jamais pour le seul qui en a besoin : cinq séries qui ne portent pas sur les mêmes lignes
ne se comparent pas.

Le § 15 — la persistance, et pourquoi elle ne nous appartient pas
-------------------------------------------------------------------
La dernière section de la page ne parle plus de bandes mais de **règle de décision**.
Exiger un dépassement prédit **deux jours de suite** retire un tiers des fausses alertes
sans perdre un seul épisode. C'est le seul gain sec du dossier.

⚠️ **Et il profite à tout le monde.** L'observation elle-même passe de 412 à 254 fausses
alertes, la chaîne AASQA de 446 à 310. Présenter ce −34 % comme un mérite de notre modèle
serait faux : c'est un mérite de la **règle**, que n'importe quel système peut adopter. Le
script lit donc les **quatre** systèmes et la page les affiche tous — sans quoi la première
question du jury démonte la diapositive.

⚠️ Ce bloc ne porte **ni le même périmètre, ni la même épreuve, ni la même échéance** que
le reste de la page : Occitanie et non France, épisodes préfectoraux et non bandes ATMO,
J0 et non J+1. Il porte donc **sa propre signature**, et c'est tout l'objet de la règle des
trois mots.

Usage  : python3 scripts/page_seuils_classes.py
Sortie : reports/figures/p5_donnees.json + reports/seuils_classes.csv
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
from recalibrer_amplitude import cartographie_quantiles  # noqa: E402
from tableau_comparatif import BANDES, NOM_BANDE, classe  # noqa: E402

HORIZON = 2
N_MIN_ANNEE = 500
DISTANCES = list(range(-4, 5))

# ⚠️ Les PM10 se lisent dans la variante LONGUE (31 mois, chaîne ancrée sur CAMS) —
# la même que la page 04. Deux pages qui liraient deux variantes du même polluant
# seraient chacune juste et l'ensemble incohérent ; la garde d'injection le refuse.
POLLUANTS = {"O3": ("O₃", ""), "NO2": ("NO₂", ""),
             "PM10": ("PM10", "_sansmembres"), "PM25": ("PM2,5", "")}
SYSTEMES = [
    ("cams",   "CAMS brut",             "l'ensemble européen brut"),
    ("aasqa",  "AASQA réglée",          "biais récent interpolé, réglage optimisé"),
    ("aasqaB", "AASQA + recalibrage",   "leur méthode, même traitement post-hoc"),
    ("teteA",  "Tête A · RMSE",         "notre optimum quadratique"),
    ("teteB",  "Tête B · alerte",       "la même sortie, amplitude recalibrée"),
]

SIGNATURE = {"perimetre": "PARTOUT — aucune observation passée de la station",
             "epreuve": "double aveugle — station ET mois cachés",
             "echeance": "J+1 — tranche 25-48 h d'une sortie 00 UTC"}

# ── § 15 · la persistance ────────────────────────────────────────────────────
# La configuration est nommée en toutes lettres et FILTRÉE sur ces valeurs : une ligne
# choisie par son rang dans le CSV changerait de sens au prochain ajout de règle.
PERSIST = RACINE / "reports/agregation_zone_occitanie.csv"
PERSIST_CONF = {"polluant": "O3", "seuil": 120.0, "regle": "max (existant)",
                "min_stations": 1}
PERSIST_ORDRE = ["observation", "notre modèle", "chaîne AASQA", "CAMS brut"]
PERSIST_SIGNATURE = {
    "perimetre": "Occitanie — 9 départements portant au moins une station",
    "epreuve": "épisodes préfectoraux réellement déclarés · seuil 120 µg/m³",
    "echeance": "J0 — tranche 1-24 h d'une sortie 00 UTC"}


def persistance() -> dict:
    """Ce que la règle de persistance change, pour les QUATRE systèmes à la fois.

    Le gain de notre modèle n'a de sens qu'à côté de celui des trois autres : la
    persistance est une propriété de la **règle de décision**, pas du modèle. La lire pour
    nous seuls produirait un chiffre juste et une affirmation fausse.
    """
    if not PERSIST.exists():
        raise SystemExit(f"{PERSIST.name} absent — lancer d'abord agregation_zone.py")
    t = pd.read_csv(PERSIST)
    for col, val in PERSIST_CONF.items():
        t = t[t[col] == val]
    attendu = 2 * len(PERSIST_ORDRE)
    if len(t) != attendu:
        raise SystemExit(f"persistance : {len(t)} lignes pour la configuration "
                         f"{PERSIST_CONF}, {attendu} attendues "
                         f"({len(PERSIST_ORDRE)} systèmes × 2 états)")
    systemes = []
    for nom in PERSIST_ORDRE:
        g = t[t["systeme"] == nom]
        if len(g) != 2:
            raise SystemExit(f"persistance : {len(g)} ligne(s) pour « {nom} »")
        sans = g[~g["persistance"].astype(bool)].iloc[0]
        avec = g[g["persistance"].astype(bool)].iloc[0]
        systemes.append({
            "nom": nom,
            "episodes": int(sans["n_episodes"]),
            "zones_jours": int(sans["n_zones_jours"]),
            "sans": {"attrapes": int(sans["attrapes"]), "fausses": int(sans["fausses"]),
                     "rappel": round(float(sans["rappel_pct"]), 1),
                     "precision": round(float(sans["precision_pct"]), 2)},
            "avec": {"attrapes": int(avec["attrapes"]), "fausses": int(avec["fausses"]),
                     "rappel": round(float(avec["rappel_pct"]), 1),
                     "precision": round(float(avec["precision_pct"]), 2)},
            # Le seul chiffre qui décide : le rappel a-t-il bougé ? Si oui, la règle
            # n'est pas gratuite pour ce système, et l'écrire « gratuit » serait faux.
            "gratuite": bool(int(sans["attrapes"]) == int(avec["attrapes"])),
            "delta_fausses_pct": round(
                100 * (int(avec["fausses"]) - int(sans["fausses"]))
                / int(sans["fausses"]), 1),
        })
    print("\n── § 15 · persistance · " + " · ".join(
        f"{k}={v}" for k, v in PERSIST_CONF.items()))
    for s in systemes:
        print(f"   {s['nom']:14s} {s['sans']['attrapes']}/{s['episodes']} épisodes · "
              f"fausses {s['sans']['fausses']:>4} → {s['avec']['fausses']:>4} "
              f"({s['delta_fausses_pct']:+.1f} %) · rappel "
              f"{s['sans']['rappel']:.1f} → {s['avec']['rappel']:.1f} % "
              f"{'· GRATUITE' if s['gratuite'] else '· COÛTE un épisode'}")
    return {"conf": {k: str(v) for k, v in PERSIST_CONF.items()},
            "signature": PERSIST_SIGNATURE, "systemes": systemes}


def colonne(sys_: pd.DataFrame, motif: str, p: str) -> str:
    c = sys_[sys_["systeme"].str.contains(motif, regex=False)]
    if len(c) != 1:
        raise SystemExit(f"{p} : {len(c)} correspondance(s) pour « {motif} »")
    return str(c.iloc[0]["code"])


def profil(o: np.ndarray, x: np.ndarray, p: str) -> dict:
    """Distribution de la distance de classe, et les deux chiffres qui décident."""
    d = classe(x, p).astype(int) - classe(o, p).astype(int)
    n = len(d)
    part = {str(k): round(100 * float(np.mean(d == k)), 2) for k in DISTANCES}
    crit = classe(o, p) >= 3          # bandes MAUVAIS et TRÈS MAUVAIS
    return {
        "part": part,
        "exact": round(100 * float(np.mean(d == 0)), 1),
        "sous": round(100 * float(np.mean(d < 0)), 1),
        "sur": round(100 * float(np.mean(d > 0)), 1),
        "dist_moy": round(float(np.mean(np.abs(d))), 3),
        # Le chiffre opérationnel : parmi les journées réellement mauvaises, combien
        # sont annoncées plus bénignes qu'elles ne sont ?
        "n_crit": int(crit.sum()),
        "crit_manquees": (None if crit.sum() == 0
                          else round(100 * float(np.mean(d[crit] < 0)), 1)),
    }


def main() -> int:
    sortie: dict = {"horizon": HORIZON, "distances": DISTANCES,
                    "signature": SIGNATURE, "persistance": persistance(),
                    "systemes": [{"c": c, "n": n, "d": d} for c, n, d in SYSTEMES],
                    "polluants": {}}
    lignes: list[dict] = []

    for p, (nom, suffixe) in POLLUANTS.items():
        # Chaque variante lit SA table de systèmes — la correspondance codée en dur a
        # disparu avec la livraison de `systemes_PM10_h2_sansmembres.csv` le 06/08.
        sys_ = pd.read_csv(
            RACINE / f"data/processed/predictions/systemes_{p}_h{HORIZON}{suffixe}.csv")
        d = pd.read_parquet(RACINE /
            f"data/processed/predictions/comparatif_{p}_h{HORIZON}{suffixe}.parquet")
        c_ref = colonne(sys_, "CAMS brut", p)
        c_aas = colonne(sys_, "OPTIMISÉ ici", p)
        c_nous = colonne(sys_, "notre modèle", p)
        d = d.dropna(subset=["valeur", c_ref, c_aas, c_nous]).copy()

        # ── Recalibrage : mois antérieurs seulement, pour NOUS et pour EUX ────────
        d["teteB"] = np.nan
        d["aasqaB"] = np.nan
        mois = sorted(d["mois"].unique())
        sans_hist = []
        for m in mois:
            hist, cur = d[d["mois"] < m], d["mois"] == m
            if len(hist) < 500:
                sans_hist.append(m)
                continue
            for src, dst in ((c_nous, "teteB"), (c_aas, "aasqaB")):
                d.loc[cur, dst] = cartographie_quantiles(
                    hist[src].to_numpy(), hist["valeur"].to_numpy(),
                    d.loc[cur, src].to_numpy())

        avant = len(d)
        d = d.dropna(subset=["teteB", "aasqaB"])
        print(f"\n── {p} · {avant:,} → {len(d):,} lignes "
              f"({len(sans_hist)} mois sans historique, retirés pour les CINQ systèmes : "
              f"{', '.join(sans_hist) or 'aucun'})")

        col = {"cams": c_ref, "aasqa": c_aas, "aasqaB": "aasqaB",
               "teteA": c_nous, "teteB": "teteB"}
        d["an"] = pd.to_datetime(d["jour"]).dt.year.astype(str)

        annees = []
        for an, g in list(d.groupby("an")) + [("toutes", d)]:
            if an != "toutes" and len(g) < N_MIN_ANNEE:
                print(f"   ✗ {an} écartée : {len(g)} jours-station")
                continue
            o = g["valeur"].to_numpy()
            prof = {k: profil(o, g[c].to_numpy(), p) for k, c in col.items()}
            mois_an = sorted(g["mois"].unique())
            # Même remarque qu'en page 04 : un tiers du réseau par mois est le
            # protocole, pas une lacune. C'est le nombre de MOIS qui qualifie l'année.
            annees.append({"an": an, "n": int(len(g)), "ns": int(g.station_id.nunique()),
                           "n_mois": len(mois_an), "mois": [mois_an[0], mois_an[-1]],
                           "faible": bool(an != "toutes"
                                          and (len(mois_an) < 6 or len(g) < 5_000)),
                           "n_crit": prof["cams"]["n_crit"], "sys": prof})
            for k, v in prof.items():
                lignes.append({"polluant": p, "annee": an, "systeme": k, "n": len(g),
                               "exact_pct": v["exact"], "sous_pct": v["sous"],
                               "sur_pct": v["sur"], "distance_moyenne": v["dist_moy"],
                               "n_critiques": v["n_crit"],
                               "critiques_sous_classees_pct": v["crit_manquees"]})
            print(f"   {an:8s} n={len(g):>7,} · crit {prof['cams']['n_crit']:>5,} · " +
                  " · ".join(f"{k} {prof[k]['exact']:.1f}%" for k in col))

        fr = controle(p, sorted(d["mois"].unique()))
        annoncer(p, fr)
        sortie["polluants"][p] = {
            "nom": nom, "fraicheur": fr, "empreinte": empreinte(p, suffixe=suffixe),
            "bandes": [{"nom": NOM_BANDE[i], "min": float(a),
                        "max": (None if not np.isfinite(b) else float(b))}
                       for i, (a, b) in enumerate(BANDES[p])],
            "annees": annees}

    # ── Exiger nommément ce qu'on croit avoir mesuré ──────────────────────────────
    for p, b in sortie["polluants"].items():
        for a in b["annees"]:
            for k, _, _ in SYSTEMES:
                if k not in a["sys"]:
                    raise SystemExit(f"{p} {a['an']} : système « {k} » absent")
                s = sum(a["sys"][k]["part"].values())
                if abs(s - 100) > 0.5:
                    raise SystemExit(f"{p} {a['an']} {k} : les parts font {s:.2f} %, pas 100")

    f = RACINE / "reports/figures/p5_donnees.json"
    f.write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")),
                 encoding="utf-8")
    t = pd.DataFrame(lignes)
    for c in ("exact_pct", "sous_pct", "critiques_sous_classees_pct"):
        if c not in t:
            raise SystemExit(f"colonne « {c} » absente du rapport")
    t.to_csv(RACINE / "reports/seuils_classes.csv", index=False)
    print(f"\nÉcrit : {f.relative_to(RACINE)} ({f.stat().st_size / 1024:.0f} ko) "
          f"· reports/seuils_classes.csv ({len(t)} lignes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
