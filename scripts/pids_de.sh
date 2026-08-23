#!/usr/bin/env bash
# Les PID qui correspondent à un motif — SANS jamais pouvoir se voir soi-même.
#
# La règle que ce script mécanise, et les deux fois où elle a été violée
# ----------------------------------------------------------------------
# `CLAUDE.md` § 1 bis : « on ne tue jamais par motif ». Le motif figure dans la ligne de
# commande du shell qui l'évalue, donc `pkill -f motif` tue l'appelant. Deux occurrences :
#
#   10/08  `pkill -f "veille_memoire.sh"` a tué le shell qui exécutait la commande ;
#   23/08  une commande contenant `pgrep -af "…|file_ressource.sh ads"` plus loin dans la
#          même ligne a fait matcher `pgrep -f "[f]ile_ressource.sh ads"` sur elle-même.
#          Le `[f]` protège le motif contre lui-même, jamais contre une AUTRE occurrence.
#
# La règle disait « deux appels séparés ». Ce n'est pas suffisant non plus : le second
# appel peut porter le motif dans son propre `$(...)`. La seule forme sûre est de rendre
# le garde INCAPABLE de se voir — d'où l'exclusion de tout l'arbre des ancêtres.
#
# Une règle violée deux fois après avoir été écrite devient du code, ou elle disparaît.
#
# Usage :  kill $(scripts/pids_de.sh "extraire_ifs")
#          scripts/pids_de.sh "methode_maximale" --details
set -uo pipefail
[ $# -ge 1 ] || { echo "usage: $0 <motif> [--details]" >&2; exit 2; }
MOTIF="$1"

# La chaîne complète des ancêtres, jusqu'à init. Un `$(...)` s'exécute dans un enfant du
# shell appelant : exclure le seul $$ laisserait passer le parent, qui porte le motif.
EXCLUS=" "
pid=$$
while [ "$pid" -gt 1 ] 2>/dev/null; do
  EXCLUS="$EXCLUS$pid "
  pid=$(awk '{print $4}' "/proc/$pid/stat" 2>/dev/null) || break
  [ -n "$pid" ] || break
done

for d in /proc/[0-9]*; do
  p=${d#/proc/}
  case "$EXCLUS" in *" $p "*) continue ;; esac
  cmd=$(tr '\0' ' ' < "$d/cmdline" 2>/dev/null) || continue
  [ -n "$cmd" ] || continue
  case "$cmd" in
    *"$MOTIF"*)
      if [ "${2:-}" = "--details" ]; then
        printf '%s\t%s\n' "$p" "${cmd:0:110}"
      else
        printf '%s\n' "$p"
      fi ;;
  esac
done
