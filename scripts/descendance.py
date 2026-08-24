#!/usr/bin/env python3
"""Ce qui tombe quand une entrée change — action P0.4.

La perte que ce script existe pour supprimer
---------------------------------------------
Le 23/08, les cinq mois manquants de la spéciation ont été complétés. Le corpus a changé,
et **rien ne disait quelles mesures publiées venaient de tomber**. Je l'ai découvert en les
refaisant : la base a bougé de +0,17 à +0,32 pt, `fourier` est passée de ✅ à 🔴, la
réfutation de `tendance` a sauté, l'ordre de deux configurations de précurseurs s'est
inversé et huit ablations jointes sont devenues incomparables. **Trois heures de mesures
refaites** pour une question — « qui dépend de la spéciation ? » — dont la réponse tient
dans un graphe.

Ce que ce script rend, et ce qu'il ne rend pas
-----------------------------------------------
Il rend la **descendance déclarée** : sources → piles → verdicts → documents. Pour chaque
artefact il compare sa date à celle de ses parents, et **nomme le parent** qui l'a périmé —
un verdict qui dit « périmé » sans dire « par quoi » envoie chercher au hasard (§ 1 quinquies).

Il ne rend PAS une preuve d'égalité : une date postérieure ne prouve pas que l'artefact a
été calculé sur ce parent-là, seulement qu'il *pouvait* l'être. C'est un minorant de la
péremption, jamais un certificat de fraîcheur — d'où le troisième état, `inaudité`, pour
les artefacts sans empreinte d'entrées, où la question **ne peut pas** être tranchée. Un
zéro de non-lecture ne se confond pas avec un zéro de non-occurrence (§ 4 bis).

Usage
------
    python3 scripts/descendance.py                  # ce qui est périmé aujourd'hui
    python3 scripts/descendance.py --si data/processed/meteo/speciation_metropole_202401.parquet
    python3 scripts/descendance.py --graphe         # la descendance déclarée, en entier
"""
from __future__ import annotations

import argparse
import csv
import glob
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# ── Les sources, par famille ────────────────────────────────────────────────────────────
# Chaque motif est VÉRIFIÉ au démarrage : un motif qui ne rend rien est une déclaration qui
# ment, et elle se lirait comme « cette famille n'a pas bougé ».
SOURCES: dict[str, list[str]] = {
    "base":         ["data/processed/meteo/cams_prevision_metropole_*.parquet"],
    "typologie":    ["data/processed/stations.parquet",
                     "data/processed/trafic_population_metropole.parquet"],
    "membres":      ["data/processed/meteo/membres_metropole_*.parquet"],
    "feux":         ["data/processed/meteo/feux_metropole_*.parquet"],
    "geoscf":       ["data/processed/meteo/geoscf_metropole_*.parquet"],
    "speciation":   ["data/processed/meteo/speciation_metropole_*.parquet"],
    "precurseurs":  ["data/processed/meteo/precurseurs_metropole_*.parquet"],
    "chimie":       ["data/processed/meteo/chimie_metropole_*.parquet"],
    "ifs":          ["data/processed/meteo/ifs_metropole_*.parquet"],
}
# `profil`, `fourier` et `tendance` se calculent depuis la base : elles n'ont pas de source
# propre, et c'est pour cela qu'elles ne figurent pas ici plutôt que par oubli.
DERIVEES_DE_BASE = ("profil", "fourier", "tendance")

# Ce qu'on lit de chaque fichier pour y chercher une citation. Un en-tête de CSV et les
# premières pages d'un document suffisent ; lire au-delà coûte des gigaoctets pour rien.
TETE_LUE = 262_144


def _mtime(p: Path) -> float:
    return p.stat().st_mtime


def sources_resolues(strict: bool = True) -> dict[str, list[Path]]:
    """Les fichiers derrière chaque famille — et le refus si un motif ne rend rien."""
    out, muets = {}, []
    for fam, motifs in SOURCES.items():
        fs = [Path(f) for m in motifs for f in glob.glob(str(RACINE / m))]
        if not fs:
            muets.append(fam)
        out[fam] = sorted(fs, key=_mtime)
    if muets and strict:
        raise SystemExit(
            f"⛔ motif(s) sans aucun fichier : {', '.join(muets)} — une source déclarée "
            f"qui ne rend rien se lit comme « cette famille n'a pas bougé ». Corriger la "
            f"déclaration ou la retirer.")
    return out


# ── Les artefacts, et de qui ils descendent ─────────────────────────────────────────────
PILE = re.compile(r"^methode_maximale_(NO2|O3|PM10|PM25)_h(\d)(.*?)(_par_pli)?\.csv$")
EXCLUE = re.compile(r"sans-([a-z-]+)")


def familles_d_une_pile(suffixe: str) -> set[str]:
    """Les familles dont CETTE pile dépend — le suffixe dit ce qui en a été retiré."""
    toutes = set(SOURCES) | set(DERIVEES_DE_BASE)
    for m in EXCLUE.finditer(suffixe):
        toutes -= set(m.group(1).split("-"))
    if "avec-ifs" not in suffixe:
        toutes -= {"ifs"}
    return toutes


def descendance() -> list[tuple[Path, list[tuple[str, Path]]]]:
    """(artefact, [(rôle du parent, chemin du parent)]) pour tout ce qui est traçable."""
    src = sources_resolues()
    liens: list[tuple[Path, list[tuple[str, Path]]]] = []
    piles: dict[str, Path] = {}

    for f in sorted((RACINE / "reports").glob("methode_maximale_*.csv")):
        m = PILE.match(f.name)
        if not m:
            continue
        _pol, _h, suff, _pp = m.groups()
        # 🔴 Ne relier QUE la source la plus récente suffit pour dater la péremption, et
        # rend `--si` faux : interrogé sur n'importe quel autre fichier de la famille, il
        # répondait « 0 artefact tombe » — un zéro de non-recherche indiscernable d'un zéro
        # de non-occurrence (§ 4 bis), dans le script même qui met en garde contre lui.
        # On relie TOUTES les sources ; la péremption prend le maximum, `--si` teste
        # l'appartenance.
        parents = [(fam, p) for fam in familles_d_une_pile(suff)
                   for p in src.get(fam, [])]
        liens.append((f, parents))
        piles[f.name] = f

    # Les verdicts, les ablations et les documents descendent des piles qu'ils CITENT — la
    # citation se lit dans le fichier, jamais dans son nom (§ 4 bis).
    #
    # 🔴 `Path.read_text()[:N]` lit le fichier ENTIER avant de tronquer. Sur ce dépôt cela
    # faisait 4,1 Go pour 696 CSV, et le balayage n'aboutissait pas. On lit une tête bornée,
    # une seule fois par fichier, et on croise contre TOUS les noms de piles d'un coup.
    noms = {n[:-4]: piles[n] for n in piles}
    candidats = [f for f in sorted((RACINE / "reports").glob("*.csv")) if not PILE.match(f.name)]
    candidats += sorted((RACINE / "reports").glob("*.md"))
    candidats += sorted((RACINE / "reports/decisions").glob("*.md"))
    for f in candidats:
        try:
            with f.open(errors="ignore") as fh:
                tete = fh.read(TETE_LUE)
        except OSError:
            continue
        cites = [p for nom, p in noms.items() if nom in tete]
        if cites:
            liens.append((f, [("pile", p) for p in cites]))
    return liens


def empreinte(f: Path) -> str | None:
    """L'empreinte d'entrées inscrite dans l'artefact, si elle y est."""
    if f.suffix != ".csv":
        return None
    try:
        with f.open(newline="", errors="ignore") as fh:
            r = csv.DictReader(fh)
            row = next(r, None)
            return (row or {}).get("empreinte_entrees")
    except Exception:
        return None


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--si", metavar="CHEMIN",
                   help="ce qui tomberait si CE fichier changeait maintenant")
    a.add_argument("--graphe", action="store_true", help="la descendance déclarée, en entier")
    o = a.parse_args()

    liens = descendance()

    if o.graphe:
        for art, parents in liens:
            print(f"\n{art.relative_to(RACINE)}")
            for role, p in sorted(parents, key=lambda x: x[0]):
                print(f"    ← {role:12s} {p.relative_to(RACINE)}")
        return 0

    if o.si:
        cible = Path(o.si) if Path(o.si).is_absolute() else RACINE / o.si
        if not cible.exists():
            print(f"⛔ {o.si} n'existe pas — on ne raisonne pas sur un fichier absent.")
            return 2
        touches = [art for art, ps in liens if any(p == cible for _, p in ps)]
        # La descendance est transitive : ce qui cite un artefact touché est touché.
        for _ in range(3):
            noms = {t.name[:-4] for t in touches}
            touches += [art for art, ps in liens
                        if art not in touches and any(p.name[:-4] in noms for _, p in ps)]
        print(f"Si « {cible.relative_to(RACINE)} » change, {len(touches)} artefact(s) tombent :\n")
        for t in sorted(touches):
            print(f"  {t.relative_to(RACINE)}")
        return 0

    perimes, inaudites, ajour = [], [], 0
    for art, parents in liens:
        ta = _mtime(art)
        plus_recents = [(role, p) for role, p in parents if _mtime(p) > ta]
        if plus_recents:
            perimes.append((art, plus_recents))
        elif art.suffix == ".csv" and empreinte(art) is None:
            inaudites.append(art)
        else:
            ajour += 1

    print(f"DESCENDANCE · {len(liens)} artefact(s) traçable(s)")
    print("═" * 92)
    if perimes:
        print(f"\n🔴 {len(perimes)} PÉRIMÉ(S) — un parent leur est postérieur :\n")
        for art, ps in sorted(perimes):
            r, p = sorted(ps, key=lambda x: -_mtime(x[1]))[0]
            print(f"  {str(art.relative_to(RACINE)):68s}")
            print(f"      ← {r} plus récent : {p.name}")
    if inaudites:
        print(f"\n⚪ {len(inaudites)} INAUDITÉ(S) — postérieurs à leurs parents, mais sans "
              f"empreinte d'entrées :\n     la fraîcheur ne peut pas être TRANCHÉE, seulement "
              f"supposée.\n")
        for art in sorted(inaudites)[:12]:
            print(f"  {art.relative_to(RACINE)}")
        if len(inaudites) > 12:
            print(f"  … et {len(inaudites) - 12} autre(s)")
    print(f"\n✅ {ajour} à jour · 🔴 {len(perimes)} périmé(s) · ⚪ {len(inaudites)} inaudité(s)")
    return 1 if perimes else 0


if __name__ == "__main__":
    sys.exit(main())
