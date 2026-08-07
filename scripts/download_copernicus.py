"""Télécharge les champs Copernicus mois par mois, de façon reprenable.

Usage : python scripts/download_copernicus.py --service era5 --debut 2019-01 --fin 2024-12
Sortie : data/raw/era5/era5_{instantane,cumule}_AAAAMM.nc  (ou cams_prevision/…)

ERA5 donne **deux fichiers par mois**, un par nature de grandeur : les champs
instantanés valent à l'heure estampillée, les champs cumulés totalisent l'heure
écoulée. Les demander ensemble fait livrer une archive ZIP sous une extension `.nc`.

**Les mois sont traités du plus récent au plus ancien.** Un téléchargement de
plusieurs heures doit rendre exploitable sa fraction déjà faite : la fenêtre
d'évaluation (2023-2024) arrive donc en premier, et une interruption ne coûte que
de l'historique d'apprentissage.

Chaque fichier est **vérifié après écriture**, puis seulement renommé à son nom
définitif. Un fichier tronqué par une coupure réseau s'ouvre parfois sans erreur et
livre des champs partiels : le détecter plus tard, dans un modèle, coûterait bien
plus cher qu'ici.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from aq.ingest import copernicus as cop  # noqa: E402

# Requêtes simultanées. **Mesuré : 3 passe, 6 ne passe pas.** Au-delà de la limite de
# tâches actives du compte, le service ne met pas en attente — il met les soumissions
# excédentaires à l'état `rejected`, et le client échoue ensuite en HTTP 400 en allant
# chercher leurs résultats. Le message ne mentionne ni quota ni concurrence, si bien
# que le vrai motif ne se lit que dans la liste des tâches (`get_jobs`).
REQUETES_PARALLELES = 3

# Le rejet étant transitoire, on réessaie plutôt que de perdre le mois. Les attentes
# sont longues à dessein : réessayer tout de suite ne fait que se faire rejeter à
# nouveau, en consommant une place dans la file.
ATTENTES_REPRISE = (120, 420, 900)

SERVICES = {
    "era5": (cop.URL_CDS, cop.JEU_ERA5),
    "cams_prevision": (cop.URL_ADS, cop.JEU_CAMS_PREVISION),
    "cams": (cop.URL_ADS, cop.JEU_CAMS_REANALYSE),
}


def lire_cle(chemin: Path = Path.home() / ".cdsapirc") -> str:
    """Lit le jeton depuis `~/.cdsapirc`.

    La clé ne vit jamais dans le dépôt : un jeton versionné reste dans l'historique
    même après suppression, et celui-ci ouvre l'accès aux deux services.
    """
    if not chemin.exists():
        raise SystemExit(f"{chemin} absent — voir ACCES.md pour la configuration.")
    for ligne in chemin.read_text().splitlines():
        if ligne.strip().startswith("key:"):
            return ligne.split(":", 1)[1].strip()
    raise SystemExit(f"Aucune ligne 'key:' dans {chemin}")


def plan_du_plus_recent(service: str, debut: date, fin: date) -> list[tuple[str, dict]]:
    """Plan de téléchargement, mois les plus récents d'abord.

    Le tri porte sur le `AAAAMM` extrait du nom, **pas** sur le nom entier : ERA5 produit
    deux fichiers par mois (`era5_instantane_…`, `era5_cumule_…`), et un tri
    alphabétique les séparerait en deux blocs. Une interruption laisserait alors des
    mois pourvus d'un seul de leurs deux flux — inexploitables.
    """
    plan = cop.plan_telechargement(debut, fin, service=service)
    return sorted(plan, key=lambda entree: (entree[0].rsplit("_", 1)[-1], entree[0]),
                  reverse=True)


def depaqueter(archive_zip: Path, destination: Path) -> list[Path]:
    """Extrait une archive CAMS en ses membres journaliers.

    Les prévisions CAMS arrivent **zippées, un netCDF par jour de prévision**
    (`ENS_FORECAST_AAAA-MM-JJ.nc`). Dans chaque membre, la coordonnée `time` vaut 0 à 72 :
    c'est l'**échéance en heures**, pas un horodatage. La date de base ne figure que dans
    le NOM du fichier — la perdre en fusionnant les membres rendrait les prévisions
    inexploitables, et rien ne le signalerait.
    """
    import zipfile

    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_zip) as archive:
        membres = [m for m in archive.namelist() if m.endswith(".nc")]
        archive.extractall(destination, members=membres)
    return [destination / m for m in membres]


def verifier(chemin: Path, service: str) -> str | None:
    """Renvoie un message d'erreur si le fichier est inexploitable, sinon `None`.

    On contrôle la structure, pas seulement l'ouverture : un fichier qui s'ouvre mais
    ne contient qu'une poignée d'heures est le cas dangereux, parce qu'il se propage
    silencieusement jusqu'aux métriques.
    """
    import zipfile

    import xarray as xr

    # Une ARCHIVE ZIP sous extension `.nc` est le cas normal pour CAMS (un membre par
    # jour de prévision) et le cas ANORMAL pour ERA5 (requête mêlant champs instantanés
    # et cumulés). Sans ce test, l'erreur remonte en « ValueError » opaque.
    if zipfile.is_zipfile(chemin):
        if service == "era5":
            with zipfile.ZipFile(chemin) as archive:
                return (f"archive ZIP et non netCDF ({archive.namelist()}) — la requête "
                        "mélange des flux instantanés et cumulés")
        return None  # CAMS : l'archive est dépaquetée par l'appelant

    try:
        jeu = xr.open_dataset(chemin)
    except Exception as exc:  # noqa: BLE001
        return f"illisible ({type(exc).__name__})"

    with jeu:
        if not jeu.data_vars:
            return "aucune variable"
        axe_temps = next(
            (c for c in ("valid_time", "time", "forecast_period") if c in jeu.sizes),
            None,
        )
        if axe_temps is None:
            return f"aucun axe temporel parmi {list(jeu.sizes)}"
        # Un mois horaire complet fait 672 h (février) à 744 h. En deçà de 600, le
        # fichier est tronqué ou la requête a été rognée par le service.
        #
        # **Sauf pour le mois en cours.** ERA5 est produit avec environ cinq jours de
        # retard : au 30 juillet, juillet ne peut pas dépasser ~600 h, et le rejeter
        # priverait de toute météo le seul mois qu'on veut rejouer. Un mois en cours est
        # donc accepté partiel — mais sa couverture réelle est **dite**, jamais devinée,
        # et l'appelant décide s'il lui suffit.
        if service == "era5" and jeu.sizes[axe_temps] < 600:
            mois = re.search(r"(\d{4})(\d{2})", chemin.name)
            en_cours = bool(mois) and pd.Period(
                f"{mois.group(1)}-{mois.group(2)}"
            ) == pd.Period(pd.Timestamp.now(tz="UTC"), freq="M")
            if not en_cours:
                return f"{jeu.sizes[axe_temps]} pas de temps seulement (mois incomplet)"
            fin = pd.Timestamp(jeu[axe_temps].max().values)
            print(f"      mois en cours accepté partiel : {jeu.sizes[axe_temps]} h, "
                  f"jusqu'au {fin:%Y-%m-%d %H h}", flush=True)
    return None


def jours_attendus(nom: str) -> int | None:
    """Nombre de journées qu'un dossier de membres doit contenir, d'après son nom.

    ⚠️ **Tous** les jetons de mois, jamais le dernier seul : `..._202401_202402` en porte
    deux, et une expression ancrée à droite n'attendrait que 29 jours au lieu de 60.
    Rend `None` quand le nom ne porte aucun mois — auquel cas on ne sait pas compter.

    ⚠️ **Le mois en cours ne peut pas être complet.** Son jumeau,
    `extract_copernicus_stations.jours_attendus`, avait appris cette leçon ; celui-ci ne
    l'avait jamais su — c'est exactement le défaut corrigé à un endroit et laissé ailleurs
    que `CLAUDE.md` § 4 bis interdit. Constaté le 07/08/2026 : les **7** jours d'août
    réellement publiés étaient jugés « 7/31 — repris », donc **retéléchargés à chaque
    appel**, et `main` rendait 1 alors que tout ce qui existe était sur disque.
    """
    jetons = re.findall(r"_(\d{4})(\d{2})(?=_|$)", Path(nom).stem)
    if not jetons:
        return None
    # La veille comme borne : la prévision du jour même peut n'être pas encore publiée.
    aujourdhui = pd.Timestamp.now(tz="UTC").normalize()
    return sum(
        max(1, aujourdhui.day - 1)
        if pd.Period(f"{a}-{m}") == pd.Period(aujourdhui, freq="M")
        else pd.Period(f"{a}-{m}").days_in_month
        for a, m in jetons
    )


def est_complet(dossier: Path, nom: str) -> bool:
    """Le seul juge de la reprise — **sur le contenu**, jamais sur l'existence.

    ⚠️ Ce test existait déjà dans `acheve()`, à l'intérieur de `main`, et il était juste.
    Mais `telecharger()` en refaisait un second, plus faible — `membres.is_dir()` — et
    c'est celui-là qui décidait. Résultat : un mois à 30 jours sur 31 était **signalé**
    incomplet à l'écran, inscrit dans les restants, puis sauté avec la mention « déjà
    présent ». Le trou ne se refermait jamais.

    Deux contrôles sur la même question, c'est le plus faible qui gagne. Il n'y en a
    plus qu'un. C'est la règle 4 de `CLAUDE.md` : le test de reprise porte sur le
    **contenu attendu**.
    """
    final = dossier / nom
    if final.exists():
        return True
    membres = dossier / Path(nom).stem
    if not membres.is_dir():
        return False
    attendus = jours_attendus(nom)
    if attendus is None:
        return True
    presents = len(list(membres.glob("*.nc")))
    if presents < attendus:
        print(f"  ↻ {membres.name} incomplet : {presents}/{attendus} jours — "
              f"repris", flush=True)
        return False
    return True


def telecharger(
    service: str, identifiants: cop.Identifiants, dossier: Path,
    nom: str, requete: dict,
) -> tuple[str, str]:
    """Télécharge une entrée du plan. Renvoie (nom, statut).

    Le résultat est un fichier netCDF (ERA5) ou un dossier de membres journaliers
    (CAMS). Les deux valent marque d'achèvement pour la reprise.
    """
    if est_complet(dossier, nom):
        return nom, "déjà présent"

    # ⚠️ `final` et `membres` restent nécessaires plus bas — la destination de l'archive
    # dépaquetée et celle du netCDF simple. Les avoir supprimés en unifiant le test de
    # reprise a fait planter le lot sur un `NameError` que les 282 tests ne voyaient pas :
    # ils couvrent `est_complet`, pas le corps complet de `telecharger`.
    final = dossier / nom
    membres = dossier / Path(nom).stem

    _, jeu = SERVICES[service]

    # Nom provisoire : un fichier au nom définitif est réputé complet, et sera sauté
    # par la reprise. Une coupure ne doit pas fabriquer un tel fichier.
    partiel = dossier / f".{nom}.partiel"

    derniere = ""
    for essai, attente in enumerate((0, *ATTENTES_REPRISE)):
        if attente:
            time.sleep(attente)
        try:
            cop.executer(identifiants, jeu, requete, str(partiel))
        except Exception as exc:  # noqa: BLE001
            partiel.unlink(missing_ok=True)
            derniere = f"{type(exc).__name__}: {str(exc)[:120]}"
            continue

        probleme = verifier(partiel, service)
        if probleme:
            partiel.unlink(missing_ok=True)
            # Un fichier mal formé ne s'améliore pas en réessayant : la requête
            # elle-même est en cause, et le service la sert depuis son cache.
            return nom, f"REJETE {probleme}"

        taille = partiel.stat().st_size / 1e6
        suffixe = f" (essai {essai + 1})" if essai else ""

        import zipfile
        if zipfile.is_zipfile(partiel):
            extraits = depaqueter(partiel, membres)
            partiel.unlink(missing_ok=True)
            return nom, f"OK {taille:.0f} Mo · {len(extraits)} jours{suffixe}"

        partiel.rename(final)
        return nom, f"OK {taille:.0f} Mo{suffixe}"

    return nom, f"ECHEC après {len(ATTENTES_REPRISE) + 1} essais · {derniere}"


def main(service: str, debut: date, fin: date) -> int:
    if service not in SERVICES:
        raise SystemExit(f"Service inconnu : {service}")

    url, _ = SERVICES[service]
    identifiants = cop.Identifiants(url=url, cle=lire_cle())
    cop.accepter_licence(identifiants)

    dossier = RACINE / "data/raw" / service
    dossier.mkdir(parents=True, exist_ok=True)

    def acheve(nom: str) -> bool:
        """Délègue à `est_complet` — un seul juge pour toute la reprise."""
        return est_complet(dossier, nom)

    plan = plan_du_plus_recent(service, debut, fin)
    restants = [(nom, req) for nom, req in plan if not acheve(nom)]
    print(f"{service} · {len(plan)} fichiers demandés · {len(restants)} à télécharger "
          f"(du plus récent au plus ancien)", flush=True)

    depart = time.time()
    fait = echecs = 0
    with ThreadPoolExecutor(max_workers=REQUETES_PARALLELES) as pool:
        futurs = [
            pool.submit(telecharger, service, identifiants, dossier, nom, req)
            for nom, req in restants
        ]
        for futur in futurs:
            nom, statut = futur.result()
            fait += 1
            echecs += not statut.startswith(("OK", "déjà"))
            print(f"  [{fait}/{len(restants)}] {time.time() - depart:6.0f}s  "
                  f"{nom}  {statut}", flush=True)

    presents = [nom for nom, _ in plan if acheve(nom)]
    volume = sum(f.stat().st_size for f in dossier.rglob("*.nc")) / 1e9
    print(f"\n{len(presents)}/{len(plan)} fichiers sur disque · {volume:.1f} Go "
          f"· {dossier}", flush=True)
    if echecs:
        print(f"{echecs} échec(s) — relancer la même commande reprend où elle s'arrête.",
              flush=True)
    return 0 if len(presents) == len(plan) else 1


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--service", default="era5", choices=sorted(SERVICES))
    parseur.add_argument("--debut", default="2019-01", help="AAAA-MM")
    parseur.add_argument("--fin", default="2024-12", help="AAAA-MM")
    args = parseur.parse_args()

    def _mois(texte: str) -> date:
        annee, mois = texte.split("-")
        return date(int(annee), int(mois), 1)

    raise SystemExit(main(args.service, _mois(args.debut), _mois(args.fin)))
