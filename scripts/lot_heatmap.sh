#!/usr/bin/env bash
# Régénération des heatmaps annuelles — leurs sorties dataient du 31/07-03/08, donc d'avant
# la régénération du corpus : O3 portait 23 mois sur 36. Deux à la fois (règle 1).
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
if ps -eo cmd | grep -q "^[^ ]*python3 scripts/heatmap_annuelle"; then
  echo "✗ un lot heatmap tourne déjà — arrêt"; exit 1
fi
PY=/home/cyril/miniforge3/envs/llm-agent/bin/python3
for paire in "NO2 PM10" "PM25"; do
  for p in $paire; do
    echo "[$(date +%H:%M:%S)] lancement $p"
    "$PY" scripts/heatmap_annuelle.py --polluant "$p" > "logs/heatmap_${p}.log" 2>&1 &
  done
  wait
done
echo
echo "[$(date +%H:%M:%S)] ── contrôle des artefacts, nommés un par un ──"
for p in NO2 O3 PM10 PM25; do
  c="reports/heatmap_annuelle_${p}.csv"
  [ -f "$c" ] && echo "  ✓ $c" || echo "  ✗ AUCUN fichier pour $p"
done
