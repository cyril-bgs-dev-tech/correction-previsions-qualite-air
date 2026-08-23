#!/usr/bin/env bash
# Rend 0 si le lot nommé tourne déjà, 1 sinon.
#
# Usage : bash scripts/lot_en_cours.sh [NOM_DU_LOT.sh]     (défaut : lot_ablation.sh)
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
# ⚠️ L'ARGUMENT, lui, traverse sans dommage — et seulement parce que c'est un jeton nu,
# sans espace ni guillemet. C'était toute la difficulté du motif : il en contenait les deux.
# Ne jamais passer ici autre chose qu'un nom de fichier.
#
# Le motif exclut sa propre invocation par le crochet `[l]` — et cela ne suffit pas :
# tout shell dont la ligne de commande contient le motif entre aussi dans `ps`. On exclut
# donc explicitement ce processus et son parent.
set -u

cible="${1:-lot_ablation.sh}"
# Crochet sur la première lettre, puis échappement des points : le motif construit ici est
# le même que celui écrit à la main auparavant, `bash scripts/[l]ot_ablation\.sh`.
motif="bash scripts/[${cible:0:1}]${cible:1}"
motif="${motif//./\\.}"

# 🔴 Exclure $$ et $PPID ne suffit pas : un `$(...)` s'exécute dans un petit-enfant du
# shell qui porte le motif, et le grand-parent restait visible. `pids_de.sh` exclut la
# chaîne ENTIÈRE des ancêtres — c'est la seule forme qui ne puisse pas se voir.
sortie=$("$(dirname "${BASH_SOURCE[0]}")/pids_de.sh" "bash scripts/${cible}" --details)

if [ -n "$sortie" ]; then
  echo "lot en cours :"
  echo "$sortie" | sed 's/^/  /'
  exit 0
fi
echo "aucun lot en cours"
exit 1
