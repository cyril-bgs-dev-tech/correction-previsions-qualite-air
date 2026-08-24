#!/usr/bin/env bash
# N tâches en parallèle, bornées par la mémoire et vérifiées sur l'ARTEFACT.
#
# Ce que ce script généralise
# ----------------------------
# `lancer_par_polluant.sh` a corrigé le défaut du 24/08 — charge 0,09 sur 32 cœurs parce
# que tout passait par une file sérialisée alors que « la parallélisation utile est ENTRE
# les ajustements » (`moteur.py`, 02/08). Mais il fige DEUX choses : les quatre polluants,
# et `methode_maximale.py`. Les tâches que le plan dérive n'ont ni l'une ni l'autre forme —
# les ablations jointes portent sur trois polluants et appellent un autre script.
#
# Ici la liste vient de l'appelant, au FORMAT QUE `plan_scores.py --taches` ÉMET DÉJÀ :
#
#     <artefact attendu> :: <commande>
#
# ce qui rend la reprise parallèle sans rien réécrire :
#
#     python3 scripts/plan_scores.py --taches | scripts/lancer_en_parallele.sh
#
# Les trois précautions, toutes reprises de mesures et non d'intuitions
# ---------------------------------------------------------------------
#   · **démarrages échelonnés** — le pic mémoire est au CHARGEMENT (11,6 Go le 08/08), pas
#     à l'ajustement (5,2 Go de palier) ; décalés, les pics ne se superposent pas ;
#   · **plafond par tâche** (`systemd-run`) — qui déborde meurt seul, code 137 (§ 1 quater) ;
#   · **verrou sur la RESSOURCE**, pas sur le script — deux lancements concurrents de
#     quatre tâches en feraient huit, et c'est la contention mesurée le 02/08 (§ 0-I).
#
# 🔴 Le verdict porte sur l'ARTEFACT, et il exige qu'il ait été RÉÉCRIT (§ 0-C)
# ------------------------------------------------------------------------------
# Un code de sortie 0 ne prouve rien : le 16/08 il venait d'un `echo`. Et l'existence seule
# ne prouve rien non plus — un fichier d'hier existe. On horodate AVANT, et on exige une
# mtime postérieure. C'est le seul contrôle que ni un plantage muet ni une reprise
# silencieuse ne peuvent franchir.
#
# Usage :  ... | scripts/lancer_en_parallele.sh [largeur] [décalage_s] [plafond] [ressource]
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE" || exit 2
LARGEUR="${1:-4}"; DECALAGE="${2:-90}"; PLAFOND="${3:-20G}"; RESSOURCE="${4:-cpu}"
JOURNAL="${5:-}"

# 🔴 Le journal se demande ICI, jamais par un tube — 24/08/2026, et c'est la règle C du
# projet violée dans ma propre commande de lancement.
#
# Lancé ainsi :  ... | scripts/lancer_en_parallele.sh 4 90 20G cpu | tee logs/G2.log
# le code de sortie appartient à `tee`. Le garde a correctement imprimé « ⛔ ABSENT » sur
# QUATRE artefacts, et la commande a rendu 0. Un contrôle dont le verdict est jeté par le
# tuyau qui le transporte ne protège de rien — et il est PIRE qu'absent, parce qu'il donne
# l'impression d'exister.
#
# La substitution de processus ci-dessous laisse `$?` au script : le journal est écrit et le
# verdict survit. C'est la seule forme qui ne se souvienne de rien.
[ -n "$JOURNAL" ] && exec > >(tee "$JOURNAL") 2>&1
P=/home/cyril/miniforge3/envs/llm-agent/bin/python3
mkdir -p logs

exec 9>"/tmp/aq-file-${RESSOURCE}.lock"
if ! flock -n 9; then
  echo "⛔ la ressource « ${RESSOURCE} » est déjà prise — rien lancé." >&2; exit 3
fi

mapfile -t LIGNES < <(grep -E ' :: ' | grep -v '^#')
[ "${#LIGNES[@]}" -gt 0 ] || { echo "aucune tâche sur l'entrée standard."; exit 0; }

DEBUT=$(date +%s)
echo "▶ ${#LIGNES[@]} tâche(s) · largeur ${LARGEUR} · décalage ${DECALAGE}s · plafond ${PLAFOND}/tâche"

declare -A CIBLE PIDCIBLE
i=0
for ligne in "${LIGNES[@]}"; do
  cible="${ligne%% :: *}"; cmd="${ligne#* :: }"
  # La largeur se tient en attendant qu'un emplacement se libère, jamais en sérialisant.
  while [ "$(jobs -rp | wc -l)" -ge "$LARGEUR" ]; do sleep 5; done
  i=$((i + 1))
  journal="logs/parallele_$(basename "${cible%.csv}" | tr -c 'A-Za-z0-9_-' '_').log"
  systemd-run --user --scope -q -p "MemoryMax=$PLAFOND" -p MemorySwapMax=0 -- \
    bash -c "cd '$RACINE' && ${cmd/#python3/$P}" > "$journal" 2>&1 &
  PIDCIBLE[$!]="$cible"; CIBLE[$cible]="$journal"
  printf '  [%d/%d] %s\n         → %s\n' "$i" "${#LIGNES[@]}" "$cible" "$journal"
  [ "$i" -lt "${#LIGNES[@]}" ] && sleep "$DECALAGE"
done

for pid in "${!PIDCIBLE[@]}"; do wait "$pid"; done

# ── Le verdict : l'artefact existe ET il est postérieur au lancement ────────────────────
echo "═══ $(date '+%H:%M:%S') · $((($(date +%s) - DEBUT) / 60)) min ═══"
MANQUE=0
for cible in "${!CIBLE[@]}"; do
  if [ ! -f "$cible" ]; then
    echo "  ⛔ ABSENT   $cible — voir ${CIBLE[$cible]}"; MANQUE=1
  elif [ "$(stat -c %Y "$cible")" -lt "$DEBUT" ]; then
    echo "  ⛔ NON RÉÉCRIT $cible (mtime $(stat -c %y "$cible" | cut -c1-16)) — voir ${CIBLE[$cible]}"; MANQUE=1
  else
    echo "  ✅ $cible · $(wc -l < "$cible") lignes"
  fi
done
exit "$MANQUE"
