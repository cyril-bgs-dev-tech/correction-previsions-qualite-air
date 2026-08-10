#!/usr/bin/env bash
# Pilote `veille_hote.ps1` depuis WSL : démarrer, lire, arrêter, tester.
#
# Le processus est lancé par `Start-Process`, donc RÉPARENTÉ côté Windows : il n'est pas
# un enfant de l'interop WSL et ne meurt pas avec la VM. C'est la propriété qu'on achète,
# et `scripts/veille_hote.sh tester` la vérifie au lieu de la supposer.
#
# ⚠️ Le détecteur de jumeau exclut SA PROPRE invocation (`$_.ProcessId -ne $PID`).
# Sans cette clause il matche le `powershell.exe` qui exécute la recherche — dont la ligne
# de commande contient le nom cherché — et annonce un jumeau qui n'existe pas. C'est le
# faux positif de CLAUDE.md § 1 bis, et la première version de ce fichier l'a rejoué à
# l'identique : la passe unitaire l'a attrapé au premier appel.
set -u
SORTIE_WIN='C:\Users\Cyril\veille_hote.csv'
SORTIE_WSL='/mnt/c/Users/Cyril/veille_hote.csv'
PS1_WIN='D:\Projet_Air_Quality\scripts\veille_hote.ps1'

compte_veilles() {
  powershell.exe -NoProfile -Command \
    'Get-CimInstance Win32_Process |
     Where-Object { $_.Name -eq "powershell.exe" -and $_.ProcessId -ne $PID -and
                    $_.CommandLine -like "*-File*veille_hote.ps1*" } |
     Measure-Object | Select-Object -ExpandProperty Count' 2>/dev/null | tr -d '\r' | tail -1
}

case "${1:-lire}" in

  demarrer)
    if [ "$(compte_veilles)" != "0" ] && [ -s "$SORTIE_WSL" ]; then
      echo "veille hôte : déjà en cours ($(wc -l < "$SORTIE_WSL") échantillons)"
      exit 0
    fi
    # `-ExecutionPolicy Bypass` porte sur CE processus seulement : la politique de la
    # machine est `Restricted` et le reste. Sans ce drapeau, `Start-Process` rend la main
    # sans erreur et n'écrit rien — un lancement silencieusement mort, que seul le contrôle
    # sur l'artefact ci-dessous distingue d'un lancement réussi.
    powershell.exe -NoProfile -Command \
      "Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','$PS1_WIN'" \
      >/dev/null 2>&1
    sleep 5
    # Contrôle sur l'ARTEFACT attendu, jamais sur le code de sortie (CLAUDE.md § 1 bis).
    if [ -s "$SORTIE_WSL" ]; then
      echo "veille hôte : démarrée · $(wc -l < "$SORTIE_WSL") ligne(s) dans $SORTIE_WIN"
    else
      echo "veille hôte : ÉCHEC — aucun échantillon écrit dans $SORTIE_WIN" >&2
      exit 1
    fi
    ;;

  arreter)
    powershell.exe -NoProfile -Command \
      'Get-CimInstance Win32_Process |
       Where-Object { $_.Name -eq "powershell.exe" -and $_.ProcessId -ne $PID -and
                      $_.CommandLine -like "*-File*veille_hote.ps1*" } |
       ForEach-Object { Stop-Process -Id $_.ProcessId -Force }' >/dev/null 2>&1
    sleep 1
    echo "veille hôte : arrêtée (restantes : $(compte_veilles))"
    ;;

  lire)
    [ -s "$SORTIE_WSL" ] || { echo "aucune veille hôte enregistrée"; exit 1; }
    echo "── $(( $(wc -l < "$SORTIE_WSL") - 1 )) échantillons · 12 derniers ──"
    tail -12 "$SORTIE_WSL"
    # Contrôle de STRUCTURE avant toute lecture de valeur (CLAUDE.md § 2 bis) : une ligne
    # à 10 champs au lieu de 6 est le signe d'un séparateur décimal virgule, et elle rend
    # des chiffres plausibles et faux au lieu de lever. On lève.
    mauvaises=$(awk -F, 'NF != 6 {n++} END {print n+0}' "$SORTIE_WSL")
    if [ "$mauvaises" != "0" ]; then
      echo "  ❌ $mauvaises ligne(s) hors format à 6 champs — CSV corrompu, analyse refusée" >&2
      echo "     (cause connue : culture non invariante côté PowerShell)" >&2
      exit 1
    fi
    echo "── pic vmmem, plancher de mémoire libre, et toute seconde sans VM ──"
    awk -F, 'NR>1 && $2+0 > pic {pic = $2+0; hp = $1}
             NR>1 && ($3+0 < bas || bas == 0) {bas = $3+0; hb = $1}
             NR>1 && $6 == 0 {morts = morts " " $1}
             END {printf "  pic vmmem     : %.2f Go à %s\n", pic, hp
                  printf "  libre minimum : %.2f Go à %s\n", bas, hb
                  if (morts != "") printf "  ⚠️ VM absente :%s\n", morts
                  else print "  VM vivante sur tout l échantillon"}' "$SORTIE_WSL"
    ;;

  tester)
    # Passe unitaire SUR LE GARDE-FOU (CLAUDE.md § 1 quater, geste 3) : un instrument non
    # testé est une croyance, et il se testera tout seul le jour où il aura échoué. On
    # exige ici la seule propriété qui compte — continuer d'écrire après la mort du shell
    # qui l'a lancé — car c'est elle qui décide s'il survivra à la coupure de la VM.
    bash "$0" arreter >/dev/null 2>&1
    rm -f "$SORTIE_WSL"
    bash "$0" demarrer || exit 1
    avant=$(wc -l < "$SORTIE_WSL")
    echo "  le shell lanceur est terminé ; attente de 10 s…"
    sleep 10
    apres=$(wc -l < "$SORTIE_WSL")
    if [ "$apres" -gt "$avant" ]; then
      echo "  ✅ $avant → $apres lignes : écrit hors de la VM et survit à son lanceur"
    else
      echo "  ❌ $avant → $apres lignes : n'écrit plus, ne survivra pas à la coupure" >&2
      exit 1
    fi
    ;;

  *) echo "usage: $0 {demarrer|arreter|lire|tester}" >&2; exit 2 ;;
esac
