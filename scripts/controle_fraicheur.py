#!/usr/bin/env python3
"""Un artefact périmé ne se distingue pas d'un artefact complet — sauf si on le compare.

Le défaut que ce module empêche de revenir
---------------------------------------------
Le 05/08/2026, les pages 04 et 05 ont été publiées sur `comparatif_<polluant>_h2.parquet`
en croyant décrire le corpus entier. Elles décrivaient **24 mois sur 37** pour le NO₂ —
août 2025 à août 2026 manquaient. Rien ne l'avait signalé : le fichier s'ouvrait, ses
colonnes étaient toutes là, ses chiffres étaient cohérents. Le trou n'a été vu que parce
qu'un lecteur a demandé « on n'a pas les 12 mois de 2025 ? ».

C'est exactement le motif que `CLAUDE.md` § 4 décrit : **l'attendu venait d'ailleurs que de
la demande**. L'artefact était son propre juge, et un script ne peut pas s'auditer sur une
hypothèse qu'il porte lui-même.

Ce que fait ce module
-----------------------
Il calcule l'attendu **depuis les sources**, jamais depuis l'artefact :

* les mois où des **observations** existent pour ce polluant, lus dans le panel ;
* les bornes des **prévisions**, lues dans les données et non dans les noms de fichiers
  (§ 4 bis : un nom groupé `..._202601_202602.parquet` porte deux mois).

L'intersection est ce que l'appariement pourrait produire aujourd'hui. Tout mois présent
là et absent de l'artefact est un **mois perdu en silence**, nommé un par un.

Et le résultat ne va pas seulement dans un journal : il est **écrit dans la page**, pour
qu'un lecteur voie le manque sans avoir à le deviner.
"""

from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
sys.path.insert(0, str(RACINE / "src"))

from aq.harmonize.timegrid import mois_couverts  # noqa: E402

PANEL = RACINE / "data/processed/panel_unifie_lcsqa.parquet"


def _court(polluant: str) -> str:
    """Le nom court de l'espèce, pris dans la table du projet et non recodé ici."""
    from fit_mos import ESPECES  # noqa: PLC0415
    for c, (p, _) in ESPECES.items():
        if p == polluant:
            return c
    raise SystemExit(f"espèce inconnue : {polluant}")


def _bornes_previsions(court: str) -> tuple[pd.Period, pd.Period]:
    """Bornes lues **dans les données**. Les noms ne servent qu'à ordonner les fichiers."""
    fichiers = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_*.parquet")))
    if not fichiers:
        raise SystemExit(f"aucune prévision pour {court}")
    t0 = pd.read_parquet(fichiers[0], columns=["timestamp_utc"])["timestamp_utc"].min()
    t1 = pd.read_parquet(fichiers[-1], columns=["timestamp_utc"])["timestamp_utc"].max()
    # ⚠️ La dernière échéance déborde sur le mois suivant : une sortie du 30 juillet à
    # 72 h touche le 2 août. Compter août comme un mois de prévision ferait réclamer un
    # mois qui n'existe qu'à hauteur de deux journées. On retire donc l'échéance maximale.
    return pd.Period(t0, freq="M"), pd.Period(t1 - pd.Timedelta(hours=72), freq="M")


def controle(polluant: str, mois_artefact: list[str]) -> dict:
    """Compare le corpus d'un artefact à ce que les sources permettraient aujourd'hui."""
    court = _court(polluant)
    p0, p1 = _bornes_previsions(court)
    obs = pd.read_parquet(PANEL, columns=["timestamp_utc"],
                          filters=[("polluant", "==", polluant)])
    mois_obs = mois_couverts(obs["timestamp_utc"])
    dispo = {str(m) for m in mois_obs if p0 <= m <= p1}
    presents = set(mois_artefact)
    manquants = sorted(dispo - presents)
    # Un mois présent dans l'artefact et absent des sources signale l'inverse : une
    # source amputée depuis la construction. Aussi anormal, et jamais regardé.
    inattendus = sorted(presents - dispo)
    return {"n_dispo": len(dispo), "n_present": len(presents),
            "manquants": manquants, "inattendus": inattendus,
            "fenetre_previsions": [str(p0), str(p1)]}


def empreinte(polluant: str, horizon: int = 2, suffixe: str = "") -> dict:
    """Identifie la **version** de l'artefact lu, pour que deux pages ne divergent pas.

    Le 05/08, l'autre agent régénérait les comparatifs pendant que ces générateurs les
    lisaient : la page 04 a lu un ozone à 25 mois et la page 05, deux minutes plus tard,
    le même ozone à 35 mois. Les deux pages étaient justes séparément et incohérentes
    ensemble. Une empreinte par polluant rend cette divergence détectable à l'injection.
    """
    f = (RACINE /
         f"data/processed/predictions/comparatif_{polluant}_h{horizon}{suffixe}.parquet")
    st = f.stat()
    return {"octets": st.st_size, "horodatage": int(st.st_mtime)}


def annoncer(polluant: str, c: dict) -> None:
    """Une ligne lisible dans le journal du lot — jamais filtrée sur le succès."""
    if c["manquants"]:
        print(f"   ⚠️ CORPUS TRONQUÉ · {polluant} : {c['n_present']} mois dans l'artefact "
              f"sur {c['n_dispo']} disponibles — manquent "
              f"{', '.join(c['manquants'][:6])}"
              f"{' …' if len(c['manquants']) > 6 else ''}")
    else:
        print(f"   ✓ corpus complet · {polluant} : {c['n_present']} mois, "
              f"aucun mois disponible non utilisé")
    if c["inattendus"]:
        print(f"   ⚠️ {polluant} : {len(c['inattendus'])} mois présents dans l'artefact "
              f"mais absents des sources — {', '.join(c['inattendus'][:6])}")


FIGURES = RACINE / "reports/figures"
SCRIPTS = RACINE / "scripts"
MOTIF_JSON = re.compile(r"p(\d+)_donnees\.json")
MOTIF_SORTIE = re.compile(r"Sortie\s*:.*?p(\d+)_donnees\.json")


def _gouvernants() -> dict[str, dict[str, list[Path]]]:
    """Pour chaque `p<N>_donnees.json`, ce dont il dérive — déduit, jamais codé en dur.

    Chaque générateur déclare lui-même sa sortie en en-tête (`Sortie : …p<N>_donnees.json`).
    Tout **autre** `p<N>_donnees.json` qu'il cite est une **entrée** : c'est ainsi que
    `page_synthese.py`, qui lit p4 et p6 pour produire p0, se range de lui-même en dernier.
    """
    gouv: dict[str, dict[str, list[Path]]] = {}
    for script in sorted(SCRIPTS.glob("page_*.py")):
        texte = script.read_text(encoding="utf-8")
        sortie = MOTIF_SORTIE.search(texte)
        if not sortie:
            continue
        n = sortie.group(1)
        cite = {m.group(1) for m in MOTIF_JSON.finditer(texte)} - {n}
        gouv[n] = {
            "generateur": [script],
            "fragments": sorted(FIGURES.glob(f"_p{n}_*")),
            "entrees": [FIGURES / f"p{m}_donnees.json" for m in sorted(cite)],
        }
    return gouv


def desynchronisations() -> tuple[list[str], list[str]]:
    """Un `p<N>_donnees.json` désaccordé d'avec ce qui le gouverne — le défaut **muet**.

    Rend deux listes séparées, parce qu'elles n'ont pas le même poids : les **manques**
    (une clé lue et absente) font échouer le contrôle, les **retards** d'horodatage ne
    sont qu'un indice — éditer la prose d'un fragment ne périme pas ses données.

    ⚠️ **Le trou par lequel la coupure du 06/08/2026 est passée.** `page_decision_reelle.py`
    avait gagné sa signature à 02 h 18 et `_p6_section.html` avait retiré « Échéance J0 » de
    la prose pour la laisser au script ; le générateur n'a jamais été relancé et
    `p6_donnees.json` datait de la veille, sans la clé. Le garde `if (sg && hs)` a fait le
    reste : **pas d'erreur de console, pas de bloc vide, juste l'échéance disparue** de la
    seule page dont l'échéance diffère de toutes les autres.

    Ce module contrôlait la couverture du corpus et **rien d'autre** : aucun contrôle ne
    comparait un `.json` à son générateur. Trois dépendances sont vérifiées ici, et la
    troisième est celle qui impose l'**ordre** de la chaîne :

    1. le `.json` doit être plus récent que le `page_*.py` qui le produit ;
    2. plus récent que ses **fragments** `_p<N>_{section.html,style.css,script.js}` — c'est
       la dépendance exacte qui a manqué le 06/08 ;
    3. plus récent que les `.json` dont il **dérive** (p0 lit p4 et p6, donc vient après).
    """
    manques: list[str] = []          # le défaut réel : une clé lue qui n'existe pas
    retards: list[str] = []          # l'indice : un gouvernant plus récent que sa sortie
    for n, dep in sorted(_gouvernants().items(), key=lambda kv: int(kv[0])):
        cible = FIGURES / f"p{n}_donnees.json"
        if not cible.exists():
            manques.append(f"p{n}_donnees.json ABSENT — générateur "
                           f"{dep['generateur'][0].name} jamais lancé")
            continue

        # ① Le contrôle exact : chaque `D.<clé>` lue par le fragment doit exister.
        presentes = set(json.loads(cible.read_text(encoding="utf-8")))
        for js in dep["fragments"]:
            if js.suffix != ".js":
                continue
            for cle in sorted(_cles_lues(js) - presentes):
                manques.append(f"p{n} : {js.name} lit **D.{cle}**, absente de "
                               f"{cible.name} — relancer {dep['generateur'][0].name}")

        # ② L'indice de désynchronisation, plus large et donc plus bavard.
        age = cible.stat().st_mtime
        for role, chemins in dep.items():
            for source in chemins:
                if not source.exists():
                    manques.append(f"p{n} : {role} manquant — {source.name}")
                elif source.stat().st_mtime > age:
                    retards.append(
                        f"p{n}_donnees.json est plus vieux que son {role[:-1]} "
                        f"{source.name} ({(source.stat().st_mtime - age) / 60:.0f} min)")
    return manques, retards


MOTIF_OBJET = re.compile(r"(?:var|let|const)\s+(\w+)\s*=\s*JSON\.parse\(")


def _cles_lues(js: Path) -> set[str]:
    """Les clés que ce fragment lit réellement dans le JSON injecté.

    Le fragment fait `var D = JSON.parse(n.textContent)` puis `D.<clé>` : on relève les
    accès sur ce nom-là. C'est le contrôle qui aurait attrapé le 06/08 — `D.signature`
    lue par `_p6_script.js`, absente de `p6_donnees.json`, et le garde `if (sg && hs)`
    qui transformait le manque en silence au lieu d'une erreur de console.
    """
    texte = js.read_text(encoding="utf-8")
    objet = MOTIF_OBJET.search(texte)
    if not objet:
        return set()
    return set(re.findall(rf"\b{re.escape(objet.group(1))}\.([A-Za-z_]\w*)", texte))


if __name__ == "__main__":
    import pyarrow.parquet as pq
    for p in ("O3", "NO2", "PM10", "PM25"):
        f = RACINE / f"data/processed/predictions/comparatif_{p}_h2.parquet"
        d = pd.read_parquet(f, columns=["mois"])
        annoncer(p, controle(p, sorted(d["mois"].unique())))

    print("\n── synchronisation des pages ─────────────────────────────────────")
    manques, retards = desynchronisations()
    for a in manques:
        print(f"   🔴 {a}")
    for a in retards:
        print(f"   ⚠️ {a}")
    if not manques:
        print(f"   ✓ {len(_gouvernants())} pages : aucune clé lue n'est absente de son JSON"
              + (f" ({len(retards)} retard(s) d'horodatage, à vérifier sans urgence)"
                 if retards else ""))
    raise SystemExit(1 if manques else 0)
