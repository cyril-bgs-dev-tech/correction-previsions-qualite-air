#!/usr/bin/env bash
# Empilement maximal, les quatre polluants — deux à la fois.
#
# Deux à la fois et pas quatre : `ajuster` borne LightGBM à n_jobs=8 (32 cœurs ici),
# donc 2 × 8 = 16 fils. Quatre lots simultanés satureraient la bande passante mémoire,
# qui est le vrai goulot (CLAUDE.md, règle 1).
#
# Le journal n'est PAS filtré : une trace d'exception ne correspond à aucun motif de
# succès et serait jetée (règle 1 bis). Et le contrôle de fin porte sur l'artefact
# attendu, jamais sur le code de sortie.
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs

# Règle 1 bis — vérifier qu'un jumeau ne tourne pas déjà. Une seconde session Claude Code
# était ouverte sur ce dépôt le 05/08 ; deux lots concurrents sur les mêmes artefacts est
# le défaut que ce projet a déjà commis deux fois.
# 🔴 `pgrep` remplacé par `pids_de.sh` le 24/08/2026. Le crochet `[m]` protège le motif
# contre lui-même, jamais contre une AUTRE occurrence du nom dans la même commande — c'est
# ce qui a produit un faux jumeau le 08/08 et, une seconde fois, le 17/08. `pids_de.sh`
# exclut toute la chaîne de ses ancêtres, donc il ne peut structurellement pas se voir.
if [ -n "$("$(dirname "${BASH_SOURCE[0]}")/pids_de.sh" "methode_maximale.py")" ]; then
  echo "✗ un lot methode_maximale tourne déjà — arrêt"
  "$(dirname "${BASH_SOURCE[0]}")/pids_de.sh" "methode_maximale.py" --details | sed 's/^/  /'
  exit 1
fi

PY=/home/cyril/miniforge3/envs/llm-agent/bin/python3   # jamais `python3` nu
H=2
for paire in "NO2 O3" "PM10 PM25"; do
  for p in $paire; do
    echo "[$(date +%H:%M:%S)] lancement $p J+$H"
    "$PY" scripts/methode_maximale.py --polluant "$p" --horizon "$H" \
      > "logs/maximale_${p}.log" 2>&1 &
  done
  wait
done

echo
echo "[$(date +%H:%M:%S)] ── contrôle des artefacts attendus, nommés un par un ──"
for p in NO2 O3 PM10 PM25; do
  cible="reports/methode_maximale_${p}_h${H}.csv"
  if [ -f "$cible" ]; then
    echo "  ✓ $cible ($(($(wc -l < "$cible") - 1)) configurations)"
  else
    echo "  ✗ AUCUN fichier écrit pour $p — voir logs/maximale_${p}.log"
    ls -la "${cible}.partiel" 2>/dev/null && echo "    (un .partiel existe : lot interrompu, pas planté)"
  fi
done
