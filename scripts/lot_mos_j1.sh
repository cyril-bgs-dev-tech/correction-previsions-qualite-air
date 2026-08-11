#!/usr/bin/env bash
# Régénération de la chaîne MOS officiel, à l'horizon 1 — c'est J0, l'échéance du produit
# officiel, et le défaut du script. (`TRANCHES[1] = (1, 24)` : les 24 premières heures de la
# sortie 00 UTC, donc le JOUR MÊME. Ne jamais l'appeler « J+1 » — § 4 ter.)
#
# Ce que la réécriture du 11/08 corrige
# -------------------------------------
# ① **Les ajustements ne sont plus lancés en parallèle.** La version précédente faisait
#    `fit_mos O3 & fit_mos NO2 & wait`. CLAUDE.md § 1 l'interdit noir sur blanc, mesuré sur
#    cette machine : trois ajustements LightGBM `n_jobs=-1` simultanés demandent 96 fils sur
#    32 cœurs, et **deux ont été tués à 90 minutes sans finir**. Ce n'est pas un ralentissement
#    de 3×, c'est un effondrement — la contention porte sur la bande passante mémoire. La
#    trace le montrait déjà : le 05/08, O₃ a fini en 33 min et son jumeau NO₂ en 101.
# ② **Plafond mémoire et journal par polluant** (§ 1 quater) : un débordement meurt seul en
#    code 137 au lieu d'emporter la VM, et la panne devient observable.
# ③ **Reprise et contrôle de fin sur l'artefact** (§ 4), au lieu d'un lot muet.
# ④ **PM10 entre dans le lot.** Il manquait ici et dans le `choices` d'argparse — nulle part
#    ailleurs. La démo Streamlit ne montrait donc que trois des quatre polluants du dossier.
#
# Les CSV du 05/08 restent VALIDES et ne sont pas refaits : le seul commit qui a touché
# `fit_mos.py` depuis (`10d5e0d`) est un changement de chemin de code **prouvé équivalent**
# — 200 tirages sur `presence`/`valeur_associee`, comparaison exhaustive des ensembles de
# mois. La reprise porte donc sur l'existence, et seul PM10 s'ajuste.
#
# Usage : bash scripts/lot_mos_j1.sh [POLLUANT ...]      (défaut : les quatre)
set -u
cd "$(dirname "$0")/.." || exit 1

H=1
ESSAIS_MAX=6
PLAFOND=32G            # les tables horaires sont plus grosses que celles du duel journalier
JOURNAL=logs/lot_mos_j1.log
VEILLE="$HOME/veille_memoire_mos_j1.csv"
MIN_OCTETS=$((50 * 1024 * 1024))   # le plus léger des CSV complets pèse ~395 Mo
POLLUANTS=("$@")
[ ${#POLLUANTS[@]} -eq 0 ] && POLLUANTS=(O3 NO2 PM25 PM10)
mkdir -p logs

complet() {   # $1 = polluant → 0 si le CSV est présent ET plausible
  local f="reports/mos_${1}_J${H}.csv"
  [ -f "$f" ] || return 1
  # Contrôle sur le CONTENU, pas sur l'existence (§ 4) : `fit_mos.py` écrit désormais sous
  # `.partiel` puis renomme, mais les fichiers antérieurs à ce correctif peuvent être
  # tronqués. La TAILLE plutôt que le nombre de lignes — ce test est rejoué à chaque
  # tentative et par le relanceur toutes les 90 s ; compter les lignes ferait lire 1,5 Go à
  # chaque appel, en concurrence avec l'ajustement lui-même (§ 1 quinquies).
  [ "$(stat -c %s "$f")" -ge "$MIN_OCTETS" ]
}

echo "=== MOS J0 démarré $(date '+%F %T') · ${POLLUANTS[*]} · plafond $PLAFOND ===" \
  | tee -a "$JOURNAL"

if ! bash scripts/machine_libre.sh; then
  echo "REFUS : un travail lourd tourne déjà" | tee -a "$JOURNAL"
  exit 2
fi
bash scripts/veille_hote.sh demarrer 2>&1 | tee -a "$JOURNAL"
scripts/veille_memoire.sh fit_mos.py "$VEILLE" 5 &
veilleur=$!
trap 'kill "$veilleur" 2>/dev/null' EXIT

for p in "${POLLUANTS[@]}"; do
  if complet "$p"; then
    echo "[$(date +%T)] ↷ $p déjà complet — sauté" | tee -a "$JOURNAL"
    continue
  fi
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    echo "[$(date +%T)] $p J0 — tentative $essai/$ESSAIS_MAX" | tee -a "$JOURNAL"
    t0=$SECONDS
    PYTHONFAULTHANDLER=1 systemd-run --user --scope --quiet \
      -p MemoryMax="$PLAFOND" -p MemorySwapMax=0 -- \
      env PYTHONFAULTHANDLER=1 python3 -u scripts/fit_mos.py \
        --polluant "$p" --horizon "$H" \
      > "logs/fit_mos_${p}_J${H}.log" 2>&1
    code=$?
    [ "$code" -eq 139 ] && echo "  ⚠️ $p segfault (139) — plateforme, pas le code" | tee -a "$JOURNAL"
    [ "$code" -eq 137 ] && echo "  ⚠️ $p tué par le plafond $PLAFOND" | tee -a "$JOURNAL"
    echo "[$(date +%T)] $p — tentative $essai, code=$code, $(((SECONDS - t0) / 60)) min" \
      | tee -a "$JOURNAL"
    # Sortie de boucle sur l'ARTEFACT, jamais sur le code : un segfault postérieur à
    # l'écriture rejouerait une heure de travail déjà faite.
    if complet "$p"; then
      [ "$code" -ne 0 ] && echo "  ↷ $p : code=$code mais le CSV est COMPLET — on ne rejoue pas" \
        | tee -a "$JOURNAL"
      break
    fi
    # Le journal ne filtre JAMAIS sur les seules lignes de succès (§ 1 bis).
    tail -5 "logs/fit_mos_${p}_J${H}.log" | tee -a "$JOURNAL"
    sleep 20
  done
done

echo "[$(date +%T)] ── contrôle des artefacts ──" | tee -a "$JOURNAL"
manque=0
for p in "${POLLUANTS[@]}"; do
  if complet "$p"; then
    echo "  ✅ reports/mos_${p}_J${H}.csv · $(du -h "reports/mos_${p}_J${H}.csv" | cut -f1)" \
      | tee -a "$JOURNAL"
  else
    echo "  ❌ ABSENT ou TRONQUÉ : reports/mos_${p}_J${H}.csv" | tee -a "$JOURNAL"
    manque=1
  fi
done
bash scripts/veille_hote.sh arreter 2>&1 | tee -a "$JOURNAL"
echo "=== MOS J0 terminé $(date '+%F %T') · manque=$manque ===" | tee -a "$JOURNAL"
exit "$manque"
