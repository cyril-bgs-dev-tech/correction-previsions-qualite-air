#!/usr/bin/env bash
# Recalcule les rapports invalidés par la correction du chargement (29/07/2026).
#
# Le chargement déduisait la fenêtre d'observations du **nom** des fichiers de prévision ;
# sur les six fichiers bi-mensuels, seul le second mois était retenu — 11 mois sur 17,
# soit 35 % du jeu perdu. Tout rapport calculé avant la correction porte sur l'échantillon
# amputé, et aucun n'est comparable aux nouveaux.
#
# **Séquentiel, jamais parallèle.** LightGBM tourne en `n_jobs=-1` : trois ajustements
# simultanés sur 32 cœurs demandent 96 fils, et deux runs de 90 minutes ont été tués
# sans finir. La contention porte sur la bande passante mémoire, pas sur les cœurs.
#
# Usage : bash scripts/recalculer_apres_correction.sh
# Journal : reports/log_recalcul.txt

set -u
cd "$(dirname "$0")/.." || exit 1

JOURNAL="reports/log_recalcul.txt"
: > "$JOURNAL"
DEPART=$(date +%s)

# Ordre : la barre à battre d'abord — tout le reste s'y compare.
TACHES=(
  "benchmark_cams.py --scope metropole --horizons 1,2,3"
  "apport_trafic_population.py --polluant NO2 --horizon 1"
  "ablation_mos.py --polluant O3 --horizon 1"
  "covariables_contre_interpolation.py --polluant O3 --horizon 1"
  "preserver_la_queue.py --polluant O3 --horizon 1"
  "valider_mos_aveugle.py --polluant O3 --horizon 1"
  "comparer_sur_meme_echantillon.py --polluant O3 --horizon 1"
  "erreur_par_regime_meteo.py --polluant O3 --horizon 1"
)

N=${#TACHES[@]}
for i in "${!TACHES[@]}"; do
  TACHE="${TACHES[$i]}"
  NOM="${TACHE%% *}"
  T0=$(date +%s)
  printf '[%d/%d] %-42s ' "$((i + 1))" "$N" "$NOM" | tee -a "$JOURNAL"

  # `$TACHE` porte le script **et** ses options : il doit être découpé en mots. Le citer
  # ferait chercher un fichier nommé « benchmark_cams.py --scope metropole ».
  # shellcheck disable=SC2086
  if timeout 7200 python3 scripts/$TACHE > "reports/log_${NOM%.py}.txt" 2>&1; then
    ETAT="ok"
  else
    ETAT="ECHEC($?)"
  fi

  DUREE=$(( $(date +%s) - T0 ))
  ECOULE=$(( $(date +%s) - DEPART ))
  RESTE=$(( ECOULE / (i + 1) * (N - i - 1) ))
  printf '%-10s %4ds · écoulé %4ds · reste ~%4ds\n' \
    "$ETAT" "$DUREE" "$ECOULE" "$RESTE" | tee -a "$JOURNAL"
done

printf '\nTerminé en %ds\n' "$(( $(date +%s) - DEPART ))" | tee -a "$JOURNAL"
