#!/usr/bin/env bash
# Banc de préprocessing — reprise nommée des familles manquantes, avec réessai.
#
# Pourquoi une reprise, et pas un relancement complet
# ------------------------------------------------------
# Le lot du 08/08 16 h 27 a perdu 6 exécutions sur 17. Diagnostic mené avant de relancer :
#
#   * le journal noyau nomme le fautif — `segfault ... in lib_lightgbm.so`, error 6 ;
#     c'est le défaut que l'en-tête de `banc_preprocessing.py` documente déjà comme
#     natif, non déterministe, et non reproductible sur données synthétiques ;
#   * DEUX hypothèses ont été réfutées avant celle-là, et il faut le dire : les colonnes
#     fabriquées ne portent aucune valeur extrême (`cams_ratio_clim` plafonne à 16,6,
#     zéro infini), et les 21 parquets CAMS de PM10 sont sains (dtype et bornes vérifiés
#     un par un) ;
#   * le rejeu à l'identique de `NO2 tendance_cams`, qui venait de mourir, a **réussi**.
#     La panne est donc transitoire : un réessai la traite, une réécriture du code non.
#
# Ce que ce lot NE fait PAS, délibérément
# ------------------------------------------
# Il ne pose pas `PYTHONNOUSERSITE=1`, alors que le diagnostic a trouvé un vrai défaut
# latent : `~/.local/lib/python3.12/site-packages` précède l'environnement conda dans
# `sys.path` et y masque scipy, joblib et threadpoolctl. C'est à corriger — mais **pas
# pendant une mesure** : l'ozone a été mesuré dans l'environnement actuel, et changer
# l'environnement entre polluants rendrait les quatre non comparables. Corriger d'abord,
# tout remesurer ensuite, ou ne rien changer : c'est le même principe que § 2 quater.
#
# La liste est NOMMÉE, une entrée par exécution manquante — jamais un compte (règle 4).
set -u

cd /mnt/d/Projet_Air_Quality || exit 1
JOURNAL=logs/lot_banc_reprise.log
ESSAIS_MAX=3
mkdir -p logs

# Ce qui manque au 08/08 17 h, relevé sur les CSV et non de mémoire.
MANQUANTS=(
  "NO2:anomalie_cams"
  "PM10:base" "PM10:harmoniques" "PM10:splines"
  "PM10:anomalie_cams" "PM10:tendance_cams" "PM10:interactions"
  "PM25:anomalie_cams" "PM25:tendance_cams" "PM25:interactions"
)

echo "=== reprise banc démarrée $(date '+%F %T') · ${#MANQUANTS[@]} exécutions ===" | tee -a "$JOURNAL"

for ENTREE in "${MANQUANTS[@]}"; do
  P="${ENTREE%%:*}"; F="${ENTREE##*:}"
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    echo "[$(date '+%T')] $P/$F — tentative $essai/$ESSAIS_MAX" | tee -a "$JOURNAL"
    t0=$SECONDS
    python3 scripts/banc_preprocessing.py --polluant "$P" --famille "$F" >> "$JOURNAL" 2>&1
    code=$?
    echo "[$(date '+%T')] $P/$F — tentative $essai, code=$code, $((SECONDS - t0))s" | tee -a "$JOURNAL"
    [ "$code" -eq 0 ] && break
    sleep 5
  done
done

for P in NO2 PM10 PM25; do
  echo "[$(date '+%T')] $P — rapport" | tee -a "$JOURNAL"
  python3 scripts/banc_preprocessing.py --polluant "$P" --rapport >> "$JOURNAL" 2>&1
  echo "[$(date '+%T')] $P — rapport code=$?" | tee -a "$JOURNAL"
done

# ── Contrôle de fin sur l'artefact attendu, famille par famille (règle 4) ────────────
echo "=== contrôle de fin $(date '+%F %T') ===" | tee -a "$JOURNAL"
manque=0
for P in NO2 PM10 PM25; do
  CIBLE="reports/banc_preprocessing_${P}_h2.csv"
  if [ ! -f "$CIBLE" ]; then
    echo "  ✗ $CIBLE ABSENT" | tee -a "$JOURNAL"; manque=1; continue
  fi
  trou=0
  for F in base harmoniques splines anomalie_cams tendance_cams interactions; do
    # colonnes du rapport : polluant,horizon,jeu,famille,... → $4 est la famille
    n=$(awk -F, -v f="$F" 'NR>1 && $4==f {c++} END {print c+0}' "$CIBLE")
    [ "$n" -eq 2 ] || { echo "  ✗ $P/$F : $n ligne(s) au lieu de 2" | tee -a "$JOURNAL"; trou=1; }
  done
  if [ "$trou" -eq 0 ]; then
    echo "  ✓ $CIBLE — 6 familles × 2 jeux" | tee -a "$JOURNAL"
  else
    manque=1
  fi
done
echo "=== reprise banc terminée $(date '+%F %T') · manque=$manque ===" | tee -a "$JOURNAL"
exit "$manque"
