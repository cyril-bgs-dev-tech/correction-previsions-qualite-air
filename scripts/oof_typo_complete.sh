#!/usr/bin/env bash
# Rend 0 si les QUATRE parquets OOF « typologie » de la campagne sont produits, 1 sinon.
#
# Condition d'arrêt de `relance_oof_typo.ps1`.
#
# ⚠️ Ici l'existence NE SUFFIT PAS, et pas pour la raison habituelle : `oof_double_aveugle.py`
# écrit sous `.partiel` puis renomme, donc un nom définitif est bien un fichier complet (§ 4).
# Le piège est autre — des `oof_<P>_h2_typo.parquet` du 03/08 existent DÉJÀ pour NO2 et PM10.
# Tester l'existence déclarerait la campagne finie avant qu'elle commence, et le rapport
# mélangerait deux dates comme il mélangeait deux variantes. C'est le « critère de fraîcheur »
# de `regenerer-peut-degrader`.
#
# Le repère de campagne est créé UNE FOIS par le lot et survit aux redémarrages de VM : sans
# cela, chaque relance remettrait la référence à l'heure et redemanderait tout le travail.
set -u
cd "$(dirname "$0")/.." || exit 1

H=${H:-2}
REPERE=logs/.oof_typo_campagne
manquants=()

[ -f "$REPERE" ] || { echo "campagne non démarrée (aucun repère)"; exit 1; }

for p in O3 NO2 PM10 PM25; do
  f="data/interim/oof/oof_${p}_h${H}_typo.parquet"
  [ -f "$f" ] && [ "$f" -nt "$REPERE" ] || manquants+=("$p")
done

if [ ${#manquants[@]} -eq 0 ]; then
  echo "OOF typo complet · O3 NO2 PM10 PM25"
  exit 0
fi
echo "OOF typo incomplet · manquent : ${manquants[*]}"
exit 1
