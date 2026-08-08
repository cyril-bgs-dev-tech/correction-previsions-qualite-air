#!/usr/bin/env bash
# Banc de préprocessing — les trois polluants restants, une famille par processus.
#
# Pourquoi en série, et pourquoi un processus par famille
# ---------------------------------------------------------
# LightGBM prend déjà 8 fils (`double_aveugle_journalier.ajuster`) : lancer deux
# ajustements ensemble a été mesuré à ×12,9 sur ce projet, la contention portant sur la
# bande passante mémoire et non sur les cœurs. Et une famille par processus est la parade
# à l'erreur de segmentation native décrite dans l'en-tête de `banc_preprocessing.py`.
#
# Calibrage (règle 1) : passe unitaire du 08/08 sur `NO2 base` — 185 s, corpus compris,
# 37 plis sur 37 prévus, gain +28,67 % écran / +29,53 % confirmation, cohérent avec le
# +27,79 % déjà publié. 17 exécutions restantes × ~190 s ≈ 55 min.
#
# `NO2 base` n'est pas relancé : il est déjà dans `banc_preprocessing_NO2_h2_plis.csv`.
# Le script réécrit les lignes d'une famille à chaque passage, donc rejouer serait exact
# mais coûterait 3 min pour un résultat identique (même graine, mêmes plis).
#
# Le journal n'est PAS filtré sur les lignes de succès (règle 1 bis) : une trace
# d'exception ne correspond à aucun motif attendu et serait précisément ce qu'on jette.
set -u   # pas de -e : une famille qui meurt ne doit pas emporter le lot

cd /mnt/d/Projet_Air_Quality || exit 1
PY=python3
JOURNAL=logs/lot_banc.log
mkdir -p logs

FAMILLES=(base harmoniques splines anomalie_cams tendance_cams interactions)

echo "=== lot banc démarré $(date '+%F %T') ===" | tee -a "$JOURNAL"

for P in NO2 PM10 PM25; do
  for F in "${FAMILLES[@]}"; do
    if [ "$P" = "NO2" ] && [ "$F" = "base" ]; then
      echo "[$(date '+%T')] $P/$F — déjà mesuré, sauté" | tee -a "$JOURNAL"
      continue
    fi
    echo "[$(date '+%T')] $P/$F — début" | tee -a "$JOURNAL"
    t0=$SECONDS
    $PY scripts/banc_preprocessing.py --polluant "$P" --famille "$F" >> "$JOURNAL" 2>&1
    code=$?
    echo "[$(date '+%T')] $P/$F — fin, code=$code, $((SECONDS - t0))s" | tee -a "$JOURNAL"
  done
  echo "[$(date '+%T')] $P — rapport" | tee -a "$JOURNAL"
  $PY scripts/banc_preprocessing.py --polluant "$P" --rapport >> "$JOURNAL" 2>&1
  echo "[$(date '+%T')] $P — rapport code=$?" | tee -a "$JOURNAL"
done

# ── Contrôle de fin sur l'ARTEFACT ATTENDU, nommé un par un (règle 4) ────────────────
# Jamais sur le code de sortie, jamais sur un compte global : le tableau doit exister ET
# porter les six familles sur les deux jeux, soit douze lignes.
echo "=== contrôle de fin $(date '+%F %T') ===" | tee -a "$JOURNAL"
manque=0
for P in NO2 PM10 PM25; do
  CIBLE="reports/banc_preprocessing_${P}_h2.csv"
  if [ ! -f "$CIBLE" ]; then
    echo "  ✗ $CIBLE ABSENT" | tee -a "$JOURNAL"; manque=1; continue
  fi
  trou=0
  for F in "${FAMILLES[@]}"; do
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
echo "=== lot banc terminé $(date '+%F %T') · manque=$manque ===" | tee -a "$JOURNAL"
exit "$manque"
