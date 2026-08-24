#!/usr/bin/env bash
# LE point d'entrée pour reprendre les mesures de score, dans n'importe quelle session.
#
# Ce qu'il fait, et pourquoi il est sûr de le relancer
# ----------------------------------------------------
# · il DÉRIVE les tâches restantes des artefacts (`plan_scores.py`), donc relancer après
#   une interruption ne refait pas ce qui est fait ;
# · il sérialise sur la ressource « cpu » par `flock` : deux lancements concurrents sont
#   impossibles, le second se retire en le disant (§ 0-I) ;
# · chaque tâche est jugée sur son ARTEFACT, jamais sur son code de sortie, et une tâche
#   qui n'écrit rien ARRÊTE la file — enchaîner sur du vide le propagerait (§ 0-C).
#
# Le réseau ECMWF est une ressource DISTINCTE : `--avec-ifs` lance l'acquisition en
# parallèle, ce qui est correct et souhaitable (§ 0-G, une ressource au repos pendant
# qu'une tâche attend ailleurs est un défaut).
#
# Usage :  scripts/reprise/relancer.sh            # les mesures seules
#          scripts/reprise/relancer.sh --avec-ifs # + l'acquisition IFS en parallèle
#          scripts/reprise/relancer.sh --plan     # ne lance rien, montre l'état
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$RACINE" || { echo "❌ racine introuvable" >&2; exit 2; }
P=/home/cyril/miniforge3/envs/llm-agent/bin/python3

case "${1:-}" in
  --plan) exec $P -u scripts/plan_scores.py ;;
esac

$P -u scripts/plan_scores.py
echo

if [ "${1:-}" = "--avec-ifs" ]; then
  # Le lot saute les mois déjà écrits ; deux passes ramassent ceux que le contrôle des
  # heures a refusés. Journal séparé : la ressource est distincte, la trace aussi.
  if [ -z "$(scripts/pids_de.sh scripts/lot_ifs_2025_2026.sh)" ]; then
    nohup bash -c 'for p in 1 2 3; do scripts/lot_ifs_2025_2026.sh; \
                   grep -q "les 19 mois demandés" logs/lot_ifs_2025_2026.log && break; done' \
          >> logs/lot_ifs_2025_2026.log 2>&1 &
    echo "▶ acquisition IFS lancée en fond (réseau) — logs/lot_ifs_2025_2026.log"
  else
    echo "▶ acquisition IFS déjà en cours — rien relancé"
  fi
fi

TACHES=$($P -u scripts/plan_scores.py --taches)
if [ -z "$TACHES" ]; then
  echo "✅ aucune tâche de mesure restante."
  exit 0
fi
echo "$TACHES" | scripts/file_ressource.sh cpu
