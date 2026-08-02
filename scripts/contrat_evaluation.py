#!/usr/bin/env python3
"""Le contrat d'évaluation — une partition gelée, scellée, et dont les consultations se comptent.

Le défaut que ce module existe pour supprimer
---------------------------------------------
L'audit externe R9 du 02/08/2026 conclut ainsi :

    « Le projet sait désormais détecter des erreurs locales, mais ne possède pas encore un
    contrat d'évaluation immuable. Sans ce contrat, chaque nouvelle correction augmente
    simultanément le modèle et la probabilité d'avoir adapté le protocole au corpus. »

Le même jour, la démonstration : un test de 90 stations déclaré « jamais consulté » a servi à
**choisir** entre 400 et 3 288 arbres. Il est devenu un jeu de validation par ce seul geste, et
personne ne l'a remarqué sur le moment. Ce n'est pas un manque de rigueur ponctuel — c'est
structurel : **rien dans le code ne distinguait un test d'un jeu de validation**, ni ne gardait
trace du nombre de fois qu'on l'avait regardé.

Ce que ce module apporte, et ce qu'il n'apporte pas
----------------------------------------------------
Il ne peut pas **empêcher** de consulter le test — aucun code ne le peut. Il fait la seule
chose qui vaille : **rendre chaque consultation visible et comptée**. Le journal
`reports/contrat/consultations.jsonl` enregistre qui a regardé, quand, avec quel modèle et
pour quel résultat. Une ligne de plus, c'est un degré de liberté de plus, et le dossier peut
alors dire *« ce chiffre a été lu à la troisième consultation »* au lieu de l'ignorer.

Le manifeste est **scellé** par une empreinte SHA-256 : toute modification de la partition,
même d'une station, change l'empreinte et invalide les mesures antérieures.

Les quatre cases — et une seule correspond à la revendication
---------------------------------------------------------------
Une prévision opérationnelle prédit **demain**, à une station **peut-être non instrumentée**.
Ni un découpage par stations ni un découpage par dates ne pose cette question. Il en faut deux,
croisés :

===============================  ==========================  ==========================
                                 **dates passées**           **dates futures**
===============================  ==========================  ==========================
**stations d'entraînement**      ① ajustement (référence)    ③ tenue dans le temps
**stations exclues + fossé**     ② transfert spatial         ④ **LA REVENDICATION**
===============================  ==========================  ==========================

Le projet a jusqu'ici publié la case ②. La case ④ est celle qu'il revendique et n'a jamais
mesurée. L'écart entre les deux **est** ce qu'un employeur a le droit de demander.

Deux produits, jamais confondus
--------------------------------
L'audit R9 relève la contradiction centrale du dossier : le plus fort levier, l'observation de
la veille (**+8,9 %**), n'existe **pas** là où rien ne mesure. Il appartient à la route
« station instrumentée mais exclue de l'apprentissage », pas à la route « lieu non instrumenté ».

Le contrat impose donc deux périmètres nommés, avec deux jeux de variables disjoints :

* ``AUX_STATIONS`` — retards autorisés (observation J−2, erreurs récentes, fraîcheur). Répond à
  *« corriger la prévision là où l'on mesure déjà »*.
* ``PARTOUT`` — aucune variable dérivée d'une observation au sol. Répond à *« prédire là où rien
  ne mesure »*. C'est le seul périmètre où la case ④ a un sens.

Ce que le contrat ne prétend pas résoudre
------------------------------------------
Le fossé spatial reste construit sur un **corrélogramme par tranches à seuil choisi** (0,10),
et non sur un variogramme ajusté avec incertitude. Le rayon est ici **figé une fois pour
toutes dans le manifeste**, ce qui le rend au moins immuable pour la suite — mais son origine
statistique reste ce qu'elle est, et le dossier doit le dire.

Usage :
  python3 scripts/contrat_evaluation.py --sceller          # crée le manifeste, une seule fois
  python3 scripts/contrat_evaluation.py --montrer          # affiche le contrat et le journal
Sortie : reports/contrat/manifeste.json · reports/contrat/consultations.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

DOSSIER = RACINE / "reports/contrat"
MANIFESTE = DOSSIER / "manifeste.json"
JOURNAL = DOSSIER / "consultations.jsonl"

GRAINE = 20260802
# Part des stations réservées au test spatial. Un tiers laisse assez de stations pour
# entraîner tout en donnant un test de taille mesurable.
PART_TEST = 1 / 3
# Longueur du bloc futur, en mois. Six mois plutôt que trois : la fenêtre d'évaluation de
# l'ozone au référentiel LCSQA est avril-septembre, et un bloc futur d'hiver ne mesurerait
# rien pour ce polluant.
MOIS_FUTURS = 6
# Rayon du fossé autour des stations de test, par polluant. ⚠️ Issu d'un **corrélogramme par
# tranches** avec seuil à 0,10 — première tranche dont la corrélation moyenne passe dessous.
# Ce n'est pas une portée de variogramme estimée avec incertitude, et 150 est une borne de
# tranche. Figé ici pour qu'il cesse au moins de bouger.
RAYON_KM = {"O3": 150.0, "PM25": 150.0, "NO2": 75.0, "PM10": 150.0}

PERIMETRES = {
    "AUX_STATIONS": "retards d'observation autorisés — corriger là où l'on mesure déjà",
    "PARTOUT": "aucune variable dérivée d'une observation au sol — prédire là où rien "
               "ne mesure",
}

CASES = {
    "1_ajustement": "stations d'entraînement × dates passées — référence, pas une mesure",
    "2_transfert_spatial": "stations exclues + fossé × dates passées",
    "3_tenue_temporelle": "stations d'entraînement × dates futures",
    "4_revendication": "stations exclues + fossé × dates futures — LA revendication",
}


def empreinte_sources() -> dict[str, str]:
    """Empreinte des fichiers dont dépend la partition.

    ⚠️ Portée limitée, et il faut le dire : l'empreinte porte sur le **nom et la taille** des
    gros fichiers, et sur le contenu complet des petits. Elle détecte une régénération ou un
    remplacement, **pas** une édition sur place de taille identique. C'est un garde-fou, pas
    une preuve d'intégrité.
    """
    sources = {}
    petits = [RACINE / "data/processed/stations.parquet"]
    gros = sorted((RACINE / "data/processed").glob("panel_*.parquet"))
    for f in petits:
        if f.exists():
            sources[f.name] = "sha256:" + hashlib.sha256(f.read_bytes()).hexdigest()[:32]
    for f in gros:
        sources[f.name] = f"taille:{f.stat().st_size}"
    if not sources:
        raise SystemExit("aucune source trouvée — sceller un contrat sur rien n'a pas de sens")
    return sources


def sceau(contenu: dict) -> str:
    """Empreinte du manifeste lui-même, calculée sur une sérialisation stable."""
    sans_sceau = {k: v for k, v in contenu.items() if k != "sceau"}
    brut = json.dumps(sans_sceau, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(brut).hexdigest()


def construire(polluants: list[str]) -> dict:
    """Construit la partition. **Ne s'exécute qu'une fois** — le manifeste est définitif."""
    from validation_bloquee import coordonnees, plis_spatiaux

    s = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                        columns=["station_id", "metropole", "active"])
    stations = np.sort(s[s["metropole"] & s["active"]]["station_id"].unique())

    # ── Partition spatiale : des GRAPPES entières partent en test, pas des stations
    #    tirées au hasard. Un tirage aléatoire laisserait chaque station de test entourée
    #    de voisines d'entraînement, ce qui est exactement le défaut qu'on veut supprimer.
    c = coordonnees(stations)
    n_groupes = max(3, int(round(1 / PART_TEST)))
    groupes = plis_spatiaux(c, n_groupes)
    st_test = np.sort(stations[groupes == 0])
    st_dev = np.sort(stations[groupes != 0])

    # ── Partition temporelle : le bloc futur est le suffixe du corpus, jamais un tirage.
    from fit_mos import charger  # noqa: PLC0415

    bornes = {}
    for p in polluants:
        j = charger(p, 1)
        t = pd.to_datetime(j["timestamp_utc"])
        if t.dt.tz is not None:
            t = t.dt.tz_localize(None)
        fin = t.max().normalize()
        coupure = (fin - pd.DateOffset(months=MOIS_FUTURS)).normalize()
        bornes[p] = {"debut": str(t.min().date()), "coupure": str(coupure.date()),
                     "fin": str(fin.date()),
                     "n_lignes": int(len(j)),
                     "n_stations": int(j["station_id"].nunique())}
        print(f"  {p} · corpus {t.min():%Y-%m-%d} → {fin:%Y-%m-%d} · "
              f"futur à partir du {coupure:%Y-%m-%d}")

    contenu = {
        "version": 1,
        "cree_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "graine": GRAINE,
        "part_test": PART_TEST,
        "mois_futurs": MOIS_FUTURS,
        "rayon_fosse_km": RAYON_KM,
        "origine_du_rayon": "corrélogramme par tranches, seuil 0,10 — PAS un variogramme "
                            "ajusté ; 150 km est une borne de tranche",
        "perimetres": PERIMETRES,
        "cases": CASES,
        "stations_test": [str(x) for x in st_test],
        "stations_dev": [str(x) for x in st_dev],
        "bornes_temporelles": bornes,
        "sources": empreinte_sources(),
    }
    contenu["sceau"] = sceau(contenu)
    return contenu


def charger_contrat() -> dict:
    """Charge le manifeste et **vérifie son sceau**. Refuse un contrat altéré."""
    if not MANIFESTE.exists():
        raise SystemExit(f"aucun contrat scellé — lancer d'abord :\n"
                         f"  python3 scripts/contrat_evaluation.py --sceller")
    contenu = json.loads(MANIFESTE.read_text(encoding="utf-8"))
    attendu = sceau(contenu)
    if contenu.get("sceau") != attendu:
        raise SystemExit(f"⚠️ SCEAU INVALIDE — le manifeste a été modifié après scellement.\n"
                         f"   attendu {attendu[:16]}… · trouvé "
                         f"{str(contenu.get('sceau'))[:16]}…\n"
                         f"   Toute mesure antérieure porte sur une AUTRE partition.")
    actuelles = empreinte_sources()
    derive = {k: (v, actuelles.get(k)) for k, v in contenu["sources"].items()
              if actuelles.get(k) != v}
    if derive:
        print(f"  ⚠️ {len(derive)} source(s) ont changé depuis le scellement :", flush=True)
        for k, (avant, apres) in derive.items():
            print(f"     {k} · {avant} → {apres}")
        print("     Les mesures sur ce contrat ne sont plus comparables aux précédentes.")
    return contenu


def journaliser(motif: str, perimetre: str, case: str, polluant: str,
                modele: str, resultat: dict) -> int:
    """Enregistre une consultation du test gelé. Rend le numéro de consultation.

    **C'est la fonction qui donne sa valeur au contrat.** On ne peut pas empêcher de regarder
    le test ; on peut compter les regards. Un résultat lu à la première consultation et un
    résultat lu à la quinzième n'ont pas la même valeur probante, et le dossier doit pouvoir
    dire lequel il présente.
    """
    DOSSIER.mkdir(parents=True, exist_ok=True)
    contrat = charger_contrat()
    precedentes = 0
    if JOURNAL.exists():
        precedentes = sum(1 for _ in JOURNAL.open(encoding="utf-8"))
    ligne = {
        "n": precedentes + 1,
        "quand": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sceau": contrat["sceau"][:16],
        "motif": motif, "perimetre": perimetre, "case": case,
        "polluant": polluant, "modele": modele, "resultat": resultat,
    }
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    return ligne["n"]


def decouper(j: pd.DataFrame, contrat: dict, polluant: str,
             case: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rend (entraînement, test) pour la case demandée, fossé compris.

    L'entraînement est **toujours** restreint aux stations de développement ET aux dates
    passées — quelle que soit la case. Seul le test bouge. C'est ce qui rend les quatre
    cases comparables entre elles : un seul ajustement, quatre lectures.
    """
    from validation_bloquee import coordonnees  # noqa: PLC0415

    if case not in CASES:
        raise SystemExit(f"case inconnue « {case} » — attendu {sorted(CASES)}")
    st_dev = set(contrat["stations_dev"])
    st_test = set(contrat["stations_test"])
    coupure = pd.Timestamp(contrat["bornes_temporelles"][polluant]["coupure"])

    jour = pd.to_datetime(j["jour"] if "jour" in j.columns else j["timestamp_utc"])
    if jour.dt.tz is not None:
        jour = jour.dt.tz_localize(None)
    passe = jour < coupure
    dans_dev = j["station_id"].isin(st_dev).to_numpy()

    entraine = dans_dev & passe.to_numpy()

    spatial = case in ("2_transfert_spatial", "4_revendication")
    futur = case in ("3_tenue_temporelle", "4_revendication")
    masque_test = (j["station_id"].isin(st_test) if spatial else pd.Series(dans_dev,
                                                                          index=j.index))
    masque_test = masque_test.to_numpy() & ((~passe).to_numpy() if futur
                                            else passe.to_numpy())

    if spatial:
        # Fossé : retirer de l'ENTRAÎNEMENT toute station trop proche d'une station de test.
        c = coordonnees(np.sort(j["station_id"].unique()))
        rayon = contrat["rayon_fosse_km"][polluant]
        ids = np.array(c.index)
        d = np.sqrt(((c.to_numpy()[:, None, :]
                      - c.loc[sorted(st_test & set(ids))].to_numpy()[None, :, :]) ** 2)
                    .sum(-1))
        proches = set(ids[d.min(axis=1) < rayon]) - st_test
        entraine &= ~j["station_id"].isin(proches).to_numpy()

    return j[entraine], j[masque_test]


def montrer() -> int:
    contrat = charger_contrat()
    print(f"CONTRAT D'ÉVALUATION · sceau {contrat['sceau'][:24]}…")
    print(f"  scellé le {contrat['cree_le']}")
    print(f"  {len(contrat['stations_dev'])} stations de développement · "
          f"{len(contrat['stations_test'])} de test (grappes spatiales entières)")
    print(f"  bloc futur : les {contrat['mois_futurs']} derniers mois")
    for p, b in contrat["bornes_temporelles"].items():
        print(f"    {p} · {b['debut']} → [{b['coupure']}] → {b['fin']}")
    print(f"  fossé : {contrat['rayon_fosse_km']}")
    print(f"  ⚠️ origine du rayon : {contrat['origine_du_rayon']}")
    print("\n  Périmètres :")
    for k, v in contrat["perimetres"].items():
        print(f"    {k:14s} {v}")
    print("\n  Cases :")
    for k, v in contrat["cases"].items():
        print(f"    {k:22s} {v}")

    n = sum(1 for _ in JOURNAL.open(encoding="utf-8")) if JOURNAL.exists() else 0
    print(f"\n{'─' * 78}\nCONSULTATIONS DU TEST GELÉ : {n}")
    if n == 0:
        print("  Le test n'a jamais été regardé. C'est le seul état où il vaut pleinement.")
    else:
        for ligne in JOURNAL.open(encoding="utf-8"):
            d = json.loads(ligne)
            print(f"  #{d['n']:2d} {d['quand'][:16]} · {d['polluant']:5s} · "
                  f"{d['case']:22s} · {d['perimetre']:12s} · {d['modele'][:28]:28s} · "
                  f"{d['motif'][:40]}")
        print(f"\n  ⚠️ {n} consultation(s) = {n} degré(s) de liberté. Un chiffre lu à la "
              f"{n}ᵉ lecture\n     n'a pas la valeur probante d'un chiffre lu à la première.")
    return 0


def main(sceller: bool, montrer_seul: bool, polluants: list[str]) -> int:
    if montrer_seul:
        return montrer()
    if not sceller:
        raise SystemExit("préciser --sceller ou --montrer")
    if MANIFESTE.exists():
        raise SystemExit(f"⚠️ un contrat existe déjà : {MANIFESTE.relative_to(RACINE)}\n"
                         f"   Il ne se re-scelle PAS. Re-partitionner après avoir vu des "
                         f"scores est\n   exactement ce que ce module existe pour empêcher. "
                         f"Pour repartir de zéro,\n   déplacer le manifeste À LA MAIN et "
                         f"considérer toutes les mesures antérieures\n   comme portant sur "
                         f"une autre partition.")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    print("Construction de la partition — une seule fois, définitivement.\n")
    contenu = construire(polluants)
    MANIFESTE.write_text(json.dumps(contenu, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"\nScellé : {MANIFESTE.relative_to(RACINE)}")
    print(f"  sceau {contenu['sceau'][:32]}…")
    print(f"  {len(contenu['stations_dev'])} dev · {len(contenu['stations_test'])} test")
    print("\nLe test n'a jamais été consulté. Chaque lecture sera comptée.")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--sceller", action="store_true")
    a.add_argument("--montrer", action="store_true")
    a.add_argument("--polluants", default="O3,NO2,PM25")
    n = a.parse_args()
    raise SystemExit(main(n.sceller, n.montrer, n.polluants.split(",")))
