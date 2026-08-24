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
#   G3 « composition »       `speciation` `precurseurs`         ⚙️ lançable depuis le 25/08
#
# ✅ Pourquoi G3 est lançable depuis le 25/08 — et ce qu'il fallait pour ça
# --------------------------------------------------------------------------
# `profil`, `fourier` et `tendance` se calculent depuis la base : elles n'ont pas de source
# propre, donc les retirer ne peut pas allonger la fenêtre. G2 est sûr.
#
# `speciation` et `precurseurs` ont leurs propres parquets, avec leurs propres trous. Les
# retirer **lève leur restriction de support** : la pile réduite tournerait sur plus de mois
# que sa référence, et l'écart mélangerait le retrait avec les mois en plus. `ablation_jointe`
# refusera — c'est son travail, et c'est le défaut réel du 23/08 sur GEOS-CF.
#
# G3 exigeait donc de pouvoir ÉPINGLER la fenêtre sur celle de la référence.
# `methode_maximale.py --mois-de` le fait depuis le 25/08, et `ablation_jointe --socle` le
# passe SYSTÉMATIQUEMENT — pas « si ça déborde » : une condition à juger à chaque appel est
# exactement le genre de vigilance qui a échoué ailleurs ici.
#
# Usage :  scripts/reprise/groupes_deploiement.sh [G2]
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$RACINE" || exit 2
GROUPE="${1:-G2}"
case "$GROUPE" in
  G2) FAM="fourier,profil,tendance" ;;
  G3) FAM="precurseurs,speciation" ;;
  *)  echo "groupe inconnu : $GROUPE (G2 et G3 sont lançables)" >&2; exit 2 ;;
esac

# La cible se DEMANDE au code — voir `_cible_ablation.py` pour ce que la reconstruire a
# failli coûter. Deux endroits qui portent la même règle finissent toujours par diverger.
for p in NO2 O3 PM10 PM25; do
  python3 scripts/reprise/_cible_ablation.py "$p" "$FAM" || exit 4
done
