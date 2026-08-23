#!/usr/bin/env python3
"""Les descripteurs de site portent un NIVEAU à chaque échelle, jamais la FORME du profil.

La question
-------------
`geo_features_metropole.parquet` donne, pour chaque station, l'exposition pondérée
`Σ poids × exp(−d/λ)` à six longueurs de décroissance — 100 m à 30 km pour les forêts,
100 m à 3 km pour les routes. Chacune est un **niveau** : combien de route, combien de
forêt, à cette échelle-là.

Aucune ne dit la **forme** du profil. Or `route_λ100 / route_λ3000` répond à une question
que le niveau ne pose jamais : *la source est-elle collée à la station, ou la station
baigne-t-elle dans un tissu dense ?* C'est la différence entre une rue-canyon et un
centre-ville — et sur le NO₂, c'est le facteur de dispersion local dominant.

Pourquoi un ARBRE ne le formera pas tout seul
-----------------------------------------------
Le même argument que `apport_asymetrie_membres.py` : un arbre partitionne sur **une
variable à la fois**. Un rapport a/b n'est pas approximable par des seuils — il le
remplace par un escalier coûteux en profondeur. Donner le rapport explicitement, c'est
offrir gratuitement ce que le modèle paie cher.

Et la symétrie avec un levier déjà mesuré : la **forme du profil horaire CAMS** (amplitude,
heure du max, pic/moyenne) rend +0,51 % au-dessus de la moyenne journalière. Les ratios
d'échelle sont **le même geste dans l'espace** — passer d'un agrégat à une forme.

Ce qui est établi AVANT de mesurer, et qui rend l'apport non trivial
----------------------------------------------------------------------
* **Les ratios sont définis partout.** `exposition(p, λ)` croît avec λ par construction
  (`exp(−d/λ)` croît en λ), donc λ_petit ≤ λ_grand : le rapport vit dans [0, 1]. Vérifié
  sur les 476 stations, monotonie 5 familles / 5, aucun dénominateur nul. Aucun repli,
  aucune valeur manquante — le défaut de la § 0-L ne peut pas se produire ici.
* **Ils ne redisent pas le niveau.** Corrélation de Spearman au niveau de la même famille :
  |ρ| ≤ 0,56, médiane 0,19. Ce n'est pas une reformulation.

Le protocole, et pourquoi celui-là
------------------------------------
Ces variables décrivent un **site**. Le dépôt a déjà mesuré ce que cela implique : la
typologie de station rend +8,5 à +8,9 pt sur le NO₂ à l'axe SPATIAL et **rien** à l'axe
temporel — le non-effet prouve le mécanisme. On mesure donc ici par défaut au **double
aveugle** (station ET mois cachés), le protocole du dossier, et `--axe temporel` donne le
témoin : si les ratios apportent quelque chose là où toutes les stations sont vues, ce
n'est pas du site qu'ils parlent.

⚠️ **Le biais de criblage est à ×2 à ×4 sur ce dépôt.** La base de comparaison contient
donc DÉJÀ tout ce que le modèle possède aujourd'hui : les niveaux λ, le relief, l'altitude,
le calendrier et CAMS. Ce qui se mesure est l'apport **marginal** de la forme.

⚠️ Et les trois configurations sont **déclarées avant la mesure**. Retenir après coup celle
qui gagne, puis publier son score sur ces mêmes plis, serait exactement le criblage que ce
fichier prétend éviter : un score choisi ici se re-mesure sur des plis qui n'ont pas servi
à le choisir, ou se publie en disant qu'il est dans l'échantillon.

Usage  : python3 scripts/apport_ratios_echelle.py --polluant NO2
Sortie : reports/apport_ratios_echelle_<polluant>_h<n>_<axe>.csv
         reports/apport_ratios_echelle_<polluant>_h<n>_<axe>_par_pli.csv
         reports/predictions_ratios_<jeu>_<polluant>.parquet  (pour bootstrap_apparie.py)
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

from aq.rapport import ecrire_rapport, libelle_echeance  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)

# Les échelles réellement présentes dans `geo_features_metropole.parquet`. Elles ne sont
# pas devinées du nom : le script vérifie leur présence et lève si l'une manque (§ 4 bis).
FAMILLES = {
    "route": (100, 300, 1000, 3000),
    "foret_tot": (100, 300, 1000, 3000, 10000, 30000),
    "chene": (100, 300, 1000, 3000, 10000, 30000),
    "conifere": (100, 300, 1000, 3000, 10000, 30000),
    "feuillu_autre": (100, 300, 1000, 3000, 10000, 30000),
}


def construire_ratios(d: pd.DataFrame) -> dict[str, list[str]]:
    """Ajoute les ratios d'échelle à `d` **en place**, et rend les colonnes par famille.

    Deux formes par famille, et pas une de plus :
    * les rapports **adjacents** (λᵢ / λᵢ₊₁) — la forme du profil, marche par marche ;
    * le rapport **d'envergure** (λ_min / λ_max) — proche contre lointain, en un nombre.

    Le niveau reste dans la base : profil + niveau au plus grand λ ré-encodent exactement
    l'information des six colonnes d'origine, sans en retirer aucune.
    """
    par_famille: dict[str, list[str]] = {}
    for f, lambdas in FAMILLES.items():
        cols = [f"{f}_lambda{l}m" for l in lambdas]
        if manque := [c for c in cols if c not in d.columns]:
            raise SystemExit(f"colonnes d'exposition absentes : {manque}")
        noms = []
        for a, b in zip(lambdas[:-1], lambdas[1:]):
            n = f"{f}_ratio{a}_{b}"
            d[n] = d[f"{f}_lambda{a}m"] / d[f"{f}_lambda{b}m"]
            noms.append(n)
        n = f"{f}_ratio{lambdas[0]}_{lambdas[-1]}"
        d[n] = d[f"{f}_lambda{lambdas[0]}m"] / d[f"{f}_lambda{lambdas[-1]}m"]
        noms.append(n)
        par_famille[f] = noms
    return par_famille


def controler_ratios(d: pd.DataFrame, colonnes: list[str]) -> None:
    """§ 2 bis — un ratio non défini ou constant est un défaut, pas une donnée.

    Le contrôle porte sur la **demande** : toutes les lignes doivent être finies, et
    chaque colonne doit varier. Un dénominateur nul rendrait ici un `inf` que LightGBM
    rangerait dans une branche à part — plausible, et faux.
    """
    fautes = []
    for c in colonnes:
        v = d[c].to_numpy()
        fini = float(np.isfinite(v).mean())
        nu = int(pd.Series(v).nunique())
        if fini < 1.0:
            fautes.append(f"{c} : {100 * (1 - fini):.2f} % de valeurs non finies")
        elif nu < 10:
            fautes.append(f"{c} : {nu} valeur(s) distincte(s) — quasi constante")
    if fautes:
        raise SystemExit("ratios inutilisables :\n   " + "\n   ".join(fautes))
    print(f"  ✅ {len(colonnes)} ratios : tous finis sur 100 % des lignes et variables",
          flush=True)


def redondance(d: pd.DataFrame, par_famille: dict[str, list[str]]) -> float:
    """La corrélation de rang au NIVEAU de la même famille — un ratio qui la redit n'apporte rien."""
    pires = []
    for f, noms in par_famille.items():
        niveau = d[f"{f}_lambda{FAMILLES[f][-1]}m"]
        for c in noms:
            pires.append(abs(float(d[c].corr(niveau, method="spearman"))))
    return float(np.max(pires))


def rmse(o: np.ndarray, x: np.ndarray) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def main(polluant: str, horizon: int, n_spa: int, axe: str) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, cols, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    par_famille = construire_ratios(d)
    r_route = par_famille["route"]
    r_tous = [c for noms in par_famille.values() for c in noms]
    controler_ratios(d, r_tous)
    print(f"  redondance maximale au niveau (|ρ| de Spearman) : {redondance(d, par_famille):.3f}",
          flush=True)

    # ── Les trois configurations, DÉCLARÉES avant la mesure ─────────────────────────
    modes = {
        "① base (CAMS, niveaux λ, relief, calendrier)": base,
        "② + ratios ROUTE (4)": base + r_route,
        "③ + ratios des 5 familles (28)": base + r_tous,
    }

    ids = np.sort(d["station_id"].unique())
    mois = np.sort(d["mois"].unique())
    print(f"\n{polluant} · {libelle_echeance(horizon)} · axe {axe} · {len(d):,} jours-station"
          f" · {len(ids)} stations · {len(mois)} mois", flush=True)

    # ── Le protocole ────────────────────────────────────────────────────────────────
    # `double` cache la station ET le mois — le protocole du dossier, et le seul où un
    # descripteur de site doit prouver quelque chose.
    # `temporel` ne cache que le mois : c'est le TÉMOIN. Un descripteur de site n'y a
    # rien à apporter, puisque le modèle a déjà vu chaque station. Un gain qui y
    # apparaîtrait dirait que ces colonnes portent autre chose que du site.
    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    plis = []
    for i, mm in enumerate(mois):
        m_te = d["mois"] == mm
        m_tr = d["mois"] != mm
        if axe == "double":
            dans = d["station_id"].isin(groupes[i % n_spa])
            m_te, m_tr = m_te & dans, m_tr & ~dans
        plis.append((mm, m_te, m_tr))

    ecartes = [(mm, int(m_te.sum()), int(m_tr.sum())) for mm, m_te, m_tr in plis
               if m_te.sum() < 200 or m_tr.sum() < 1000]
    if ecartes:
        print(f"  ⚠️ {len(ecartes)} pli(s) écarté(s) sur {len(plis)} pour effectif "
              f"insuffisant : " + ", ".join(f"{m}({a}/{b})" for m, a, b in ecartes),
              flush=True)
    print(f"  périmètre effectif : {len(plis) - len(ecartes)} plis exécutés sur {len(plis)}"
          f" prévus", flush=True)

    pred = {k: np.full(len(d), np.nan) for k in modes}
    par_pli: list[dict] = []
    for i, (mm, m_te, m_tr) in enumerate(plis):
        if m_te.sum() < 200 or m_tr.sum() < 1000:
            continue
        te, tr = d[m_te], d[m_tr]
        idx = np.flatnonzero(m_te.to_numpy())
        o, c = te["valeur"].to_numpy(), te["cams_jour"].to_numpy()
        ligne = {"polluant": polluant, "horizon": horizon, "axe": axe, "mois": mm,
                 "n_test": len(te), "n_train": len(tr),
                 "n_stations_test": int(te["station_id"].nunique()),
                 "rmse_ancre": rmse(o, c)}
        for k, (nom, colonnes) in enumerate(modes.items()):
            p = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
            pred[nom][idx] = p
            ligne[f"rmse_config{k + 1}"] = rmse(o, p)
        par_pli.append(ligne)
        if (i + 1) % 6 == 0:
            print(f"  {i + 1}/{len(plis)} plis · {(time.time() - depart) / 60:.1f} min",
                  flush=True)

    ok = np.ones(len(d), bool)
    for nom, v in pred.items():
        if not np.isfinite(v).any():
            raise SystemExit(f"le mode « {nom} » n'a rien produit")
        ok &= np.isfinite(v)
    o = d["valeur"].to_numpy()[ok]
    ancre = d["cams_jour"].to_numpy()[ok]
    r_ancre = rmse(o, ancre)

    tp = pd.DataFrame(par_pli)
    print(f"\n{'═' * 96}")
    print(f"APPORT DES RATIOS D'ÉCHELLE · {polluant} · {libelle_echeance(horizon)} · "
          f"axe {axe} · {int(ok.sum()):,} prédictions")
    print(f"{'═' * 96}")
    print(f"  {'configuration':46s} {'RMSE':>8s} {'gain/CAMS':>10s} {'marginal':>9s} "
          f"{'σ plis':>7s} {'plis>0':>8s}")
    lignes, ref_gain, ref_rmse_pli = [], None, tp["rmse_config1"].to_numpy()
    for k, nom in enumerate(modes):
        x = pred[nom][ok]
        g = 100 * (1 - rmse(o, x) / r_ancre)
        # L'écart APPARIÉ pli à pli contre la configuration ①. Les plis partagent leurs
        # lignes, leur graine et leur découpage : la différence est bien plus serrée que
        # la dispersion de chaque série prise séparément (cf. `bootstrap_apparie.py`).
        dif = 100 * (1 - tp[f"rmse_config{k + 1}"].to_numpy() / ref_rmse_pli)
        marge = np.nan if ref_gain is None else g - ref_gain
        if ref_gain is None:
            ref_gain = g
        print(f"  {nom:46s} {rmse(o, x):8.4f} {g:+9.2f}% "
              f"{'—' if k == 0 else f'{marge:+8.2f}'} {np.std(dif):7.3f} "
              f"{int((dif > 0).sum()):4d}/{len(dif)}")
        lignes.append({"polluant": polluant, "horizon": horizon, "axe": axe,
                       "configuration": nom, "n_colonnes": len(modes[nom]),
                       "rmse_candidat": rmse(o, x), "rmse_ancre": r_ancre,
                       "gain_pct": g, "apport_marginal_pct": marge,
                       "ecart_apparie_moyen_pct": float(np.mean(dif)),
                       "ecart_apparie_sigma_pct": float(np.std(dif)),
                       "n_plis_positifs": int((dif > 0).sum()), "n_plis": len(dif),
                       "n_plis_prevus": len(plis), "n_plis_ecartes": len(ecartes),
                       "n_lignes": int(ok.sum()),
                       "fenetre": f"{mois[0]}→{mois[-1]}", "n_mois": len(mois)})

    contexte = {"polluant": polluant, "axe": axe, "echeance": libelle_echeance(horizon)}
    suff = f"{polluant}_h{horizon}_{axe}"
    ecrire_rapport(pd.DataFrame(lignes),
                   RACINE / f"reports/apport_ratios_echelle_{suff}.csv", contexte,
                   attendues=["gain_pct", "apport_marginal_pct", "ecart_apparie_moyen_pct"])
    ecrire_rapport(tp, RACINE / f"reports/apport_ratios_echelle_{suff}_par_pli.csv",
                   contexte, attendues=["rmse_config1", "rmse_config2", "rmse_config3"])

    # Les prédictions appariées, pour l'intervalle par blocs de mois × groupes
    # géographiques. Deux candidats écrits, jamais un seul : choisir ici celui qui gagne
    # serait le criblage que la docstring refuse.
    for k, nom in list(enumerate(modes))[1:]:
        sortie = RACINE / f"reports/predictions_ratios{k + 1}_{polluant}_{axe}.parquet"
        pd.DataFrame({"station_id": d["station_id"].to_numpy()[ok],
                      "jour": d["jour"].to_numpy()[ok], "obs": o,
                      "pred_reference": pred[list(modes)[0]][ok],
                      "pred_candidat": pred[nom][ok]}).to_parquet(sortie, index=False)
        print(f"Écrit : {sortie.relative_to(RACINE)}")

    print(f"\nÉcrit : reports/apport_ratios_echelle_{suff}.csv · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--axe", default="double", choices=("double", "temporel"),
                   help="« double » cache station ET mois (protocole du dossier) ; "
                        "« temporel » ne cache que le mois — c'est le TÉMOIN")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux, n.axe))
