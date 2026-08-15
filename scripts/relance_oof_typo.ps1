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
# ⚠️ DEUX bornes, et surtout PAS UNE SEULE — le défaut mesuré le 14/08 sur le jumeau
# `relance_optuna_reglage.ps1`, qui a coûté 31 heures de calcul.
#
# Un compteur unique ne distinguait pas une RELANCE d'une simple constatation que le lot
# tourne encore : chaque tour de surveillance consommait le budget censé protéger d'un
# défaut structurel. Le lot Optuna a tourné 5 h d'un seul tenant, les 20 passes ont été
# brûlées en 40 minutes à écrire « un lot tourne déjà », et le relanceur était mort quatre
# heures avant la panique noyau qu'il devait couvrir.
#
# Ce qu'on borne est le nombre de FOIS OÙ L'ON REPART. Ce qu'on ne borne PAS est le temps
# passé à regarder un lot sain avancer. Les deux ne se comptent pas dans la même unité —
# les confondre borne le mauvais.
$relancesMax = 20      # relances RÉELLES ; la surveillance n'en consomme aucune
$heuresMax   = 14      # échéance de surveillance, dimensionnée sur la durée du lot
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

$echeance = (Get-Date).AddHours($heuresMax)
Note ("=== relanceur OOF typologie démarré · {0} relances au plus · surveillance jusqu'à {1} ===" `
      -f $relancesMax, $echeance.ToString('yyyy-MM-dd HH:mm'))
$relances = 0
$eclairs = 0

$i = 0

while ((Get-Date) -lt $echeance -and $relances -lt $relancesMax) {
  $i++

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
    # La ligne porte l'ÉTAT DE L'ARTEFACT, pas seulement « ça tourne » (§ 1 quinquies) :
    # le journal montre la PROGRESSION, donc un gel devient lisible. Un moniteur
    # qui ne dit que « vivant » est muet sur un lot vivant qui n'avance plus.
    Note "veille $i : lot en cours — $etat"
    Start-Sleep -Seconds 90
    continue
  }

  $relances++
  Note "relance $relances/$relancesMax (passe $i) — $etat"
  $t0 = Get-Date
  & wsl.exe -d $distro -- bash -lc "$prelude && cd $racine && bash scripts/lot_oof_typo.sh"
  $code = $LASTEXITCODE
  $duree = [int]((Get-Date) - $t0).TotalSeconds

  if ($code -eq 2) {
    # Le lot a REFUSÉ de démarrer : rien n'est reparti, rien n'est dû au budget.
    $relances--
    Note "veille $i : refus (un lot tourne déjà) — attente 90 s, relance non décomptée"
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
if ($LASTEXITCODE -ne 0) {
  # NOMMER laquelle des deux bornes a cédé : l'une dit qu'un défaut se répète,
  # l'autre seulement que le lot est plus long que prévu.
  $cause = if ($relances -ge $relancesMax) { "budget de $relancesMax relances épuisé" }
           elseif ((Get-Date) -ge $echeance) { "échéance de $heuresMax h atteinte" }
           else { "arrêt anticipé (voir ci-dessus)" }
  Note "ARRÊT SANS ABOUTIR — $cause · $final"
}
