# Relance la campagne OOF « typologie » depuis l'HÔTE, jusqu'aux 4 parquets frais.
#
# Même patron que `relance_duel_chimere.ps1` — la VM meurt d'un kernel panic sous charge (16
# mesurés du 04/08 au 11/08, tous dans `release_pages`), et un relanceur qui vivrait DANS la
# VM mourrait avec elle. Les ESSAIS_MAX du lot ne couvrent que le segfault, où le processus
# meurt et la boucle shell survit.
#
# ⚠️ CE FICHIER DOIT ÊTRE ENREGISTRÉ AVEC UN BOM UTF-8 (ef bb bf). PowerShell 5.1 lit un
# `.ps1` sans BOM en Windows-1252 : chaque accent casse une chaîne et le script ne parse même
# pas — « Jeton inattendu », « terminateur ' manquant ». Vérifier après toute réécriture :
#   powershell -NoProfile -Command "$e=$null; $null=[System.Management.Automation.Language.Parser]::ParseFile('D:\...\x.ps1',[ref]$null,[ref]$e); if($e){$e|%{$_.Message}}else{'OK'}"

$distro  = 'Ubuntu'
$racine  = '/mnt/d/Projet_Air_Quality'

# `wsl.exe -- bash -lc` est un shell de LOGIN : il ne source pas ~/.bashrc, donc pas conda.
# Sans ce prélude, `python3` résout vers /usr/bin/python3 et le lot meurt en
# ModuleNotFoundError en 0 min — indéfiniment, sans que la reprise serve à rien.
$prelude = 'source /home/cyril/miniforge3/etc/profile.d/conda.sh && conda activate llm-agent'
$journal = 'C:\Users\Cyril\relance_oof_typo.log'
$passes  = 20
$plancher = 60

function Note($m) {
  $l = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m
  Write-Output $l
  Add-Content -Path $journal -Value $l -Encoding UTF8
}

# Garde-jumeau (§ 1 bis) : `$_.ProcessId -ne $PID` exclut SA PROPRE invocation, sans quoi le
# garde se voit lui-même et refuse toujours.
$jumeaux = @(Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'powershell.exe' -and $_.ProcessId -ne $PID -and
  $_.CommandLine -like '*-File*relance_oof_typo.ps1*' })
if ($jumeaux.Count -gt 0) {
  Note ("REFUS : {0} relanceur(s) déjà en cours — pid {1}" -f $jumeaux.Count, ($jumeaux.ProcessId -join ','))
  exit 3
}

Note "=== relanceur OOF typo démarré · $passes passes au plus ==="
$eclairs = 0

for ($i = 1; $i -le $passes; $i++) {

  # Condition d'arrêt sur l'ARTEFACT, jamais sur un code de sortie (§ 1 bis).
  $etat = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/oof_typo_complete.sh"
  if ($LASTEXITCODE -eq 0) {
    Note "TERMINÉ en $i passe(s) — $etat"
    break
  }

  # Un lot tourne-t-il déjà ? `machine_libre.sh` ne voit que les processus lourds : entre
  # deux tentatives il répond « libre » et laisserait démarrer un second lot.
  $vu = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/lot_en_cours.sh lot_oof_typo.sh"
  if ($LASTEXITCODE -eq 0) {
    Note "passe $i : un lot tourne déjà — $vu"
    Start-Sleep -Seconds 90
    continue
  }

  Note "passe $i/$passes — $etat"
  $t0 = Get-Date
  & wsl.exe -d $distro -- bash -lc "$prelude && cd $racine && bash scripts/lot_oof_typo.sh"
  $code = $LASTEXITCODE
  $duree = [int]((Get-Date) - $t0).TotalSeconds

  if ($code -eq 2) {
    Note "passe $i : refus (un lot tourne déjà) — attente 90 s"
    Start-Sleep -Seconds 90
    continue
  }

  Note "passe $i : le lot a rendu la main · code=$code · ${duree}s"

  # Détecteur d'échec STRUCTUREL. Une passe réelle dure des minutes ; une passe qui rend la
  # main en quelques secondes n'a rien calculé — environnement absent, chemin faux. Réessayer
  # 20 fois ne la réparera pas. « Un code 1 en 0 minute ne se lit jamais comme un code 139 en
  # 8 minutes. »
  if ($duree -lt $plancher) {
    $eclairs++
    Note "  ⚠️ passe éclair ($duree s < $plancher s) — $eclairs d'affilée ; ce n'est pas la plateforme"
    if ($eclairs -ge 3) {
      Note "ARRÊT : 3 passes éclair d'affilée — défaut structurel. Lire logs/lot_oof_typo.log"
      break
    }
  } else {
    $eclairs = 0
  }

  Start-Sleep -Seconds 15
}

$final = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/oof_typo_complete.sh"
if ($LASTEXITCODE -ne 0) { Note "ARRÊT SANS ABOUTIR — $final" }
