#!/usr/bin/env bash
# Une file de tâches SÉRIALISÉE sur une ressource nommée, verrouillée contre les jumelles.
#
# Le défaut que ce script existe pour supprimer — 16/08/2026
# ----------------------------------------------------------
# Charge **0,45 sur 32 cœurs**, GPU à **1 %**, alors que trois chantiers longs étaient
# identifiés et attendaient leur tour : j'enchaînais à la main, un travail après l'autre.
# Confondre « la concurrence n'est pas la réponse par défaut » (§ 1) avec « ne rien lancer
# en parallèle » coûte exactement le temps qu'on croit économiser.
#
# La règle, et elle tient en une ligne
# -------------------------------------
#   **Sérialiser DANS une ressource, paralléliser ENTRE les ressources.**
#
# Une file bloquée sur du temps serveur — 84 % du coût d'une requête ADS — n'occupe aucun
# cœur : elle n'excuse donc jamais un CPU ou un GPU au repos.
#
# Ce que le verrou garantit
# --------------------------
# Deux files sur la MÊME ressource s'effondrent : trois ajustements LightGBM concurrents
# ont été mesurés à un ordre de grandeur de perte, six requêtes ADS sont rejetées. Le
# `flock` rend la faute impossible plutôt que déconseillée — et c'est aussi le garde-jumeau
# de la § 1 bis, en version qui ne peut pas se tromper de motif : on verrouille un
# **nom de ressource**, pas une ligne de commande qui se contient elle-même.
#
# Usage — les tâches arrivent sur l'entrée standard, une par ligne, `artefact :: commande` :
#
#   scripts/file_ressource.sh gpu <<'EOF'
#   reports/optuna_realmlp_O3.csv :: python3 -u scripts/optuna_realmlp.py --polluant O3
#   reports/optuna_realmlp_PM10.csv :: python3 -u scripts/optuna_realmlp.py --polluant PM10
#   EOF
#
# Chaque tâche passe par `lancer_controle.sh` : le verdict porte sur l'**artefact**, jamais
# sur le code de sortie, et une tâche qui n'écrit rien **arrête la file** — enchaîner sur
# un travail qui n'a rien produit propage le vide.
set -uo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE" || { echo "❌ racine introuvable" >&2; exit 2; }

[ $# -ge 1 ] || { echo "usage: $0 <ressource>  (tâches sur stdin, 'artefact :: commande')" >&2; exit 2; }
RESSOURCE="$1"
VERROU="/tmp/aq-file-${RESSOURCE}.lock"

exec 9>"$VERROU" || { echo "❌ verrou inaccessible : $VERROU" >&2; exit 2; }
if ! flock -n 9; then
  echo "⛔ file « $RESSOURCE » DÉJÀ en cours (verrou $VERROU) — rien lancé." >&2
  echo "   Sérialiser dans une ressource n'est pas négociable : deux files concurrentes" >&2
  echo "   sur le même matériel sont mesurées à un ordre de grandeur de perte." >&2
  exit 3
fi

mapfile -t TACHES
N=0; for l in "${TACHES[@]}"; do [[ -n "${l// }" && "$l" != \#* ]] && N=$((N+1)); done
echo "▶ file « $RESSOURCE » · $N tâche(s) · verrou pris $(date '+%H:%M:%S')"

i=0; DEPART=$(date +%s)
for ligne in "${TACHES[@]}"; do
  [[ -z "${ligne// }" || "$ligne" == \#* ]] && continue
  i=$((i+1))
  cible="${ligne%% :: *}"; commande="${ligne#* :: }"
  if [ "$cible" = "$ligne" ]; then
    echo "❌ ligne sans ' :: ' — artefact attendu obligatoire : $ligne" >&2
    exit 2
  fi
  echo "── [$i/$N] $(date '+%H:%M:%S') · $commande"
  if ! scripts/lancer_controle.sh "$cible" -- bash -c "$commande"; then
    echo "⛔ file « $RESSOURCE » ARRÊTÉE à la tâche $i/$N — artefact non produit."
    echo "   Les $((N-i)) suivantes ne sont PAS lancées : enchaîner sur un travail qui"
    echo "   n'a rien écrit propagerait le vide."
    exit 1
  fi
done
echo "✅ file « $RESSOURCE » terminée · $N/$N · $(( ($(date +%s) - DEPART) / 60 )) min"
