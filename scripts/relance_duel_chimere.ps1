# Relance le duel CHIMERE depuis l'HÔTE, jusqu'à ce que les 4 polluants soient mesurés.
#
# Pourquoi ce fichier existe alors que `relance_ablation.ps1` existait déjà
# ------------------------------------------------------------------------
# Le 11/08 à 18 h 10, la VM est morte du 16ᵉ kernel panic pendant la 3ᵉ tentative de NO₂.
# `lot_duel_chimere.sh` réessaie pourtant huit fois par polluant — mais ses huit tentatives
# ne protègent que du SEGFAULT, où le processus meurt et la boucle shell survit. Quand c'est
# la VM qui est démontée, la boucle meurt avec elle et personne ne relance : le lot était
# muet depuis 25 minutes quand on s'en est aperçu.
#
# Le mécanisme qui manquait avait déjà été construit le matin même pour le lot d'ablation.
# Il n'avait simplement jamais été appliqué à ce lot-ci, écrit après. C'est la § 4 bis dans
# sa forme la plus banale : le correctif posé à un endroit, jamais cherché ailleurs.
#
# Appel SYNCHRONE, volontairement : `wsl.exe` ne rend la main que lorsque le lot finit ou que
# la VM meurt. Pas de processus orphelin à gérer, et la boucle itère naturellement sur la
# mort de la VM. `wsl.exe` relance la distribution éteinte au premier appel suivant.
#
# La reprise est portée par le lot lui-même : `lot_duel_chimere.sh` saute tout polluant dont
# le CSV porte déjà sa dernière ligne. Le relanceur n'a aucun état à tenir — il ne fait que
# rappeler.

$distro  = 'Ubuntu'
$racine  = '/mnt/d/Projet_Air_Quality'

# ⚠️ `wsl.exe -- bash -lc` est un shell de LOGIN : il source /etc/profile et ~/.profile, mais
# PAS ~/.bashrc — donc pas l'activation conda, qui y vit. `python3` y résout vers
# /usr/bin/python3, sans numpy. Le lot d'ablation a brûlé 16 tentatives en `ModuleNotFoundError`
# avant qu'on comprenne que ce n'était PAS le segfault habituel (mesuré le 11/08).
$prelude = 'source /home/cyril/miniforge3/etc/profile.d/conda.sh && conda activate llm-agent'
$journal = 'C:\Users\Cyril\relance_duel_chimere.log'
$passes  = 20          # borne : un défaut non transitoire ne doit pas boucler sans fin
$plancher = 60         # sous cette durée, une passe n'a pas pu calculer quoi que ce soit

function Note($m) {
  $l = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m
  Write-Output $l
  Add-Content -Path $journal -Value $l -Encoding UTF8
}

# ── Garde-jumeau (§ 1 bis). Deux relanceurs lanceraient deux lots écrivant le même CSV :
# c'est la collision du 31/07. `$_.ProcessId -ne $PID` exclut SA PROPRE invocation — sans
# quoi le garde se voit lui-même et refuse toujours (faux positif du 08/08).
$jumeaux = @(Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'powershell.exe' -and $_.ProcessId -ne $PID -and
  $_.CommandLine -like '*-File*relance_duel_chimere.ps1*' })
if ($jumeaux.Count -gt 0) {
  Note ("REFUS : {0} relanceur(s) déjà en cours — pid {1}" -f $jumeaux.Count, ($jumeaux.ProcessId -join ','))
  exit 3
}

Note "=== relanceur duel CHIMERE démarré · $passes passes au plus ==="
$eclairs = 0

for ($i = 1; $i -le $passes; $i++) {

  # ── condition d'arrêt : sur l'ARTEFACT attendu, jamais sur un code de sortie (§ 1 bis)
  $etat = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/duel_chimere_complete.sh"
  if ($LASTEXITCODE -eq 0) {
    Note "TERMINÉ en $i passe(s) — $etat"
    break
  }

  # ── Un lot tourne-t-il DÉJÀ ? `machine_libre.sh`, appelé par le lot lui-même, ne voit que
  # les processus lourds : ENTRE deux tentatives (~20 s de rechargement après un segfault) il
  # répond « libre » et laisse démarrer un second lot. Le garde porte donc sur la COQUILLE du
  # lot, pas sur sa charge.
  $vu = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/lot_en_cours.sh lot_duel_chimere.sh"
  if ($LASTEXITCODE -eq 0) {
    Note "passe $i : un lot tourne déjà — $vu"
    Start-Sleep -Seconds 90
    continue
  }

  Note "passe $i/$passes — $etat"
  $t0 = Get-Date
  & wsl.exe -d $distro -- bash -lc "$prelude && cd $racine && bash scripts/lot_duel_chimere.sh"
  $code = $LASTEXITCODE
  $duree = [int]((Get-Date) - $t0).TotalSeconds

  if ($code -eq 2) {
    # `machine_libre.sh` a refusé : un lot tourne déjà. Attendre franchement.
    Note "passe $i : refus (un lot tourne déjà) — attente 90 s"
    Start-Sleep -Seconds 90
    continue
  }

  Note "passe $i : le lot a rendu la main · code=$code · ${duree}s"

  # ── Détecteur d'échec STRUCTUREL, et c'est la leçon des 16 tentatives brûlées.
  # Une passe réelle dure des minutes : le lot charge 37 mois et ajuste, même quand il
  # segfaute au bout de 3 min. Une passe qui rend la main en quelques secondes n'a rien
  # calculé du tout — environnement absent, chemin faux, argument refusé. Réessayer 20 fois
  # ne la réparera pas ; la borne globale, elle, laisserait brûler l'après-midi.
  # « Un code 1 en 0 minute ne se lit jamais comme un code 139 en 8 minutes. »
  if ($duree -lt $plancher) {
    $eclairs++
    Note "  ⚠️ passe éclair ($duree s < $plancher s) — $eclairs d'affilée ; ce n'est pas la plateforme"
    if ($eclairs -ge 3) {
      Note "ARRÊT : 3 passes éclair d'affilée — défaut structurel, pas transitoire. Lire logs/lot_duel_chimere.log"
      break
    }
  } else {
    $eclairs = 0
  }

  Start-Sleep -Seconds 15
}

$final = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/duel_chimere_complete.sh"
if ($LASTEXITCODE -ne 0) { Note "ARRÊT SANS ABOUTIR — $final" }
