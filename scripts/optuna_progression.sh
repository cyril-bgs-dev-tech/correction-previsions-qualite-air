#!/usr/bin/env bash
# Progression VIVANTE d'un réglage Optuna — pour le journal du relanceur hôte.
#
# Pourquoi ce fichier existe (mesuré le 15/08)
# ---------------------------------------------
# `optuna_reglage_complete.sh` compte les lignes du CSV, et c'est juste pour ce qu'il fait :
# la condition d'arrêt doit porter sur ce qui est PUBLIÉ. Mais `optuna_mos.py` n'écrit son
# CSV qu'à la toute fin d'une exécution — donc pendant les cinq heures que dure un polluant,
# ce compte vaut 0 et ne bouge pas.
#
# Le relanceur s'en servait pour sa ligne de veille. Résultat : 37 lignes consécutives
# annonçant « PM10(0) PM25(0) » pendant que l'étude passait de 32 à 61 essais. **Un journal
# qui affiche le même zéro pendant onze heures est indiscernable d'un lot gelé** — c'est
# exactement la § 1 quinquies, et je l'avais rejouée en croyant l'appliquer.
#
# La source vivante est le `.db` : Optuna y écrit à chaque essai. On le lit en LECTURE SEULE
# (`mode=ro`) pour ne jamais poser de verrou sur l'étude en cours.
#
# ⚠️ Aucune dépendance à conda : `wsl.exe -- bash -lc` est un shell de login, il ne source
# pas ~/.bashrc. `sqlite3` est dans la bibliothèque standard de Python, donc /usr/bin/python3
# suffit — et c'est délibéré.
set -u
cd "$(dirname "$0")/.." || exit 1

CIBLE=${CIBLE:-200}
POLLUANTS=("$@")
[ ${#POLLUANTS[@]} -eq 0 ] && POLLUANTS=(NO2 PM10 PM25)

python3 - "$CIBLE" "${POLLUANTS[@]}" <<'PY'
import sqlite3, sys, pathlib, time

cible = int(sys.argv[1])
morceaux = []
for p in sys.argv[2:]:
    db = pathlib.Path(f"reports/optuna/mos_{p}_lgbm.db")
    if not db.exists():
        morceaux.append(f"{p} 0/{cible}")
        continue
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        n = c.execute("SELECT COUNT(*) FROM trials WHERE state='COMPLETE'").fetchone()[0]
        c.close()
    except sqlite3.Error as e:
        # Ne jamais taire : un compteur illisible doit se voir, pas se lire comme un zéro.
        morceaux.append(f"{p} ILLISIBLE({e.__class__.__name__})")
        continue
    # L'âge du .db date la dernière écriture : c'est lui qui distingue « lent » de « gelé ».
    age = int(time.time() - db.stat().st_mtime)
    morceaux.append(f"{p} {n}/{cible} (écrit il y a {age}s)")

print(" · ".join(morceaux))
PY
