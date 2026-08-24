#!/usr/bin/env bash
# Une GÉNÉRATION : un instantané immuable de code + corpus + tâches, puis la file.
#
# Le défaut que ce contrat supprime — revue exécutive du 24/08/2026
# ------------------------------------------------------------------
# La nuit du 23 au 24 a interrompu ses files SIX fois pour y injecter des correctifs, et
# cassé la chaîne DEUX fois en modifiant du Python qu'une tâche future allait charger.
# Chaque interruption était défendable isolément ; ensemble elles prouvent qu'il manquait
# une frontière.
#
#   « La bonne discipline n'est ni geler tout le dépôt pendant huit heures, ni corriger à
#     chaud. C'est geler la GÉNÉRATION EN COURS. »
#
# Une génération enregistre avant sa première tâche : l'empreinte du code, celle du corpus,
# la liste ordonnée des tâches et son identifiant. Le développement continue ailleurs ; les
# correctifs entrent dans la génération SUIVANTE.
#
# ⚠️ Ce script n'interdit pas techniquement d'éditer un fichier — il rend l'écart VISIBLE :
# le manifeste dit sur quel code la génération a démarré, et `--verifier` dit si le dépôt a
# bougé depuis. C'est le même choix que partout ici : rendre la faute observable plutôt que
# de prétendre l'empêcher.
#
# Quand interrompre une génération malgré tout — la liste est courte et fermée :
#   cible ou agrégation · support du corpus · séparation des plis · colonnes servies ·
#   référence de comparaison · calcul du score · intégrité de l'artefact.
# Pour un journal, un message, une optimisation ou un garde non nécessaire à la validité
# des sorties en cours : laisser finir.
#
# Usage :  scripts/plan_scores.py --taches | scripts/generation.sh cpu "reprise-corpus"
#          scripts/generation.sh --verifier <id>
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE" || { echo "❌ racine introuvable" >&2; exit 2; }
DOSSIER=reports/generations

empreinte_code() {
  # Le commit ET l'état du répertoire de travail : une génération lancée sur des
  # modifications non commitées doit le dire, sinon le manifeste ment.
  local tete sale
  tete=$(git rev-parse --short HEAD 2>/dev/null || echo "hors-git")
  sale=$(git status --porcelain -- scripts src 2>/dev/null | wc -l)
  echo "${tete}$([ "$sale" -gt 0 ] && echo "+${sale}modifs")"
}

if [ "${1:-}" = "--verifier" ]; then
  ID="${2:?usage: $0 --verifier <id>}"
  M="$DOSSIER/$ID.manifeste"
  [ -f "$M" ] || { echo "❌ manifeste inconnu : $M" >&2; exit 2; }
  ATTENDU=$(grep '^code ' "$M" | cut -d' ' -f2-)
  ACTUEL=$(empreinte_code)
  echo "génération $ID · code au lancement : $ATTENDU · maintenant : $ACTUEL"
  [ "$ATTENDU" = "$ACTUEL" ] && echo "✅ le dépôt n'a pas bougé" \
    || echo "⚠️ le dépôt a CHANGÉ depuis le lancement — les tâches non encore démarrées
   chargeront un autre code que celles déjà finies."
  exit 0
fi

RESSOURCE="${1:?usage: $0 <ressource> [libellé]}"
LIBELLE="${2:-sans-libelle}"
mkdir -p "$DOSSIER"
mapfile -t TACHES
N=0; for l in "${TACHES[@]}"; do [[ -n "${l// }" && "$l" != \#* ]] && N=$((N+1)); done
[ "$N" -gt 0 ] || { echo "aucune tâche — rien lancé."; exit 0; }

ID="$(date +%Y%m%d-%H%M%S)-${RESSOURCE}"
M="$DOSSIER/$ID.manifeste"
{
  echo "generation $ID"
  echo "libelle $LIBELLE"
  echo "ressource $RESSOURCE"
  echo "lance_le $(date -Is)"
  echo "code $(empreinte_code)"
  echo "corpus $(/home/cyril/miniforge3/envs/llm-agent/bin/python3 -c "
import sys; sys.path.insert(0,'src')
from pathlib import Path
from aq.ingest.controle import empreinte_corpus
print(empreinte_corpus(['data/processed/meteo/speciation_metropole_*.parquet',
                        'data/processed/meteo/precurseurs_metropole_*.parquet',
                        'data/processed/meteo/chimie_metropole_*.parquet',
                        'data/processed/meteo/geoscf_metropole_*.parquet'], Path('.')))
" 2>/dev/null || echo "indisponible")"
  echo "n_taches $N"
  echo "---"
  printf '%s\n' "${TACHES[@]}"
} > "$M"

echo "▶ génération $ID · $N tâche(s) · code $(empreinte_code)"
echo "  manifeste : $M"
echo "  ⚠️ ne plus modifier scripts/ ni src/ jusqu'à la fin — préparer la suite ailleurs."
printf '%s\n' "${TACHES[@]}" | scripts/file_ressource.sh "$RESSOURCE"
CODE=$?
echo "fini_le $(date -Is)" >> "$M"
echo "code_fin $(empreinte_code)" >> "$M"
exit "$CODE"
