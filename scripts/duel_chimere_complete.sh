#!/usr/bin/env bash
# Rend 0 si les QUATRE polluants portent leur duel CHIMERE complet, 1 sinon.
#
# Sert de condition d'arrêt au relanceur hôte `relance_duel_chimere.ps1`. Le test porte sur
# le CONTENU attendu, jamais sur l'existence du fichier (§ 4) : une tentative tuée en pleine
# écriture — et la plateforme en tue une sur deux — laisse un CSV au bon nom, amputé de sa
# fin. C'est le même contrôle que celui du lot ; il est ici pour être appelable depuis
# l'hôte, qui ne peut pas lire l'intérieur du lot.
#
# Le marqueur est la DERNIÈRE des six lignes écrites, et il est ASCII : « CAMS + notre
# correction » le préfixe, donc seul le libellé long correspond, et `grep -F` suffit — pas
# d'expression régulière dont les métacaractères auraient à traverser l'interop (§ 2 bis :
# une seule correspondance, jamais zéro ni deux).
set -u
cd "$(dirname "$0")/.." || exit 1

H=${H:-2}
MARQUEUR="CAMS + notre correction + krigeage"
manquants=()

for p in O3 NO2 PM10 PM25; do
  f="reports/duel_chimere_${p}_h${H}.csv"
  command grep -qF "$MARQUEUR" "$f" 2>/dev/null || manquants+=("$p")
done

if [ ${#manquants[@]} -eq 0 ]; then
  echo "duel CHIMERE complet · O3 NO2 PM10 PM25"
  exit 0
fi
echo "duel CHIMERE incomplet · manquent : ${manquants[*]}"
exit 1
