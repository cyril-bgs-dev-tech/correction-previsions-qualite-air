#!/usr/bin/env bash
# Les quatre polluants EN PARALLÈLE — la parallélisation utile est entre les ajustements.
#
# Ce que ce script corrige
# -------------------------
# `moteur.py` porte une mesure du 02/08 : « LightGBM plafonne à ~1,5 cœur quel que soit
# n_jobs — le jeu est trop petit pour que la synchronisation des fils soit rentable. La
# parallélisation utile est ENTRE les ajustements, pas dedans. »
#
# Et pourtant tout passait par une file « cpu » sérialisée. Résultat mesuré le 24/08 à
# 13 h : **charge 0,09 sur 32 cœurs**. Une ressource au repos pendant qu'une tâche attend
# est un défaut, pas une prudence (§ 0-G) — et ici la tâche n'attendait même pas, elle
# faisait la queue derrière elle-même.
#
# ⚠️ La règle « un seul lot » de `CLAUDE.md` vient d'un essai en `n_jobs=-1`, où trois
# ajustements demandaient 96 fils sur 32 cœurs. À `n_jobs=8`, quatre lots en demandent 32 —
# et LightGBM n'en utilise réellement que ~1,5 chacun. Ce n'est pas la même situation.
#
# Deux précautions, l'une mesurée et l'autre structurelle :
#   · **démarrages ÉCHELONNÉS** — le pic mémoire est au CHARGEMENT (11,6 Go mesurés le
#     08/08), pas à l'ajustement (5,2 Go de palier). Quatre chargements simultanés
#     demanderaient 46 Go d'un coup ; décalés de 90 s, ils ne se superposent pas ;
#   · **plafond mémoire par lot** via `systemd-run` — un processus qui déborde dans un
#     cgroup borné meurt seul, code 137, machine intacte (§ 1 quater).
#
# Usage :  scripts/lancer_par_polluant.sh "--ablation --exclure geoscf,feux --fenetre complete --avec-ifs"
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE" || exit 2
P=/home/cyril/miniforge3/envs/llm-agent/bin/python3
ARGS="${1:?usage: $0 \"<arguments de methode_maximale>\"}"
DECALAGE="${2:-90}"
PLAFOND="${3:-20G}"

# Le verrou porte sur la ressource, pas sur le script : deux lancements concurrents de
# QUATRE lots feraient huit, et là on retomberait dans la contention mesurée.
exec 9>/tmp/aq-file-cpu.lock
if ! flock -n 9; then
  echo "⛔ la ressource « cpu » est déjà prise — rien lancé." >&2; exit 3
fi

echo "▶ quatre polluants en parallèle · décalage ${DECALAGE}s · plafond ${PLAFOND}/lot"
echo "  $ARGS"
PIDS=""
for p in NO2 O3 PM10 PM25; do
  J="logs/parallele_${p}.log"
  systemd-run --user --scope -q -p "MemoryMax=$PLAFOND" -p MemorySwapMax=0 -- \
    $P -u scripts/methode_maximale.py --polluant "$p" --horizon 2 $ARGS > "$J" 2>&1 &
  PIDS="$PIDS $!"
  echo "  $p lancé · $J"
  [ "$p" = "PM25" ] || sleep "$DECALAGE"
done

echo "▶ attente · charge $(uptime | grep -oE 'load average.*')"
CODE=0
for pid in $PIDS; do wait "$pid" || CODE=1; done
echo "═══ terminé · $(date '+%H:%M:%S') ═══"
for p in NO2 O3 PM10 PM25; do
  echo "  $p : $(grep -cE 'Écrit' "logs/parallele_${p}.log" 2>/dev/null) artefact(s) · "\
"$(grep -oE '[0-9.]+ min$' "logs/parallele_${p}.log" 2>/dev/null | tail -1)"
done
exit "$CODE"
