#!/usr/bin/env python3
"""Le chemin du rapport d'une ablation jointe — DEMANDÉ au code, jamais reconstruit.

Pourquoi ce fichier de sept lignes existe
------------------------------------------
`groupes_deploiement.sh` écrivait la cible en shell, en recopiant la règle de nommage de
`ablation_jointe.py`. Puis `--socle` a reçu son propre suffixe `_socle` — pour ne pas écraser
la jumelle historique — et la ligne shell est devenue fausse **en silence**. Le travail aurait
été juste et le VERDICT faux : « ABSENT » sur quatre fichiers correctement écrits.

Un faux négatif de garde-fou coûte plus qu'une panne : il use la confiance dans le contrôle,
et le prochain « ABSENT » sera lu comme du bruit.

> **Deux endroits qui portent la même règle finissent toujours par diverger. Un seul la porte.**

Usage : python3 scripts/reprise/_cible_ablation.py NO2 fourier,profil,tendance
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ablation_jointe import chemins  # noqa: E402

pol, fam = sys.argv[1], sorted(sys.argv[2].split(","))
_ref, _sans, _excl, suff = chemins(pol, 2, fam, False, True)
cible = f"reports/ablation_jointe_{'-'.join(fam)}_{pol}_h2{suff}.csv"
print(f"{cible} :: python3 -u scripts/ablation_jointe.py "
      f"--polluant {pol} --familles {','.join(fam)} --socle")
