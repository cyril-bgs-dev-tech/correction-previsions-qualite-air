#!/usr/bin/env bash
# Banc — comble les quatre exécutions encore manquantes, avec espacement.
#
# Ce que les deux lots précédents ont appris, et qui dicte ce troisième
# ------------------------------------------------------------------------
# Le segfault de `lib_lightgbm.so` est **aléatoire**, pas propre à un couple : NO2
# `anomalie_cams` a échoué 4 fois d'affilée puis réussi à la 5ᵉ, avec la même graine et
# le même corpus. Deux hypothèses ont été réfutées en chemin — valeurs extrêmes dans les
# colonnes fabriquées (max|x| = 16,6, zéro infini) et parquets CAMS abîmés (21 fichiers
# PM10 vérifiés un par un, tous sains) — et le témoin passe toujours, donc la machine
# n'est pas dégradée.
#
# Le seul motif qui reste : **les succès sont des exécutions isolées, les échecs sont des
# exécutions enchaînées à 5 s d'intervalle.** D'où 30 s entre deux tentatives. C'est une
# hypothèse, pas une explication — elle est ici parce qu'elle est gratuite et cohérente
# avec les mesures, pas parce qu'elle est démontrée.
set -u

cd /mnt/d/Projet_Air_Quality || exit 1
JOURNAL=logs/lot_banc_combler.log
ESSAIS_MAX=6
PAUSE=30
mkdir -p logs

MANQUANTS=("PM10:base" "PM10:tendance_cams" "PM10:interactions" "PM25:interactions")

echo "=== comblement démarré $(date '+%F %T') · ${#MANQUANTS[@]} exécutions ===" | tee -a "$JOURNAL"

for ENTREE in "${MANQUANTS[@]}"; do
  P="${ENTREE%%:*}"; F="${ENTREE##*:}"
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    echo "[$(date '+%T')] $P/$F — tentative $essai/$ESSAIS_MAX" | tee -a "$JOURNAL"
    t0=$SECONDS
    python3 scripts/banc_preprocessing.py --polluant "$P" --famille "$F" >> "$JOURNAL" 2>&1
    code=$?
    echo "[$(date '+%T')] $P/$F — tentative $essai, code=$code, $((SECONDS - t0))s" | tee -a "$JOURNAL"
    [ "$code" -eq 0 ] && break
    sleep "$PAUSE"
  done
  sleep "$PAUSE"
done

for P in PM10 PM25; do
  python3 scripts/banc_preprocessing.py --polluant "$P" --rapport >> "$JOURNAL" 2>&1
  echo "[$(date '+%T')] $P — rapport code=$?" | tee -a "$JOURNAL"
done

# ── Contrôle de fin sur les quatre polluants, famille par famille (règle 4) ──────────
echo "=== contrôle de fin $(date '+%F %T') ===" | tee -a "$JOURNAL"
manque=0
for P in O3 NO2 PM10 PM25; do
  CIBLE="reports/banc_preprocessing_${P}_h2.csv"
  if [ ! -f "$CIBLE" ]; then
    echo "  ✗ $CIBLE ABSENT" | tee -a "$JOURNAL"; manque=1; continue
  fi
  trou=0
  for F in base harmoniques splines anomalie_cams tendance_cams interactions; do
    n=$(awk -F, -v f="$F" 'NR>1 && $4==f {c++} END {print c+0}' "$CIBLE")
    [ "$n" -eq 2 ] || { echo "  ✗ $P/$F : $n ligne(s) au lieu de 2" | tee -a "$JOURNAL"; trou=1; }
  done
  if [ "$trou" -eq 0 ]; then
    echo "  ✓ $CIBLE — 6 familles × 2 jeux" | tee -a "$JOURNAL"
  else
    manque=1
  fi
done
echo "=== comblement terminé $(date '+%F %T') · manque=$manque ===" | tee -a "$JOURNAL"
exit "$manque"
