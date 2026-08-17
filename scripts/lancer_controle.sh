#!/usr/bin/env bash
# Lance une commande et rend un verdict fondé sur l'ARTEFACT, jamais sur le code de sortie.
#
# Le défaut que ce script existe pour supprimer
# ----------------------------------------------
# Le 16/08/2026, deux fois dans la même session :
#
#   cmd | head -5 ; echo "code=$?"        → le code lu est celui de `head`, toujours 0
#   cmd > logs/x.log ; echo "code=$?"     → le `echo` réussit même si la redirection échoue
#
# La seconde a fait annoncer « archivage PREV'AIR terminé, exit 0 » pour un script qui
# n'avait pas tourné du tout — le répertoire courant avait changé et `logs/` n'existait
# pas depuis là. Un rapport de succès sur un travail non fait est pire qu'une erreur : il
# ferme la question.
#
# Ce que le script impose, et qui n'est pas négociable
# -----------------------------------------------------
#  1. la commande n'est JAMAIS dans un tube — `$?` lui appartient ;
#  2. le verdict porte sur un artefact NOMMÉ, qui doit exister ET avoir été réécrit
#     pendant l'exécution. Un fichier laissé par une exécution précédente ne compte pas ;
#  3. les chemins sont résolus depuis la racine du dépôt, pas depuis $PWD — l'état d'un
#     shell ne traverse pas une commande (règle F).
#
# Usage :
#   scripts/lancer_controle.sh <artefact attendu> -- <commande...>
#
# Exemple :
#   scripts/lancer_controle.sh reports/gain_reglage_O3.csv -- \
#       python3 -u scripts/gain_reglage.py --polluant O3
set -uo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE" || { echo "❌ racine introuvable : $RACINE" >&2; exit 2; }

[ $# -ge 3 ] || { echo "usage: $0 <artefact> -- <commande...>" >&2; exit 2; }
CIBLE="$1"; shift
[ "$1" = "--" ] || { echo "❌ attendu '--' après l'artefact, reçu '$1'" >&2; exit 2; }
shift

# Horodatage AVANT, pour distinguer « réécrit » de « déjà là ». `stat` sur un fichier
# absent doit valoir 0, pas faire échouer le script — d'où le `|| echo 0`.
AVANT=0
[ -e "$CIBLE" ] && AVANT=$(stat -c %Y "$CIBLE" 2>/dev/null || echo 0)
DEPART=$(date +%s)

printf '▶ %s\n  artefact attendu : %s\n' "$*" "$CIBLE"
"$@"                       # ← jamais de tube ici : `$?` doit appartenir à la commande
CODE=$?
DUREE=$(( $(date +%s) - DEPART ))

# ── Le verdict : trois questions, dans cet ordre ────────────────────────────────────
if [ ! -e "$CIBLE" ]; then
  echo "❌ ÉCHEC · code=$CODE · ${DUREE}s · AUCUN artefact écrit : $CIBLE"
  exit 1
fi
APRES=$(stat -c %Y "$CIBLE" 2>/dev/null || echo 0)
if [ "$APRES" -le "$AVANT" ]; then
  echo "❌ ÉCHEC · code=$CODE · ${DUREE}s · artefact NON RÉÉCRIT (daté du $(date -d @"$APRES" '+%d/%m %H:%M')) : $CIBLE"
  echo "   Un fichier laissé par une exécution précédente ne prouve rien."
  exit 1
fi
if [ "$CODE" -ne 0 ]; then
  # L'artefact est là ET frais, mais la commande a échoué : les deux signaux se
  # contredisent. On ne tranche pas à la place de l'appelant — on le dit.
  echo "⚠️ CONTRADICTION · code=$CODE mais artefact réécrit · ${DUREE}s · $CIBLE"
  echo "   Sortie partielle probable : vérifier le contenu avant de s'en servir."
  exit 1
fi
echo "✅ code=0 · ${DUREE}s · $CIBLE réécrit ($(du -h "$CIBLE" | cut -f1))"
