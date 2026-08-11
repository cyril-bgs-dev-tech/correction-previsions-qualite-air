#!/usr/bin/env bash
# Leur chaîne de méthode — CHIMERE brut → krigeage du biais — contre la nôtre.
#
# Ce que ce lot ajoute au duel PREV'AIR déjà publié
# ---------------------------------------------------
# Le duel direct (§ 10 quater) oppose nos sorties à LEUR PRODUIT, sur onze jours d'été.
# Celui-ci oppose nos sorties à LEUR MÉTHODE, sur trois ans : AS-CHI est un krigeage du
# résidu observation−modèle, pas un apprentissage (sourcé, commit 29b9fcc). Or CHIMERE
# est un membre de l'ensemble CAMS et ce dépôt l'archive aux stations : on peut donc
# rejouer leur chaîne depuis LEUR point de départ, sur exactement nos lignes.
#
# ⚠️ Ce n'est pas PREV'AIR. Leur CHIMERE est national — maille fine, inventaire français,
# assimilation ; le nôtre est le membre européen à 10 km. Le script le réaffirme à chaque
# exécution et la réserve doit accompagner toute citation.
#
# Pourquoi un lot, pour quatre commandes
# ----------------------------------------
# La plateforme corrompt la mémoire (REPRISE § ⑤) : ~1 tentative sur 5 meurt en segfault
# ou emporte la VM, sans que le résultat soit faux pour autant. Un lot qui réessaie
# aboutit ; une commande lancée à la main n'aboutit qu'avec de la chance et de la
# surveillance humaine. Le plafond mémoire n'est pas une optimisation : il rend la panne
# observable au lieu de tuer l'hôte (§ 1 quater).
#
# Usage : bash scripts/lot_duel_chimere.sh [POLLUANT ...]      (défaut : les quatre)
set -u
cd "$(dirname "$0")/.." || exit 1

H=2                    # échéance J+1 (les tranches sont 1-24 h = J0, 25-48 h = J+1)
ESSAIS_MAX=8
PLAFOND=24G            # même plafond que le lot d'ablation, dont le pic mesuré est 18,9 Go
JOURNAL=logs/lot_duel_chimere.log
VEILLE="$HOME/veille_memoire_duel_chimere.csv"   # hors /mnt/d : doit survivre à la coupure
MARQUEUR="CAMS + notre correction + krigeage"    # la DERNIÈRE ligne écrite du CSV : sa
                                                 # présence atteste un fichier complet
POLLUANTS=("$@")
[ ${#POLLUANTS[@]} -eq 0 ] && POLLUANTS=(O3 NO2 PM10 PM25)
mkdir -p logs

echo "=== duel CHIMERE démarré $(date '+%F %T') · ${POLLUANTS[*]} · plafond $PLAFOND ===" \
  | tee -a "$JOURNAL"

if ! bash scripts/machine_libre.sh; then
  echo "REFUS : un travail lourd tourne déjà" | tee -a "$JOURNAL"
  exit 2
fi
bash scripts/veille_hote.sh demarrer 2>&1 | tee -a "$JOURNAL"
scripts/veille_memoire.sh duel_chimere_krigeage.py "$VEILLE" 5 &
veilleur=$!
trap 'kill "$veilleur" 2>/dev/null' EXIT

for p in "${POLLUANTS[@]}"; do
  cible="reports/duel_chimere_${p}_h${H}.csv"
  # Reprise sur le CONTENU attendu, jamais sur l'existence (§ 4) : un CSV écrit par une
  # tentative tuée en cours d'écriture porte le bon nom et pas la dernière ligne.
  if [ -f "$cible" ] && command grep -qF "$MARQUEUR" "$cible"; then
    echo "[$(date +%T)] ↷ $p déjà complet — sauté" | tee -a "$JOURNAL"
    continue
  fi
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    echo "[$(date +%T)] $p J+$((H - 1)) — tentative $essai/$ESSAIS_MAX" | tee -a "$JOURNAL"
    t0=$SECONDS
    echo "── tentative $essai · $(date '+%F %T') ──" >> "logs/duel_chimere_${p}.log"
    PYTHONFAULTHANDLER=1 systemd-run --user --scope --quiet \
      -p MemoryMax="$PLAFOND" -p MemorySwapMax=0 -- \
      env PYTHONFAULTHANDLER=1 python3 -u scripts/duel_chimere_krigeage.py \
        --polluant "$p" --horizon "$H" \
      >> "logs/duel_chimere_${p}.log" 2>&1
    code=$?
    [ "$code" -eq 139 ] && echo "  ⚠️ $p segfault (139) — plateforme, pas le code" | tee -a "$JOURNAL"
    [ "$code" -eq 137 ] && echo "  ⚠️ $p tué par le plafond $PLAFOND" | tee -a "$JOURNAL"
    echo "[$(date +%T)] $p — tentative $essai, code=$code, $(((SECONDS - t0) / 60)) min" \
      | tee -a "$JOURNAL"
    # La sortie de boucle porte sur l'ARTEFACT, jamais sur le code (§ 1 bis) — et ce n'est
    # pas une précaution théorique. Le 11/08 à 18 h 44, PM25 a écrit ses six lignes PUIS
    # segfauté en libérant sa mémoire (`duel_chimere_krigeage.py, line 246 in <module>`,
    # c'est-à-dire la sortie de l'interpréteur). Code 139, fichier complet. Tester le code
    # rejouait un travail déjà fait — une fois ici, jusqu'à sept fois dans le cas défavorable,
    # soit 21 minutes pour réécrire à l'identique un CSV qui était bon.
    if [ -f "$cible" ] && command grep -qF "$MARQUEUR" "$cible"; then
      [ "$code" -ne 0 ] && echo "  ↷ $p : code=$code mais le CSV est COMPLET — le segfault" \
        "est postérieur à l'écriture, on ne rejoue pas" | tee -a "$JOURNAL"
      break
    fi
    # Le journal ne filtre JAMAIS sur les seules lignes de succès (§ 1 bis) : c'est la
    # trace de l'exception qu'on avait besoin de lire.
    tail -5 "logs/duel_chimere_${p}.log" | tee -a "$JOURNAL"
    sleep 20
  done
done

# ── Contrôle de fin sur l'artefact, nommé un par un (§ 4) ──────────────────────────
echo "[$(date +%T)] ── contrôle des artefacts ──" | tee -a "$JOURNAL"
manque=0
for p in "${POLLUANTS[@]}"; do
  cible="reports/duel_chimere_${p}_h${H}.csv"
  if [ -f "$cible" ] && command grep -qF "$MARQUEUR" "$cible"; then
    echo "  ✅ $cible · $(( $(wc -l < "$cible") - 1 )) lignes" | tee -a "$JOURNAL"
  else
    echo "  ❌ AUCUN fichier complet : $cible" | tee -a "$JOURNAL"
    manque=1
  fi
done
bash scripts/veille_hote.sh arreter 2>&1 | tee -a "$JOURNAL"
echo "=== duel CHIMERE terminé $(date '+%F %T') · manque=$manque ===" | tee -a "$JOURNAL"
exit "$manque"
