# Relance le réglage Optuna depuis l'HÔTE, jusqu'à ce que les 3 polluants soient à 200 essais.
#
# Pourquoi ce fichier existe
# ----------------------------
# `lot_optuna_reglage.sh` réessaie huit fois par polluant, mais ses huit tentatives ne
# protègent que du SEGFAULT — celui où le processus meurt et la boucle shell survit. Quand
# c'est la VM qui est démontée (16 kernel panics du 04 au 11/08), la boucle meurt avec elle
# et personne ne relance. Un lot de six heures sans relanceur hôte est un lot qui a une
# chance sur deux de ne pas finir la nuit.
#
# Appel SYNCHRONE, volontairement : `wsl.exe` ne rend la main que lorsque le lot finit ou que
# la VM meurt. Pas d'orphelin à gérer, et la boucle itère naturellement sur la mort de la VM.
#
# La reprise est portée par Optuna lui-même : l'étude vit dans son `.db` et un essai perdu
# est un essai, jamais l'étude. Le relanceur n'a aucun état à tenir.

$distro  = 'Ubuntu'
$racine  = '/mnt/d/Projet_Air_Quality'

# ⚠️ `wsl.exe -- bash -lc` est un shell de LOGIN : il source /etc/profile et ~/.profile, mais
# PAS ~/.bashrc — donc pas conda, qui y vit. Sans ce prélude, `python3` résout vers
# /usr/bin/python3, sans numpy : 16 tentatives brûlées en ModuleNotFoundError le 11/08.
$prelude = 'source /home/cyril/miniforge3/etc/profile.d/conda.sh && conda activate llm-agent'
$journal = 'C:\Users\Cyril\relance_optuna_reglage.log'
$passes  = 20
$plancher = 60         # sous cette durée, une passe n'a pas pu calculer quoi que ce soit

function Note($m) {
  $l = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m
  Write-Output $l
  Add-Content -Path $journal -Value $l -Encoding UTF8
}

# ── Garde-jumeau (§ 1 bis). `$_.ProcessId -ne $PID` exclut SA PROPRE invocation — sans quoi
# le garde se voit lui-même et refuse toujours, ce qui est pire qu'un garde absent.
$jumeaux = @(Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'powershell.exe' -and $_.ProcessId -ne $PID -and
  $_.CommandLine -like '*-File*relance_optuna_reglage.ps1*' })
if ($jumeaux.Count -gt 0) {
  Note ("REFUS : {0} relanceur(s) déjà en cours — pid {1}" -f $jumeaux.Count, ($jumeaux.ProcessId -join ','))
  exit 3
}

Note "=== relanceur réglage Optuna démarré · $passes passes au plus ==="
$eclairs = 0

for ($i = 1; $i -le $passes; $i++) {

  # ── condition d'arrêt : sur l'ARTEFACT attendu, jamais sur un code de sortie (§ 1 bis)
  $etat = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/optuna_reglage_complete.sh"
  if ($LASTEXITCODE -eq 0) {
    Note "TERMINÉ en $i passe(s) — $etat"
    break
  }

  # ── Un lot tourne-t-il DÉJÀ ? `machine_libre.sh` ne voit que les processus lourds : ENTRE
  # deux tentatives il répond « libre » et laisserait démarrer un second lot, qui écrirait
  # dans la même étude Optuna. Le garde porte donc sur la COQUILLE du lot.
  $vu = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/lot_en_cours.sh lot_optuna_reglage.sh"
  if ($LASTEXITCODE -eq 0) {
    Note "passe $i : un lot tourne déjà — $vu"
    Start-Sleep -Seconds 120
    continue
  }

  Note "passe $i/$passes — $etat"
  $t0 = Get-Date
  & wsl.exe -d $distro -- bash -lc "$prelude && cd $racine && bash scripts/lot_optuna_reglage.sh"
  $code = $LASTEXITCODE
  $duree = [int]((Get-Date) - $t0).TotalSeconds

  if ($code -eq 2) {
    Note "passe $i : refus (un lot tourne déjà) — attente 120 s"
    Start-Sleep -Seconds 120
    continue
  }

  Note "passe $i : le lot a rendu la main · code=$code · ${duree}s"

  # ── Détecteur d'échec STRUCTUREL : une passe réelle dure des minutes. Une passe qui rend
  # la main en quelques secondes n'a rien calculé — environnement absent, chemin faux,
  # argument refusé. Réessayer vingt fois ne la réparera pas.
  if ($duree -lt $plancher) {
    $eclairs++
    Note "  ⚠️ passe éclair ($duree s < $plancher s) — $eclairs d'affilée ; ce n'est pas la plateforme"
    if ($eclairs -ge 3) {
      Note "ARRÊT : 3 passes éclair d'affilée — défaut structurel. Lire logs/lot_optuna_reglage.log"
      break
    }
  } else {
    $eclairs = 0
  }

  Start-Sleep -Seconds 15
}

$final = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/optuna_reglage_complete.sh"
if ($LASTEXITCODE -ne 0) { Note "ARRÊT SANS ABOUTIR — $final" }
