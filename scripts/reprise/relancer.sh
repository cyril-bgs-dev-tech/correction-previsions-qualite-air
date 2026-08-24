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

# 🔴 Le préflight d'intégrité passe AVANT tout — il coûte des secondes et il a été écrit
# après que trois heures de mesures ont dû être refaites pour un corpus troué que la pile
# SIGNALAIT à chaque exécution, sans que personne ne le lise. Un diagnostic imprimé qui
# n'arrête rien n'est pas un contrôle.
if ! $P -u scripts/preflight.py; then
  echo
  echo "⛔ Le préflight refuse. Mesurer maintenant produirait des chiffres à refaire."
  echo "   Compléter les familles à trou, ou restreindre la fenêtre d'évaluation."
  echo "   Pour passer outre en connaissance de cause : --malgre-tout"
  [ "${1:-}" = "--malgre-tout" ] || exit 1
  echo "   ⚠️ --malgre-tout : les mesures porteront un indicateur d'époque."
fi
echo

$P -u scripts/plan_scores.py
echo

if [ "${1:-}" = "--avec-ifs" ]; then
  # Le lot saute les mois déjà écrits ; deux passes ramassent ceux que le contrôle des
  # heures a refusés. Journal séparé : la ressource est distincte, la trace aussi.
  # 🔴 Par la FILE DE RESSOURCE, jamais par un garde qu'on peut contourner — 24/08/2026.
  #
  # Un garde `if [ -z "$(pids_de …)" ]` protège ce script, pas la ressource : le 24/08
  # j'ai lancé un second lot à la main, hors de ce chemin, et deux téléchargements
  # concurrents ont repris sur le seau qui bride — la panne même que la nuit avait passée
  # à diagnostiquer. Le `flock` de `file_ressource.sh` rend le jumeau IMPOSSIBLE au lieu de
  # le déconseiller, et il vaut pour tout appelant, y compris moi en ligne de commande.
  #
  # La ressource « ecmwf » est DISTINCTE de « cpu » : les deux files tournent ensemble,
  # c'est le § 0-G. Sérialiser dedans, paralléliser entre.
  echo "data/processed/meteo/ifs_metropole_202607.parquet :: bash -c 'for p in 1 2 3; do scripts/lot_ifs_2025_2026.sh || true; grep -q \"les 19 mois demandés\" logs/lot_ifs_2025_2026.log && break; done'" \
    | nohup scripts/file_ressource.sh ecmwf >> logs/lot_ifs_2025_2026.log 2>&1 &
  sleep 2
  if grep -q "DÉJÀ en cours" logs/lot_ifs_2025_2026.log 2>/dev/null; then
    echo "▶ acquisition IFS déjà en cours — le verrou l'a refusée, rien relancé"
  else
    echo "▶ acquisition IFS lancée en fond (ressource « ecmwf ») — logs/lot_ifs_2025_2026.log"
  fi
fi

TACHES=$($P -u scripts/plan_scores.py --taches)
if [ -z "$TACHES" ]; then
  echo "✅ aucune tâche de mesure restante."
  exit 0
fi
# La file passe par le contrat de génération : empreinte du code, du corpus, liste figée.
# Voir `scripts/generation.sh` — six interruptions et deux chaînes cassées en une nuit ont
# montré qu'une file sans instantané immuable n'est pas pilotable.
echo "$TACHES" | scripts/generation.sh cpu "reprise-$(date +%d%m-%H%M)"
