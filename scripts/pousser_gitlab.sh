#!/usr/bin/env bash
# Pousser vers GitLab, protection de branche comprise — et VÉRIFIÉE, jamais supposée.
#
# Les trois défauts que ce script existe pour supprimer — 25/08/2026
# ------------------------------------------------------------------
# ① `~/.git-credentials` porte PLUSIEURS lignes (gitlab, github). Un `sed` appliqué au
#    fichier entier concatène les tokens avec un retour ligne : l'en-tête `PRIVATE-TOKEN`
#    devient invalide, curl rend **HTTP 000 en 60 ms**, et l'appel échoue SANS RIEN DIRE
#    d'utile. Ici on cible la ligne de l'hôte.
#
# ② Un `PATCH` qui échoue ainsi ne lève pas la protection — mais un `PATCH` de RESTAURATION
#    qui échoue de la même façon ne la remet pas non plus. La séquence « lever, pousser,
#    remettre » peut donc laisser la branche dans l'un OU l'autre état sans le signaler.
#    **Le code HTTP ne suffit pas : on relit l'état.**
#
# ③ Et le plus souvent, lever ne sert à rien : un push en AVANCE RAPIDE passe sur une branche
#    protégée. On ne lève que si le push simple a été refusé.
#
# Usage :  scripts/pousser_gitlab.sh [branche]
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE" || exit 2
BRANCHE="${1:-main}"
PROJET="cyril.bgs.dev%2Fcorrection-previsions-qualite-air"
API="https://gitlab.com/api/v4/projects/$PROJET/protected_branches"
TOKEN=$(command grep -m1 '@gitlab\.com' ~/.git-credentials 2>/dev/null \
        | sed -E 's#.*://[^:]+:([^@]+)@.*#\1#')
[ -n "$TOKEN" ] || { echo "⛔ aucun identifiant gitlab dans ~/.git-credentials" >&2; exit 2; }

etat_force_push() {  # rend "true", "false", ou "" si l'API n'a pas répondu
  curl -s --max-time 30 -H "PRIVATE-TOKEN: $TOKEN" "$API" 2>/dev/null \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print(next((str(b.get('allow_force_push')).lower() for b in d if b['name']=='$BRANCHE'),''))" 2>/dev/null
}
regler_force_push() {  # $1 = true|false — puis on RELIT, on ne croit pas le code HTTP
  curl -s --max-time 30 -X PATCH -H "PRIVATE-TOKEN: $TOKEN" \
       "$API/$BRANCHE?allow_force_push=$1" -o /dev/null
  local vu; vu=$(etat_force_push)
  [ "$vu" = "$1" ] && echo "  force_push = $vu ✅" || {
    echo "  🔴 force_push demandé « $1 », LU « ${vu:-∅} » — l'API n'a pas obéi." >&2; return 1; }
}

echo "▶ push simple vers gitlab/$BRANCHE"
if git push gitlab "$BRANCHE" 2>&1 | sed -E 's/(glpat|ghp)[-_][A-Za-z0-9._-]+/\1-***/g'; then
  if git merge-base --is-ancestor "gitlab/$BRANCHE" HEAD 2>/dev/null; then
    echo "✅ avance rapide — la protection n'a jamais eu à être levée."; exit 0
  fi
fi

echo "▶ refusé : la branche a divergé. Levée TEMPORAIRE de la protection."
regler_force_push true || exit 3
git push gitlab "$BRANCHE" --force-with-lease 2>&1 | sed -E 's/(glpat|ghp)[-_][A-Za-z0-9._-]+/\1-***/g'
CODE=$?
echo "▶ remise en protection"
regler_force_push false || {
  echo "🔴🔴 LA BRANCHE EST RESTÉE SANS PROTECTION — la remettre à la main :" >&2
  echo "     Settings → Repository → Protected branches → $BRANCHE" >&2; exit 4; }
exit "$CODE"
