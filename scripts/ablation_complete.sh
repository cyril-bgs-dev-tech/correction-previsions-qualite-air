#!/usr/bin/env bash
# Rend 0 si les QUATRE polluants portent leurs lignes d'ablation, 1 sinon.
#
# Sert de condition d'arrêt au relanceur hôte `relance_ablation.ps1`. Le test porte sur le
# CONTENU attendu, jamais sur l'existence du fichier (§ 4) : les CSV du 08/08 portent le bon
# nom, la bonne taille, et aucune ligne d'ablation.
#
# Le marqueur cherché est volontairement ASCII — la ligne réelle commence par U+2212 (« − »),
# qui ne traverse pas proprement l'interop PowerShell/WSL. `tendance (ablation)` ne se lit
# nulle part ailleurs dans ces CSV, donc il désigne bien une ligne et une seule (§ 2 bis).
set -u
cd "$(dirname "$0")/.." || exit 1

H=${H:-2}
MARQUEUR="tendance (ablation)"
manquants=()

for p in O3 NO2 PM10 PM25; do
  f="reports/methode_maximale_${p}_h${H}.csv"
  grep -qF "$MARQUEUR" "$f" 2>/dev/null || manquants+=("$p")
done

if [ ${#manquants[@]} -eq 0 ]; then
  echo "ablation complète · O3 NO2 PM10 PM25"
  exit 0
fi
echo "ablation incomplète · manquent : ${manquants[*]}"
exit 1
