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
[ $# -ge 1 ] || { echo "usage: $0 <motif> [--details] [--contient]" >&2; exit 2; }
MOTIF="$1"

# 🔴 Le motif est le PREMIER argument, et rien ne l'imposait — 24/08/2026.
#
# Appelé « pids_de.sh --contient methode_maximale », `$1` vaut « --contient » : le garde
# cherche alors les processus dont la ligne de commande contient « --contient », et n'en
# trouve JAMAIS. Il rend zéro, sans un mot, et « zéro » se lit « rien ne tourne ».
#
# C'est le défaut que la § 1 bis nomme — *ce garde ment dans les deux sens* — sous sa forme
# la plus coûteuse : le faux négatif. Un faux positif bloque le travail et se voit ; un faux
# négatif AUTORISE un doublon et se lit comme une bonne nouvelle. Le 31/07, deux `lot_ifs.sh`
# concurrents ont fait perdre deux mois de données à cause exactement de cela.
#
# On ne corrige pas cela par de la vigilance : on le rend IMPOSSIBLE.
case "$MOTIF" in
  -*) echo "⛔ « $MOTIF » est une option, pas un motif. Le motif vient EN PREMIER :" >&2
      echo "     $0 <motif> [--details] [--contient]" >&2
      echo "   Sans ce refus, le garde chercherait « $MOTIF » dans les lignes de commande," >&2
      echo "   n'en trouverait aucune, et son zéro se lirait « rien ne tourne »." >&2
      exit 2 ;;
esac
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
  # ⚠️ L'ORDRE des redirections décide de qui voit l'erreur — 24/08/2026.
  # `tr … < "$f" 2>/dev/null` : bash applique `< "$f"` d'ABORD, et si le fichier a disparu
  # — /proc change sous nos pieds à chaque balayage — il imprime son « No such file » avant
  # que `2>` ne détourne stderr. Le message s'échappe donc malgré la redirection.
  # `2>/dev/null` posé EN PREMIER couvre l'échec de la redirection qui le suit.
  cmd=$(tr '\0' ' ' 2>/dev/null < "$d/cmdline") || continue
  [ -n "$cmd" ] || continue
  # Chaque argument séparément : le motif doit ÊTRE un argument, ou en être le suffixe
  # après un « / ». « scripts/x.py » matche « /chemin/scripts/x.py » et « scripts/x.py »,
  # jamais un `bash -c "… scripts/x.py …"` dont c'est un fragment.
  trouve=""
  if [ "${LAXISTE:-}" = "1" ]; then
    case "$cmd" in *"$MOTIF"*) trouve=1 ;; esac
  else
    # ⚠️ La redirection porte le `2>/dev/null`, pas la boucle : un processus qui meurt
    # pendant le balayage est normal — /proc change sous nos pieds — et une erreur affichée
    # pour cela masquerait les vraies. Sans ce garde, la sortie standard du lot se
    # remplissait de « No such file or directory ».
    { while IFS= read -r -d '' arg; do
        case "$arg" in
          "$MOTIF"|*/"$MOTIF") trouve=1; break ;;
        esac
      done < "$d/cmdline"; } 2>/dev/null
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
