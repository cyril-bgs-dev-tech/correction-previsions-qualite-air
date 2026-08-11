#!/usr/bin/env bash
# Rejoue `oof_double_aveugle.py --typologie` sur les QUATRE polluants, à J+1.
#
# Pourquoi rejouer ce qui existe déjà
# -----------------------------------
# `reports/stations_degradees_h2.csv` croise les quatre polluants. Or les OOF du 03/08 n'ont
# pas été produits avec les mêmes options : NO2 et PM10 portent `_typo`, O3 et PM25 non.
# Croiser des variantes différentes dans une seule table, c'est le défaut « une variante
# écrase sa jumelle » — chaque ligne est juste, la comparaison entre lignes ne l'est pas.
# Une seule variante pour les quatre, et le tableau redevient lisible.
#
# ⚠️ Ce que ce lot NE corrige PAS, et qui doit accompagner toute citation : ce script ne
# connaît pas l'étage `tendance`, passé en production le 11/08 sur les quatre polluants
# (commit 398ac1d). Les parts mesurées ici décrivent la pile SANS cet étage. Le sens de
# l'écart n'est pas établi — ne pas le supposer favorable.
#
# Usage : bash scripts/lot_oof_typo.sh [POLLUANT ...]      (défaut : les quatre)
set -u
cd "$(dirname "$0")/.." || exit 1

H=2                    # échéance J+1 (1-24 h = J0, 25-48 h = J+1)
ESSAIS_MAX=8
PLAFOND=24G
JOURNAL=logs/lot_oof_typo.log
REPERE=logs/.oof_typo_campagne
VEILLE="$HOME/veille_memoire_oof_typo.csv"
POLLUANTS=("$@")
[ ${#POLLUANTS[@]} -eq 0 ] && POLLUANTS=(O3 NO2 PM10 PM25)
mkdir -p logs data/interim/oof

# Le repère date la campagne et ne se recrée JAMAIS : il est la référence de fraîcheur pour
# `oof_typo_complete.sh`, et la remettre à l'heure à chaque relance redemanderait tout.
[ -f "$REPERE" ] || { touch "$REPERE"; echo "repère de campagne créé : $(date '+%F %T')" \
  | tee -a "$JOURNAL"; }

echo "=== OOF typo démarré $(date '+%F %T') · ${POLLUANTS[*]} · plafond $PLAFOND ===" \
  | tee -a "$JOURNAL"

if ! bash scripts/machine_libre.sh; then
  echo "REFUS : un travail lourd tourne déjà" | tee -a "$JOURNAL"
  exit 2
fi
bash scripts/veille_hote.sh demarrer 2>&1 | tee -a "$JOURNAL"
scripts/veille_memoire.sh oof_double_aveugle.py "$VEILLE" 5 &
veilleur=$!
trap 'kill "$veilleur" 2>/dev/null' EXIT

for p in "${POLLUANTS[@]}"; do
  cible="data/interim/oof/oof_${p}_h${H}_typo.parquet"
  # Reprise sur la FRAÎCHEUR, pas sur l'existence : les parquets du 03/08 portent déjà ce
  # nom pour NO2 et PM10 (§ 4 — d'où vient l'attendu).
  if [ -f "$cible" ] && [ "$cible" -nt "$REPERE" ]; then
    echo "[$(date +%T)] ↷ $p déjà refait dans cette campagne — sauté" | tee -a "$JOURNAL"
    continue
  fi
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    echo "[$(date +%T)] $p J+$((H - 1)) — tentative $essai/$ESSAIS_MAX" | tee -a "$JOURNAL"
    t0=$SECONDS
    echo "── tentative $essai · $(date '+%F %T') ──" >> "logs/oof_typo_${p}.log"
    PYTHONFAULTHANDLER=1 systemd-run --user --scope --quiet \
      -p MemoryMax="$PLAFOND" -p MemorySwapMax=0 -- \
      env PYTHONFAULTHANDLER=1 python3 -u scripts/oof_double_aveugle.py \
        --polluant "$p" --horizon "$H" --typologie \
      >> "logs/oof_typo_${p}.log" 2>&1
    code=$?
    [ "$code" -eq 139 ] && echo "  ⚠️ $p segfault (139) — plateforme, pas le code" | tee -a "$JOURNAL"
    [ "$code" -eq 137 ] && echo "  ⚠️ $p tué par le plafond $PLAFOND" | tee -a "$JOURNAL"
    echo "[$(date +%T)] $p — tentative $essai, code=$code, $(((SECONDS - t0) / 60)) min" \
      | tee -a "$JOURNAL"
    # Sortie de boucle sur l'ARTEFACT, jamais sur le code : un segfault postérieur à
    # l'écriture rejouerait un travail déjà fait (mesuré sur PM25 le 11/08).
    if [ -f "$cible" ] && [ "$cible" -nt "$REPERE" ]; then
      [ "$code" -ne 0 ] && echo "  ↷ $p : code=$code mais le parquet est FRAIS — on ne rejoue pas" \
        | tee -a "$JOURNAL"
      break
    fi
    # Le journal ne filtre JAMAIS sur les seules lignes de succès (§ 1 bis).
    tail -5 "logs/oof_typo_${p}.log" | tee -a "$JOURNAL"
    sleep 20
  done
done

echo "[$(date +%T)] ── contrôle des artefacts ──" | tee -a "$JOURNAL"
manque=0
for p in "${POLLUANTS[@]}"; do
  cible="data/interim/oof/oof_${p}_h${H}_typo.parquet"
  if [ -f "$cible" ] && [ "$cible" -nt "$REPERE" ]; then
    echo "  ✅ $cible · $(du -h "$cible" | cut -f1)" | tee -a "$JOURNAL"
  else
    echo "  ❌ AUCUN parquet frais : $cible" | tee -a "$JOURNAL"
    manque=1
  fi
done
bash scripts/veille_hote.sh arreter 2>&1 | tee -a "$JOURNAL"
echo "=== OOF typo terminé $(date '+%F %T') · manque=$manque ===" | tee -a "$JOURNAL"
exit "$manque"
