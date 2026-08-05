#!/usr/bin/env bash
# Régénération des tableaux comparatifs — les artefacts du 03/08 portaient un corpus tronqué.
#
# Pourquoi ce lot existe : la liste d'actions « à la fin des téléchargements » du 04/08
# nommait `production_reelle.py`, `pages_soutenance.py` et `pages_regions.py` — et oubliait
# `tableau_comparatif.py`. Ses parquets sont restés sur le corpus du 03/08 : NO₂ 24 mois sur
# 37, O₃ 25, PM2,5 19. Les pages 04 et 05 en dérivent.
#
# Deux à la fois : `ajuster` borne LightGBM à n_jobs=8 sur 32 cœurs. Passe unitaire faite —
# NO₂ en 3,8 min, 109 635 lignes — donc ~8 min pour les trois restants.
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs

if ps -eo cmd | grep -q "^[^ ]*python3 scripts/tableau_comparatif"; then
  echo "✗ un lot tableau_comparatif tourne déjà — arrêt"; exit 1
fi

PY=/home/cyril/miniforge3/envs/llm-agent/bin/python3
H=2
for paire in "O3 PM25" "PM10"; do
  for p in $paire; do
    echo "[$(date +%H:%M:%S)] lancement $p J+$H"
    "$PY" scripts/tableau_comparatif.py --polluant "$p" --horizon "$H" \
      > "logs/comparatif_regen_${p}.log" 2>&1 &
  done
  wait
done

echo
echo "[$(date +%H:%M:%S)] ── contrôle : mois présents dans chaque artefact ──"
"$PY" - <<'PY'
import pandas as pd, pathlib
att = pd.period_range('2023-08', '2026-07', freq='M').strftime('%Y-%m')
for p in ("NO2", "O3", "PM10", "PM25"):
    f = pathlib.Path(f"data/processed/predictions/comparatif_{p}_h2.parquet")
    if not f.exists():
        print(f"  ✗ AUCUN artefact pour {p}"); continue
    t = pd.read_parquet(f)
    m = set(pd.to_datetime(t["jour"]).dt.strftime("%Y-%m"))
    # PM10 n'a pas d'observations avant 2024-01 : son attendu n'est pas celui des autres.
    attendu = [x for x in att if not (p == "PM10" and x < "2024-01")]
    manque = [x for x in attendu if x not in m]
    etat = "✓" if not manque else f"✗ manque {len(manque)} : {', '.join(manque[:6])}"
    print(f"  {p:5s} {len(m):2d} mois · {len(t):>7,} lignes  {etat}")
PY
