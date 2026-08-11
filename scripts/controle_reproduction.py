#!/usr/bin/env python3
"""Les configurations déjà mesurées se reproduisent-elles ?

Le lot d'ablation recalcule les 8 anciennes configurations en plus des 5 nouvelles. Ce
n'est pas du gaspillage : c'est le seul contrôle qui dise si l'ENTRÉE a bougé entre deux
générations. Si `base` ne rend plus la même chose, ce n'est pas l'ablation qui a changé
quelque chose, c'est le corpus — et il faut le savoir AVANT de publier.

Le seuil, et pourquoi il n'est pas zéro
---------------------------------------
Exiger la reproduction au bit près d'un ajustement LightGBM à 8 fils est un contrôle
FAUX : l'ordre de réduction des fils varie d'une exécution à l'autre. `CLAUDE.md`
§ 1 quater l'a mesuré — deux exécutions de la pile O₃ séparées par sept crashs rendent
« identiques à la décimale », avec un écart de ~1 × 10⁻⁴ sur la typologie, explicitement
attribué à cet ordre de réduction.

Le seuil retenu est **0,05 point**, encadré des deux côtés :
  · ~500 × au-dessus du bruit de réduction documenté (1 × 10⁻⁴) ;
  · ~40 × en dessous de la barre de bruit de la méthode elle-même (±2,02 pt, dominée par
    la partition — voir la fiche « la barre de bruit et ce qu'elle autorise »).

Un écart au-dessus n'est pas une preuve de faute : c'est l'ordre de grandeur à partir
duquel il faut aller regarder plutôt que conclure.

Usage : python3 scripts/controle_reproduction.py [POLLUANT ...]   (défaut : les quatre)
"""
from __future__ import annotations

import subprocess
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
SEUIL = 0.05          # point de pourcentage — justification dans le docstring
BRUIT_METHODE = 2.02  # ±, pour situer l'écart


def reference(rel: str) -> pd.DataFrame | None:
    """La version commitée du CSV — la génération précédente, quelle que soit sa date."""
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=RACINE,
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return pd.read_csv(StringIO(r.stdout))


def controler(p: str) -> tuple[str, float, int] | None:
    rel = f"reports/methode_maximale_{p}_h2.csv"
    f = RACINE / rel
    if not f.exists():
        print(f"  {p:5s} — CSV absent, rien à contrôler")
        return None
    ref = reference(rel)
    if ref is None:
        print(f"  {p:5s} — aucune version commitée : première génération, rien à comparer")
        return None

    # ⚠️ Un fichier NON régénéré est identique à sa version commitée : l'écart vaut alors
    # zéro et le contrôle passe — mais il n'a rien contrôlé. C'est le « zéro de non-lecture
    # indiscernable d'un zéro de non-occurrence » de § 4 bis, et il donnerait ici une
    # fausse assurance juste avant publication. On le nomme au lieu de le compter.
    if pd.read_csv(f).equals(ref):
        print(f"  ⬜ {p:5s} — identique à la version commitée : PAS régénéré, "
              f"le contrôle est sans objet")
        return None

    a = ref.set_index("configuration")["gain_pct"].astype(float)
    b = pd.read_csv(f).set_index("configuration")["gain_pct"].astype(float)
    communes = [c for c in a.index if c in b.index]
    if not communes:
        print(f"  {p:5s} — 0 configuration commune : les deux fichiers ne parlent pas "
              f"de la même chose")
        return None

    ecarts = {c: float(b[c]) - float(a[c]) for c in communes}
    pire_nom = max(ecarts, key=lambda c: abs(ecarts[c]))
    pire = abs(ecarts[pire_nom])
    etat = "✓" if pire < SEUIL else "⚠️"
    print(f"  {etat} {p:5s} — {len(communes):2d} configurations communes · pire écart "
          f"{pire:.2e} pt sur « {pire_nom[:34]} »")
    if pire >= SEUIL:
        for c in sorted(ecarts, key=lambda c: -abs(ecarts[c]))[:5]:
            print(f"        {c[:44]:44s} {a[c]:+8.4f} → {b[c]:+8.4f}  ({ecarts[c]:+.4f})")
    return (p, pire, len(communes))


def main() -> int:
    demandes = sys.argv[1:] or ["O3", "NO2", "PM10", "PM25"]
    print(f"Contrôle de reproduction — seuil {SEUIL} pt "
          f"(barre de bruit de la méthode : ±{BRUIT_METHODE} pt)\n")
    res = [r for p in demandes if (r := controler(p)) is not None]
    if not res:
        print("\nAucun polluant contrôlable.")
        return 0
    # Périmètre EFFECTIF, jamais le périmètre demandé (§ 2 quater).
    absents = [p for p in demandes if p not in {r[0] for r in res}]
    pire = max(r[1] for r in res)
    print(f"\n  périmètre : {len(res)}/{len(demandes)} contrôlés"
          + (f" · non contrôlés : {', '.join(absents)}" if absents else ""))
    print(f"  pire écart tous polluants : {pire:.2e} pt "
          f"= {pire / BRUIT_METHODE:.1e} × la barre de bruit")
    if pire >= SEUIL:
        print("\n⚠️ Au moins un écart dépasse le seuil — aller REGARDER avant de publier.")
        return 1
    print("\n✓ Reproduction confirmée à la précision que la méthode possède.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
