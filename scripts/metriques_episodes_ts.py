#!/usr/bin/env python3
"""Évaluer la détection d'épisodes avec les métriques de la détection d'anomalies.

Le problème de mesure
---------------------
Nos scores de détection (POD, FAR, CSI) comparent, **jour par jour et station par station**,
un dépassement prévu à un dépassement observé. Un épisode détecté avec un jour de retard
compte donc pour **deux erreurs** : une non-détection et une fausse alerte.

Or un épisode de pollution n'est pas un événement ponctuel : il **dure**, monte et retombe,
et un décalage d'un jour sur sa détection n'a pas le même coût opérationnel qu'une absence
totale de détection. La littérature de détection d'anomalies en séries temporelles a
développé des métriques pour exactement ce cas — notamment le **VUS-PR** et les métriques
d'**affiliation**, qui tolèrent un décalage et raisonnent par **plages** plutôt que par points.

Ce script rejoue nos détections avec ces métriques. Il ne change aucun modèle : il change la
**règle de comptage**. Deux issues, toutes deux utiles :

- si les scores remontent nettement, notre POD de 0,239 hors échantillon sous-estimait la
  capacité réelle, et le diagnostic du test 2025 doit être nuancé ;
- s'ils ne bougent pas, la faiblesse est réelle et le constat tient tel quel.

**Ce que le script ne fait pas** : il ne remplace pas POD/FAR/CSI, qui restent les métriques
du référentiel LCSQA et donc celles qu'il faut publier. Il ajoute une lecture complémentaire,
et sert à savoir si notre mesure principale est trop sévère.

Usage : python3 scripts/metriques_episodes_ts.py [--polluant O3] [--source 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from scores_episodes import scores  # noqa: E402

SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0}


def metriques_ts(labels: np.ndarray, score: np.ndarray, fenetre: int = 3) -> dict:
    """Métriques de détection d'anomalies en séries temporelles, par station.

    `slidingWindow` vaut ici **3 jours** : c'est la durée typique d'un épisode de pollution,
    et c'est la tolérance temporelle qu'on accorde à la détection. La valeur par défaut de
    la bibliothèque (100) est calibrée pour des séries à haute fréquence et n'aurait aucun
    sens sur des jours.
    """
    from TSB_AD.evaluation.metrics import get_metrics

    if labels.sum() == 0 or labels.sum() == len(labels):
        return {}
    try:
        return get_metrics(score.astype(float), labels.astype(int), slidingWindow=fenetre)
    except Exception as erreur:  # noqa: BLE001 — une série dégénérée ne doit pas tout arrêter
        return {"erreur": type(erreur).__name__}


def charger(polluant: str, source: str) -> tuple[pd.DataFrame, str, list[tuple[str, str]]]:
    """Renvoie les prédictions **déjà au jour**, leur provenance, et les produits à comparer.

    Deux sources, deux formes. La période apprise est stockée à l'heure et doit être agrégée
    ici ; le test 2025 est produit directement en jours-station et porte en plus le MOS
    officiel, ce qui permet d'y opposer trois produits au lieu de deux.
    """
    if source == "2025":
        chemin = RACINE / f"reports/test_hors_echantillon_2025_detail_{polluant}.csv"
        if not chemin.exists():
            raise SystemExit(f"{chemin.name} absent — relancer "
                             f"test_hors_echantillon_2025.py (il écrit ce détail)")
        j = pd.read_csv(chemin, parse_dates=["jour"]).rename(
            columns={"obs_jour": "observe", "cams_jour": "cams"})
        produits = [("CAMS brut", "cams"), ("corrigé", "corrige")]
        if "officiel_mos" in j:
            produits.insert(1, ("MOS officiel", "officiel_mos"))
        j = j.dropna(subset=["observe"] + [c for _, c in produits])
        return j, "1ᵉʳ semestre 2025, hors fenêtre d'apprentissage", produits

    d = pd.read_csv(RACINE / f"reports/mos_{polluant}_J1.csv",
                    parse_dates=["timestamp_utc"]).dropna(
        subset=["observe", "cams", "corrige"])

    # Agrégation en maximum journalier 8 h, la grandeur réglementaire.
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
    return (j, "17 mois appris (validation par stations exclues)",
            [("CAMS brut", "cams"), ("corrigé", "corrige")])


def main(polluant: str, source: str, fenetre: int) -> int:
    j, description, produits = charger(polluant, source)
    seuil = SEUILS[polluant]

    print(f"{polluant} · {description}")
    print(f"  {len(j):,} jours-station · {j['station_id'].nunique()} stations · "
          f"tolérance temporelle {fenetre} jours\n", flush=True)

    # ── Comptage ponctuel : ce que nous publions aujourd'hui ──────────────────
    depasse = (j["observe"] >= seuil).to_numpy()
    print("Comptage PONCTUEL (jour par jour, notre mesure actuelle) :")
    print(f"{'produit':14s} {'POD':>6s} {'FAR':>6s} {'CSI':>6s}")
    for nom, col in produits:
        s = scores(depasse, (j[col] >= seuil).to_numpy())
        print(f"{nom:14s} {s['POD']:6.3f} {s['FAR']:6.3f} {s['CSI']:6.3f}", flush=True)

    # ── Comptage tolérant : par station, avec décalage admis ──────────────────
    print(f"\nComptage TOLÉRANT (VUS-PR et affiliation, ±{fenetre} jours), "
          f"moyenné par station :")
    resultats: dict[str, list[dict]] = {col: [] for _, col in produits}
    for _, g in j.groupby("station_id"):
        g = g.sort_values("jour")
        labels = (g["observe"] >= seuil).to_numpy().astype(int)
        if labels.sum() < 2 or len(g) < 30:
            continue
        for _, col in produits:
            # Le score est la **concentration prédite** : plus elle est haute, plus
            # l'épisode est probable. Aucun seuil n'est appliqué — c'est tout l'intérêt
            # d'une métrique de rang.
            m = metriques_ts(labels, g[col].to_numpy(), fenetre)
            if m and "erreur" not in m:
                resultats[col].append(m)

    reference = produits[0][1]
    if not any(resultats[c] for _, c in produits):
        print("  aucune station évaluable (trop peu d'épisodes par station)")
        return 0

    modele = next(v[0] for v in resultats.values() if v)
    cles = [k for k, v in modele.items() if isinstance(v, (int, float, np.floating))]
    effectifs = {c: len(v) for c, v in resultats.items()}
    print(f"  stations évaluées : "
          f"{', '.join(f'{n} {effectifs[c]}' for n, c in produits)}\n")

    entete = f"{'métrique':22s}" + "".join(f"{n:>13s}" for n, _ in produits)
    print(entete + f"{'écart':>9s}")
    lignes = []
    for cle in cles:
        moyennes = {c: float(np.mean([m[cle] for m in resultats[c] if cle in m]))
                    if resultats[c] else float("nan") for _, c in produits}
        # L'écart affiché oppose **notre** correction au CAMS brut, qui est la référence
        # du tableau ; les autres produits se lisent en colonne.
        ecart = moyennes["corrige"] - moyennes[reference]
        marque = " ←" if abs(ecart) > 0.02 else ""
        print(f"{cle:22s}" + "".join(f"{moyennes[c]:13.4f}" for _, c in produits)
              + f"{ecart:+9.4f}{marque}", flush=True)
        lignes.append({"metrique": cle, **{c: moyennes[c] for _, c in produits},
                       "ecart": ecart})

    suffixe = "" if source == "appris" else f"_{source}"
    sortie = RACINE / f"reports/metriques_episodes_ts_{polluant}{suffixe}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    print("Lecture : si l'écart corrigé − brut est franchement positif ici alors qu'il est "
          "faible\nen comptage ponctuel, notre métrique actuelle sous-estime la capacité "
          "réelle de détection.", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--source", default="appris", choices=("appris", "2025"))
    p.add_argument("--fenetre", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.source, args.fenetre))
