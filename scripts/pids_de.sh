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
# 🔴 Et exclure ses ancêtres ne suffisait pas — trouvé en le testant, le 24/08.
#
# Le premier essai a rendu un shell orphelin d'une commande antérieure, dont la ligne
# contenait `scripts/methode_maximale.py` au milieu d'une liste de tâches. Ce n'était ni
# un ancêtre ni un faux positif sur soi : c'était un VRAI processus qui MENTIONNE le
# motif. Un garde-jumeau qui compte les commandes parlant du script est aussi faux qu'un
# garde qui se voit lui-même — il bloque le travail en annonçant un jumeau inexistant,
# ce que le 08/08 et le 17/08 ont déjà coûté.
#
# La comparaison porte donc sur les ARGUMENTS pris un par un, pas sur la ligne recollée.
# Un vrai lot a `scripts/methode_maximale.py` comme argument entier ; un shell qui en
# parle l'a enfoui dans un `-c "…"`, qui est un seul argument gigantesque.
#
# Usage :  kill $(scripts/pids_de.sh "extraire_ifs.py")
#          scripts/pids_de.sh "scripts/methode_maximale.py" --details
#          scripts/pids_de.sh "quelque-chose" --contient   # ancien comportement, laxiste
set -uo pipefail
[ $# -ge 1 ] || { echo "usage: $0 <motif> [--details]" >&2; exit 2; }
MOTIF="$1"
LAXISTE=0
for a in "$@"; do [ "$a" = "--contient" ] && LAXISTE=1; done
export LAXISTE

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
  # Chaque argument séparément : le motif doit ÊTRE un argument, ou en être le suffixe
  # après un « / ». « scripts/x.py » matche « /chemin/scripts/x.py » et « scripts/x.py »,
  # jamais un `bash -c "… scripts/x.py …"` dont c'est un fragment.
  trouve=""
  if [ "${LAXISTE:-}" = "1" ]; then
    case "$cmd" in *"$MOTIF"*) trouve=1 ;; esac
  else
    while IFS= read -r -d '' arg; do
      case "$arg" in
        "$MOTIF"|*/"$MOTIF") trouve=1; break ;;
      esac
    done < "$d/cmdline" 2>/dev/null
  fi
  case "$trouve" in
    1)
      if [ "${2:-}" = "--details" ] || [ "${3:-}" = "--details" ]; then
        printf '%s\t%s\n' "$p" "${cmd:0:110}"
      else
        printf '%s\n' "$p"
      fi ;;
  esac
done
