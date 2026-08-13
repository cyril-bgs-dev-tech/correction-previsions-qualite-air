#!/usr/bin/env bash
# Ce que le RÉGLAGE par polluant vaut à NOTRE méthode — le pendant de `optimisation_krigeage`.
#
# La question, et pourquoi les deux moitiés se tiennent
# ------------------------------------------------------
# `duel_chimere_krigeage.py` fige la variante de krigeage adverse pour ne pas « lui donner
# deux chances quand nous n'en prenons qu'une ». `optimisation_krigeage.py` a chiffré ce que
# cette précaution leur coûte : **au plus ~1 %, et négatif sur la moitié des polluants**
# quand la variante est choisie honnêtement.
#
# Il manquait l'autre moitié : combien NOTRE méthode gagnerait au même traitement. Sans
# elle, la phrase « nous n'en prenons qu'une » reste une affirmation non mesurée — et c'est
# exactement le défaut que ce dépôt reproche ailleurs (§ 4 ter : rendre la comparaison
# équitable plutôt que d'écrire qu'elle ne l'est pas).
#
# O3 est déjà mesuré (201 essais, 02/08) : 8,5254 → 8,1027, soit +4,96 %. Ce lot porte les
# trois autres à la MÊME cible de 200 essais — un réglage à 10 essais et un à 200 ne se
# comparent pas.
#
# ⚠️ Ce gain porte sur l'axe SPATIAL — hyperparamètres choisis par validation imbriquée sur
# des groupes de stations, mesurés sur des stations jamais consultées. Le projet a mesuré
# qu'un réglage gagnant en spatial peut PERDRE en temporel (+5 / −3 points). L'axe se cite
# avec le chiffre, sans exception.
#
# Pourquoi un lot, et pourquoi séquentiel
# -----------------------------------------
# La plateforme corrompt la mémoire (REPRISE § ⑤). Optuna reprend nativement sur son `.db` :
# une tentative tuée ne perd que l'essai en cours, jamais l'étude. C'est la reprise la moins
# chère du dépôt — il n'y a rien à écrire pour l'obtenir.
#
# SÉQUENTIEL, jamais en parallèle : un ajustement LightGBM prend déjà tous les cœurs, et
# trois lancés ensemble sur 32 cœurs demandent 96 fils — mesuré sur ce projet, deux ont été
# tués à 90 minutes sans finir. Ce n'est pas un ralentissement de 3×, c'est un effondrement.
#
# Coût mesuré avant lancement (§ 1) : 10 essais NO2 = 6,3 min → 200 essais ≈ 2 h par
# polluant, ≈ 6 h pour les trois.
#
# Usage : bash scripts/lot_optuna_reglage.sh [POLLUANT ...]     (défaut : NO2 PM10 PM25)
set -u
cd "$(dirname "$0")/.." || exit 1

CIBLE=200
ESSAIS_MAX=8
PLAFOND=24G
JOURNAL=logs/lot_optuna_reglage.log
POLLUANTS=("$@")
[ ${#POLLUANTS[@]} -eq 0 ] && POLLUANTS=(NO2 PM10 PM25)
mkdir -p logs

essais_faits() {   # nombre d'essais PUBLIÉS pour un polluant — 0 si le CSV n'existe pas
  local f="reports/optuna_mos_${1}_lgbm.csv"
  [ -f "$f" ] && echo $(( $(wc -l < "$f") - 1 )) || echo 0
}

echo "=== réglage Optuna démarré $(date '+%F %T') · ${POLLUANTS[*]} · cible $CIBLE ===" \
  | tee -a "$JOURNAL"

if ! bash scripts/machine_libre.sh; then
  echo "REFUS : un travail lourd tourne déjà" | tee -a "$JOURNAL"
  exit 2
fi

for p in "${POLLUANTS[@]}"; do
  # Reprise sur le CONTENU attendu (§ 4), et elle est ici gratuite : Optuna a déjà tout
  # gardé dans son `.db`, le CSV n'est qu'un reflet.
  n=$(essais_faits "$p")
  if [ "$n" -ge "$CIBLE" ]; then
    echo "[$(date +%T)] ↷ $p déjà à $n essais — sauté" | tee -a "$JOURNAL"
    continue
  fi
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    echo "[$(date +%T)] $p — tentative $essai/$ESSAIS_MAX (à $n essais sur $CIBLE)" \
      | tee -a "$JOURNAL"
    t0=$SECONDS
    echo "── tentative $essai · $(date '+%F %T') ──" >> "logs/optuna_${p}.log"
    systemd-run --user --scope --quiet \
      -p MemoryMax="$PLAFOND" -p MemorySwapMax=0 -- \
      env PYTHONFAULTHANDLER=1 python3 -u scripts/optuna_mos.py \
        --polluant "$p" --algo lgbm --essais "$CIBLE" \
      >> "logs/optuna_${p}.log" 2>&1
    code=$?
    [ "$code" -eq 139 ] && echo "  ⚠️ $p segfault (139) — plateforme, pas le code" | tee -a "$JOURNAL"
    [ "$code" -eq 137 ] && echo "  ⚠️ $p tué par le plafond $PLAFOND" | tee -a "$JOURNAL"
    apres=$(essais_faits "$p")
    echo "[$(date +%T)] $p — tentative $essai, code=$code, $(((SECONDS - t0) / 60)) min, " \
         "$n → $apres essais" | tee -a "$JOURNAL"
    # La sortie de boucle porte sur l'ARTEFACT, jamais sur le code (§ 1 bis).
    if [ "$apres" -ge "$CIBLE" ]; then
      [ "$code" -ne 0 ] && echo "  ↷ $p : code=$code mais l'étude est COMPLÈTE" | tee -a "$JOURNAL"
      break
    fi
    # Une tentative qui n'a PAS avancé le compteur signale autre chose qu'un segfault
    # (environnement, argument refusé) : le journal doit le montrer, jamais le taire.
    [ "$apres" -le "$n" ] && { echo "  ⚠️ aucun essai gagné sur cette tentative :" \
      | tee -a "$JOURNAL"; tail -5 "logs/optuna_${p}.log" | tee -a "$JOURNAL"; }
    n=$apres
    sleep 20
  done
done

# ── Contrôle de fin sur l'artefact, nommé un par un (§ 4) ──────────────────────────
echo "[$(date +%T)] ── contrôle des artefacts ──" | tee -a "$JOURNAL"
manque=0
for p in "${POLLUANTS[@]}"; do
  n=$(essais_faits "$p")
  if [ "$n" -ge "$CIBLE" ]; then
    echo "  ✅ reports/optuna_mos_${p}_lgbm.csv · $n essais" | tee -a "$JOURNAL"
  else
    echo "  ❌ INCOMPLET : reports/optuna_mos_${p}_lgbm.csv · $n sur $CIBLE" | tee -a "$JOURNAL"
    manque=1
  fi
done
echo "=== réglage Optuna terminé $(date '+%F %T') · manque=$manque ===" | tee -a "$JOURNAL"
exit "$manque"
