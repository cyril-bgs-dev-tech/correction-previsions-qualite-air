#!/usr/bin/env python3
"""L'observation récente — le prédicteur que nous avons exclu par un raisonnement trop large.

Ce qui a été confondu
---------------------
Le projet exclut la météo de réanalyse parce qu'elle **n'existe pas** à l'heure d'émission.
Il a exclu les observations récentes **par le même geste**. Ce n'est pas le même raisonnement :
ERA5 décrit le présent depuis le futur, tandis que la mesure d'avant-hier est là, publiée, et
que le MOS officiel de Copernicus **s'en sert** — sa documentation le dit.

Nous avons donc peut-être écarté, par excès de prudence, le prédicteur le plus fort du domaine :
la persistance du biais local.

Ce que ce test change — et ce n'est pas qu'un score
---------------------------------------------------
Une observation passée n'existe **qu'aux stations instrumentées**. L'ajouter scinde le projet
en deux usages qui n'ont ni le même périmètre ni la même valeur :

| usage | entrées | ce qu'on peut prétendre |
|---|---|---|
| **A — corriger aux stations** | CAMS + terrain + calendrier **+ observations passées** | comparable au MOS officiel, sur son terrain |
| **B — prédire là où rien ne mesure** | CAMS + terrain + calendrier | la seule revendication propre du projet |

Le test mesure A. **Il ne remplace pas B**, et présenter le gain de A comme celui du projet
serait un glissement de périmètre — exactement ce qu'une relecture a reproché à « station
inconnue », qui signifie *autre station du même réseau* et non *lieu quelconque*.

La règle de disponibilité, choisie conservatrice
------------------------------------------------
La prévision qui couvre le jour J est émise la veille. Les mesures de J−1 ne sont donc pas
toutes publiées, et celles qui le sont ne sont pas validées. On ne retient que les observations
jusqu'à la **fin de J−2**, soit un décalage d'au moins 24 h sur l'émission. C'est plus strict
que ce que fait le produit officiel ; si le gain existe sous cette contrainte, il existe *a
fortiori* sous une règle plus permissive.

Usage : python3 scripts/apport_observation_veille.py [--polluant O3]
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

from aq.eval.critere import seuil  # noqa: E402
from apport_meteo import evaluer, ic_difference, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

DECALAGE = 2  # jours : on n'utilise rien de plus récent que la fin de J−2
# Le critère de rétention vit dans `aq.eval.critere` : **relatif au RMSE de base**,
# donc comparable entre polluants. L'ancien 0,3 µg/m³ absolu valait 2 % sur le NO₂
# et 11 % sur les PM2,5 — il écartait ces dernières par artefact d'unité.


def variables_passees(j: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Observations et erreurs de CAMS antérieures, décalées de `DECALAGE` jours.

    Le décalage est appliqué **par station** sur une série réindexée au jour calendaire :
    un simple `shift(n)` sur des lignes trouées prendrait « l'enregistrement n lignes plus
    haut », qui peut dater de trois semaines si la station a été en panne. C'est la même
    faute que de déduire une fenêtre d'un nom de fichier — on lit la donnée, pas sa position.
    """
    d = j[["station_id", "jour", "obs_jour", "cams_jour"]].copy()
    d["jour"] = pd.to_datetime(d["jour"])
    d["erreur_cams"] = d["obs_jour"] - d["cams_jour"]

    morceaux = []
    for station, g in d.groupby("station_id", sort=False):
        g = g.set_index("jour").sort_index()
        complet = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="D"))
        passe = complet[["obs_jour", "erreur_cams"]].shift(DECALAGE)
        sortie = pd.DataFrame(index=complet.index)
        sortie["obs_j_moins"] = passe["obs_jour"]
        sortie["err_j_moins"] = passe["erreur_cams"]
        # Moyennes des jours antérieurs : la persistance d'un biais se lit mieux sur
        # plusieurs jours que sur un seul, qui peut être atypique.
        for n in (3, 7):
            sortie[f"obs_moy_{n}j"] = passe["obs_jour"].rolling(n, min_periods=2).mean()
            sortie[f"err_moy_{n}j"] = passe["erreur_cams"].rolling(n, min_periods=2).mean()
        sortie["err_ecart_7j"] = passe["erreur_cams"].rolling(7, min_periods=3).std()
        # **La fraîcheur est une variable, pas un détail.** Une station en panne depuis dix
        # jours fournit une valeur ancienne ; le modèle doit pouvoir en tenir compte plutôt
        # que de la traiter comme une mesure d'avant-hier.
        age = pd.Series(np.arange(len(complet)), index=complet.index)
        dernier = age.where(complet["obs_jour"].notna()).ffill()
        sortie["fraicheur_j"] = (age - dernier + DECALAGE).clip(upper=30)
        sortie["station_id"] = station
        morceaux.append(sortie.reset_index(names="jour"))

    passees = pd.concat(morceaux, ignore_index=True)
    noms = [c for c in passees.columns if c not in ("station_id", "jour")]
    return passees, noms


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    passees, noms = variables_passees(j)
    j["jour"] = pd.to_datetime(j["jour"])
    avant = len(j)
    j = j.merge(passees, on=["station_id", "jour"], how="left")
    couverture = float(j["obs_j_moins"].notna().mean())
    j = j.dropna(subset=["obs_j_moins", "err_j_moins"])
    print(f"{polluant} · {avant:,} → {len(j):,} jours-station "
          f"({100 * couverture:.1f} % ont une observation à J−{DECALAGE}) · "
          f"{j['station_id'].nunique()} stations", flush=True)
    print(f"  fraîcheur médiane {j['fraicheur_j'].median():.0f} j · "
          f"90ᵉ centile {j['fraicheur_j'].quantile(0.9):.0f} j", flush=True)

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})

    jeux = {"B — sans observation": base, "A — avec observations passées": base + noms}
    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:30s} {len(predicteurs):3d} var · RMSE {resultats[nom]['rmse']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    print(f"\n{'usage':30s} {'RMSE':>7s} {'décile haut':>12s} {'POD':>7s} {'CSI':>7s}")
    for nom, r in resultats.items():
        print(f"{nom:30s} {r['rmse']:7.3f} {r['rmse_decile_haut']:12.3f} "
              f"{r.get('POD', np.nan):7.3f} {r.get('CSI', np.nan):7.3f}", flush=True)

    ref, avec = resultats["B — sans observation"], resultats["A — avec observations passées"]
    gain = ref["rmse"] - avec["rmse"]
    bas, haut = ic_difference(predictions["B — sans observation"],
                              predictions["A — avec observations passées"])
    print(f"\n{'─' * 74}")
    print(f"gain {gain:+.3f} µg/m³ ({100 * gain / ref['rmse']:+.1f} % relatif) · "
          f"IC95 [{bas:+.3f} ; {haut:+.3f}] · décile haut "
          f"{avec['rmse_decile_haut'] - ref['rmse_decile_haut']:+.3f}")
    print(f"→ {'écart établi' if bas > 0 else 'IC contenant zéro'} · "
          f"{'au-dessus' if gain >= seuil(ref['rmse']) else 'sous'} le critère relatif "
          f"de {seuil(ref['rmse']):.3f} µg/m³ (2 % du RMSE de base)")
    print("\n⚠️ Périmètre : ce gain vaut pour l'usage **A**, corriger aux stations "
          "instrumentées.\n   Il ne s'applique pas à l'usage B — prédire là où rien ne "
          "mesure — qui reste\n   la seule revendication propre du projet. Ne jamais citer "
          "l'un pour l'autre.")

    pd.DataFrame(resultats).T.to_csv(
        RACINE / f"reports/apport_observation_veille_{polluant}.csv")
    pd.DataFrame([{"polluant": polluant, "gain": gain, "relatif_pct": 100 * gain / ref["rmse"],
                   "ic_bas": bas, "ic_haut": haut, "couverture": couverture,
                   "decalage_j": DECALAGE}]).to_csv(
        RACINE / f"reports/apport_observation_veille_{polluant}_ic.csv", index=False)
    print(f"\nÉcrit : reports/apport_observation_veille_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
