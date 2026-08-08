#!/usr/bin/env python3
"""Banc de préprocessing — ce qu'une transformation de variables apporte, ou n'apporte pas.

Ce que ce banc refuse de tester, et pourquoi
---------------------------------------------
**Un modèle à arbres est invariant aux transformations monotones d'une seule variable.**
LightGBM coupe sur des seuils ordonnés : `log(x)`, `√x`, Box-Cox, normalisation
quantile, ou `x²` sur un domaine positif produisent **exactement le même arbre**, au
binning près. Les inscrire au banc reviendrait à mesurer du bruit, puis à publier le
meilleur tirage — c'est le biais de criblage, mesuré **×2 à ×4** sur ce projet.

Le banc ne teste donc que ce qu'un arbre **ne peut pas construire seul** :

1. la **périodicité** — un arbre a besoin de nombreuses coupes pour approcher un cycle
   annuel, là où deux colonnes de sinus le donnent d'un coup ;
2. les **rapports et écarts entre colonnes** — les coupes sont parallèles aux axes, donc
   `a / b` demande un escalier ;
3. les **agrégats de groupe** — une moyenne par station est une information *entre*
   lignes, qu'aucune coupe ne peut atteindre.

Ce que le périmètre impose
----------------------------
Toutes les variables construites ici se calculent **depuis CAMS, le calendrier et les
descripteurs de site** — jamais depuis une observation. C'est délibéré : le point faible
du dossier est le périmètre **PARTOUT** (prédire là où aucune station ne mesure, ozone
+13,75 %), et une variable qui exigerait l'historique observé du point le quitterait pour
le périmètre AUX STATIONS, où le gain est déjà connu et deux fois plus élevé.

⚠️ `anomalie_cams` et `tendance_cams` utilisent le **passé de CAMS au point**, pas le
passé des mesures. Une prévision passée existe partout, y compris là où rien ne mesure :
le périmètre est conservé. C'est la distinction que `CLAUDE.md` § 2 quater demande
d'énoncer plutôt que de laisser deviner.

Le protocole, et sa défense contre le criblage
------------------------------------------------
Épreuve **double aveugle** — station *et* mois cachés ensemble —, plis identiques d'une
variante à l'autre pour que la comparaison soit **appariée**. Et les plis sont coupés en
deux jeux disjoints :

* **écran** — deux tiers des mois, où toutes les familles concourent ;
* **confirmation** — le tiers restant, que seules les familles survivantes touchent, et
  **une seule fois**.

Sans cela, le meilleur de N essais est optimiste d'un facteur mesuré à 2 à 4 sur ce
projet. Une famille qui gagne à l'écran et s'effondre en confirmation n'a rien trouvé.

Une famille, un processus
---------------------------
Le banc tournait d'abord les six variantes dans un seul processus. LightGBM y a produit
une **erreur de segmentation**, native donc muette, reproductible à la quatrième famille
alors que les variables passaient tous les contrôles — et non reproductible sur données
synthétiques de même forme. La cause est un état cumulé du processus, pas la donnée.
Chaque famille tourne donc isolément, le corpus est mis en cache, et les gains **par pli**
sont écrits au fur et à mesure : un banc qui meurt ne perd que sa famille en cours.

Usage :
  for f in base harmoniques splines anomalie_cams tendance_cams interactions; do
      python3 scripts/banc_preprocessing.py --polluant O3 --famille $f
  done
  python3 scripts/banc_preprocessing.py --polluant O3 --rapport

Sorties : reports/banc_preprocessing_<polluant>_h<horizon>_plis.csv  (gains par pli)
          reports/banc_preprocessing_<polluant>_h<horizon>.csv       (tableau final)
"""

from __future__ import annotations

import argparse
import gc
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from double_aveugle_journalier import GRAINE, ajuster, gain  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import DEFAUT  # noqa: E402

N_GROUPES_STATIONS = 5
PART_ECRAN = 2 / 3


# ─────────────────────────────────────────────────────────────────────────────
# Les familles. Chacune rend les NOUVELLES colonnes, jamais le tableau entier.
# ─────────────────────────────────────────────────────────────────────────────

def f_harmoniques(d: pd.DataFrame) -> pd.DataFrame:
    """Harmoniques d'ordre 2 et 3 du cycle annuel.

    L'ordre 1 (`jour_annee_sin/cos`) est déjà dans `mos.variables_calendaires`. Il ne sait
    représenter qu'un cycle **à un seul maximum**. La chimie de l'ozone en a deux — montée
    photochimique de printemps, pic de canicule — et les PM aussi : chauffage l'hiver,
    épandage au printemps. Les harmoniques supérieures les portent sans que l'arbre ait à
    découper le calendrier en tranches.
    """
    angle = 2 * np.pi * d["jour"].dt.dayofyear / 365.25
    return pd.DataFrame({f"annee_{k}_{f}": (np.sin if f == "sin" else np.cos)(k * angle)
                         for k in (2, 3) for f in ("sin", "cos")}, index=d.index)


def f_splines(d: pd.DataFrame) -> pd.DataFrame:
    """Base de B-splines **périodiques** sur le jour de l'année.

    Alternative aux harmoniques : au lieu d'un cycle global, une base locale qui peut
    marquer une saison sans déformer les autres. Douze fonctions, soit environ une par
    mois, mais continues et sans le décrochage du 31 décembre au 1ᵉʳ janvier que produit
    une variable `mois` traitée en entier.
    """
    from sklearn.preprocessing import SplineTransformer  # noqa: PLC0415

    j = d["jour"].dt.dayofyear.to_numpy(dtype=float).reshape(-1, 1)
    base = SplineTransformer(n_knots=12, degree=3, extrapolation="periodic",
                             include_bias=False).fit_transform(j)
    return pd.DataFrame(base, columns=[f"spline_annee_{i}" for i in range(base.shape[1])],
                        index=d.index)


def f_anomalie_cams(d: pd.DataFrame) -> pd.DataFrame:
    """Écart de CAMS à **sa propre climatologie au point** — un agrégat de groupe.

    CAMS ne se trompe pas de la même façon partout : sur un site urbain il sous-estime
    structurellement le NO₂, en altitude il surestime l'ozone nocturne. Le modèle ne peut
    pas le déduire d'une coupe, parce que « 40 µg/m³ » ne veut pas dire la même chose selon
    le site. Trois colonnes : l'écart à la moyenne du site, l'écart à la moyenne du site
    **au même mois calendaire**, et le rapport — qui dit « aujourd'hui vaut 1,4 fois
    l'ordinaire ici », ce qu'aucun escalier de coupes ne construit.

    ⚠️ Aucune observation n'entre ici : ces moyennes se calculent sur la série CAMS, qui
    existe partout. Le périmètre PARTOUT est conservé.
    """
    c = d["cams_jour"]
    par_station = c.groupby(d["station_id"]).transform("mean")
    mois_cal = d["jour"].dt.month
    par_station_mois = c.groupby([d["station_id"], mois_cal]).transform("mean")
    return pd.DataFrame({
        "cams_ecart_clim": c - par_station,
        "cams_ecart_clim_mois": c - par_station_mois,
        "cams_ratio_clim": c / par_station.replace(0, np.nan),
    }, index=d.index)


def f_tendance_cams(d: pd.DataFrame) -> pd.DataFrame:
    """Dynamique récente de CAMS au point — la variable la plus « série temporelle » du lot.

    Le levier le plus fort du projet est l'historique **observé** du site (+7,9 points sur
    l'ozone), mais il n'existe qu'aux stations. Celui-ci en est l'équivalent déployable
    partout : la prévision d'hier existe partout où celle d'aujourd'hui existe. On lui
    demande de porter l'installation d'un épisode — un niveau élevé qui **monte** n'est pas
    un niveau élevé qui retombe, et la valeur du jour ne distingue pas les deux.
    """
    ordre = d.sort_values(["station_id", "jour"])
    passe = ordre.groupby("station_id")["cams_jour"].shift(1)      # jamais le jour même
    sortie = pd.DataFrame(index=ordre.index)
    sortie["cams_veille"] = passe
    sortie["cams_delta_1j"] = ordre["cams_jour"] - passe
    par_station = passe.groupby(ordre["station_id"])
    for f in (3, 7):
        moyenne = par_station.rolling(f, min_periods=max(2, f // 2)).mean()
        moyenne.index = moyenne.index.droplevel(0)
        sortie[f"cams_moy_{f}j"] = moyenne
        sortie[f"cams_ecart_moy_{f}j"] = ordre["cams_jour"] - moyenne
    volatilite = par_station.rolling(7, min_periods=4).std()
    volatilite.index = volatilite.index.droplevel(0)
    sortie["cams_volatilite_7j"] = volatilite
    return sortie.sort_index()


def f_interactions(d: pd.DataFrame, base: list[str], k: int = 6) -> pd.DataFrame:
    """Produits et rapports des `k` variables les plus utiles au modèle de base.

    C'est la « combinatoire polynomiale » demandée, **bornée par l'importance** : les 60
    variables donnent 1 770 paires, dont la quasi-totalité sont du bruit qu'un criblage
    finirait par élire. On n'en garde que les paires issues du sommet du classement, et on
    dit combien de colonnes cela fait — un banc qui ne compte pas ses essais ne peut pas
    corriger son biais de criblage.
    """
    from lightgbm import LGBMRegressor  # noqa: PLC0415

    modele = LGBMRegressor(random_state=GRAINE, n_jobs=8, verbose=-1,
                           n_estimators=200, learning_rate=0.1)
    modele.fit(d[base], d["valeur"] - d["cams_jour"])
    ordre = pd.Series(modele.feature_importances_, index=base).sort_values(ascending=False)
    tete = [c for c in ordre.index[:k] if d[c].nunique() > 2]

    sortie = pd.DataFrame(index=d.index)
    for i, a in enumerate(tete):
        for b in tete[i + 1:]:
            sortie[f"x_{a}__{b}"] = d[a] * d[b]
            # ⚠️ `replace(0, nan)` ne protège que du zéro **exact**. Or `jour_annee_sin`
            # passe par des valeurs de l'ordre de 1e-17 : le rapport atteint alors 1e17,
            # une valeur finie que LightGBM accepte puis sur laquelle son binning produit
            # une **erreur de segmentation**. C'est la seule famille qui plantait encore
            # une fois chacune isolée dans son processus. On borne au lieu de diviser à
            # l'aveugle — un dénominateur sous 1e-6 n'est pas une information, c'est un
            # zéro déguisé.
            denom = d[b].where(d[b].abs() > 1e-6)
            sortie[f"r_{a}__{b}"] = (d[a] / denom).clip(-1e6, 1e6)
    print(f"  interactions : sommet = {', '.join(tete)} → {sortie.shape[1]} colonnes",
          flush=True)
    return sortie


FAMILLES = {
    "harmoniques": f_harmoniques,
    "splines": f_splines,
    "anomalie_cams": f_anomalie_cams,
    "tendance_cams": f_tendance_cams,
    "interactions": f_interactions,
}


# ─────────────────────────────────────────────────────────────────────────────

def plis_double_aveugle(d: pd.DataFrame) -> list[tuple[str, pd.Series, pd.Series]]:
    """Les plis du double aveugle, **identiques** à ceux de `double_aveugle_journalier`.

    Même graine, même partition : les variantes de ce banc se comparent donc aux chiffres
    déjà publiés, et entre elles de façon appariée. Un banc qui redéfinirait ses plis
    mesurerait la partition autant que la transformation — σ 0,20 point par partition
    contre 1,31 par composition en mois, mesuré le 04/08.
    """
    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), N_GROUPES_STATIONS)
    plis = []
    for i, m in enumerate(np.sort(d["mois"].unique())):
        dans = d["station_id"].isin(groupes[i % N_GROUPES_STATIONS])
        plis.append((f"{m}+s{i % N_GROUPES_STATIONS + 1}",
                     (d["mois"] == m) & dans, (d["mois"] != m) & ~dans))
    return plis


def jouer(d: pd.DataFrame, colonnes: list[str],
          plis: list[tuple[str, pd.Series, pd.Series]]) -> tuple[float, np.ndarray, int]:
    """Gain global sur un jeu de plis, plus le gain **par pli** pour l'appariement."""
    obs, cams, pred, par_pli, etiquettes, ecartes = [], [], [], [], [], 0
    # ⚠️ **Le cadre est défragmenté et réduit avant d'entrer dans LightGBM.** Concaténer
    # les colonnes d'une famille laisse un `DataFrame` en blocs multiples ; passé tel quel,
    # `Dataset.__init_from_np2d` a produit une **erreur de segmentation** — native, donc
    # sans trace Python, et **non déterministe** : le premier lancement est mort à la
    # quatrième famille, le second à la première. Une copie contiguë en float64 supprime
    # le chemin sans copie qui plantait. Coût : quelques centaines de Mo, une fois.
    # `cams_jour` est **déjà** dans `colonnes` : le citer deux fois créerait une colonne
    # dupliquée, que LightGBM ne rejette pas et traite de travers. On dédoublonne en
    # gardant l'ordre — `dict.fromkeys` le fait sans trier.
    gardees = list(dict.fromkeys(["valeur", "cams_jour", *colonnes]))
    d = d[gardees].astype({c: "float64" for c in gardees}).copy()
    for etiquette, mt, mtr in plis:
        te, tr = d[mt.to_numpy()], d[mtr.to_numpy()]
        if len(te) < 200 or tr.empty:
            # `CLAUDE.md` § 2 quater : un pli écarté change le dénominateur en silence.
            ecartes += 1
            continue
        p = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
        par_pli.append(gain(te["valeur"].to_numpy(), te["cams_jour"].to_numpy(), p))
        etiquettes.append(etiquette)
        obs.append(te["valeur"].to_numpy())
        cams.append(te["cams_jour"].to_numpy())
        pred.append(p)
    return (gain(np.concatenate(obs), np.concatenate(cams), np.concatenate(pred)),
            np.array(par_pli), ecartes, etiquettes)


def ic_apparie(a: np.ndarray, b: np.ndarray, tirages: int = 5000) -> tuple[float, float]:
    """IC95 de l'écart **apparié** pli à pli — le bruit de partition s'annule."""
    rng = np.random.default_rng(GRAINE)
    ecart = a - b
    tirage = rng.choice(ecart, size=(tirages, len(ecart)), replace=True).mean(axis=1)
    return float(np.percentile(tirage, 2.5)), float(np.percentile(tirage, 97.5))




CACHE = RACINE / "data/interim"


def preparer(polluant: str, horizon: int) -> tuple[pd.DataFrame, list[str]]:
    """Corpus journalier prêt à l'emploi, **mis en cache**.

    Le chargement coûte deux minutes ; le banc tourne une famille par processus (voir
    `executer`), donc il paierait ce prix six fois. Le cache le ramène à quelques
    secondes. Nom provisoire puis renommage, règle 4.
    """
    import json  # noqa: PLC0415

    cache = CACHE / f"banc_{polluant}_h{horizon}.parquet"
    liste = cache.with_suffix(".colonnes.json")
    if cache.exists() and liste.exists():
        return pd.read_parquet(cache), json.loads(liste.read_text(encoding="utf-8"))

    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    CACHE.mkdir(parents=True, exist_ok=True)
    prov = cache.with_suffix(".parquet.partiel")
    d.to_parquet(prov, index=False)
    prov.replace(cache)
    liste.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
    return d, base


def chemin_plis(polluant: str, horizon: int) -> Path:
    return RACINE / f"reports/banc_preprocessing_{polluant}_h{horizon}_plis.csv"


def executer(polluant: str, horizon: int, famille: str) -> int:
    """Une famille, **un processus**.

    ⚠️ Le banc tournait d'abord les six variantes dans un seul processus. LightGBM y a
    produit une **erreur de segmentation** dans `Dataset.__init_from_np2d` — native, donc
    sans trace Python tant que `faulthandler` n'était pas armé. Trois lancements, trois
    morts, la dernière reproductible à la quatrième famille alors que les variables
    passaient tous les contrôles : ni infini, ni NaN anormal, index aligné, plages saines,
    et aucune reproduction sur données synthétiques de même forme. La cause est un **état
    cumulé du processus**, pas la donnée.

    Isoler chaque famille supprime la question. Le corpus est mis en cache pour que le
    prix payé — un chargement par processus — retombe à quelques secondes.
    """
    depart = time.time()
    d, base = preparer(polluant, horizon)
    plis = plis_double_aveugle(d)
    n_ecran = int(len(plis) * PART_ECRAN)
    jeux = {"écran": plis[:n_ecran], "confirmation": plis[n_ecran:]}

    if famille == "base":
        cols, n_neuves = base, 0
    else:
        neuves = (FAMILLES[famille](d, base) if famille == "interactions"
                  else FAMILLES[famille](d))
        d = pd.concat([d, neuves], axis=1)
        cols, n_neuves = base + list(neuves.columns), neuves.shape[1]

    lignes = []
    for nom_jeu, sous in jeux.items():
        g, par_pli, ecartes, etiquettes = jouer(d, cols, sous)
        print(f"  {famille:16s} {nom_jeu:12s} gain {g:+6.2f} % · {len(par_pli)} plis"
              f"{f' · {ecartes} écarté(s)' if ecartes else ''}", flush=True)
        lignes += [{"famille": famille, "jeu": nom_jeu, "pli": e, "gain_pli_pct": v,
                    "gain_jeu_pct": g, "n_colonnes_ajoutees": n_neuves,
                    "n_plis_ecartes": ecartes}
                   for e, v in zip(etiquettes, par_pli, strict=True)]

    cible = chemin_plis(polluant, horizon)
    t = pd.DataFrame(lignes)
    if cible.exists():
        ancien = pd.read_csv(cible)
        t = pd.concat([ancien[ancien["famille"] != famille], t], ignore_index=True)
    prov = cible.with_suffix(".csv.partiel")
    t.to_csv(prov, index=False)
    prov.replace(cible)
    print(f"  → {cible.name} · {len(t)} lignes · {time.time() - depart:.0f}s", flush=True)
    return 0


def rapport(polluant: str, horizon: int) -> int:
    """Le tableau final, calculé depuis les gains **par pli** — jamais recopié."""
    source = chemin_plis(polluant, horizon)
    if not source.exists():
        raise SystemExit(f"{source.name} absent — lancer d'abord --famille base")
    p = pd.read_csv(source)
    if "base" not in set(p["famille"]):
        raise SystemExit("la famille `base` manque : aucune comparaison appariée possible")

    lignes = []
    for jeu in ("écran", "confirmation"):
        sous = p[p["jeu"] == jeu]
        ref = sous[sous["famille"] == "base"].set_index("pli")["gain_pli_pct"]
        for famille, bloc in sous.groupby("famille", sort=False):
            b = bloc.set_index("pli")["gain_pli_pct"]
            communs = ref.index.intersection(b.index)
            bas, haut = ((0.0, 0.0) if famille == "base" else
                         ic_apparie(b[communs].to_numpy(), ref[communs].to_numpy()))
            lignes.append({
                "polluant": polluant, "horizon": horizon, "jeu": jeu, "famille": famille,
                "n_colonnes_ajoutees": int(bloc["n_colonnes_ajoutees"].iloc[0]),
                "n_plis": len(communs), "gain_pct": float(bloc["gain_jeu_pct"].iloc[0]),
                "ecart_pt": float(bloc["gain_jeu_pct"].iloc[0]
                                  - sous[sous["famille"] == "base"]["gain_jeu_pct"].iloc[0]),
                "ic_bas": bas, "ic_haut": haut,
                "verdict": "base" if famille == "base" else
                           ("gagne" if bas > 0 else "perd" if haut < 0 else "indécis")})

    t = pd.DataFrame(lignes).sort_values(["jeu", "ecart_pt"], ascending=[True, False])
    attendues = {"famille", "jeu", "gain_pct", "ecart_pt", "ic_bas", "ic_haut", "verdict"}
    if manque := attendues - set(t.columns):
        raise SystemExit(f"colonnes absentes du rapport : {sorted(manque)}")
    cible = RACINE / f"reports/banc_preprocessing_{polluant}_h{horizon}.csv"
    t.to_csv(cible, index=False)

    for jeu in ("écran", "confirmation"):
        bloc = t[t["jeu"] == jeu]
        if bloc.empty:
            continue
        print(f"\n── {jeu} · {int(bloc['n_plis'].max())} plis ──")
        for _, r in bloc.iterrows():
            marque = {"gagne": "✅", "perd": "❌", "indécis": "🟠", "base": "  "}[r["verdict"]]
            print(f"  {marque} {r['famille']:16s} gain {r['gain_pct']:+6.2f} % · "
                  f"écart {r['ecart_pt']:+5.2f} pt · "
                  f"IC95 [{r['ic_bas']:+.2f} ; {r['ic_haut']:+.2f}] · "
                  f"+{int(r['n_colonnes_ajoutees'])} col")
    print(f"\nÉcrit : {cible.relative_to(RACINE)} · {len(t)} lignes")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM10", "PM25"])
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--famille", default=None,
                   choices=["base", *FAMILLES], help="une famille, un processus")
    a.add_argument("--rapport", action="store_true",
                   help="assemble le tableau final depuis les gains par pli")
    args = a.parse_args()
    if args.rapport:
        raise SystemExit(rapport(args.polluant, args.horizon))
    if not args.famille:
        raise SystemExit("préciser --famille (une par processus) ou --rapport")
    raise SystemExit(executer(args.polluant, args.horizon, args.famille))
