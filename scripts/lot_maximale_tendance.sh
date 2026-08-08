#!/usr/bin/env bash
# Empilement maximal, les quatre polluants — avec l'étage `tendance` ajouté le 08/08.
#
# Pourquoi ce lot remplace `lot_maximale.sh` plutôt que de le rejouer
# ---------------------------------------------------------------------
# `lot_maximale.sh` lance **deux polluants à la fois**, ce qui était sain le 05/08 avec
# `n_jobs=8` borné. Le 08/08, LightGBM a segfaulté 28 fois sur ~41 exécutions du banc, et
# le seul motif qui séparait succès et échecs était l'**isolement** : toutes les
# exécutions isolées ont fini, la plupart des exécutions enchaînées sont mortes. Ce lot
# est donc **strictement en série**, avec 30 s entre deux, et réessaie.
#
# ⚠️ La granularité a changé par rapport au calibrage du 05/08 (un étage de plus, deux
# polluants en moins en parallèle) : l'étalonnage précédent ne vaut plus, et la durée
# annoncée ici est une extrapolation, pas une mesure (règle 1 bis).
set -u
cd /mnt/d/Projet_Air_Quality || exit 1
mkdir -p logs

if pgrep -f "[m]ethode_maximale.py" > /dev/null; then
  echo "✗ un lot methode_maximale tourne déjà — arrêt"; exit 1
fi

PY=/home/cyril/miniforge3/envs/llm-agent/bin/python3   # jamais `python3` nu
H=2
ESSAIS_MAX=3
JOURNAL=logs/lot_maximale_tendance.log

echo "=== lot maximale+tendance démarré $(date '+%F %T') ===" | tee -a "$JOURNAL"

for p in O3 PM10 PM25 NO2; do
  for (( essai = 1; essai <= ESSAIS_MAX; essai++ )); do
    echo "[$(date +%T)] $p J+$H — tentative $essai/$ESSAIS_MAX" | tee -a "$JOURNAL"
    t0=$SECONDS
    "$PY" scripts/methode_maximale.py --polluant "$p" --horizon "$H" \
      > "logs/maximale_${p}.log" 2>&1
    code=$?
    echo "[$(date +%T)] $p — tentative $essai, code=$code, $(((SECONDS - t0) / 60)) min" \
      | tee -a "$JOURNAL"
    [ "$code" -eq 0 ] && break
    tail -3 "logs/maximale_${p}.log" | tee -a "$JOURNAL"
    sleep 30
  done
  sleep 30
done

# ── Contrôle de fin sur l'artefact attendu, nommé un par un (règle 4) ────────────────
# On exige aussi que la ligne « + tendance » soit PRÉSENTE : un fichier écrit par une
# version antérieure du script aurait le bon nom, la bonne taille, et pas l'étage.
echo "[$(date +%T)] ── contrôle des artefacts ──" | tee -a "$JOURNAL"
manque=0
for p in O3 PM10 PM25 NO2; do
  cible="reports/methode_maximale_${p}_h${H}.csv"
  if [ ! -f "$cible" ]; then
    echo "  ✗ AUCUN fichier écrit pour $p — voir logs/maximale_${p}.log" | tee -a "$JOURNAL"
    ls -la "${cible}.partiel" 2>/dev/null && echo "    (un .partiel existe : interrompu, pas planté)"
    manque=1; continue
  fi
  if grep -q "+ tendance" "$cible"; then
    echo "  ✓ $cible ($(($(wc -l < "$cible") - 1)) configurations, étage tendance présent)" \
      | tee -a "$JOURNAL"
  else
    echo "  ✗ $cible existe mais SANS l'étage « + tendance »" | tee -a "$JOURNAL"; manque=1
  fi
done
echo "=== lot terminé $(date '+%F %T') · manque=$manque ===" | tee -a "$JOURNAL"
exit "$manque"
