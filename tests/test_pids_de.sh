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
#    Le témoin est un CHEMIN DE SCRIPT, c'est-à-dire le vrai cas d'usage : le motif doit
#    être un argument entier. « sleep 47 » n'en est pas un — c'est deux — et la première
#    version de ce test l'attendait, parce qu'elle avait été écrite pour le matcher
#    laxiste. Elle a échoué au premier passage du matcher strict, ce qui est exactement
#    son travail.
TEMOIN=$(mktemp -d)/temoin_pids_de.sh
printf '#!/usr/bin/env bash\nsleep 47\n' > "$TEMOIN"; chmod +x "$TEMOIN"
"$TEMOIN" & DORMEUR=$!
sleep 0.4
R=$(scripts/pids_de.sh "temoin_pids_de.sh" | grep -c "^${DORMEUR}$")
verifier "trouve un processus réel par son chemin d'argument" "1" "$R"

# ⑤ Et il ne rend PAS une commande qui se contente de MENTIONNER le motif — le défaut du
#    24/08, un shell orphelin dont la ligne portait « scripts/methode_maximale.py » au
#    milieu d'une liste de tâches.
# ⚠️ Une commande APRÈS le `sleep`, sinon bash optimise la DERNIÈRE commande d'un `-c` en
#    `exec` : sa ligne de commande devient « sleep 43 », le témoin ne mentionne plus rien,
#    et le test passe pour une mauvaise raison. Les deux premières versions de ce test
#    l'ont fait, dont une avec un `: ;` en tête qui ne changeait rien — c'est la dernière
#    commande qui est exécutée en place, pas la première.
bash -c "sleep 43; true # $TEMOIN dans un commentaire" & BAVARD=$!
sleep 0.4
R=$(scripts/pids_de.sh "temoin_pids_de.sh" | grep -c "^${BAVARD}$")
verifier "ignore une commande qui mentionne le motif" "0" "$R"
R=$(scripts/pids_de.sh "temoin_pids_de.sh" --contient | grep -c "^${BAVARD}$")
verifier "--contient la voit, lui" "1" "$R"
kill "$DORMEUR" "$BAVARD" 2>/dev/null
rm -rf "$(dirname "$TEMOIN")"

# ⑥ Sans motif, il refuse plutôt que de tout rendre.
scripts/pids_de.sh >/dev/null 2>&1 && { echo "  ❌ accepte l'absence de motif"; ECHECS=$((ECHECS+1)); } \
  || echo "  ✅ refuse l'absence de motif"

# ⑦ Une OPTION en première position est refusée — le faux négatif le plus coûteux.
#
# « pids_de.sh --contient motif » faisait chercher les processus contenant « --contient ».
# Aucun n'en contient : le garde rendait zéro, sans un mot, et « zéro » se lit « rien ne
# tourne ». Un faux positif bloque le travail et se voit ; un faux négatif AUTORISE un
# doublon et se lit comme une bonne nouvelle.
for opt in --contient --details; do
  if scripts/pids_de.sh "$opt" motif >/dev/null 2>&1; then
    echo "  ❌ accepte « $opt » comme motif"; ECHECS=$((ECHECS+1))
  else
    echo "  ✅ refuse « $opt » en première position"
  fi
done

# ⑧ Et le balayage ne fuit pas sur stderr quand un processus meurt pendant la lecture.
#    /proc change sous nos pieds ; l'ordre des redirections décide de qui voit l'erreur.
FUITES=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  FUITES=$((FUITES + $(scripts/pids_de.sh "bash" 2>&1 >/dev/null | wc -l)))
done
verifier "aucune fuite sur stderr en dix balayages" "0" "$FUITES"

echo
[ "$ECHECS" -eq 0 ] && echo "tous les contrôles passent" || echo "$ECHECS échec(s)"
exit "$ECHECS"
