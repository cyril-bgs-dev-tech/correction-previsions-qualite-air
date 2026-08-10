#!/usr/bin/env bash
# Échantillonne la mémoire de la machine pendant un lot — et laisse une trace qui SURVIT
# à la mort de la VM.
#
# Pourquoi ce script existe (08/08/2026)
# --------------------------------------
# Trois coupures WSL en vingt-six minutes, toutes 8 à 11 min après le lancement du même
# lot, et **aucune trace noyau** : ni OOM, ni panique, ni segfault. Un lot qui tue sa
# machine ne laisse rien à lire — sauf si quelqu'un écrivait pendant qu'il tournait.
#
# Deux choix qui ne sont pas des détails :
#   * la trace est écrite sur le **système de fichiers Linux** ($HOME), jamais sur /mnt/d.
#     drvfs a déjà perdu des écritures en silence sur ce projet, et une trace perdue au
#     redémarrage est exactement la trace qu'on voulait ;
#   * les lignes sont suivies d'un `sync` : sans lui, les dernières secondes — les seules
#     qui expliquent la mort — restent dans le cache et disparaissent avec la VM.
#
# ⚠️ Mais PAS à chaque ligne — corrigé le 10/08/2026 (CLAUDE.md § 1 quinquies, geste ②).
# La version d'origine forçait un `sync` toutes les 2 s, soit ~30 barrières de durabilité
# par minute sur le système de fichiers que le lot utilise aussi. Le 10/08, cinq minutes
# après l'avoir armée pour la première fois à côté d'un lot, le journal ext4 s'est figé :
# `sync` bloqué 61 min en `jbd2_log_wait_commit`, huit `systemd-journald` en `D`, et le lot
# gelé sans rien produire. **Une occurrence ne fait pas une cause** — mais suivre un RSS
# n'exige aucune durabilité, donc le correctif est gratuit et la suspicion suffit.
# Un `sync` tous les `n_sync` échantillons : la trace reste, la barrière devient rare.
#
# Usage : scripts/veille_memoire.sh <motif_de_processus> [fichier_sortie] [pas_secondes] [n_sync]
set -u
motif="${1:?motif de processus à suivre, ex. methode_maximale.py}"
sortie="${2:-$HOME/veille_memoire.csv}"
pas="${3:-2}"
n_sync="${4:-10}"

echo "horodatage,mem_utilisee_Mo,mem_dispo_Mo,swap_Mo,rss_suivi_Mo,n_proc" > "$sortie"
sync "$sortie"

i=0
while :; do
  read -r used avail <<< "$(free -m | awk 'NR==2 {print $3, $7}')"
  swap=$(free -m | awk 'NR==3 {print $3}')
  read -r rss n <<< "$(ps -eo rss,cmd --no-headers 2>/dev/null |
                        grep -F -- "$motif" | grep -v grep |
                        awk '{s += $1; c++} END {printf "%d %d", s / 1024, c}')"
  printf '%s,%s,%s,%s,%s,%s\n' \
    "$(date +%T)" "$used" "$avail" "$swap" "${rss:-0}" "${n:-0}" >> "$sortie"
  i=$((i + 1))
  [ $((i % n_sync)) -eq 0 ] && sync "$sortie"
  sleep "$pas"
done
