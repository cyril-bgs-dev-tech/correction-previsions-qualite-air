#!/usr/bin/env bash
# Compléter l'IFS dans la fenêtre d'évaluation, PUIS cribler — jamais l'inverse.
#
# Pourquoi cet ordre n'est pas négociable
# ----------------------------------------
# Au 24/08 à 09 h, l'IFS couvre 17 mois sur les 29 de la fenêtre d'évaluation, avec SIX
# TROUS AU MILIEU : 2025-03, 04, 05, 07, 08 et 09. Cribler dessus produirait exactement
# le défaut que la nuit a passé à éliminer — sous validation mois-caché, « IFS absent »
# vaut « nous sommes dans ces mois-là ».
#
# La référence propre, elle, EST prête : les quatre piles auditables ont été régénérées
# entre 03 h 44 et 04 h 17 et portent leur empreinte d'entrées. Ce n'est donc pas la
# référence qui manque, c'est le matériel.
#
# Le script attend le lot en cours, complète par la file de ressource « ecmwf » — dont le
# verrou rend un jumeau impossible —, vérifie qu'il n'y a plus de trou, et seulement alors
# lance le criblage sur la ressource « cpu ».
#
# Usage :  nohup scripts/reprise/criblage_ifs.sh > logs/criblage_ifs.log 2>&1 &
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$RACINE" || exit 2
P=/home/cyril/miniforge3/envs/llm-agent/bin/python3

# ① Attendre le lot déjà lancé — par PID, jamais par motif (§ 1 bis).
PIDS=$(scripts/pids_de.sh scripts/lot_ifs_2025_2026.sh)
if [ -n "$PIDS" ]; then
  echo "⏸ lot IFS en cours (pid $PIDS) — attente · $(date '+%H:%M:%S')"
  for p in $PIDS; do while kill -0 "$p" 2>/dev/null; do sleep 120; done; done
fi

# ② Compléter, jusqu'à trois passes. Le lot saute les mois déjà écrits.
for passe in 1 2 3; do
  MANQUE=$($P -c "
import pandas as pd, pathlib
d = pathlib.Path('data/processed/meteo')
fen = [f'{x:%Y%m}' for x in pd.date_range('2023-08','2025-12',freq='MS')]
ok = [m for m in fen if (d/f'ifs_metropole_{m}.parquet').exists()]
i0, i1 = fen.index(ok[0]), fen.index(ok[-1])
print(' '.join(m for m in fen[i0:i1+1] if m not in ok))")
  [ -z "$MANQUE" ] && { echo '✅ aucun trou dans la fenêtre'; break; }
  echo "▶ passe $passe · trous restants : $MANQUE · $(date '+%H:%M:%S')"
  echo "data/processed/meteo/ifs_metropole_202512.parquet :: scripts/lot_ifs_2025_2026.sh" \
    | scripts/file_ressource.sh ecmwf || true
done

# ③ Le verdict porte sur l'ARTEFACT : plus de trou, ou on ne crible pas.
MANQUE=$($P -c "
import pandas as pd, pathlib
d = pathlib.Path('data/processed/meteo')
fen = [f'{x:%Y%m}' for x in pd.date_range('2023-08','2025-12',freq='MS')]
ok = [m for m in fen if (d/f'ifs_metropole_{m}.parquet').exists()]
i0, i1 = fen.index(ok[0]), fen.index(ok[-1])
print(' '.join(m for m in fen[i0:i1+1] if m not in ok))")
if [ -n "$MANQUE" ]; then
  echo "⛔ trous persistants : $MANQUE"
  echo "   Le criblage n'est PAS lancé : il porterait un indicateur d'époque."
  exit 1
fi

# ④ Cribler, sur la ressource cpu, dans une génération à part.
echo "▶ IFS complet dans la fenêtre — criblage lancé · $(date '+%H:%M:%S')"
for p in NO2 O3 PM10 PM25; do
  echo "reports/apport_ifs_${p}_h2_double.csv :: $P -u scripts/apport_precurseurs.py --lot ifs --polluant $p --horizon 2 --axe double"
done | scripts/generation.sh cpu "criblage-ifs"
