#!/bin/bash
# Lot IFS — mars à décembre 2024, seule fenêtre où le flux 0,25° existe.
#
# **L'IFS à 0,25° ne commence qu'en mars 2024** dans le seau AWS — vérifié par interrogation :
# août 2023, janvier et février 2024 ne portent que `0p4-beta`, un flux bêta à 0,4°. Demander
# `0p25` sur ces mois échoue à chaque pas, silencieusement, avec quatre tentatives par requête :
# cinq minutes de lot pour zéro fichier. La fenêtre exploitable est donc **10 mois sur 17**.
#
# ⚠️ Ne jamais interrompre ce lot par `pkill -f "extraire_ifs"` : le motif figure dans la ligne
# de commande du shell appelant, qui se tue lui-même. Utiliser le PID.
set -u
cd /mnt/d/Projet_Air_Quality
P=/home/cyril/miniforge3/envs/llm-agent/bin/python3

for m in 3 4 5 6 8 9 10 11 12; do
  mm=$(printf "%02d" "$m")
  cible="data/processed/meteo/ifs_metropole_2024${mm}.parquet"
  [ -f "$cible" ] && { echo "── 2024-${mm} déjà extrait"; continue; }
  jours=$($P -c "import calendar;print(calendar.monthrange(2024,$m)[1])")
  echo "── 2024-${mm} · $jours jours"
  # ⚠️ Ne JAMAIS filtrer cette sortie sur les seules lignes de succès. Une première version
  # faisait `| grep -E "Écrit|aucun|échec\(s\)$" | tail -2` : les mois 09 et 10 ont téléchargé
  # leurs 30 jours « 0 échec(s) », puis le décodage a levé — et la trace, ne correspondant à
  # aucun motif, a été jetée. Le journal montrait un lot sain, deux mois manquaient.
  # Le filtre garde donc aussi les signatures d'échec, et la sortie complète va dans un
  # journal par mois, qui reste consultable.
  $P scripts/extraire_ifs.py --annee 2024 --mois "$m" --jours "$jours" \
    > "reports/log_ifs_2024${mm}.txt" 2>&1
  code=$?
  grep -E "Écrit|aucun|Traceback|Error|Echec|ControleEchec|échec\(s\)$" \
    "reports/log_ifs_2024${mm}.txt" | tail -4
  # Le contrôle porte sur le **contenu attendu**, jamais sur le code de sortie seul.
  [ -f "$cible" ] || echo "  ⚠️ 2024-${mm} : AUCUN parquet écrit (code $code) — voir reports/log_ifs_2024${mm}.txt"
  # Le GRIB brut ne sert qu'à produire le parquet : 7,4 Go par mois contre quelques centaines
  # de Ko en sortie. On le purge dès l'extraction faite, sinon dix mois consomment 74 Go pour
  # rien. Le parquet vaut marque d'achèvement pour la reprise.
  [ -f "$cible" ] && rm -f data/raw/ifs/ifs_2024"${mm}"*.grib2
done

echo "── total ──"
ls data/processed/meteo/ifs_metropole_*.parquet 2>/dev/null | wc -l
du -sh data/raw/ifs 2>/dev/null
