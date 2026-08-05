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
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

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
    mois_obs = set(pd.PeriodIndex(pd.to_datetime(obs["timestamp_utc"]), freq="M").unique())
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


if __name__ == "__main__":
    import pyarrow.parquet as pq
    for p in ("O3", "NO2", "PM10", "PM25"):
        f = RACINE / f"data/processed/predictions/comparatif_{p}_h2.parquet"
        d = pd.read_parquet(f, columns=["mois"])
        annoncer(p, controle(p, sorted(d["mois"].unique())))
