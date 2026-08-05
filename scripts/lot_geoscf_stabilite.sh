#!/usr/bin/env bash
# Deux questions qui restent après la mesure par flux du 05/08 :
#   ① le gain est-il stable d'une partition à l'autre ? (la barre ±2,02 pt connue porte sur
#      un score absolu, pas sur un écart apparié)
#   ② sa baisse en v2 vient-elle du produit ou de la famine de données ?
#
# Coût mesuré sur la passe unitaire : 1,6 min par graine en v2, ~3,8 min en v1.
# Deux fronts × n_jobs=8 = 16 fils sur 32 cœurs — la contention mémoire reste hors de portée.
# ⚠️ Aucun filtre sur le journal (règle 1 bis) ; contrôle de fin sur l'artefact.
set -u
cd /mnt/d/Projet_Air_Quality

echo "══ [$1] DÉBUT $(date +%H:%M:%S)"
shift
for u in "$@"; do
  IFS=: read -r quoi pol ver <<<"$u"
  case $quoi in
    stab) cible="reports/stabilite_geoscf_${pol}_${ver}.csv"
          cmd=(python3 scripts/stabilite_apport_geoscf.py --polluant "$pol" --version "$ver" --graines 4) ;;
    taille) cible="reports/controle_taille_geoscf_${pol}.csv"
          cmd=(python3 scripts/controle_taille_geoscf.py --polluant "$pol") ;;
    *) echo "== inconnu : $u"; continue ;;
  esac
  echo "══ $quoi $pol $ver · $(date +%H:%M:%S) ══"
  "${cmd[@]}" 2>&1
  [ -f "$cible" ] && echo "══ $quoi $pol $ver OK → $cible ($(date +%H:%M:%S))" \
                  || echo "══ $quoi $pol $ver ÉCHEC — AUCUN fichier écrit ($(date +%H:%M:%S))"
done
echo "══ FRONT TERMINÉ $(date +%H:%M:%S)"
