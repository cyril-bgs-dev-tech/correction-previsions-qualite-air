#!/usr/bin/env bash
# Acquisition IFS 0,25° — janvier 2025 à juillet 2026, sur le seau public ECMWF.
#
# Ce que la passe unitaire a établi, le 23/08/2026 — les DEUX axes, jamais un seul
# ----------------------------------------------------------------------------------
# **Axe résultat** : le flux 0p25 sert 2025 et 2026, et les six champs de surface demandés
# (2t, 2d, 10u, 10v, ssrd, tp) sont présents dans l'index de chaque pas. Vérifié sur
# 2025-06-15 et 2026-08-10 avant tout téléchargement.
#
# **Axe coût** : 43 Mo et 16 s par jour, mesurés sur juin 2024 à la granularité DÉFINITIVE
# (un mois entier), soit 1,29 Go et 8 min par mois → 20 mois = 26 Go et ~2,7 h. La
# tolérance de regroupement des plages d'octets est passée de 20 Mo à 1 Mo : 2 % de
# superflu au lieu de 77 %, transfert divisé par 4,2, pour 47 requêtes par jour au lieu de
# 16 — quand le service en accepte 288 par minute.
#
# La fenêtre, et pourquoi elle s'arrête là
# -----------------------------------------
# · **le seau ne porte RIEN avant fin février 2024** — 404 sur `0p25` ET sur `0p4-beta`
#   pour 2023-08, 2023-11, 2024-01 et 2024-02. Le commentaire de `lot_ifs.sh`, écrit en
#   juillet, annonçait « seulement du 0p4-beta » : vérifié ce soir, c'est faux, il n'y a
#   rien. Une affirmation sur un service se re-mesure, elle ne se recopie pas ;
# · et la transition se fait DANS mars 2024 : le 1ᵉʳ mars ne porte que **4 de nos
#   6 champs** (ni `2d` ni `ssrd`), le 15 les porte tous les six. Le parquet de 2024-03
#   existe et paraît complet — 31 jours, 20 Mo — mais son rayonnement et son point de
#   rosée ne couvrent que 84 % du mois. La fenêtre propre commence donc en **2024-04** ;
# · 2026-08 est en cours au moment d'écrire : un mois partiel est un code d'époque, il
#   sera acquis quand il sera complet.
#
# Au terme : **2024-04 → 2026-07, 28 mois** d'IFS à 0,25° portant les six champs.
#
# ⚠️ Ne jamais tuer ce lot par motif : le nom du script figure dans la ligne de commande du
# shell qui le lance, qui se tuerait lui-même (§ 1 bis). PID explicites.
set -uo pipefail
RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE" || { echo "❌ racine introuvable" >&2; exit 2; }
P=/home/cyril/miniforge3/envs/llm-agent/bin/python3

MOIS=""
for m in $(seq 1 12); do MOIS="$MOIS 2025-$m"; done
for m in $(seq 1 7);  do MOIS="$MOIS 2026-$m"; done

TOTAL=0; FAITS=0; ECHECS=""; DEPART=$(date +%s)
for am in $MOIS; do
  AN=${am%-*}; MO=${am#*-}
  MM=$(printf "%02d" "$MO")
  CIBLE="data/processed/meteo/ifs_metropole_${AN}${MM}.parquet"
  TOTAL=$((TOTAL+1))
  if [ -f "$CIBLE" ]; then
    echo "── ${AN}-${MM} déjà extrait — sauté"; FAITS=$((FAITS+1)); continue
  fi
  JOURS=$($P -c "import calendar;print(calendar.monthrange($AN,$MO)[1])")
  echo "── ${AN}-${MM} · $JOURS jours · $(date '+%H:%M:%S')"
  JOURNAL="reports/log_ifs_${AN}${MM}.txt"
  $P scripts/extraire_ifs.py --annee "$AN" --mois "$MO" --jours "$JOURS" > "$JOURNAL" 2>&1
  # ⚠️ Le filtre garde AUSSI les signatures d'échec. Une version antérieure de ce lot ne
  # gardait que les lignes de succès : deux mois ont affiché « 0 échec(s) » puis le décodage
  # a levé, la trace ne correspondait à aucun motif et a été jetée. Le journal montrait un
  # lot sain, deux mois manquaient (§ 1 bis).
  grep -E "Écrit|extrapolation|Cache GRIB purgé|absent|Traceback|Error|Echec|échec\(s\)$" \
       "$JOURNAL" | tail -3
  # Le verdict porte sur l'ARTEFACT, jamais sur le code de sortie (§ 0-C).
  if [ -f "$CIBLE" ]; then
    FAITS=$((FAITS+1))
    echo "   ✅ $CIBLE ($(du -h "$CIBLE" | cut -f1)) · libre $(df -h /mnt/d | tail -1 | awk '{print $4}')"
  else
    ECHECS="$ECHECS ${AN}-${MM}"
    echo "   ❌ AUCUN parquet écrit — journal complet dans $JOURNAL"
  fi
done

echo
echo "═══ IFS 2025-2026 · $FAITS/$TOTAL mois · $(( ($(date +%s)-DEPART)/60 )) min ═══"
[ -n "$ECHECS" ] && { echo "❌ échecs :$ECHECS"; exit 1; }
# Contrôle final sur la LISTE nommée, jamais sur un compte (§ 4).
MANQUE=""
for am in $MOIS; do
  AN=${am%-*}; MM=$(printf "%02d" "${am#*-}")
  [ -f "data/processed/meteo/ifs_metropole_${AN}${MM}.parquet" ] || MANQUE="$MANQUE ${AN}-${MM}"
done
[ -n "$MANQUE" ] && { echo "❌ mois absents :$MANQUE"; exit 1; }
echo "✅ les 19 mois demandés sont sur disque"
