#!/bin/bash
# GFAS pour 2025 — le jeu couvre jusqu'au 03/12/2025, donc janvier à juin sont disponibles.
cd /mnt/d/Projet_Air_Quality
P=/home/cyril/miniforge3/envs/llm-agent/bin/python3
for m in 1 2 3 4 5 6 7; do
  mm=$(printf "%02d" $m)
  [ -f "data/raw/gfas/gfas_2025${mm}.nc" ] && continue
  $P scripts/passe_unitaire_gfas.py --annee 2025 --mois "$m" 2>&1 | grep -E "Écrit|⚠️|ÉCHEC"
done
$P scripts/exposition_feux.py --scope metropole 2>&1 | grep -E "lignes ·|mois écrits"
