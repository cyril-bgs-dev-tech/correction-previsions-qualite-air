#!/usr/bin/env python3
"""Quand faut-il réentraîner ? Détecter la dérive dans l'espace du résidu.

Ce que le test précédent a établi
---------------------------------
`capteur_situation_anormale.py` a montré qu'un détecteur d'anomalies sur l'**état d'entrée**
est aveugle aux ruptures de la chaîne CAMS (55ᵉ et 48ᵉ percentile — le hasard). L'explication
est structurelle : une mise à jour du modèle amont change la **relation** entre `cams` et
l'observation, pas la **distribution** des entrées. C'est une dérive de *concept*, pas de
*covariables*.

L'instrument juste est donc un moniteur sur le **résidu** `observation − cams`. Il exige des
observations, donc il surveille *a posteriori* — ce n'est pas un capteur avant prévision, mais
il répond à une question qu'aucune AASQA n'a industrialisée : **quand le post-traitement
doit-il être réentraîné ?**

Le test, et le piège qu'il doit éviter
--------------------------------------
Mêmes dates que le test précédent, **fixées d'avance** : 13/11 et 03/12/2024.

**Le piège** : les deux ruptures tombent en novembre-décembre, et le résidu a une forte
structure saisonnière. Un détecteur naïf crierait « anomalie » sur l'hiver entier et
paraîtrait réussir. Le contrôle est donc obligatoire — on compare le rang des dates de rupture
parmi les jours **du même mois des autres années**, jamais parmi tous les jours.

Ce que le script mesure
-----------------------
1. le rang du signal aux dates déclarées, avec et sans contrôle saisonnier ;
2. la **latence de détection** — combien de jours après la rupture l'alarme se déclenche.
   C'est la seule mesure qui intéresse un service : savoir six mois plus tard qu'il fallait
   réentraîner n'a aucune valeur ;
3. le taux de fausses alarmes de la règle, sur toute la période.

Usage : python3 scripts/moniteur_residu.py [--polluant O3]
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

RUPTURES = [pd.Timestamp("2024-11-13"), pd.Timestamp("2024-12-03")]
REFERENCE = 28   # jours de la fenêtre de référence
COURANTE = 7     # jours de la fenêtre courante
LATENCE_MAX = 21  # au-delà, une détection n'a plus d'intérêt opérationnel


def serie_residu(polluant: str) -> pd.DataFrame:
    """Résidu journalier moyen sur le parc, au grain réglementaire.

    L'agrégation nationale est délibérée : une rupture de la chaîne CAMS touche toutes les
    stations à la fois, et moyenner divise le bruit par √n. Un moniteur par station serait
    plus sensible aux pannes locales — c'est un autre objet.
    """
    d = pd.read_csv(RACINE / f"reports/mos_{polluant}_J1.csv",
                    parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])
    d = d.sort_values(["station_id", "timestamp_utc"])
    d["jour"] = d["timestamp_utc"].dt.floor("D")
    for c in ("observe", "cams", "corrige"):
        d[c + "_8h"] = (d.groupby("station_id")[c]
                          .transform(lambda s: s.rolling(8, min_periods=6).mean()))
    j = (d.groupby(["station_id", "jour"])
           .agg(observe=("observe_8h", "max"), cams=("cams_8h", "max"),
                corrige=("corrige_8h", "max"), n=("timestamp_utc", "size"))
           .reset_index())
    j = j[j["n"] >= 18].dropna(subset=["observe", "cams", "corrige"])
    j["residu_brut"] = j["observe"] - j["cams"]
    j["residu_corrige"] = j["observe"] - j["corrige"]

    quotidien = (j.groupby("jour")
                  .agg(residu_brut=("residu_brut", "mean"),
                       residu_corrige=("residu_corrige", "mean"),
                       n_stations=("station_id", "nunique")).reset_index())
    quotidien["jour"] = pd.to_datetime(quotidien["jour"]).dt.tz_localize(None)
    return quotidien.sort_values("jour").reset_index(drop=True)


def statistique_rupture(serie: pd.Series) -> pd.Series:
    """Écart standardisé entre une fenêtre courante et la référence qui la précède.

    C'est la forme la plus simple d'un test de rupture de moyenne, et elle est **causale** :
    à chaque date, elle n'utilise que le passé. Un détecteur qui regarderait après la date
    serait inutilisable en surveillance — il faut pouvoir l'exécuter le matin même.
    """
    ref_moy = serie.shift(COURANTE).rolling(REFERENCE, min_periods=REFERENCE // 2).mean()
    ref_ect = serie.shift(COURANTE).rolling(REFERENCE, min_periods=REFERENCE // 2).std()
    courante = serie.rolling(COURANTE, min_periods=COURANTE - 2).mean()
    return (courante - ref_moy).abs() / ref_ect.replace(0, np.nan)


def rang_saisonnier(d: pd.DataFrame, colonne: str, date: pd.Timestamp,
                    fenetre: int = LATENCE_MAX) -> dict:
    """Rang du signal après une rupture, parmi les jours du **même mois** des autres années.

    Sans ce contrôle, un détecteur qui ne ferait que suivre la saison obtiendrait un rang
    excellent sur deux ruptures situées toutes deux en novembre-décembre.
    """
    apres = d[(d["jour"] >= date) & (d["jour"] <= date + pd.Timedelta(days=fenetre))]
    if apres.empty or apres[colonne].isna().all():
        return {}
    pic = float(apres[colonne].max())

    memes_mois = d[(d["jour"].dt.month == date.month)
                   & ~((d["jour"] >= date - pd.Timedelta(days=fenetre))
                       & (d["jour"] <= date + pd.Timedelta(days=fenetre)))]
    comparaison = memes_mois[colonne].dropna()
    tous = d[colonne].dropna()

    # Latence : premier jour où la statistique dépasse le 95ᵉ percentile de la référence
    # saisonnière. C'est la règle qu'un service appliquerait, pas une lecture après coup.
    seuil = float(comparaison.quantile(0.95)) if len(comparaison) >= 20 else float("nan")
    latence = np.nan
    if not np.isnan(seuil):
        franchi = apres[apres[colonne] >= seuil]
        if not franchi.empty:
            latence = int((franchi["jour"].iloc[0] - date).days)

    return {
        "date": date.date().isoformat(), "pic": pic,
        "rang_global": float((tous < pic).mean() * 100),
        "rang_saisonnier": float((comparaison < pic).mean() * 100)
        if len(comparaison) >= 20 else float("nan"),
        "n_comparaison": len(comparaison), "seuil_95": seuil, "latence_j": latence,
    }


def main(polluant: str) -> int:
    depart = time.time()
    d = serie_residu(polluant)
    print(f"{polluant} · {len(d)} jours · {d['jour'].min():%d/%m/%Y} → "
          f"{d['jour'].max():%d/%m/%Y} · {d['n_stations'].median():.0f} stations par jour\n",
          flush=True)

    for source in ("residu_brut", "residu_corrige"):
        d["stat_" + source] = statistique_rupture(d[source])

    lignes = []
    for source, libelle in (("residu_brut", "résidu de CAMS brut"),
                            ("residu_corrige", "résidu après correction")):
        col = "stat_" + source
        print(f"── {libelle} ──")
        print(f"{'rupture':12s} {'pic':>7s} {'rang global':>12s} "
              f"{'rang saisonnier':>16s} {'latence':>9s}")
        for date in RUPTURES:
            r = rang_saisonnier(d, col, date)
            if not r:
                continue
            lat = f"{r['latence_j']} j" if not np.isnan(r["latence_j"]) else "jamais"
            print(f"{r['date']:12s} {r['pic']:7.2f} {r['rang_global']:11.0f}ᵉ "
                  f"{r['rang_saisonnier']:15.0f}ᵉ {lat:>9s}", flush=True)
            lignes.append({"source": source, **r})

        # **Une seule règle, calibrée sur l'historique** — c'est ce qu'un service déploierait.
        # Moyenner deux seuils dérivés chacun d'une référence saisonnière différente produisait
        # des chiffres incohérents : une rupture pouvait afficher une latence de 5 jours et
        # n'être comptée dans aucune alarme.
        seuil = float(d[col].quantile(0.95))
        alarmes = d[d[col] >= seuil]
        proche = pd.Series(False, index=alarmes.index)
        for date in RUPTURES:
            proche |= ((alarmes["jour"] >= date)
                       & (alarmes["jour"] <= date + pd.Timedelta(days=LATENCE_MAX)))
        n_jours = int(d[col].notna().sum())
        print(f"  règle unique « stat ≥ {seuil:.2f} » (95ᵉ percentile de l'historique) : "
              f"{len(alarmes)} alarmes\n  sur {n_jours} jours — une tous les "
              f"{n_jours / max(len(alarmes), 1):.0f} jours — dont {int(proche.sum())} "
              f"dans les {LATENCE_MAX} j\n  suivant une rupture déclarée.")

        # **La taille de l'effet décide de ce qui est atteignable**, et vaut mieux qu'un
        # verdict : elle dit combien de jours d'accumulation seraient nécessaires.
        for date in RUPTURES:
            avant = d[(d["jour"] >= date - pd.Timedelta(days=28)) & (d["jour"] < date)][source]
            apres = d[(d["jour"] >= date)
                      & (d["jour"] <= date + pd.Timedelta(days=28))][source]
            if len(avant) < 10 or len(apres) < 10:
                continue
            saut = float(apres.mean() - avant.mean())
            bruit = float(d[source].diff().std())
            # n pour distinguer un décalage `saut` du bruit quotidien à 95 % / puissance 80 %
            besoin = (2 * 1.96 * bruit / saut) ** 2 if saut else float("inf")
            print(f"    {date.date()} · décalage du résidu {saut:+.2f} µg/m³ · bruit "
                  f"quotidien σ={bruit:.2f} → **{besoin:.0f} jours** d'accumulation "
                  f"nécessaires")
        print(flush=True)

    table = pd.DataFrame(lignes)
    table.to_csv(RACINE / f"reports/moniteur_residu_{polluant}.csv", index=False)
    d.to_csv(RACINE / f"reports/moniteur_residu_{polluant}_serie.csv", index=False)

    print("=" * 74)
    brut = table[table["source"] == "residu_brut"]
    if not brut.empty:
        rangs = brut["rang_saisonnier"].dropna()
        detecte = int((rangs >= 90).sum())
        print(f"Sur le résidu de CAMS brut, {detecte} rupture(s) sur {len(rangs)} dépassent "
              f"le 90ᵉ percentile\nsaisonnier.", end=" ")
        if detecte == len(rangs) and len(rangs) > 0:
            print("→ **la dérive est détectable dans l'espace du résidu**, là où elle "
                  "était\ninvisible sur l'état d'entrée.")
        elif detecte:
            print("→ détection **partielle** : le signal existe mais n'est pas fiable sur "
                  "les deux cas.")
        else:
            print("→ **aucune détection** : même en espace résidu, ces ruptures ne se voient "
                  "pas\nsur un parc agrégé.")
    print(f"\nÉcrit : reports/moniteur_residu_{polluant}.csv · {time.time() - depart:.0f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    args = p.parse_args()
    raise SystemExit(main(args.polluant))
