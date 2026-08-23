#!/usr/bin/env bash
# Un lot de mesure d'apport, sur les quatre polluants — générique.
#
#   bash scripts/lot_apports.sh apport_ratios_echelle [axe] [horizon]
#
# Le nom du script Python EST le préfixe de ses artefacts : un seul argument, donc, et
# aucune façon de les faire diverger.
#
# § 0-F : chemins résolus depuis la racine du dépôt, jamais depuis $PWD.
# § 0-C : le verdict porte sur l'ARTEFACT — un script qui rend 0 sans écrire n'a rien fait.
# § 0-B : deux bornes SÉPARÉES — un budget d'essais par polluant, une échéance horaire —
#         et le message de fin nomme celle qui a cédé.
set -u
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
NOM="${1:?usage : lot_apports.sh <nom_du_script_sans_.py> [axe] [horizon]}"
AXE="${2:-double}"
HORIZON="${3:-2}"
ESSAIS_MAX=3
ECHEANCE=$(( $(date +%s) + 4 * 3600 ))
SCRIPT="$RACINE/scripts/${NOM}.py"
JOURNAL="$RACINE/logs/${NOM}_${AXE}.log"
mkdir -p "$RACINE/logs"
[ -f "$SCRIPT" ] || { echo "script introuvable : $SCRIPT"; exit 2; }

echo "=== $NOM · axe $AXE · horizon $HORIZON · $(date -Is) ===" | tee -a "$JOURNAL"
for P in NO2 O3 PM10 PM25; do
  CIBLE="$RACINE/reports/${NOM}_${P}_h${HORIZON}_${AXE}.csv"
  if [ -f "$CIBLE" ] && [ "$CIBLE" -nt "$SCRIPT" ]; then
    echo "  $P : artefact plus récent que le script — sauté" | tee -a "$JOURNAL"
    continue
  fi
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    if [ "$(date +%s)" -ge "$ECHEANCE" ]; then
      echo "  ⛔ ARRÊT : échéance horaire atteinte — c'est LA DURÉE qui a cédé" \
        | tee -a "$JOURNAL"
      break 2
    fi
    echo "  → $P essai $essai/$ESSAIS_MAX · $(date +%H:%M:%S)" | tee -a "$JOURNAL"
    PYTHONFAULTHANDLER=1 python3 -u "$SCRIPT" --polluant "$P" --horizon "$HORIZON" \
      --axe "$AXE" >> "$JOURNAL" 2>&1
    if [ -f "$CIBLE" ] && [ "$CIBLE" -nt "$SCRIPT" ]; then
      echo "  ✅ $P écrit" | tee -a "$JOURNAL"
      break
    fi
    echo "  ⚠️ $P : aucun artefact réécrit à l'essai $essai" | tee -a "$JOURNAL"
    [ "$essai" -eq "$ESSAIS_MAX" ] && \
      echo "  ⛔ $P ABANDONNÉ — c'est le BUDGET D'ESSAIS qui a cédé" | tee -a "$JOURNAL"
  done
done
echo "=== fin · $(date -Is) ===" | tee -a "$JOURNAL"
for P in NO2 O3 PM10 PM25; do
  C="$RACINE/reports/${NOM}_${P}_h${HORIZON}_${AXE}.csv"
  [ -f "$C" ] && echo "  ✔ $(basename "$C")" || echo "  ✘ MANQUANT : $(basename "$C")"
done | tee -a "$JOURNAL"
