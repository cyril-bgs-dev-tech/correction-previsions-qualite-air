#!/usr/bin/env bash
# Ablation : ce que chaque famille apporte POUR CHAQUE POLLUANT, hors effet d'ordre.
#
# Pourquoi ce lot, alors que `methode_maximale` mesure déjà des apports
# ------------------------------------------------------------------------
# Les configurations cumulatives répondent à « que gagne-t-on en empilant dans CET
# ordre ». Elles ne répondent pas à « faut-il garder cette famille pour CE polluant » :
# un étage placé tôt s'attribue ce qu'un étage plus tardif aurait apporté seul. Les
# chiffres du 08/08 le montrent sans le trancher — la typologie vaut +8,97 pt sur le NO₂
# et **−0,13 sur l'ozone**, `tendance` +2,08 sur l'ozone et +0,13 à +0,45 ailleurs.
# L'ablation retire une famille de la pile complète, toutes les autres en place : c'est
# la seule lecture qui ne dépende pas de l'ordre.
#
# ⚠️ C'est une MESURE, pas une sélection. Élaguer les familles dont l'ablation ne coûte
# rien puis publier le score de la pile élaguée sur ces mêmes plis serait le biais de
# criblage mesuré à ×2 à ×4 sur ce dépôt. Le score d'une pile choisie ici se re-mesure
# ailleurs, ou se publie en déclarant qu'il est dans l'échantillon.
#
# Le lot recalcule les 13 configurations, pas seulement les 5 nouvelles — et c'est
# voulu : les 8 anciennes servent de **contrôle de reproduction**. Le corpus a bougé
# depuis le 08/08 (couverture des membres passée de ~40 % à ~94 %), donc si `base` ne
# rend plus 7,009 % sur l'ozone, ce n'est pas l'ablation qui a changé quelque chose,
# c'est l'entrée — et il faut le savoir AVANT de publier quoi que ce soit.
set -u
cd "$(dirname "$0")/.." || exit 1

H=2
ESSAIS_MAX=20        # taux d'échec mesuré ~17 % par tentative — voir lot_maximale_tendance.sh
PLAFOND=24G          # pic réel mesuré à 18,9 Go sur NO₂ ; ce n'est PAS «10× le besoin»
JOURNAL=logs/lot_ablation.log
VEILLE="$HOME/veille_memoire_ablation.csv"   # hors /mnt/d : doit survivre à la coupure
MARQUEUR="− fourier (ablation)"              # la DERNIÈRE ablation écrite : sa présence
                                             # atteste que le fichier est complet
mkdir -p logs

echo "=== lot ablation démarré $(date '+%F %T') · plafond $PLAFOND ===" | tee -a "$JOURNAL"

# Garde-fous armés par le lot, pas par la mémoire de l'opérateur (§ 1 quater).
if ! bash scripts/machine_libre.sh; then
  echo "REFUS : un travail lourd tourne déjà" | tee -a "$JOURNAL"
  exit 2
fi
bash scripts/veille_hote.sh demarrer 2>&1 | tee -a "$JOURNAL"
scripts/veille_memoire.sh methode_maximale.py "$VEILLE" 2 &
veilleur=$!
trap 'kill "$veilleur" 2>/dev/null' EXIT

for p in O3 NO2 PM10 PM25; do
  cible="reports/methode_maximale_${p}_h${H}.csv"
  # Reprise sur le CONTENU attendu, jamais sur l'existence (§ 4) : le CSV du 08/08 porte
  # le bon nom, la bonne taille, et aucune ligne d'ablation.
  if [ -f "$cible" ] && command grep -qF "$MARQUEUR" "$cible"; then
    echo "[$(date +%T)] ↷ $p déjà complet avec les ablations — sauté" | tee -a "$JOURNAL"
    continue
  fi
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    echo "[$(date +%T)] $p J+$H — tentative $essai/$ESSAIS_MAX" | tee -a "$JOURNAL"
    t0=$SECONDS
    echo "── tentative $essai · $(date '+%F %T') ──" >> "logs/ablation_${p}.log"
    PYTHONFAULTHANDLER=1 systemd-run --user --scope --quiet \
      -p MemoryMax="$PLAFOND" -p MemorySwapMax=0 -- \
      env PYTHONFAULTHANDLER=1 python3 -u scripts/methode_maximale.py \
        --polluant "$p" --horizon "$H" --ablation \
      >> "logs/ablation_${p}.log" 2>&1
    code=$?
    [ "$code" -eq 139 ] && echo "  ⚠️ $p segfault (139) — reprise sur .partiel" | tee -a "$JOURNAL"
    [ "$code" -eq 137 ] && echo "  ⚠️ $p tué par le plafond $PLAFOND — débordement mémoire" \
      | tee -a "$JOURNAL"
    echo "[$(date +%T)] $p — tentative $essai, code=$code, $(((SECONDS - t0) / 60)) min" \
      | tee -a "$JOURNAL"
    [ "$code" -eq 0 ] && break
    tail -3 "logs/ablation_${p}.log" | tee -a "$JOURNAL"
    sleep 30
  done
  sleep 30
done

# ── Contrôle de fin sur l'artefact, nommé un par un (§ 4) ───────────────────────────
echo "[$(date +%T)] ── contrôle des artefacts ──" | tee -a "$JOURNAL"
manque=0
for p in O3 NO2 PM10 PM25; do
  cible="reports/methode_maximale_${p}_h${H}.csv"
  if [ -f "$cible" ] && command grep -qF "$MARQUEUR" "$cible"; then
    n=$(command grep -c "(ablation)" "$cible")
    echo "  ✅ $p — $n ablations" | tee -a "$JOURNAL"
  else
    echo "  ❌ $p — AUCUNE ablation écrite" | tee -a "$JOURNAL"
    manque=1
  fi
done
[ $manque -eq 0 ] && echo "LOT COMPLET" | tee -a "$JOURNAL" || echo "LOT INCOMPLET" | tee -a "$JOURNAL"
exit $manque
