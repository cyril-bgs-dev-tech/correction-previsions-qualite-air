#!/usr/bin/env bash
# Miroir GitHub — publier sur le compte qui RÉPOND, sans attendre le recours.
#
# Pourquoi ce script existe
# ---------------------------
# `cyril-bgs-dev-tech` porte tout le travail récent et rend **404** aux visiteurs non
# authentifiés depuis le 18/08/2026. Un recours est déposé (7 à 10 jours ouvrés), donc
# possiblement après l'échéance du 22/08.
#
# Mais un second compte existe et il est VIVANT : `InProgress63`, vérifié le 21/08 —
# HTTP 200 en anonyme, 4 dépôts publics, confirmé par Cyril. Il n'y a donc rien à attendre :
# on republie dessus, et la candidature retrouve un lien GitHub qui s'ouvre.
#
# Frère de `miroir_gitlab.sh`, structuré pareil. Deux scripts plutôt qu'un paramétré : à la
# veille de l'échéance, on ne réécrit pas le code qui marche pour éviter une duplication.
# À fusionner APRÈS l'envoi, pas avant.
#
# Usage :
#   printf '%s' 'ghp_…' > ~/.github_token && chmod 600 ~/.github_token
#   bash scripts/miroir_github.sh                        # les dépôts par défaut
#   bash scripts/miroir_github.sh <chemin> [<chemin>…]
#
# Le jeton doit porter la portée `repo`. Il ne transite JAMAIS par une conversation.
set -uo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RACINE="$(dirname "$ICI")"
DEPOTS_DEFAUT=("$RACINE" "$HOME/Portfolio")
API="https://api.github.com"

echo "═══ Miroir GitHub ═══"

JETON="$HOME/.github_token"
if [ -z "${GITHUB_TOKEN:-}" ] && [ -r "$JETON" ]; then
  GITHUB_TOKEN="$(tr -d ' \t\r\n' < "$JETON")"; export GITHUB_TOKEN
fi
if [ -z "${GITHUB_TOKEN:-}" ]; then
  cat <<'AIDE'
  ❌ GITHUB_TOKEN absent.

  À faire une fois, connecté en tant que InProgress63 :
    1. https://github.com/settings/tokens?type=beta
       → « Generate new token » · Repository access : All repositories
       → Permissions ▸ Repository ▸ Contents : Read and write · Administration : Read and write
    2. l'écrire hors du dépôt :

         printf '%s' 'github_pat_…' > ~/.github_token && chmod 600 ~/.github_token

  Ce fichier vit dans $HOME, jamais sur /mnt/d : il ne peut pas être commité par accident.
AIDE
  exit 1
fi

UTILISATEUR="$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" "$API/user" \
  | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("login",""))
except Exception: print("")')"
[ -z "$UTILISATEUR" ] && { echo "  ❌ jeton refusé — vérifier la portée et l'expiration."; exit 1; }
echo "  compte GitHub : $UTILISATEUR"

DEPOTS=("$@"); [ ${#DEPOTS[@]} -eq 0 ] && DEPOTS=("${DEPOTS_DEFAUT[@]}")
ECHECS=0

for CHEMIN in "${DEPOTS[@]}"; do
  echo
  [ -d "$CHEMIN/.git" ] || { echo "  ⏭️  $CHEMIN — pas un dépôt git"; continue; }

  # Le nom ne se déduit PAS du dossier : sur GitLab ce raccourci avait créé un doublon, et la
  # lettre citait celui qui n'était plus mis à jour. Un push réussi sur la mauvaise cible est
  # un échec silencieux.
  case "$(basename "$CHEMIN")" in
    Projet_Air_Quality) NOM="correction-previsions-qualite-air" ;;
    *)                  NOM="$(basename "$CHEMIN")" ;;
  esac
  BRANCHE="$(git -C "$CHEMIN" branch --show-current)"
  echo "── $NOM (branche $BRANCHE) ──"

  SALE="$(git -C "$CHEMIN" status --porcelain | wc -l)"
  if [ "$SALE" -gt 0 ]; then
    echo "  ❌ $SALE fichier(s) non commité(s) — le miroir reflète un état publié."
    ECHECS=$((ECHECS + 1)); continue
  fi

  EXISTE="$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer $GITHUB_TOKEN" "$API/repos/$UTILISATEUR/$NOM")"
  if [ "$EXISTE" != "200" ]; then
    CREE="$(curl -s -X POST -H "Authorization: Bearer $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github+json" "$API/user/repos" \
      -d "{\"name\":\"$NOM\",\"private\":false,\"has_issues\":true,\"has_wiki\":false}" \
      | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("full_name",""))
except Exception: print("")')"
    [ -z "$CREE" ] && { echo "  ❌ création refusée — nom déjà pris, ou portée insuffisante."; ECHECS=$((ECHECS+1)); continue; }
    echo "  dépôt créé : $CREE"
  else
    echo "  dépôt déjà présent, mise à jour"
  fi

  # Jamais `--mirror` : il emporterait les refs techniques (refs/codex/…) qui n'ont rien à
  # faire sur un dépôt public.
  URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${UTILISATEUR}/${NOM}.git"
  git -C "$CHEMIN" push --quiet --force "$URL" "$BRANCHE:$BRANCHE" 2>&1 | tail -3
  git -C "$CHEMIN" push --quiet --tags "$URL" 2>/dev/null || true

  # LE contrôle : sans jeton, sans session. C'est très exactement ce qui manquait sur l'autre
  # compte, et son absence a coûté deux jours de publications invisibles (`CLAUDE.md` § 0-C).
  PUBLIC="https://github.com/$UTILISATEUR/$NOM"
  BRUT="https://raw.githubusercontent.com/$UTILISATEUR/$NOM/$BRANCHE/README.md"
  sleep 3
  CODE_PAGE="$(curl -s -o /dev/null -w '%{http_code}' -L "$PUBLIC")"
  CODE_BRUT="$(curl -s -o /dev/null -w '%{http_code}' -L "$BRUT")"
  OCTETS="$(curl -s -L "$BRUT" | wc -c)"
  echo "  page dépôt (anonyme) : HTTP $CODE_PAGE"
  echo "  README brut (anonyme) : HTTP $CODE_BRUT · $OCTETS octets"

  if [ "$CODE_BRUT" = "200" ] && [ "$OCTETS" -gt 500 ]; then
    echo "  ✅ lisible sans compte : $PUBLIC"
  else
    echo "  ❌ contenu NON servi aux anonymes — ne pas mettre ce lien dans la candidature."
    ECHECS=$((ECHECS + 1))
  fi
done

echo
[ "$ECHECS" -eq 0 ] && echo "✅ Tous les miroirs GitHub sont lisibles sans authentification." \
                    || echo "❌ $ECHECS dépôt(s) en échec — voir ci-dessus."
exit "$ECHECS"
