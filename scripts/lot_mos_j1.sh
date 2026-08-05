#!/usr/bin/env bash
# Régénération de la chaîne MOS officiel, à l'horizon 1 — c'est J0, l'échéance du produit
# officiel, et le défaut du script. Les amonts dataient du 29/07.
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
if ps -eo cmd | grep -q "^[^ ]*python3 scripts/fit_mos"; then echo "✗ fit_mos tourne déjà"; exit 1; fi
PY=/home/cyril/miniforge3/envs/llm-agent/bin/python3
for paire in "O3 NO2" "PM25"; do
  for p in $paire; do
    echo "[$(date +%H:%M:%S)] fit_mos $p J1"
    "$PY" scripts/fit_mos.py --polluant "$p" --horizon 1 > "logs/fit_mos_${p}_J1.log" 2>&1 &
  done
  wait
done
echo "[$(date +%H:%M:%S)] ── comparaison au MOS officiel (horizon 1 par défaut) ──"
for p in O3 NO2 PM25; do
  "$PY" scripts/comparer_mos_officiel_annee.py --polluant "$p" > "logs/mos_annee_${p}.log" 2>&1
  c="reports/comparaison_mos_officiel_annee_${p}.csv"
  [ -f "$c" ] && echo "  ✓ $c ($(($(wc -l < "$c") - 1)) lignes)" || echo "  ✗ AUCUN pour $p"
done
