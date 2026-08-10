# Échantillonne la machine HÔTE pendant qu'un lot tourne dans WSL.
#
# Pourquoi ce script existe (10/08/2026)
# --------------------------------------
# `veille_memoire.sh` échantillonne depuis l'INTÉRIEUR de la VM. Il meurt donc à la
# seconde même de l'événement qu'il est censé documenter : sa dernière ligne précède
# toujours la coupure, et il n'enregistre jamais ni la coupure, ni ce que faisait l'hôte
# pendant. Huit démontages de VM le 10/08 (Hyper-V-VmSwitch 233 à 11:01, 11:44, 12:08,
# 12:09, 12:39, 12:58, 13:24, 13:25) sans un seul `Kernel-Power 41` : Windows tient, c'est
# la VM qui disparaît. Aucun instrument du dépôt ne regardait de ce côté-là.
#
# CLAUDE.md § 1 quater tirait déjà la leçon — « quand l'hôte tombe, la trace est chez
# l'hôte » — mais ne l'appliquait qu'à la FOUILLE APRÈS COUP (journaux d'événements). La
# MESURE PENDANT, elle, était restée entièrement dans la VM.
#
# Trois choix qui ne sont pas des détails :
#   * le fichier est sur C:, hors de la VM — il survit à sa mort, ce qui est tout l'objet ;
#   * `Add-Content` ouvre et ferme à chaque ligne : chaque échantillon est sur le disque
#     avant le suivant, comme le `sync` de la version Linux ;
#   * la disparition de `vmmemWSL` est ÉCRITE (`vmmem_Go=0`) au lieu d'arrêter la boucle.
#     C'est la ligne qui date la coupure à la seconde, et les suivantes disent si l'hôte
#     était sous pression au moment où il a lâché la VM.
#
# Aucun compteur de performance n'est utilisé : leurs noms sont TRADUITS sur un Windows
# français et un `Get-Counter '\Memory\Committed Bytes'` y échoue. Les classes CIM, elles,
# portent des noms invariants.
#
# Usage (depuis Windows) : powershell -NoProfile -File scripts\veille_hote.ps1
# Usage (depuis WSL)     : scripts/veille_hote.sh demarrer
param(
  [string]$Sortie = "$env:USERPROFILE\veille_hote.csv",
  [int]$PasSecondes = 2
)

$ErrorActionPreference = 'Continue'

# ⚠️ Culture invariante, sinon le CSV est FAUX sans jamais lever.
# Ce Windows est en français : `2,7` s'écrit avec une virgule, qui est aussi le séparateur
# de champs. Chaque ligne partait donc à 10 colonnes au lieu de 6, et l'analyse rendait
# « pic vmmem 2,00 Go » — la partie entière prise pour la valeur. Un chiffre plausible,
# jamais signalé, exactement la famille de défauts que CLAUDE.md § 2 ter traque.
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture

Add-Content -Path $Sortie -Value 'horodatage,vmmem_Go,libre_Go,engage_Go,limite_engagement_Go,vm_vivante'

while ($true) {
  $vm = Get-Process vmmemWSL -ErrorAction SilentlyContinue
  $vmGo = if ($vm) { [math]::Round(($vm | Measure-Object WorkingSet64 -Sum).Sum / 1GB, 2) } else { 0 }
  $vivante = if ($vm) { 1 } else { 0 }

  $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
  if ($os) {
    $libreGo  = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    # Charge d'engagement = virtuel total - virtuel libre. C'est CETTE grandeur que Windows
    # épuise avant de tuer une VM, pas la RAM libre : une machine peut afficher 40 Go libres
    # et refuser une allocation parce que l'engagement est à sa limite.
    $engageGo = [math]::Round(($os.TotalVirtualMemorySize - $os.FreeVirtualMemory) / 1MB, 2)
    $limiteGo = [math]::Round($os.TotalVirtualMemorySize / 1MB, 2)
  } else {
    $libreGo = -1; $engageGo = -1; $limiteGo = -1
  }

  $ligne = '{0},{1},{2},{3},{4},{5}' -f (Get-Date -Format 'HH:mm:ss'), $vmGo, $libreGo, $engageGo, $limiteGo, $vivante
  Add-Content -Path $Sortie -Value $ligne
  Start-Sleep -Seconds $PasSecondes
}
