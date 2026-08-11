#!/usr/bin/env bash
# Rend 0 si un `lot_ablation.sh` tourne déjà, 1 sinon.
#
# Pourquoi un FICHIER plutôt qu'un `pgrep` en ligne dans le relanceur
# -------------------------------------------------------------------
# Le motif écrit en ligne dans `relance_ablation.ps1` traversait
# PowerShell → wsl.exe → bash -lc, et **ses guillemets se perdaient en route** :
# `pgrep -f "bash scripts/[l]ot_ablation\.sh"` arrivait comme
# `pgrep -f bash scripts/[l]ot_ablation\.sh`, donc motif = « bash », qui matche TOUS les
# bash de la machine. Le garde répondait « un lot tourne déjà » en permanence — un faux
# positif qui bloque le travail *et* affirme le contraire de la réalité (§ 1 bis).
# Un fichier n'a pas de couche de citation à traverser.
#
# Le motif exclut sa propre invocation par le crochet `[l]` — et cela ne suffit pas :
# tout shell dont la ligne de commande contient le motif entre aussi dans `ps`. On exclut
# donc explicitement ce processus et son parent.
set -u

sortie=$(pgrep -af 'bash scripts/[l]ot_ablation\.sh' 2>/dev/null \
         | awk -v moi="$$" -v pere="$PPID" '$1 != moi && $1 != pere')

if [ -n "$sortie" ]; then
  echo "lot en cours :"
  echo "$sortie" | sed 's/^/  /'
  exit 0
fi
echo "aucun lot en cours"
exit 1
