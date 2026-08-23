#!/usr/bin/env python3
"""La spéciation CAMS apporte-t-elle quelque chose — ou décore-t-elle ?

L'hypothèse testée
-------------------
Notre modèle corrige un **résidu** `observation − CAMS` à partir d'une masse totale. Lui
donner la **composition** du champ — carbone résidentiel (chauffage au bois), aérosol
inorganique secondaire (nitrate agricole), poussières, feux, matière organique — devrait
lui permettre d'apprendre un biais **par source** au lieu d'un biais moyen.

C'est le levier le plus plausible pour l'écart mesuré face à AS-CHI sur les particules :
leur CHIMERE tourne sur l'inventaire d'émissions français, le nôtre est un ensemble
européen dont on n'exploitait que la somme.

🔴 Ce que ce test refuse de faire
----------------------------------
* **Il ne mesure PAS sur l'axe spatial.** Ce dépôt a établi deux fois qu'un gain y trouvé
  ne transfère pas : +4 à +7 % en spatial, ~0 en temporel. L'axe est temporel, et lui seul.
* **Il ne compare pas des lignes différentes.** Les deux configurations sont ajustées et
  notées sur **exactement les mêmes lignes** — celles où la spéciation existe. Sans quoi
  l'écart mesurerait un changement de corpus (§ 2 quater).
* **Il ne conclut pas sur un écart brut.** Le criblage du dépôt exige un gain **relatif** au
  RMSE de base, parce que 0,3 µg/m³ vaut 2 % sur NO₂ et 11 % sur PM2,5.

⚠️ Le nitrate n'existe que depuis 2024-12. Le faire entrer amputerait le corpus de onze
mois ; il est donc **exclu du socle** et testé à part, sur sa propre fenêtre.

Usage : python3 scripts/ablation_speciation.py --polluant PM10
Sortie : reports/ablation_speciation_<polluant>.csv
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
sys.path.insert(0, str(RACINE / "scripts"))

from aq.rapport import ecrire_rapport  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from optuna_mos import GRAINE, params_reference, rmse, typologie  # noqa: E402

# ⚠️ **L'ÉCHÉANCE de la base doit être celle de la spéciation.** `jeu_journalier` appelle
# `charger(polluant, 1)` en dur, et `TRANCHES[1] = (1, 24)` désigne **J0**. Or la spéciation
# est téléchargée aux échéances **25-48 h**, donc J+1. Jointes sur le seul `(station, jour)`,
# les deux décrivaient le même jour civil vu par **deux sorties différentes** — celle du jour
# même pour la base, celle de la veille pour la spéciation.
#
# Ce n'était pas une fuite : le flux 25-48 h est **moins frais**, pas plus. Mais la question
# mesurée n'était pas celle du dossier — « une base J0 gagne-t-elle à recevoir une composition
# J+1 plus ancienne ? » au lieu de « la composition apporte-t-elle à la chaîne J+1 ? ».
# Signalé par une revue externe le 17/08 ; les gains de +4,90 à +11,57 % mesurés avant ce
# correctif sont des signaux exploratoires, pas des résultats.
HORIZON = 2      # TRANCHES[2] = (25, 48) — J+1, l'échéance de la spéciation ET du dossier

# Sept traceurs. Les deux derniers viennent du complément, sur recommandation d'une revue
# externe et pour une raison précise chacun :
# * `pm10_ss_conc` (sel marin sec) — le seul régime **PM10 grossier** du lot ; les cinq
#   autres sont en PM2,5 ou en poussière. Sans lui l'ablation PM10 était incomplète par
#   construction, ce qui est plus grave qu'incomplète par manque de temps ;
# * `ectot_conc` (carbone élémentaire total) — sans le total, `ecres_conc` n'est pas
#   interprétable : on ne peut pas distinguer « chauffage résidentiel » de « combustion ».
# 🔴 `pm2p5_total_om_conc` a QUITTÉ le socle le 23/08/2026 : elle est absente de 2023-08,
# 09 et 10, donc tardive. SOCLE et TARDIVES sont disjoints par définition — l'un est ce
# qui est toujours là, l'autre ce qui manque parfois.
# 🔴 `ectot_conc` et `pm10_ss_conc` ont quitté le socle le 24/08/2026 : mesurées sur les
# 37 mois extraits, elles n'en couvrent que **32** — elles viennent du lot COMPLÉMENT, dont
# l'archive commence en 2024-01. Elles étaient donc des indicateurs d'époque classés parmi
# les colonnes « toujours présentes », et `core7` — la variante censée n'en porter aucun —
# les gardait.
#
# C'est la troisième fois cette nuit que cette liste ment. D'où le garde ci-dessous : la
# classification est vérifiée CONTRE LES DONNÉES à chaque chargement, au lieu d'être crue.
SOCLE = ["dust", "ecres_conc", "pmwf_conc", "sia_conc"]

# 🔴 Une leçon vit à UN endroit ; les autres la CITENT (§ 0-J). Cette liste existait ici
# ET dans `extraire_speciation.py`, et le 23/08 seule la seconde avait été mise à jour :
# `core7` continuait d'écarter le seul nitrate.
#
# ⚠️ Et l'unification a d'abord CASSÉ la chaîne, parce que la matière organique figurait
# encore dans SOCLE : `SOCLE + TARDIVES` la contenait deux fois, et `pd.concat` refuse un
# index non unique. Deux listes qui se ressemblent ne veulent pas forcément dire la même
# chose — ici l'une décrit ce que le FOURNISSEUR sert, l'autre ce que la pile ÉCARTE. Les
# fusionner exigeait de vérifier qu'elles restent disjointes, pas seulement qu'elles
# existent en un exemplaire.
from extraire_speciation import TARDIVES as _TARDIVES_EXTRACTION  # noqa: E402

# Les tardives de la MESURE : celles de l'extraction, plus les deux du lot complément, dont
# l'archive est plus courte que celle du lot principal.
TARDIVES = list(_TARDIVES_EXTRACTION) + ["ectot_conc", "pm10_ss_conc"]

if set(SOCLE) & set(TARDIVES):  # pragma: no cover — un garde, pas une branche
    raise SystemExit(f"SOCLE et TARDIVES se chevauchent : "
                     f"{sorted(set(SOCLE) & set(TARDIVES))} — une colonne est soit "
                     f"toujours présente, soit tardive, jamais les deux.")
N_FILS = 4


def charger_speciation() -> pd.DataFrame:
    """Agrège la spéciation horaire J+1 en valeurs journalières par station.

    Les fichiers portent 24 échéances (25-48 h) d'une sortie 00 UTC, soit exactement le
    jour J+1. La moyenne journalière est donc la grandeur homogène à notre cible ; on
    garde aussi le **maximum** pour les espèces à pic — un épisode de feux ou de poussière
    est un événement, pas un niveau.
    """
    fichiers = sorted(glob.glob(str(RACINE / "data/processed/meteo/speciation_metropole_*.parquet")))
    if not fichiers:
        raise SystemExit("aucune spéciation extraite — lancer scripts/extraire_speciation.py")
    # ⚠️ **Concaténer AVANT d'agréger, jamais l'inverse.** Le fichier d'un mois va jusqu'à
    # l'heure 768, soit `01 du mois suivant + 24 h` = **le 2 à 00:00** ; celui du mois
    # suivant démarre à l'heure 25, soit **le 2 à 01:00**. Le 2 de chaque mois est donc
    # servi par DEUX fichiers — 1 heure d'un côté, 23 de l'autre.
    #
    # Agréger par fichier puis concaténer produisait **deux lignes partielles** pour ce
    # jour-là : 14 756 doublons, une jointure qui rendait **103 %** des lignes de base, et
    # des moyennes journalières calculées sur une seule heure. Rien ne plantait ; le compte
    # de lignes AUGMENTAIT, ce qui est le seul signal qu'une jointure a mal tourné.
    morceaux = []
    for f in fichiers:
        t = pd.read_parquet(f)
        t["jour"] = pd.to_datetime(t["timestamp_utc"]).dt.tz_localize(None).dt.floor("D")
        garde = ["station_id", "jour"] + (["echeance_h"] if "echeance_h" in t.columns else [])
        morceaux.append(t[garde + [c for c in SOCLE + TARDIVES if c in t.columns]])
    brut = pd.concat(morceaux, ignore_index=True)
    # 🔴 La classification se VÉRIFIE contre les données, elle ne se croit pas. Elle a
    # menti trois fois en une nuit : la matière organique, puis le chevauchement
    # SOCLE/TARDIVES, puis les deux colonnes du lot complément. Une colonne du socle
    # absente de mois entiers est un indicateur d'époque déguisé en variable stable.
    mois_brut = pd.to_datetime(brut["jour"]).dt.strftime("%Y-%m")
    traitres = []
    for c in SOCLE:
        if c not in brut.columns:
            traitres.append(f"{c} (absente)")
            continue
        vus = mois_brut[brut[c].notna()].nunique()
        if vus < mois_brut.nunique():
            traitres.append(f"{c} ({vus}/{mois_brut.nunique()} mois)")
    if traitres:
        raise SystemExit(
            "❌ colonne(s) du SOCLE absente(s) de mois entiers : " + ", ".join(traitres)
            + "\n   Le socle est ce qui est TOUJOURS là. Une colonne trouée y est un "
              "indicateur d'époque déguisé : la déplacer dans TARDIVES.")
    cols = [c for c in SOCLE + TARDIVES if c in brut.columns]
    g = brut.groupby(["station_id", "jour"])[cols].agg(["mean", "max"])
    g.columns = [f"spe_{a}_{b}" for a, b in g.columns]
    d = g.reset_index()
    d.attrs["echeances"] = tuple(sorted(brut["echeance_h"].unique())) \
        if "echeance_h" in brut.columns else ()
    if (dbl := d.duplicated(["station_id", "jour"]).sum()):
        raise SystemExit(f"{dbl} doublons (station, jour) après agrégation — anormal")
    print(f"  spéciation : {len(d):,} jours-station · {len(fichiers)} mois · "
          f"{d['jour'].min():%Y-%m-%d} → {d['jour'].max():%Y-%m-%d}", flush=True)
    return d


GROUPES = {
    "grossier_naturel": ["dust", "pm10_ss_conc"],
    "combustion_organique": ["ecres_conc", "ectot_conc", "pm2p5_total_om_conc", "pmwf_conc"],
    "secondaire": ["sia_conc"],
}


def forme_du_total(polluant: str, horizon: int) -> pd.DataFrame:
    """min, max, écart-type et P90−P10 des 24 échéances du total CAMS.

    🔴 **Le contrôle qui décide de l'interprétation.** Les variables de spéciation sont
    résumées par leur moyenne ET leur maximum journaliers. Un maximum de composant porte
    donc une **amplitude intra-journalière** que la base — qui ne connaît que `cams_jour` et
    `cams_moy_jour` — n'a pas. Si le gain de la spéciation disparaît une fois la forme du
    total donnée au modèle, alors elle ne portait pas de la composition : elle portait une
    statistique de forme, et l'histoire des sources s'effondre.

    C'est la configuration `T` de la revue externe, et le moins cher de ses contrôles.
    """
    jeu = charger(polluant, horizon)
    jeu = jeu.dropna(subset=["cams"])
    jour = pd.to_datetime(jeu["timestamp_utc"]).dt.tz_localize(None).dt.floor("D")
    g = jeu.assign(jour=jour).groupby(["station_id", "jour"])["cams"]
    f = g.agg(cams_min="min", cams_max="max", cams_ect="std").reset_index()
    q = g.quantile([0.1, 0.9]).unstack()
    f["cams_p90_p10"] = (q[0.9] - q[0.1]).to_numpy()
    return f


def jeu_journalier_a(polluant: str, horizon: int) -> tuple[pd.DataFrame, list[str]]:
    """`jeu_journalier` d'`optuna_mos`, mais l'horizon devient un ARGUMENT.

    Copie délibérée plutôt qu'import : `optuna_mos.jeu_journalier` est appelé par cinq
    scripts qui attendent J0. Le paramétrer là-bas changerait leur résultat en silence.
    """
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    j["jour"] = pd.to_datetime(j["jour"])
    if j["jour"].dt.tz is not None:
        j["jour"] = j["jour"].dt.tz_localize(None)
    typo, cols_typo = typologie(np.sort(j["station_id"].unique()))
    j = j.merge(typo, on="station_id", how="left")
    if j[cols_typo].isna().any().any():
        raise SystemExit("typologie perdue à la jointure")
    return j, predicteurs + cols_typo


def main(polluant: str) -> int:
    t0 = time.time()
    j, base = jeu_journalier_a(polluant, HORIZON)
    j["jour"] = pd.to_datetime(j["jour"]).dt.tz_localize(None)
    print(f"  base : horizon {HORIZON} (échéances 25-48 h = J+1), "
          f"aligné sur la spéciation", flush=True)
    spe = charger_speciation()

    # ── Le contrôle d'alignement, qui manquait et qui a laissé passer le défaut ─────────
    # Joindre sur `(station, jour)` ne vérifie RIEN de l'échéance : deux sorties distinctes
    # décrivant le même jour civil se joignent parfaitement. On exige donc que les deux flux
    # couvrent la MÊME plage d'échéances avant de les réunir.
    # ⚠️ **`echeance_h` ne porte PAS une échéance sur ces fichiers.** Pour un `.nc` mensuel,
    # `_normaliser_colonnes` y met les **heures depuis le début du mois** (25 → 768) : le nom
    # vient des fichiers JOURNALIERS, où il est juste. L'échéance réelle se reconstruit —
    # `((h − 25) mod 24) + 25` — et elle tient bien dans 25-48, donc J+1. Vérifié le 17/08.
    ech = spe.attrs.get("echeances", ())
    if ech:
        reelles = sorted({((int(h) - 25) % 24) + 25 for h in ech})
        if reelles != list(range(25, 49)):
            raise SystemExit(f"échéances réelles {reelles[:4]}…{reelles[-2:]} — attendu 25-48 "
                             f"(J+1). La spéciation n'est pas alignée sur la base.")
        print(f"  ✓ échéances réelles 25-48 h (J+1) — base et spéciation alignées",
              flush=True)

    f = forme_du_total(polluant, HORIZON)
    j = j.merge(f, on=["station_id", "jour"], how="left")

    avant = len(j)
    j = j.merge(spe, on=["station_id", "jour"], how="inner")
    cols_spe = [c for c in j.columns if c.startswith("spe_")
                and not any(t in c for t in TARDIVES)]
    print(f"{polluant} · {avant:,} → {len(j):,} jours-station après jointure "
          f"({100*len(j)/avant:.0f} % conservés) · {len(cols_spe)} variables de spéciation",
          flush=True)
    if len(j) < 20_000:
        raise SystemExit(f"{len(j)} lignes après jointure — trop peu pour conclure")

    # Partage TEMPOREL, identique aux autres bancs de ce dépôt.
    jours = np.sort(j["jour"].unique())
    coupe = jours[len(jours) // 2]
    entr = (j["jour"] < coupe).to_numpy()
    test = ~entr
    y = (j["obs_jour"] - j["cams_jour"]).to_numpy(dtype=np.float32)
    obs = j.loc[test, "obs_jour"].to_numpy()
    cams = j.loc[test, "cams_jour"].to_numpy()

    from lightgbm import LGBMRegressor  # noqa: PLC0415

    gardees: dict[str, np.ndarray] = {}

    def mesurer(colonnes: list[str], nom: str, garder: str | None = None) -> float:
        X = j[colonnes].to_numpy(dtype=np.float32)
        m = LGBMRegressor(n_estimators=400, random_state=GRAINE, verbose=-1,
                          n_jobs=N_FILS, **params_reference("lgbm"))
        m.fit(X[entr], y[entr])
        pred = np.clip(cams + m.predict(X[test]), 0, None)
        if garder:
            gardees[garder] = pred
        r = rmse(obs, pred)
        print(f"  {nom:34s} RMSE {r:7.4f} · {len(colonnes):3d} variables", flush=True)
        return r

    cols_forme = [c for c in ("cams_min", "cams_max", "cams_ect", "cams_p90_p10")
                  if c in j.columns]
    r_cams = rmse(obs, cams)
    r_base = mesurer(base, "B · base", garder="pred_base")
    r_T = mesurer(base + cols_forme, "T · base + forme du total")
    r_tout = mesurer(base + cols_forme + cols_spe, "S · T + spéciation", garder="pred_spe")

    lignes = [{"config": "CAMS brut", "rmse": r_cams, "n_variables": 0},
              {"config": "B base", "rmse": r_base, "n_variables": len(base)},
              {"config": "T base+forme", "rmse": r_T,
               "n_variables": len(base) + len(cols_forme)},
              {"config": "S T+spéciation", "rmse": r_tout,
               "n_variables": len(base) + len(cols_forme) + len(cols_spe)}]

    # ── La question qui décide : S − T, et non S − B ───────────────────────────────────
    print(f"\n  S − B (contre la base nue)    {100*(1-r_tout/r_base):+6.2f} %", flush=True)
    print(f"  T − B (la FORME seule)        {100*(1-r_T/r_base):+6.2f} %", flush=True)
    print(f"  S − T (la COMPOSITION seule)  {100*(1-r_tout/r_T):+6.2f} %  ← ce qui compte",
          flush=True)

    # ── Décomposition en trois groupes physiques, qui remplace le leave-one-out ────────
    for nom, membres in GROUPES.items():
        sans = [c for c in cols_spe if not any(m in c for m in membres)]
        r = mesurer(base + cols_forme + sans, f"  sans {nom}")
        lignes.append({"config": f"sans {nom}", "rmse": r,
                       "n_variables": len(base) + len(cols_forme) + len(sans)})

    t = pd.DataFrame(lignes)
    t["gain_vs_base_pct"] = 100 * (1 - t["rmse"] / r_base)
    t["gain_vs_forme_pct"] = 100 * (1 - t["rmse"] / r_T)
    t["gain_vs_cams_pct"] = 100 * (1 - t["rmse"] / r_cams)

    apport = 100 * (1 - r_tout / r_T)   # l'apport PROPRE de la composition
    print(f"\n  → la spéciation rend {apport:+.2f} % contre la base", flush=True)

    # Le criblage du dépôt : un gain RELATIF, parce que 0,3 µg/m³ vaut 2 % sur NO₂ et 11 %
    # sur PM2,5. Le seuil est 2 % du RMSE de base.
    from aq.eval.critere import PART_RETENTION  # noqa: PLC0415

    verdict = ("RETENU" if apport >= 100 * PART_RETENTION else
               f"écarté — sous le seuil de {100 * PART_RETENTION:.0f} %")
    print(f"  criblage : {verdict}", flush=True)

    # Les prédictions ligne à ligne, pour que l'incertitude se mesure APPARIÉE — sur les
    # mêmes observations — et non en comparant deux dispersions indépendantes. La barre de
    # bruit du dépôt (±2,02 pt) porte sur un score ABSOLU non apparié : la comparer à un
    # écart apparié surestimerait l'incertitude de plusieurs fois.
    pd.DataFrame({
        "station_id": j.loc[test, "station_id"].to_numpy(),
        "jour": j.loc[test, "jour"].to_numpy(),
        "obs": obs, "pred_reference": gardees["pred_base"],
        "pred_candidat": gardees["pred_spe"],
    }).to_parquet(RACINE / f"reports/predictions_speciation_{polluant}.parquet", index=False)

    ecrire_rapport(t, RACINE / f"reports/ablation_speciation_{polluant}.csv",
                   contexte={"polluant": polluant, "axe": "temporel"},
                   attendues=["config", "rmse", "gain_vs_base_pct"])
    print(f"Écrit · {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10", choices=("O3", "NO2", "PM10", "PM25"))
    n = a.parse_args()
    raise SystemExit(main(n.polluant))
