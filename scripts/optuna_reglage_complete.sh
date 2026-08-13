#!/usr/bin/env bash
# Rend 0 si les TROIS polluants manquants portent une étude Optuna complète, 1 sinon.
#
# Sert de condition d'arrêt au relanceur hôte `relance_optuna_reglage.ps1`, qui ne peut pas
# lire l'intérieur du lot. Le test porte sur le CONTENU attendu, jamais sur l'existence du
# fichier (§ 4) : `optuna_mos.py` réécrit son CSV à CHAQUE fin d'exécution, avec autant de
# lignes que l'étude compte d'essais. Un fichier de 10 lignes est donc un fichier normal
# d'une étude inachevée — pas un fichier corrompu, et c'est justement ce qu'il faut
# distinguer.
#
# ⚠️ Le compte se fait sur les LIGNES du CSV, pas sur le `.db` : la base porte aussi les
# essais élagués et en cours, et le lot doit s'arrêter sur ce qui est PUBLIÉ.
#
# O3 n'est pas dans la liste : son étude est complète depuis le 02/08 (201 essais).
set -u
cd "$(dirname "$0")/.." || exit 1

CIBLE=${CIBLE:-200}
manquants=()

for p in NO2 PM10 PM25; do
  f="reports/optuna_mos_${p}_lgbm.csv"
  n=0
  [ -f "$f" ] && n=$(( $(wc -l < "$f") - 1 ))
  [ "$n" -ge "$CIBLE" ] || manquants+=("$p($n)")
done

if [ ${#manquants[@]} -eq 0 ]; then
  echo "réglage Optuna complet · NO2 PM10 PM25 à $CIBLE essais"
  exit 0
fi
echo "réglage Optuna incomplet · manquent : ${manquants[*]} sur $CIBLE"
exit 1
