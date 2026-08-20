#!/usr/bin/env bash
# Miroir GitLab — publier les dépôts là où ils sont réellement lisibles.
#
# Pourquoi ce script existe
# ---------------------------
# Le 18/08/2026, le compte GitHub `cyril-bgs-dev-tech` a cessé d'être servi aux visiteurs
# non authentifiés : profil, API et sept dépôts publics rendent 404, alors que le jeton du
# propriétaire les voit tous marqués `public`. Mesuré depuis deux réseaux indépendants, avec
# témoins. La lettre de candidature renvoie deux fois à l'un de ces dépôts.
#
# Un recours a été déposé, délai annoncé 7 à 10 jours ouvrés. Ce script est le filet : il
# republie les dépôts sur GitLab, où ils sont lisibles sans compte ni authentification.
#
# Ce que ce script NE fait pas, et ne peut pas faire
# ---------------------------------------------------
# Créer le compte GitLab et générer le jeton. Ces deux gestes appartiennent à Cyril. Le
# script s'arrête proprement s'il manque le jeton, en disant exactement quoi produire.
#
# Le contrôle qui compte
# ------------------------
# Le succès n'est PAS le code de sortie de `git push` (`CLAUDE.md` § 0-C). C'est qu'une
# requête **anonyme** — sans jeton, sans session — obtienne le contenu. C'est très
# exactement le contrôle qui manquait côté GitHub, et son absence a coûté deux jours de
# publications invisibles.
#
# Usage :
#   export GITLAB_TOKEN='glpat-…'          # portées : api, write_repository
#   bash scripts/miroir_gitlab.sh                    # tous les dépôts de la liste
#   bash scripts/miroir_gitlab.sh <chemin> [<chemin>…]   # ou ceux-ci seulement
set -uo pipefail

# Chemins ABSOLUS, résolus depuis l'emplacement du script — l'état d'un shell ne traverse
# pas une commande (`CLAUDE.md` § 0-F).
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RACINE="$(dirname "$ICI")"

# Les dépôts à miroiter, dans l'ordre d'importance pour la candidature.
DEPOTS_DEFAUT=(
  "$RACINE"
  "$HOME/Portfolio"
)

API="https://gitlab.com/api/v4"

echo "═══ Miroir GitLab ═══"

# ── ① Le jeton, sans lequel rien n'est possible ───────────────────────────────────────
# Repli sur un fichier hors dépôt : un secret collé dans une conversation y reste consigné,
# un fichier en 600 dans $HOME ne quitte pas la machine. Le dépôt vit sur /mnt/d, le fichier
# non — il ne peut donc pas être commité par accident.
JETON="$HOME/.gitlab_token"
if [ -z "${GITLAB_TOKEN:-}" ] && [ -r "$JETON" ]; then
  GITLAB_TOKEN="$(tr -d ' \t\r\n' < "$JETON")"
  export GITLAB_TOKEN
fi

if [ -z "${GITLAB_TOKEN:-}" ]; then
  cat <<'AIDE'
  ❌ GITLAB_TOKEN absent.

  À faire une fois, côté GitLab :
    1. créer un compte sur https://gitlab.com/users/sign_up
    2. https://gitlab.com/-/user_settings/personal_access_tokens
       → nom : « miroir », portées : api + write_repository, expiration : 1 an
    3. l'écrire dans un fichier que ce script lira, hors du dépôt :

         printf '%s' 'glpat-…' > ~/.gitlab_token && chmod 600 ~/.gitlab_token

  Ce fichier vit dans $HOME, jamais sur /mnt/d : il ne peut pas être commité par accident,
  et le jeton n'a pas à transiter par une conversation, où il resterait consigné.
AIDE
  exit 1
fi

# ── ② Qui est-on ? — et ça vérifie le jeton du même geste ─────────────────────────────
UTILISATEUR="$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$API/user" \
  | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
    print(d.get("username", ""))
except Exception:
    print("")')"

if [ -z "$UTILISATEUR" ]; then
  echo "  ❌ jeton refusé par GitLab — vérifier les portées (api, write_repository) et l'expiration."
  exit 1
fi
echo "  compte GitLab : $UTILISATEUR"

DEPOTS=("$@")
[ ${#DEPOTS[@]} -eq 0 ] && DEPOTS=("${DEPOTS_DEFAUT[@]}")

ECHECS=0
for CHEMIN in "${DEPOTS[@]}"; do
  echo
  if [ ! -d "$CHEMIN/.git" ]; then
    echo "  ⏭️  $CHEMIN — pas un dépôt git, ignoré"
    continue
  fi

  # Le nom du projet GitLab ne se déduit PAS du dossier local. Le 20/08, ce raccourci a
  # recréé « Projet_Air_Quality » à côté de « correction-previsions-qualite-air » : deux
  # projets pour un dépôt, et la lettre de candidature citait celui qui n'était plus mis à
  # jour. Un push qui réussit sur la mauvaise cible est un échec silencieux.
  case "$(basename "$CHEMIN")" in
    Projet_Air_Quality) NOM="correction-previsions-qualite-air" ;;
    *)                  NOM="$(basename "$CHEMIN")" ;;
  esac
  BRANCHE="$(git -C "$CHEMIN" branch --show-current)"
  echo "── $NOM (branche $BRANCHE) ──"

  # ── ③ Refuser de publier un travail non commité : le miroir doit refléter un état, pas
  #     un brouillon. Un `git push` silencieux sur un arbre sale publie une version que
  #     personne n'a relue.
  SALE="$(git -C "$CHEMIN" status --porcelain | wc -l)"
  if [ "$SALE" -gt 0 ]; then
    echo "  ❌ $SALE fichier(s) non commité(s) — commiter d'abord, le miroir reflète un état publié."
    ECHECS=$((ECHECS + 1))
    continue
  fi

  # ── ④ Créer le projet s'il n'existe pas. `visibility=public` est le point : c'est ce que
  #     GitHub n'honore plus.
  CIBLE="$UTILISATEUR%2F$NOM"
  EXISTE="$(curl -s -o /dev/null -w '%{http_code}' \
    --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$API/projects/$CIBLE")"

  if [ "$EXISTE" != "200" ]; then
    # ⚠️ NE PAS dériver la description du dernier sujet de commit : le 20/08, le projet
    #    Portfolio s'est retrouvé décrit par « Le compte des notebooks passe à 1 050, et la
    #    réserve de trop disparaît » — un message de commit, lisible comme une description.
    #    Trouvé par capture d'écran, pas par relecture du code. Sans description explicite,
    #    mieux vaut n'en poser aucune : GitLab affiche alors le README, qui est le bon texte.
    DESCR="${DESCRIPTION:-}"
    CREE="$(curl -s -X POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
      --data-urlencode "name=$NOM" \
      --data-urlencode "path=$NOM" \
      --data-urlencode "visibility=public" \
      --data-urlencode "description=$DESCR" \
      "$API/projects" | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("path_with_namespace", ""))
except Exception:
    print("")')"
    if [ -z "$CREE" ]; then
      echo "  ❌ création du projet refusée — nom déjà pris hors de ton espace, ou portée api manquante."
      ECHECS=$((ECHECS + 1))
      continue
    fi
    echo "  projet créé : $CREE"
  else
    echo "  projet déjà présent, mise à jour"
  fi

  # ── ⑤ Pousser la BRANCHE et les étiquettes — jamais `--mirror`, qui emporterait aussi
  #     les refs techniques (`refs/codex/…` en compte 1 sur ce dépôt) qui n'ont rien à faire
  #     sur un dépôt public.
  URL="https://oauth2:${GITLAB_TOKEN}@gitlab.com/${UTILISATEUR}/${NOM}.git"
  if ! git -C "$CHEMIN" push --quiet --force "$URL" "$BRANCHE:$BRANCHE" 2>&1 | tail -3; then
    echo "  ⚠️  le push a signalé une erreur — le contrôle anonyme ci-dessous tranchera"
  fi
  git -C "$CHEMIN" push --quiet --tags "$URL" 2>/dev/null || true

  # ── ⑥ LE contrôle : une requête ANONYME obtient-elle le contenu ? Sans jeton, sans
  #     session. C'est ce qui manquait côté GitHub, et son absence a coûté deux jours.
  PUBLIC="https://gitlab.com/$UTILISATEUR/$NOM"
  sleep 2
  CODE_PAGE="$(curl -s -o /dev/null -w '%{http_code}' -L "$PUBLIC")"
  CODE_RAW="$(curl -s -o /dev/null -w '%{http_code}' -L "$PUBLIC/-/raw/$BRANCHE/README.md")"
  OCTETS="$(curl -s -L "$PUBLIC/-/raw/$BRANCHE/README.md" | wc -c)"

  echo "  page projet (anonyme) : HTTP $CODE_PAGE"
  echo "  README brut (anonyme) : HTTP $CODE_RAW · $OCTETS octets"

  if [ "$CODE_RAW" = "200" ] && [ "$OCTETS" -gt 500 ]; then
    echo "  ✅ lisible sans compte : $PUBLIC"
  else
    echo "  ❌ le contenu n'est PAS servi aux anonymes — ne pas mettre ce lien dans la lettre."
    ECHECS=$((ECHECS + 1))
  fi
done

echo
if [ "$ECHECS" -eq 0 ]; then
  echo "✅ Tous les miroirs sont lisibles sans authentification."
else
  echo "❌ $ECHECS dépôt(s) en échec — voir ci-dessus."
fi
exit "$ECHECS"
