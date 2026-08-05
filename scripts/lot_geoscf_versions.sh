#!/usr/bin/env bash
# Reprise du 05/08 : mesurer l'apport GEOS-CF **par flux**, jamais sur le corpus mixte.
#
# v1 (12z, 2023-08→2025-12) et v2 (09z, 2026-01→) ne sont pas le même prédicteur : sur
# octobre 2025, où les deux tournaient, l'ozone diffère de +15,41 µg/m³ en moyenne.
# Un corpus mixte donne au modèle une variable qui change de définition en janvier 2026.
#
# Deux fronts en parallèle : n_jobs=8 par ajustement, 32 cœurs → 16 fils, sans contention.
# ⚠️ Le journal ne filtre RIEN (règle 1 bis) et le contrôle de fin porte sur l'artefact.
set -u
cd /mnt/d/Projet_Air_Quality

front() {                    # $1 = étiquette · $2.. = "polluant:version"
  local etq=$1; shift
  for u in "$@"; do
    local pol=${u%%:*} ver=${u##*:}
    local cible="reports/apport_geoscf_${pol}_h2_${ver}.csv"
    echo "══ [$etq] $pol / $ver · $(date +%H:%M:%S) ══"
    python3 scripts/apport_geoscf.py --polluant "$pol" --horizon 2 --version "$ver" 2>&1
    if [ -f "$cible" ]; then
      echo "══ [$etq] $pol / $ver OK → $cible ($(date +%H:%M:%S))"
    else
      echo "══ [$etq] $pol / $ver ÉCHEC — AUCUN fichier écrit ($(date +%H:%M:%S))"
    fi
  done
  echo "══ [$etq] FRONT TERMINÉ $(date +%H:%M:%S)"
}

front "$@"
