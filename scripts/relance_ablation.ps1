# Relance le lot d'ablation depuis l'HÔTE, jusqu'à ce que les 4 polluants soient mesurés.
#
# Pourquoi côté Windows et pas côté WSL
# -------------------------------------
# La VM meurt d'un kernel panic toutes les ~8 à 16 minutes sous charge (14 panics mesurés du
# 04/08 au 11/08, tous dans `release_pages` — voir CLAUDE.md § 1 quater). Un relanceur qui
# vivrait DANS la VM mourrait avec elle : c'est exactement l'angle mort qui a coûté quatre
# jours. Ce script vit chez l'hôte, donc il survit à ce qu'il surveille.
#
# Appel SYNCHRONE, volontairement : `wsl.exe` ne rend la main que lorsque le lot finit ou que
# la VM meurt. Pas de processus orphelin à gérer, et la boucle itère naturellement sur la
# mort de la VM. `wsl.exe` relance la distribution éteinte au premier appel suivant.
#
# La reprise est portée par le lot lui-même : `lot_ablation.sh` saute les polluants dont le
# CSV porte déjà ses ablations, et `methode_maximale.py` reprend sur son `.partiel`. Le
# relanceur n'a donc aucun état à tenir — il ne fait que rappeler.

$distro  = 'Ubuntu'
$racine  = '/mnt/d/Projet_Air_Quality'

# ⚠️ `wsl.exe -- bash -lc` est un shell de LOGIN : il source /etc/profile et ~/.profile, mais
# PAS ~/.bashrc — donc pas l'activation conda, qui y vit. `python3` y résout vers
# /usr/bin/python3, sans numpy. Le lot échouait alors en `ModuleNotFoundError` en 0 min,
# 20 fois de suite, et la reprise ne servait à rien puisque rien n'était jamais calculé.
# Mesuré le 11/08 : 16 tentatives brûlées avant de comprendre que ce n'était PAS le segfault
# habituel. Un code de sortie 1 en 0 minute ne se lit jamais comme un code 139 en 8 minutes.
$prelude = 'source /home/cyril/miniforge3/etc/profile.d/conda.sh && conda activate llm-agent'
$journal = 'C:\Users\Cyril\relance_ablation.log'
$passes  = 40          # borne : un défaut non transitoire ne doit pas boucler sans fin

function Note($m) {
  $l = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m
  Write-Output $l
  Add-Content -Path $journal -Value $l -Encoding UTF8
}

# ── Garde-jumeau (§ 1 bis). Deux relanceurs lanceraient deux lots : c'est la faute du 31/07,
# et elle s'est reproduite ici au premier essai. `$_.ProcessId -ne $PID` exclut SA PROPRE
# invocation — sans quoi le garde se voit lui-même et refuse toujours (faux positif du 08/08).
$jumeaux = @(Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'powershell.exe' -and $_.ProcessId -ne $PID -and
  $_.CommandLine -like '*-File*relance_ablation.ps1*' })
if ($jumeaux.Count -gt 0) {
  Note ("REFUS : {0} relanceur(s) déjà en cours — pid {1}" -f $jumeaux.Count, ($jumeaux.ProcessId -join ','))
  exit 3
}

Note "=== relanceur démarré · $passes passes au plus ==="

for ($i = 1; $i -le $passes; $i++) {

  # ── condition d'arrêt : sur l'ARTEFACT attendu, jamais sur un code de sortie (§ 1 bis)
  $etat = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/ablation_complete.sh"
  if ($LASTEXITCODE -eq 0) {
    Note "TERMINÉ en $i passe(s) — $etat"
    break
  }

  # ── Un lot tourne-t-il DÉJÀ ? `machine_libre.sh`, appelé par le lot lui-même, ne voit que
  # les processus lourds : ENTRE deux tentatives (~30 s de rechargement après un segfault) il
  # répond « libre » et laisse démarrer un second lot. C'est arrivé à 13 h 48 le 11/08 — deux
  # `lot_ablation.sh` écrivant le même `.partiel`, c'est-à-dire la collision de § 1 bis qui
  # avait déjà coûté deux mois de parquets le 31/07. Le garde porte donc sur la COQUILLE du
  # lot, pas sur sa charge.
  #   ⚠️ Le motif est dans un FICHIER, pas en ligne : écrit ici, ses guillemets se perdaient
  # en traversant PowerShell → wsl.exe → bash -lc, `pgrep` recevait « bash » comme motif et
  # matchait TOUS les bash de la machine. Faux positif permanent, mesuré le 11/08 à 13 h 59.
  $vu = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/lot_en_cours.sh"
  if ($LASTEXITCODE -eq 0) {
    Note "passe $i : un lot tourne déjà — $vu"
    Start-Sleep -Seconds 90
    continue
  }

  Note "passe $i/$passes — $etat"
  $t0 = Get-Date
  & wsl.exe -d $distro -- bash -lc "$prelude && cd $racine && bash scripts/lot_ablation.sh"
  $code = $LASTEXITCODE
  $duree = [int]((Get-Date) - $t0).TotalSeconds

  if ($code -eq 2) {
    # `machine_libre.sh` a refusé : un lot tourne déjà. Attendre franchement.
    Note "passe $i : refus (un lot tourne déjà) — attente 90 s"
    Start-Sleep -Seconds 90
  } else {
    Note "passe $i : le lot a rendu la main · code=$code · ${duree}s"
    Start-Sleep -Seconds 15
  }
}

$final = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/ablation_complete.sh"
if ($LASTEXITCODE -ne 0) { Note "ARRÊT SANS ABOUTIR — $final" }
