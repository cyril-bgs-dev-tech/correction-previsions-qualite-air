#!/usr/bin/env bash
# Répond à la question qui n'a pas été posée le 10/08 : « la machine est-elle libre ? »
#
# Ce jour-là, un rendu PDF + PNG de pages départementales (13:01-13:08) a tourné PENDANT
# l'ajustement LightGBM de NO₂ lancé à 12:34. CLAUDE.md § 1 l'interdit noir sur blanc —
# « une bibliothèque qui prend déjà tous les cœurs ne se parallélise pas en la lançant
# plusieurs fois », mesuré à ×12,9 sur ce dépôt. La règle était écrite ; le contrôle qui
# l'applique n'existait pas. Le voici : une commande, avant tout lancement lourd.
#
# Aucun `grep` n'est utilisé : le filtrage se fait dans `awk`, sur le champ `args`. C'est
# délibéré — un `grep` dont le motif nomme ce qu'il cherche apparaît lui-même dans `ps` et
# se compte comme un jumeau (CLAUDE.md § 1 bis). Le tri par awk ne peut pas se voir.
#
# Code de sortie : 0 si la machine est libre, 1 si un travail lourd tourne.
set -u

echo "── travaux lourds en cours ──"
ps -eo pid,etimes,rss,args --no-headers | awk -v self=$$ '
  $1 == self { next }
  { cmd = ""; for (i = 4; i <= NF; i++) cmd = cmd " " $i }
  cmd ~ /machine_libre|veille_hote|veille_memoire/ { next }
  cmd ~ /python3 .*scripts\/|chrom|puppeteer|playwright|ollama runner|node .*(pdf|render)/ {
      printf "  ⚠️ pid %-7s %6.1f min  %5.1f Go  %s\n", $1, $2 / 60, $3 / 1048576, substr(cmd, 2, 80)
      n++
  }
  END {
      if (n == 0) print "  aucun — la machine est libre"
      exit (n > 0)
  }'
libre=$?

echo "── mémoire ──"
free -g | awk 'NR==2 {printf "  VM      : %d Go utilisés, %d Go disponibles sur %d\n", $3, $7, $2}'
powershell.exe -NoProfile -Command \
  '$vm = Get-Process vmmemWSL -ErrorAction SilentlyContinue
   $os = Get-CimInstance Win32_OperatingSystem
   "  hote    : vmmemWSL {0:N1} Go | {1:N1} Go libres sur {2:N1} | engagement {3:N1}/{4:N1} Go" -f
     $(if ($vm) { ($vm | Measure-Object WorkingSet64 -Sum).Sum / 1GB } else { 0 }),
     ($os.FreePhysicalMemory / 1MB), ($os.TotalVisibleMemorySize / 1MB),
     (($os.TotalVirtualMemorySize - $os.FreeVirtualMemory) / 1MB), ($os.TotalVirtualMemorySize / 1MB)' \
  2>/dev/null | tr -d '\r'

echo "── veille hôte ──"
if [ -s /mnt/c/Users/Cyril/veille_hote.csv ]; then
  echo "  active · $(( $(wc -l < /mnt/c/Users/Cyril/veille_hote.csv) - 1 )) échantillons"
else
  echo "  ❌ ABSENTE — lancer \`scripts/veille_hote.sh demarrer\` avant tout lot"
fi

exit $libre
