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

# ⚠️ DEUX bornes, et surtout PAS UNE SEULE — c'est le défaut qui a coûté 31 heures le 14/08.
#
# La version précédente comptait « 20 passes » sans distinguer une RELANCE d'une simple
# constatation que le lot tourne encore. Chaque tour de surveillance consommait donc le
# budget censé protéger d'un défaut structurel : NO2 a tourné 5 h d'un seul tenant, les
# 20 passes ont été brûlées en 40 minutes à écrire « un lot tourne déjà », et le relanceur
# était mort à 22 h 27 quand la VM a paniqué à 02 h 21. Personne n'a relancé, PM10 est
# resté à 38 essais et PM25 n'a jamais démarré.
#
# Ce qu'on veut borner est le nombre de FOIS OÙ L'ON REPART — un défaut non transitoire ne
# doit pas boucler sans fin. Ce qu'on ne veut PAS borner est le temps passé à regarder un
# lot sain avancer. Les deux ne se comptent pas dans la même unité : l'un est un nombre
# d'événements, l'autre une durée. Les confondre borne le mauvais.
$relancesMax = 20      # relances RÉELLES ; la surveillance n'en consomme aucune
# Échéance dimensionnée sur la CADENCE MESURÉE, pas sur une intuition (§ 1) : 40 essais PM10
# en 88 min le 15/08, soit ~27 essais/h → 128 essais restants ≈ 4,7 h, puis PM25 ≈ 7,4 h,
# fin attendue vers 23 h. 18 h laisse de quoi absorber plusieurs paniques sans rien coûter :
# la boucle s'arrête sur l'ARTEFACT dès qu'il est complet, jamais sur l'échéance.
$heuresMax   = 18
$plancher    = 60      # sous cette durée, une passe n'a pas pu calculer quoi que ce soit

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

$echeance = (Get-Date).AddHours($heuresMax)
Note ("=== relanceur réglage Optuna démarré · {0} relances au plus · surveillance jusqu'à {1} ===" `
      -f $relancesMax, $echeance.ToString('yyyy-MM-dd HH:mm'))
$eclairs  = 0
$relances = 0
$i        = 0

while ((Get-Date) -lt $echeance -and $relances -lt $relancesMax) {
  $i++

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
    # La ligne porte la PROGRESSION, pas « ça tourne » — et surtout pas `$etat` (§ 1 quinquies).
    #
    # ⚠️ Première version de ce correctif, le 15/08 : elle affichait `$etat`, en croyant
    # justement montrer la progression. Or `optuna_reglage_complete.sh` compte les lignes du
    # CSV, que `optuna_mos.py` n'écrit qu'à la FIN d'une exécution. Le journal a donc répété
    # « PM10(0) PM25(0) » 37 fois d'affilée pendant que l'étude passait de 32 à 61 essais.
    # Un compteur qui ne bouge jamais est indiscernable d'un lot gelé : la règle appliquée
    # à l'envers, dans le geste même qui prétendait l'appliquer.
    #
    # La source VIVANTE est le `.db`, où Optuna écrit à chaque essai — et l'âge du fichier
    # distingue « lent » de « gelé ». C'est ce que rend `optuna_progression.sh`.
    $prog = & wsl.exe -d $distro -- bash -lc "bash $racine/scripts/optuna_progression.sh PM10 PM25"
    Note "veille $i : $prog"
    Start-Sleep -Seconds 120
    continue          # ⚠️ ne consomme AUCUNE relance : surveiller n'est pas repartir
  }

  $relances++
  Note "relance $relances/$relancesMax (passe $i) — $etat"
  $t0 = Get-Date
  & wsl.exe -d $distro -- bash -lc "$prelude && cd $racine && bash scripts/lot_optuna_reglage.sh"
  $code = $LASTEXITCODE
  $duree = [int]((Get-Date) - $t0).TotalSeconds

  if ($code -eq 2) {
    # Le lot a REFUSÉ de démarrer : rien n'est reparti, donc rien n'est dû au budget.
    $relances--
    Note "veille $i : refus (un lot tourne déjà) — attente 120 s, relance non décomptée"
    Start-Sleep -Seconds 120
    continue
  }

  Note "relance $relances : le lot a rendu la main · code=$code · ${duree}s"

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
if ($LASTEXITCODE -ne 0) {
  # NOMMER laquelle des deux bornes a cédé : « épuisé » et « expiré » appellent des gestes
  # opposés — l'un dit qu'un défaut se répète, l'autre seulement que le lot est plus long
  # que prévu. Un message qui les confond envoie chercher au mauvais endroit.
  $cause = if ($relances -ge $relancesMax) { "budget de $relancesMax relances épuisé" }
           elseif ((Get-Date) -ge $echeance) { "échéance de $heuresMax h atteinte — le lot dure plus que prévu" }
           else { "arrêt anticipé (voir ci-dessus)" }
  Note "ARRÊT SANS ABOUTIR — $cause · $final"
}
