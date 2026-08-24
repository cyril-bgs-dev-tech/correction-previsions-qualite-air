#!/usr/bin/env bash
# Les ablations JOINTES par groupe de déploiement — action P1.8, décision DEC-2026-08-24-03.
#
# Pourquoi par groupe et non famille par famille
# -----------------------------------------------
# Deux familles qui décrivent la même chose s'annulent à l'ablation individuelle : retirez
# l'une, l'autre rattrape, et chacune paraît inutile. Mesuré le 24/08 sur le socle : onze
# des vingt-huit apports individuels sont plus petits que leur propre amplitude au
# jackknife. Un groupe réunit ce qui **tombe ensemble** — même source, même disponibilité.
#
# Ce que ce script lance, et ce qu'il ne lance PAS
# -------------------------------------------------
#   G1 « site »              `typologie`                       ✅ DÉJÀ MESURÉ — famille seule,
#   G4 « dispersion »        `membres`                          l'ablation est dans la pile.
#   G2 « forme du jour »     `profil` `fourier` `tendance`      ⚙️ lancé ici
#   G3 « composition »       `speciation` `precurseurs`         🔴 BLOQUÉ — voir ci-dessous
#
# 🔴 Pourquoi G3 ne peut pas être lancé tel quel
# ------------------------------------------------
# `profil`, `fourier` et `tendance` se calculent depuis la base : elles n'ont pas de source
# propre, donc les retirer ne peut pas allonger la fenêtre. G2 est sûr.
#
# `speciation` et `precurseurs` ont leurs propres parquets, avec leurs propres trous. Les
# retirer **lève leur restriction de support** : la pile réduite tournerait sur plus de mois
# que sa référence, et l'écart mélangerait le retrait avec les mois en plus. `ablation_jointe`
# refusera — c'est son travail, et c'est le défaut réel du 23/08 sur GEOS-CF.
#
# G3 exige donc de pouvoir ÉPINGLER la fenêtre sur celle de la référence. Tant que
# `methode_maximale.py` ne sait pas le faire, lancer G3 produirait un refus, pas une mesure.
#
# Usage :  scripts/reprise/groupes_deploiement.sh [G2]
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$RACINE" || exit 2
GROUPE="${1:-G2}"
case "$GROUPE" in
  G2) FAM="fourier,profil,tendance" ;;
  G3) echo "🔴 G3 est bloqué : retirer speciation/precurseurs allonge la fenêtre, et" >&2
      echo "   l'écart mélangerait le retrait avec les mois en plus. Épingler la fenêtre" >&2
      echo "   d'abord (--mois-de sur methode_maximale.py)." >&2; exit 3 ;;
  *)  echo "groupe inconnu : $GROUPE (G2 seul est lançable)" >&2; exit 2 ;;
esac

for p in NO2 O3 PM10 PM25; do
  cible="reports/methode_maximale_${p}_h2_sans-feux-$(echo "$FAM" | tr ',' '-' | tr ' ' '-')-geoscf_fenetre-complete.csv"
  echo "reports/ablation_jointe_$(echo "$FAM" | tr ',' '-')_${p}_h2.csv :: python3 -u scripts/ablation_jointe.py --polluant $p --familles $FAM --socle"
done
