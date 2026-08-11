#!/usr/bin/env bash
# Rend 0 si les QUATRE CSV MOS J0 sont présents et plausibles, 1 sinon.
#
# Condition d'arrêt de `relance_mos_j1.ps1`. Le test porte sur le CONTENU (§ 4) : ces CSV
# pèsent 400 à 600 Mo et, avant le correctif du 11/08, `fit_mos.py` écrivait directement sous
# le nom définitif — une écriture interrompue laissait donc un fichier tronqué au bon nom.
#
# ⚠️ **La taille, pas le nombre de lignes** — et c'est une correction, pas un raccourci.
# La première version comptait les lignes. Le relanceur appelant ce script toutes les 90 s,
# cela imposait ~1,5 Go de lecture disque par appel, **en concurrence avec l'ajustement
# LightGBM qu'il surveille**. C'est § 1 quinquies : un instrument ne doit pas peser plus que
# ce qu'il mesure, et une veille qui martèle le même système de fichiers que le lot a déjà
# gelé cette machine une fois. `stat` répond en O(1).
#
# ⚠️ Le seuil regarde du bon côté (§ 2 quinquies) : le défaut redouté est une écriture
# TRONQUÉE, donc un fichier plus PETIT que prévu — un plancher d'octets est bien orienté.
set -u
cd "$(dirname "$0")/.." || exit 1

H=${H:-1}
MIN_OCTETS=$((50 * 1024 * 1024))   # le plus léger des CSV complets pèse ~395 Mo
manquants=()

for p in O3 NO2 PM25 PM10; do
  f="reports/mos_${p}_J${H}.csv"
  if [ ! -f "$f" ] || [ "$(stat -c %s "$f")" -lt "$MIN_OCTETS" ]; then
    manquants+=("$p")
  fi
done

if [ ${#manquants[@]} -eq 0 ]; then
  echo "MOS J0 complet · O3 NO2 PM25 PM10"
  exit 0
fi
echo "MOS J0 incomplet · manquent : ${manquants[*]}"
exit 1
