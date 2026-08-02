#!/usr/bin/env python3
"""Le poids de chaque source d'information, mois par mois.

La question
-----------
Le dossier mesure ce que chaque bloc de variables apporte **en moyenne**. Il ne dit pas *quand*
il apporte. Or un service ne se demande pas si les feux comptent en général : il se demande si
les feux comptent **aujourd'hui**.

Ce que le script mesure
-----------------------
Une **importance par permutation**, calculée mois par mois. Pour chaque bloc de variables et
chaque mois, on mélange les valeurs du bloc **à l'intérieur du mois** et l'on mesure de combien
l'erreur augmente. Un bloc dont la permutation ne change rien n'apportait rien ce mois-là.

Pourquoi la permutation plutôt que le réapprentissage
------------------------------------------------------
Réentraîner un modèle par bloc et par mois coûterait des centaines d'ajustements. La
permutation interroge le **modèle déjà appris** : elle mesure ce qu'il utilise, non ce qu'il
pourrait utiliser. C'est la bonne question ici — on décrit un modèle donné, on n'en cherche pas
un meilleur.

**Sa limite, à énoncer** : deux blocs porteurs de la même information se partagent l'importance
et paraissent tous deux faibles. Le projet a mesuré que les familles météo sont largement
redondantes ; ces chiffres se lisent donc comme des **contributions marginales**, pas comme des
parts d'un tout.

Le mélange est **stratifié par mois** : mélanger sur l'année entière détruirait aussi le signal
saisonnier, et l'on mesurerait alors la saison plutôt que le bloc.

Usage : python3 scripts/importance_temporelle.py [--polluant O3]
Sortie : reports/importance_temporelle_O3.csv
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import controle as ctl  # noqa: E402
from apport_observation_veille import variables_passees  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from heatmap_annuelle import MEMBRES, PREFIXE  # noqa: E402
from aq.ingest.controle import ControleEchec  # noqa: E402
from modele_final import REGLE  # noqa: E402

# Les blocs, dans l'ordre où le dossier les a introduits. Le regroupement suit le **mécanisme**
# et non la commodité : le relief et le paysage décrivent tous deux le lieu, mais l'un porte la
# forme du terrain et l'autre les sources biogéniques.
BLOCS = {
    "prévision CAMS": lambda c: c in ("cams_jour", "cams_moy_jour", "echeance_h"),
    "calendrier": lambda c: bool(re.match(r"(heure|jour|mois|semaine|sin|cos|weekend|ferie)", c)),
    "paysage": lambda c: bool(re.match(
        r"(chene|feuillu|conifere|resineux|foret|hetre|pin|prairie|culture|urbain|eau)", c)),
    "relief": lambda c: bool(re.match(r"(tpi|pente|rugosite|expo|altitude|encaissement|"
                                      r"profondeur|relief)", c)),
    "trafic et population": lambda c: bool(re.match(r"(route|trafic|autoroute|importance|pop)", c)),
    "position": lambda c: c in ("lat_wgs84", "lon_wgs84"),
    "observation à J−2": lambda c: bool(re.match(r"(obs_j|err_j|obs_moy|err_moy|err_ecart|"
                                                 r"fraicheur)", c)),
    "membres d'ensemble": lambda c: c in MEMBRES,
    "exposition aux feux": lambda c: c.startswith("feu_"),
}


def joindre(j: pd.DataFrame, motif: str, cle: list[str], quoi: str) -> pd.DataFrame:
    fichiers = sorted(glob.glob(str(RACINE / "data/processed/meteo" / motif)))
    if not fichiers:
        print(f"  ⚠️ {quoi} absent", flush=True)
        return j
    d = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    if "jour" in d.columns:
        d["jour"] = pd.to_datetime(d["jour"])
    avant = len(j)
    j = j.merge(d, on=cle, how="left")
    print(f"  {quoi} · {len(fichiers)} fichiers · {avant:,} lignes conservées", flush=True)
    return j


def main(polluant: str, n_plis: int, graine: int) -> int:
    depart = time.time()
    court = PREFIXE[polluant]
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    membres_h = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/membres_metropole_{court}_*.parquet")))
    if membres_h:
        m = pd.concat([pd.read_parquet(f) for f in membres_h], ignore_index=True)
        ctl.exiger_colonnes(m, MEMBRES, "membres")
        jeu = jeu.merge(m[["station_id", "timestamp_utc"] + MEMBRES],
                        on=["station_id", "timestamp_utc"], how="left")

    presents = [c for c in MEMBRES if c in jeu.columns]
    j = agreger_journalier(jeu, colonnes + presents, GRANDEUR_PAR_POLLUANT[polluant])
    j["jour"] = pd.to_datetime(j["jour"])
    passees, obs = variables_passees(j)
    j = j.merge(passees, on=["station_id", "jour"], how="left")
    j = joindre(j, "feux_metropole_*.parquet", ["station_id", "jour"], "exposition aux feux")

    # Le produit officiel, pour que la carte porte ses **référentiels** : sans eux, elle dit
    # quelle source pèse, jamais si la correction a bien marché ce mois-là.
    archives = sorted((RACINE / "data/raw/cams_mos_officiel").glob(f"{court}_*.zip"))
    if archives:
        from comparer_mos_officiel import journalier, lire_officiel

        o = pd.concat([journalier(lire_officiel(a), ["officiel_mos"],
                                  GRANDEUR_PAR_POLLUANT[polluant]) for a in archives],
                      ignore_index=True)
        o["jour"] = pd.to_datetime(o["jour"]).dt.tz_localize(None)
        j["jour"] = (j["jour"].dt.tz_localize(None)
                     if getattr(j["jour"].dt, "tz", None) is not None else j["jour"])
        j = j.merge(o, on=["station_id", "jour"], how="left")
        print(f"  MOS officiel · {len(archives)} archives · "
              f"{int(j['officiel_mos'].notna().sum()):,} lignes renseignées", flush=True)

    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    feux = [c for c in j.columns if c.startswith("feu_")]
    predicteurs = base + obs + presents + feux
    # Les lignes incomplètes sont écartées **une fois pour toutes** : comparer des mois dont
    # certains n'ont pas les mêmes colonnes renseignées mesurerait la couverture, pas
    # l'importance.
    j = j.dropna(subset=predicteurs)
    ctl.exiger_lignes(j, 5000, "jeu complet")

    j["mois"] = j["jour"].dt.to_period("M")
    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    print(f"\n{polluant} · {len(j):,} jours-station · {j['mois'].nunique()} mois · "
          f"{len(predicteurs)} prédicteurs", flush=True)


    # **Un modèle par pli, tous conservés.** Une première version comparait une référence
    # calculée hors pli — donc par trois modèles différents — à une version permutée calculée
    # par le seul dernier modèle, appliqué à toutes les lignes y compris celles qu'il avait
    # apprises. Elle mesurait l'écart entre deux modèles, pas l'apport d'un bloc, et rendait
    # des importances **négatives** : mélanger une variable paraissait améliorer la prédiction.
    #
    # Une permutation ne peut pas améliorer un modèle. Une importance négative systématique est
    # donc toujours le signe que la référence et la version permutée ne viennent pas du même
    # estimateur.
    modeles = {}
    j["pred"] = np.nan
    for g in range(n_plis):
        test = (j["groupe"] == g).to_numpy()
        modele = modele_mos(graine=0)
        modele.fit(j.loc[~test, predicteurs],
                   j.loc[~test, "obs_jour"] - j.loc[~test, "cams_jour"])
        j.loc[test, "pred"] = j.loc[test, "cams_jour"] + modele.predict(j.loc[test, predicteurs])
        modeles[g] = modele
    print(f"  {len(modeles)} modèles ajustés · {time.time() - depart:.0f}s", flush=True)

    # ── Le second périmètre, ajusté sur les mêmes plis ────────────────────────
    # Le pipeline gelé du dossier ne joint ni l'observation à J−2, ni les membres, ni les
    # feux : il tourne **partout**, y compris là où aucune station n'existe. Le modèle
    # ci-dessus les utilise tous les trois, donc il ne vaut qu'au **périmètre instrumenté**.
    # Publier un seul des deux sous le nom « notre correction » fait passer le chiffre du
    # périmètre restreint pour celui du produit déployable. On calcule donc les deux.
    hors_national = {"observation à J−2", "membres d'ensemble", "exposition aux feux"}
    predicteurs_nat = [c for c in predicteurs
                       if not any(BLOCS[b](c) for b in hors_national if b in BLOCS)]
    if len(predicteurs_nat) == len(predicteurs):
        raise ControleEchec(
            "le périmètre national retient toutes les variables : les blocs temps réel "
            "ne sont pas reconnus, les deux produits seraient identiques")
    j["pred_nat"] = np.nan
    for g in range(n_plis):
        test = (j["groupe"] == g).to_numpy()
        m = modele_mos(graine=0)
        m.fit(j.loc[~test, predicteurs_nat],
              j.loc[~test, "obs_jour"] - j.loc[~test, "cams_jour"])
        j.loc[test, "pred_nat"] = (j.loc[test, "cams_jour"]
                                   + m.predict(j.loc[test, predicteurs_nat]))
    print(f"  périmètre national : {len(predicteurs_nat)} prédicteurs sur "
          f"{len(predicteurs)} · {time.time() - depart:.0f}s", flush=True)

    blocs = {nom: [c for c in predicteurs if test(c)] for nom, test in BLOCS.items()}
    blocs = {n: v for n, v in blocs.items() if v}
    orphelines = [c for c in predicteurs if not any(c in v for v in blocs.values())]
    if orphelines:
        print(f"  ⚠️ non classées : {orphelines[:6]}", flush=True)

    rng = np.random.default_rng(graine)
    lignes = []
    for mois, g in j.groupby("mois"):
        if len(g) < 200:
            continue
        base_err = float(np.sqrt(((g["obs_jour"] - g["pred"]) ** 2).mean()))
        for nom, variables in blocs.items():
            # Chaque pli est permuté puis prédit **par son propre modèle**, sur ses seules
            # lignes de test : référence et version permutée partagent alors l'estimateur, et
            # l'écart mesure bien l'apport du bloc.
            carres, effectif = 0.0, 0
            for pli, sous in g.groupby("groupe"):
                melange = sous.copy()
                # **Permuter à l'intérieur du mois**, jamais sur l'année : un mélange global
                # détruirait aussi la saison, et l'on mesurerait alors le calendrier partout.
                ordre = rng.permutation(len(melange))
                for c in variables:
                    melange[c] = melange[c].to_numpy()[ordre]
                perturbe = (melange["cams_jour"]
                            + modeles[pli].predict(melange[predicteurs]))
                carres += float(((melange["obs_jour"] - perturbe) ** 2).sum())
                effectif += len(melange)
            err = float(np.sqrt(carres / max(effectif, 1)))
            lignes.append({"mois": str(mois), "bloc": nom, "n": len(g),
                           "rmse_base": base_err, "rmse_permute": err,
                           "importance": err - base_err})
        print(f"  {mois} · {len(g):,} jours · {time.time() - depart:.0f}s", flush=True)

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/importance_temporelle_{polluant}.csv", index=False)

    # ── Les référentiels, mois par mois ───────────────────────────────────────
    # **Sur les mêmes lignes pour les trois produits.** Le MOS officiel ne couvre pas toutes
    # les stations ; comparer chacun sur sa propre couverture mesurerait la disponibilité du
    # produit officiel plutôt que sa qualité.
    produits = [("cams_jour", "CAMS brut"),
                ("pred_nat", "notre correction · partout"),
                ("pred", "notre correction · aux stations")]
    if "officiel_mos" in j.columns:
        produits.insert(1, ("officiel_mos", "MOS officiel Copernicus"))
    communes = j.dropna(subset=[c for c, _ in produits])
    perf = []
    for mois, g in communes.groupby("mois"):
        if len(g) < 200:
            continue
        for colonne, nom in produits:
            perf.append({"mois": str(mois), "produit": nom, "n": len(g),
                         "rmse": float(np.sqrt(((g["obs_jour"] - g[colonne]) ** 2).mean()))})
    perf = pd.DataFrame(perf)
    perf.to_csv(RACINE / f"reports/performance_mensuelle_{polluant}.csv", index=False)
    print(f"\nréférentiels sur {len(communes):,} lignes communes · "
          f"{perf['mois'].nunique()} mois")
    for nom, g in perf.groupby("produit"):
        # **Agrégation quadratique** : une RMSE est la racine d'une moyenne de carrés, donc
        # √(Σ nₘ·RMSEₘ²/Σ nₘ). La moyenne linéaire employée ici jusqu'au 31/07/2026
        # sous-estimait, et davantage les produits aux mois dispersés — donc CAMS brut plus
        # que nos corrections. Jumeau du défaut trouvé dans `verite_dossier.py`.
        poids = g["n"].to_numpy(dtype="float64")
        agregee = float(np.sqrt(np.sum(poids * g["rmse"].to_numpy() ** 2) / poids.sum()))
        print(f"  {nom:28s} RMSE agrégée {agregee:6.2f} · "
              f"pire mois {g['rmse'].max():6.2f} ({g.loc[g['rmse'].idxmax(), 'mois']})",
              flush=True)

    print(f"\n{'bloc':24s} {'moyenne':>9s} {'max':>8s} {'mois du max':>12s}")
    for nom, g in table.groupby("bloc"):
        pic = g.loc[g["importance"].idxmax()]
        print(f"{nom:24s} {g['importance'].mean():9.3f} {pic['importance']:8.3f} "
              f"{pic['mois']:>12s}", flush=True)
    print(f"\nÉcrit : reports/importance_temporelle_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--plis", type=int, default=3)
    p.add_argument("--graine", type=int, default=0)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis, args.graine))
