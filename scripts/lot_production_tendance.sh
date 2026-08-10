#!/usr/bin/env bash
# Régénère les 4 corpus de production avec l'étage `tendance`, un polluant à la fois.
#
# Pourquoi un lot et pas quatre commandes :
#  · en SÉRIE obligatoirement — deux ajustements LightGBM en parallèle ont été mesurés à
#    ×12,9 sur ce dépôt, la contention porte sur la bande passante mémoire ;
#  · avec REPRISE — un chargement de corpus sur deux à cinq finit en `code=139` sur cette
#    machine ; un lot qui repart de zéro n'aboutirait jamais. La reprise teste le CONTENU
#    (la colonne `cams_veille` est-elle là ?), jamais l'existence du fichier ;
#  · avec SAUVEGARDE — `to_parquet` n'est pas atomique et `data/` est gitignoré : une
#    interruption en pleine écriture détruirait un corpus sans filet.
#
# Le contrôle de fin porte sur l'artefact attendu, jamais sur le code de sortie.
set -u
cd "$(dirname "$0")/.." || exit 1

POLLUANTS=(O3 NO2 PM10 PM25)
MAX=6
# 5 × la cadence MESURÉE (un mois écrit toutes les 30-36 s, sur trois exécutions du 10/08).
# Le seuil se dérive d'une mesure, jamais d'une intuition — § 1 quinquies, geste ①.
GEL_S=180
JOURNAL="logs/lot_production_tendance.log"
mkdir -p logs

echo "═══ départ $(date +%H:%M:%S) ═══" | tee -a "$JOURNAL"

# ── Garde-fous, armés PAR LE LOT et non par ma mémoire (10/08/2026) ────────────
# Le 10/08, la VM a été démontée 8 fois (`Hyper-V-VmSwitch 233`) pendant ce lot, sans un
# seul `Kernel-Power 41` : Windows tenait, la VM mourait. Aucune cause n'a pu être établie
# parce que le seul échantillonneur du dépôt vit DANS la VM qu'il mesure — il meurt à la
# seconde de l'événement. Et un rendu PDF concurrent tournait, ce que CLAUDE.md § 1 interdit.
# Les deux contrôles sont donc ici, dans le lot : un instrument qu'il faut penser à lancer
# est un instrument qui manquera le jour où il servait.
if ! bash scripts/machine_libre.sh; then
  echo "REFUS : un travail lourd tourne déjà — voir la liste ci-dessus" | tee -a "$JOURNAL"
  exit 2
fi
bash scripts/veille_hote.sh demarrer 2>&1 | tee -a "$JOURNAL"
scripts/veille_memoire.sh "scripts/production_reelle.py" "$HOME/veille_memoire_tendance.csv" 2 &
veille_invitee=$!
trap 'kill $veille_invitee 2>/dev/null' EXIT

# ── Sauvegarde : une seule fois, jamais écrasée par une relance du lot ──────────
for p in "${POLLUANTS[@]}"; do
  f="data/processed/predictions/production_${p}_h1.parquet"
  [ -f "$f" ] && [ ! -f "$f.sans_tendance" ] && cp "$f" "$f.sans_tendance" \
    && echo "  sauvegardé : $(basename "$f").sans_tendance" | tee -a "$JOURNAL"
done

# 0 si le parquet porte déjà l'étage `tendance`.
#
# ⚠️ Le test porte sur la PROVENANCE inscrite dans le parquet, jamais sur son schéma.
# La version précédente cherchait la colonne `cams_veille` : c'est un PRÉDICTEUR, et le
# parquet n'écrit que des sorties. Le contrôle était donc faux dans un seul sens — il ne
# pouvait jamais réussir — et aurait relancé six fois chacun des quatre polluants avant
# d'annoncer « LOT INCOMPLET » sur un lot complet.
a_tendance() {
  python3 -c "
import sys, pyarrow.parquet as pq
try:
    meta = pq.read_schema(sys.argv[1]).metadata or {}
except Exception:
    sys.exit(1)
fam = meta.get(b'familles', b'').decode()
sys.exit(0 if 'cams_veille' in fam.split(',') else 1)" "$1" 2>/dev/null
}

for p in "${POLLUANTS[@]}"; do
  f="data/processed/predictions/production_${p}_h1.parquet"
  if a_tendance "$f"; then
    echo "  $p : déjà à jour, sauté" | tee -a "$JOURNAL"
    continue
  fi
  for i in $(seq 1 $MAX); do
    echo "── $p · tentative $i · $(date +%H:%M:%S)" | tee -a "$JOURNAL"
    jrn="logs/production_tendance_${p}.log"
    unite="tendance_${p}_$$_${i}"
    touch "$jrn"
    systemd-run --user --scope --unit="$unite" -p MemoryMax=24G -p MemorySwapMax=0 --quiet \
      env PYTHONFAULTHANDLER=1 python3 -u scripts/production_reelle.py --polluant "$p" \
      >> "$jrn" 2>&1 &
    fils=$!

    # ── Chien de garde de GEL (CLAUDE.md § 1 quinquies) ─────────────────────────
    # Le 10/08, cet appel est resté 60 minutes en état `R` sans écrire une seule ligne,
    # pendant qu'un moniteur qui ne surveillait que le pid le voyait bien vivant. La
    # cadence réelle est d'un mois écrit toutes les 30 à 36 s : au-delà de GEL_S on
    # abandonne la tentative, et la reprise en relance une propre. Un gel coûte alors
    # cinq minutes au lieu d'une heure.
    # Le kill porte sur le SCOPE, pas sur `$!` : tuer `systemd-run` laisserait le Python
    # vivant dans son cgroup.
    while kill -0 "$fils" 2>/dev/null; do
      sleep 30
      age=$(( $(date +%s) - $(stat -c %Y "$jrn") ))
      [ "$age" -le "$GEL_S" ] && continue
      echo "   ⏱️ GEL : $jrn inchangé depuis ${age}s (cadence normale ~35s) — tentative abandonnée" | tee -a "$JOURNAL"
      systemctl --user kill --signal=SIGKILL "${unite}.scope" 2>/dev/null
      sleep 5
      if kill -0 "$fils" 2>/dev/null; then
        echo "   🔴 le processus a SURVÉCU à SIGKILL — le noyau ne traite plus ses signaux." | tee -a "$JOURNAL"
        echo "      Rien en espace utilisateur ne le récupérera : \`wsl --shutdown\` requis." | tee -a "$JOURNAL"
        echo "LOT INTERROMPU — VM à redémarrer" | tee -a "$JOURNAL"
        exit 3
      fi
      break
    done
    wait "$fils" 2>/dev/null
    code=$?
    if a_tendance "$f"; then
      echo "   ✅ $p écrit avec tendance (code=$code)" | tee -a "$JOURNAL"
      break
    fi
    echo "   ✗ $p échoué (code=$code)" | tee -a "$JOURNAL"
  done
done

echo "═══ bilan $(date +%H:%M:%S) ═══" | tee -a "$JOURNAL"
manque=0
for p in "${POLLUANTS[@]}"; do
  f="data/processed/predictions/production_${p}_h1.parquet"
  if a_tendance "$f"; then
    echo "  ✅ $p" | tee -a "$JOURNAL"
  else
    echo "  ❌ $p — AUCUN parquet à jour" | tee -a "$JOURNAL"
    manque=1
  fi
done
[ $manque -eq 0 ] && echo "LOT COMPLET" | tee -a "$JOURNAL" || echo "LOT INCOMPLET" | tee -a "$JOURNAL"
exit $manque
