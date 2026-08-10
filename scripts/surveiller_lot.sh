#!/usr/bin/env bash
# Flux d'événements pour `Monitor` : progression, GEL, et arrêt d'un lot long.
#
# Pourquoi ce script existe (10/08/2026 — CLAUDE.md § 1 quinquies)
# ----------------------------------------------------------------
# Le moniteur de ce jour-là ne testait que `kill -0 $PID`. Le lot est resté vivant, en état
# `R`, et n'a plus rien produit pendant **56 minutes** : le moniteur n'a rien remonté, et
# son silence s'est lu comme une bonne nouvelle. La cadence normale était pourtant connue —
# un mois écrit toutes les 30 à 36 s — donc cinq minutes de silence valaient déjà 10 fois
# l'intervalle attendu.
#
# La grandeur à surveiller n'est pas le processus, c'est l'ARTEFACT. Un processus vivant ne
# prouve rien ; un fichier dont la date de modification avance prouve du travail.
#
# Usage : surveiller_lot.sh <pid> <journal> <artefact_qui_avance> <intervalle_attendu_s> [motif]
set -u
PID="${1:?pid exact du lot — jamais un motif, § 1 bis}"
JOURNAL="${2:?journal du lot}"
ARTEFACT="${3:?fichier dont la date doit avancer}"
ATTENDU="${4:?intervalle normal entre deux écritures, en secondes, MESURÉ}"
MOTIF="${5:-tentative|échoué|écrit avec|LOT (COMPLET|INCOMPLET)|REFUS}"

SEUIL=$((5 * ATTENDU))   # 5 × la cadence mesurée : au-delà, ce n'est plus de la lenteur
n=$(wc -l < "$JOURNAL" 2>/dev/null || echo 0)
en_gel=0
depuis=0

while :; do
  # ── progression : les lignes neuves du journal ────────────────────────────────
  m=$(wc -l < "$JOURNAL" 2>/dev/null || echo "$n")
  if [ "$m" -gt "$n" ]; then
    sed -n "$((n + 1)),${m}p" "$JOURNAL" | grep -E --line-buffered "$MOTIF"
    n=$m
  fi

  # ── GEL : l'artefact n'avance plus, alors que le processus vit ────────────────
  if [ -e "$ARTEFACT" ]; then
    age=$(( $(date +%s) - $(stat -c %Y "$ARTEFACT") ))
    if [ "$age" -gt "$SEUIL" ]; then
      # une alerte à l'entrée en gel, puis une rappel toutes les 10 min — jamais à chaque
      # tour, sinon le flux se fait couper pour volume et on perd aussi la fin
      if [ "$en_gel" -eq 0 ] || [ $(( $(date +%s) - depuis )) -ge 600 ]; then
        echo "⚠️ GEL : $(basename "$ARTEFACT") inchangé depuis ${age}s (cadence normale ${ATTENDU}s) — pid $PID vivant, état $(ps -o stat= -p "$PID" 2>/dev/null)"
        en_gel=1; depuis=$(date +%s)
      fi
    elif [ "$en_gel" -eq 1 ]; then
      echo "✅ REPRISE : $(basename "$ARTEFACT") avance de nouveau"
      en_gel=0
    fi
  fi

  # ── arrêt : par pid exact, jamais par motif (le moniteur se matcherait lui-même) ──
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "⛔ LOT ARRÊTÉ (pid $PID absent) — dernières lignes :"
    tail -3 "$JOURNAL"
    break
  fi
  sleep 20
done
