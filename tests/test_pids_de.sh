#!/usr/bin/env bash
# Le garde ne doit JAMAIS se voir, ni voir son appelant. Testé contre `pgrep`, qui les voit.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
ECHECS=0
verifier() { # nom, attendu, obtenu
  if [ "$2" = "$3" ]; then echo "  ✅ $1"
  else echo "  ❌ $1 — attendu « $2 », obtenu « $3 »"; ECHECS=$((ECHECS+1)); fi
}

# ① Le motif est le nom du garde lui-même, dans une substitution : le cas du 23/08 où
#    `pgrep -f "[f]ile_ressource.sh ads"` a matché le shell appelant, qui portait le motif
#    en clair plus loin dans la même commande.
R=$(scripts/pids_de.sh "pids_de" | wc -l)
verifier "ne se voit pas lui-même dans une substitution" "0" "$R"

# ② Le témoin : pgrep, lui, voit l'appelant. Sans ce contraste, le test ne dit pas ce
#    qu'il empêche.
P=$(pgrep -f "pids_de" 2>/dev/null | wc -l)
[ "$P" -ge 1 ] && echo "  ✅ témoin : pgrep -f voit l'appelant ($P processus)" \
  || { echo "  ⚠️ témoin muet — pgrep ne voit plus l'appelant, le contraste est perdu"; }

# ③ Un ancêtre lointain porte le motif : deux niveaux de bash au-dessus.
R=$(bash -c 'bash -c "scripts/pids_de.sh temoin_lointain_xyz"' | wc -l)
verifier "ne voit pas un ancêtre à deux niveaux" "0" "$R"

# ④ Il trouve tout de même un processus réel — un garde qui ne rend jamais rien est inutile.
sleep 47 & DORMEUR=$!
sleep 0.3
R=$(scripts/pids_de.sh "sleep 47" | grep -c "^${DORMEUR}$")
verifier "trouve un processus réel" "1" "$R"
kill "$DORMEUR" 2>/dev/null

# ⑤ Sans motif, il refuse plutôt que de tout rendre.
scripts/pids_de.sh >/dev/null 2>&1 && { echo "  ❌ accepte l'absence de motif"; ECHECS=$((ECHECS+1)); } \
  || echo "  ✅ refuse l'absence de motif"

echo
[ "$ECHECS" -eq 0 ] && echo "tous les contrôles passent" || echo "$ECHECS échec(s)"
exit "$ECHECS"
